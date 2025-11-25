#!/usr/bin/env python3
"""
Fetch China monthly soybean (HS 1201) import quantities from UN Comtrade (last 3 months)
and load numeric-only records into raw_intelligence.macro_economic_indicators.
"""
import json
import time
import uuid
import requests
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from typing import List, Dict, Optional
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
BASE_URL = "https://comtrade.un.org/api/get"


def last_n_months(n: int) -> List[str]:
    today = datetime.utcnow()
    months: List[str] = []
    year = today.year
    month = today.month
    for _ in range(n):
        months.append(f"{year}{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


def month_start_end(yyyymm: str) -> datetime:
    year = int(yyyymm[:4])
    month = int(yyyymm[4:6])
    return datetime(year, month, 1, tzinfo=timezone.utc)


def fetch_uncomtrade_month(yyyymm: str) -> Optional[Dict]:
    params = {
        "max": "50000",
        "type": "C",
        "freq": "M",
        "px": "HS",
        "ps": yyyymm,
        "rg": "1",   # imports
        "r": "156",   # China
        "p": "all",   # all partners; we'll aggregate
        "cc": "1201", # soybeans
        "fmt": "json",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def parse_quantity(dataset: List[Dict]) -> Optional[float]:
    if not dataset:
        return None
    total_kg = 0.0
    for record in dataset:
        kg = None
        if record.get("NetWeight") is not None:
            try:
                kg = float(record["NetWeight"])  # kilograms
            except Exception:
                kg = None
        elif record.get("TradeQuantity") is not None:
            qty = None
            try:
                qty = float(record["TradeQuantity"])
            except Exception:
                qty = None
            if qty is not None:
                qt_desc = (record.get("qtDesc") or "").lower()
                if "kilogram" in qt_desc:
                    kg = qty
                elif any(x in qt_desc for x in ["tonne", "metric ton", "ton"]):
                    kg = qty * 1000.0
        if kg is not None:
            total_kg += kg
    if total_kg == 0.0:
        return None
    return total_kg / 1_000_000_000.0  # MMT


def build_econ_record(ts: datetime, indicator: str, value: float, source_url: str) -> Dict:
    return {
        "time": ts,
        "indicator": indicator,
        "value": value,
        "source_name": "UN_Comtrade",
        "confidence_score": 0.85,
        "provenance_uuid": str(uuid.uuid4()),
        "ingest_timestamp_utc": datetime.now(timezone.utc),
        "source_url": source_url,
        "notes": "HS 1201 soybeans, rg=1 imports, r=156 China, p=World",
    }


def load_records(client: bigquery.Client, table_id: str, records: List[Dict]) -> None:
    if not records:
        return
    table = client.get_table(table_id)
    schema_cols = [f.name for f in table.schema]
    aligned = [{k: (r[k] if k in r else None) for k in schema_cols} for r in records]
    job = client.load_table_from_json(aligned, table, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"))
    job.result()


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    months = last_n_months(12)
    out: List[Dict] = []
    for m in months:
        data = fetch_uncomtrade_month(m)
        if not data or not data.get("dataset"):
            continue
        mmt = parse_quantity(data["dataset"])  # million metric tons
        if mmt is None:
            continue
        ts = month_start_end(m)
        # Indicator uses MMT units explicitly
        indicator = "cn_soybean_imports_mmt"
        # Recreate source URL for provenance
        source_url = f"{BASE_URL}?max=50000&type=C&freq=M&px=HS&ps={m}&rg=1&r=156&p=all&cc=1201&fmt=json"
        out.append(build_econ_record(ts, indicator, mmt, source_url))
        time.sleep(1)

    if out:
        load_records(client, f"{PROJECT_ID}.raw_intelligence.macro_economic_indicators", out)
        print(json.dumps({"loaded_rows": len(out), "indicator": out[0]["indicator"], "months_loaded": [d["time"].strftime('%Y-%m') for d in out]}))
    else:
        print(json.dumps({"loaded_rows": 0, "message": "No data parsed"}))


if __name__ == "__main__":
    main()


