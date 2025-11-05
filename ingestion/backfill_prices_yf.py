#!/usr/bin/env python3
"""
Backfill last ~30 days of daily prices for core futures via yfinance and load to BigQuery:
  - soybean_oil_prices (ZL=F → ZL)
  - soybean_prices (ZS=F → ZS)
  - soybean_meal_prices (ZM=F → ZM)
  - corn_prices (ZC=F → ZC)
  - cotton_prices (CT=F → CT)

Loads only columns present in each destination table (schema-aligned) to avoid mismatches.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple

import yfinance as yf  # type: ignore
from google.cloud import bigquery  # type: ignore

PROJECT_ID = "cbi-v14"

MAPPING: List[Tuple[str, str, str]] = [
    ("ZL=F", "ZL", "soybean_oil_prices"),
    ("ZS=F", "ZS", "soybean_prices"),
    ("ZM=F", "ZM", "soybean_meal_prices"),
    ("ZC=F", "ZC", "corn_prices"),
    ("CT=F", "CT", "cotton_prices"),
]


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def load_table(client: bigquery.Client, table_id: str, rows: List[Dict]) -> int:
    if not rows:
        return 0
    table = client.get_table(table_id)
    schema_cols = [f.name for f in table.schema]
    aligned = [{k: (r[k] if k in r else None) for k in schema_cols} for r in rows]
    job = client.load_table_from_json(
        aligned, table, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    )
    job.result()
    return len(aligned)


def backfill_symbol(client: bigquery.Client, yf_symbol: str, out_symbol: str, table: str) -> int:
    # Pull ~45 days to ensure 30 business days
    df = yf.download(yf_symbol, period="45d", interval="1d", progress=False)
    if df is None or df.empty:
        return 0
    df = df.dropna()
    rows: List[Dict] = []
    for ts, row in df.iterrows():
        # Ensure datetime
        if not isinstance(ts, datetime):
            try:
                ts = datetime.fromtimestamp(ts)
            except Exception:
                continue
        record: Dict = {
            "time": iso(ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts),
            "symbol": out_symbol,
            "open": float(row.get("Open")) if row.get("Open") is not None else None,
            "high": float(row.get("High")) if row.get("High") is not None else None,
            "low": float(row.get("Low")) if row.get("Low") is not None else None,
            "close": float(row.get("Close")) if row.get("Close") is not None else None,
            "volume": float(row.get("Volume")) if row.get("Volume") is not None else None,
            "source_name": "yfinance",
            "confidence_score": 0.70,
            "ingest_timestamp_utc": iso(datetime.now(timezone.utc)),
            "provenance_uuid": str(uuid.uuid4()),
        }
        rows.append(record)
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.{table}"
    return load_table(client, table_id, rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    total = 0
    results = []
    for yf_symbol, out_symbol, table in MAPPING:
        loaded = backfill_symbol(client, yf_symbol, out_symbol, table)
        results.append({"table": table, "rows": loaded})
        total += loaded
    print({"total_rows": total, "details": results})


if __name__ == "__main__":
    main()






