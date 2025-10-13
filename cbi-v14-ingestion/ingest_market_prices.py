#!/usr/bin/env python3
"""
Market prices ingestion for CBI-V14
Primary feed: TradingEconomics
Fallback feed: Polygon.io
Rate limiting: >=5 minutes between API calls; after backfill, refresh every 4 hours.
Outputs to staging.market_prices with canonical metadata.
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timedelta

import pandas as pd
import requests
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "staging"
TABLE_ID = "market_prices"

TRADINGECONOMICS_CLIENT = os.environ.get("TRADINGECONOMICS_CLIENT")
TRADINGECONOMICS_API_KEY = os.environ.get("TRADINGECONOMICS_API_KEY")
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")

TRADINGECONOMICS_BASE = "https://api.tradingeconomics.com"
POLYGON_BASE = "https://api.polygon.io"

# TradingEconomics category/slug references collected from
# https://docs.tradingeconomics.com/documentation/indicators/
# Polygon tickers follow daily aggregates documentation https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksTicker__range__multiplier___timespan___from___to

MARKET_MANIFEST = {
    # Soy complex
    "ZL": {
        "te": {"category": "commodities", "slug": "soybean-oil"},
        "polygon": "ZL"
    },
    "ZS": {
        "te": {"category": "commodities", "slug": "soybeans"},
        "polygon": "ZS"
    },
    "ZM": {
        "te": {"category": "commodities", "slug": "soybean-meal"},
        "polygon": "ZM"
    },
    # Cross-commodities
    "ZC": {
        "te": {"category": "commodities", "slug": "corn"},
        "polygon": "ZC"
    },
    "ZW": {
        "te": {"category": "commodities", "slug": "wheat"},
        "polygon": "ZW"
    },
    "CC": {
        "te": {"category": "commodities", "slug": "cocoa"},
        "polygon": "CC"
    },
    "CT": {
        "te": {"category": "commodities", "slug": "cotton"},
        "polygon": "CT"
    },
    "FCPO": {
        "te": {"category": "commodities", "slug": "palm-oil"},
        "polygon": None  # Polygon does not list Bursa FCPO contracts
    },
    "RS": {
        "te": {"category": "commodities", "slug": "canola"},
        "polygon": None
    },
    "SUN": {
        "te": {"category": "commodities", "slug": "sunflower-oil"},
        "polygon": None
    },
    # Energy & metals
    "CL": {
        "te": {"category": "commodities", "slug": "crude-oil"},
        "polygon": "CL"
    },
    "BZ": {
        "te": {"category": "commodities", "slug": "brent"},
        "polygon": "BZ"
    },
    "NG": {
        "te": {"category": "commodities", "slug": "natural-gas"},
        "polygon": "NG"
    },
    "GC": {
        "te": {"category": "commodities", "slug": "gold"},
        "polygon": "GC"
    },
    # Macro & volatility
    "DX": {
        "te": {"category": "commodities", "slug": "us-dollar-index"},
        "polygon": "DX-Y.NYB"
    },
    "TNX": {
        "te": {"category": "markets", "slug": "united-states-government-bond-10y"},
        "polygon": "TNX"
    },
    "VIX": {
        "te": {"category": "markets", "slug": "volatility-s-p-500"},
        "polygon": "VIX"
    },
    # FX
    "USD/BRL": {
        "te": {"category": "currency", "slug": "usd-brazil-real"},
        "polygon": "BRLUSD"
    },
    "USD/CNY": {
        "te": {"category": "currency", "slug": "usd-chinese-yuan"},
        "polygon": "CNYUSD"
    }
}

RATE_LIMIT_SLEEP = 300  # 5 minutes in seconds


def fetch_tradingeconomics(symbol: str, manifest_entry, start: datetime, end: datetime) -> pd.DataFrame:
    if not (TRADINGECONOMICS_CLIENT and TRADINGECONOMICS_API_KEY):
        return pd.DataFrame()
    te_info = manifest_entry.get("te") if manifest_entry else None
    if not te_info:
        return pd.DataFrame()
    category = te_info.get("category")
    slug = te_info.get("slug")
    if not (category and slug):
        return pd.DataFrame()
    url = f"{TRADINGECONOMICS_BASE}/markets/{category}/{slug}"
    params = {
        "c": f"{TRADINGECONOMICS_CLIENT}:{TRADINGECONOMICS_API_KEY}",
        "d1": start.strftime("%Y-%m-%d"),
        "d2": end.strftime("%Y-%m-%d"),
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or not data:
            print(f"TradingEconomics empty for {symbol}: {data if isinstance(data, dict) else '[]'}")
            return pd.DataFrame()
        df = pd.DataFrame(data)
        if "Date" not in df or "Close" not in df:
            print(f"TradingEconomics missing fields for {symbol}: {df.columns.tolist()}")
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["Date"]).dt.date
        df = df.loc[(df["date"] >= start.date()) & (df["date"] <= end.date())].copy()
        if df.empty:
            return df
        df.rename(columns={
            "Close": "close_price",
            "Open": "open_price",
            "High": "high_price",
            "Low": "low_price",
            "Volume": "volume"
        }, inplace=True)
        df["symbol"] = symbol
        df["exchange"] = df.get("Exchange", slug)
        df["source_name"] = "TradingEconomics"
        df["confidence_score"] = 0.95
        df["ingest_timestamp_utc"] = datetime.utcnow()
        df["provenance_uuid"] = [str(uuid.uuid4()) for _ in range(len(df))]
        columns = [
            "date", "symbol", "exchange", "open_price", "high_price",
            "low_price", "close_price", "volume", "source_name",
            "confidence_score", "ingest_timestamp_utc", "provenance_uuid"
        ]
        for col in ["open_price", "high_price", "low_price", "close_price"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        if "volume" in df:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        return df[columns]
    except Exception as exc:
        print(f"TradingEconomics fetch failed for {symbol}: {exc}")
        return pd.DataFrame()


def fetch_polygon(symbol: str, ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    if not POLYGON_API_KEY:
        return pd.DataFrame()
    url = (
        f"{POLYGON_BASE}/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
    )
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return pd.DataFrame()
        df = pd.DataFrame(results)
        df["date"] = pd.to_datetime(df["t"], unit="ms").dt.date
        df.rename(columns={
            "o": "open_price",
            "h": "high_price",
            "l": "low_price",
            "c": "close_price",
            "v": "volume"
        }, inplace=True)
        df["symbol"] = symbol
        df["exchange"] = data.get("ticker", ticker)
        df["source_name"] = "Polygon"
        df["confidence_score"] = 0.80
        df["ingest_timestamp_utc"] = datetime.utcnow()
        df["provenance_uuid"] = [str(uuid.uuid4()) for _ in range(len(df))]
        columns = [
            "date", "symbol", "exchange", "open_price", "high_price",
            "low_price", "close_price", "volume", "source_name",
            "confidence_score", "ingest_timestamp_utc", "provenance_uuid"
        ]
        return df[columns]
    except Exception as exc:
        print(f"Polygon fetch failed for {symbol}: {exc}")
        return pd.DataFrame()


def load_dataframe(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        print(f"Loaded {len(df)} rows into {table_ref}")
        return len(df)
    except Exception as exc:
        print(f"BigQuery load failed: {exc}")
        return 0


def ingest_symbol(symbol: str, start: datetime, end: datetime) -> int:
    manifest_entry = MARKET_MANIFEST.get(symbol)
    if not manifest_entry:
        print(f"Symbol {symbol} not configured in manifest")
        return 0
    endpoint_tuple = manifest_entry.get("te")
    rows = 0
    if endpoint_tuple:
        df = fetch_tradingeconomics(symbol, manifest_entry, start, end)
        rows = load_dataframe(df)
        if rows > 0:
            return rows
        print(f"TradingEconomics returned no data for {symbol}, trying Polygon...")
    ticker = manifest_entry.get("polygon")
    if ticker:
        df = fetch_polygon(symbol, ticker, start, end)
        rows = load_dataframe(df)
        if rows > 0:
            return rows
    print(f"No data for {symbol} in requested range")
    return 0


def backfill(symbols, years):
    end = datetime.utcnow()
    start = end - timedelta(days=years * 365)
    total_rows = 0
    current_start = start
    chunk = timedelta(days=180)
    while current_start < end:
        current_end = min(current_start + chunk, end)
        print(f"Backfilling {current_start.date()} to {current_end.date()}")
        for symbol in symbols:
            total_rows += ingest_symbol(symbol, current_start, current_end)
        print(f"Sleeping {RATE_LIMIT_SLEEP} seconds for rate limit")
        time.sleep(RATE_LIMIT_SLEEP)
        current_start = current_end + timedelta(days=1)
    print(f"Backfill complete: {total_rows} rows loaded")


def update_recent(symbols, days):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    total_rows = 0
    for symbol in symbols:
        total_rows += ingest_symbol(symbol, start, end)
    print(f"Update complete: {total_rows} rows loaded")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backfill', action='store_true')
    parser.add_argument('--years', type=int, default=5)
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--days', type=int, default=5)
    args = parser.parse_args()

    symbols = list(MARKET_MANIFEST.keys())
    if args.backfill:
        backfill(symbols, years=args.years)
    elif args.update:
        update_recent(symbols, days=args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
