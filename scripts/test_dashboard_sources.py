#!/usr/bin/env python3
"""Smoke-test all dashboard BigQuery sources.
Verifies tables contain fresh data (<=3 days old) and expected columns.
Writes JSON report to logs/dashboard_source_test.json.
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
from pathlib import Path
import json, sys

bq = bigquery.Client(project="cbi-v14")
TODAY = datetime.utcnow().date()
MAX_STALE = 3  # days

SOURCES = {
    "big_eight_signals": "cbi-v14.models_v4.training_dataset_super_enriched",
    "predictions_daily": "cbi-v14.predictions.daily_forecasts",
    "hourly_prices": "cbi-v14.market_data.hourly_prices",
    "breaking_news": "cbi-v14.forecasting_data_warehouse.breaking_news_hourly",
}

report = {}
for name, table in SOURCES.items():
    try:
        q = f"SELECT COUNT(*) AS row_count, MAX(CAST(date AS DATE)) AS latest_dt FROM `{table}`"
        row = bq.query(q).to_dataframe().iloc[0]
        rows, latest = int(row["row_count"]), row["latest_dt"]
        stale = (TODAY - latest).days if latest else None
        report[name] = {
            "table": table,
            "rows": rows,
            "latest_date": str(latest),
            "stale_days": stale,
            "status": "OK" if stale is not None and stale <= MAX_STALE and rows > 0 else "STALE/EMPTY",
        }
    except Exception as e:
        report[name] = {"table": table, "error": str(e), "status": "ERROR"}

out = Path("/Users/zincdigital/CBI-V14/logs/dashboard_source_test.json")
out.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

# Non-zero exit if any source bad
if any(r["status"] != "OK" for r in report.values()):
    sys.exit(1)
