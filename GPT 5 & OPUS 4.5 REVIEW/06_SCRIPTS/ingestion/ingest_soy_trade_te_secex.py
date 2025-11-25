#!/usr/bin/env python3
"""
UN Comtrade + SECEX ingestor for soybean trade metrics (no API key required).
- Brazil exports of soybeans (monthly, last 12 months) via UN Comtrade (HS 1201, rg=2).
- Optional: Brazil exports to China specifically (partner 156) via UN Comtrade.
- Optional: Check SECEX CSV availability for provenance logging (no parsing yet).

Writes numeric-only rows to raw_intelligence.macro_economic_indicators.
"""
import json
import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

import requests
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
COMTRADE_BASE = "https://comtradeapi.un.org/public/v1/preview/flowtrade"


def bq_load(client: bigquery.Client, table_id: str, rows: List[Dict]) -> None:
    if not rows:
        return
    table = client.get_table(table_id)
    schema_cols = [f.name for f in table.schema]
    aligned = [{k: (r.get(k)) for k in schema_cols} for r in rows]
    job = client.load_table_from_json(aligned, table, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"))
    job.result()


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def build_row(ts: datetime, indicator: str, value: float, source_name: str, source_url: str, notes: str, conf: float = 0.85) -> Dict:
    return {
        "time": iso(ts),
        "indicator": indicator,
        "value": value,
        "source_name": source_name,
        "confidence_score": conf,
        "ingest_timestamp_utc": iso(datetime.now(timezone.utc)),
        "provenance_uuid": str(uuid.uuid4()),
        "source_url": source_url,
        "notes": notes[:1000],
    }


def last_n_months(n: int) -> List[str]:
    today = datetime.now(timezone.utc)
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


def month_to_datetime(yyyymm: str) -> datetime:
    year = int(yyyymm[:4])
    month = int(yyyymm[4:6])
    return datetime(year, month, 1, tzinfo=timezone.utc)


def fetch_uncomtrade_series(reporter: str, flow: str, partner: str = "all", months: int = 12) -> List[Tuple[str, float, str]]:
    """Fetch last N months of HS1201 soybean trade (NetWeight) from UN Comtrade classic API."""
    results: List[Tuple[str, float, str]] = []
    flow_code = "1" if flow == "import" else "2"
    for m in last_n_months(months):
        params = {
            "typeCode": "C",
            "freqCode": "M",
            "period": m,
            "reporterCode": reporter,
            "partnerCode": partner,
            "flowCode": flow_code,
            "cmdCode": "1201",
            "customsCode": "C00",
            "partner2Code": "0",
            "motCode": "0",
            "format": "JSON",
        }
        try:
            resp = requests.get(COMTRADE_BASE, params=params, timeout=60)
            if resp.status_code != 200:
                continue
            data = resp.json()
        except Exception:
            continue

        dataset = data.get("dataset", []) if isinstance(data, dict) else []
        total_kg = 0.0
        for record in dataset:
            net_weight = record.get("NetWeight")
            if net_weight is None:
                continue
            try:
                total_kg += float(net_weight)
            except Exception:
                continue

        if total_kg <= 0:
            continue

        mmt = total_kg / 1_000_000_000.0
        source_url = (
            f"{COMTRADE_BASE}?typeCode=C&freqCode=M&period={m}&reporterCode={reporter}&partnerCode={partner}&flowCode={flow_code}&cmdCode=1201&customsCode=C00&format=JSON"
        )
        results.append((m, mmt, source_url))
        time.sleep(1)

    return results


def try_secex_csv(year: int) -> Optional[str]:
    # Known public base for ComexStat microdata (CSV or ZIP) may vary; try a plausible CSV path first
    candidates = [
        f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_{year}.csv",
        f"https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_{year}.zip",
    ]
    for u in candidates:
        try:
            r = requests.get(u, timeout=30)
            if r.status_code == 200 and len(r.content) > 1024:
                return u
        except Exception:
            pass
    return None


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.raw_intelligence.macro_economic_indicators"

    rows: List[Dict] = []

    # Brazil exports to all destinations (reporter 076, flow exports, partner all)
    br_world = fetch_uncomtrade_series(reporter="076", flow="export", partner="0", months=12)
    for period, mmt, url in br_world:
        rows.append(
            build_row(
                ts=month_to_datetime(period),
                indicator="br_soybean_exports_mmt",
                value=mmt,
                source_name="UN_Comtrade",
                source_url=url,
                notes="Brazil soybean exports (HS1201) all partners via UN Comtrade",
                conf=0.8,
            )
        )

    # Brazil exports to China specifically (partner 156) for trade focus
    br_china = fetch_uncomtrade_series(reporter="076", flow="export", partner="156", months=12)
    for period, mmt, url in br_china:
        rows.append(
            build_row(
                ts=month_to_datetime(period),
                indicator="br_to_cn_soybean_exports_mmt",
                value=mmt,
                source_name="UN_Comtrade",
                source_url=url,
                notes="Brazil soybean exports to China (HS1201) via UN Comtrade",
                conf=0.75,
            )
        )

    # Optional: note SECEX availability for future enriched parsing
    secex_url = try_secex_csv(datetime.now(timezone.utc).year)
    if secex_url:
        rows.append(
            build_row(
                ts=datetime(datetime.now(timezone.utc).year, datetime.now(timezone.utc).month, 1, tzinfo=timezone.utc),
                indicator="br_secex_soy_exports_provenance",
                value=0.0,
                source_name="SECEX_ComexStat",
                source_url=secex_url,
                notes="SECEX CSV reachable; detailed NCM1201 parsing pending",
                conf=0.5,
            )
        )

    if rows:
        bq_load(client, table_id, rows)
        print(json.dumps({"loaded_rows": len(rows), "indicators": list({r["indicator"] for r in rows})}))
    else:
        print(json.dumps({"loaded_rows": 0, "message": "No UN Comtrade data returned"}))


if __name__ == "__main__":
    main()




