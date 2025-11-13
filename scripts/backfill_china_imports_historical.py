#!/usr/bin/env python3
"""
China Soybean Imports Historical Backfill (2017-2025)
======================================================
Backfills 8+ years of China soybean import data from UN Comtrade API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'ingestion'))

import json
import time
import uuid
import requests
from datetime import datetime, timezone
from calendar import monthrange
from typing import List, Dict, Optional
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
BASE_URL = "https://comtrade.un.org/api/get"
TABLE_ID = f"{PROJECT_ID}.forecasting_data_warehouse.economic_indicators"

def fetch_uncomtrade_month(yyyymm: str) -> Optional[Dict]:
    """Fetch UN Comtrade data for a specific month"""
    params = {
        "max": "50000",
        "type": "C",
        "freq": "M",
        "px": "HS",
        "ps": yyyymm,
        "rg": "1",   # imports
        "r": "156",   # China
        "p": "all",   # all partners
        "cc": "1201", # soybeans (HS code 1201)
        "fmt": "json",
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"⚠️  HTTP {resp.status_code} for {yyyymm}")
            return None
        return resp.json()
    except Exception as e:
        logger.error(f"❌ Error fetching {yyyymm}: {e}")
        return None


def parse_quantity(dataset: List[Dict]) -> Optional[float]:
    """Parse import quantity from UN Comtrade dataset (returns MMT)"""
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
    return total_kg / 1_000_000_000.0  # Convert to MMT (million metric tons)


def build_econ_record(ts: datetime, indicator: str, value: float, source_url: str) -> Dict:
    """Build economic indicator record for BigQuery"""
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


def check_existing_month(client: bigquery.Client, yyyymm: str) -> bool:
    """Check if data for this month already exists"""
    year = int(yyyymm[:4])
    month = int(yyyymm[4:6])
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    
    query = f"""
    SELECT COUNT(*) as cnt
    FROM `{TABLE_ID}`
    WHERE indicator = 'cn_soybean_imports_mmt'
      AND EXTRACT(YEAR FROM time) = {year}
      AND EXTRACT(MONTH FROM time) = {month}
    """
    
    try:
        result = client.query(query).to_dataframe()
        return result.iloc[0]['cnt'] > 0
    except:
        return False


def load_records(client: bigquery.Client, records: List[Dict]) -> int:
    """Load records to BigQuery"""
    if not records:
        return 0
    
    try:
        table = client.get_table(TABLE_ID)
        schema_cols = [f.name for f in table.schema]
        aligned = [{k: (r[k] if k in r else None) for k in schema_cols} for r in records]
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            schema_update_options=['ALLOW_FIELD_ADDITION']
        )
        job = client.load_table_from_json(aligned, TABLE_ID, job_config=job_config)
        job.result()
        
        if job.errors:
            logger.error(f"❌ BigQuery load errors: {job.errors}")
            return 0
        
        return len(records)
    except Exception as e:
        logger.error(f"❌ Failed to load records: {e}")
        return 0


def generate_month_list(start_year: int, start_month: int, end_year: int, end_month: int) -> List[str]:
    """Generate list of YYYYMM strings for date range"""
    months = []
    year = start_year
    month = start_month
    
    while year < end_year or (year == end_year and month <= end_month):
        months.append(f"{year}{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return months


def backfill_china_imports(start_year: int = 2017, end_year: int = 2025):
    """
    Backfill China soybean imports from UN Comtrade.
    
    Args:
        start_year: Starting year (default: 2017)
        end_year: Ending year (default: 2025)
    """
    client = bigquery.Client(project=PROJECT_ID)
    
    # Generate all months to process
    current_date = datetime.now()
    end_month = current_date.month if end_year == current_date.year else 12
    
    months = generate_month_list(start_year, 1, end_year, end_month)
    
    logger.info(f"🚀 Starting China imports backfill: {start_year}-01 to {end_year}-{end_month:02d}")
    logger.info(f"📅 Total months to process: {len(months)}")
    
    total_loaded = 0
    skipped = 0
    failed = 0
    results = []
    
    for yyyymm in months:
        year = int(yyyymm[:4])
        month = int(yyyymm[4:6])
        
        logger.info(f"\n📅 Processing {year}-{month:02d}...")
        
        # Check if already exists
        if check_existing_month(client, yyyymm):
            logger.info(f"⏭️  Data for {yyyymm} already exists, skipping")
            skipped += 1
            results.append({
                'month': yyyymm,
                'status': 'SKIPPED',
                'rows_loaded': 0
            })
            continue
        
        # Fetch data
        data = fetch_uncomtrade_month(yyyymm)
        if not data or not data.get("dataset"):
            logger.warning(f"⚠️  No data for {yyyymm}")
            failed += 1
            results.append({
                'month': yyyymm,
                'status': 'NO_DATA',
                'rows_loaded': 0
            })
            time.sleep(2)  # Rate limiting
            continue
        
        # Parse quantity
        mmt = parse_quantity(data["dataset"])
        if mmt is None:
            logger.warning(f"⚠️  Could not parse quantity for {yyyymm}")
            failed += 1
            results.append({
                'month': yyyymm,
                'status': 'PARSE_FAILED',
                'rows_loaded': 0
            })
            time.sleep(2)
            continue
        
        # Build record
        month_start = datetime(year, month, 1, tzinfo=timezone.utc)
        source_url = f"{BASE_URL}?max=50000&type=C&freq=M&px=HS&ps={yyyymm}&rg=1&r=156&p=all&cc=1201&fmt=json"
        record = build_econ_record(month_start, "cn_soybean_imports_mmt", mmt, source_url)
        
        # Load to BigQuery
        rows_loaded = load_records(client, [record])
        total_loaded += rows_loaded
        
        if rows_loaded > 0:
            logger.info(f"✅ {yyyymm}: Loaded {mmt:.2f} MMT")
            results.append({
                'month': yyyymm,
                'status': 'SUCCESS',
                'rows_loaded': rows_loaded,
                'value_mmt': mmt
            })
        else:
            failed += 1
            results.append({
                'month': yyyymm,
                'status': 'LOAD_FAILED',
                'rows_loaded': 0
            })
        
        # Rate limiting (UN Comtrade has rate limits)
        time.sleep(3)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("CHINA IMPORTS BACKFILL SUMMARY")
    logger.info("="*60)
    logger.info(f"Total rows loaded: {total_loaded}")
    logger.info(f"Months processed: {len(months)}")
    logger.info(f"Successful: {total_loaded}")
    logger.info(f"Skipped (already exists): {skipped}")
    logger.info(f"Failed: {failed}")
    
    return {
        'total_rows_loaded': total_loaded,
        'months_processed': len(months),
        'successful': total_loaded,
        'skipped': skipped,
        'failed': failed,
        'results': results
    }


if __name__ == '__main__':
    import sys
    
    start_year = 2017
    end_year = 2025
    
    if len(sys.argv) > 1:
        start_year = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_year = int(sys.argv[2])
    
    result = backfill_china_imports(start_year, end_year)
    print(json.dumps(result, indent=2))

