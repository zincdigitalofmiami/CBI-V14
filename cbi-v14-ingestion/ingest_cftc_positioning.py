#!/usr/bin/env python3
"""
CFTC COT (Commitment of Traders) Data Scraper
=============================================
Loads real CFTC soybean oil positioning data into staging.cftc_cot.
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging
from google.cloud import bigquery
from advanced_scraper_base import AdvancedScraper
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT = 'cbi-v14'
DATASET = 'staging'
TABLE = 'cftc_cot'


class CFTCScraper(AdvancedScraper):
    """CFTC COT data scraper - NO SYNTHETIC DATA"""

    LEGACY_FUTURES_URL = 'https://publicreporting.cftc.gov/resource/6dca-aqww.json'
    DISAGGREGATED_URL = 'https://publicreporting.cftc.gov/resource/jun7-fc8e.json'
    TFF_URL = 'https://publicreporting.cftc.gov/resource/gpe5-46if.json'

    SOYBEAN_OIL_NAMES = ['SOYBEAN OIL', 'SOYBEAN_OIL', 'BEAN OIL']
    SOYBEAN_OIL_CODE = '007601'

    def __init__(self):
        super().__init__(
            source_name='CFTC',
            base_url='https://publicreporting.cftc.gov',
            min_delay=2.0,
            max_delay=4.0,
            timeout=60
        )
        self.client = bigquery.Client(project=PROJECT)

    def fetch_cot_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        params = {
            '$where': f"report_date_as_yyyy_mm_dd >= '{start_date}' AND report_date_as_yyyy_mm_dd <= '{end_date}'",
            '$limit': limit,
            '$order': 'report_date_as_yyyy_mm_dd DESC'
        }

        logger.info(f"🔍 Fetching CFTC COT data from {start_date} to {end_date}")

        try:
            response = self.fetch(self.DISAGGREGATED_URL, method='GET', params=params)
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Fetched {len(data)} total records from disaggregated endpoint")
                soy_oil_data = self._filter_soybean_oil(data)
                if soy_oil_data:
                    logger.info(f"✅ Found {len(soy_oil_data)} soybean oil records")
                    return soy_oil_data
                else:
                    logger.warning("⚠️ No soybean oil records in disaggregated data, trying legacy...")
        except Exception as e:
            logger.error(f"❌ Disaggregated endpoint failed: {e}")

        try:
            response = self.fetch(self.LEGACY_FUTURES_URL, method='GET', params=params)
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Fetched {len(data)} total records from legacy endpoint")
                soy_oil_data = self._filter_soybean_oil(data)
                if soy_oil_data:
                    logger.info(f"✅ Found {len(soy_oil_data)} soybean oil records")
                    return soy_oil_data
        except Exception as e:
            logger.error(f"❌ Legacy endpoint failed: {e}")

        logger.warning("⚠️ No CFTC data found for soybean oil")
        return []

    def _filter_soybean_oil(self, data: List[Dict]) -> List[Dict]:
        filtered = []
        for record in data:
            commodity = record.get('commodity', '').upper()
            cftc_code = record.get('cftc_commodity_code', '')
            market_name = record.get('market_and_exchange_names', '').upper()
            is_soybean_oil = (
                any(name in commodity for name in self.SOYBEAN_OIL_NAMES) or
                cftc_code == self.SOYBEAN_OIL_CODE or
                any(name in market_name for name in self.SOYBEAN_OIL_NAMES)
            )
            if is_soybean_oil:
                filtered.append(record)
        return filtered

    def transform_to_schema(self, cftc_records: List[Dict]) -> List[Dict]:
        transformed = []
        for rec in cftc_records:
            try:
                report_date = rec.get('report_date_as_yyyy_mm_dd', rec.get('as_of_date_in_form_yymmdd'))
                if report_date:
                    report_date = report_date[:10]
                commercial_long = int(float(rec.get('comm_positions_long_all', rec.get('commercial_long', 0))))
                commercial_short = int(float(rec.get('comm_positions_short_all', rec.get('commercial_short', 0))))
                managed_money_long = int(float(rec.get('m_money_positions_long_all', 0)))
                managed_money_short = int(float(rec.get('m_money_positions_short_all', 0)))
                open_interest = int(float(rec.get('open_interest_all', rec.get('open_interest', 0))))

                if report_date and len(report_date) == 8:
                    year = '20' + report_date[:2]
                    month = report_date[2:4]
                    day = report_date[4:6]
                    report_date = f"{year}-{month}-{day}"

                transformed.append({
                    'report_date': report_date,
                    'commodity': 'Soybean_Oil',
                    'contract_code': 'ZL',
                    'managed_money_long': float(managed_money_long),
                    'managed_money_short': float(managed_money_short),
                    'managed_money_net': float(managed_money_long - managed_money_short),
                    'commercial_long': float(commercial_long),
                    'commercial_short': float(commercial_short),
                    'commercial_net': float(commercial_long - commercial_short),
                    'open_interest': float(open_interest),
                    'source_name': 'CFTC_API',
                    'confidence_score': 0.95,
                    'ingest_timestamp_utc': datetime.now(timezone.utc).isoformat(),
                    'provenance_uuid': str(uuid.uuid4())
                })

            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"⚠️ Failed to parse record: {e}")
                continue

        return transformed

    def load_to_bigquery(self, rows: List[Dict]) -> int:
        if not rows:
            logger.warning("⚠️ No rows to load")
            return 0

        table_id = f"{PROJECT}.{DATASET}.{TABLE}"

        try:
            schema = [
                bigquery.SchemaField("report_date", "DATE"),
                bigquery.SchemaField("commodity", "STRING"),
                bigquery.SchemaField("contract_code", "STRING"),
                bigquery.SchemaField("managed_money_long", "FLOAT"),
                bigquery.SchemaField("managed_money_short", "FLOAT"),
                bigquery.SchemaField("managed_money_net", "FLOAT"),
                bigquery.SchemaField("commercial_long", "FLOAT"),
                bigquery.SchemaField("commercial_short", "FLOAT"),
                bigquery.SchemaField("commercial_net", "FLOAT"),
                bigquery.SchemaField("open_interest", "FLOAT"),
                bigquery.SchemaField("source_name", "STRING"),
                bigquery.SchemaField("confidence_score", "FLOAT"),
                bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                bigquery.SchemaField("provenance_uuid", "STRING"),
            ]
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            job = self.client.load_table_from_json(rows, table_id, job_config=job_config)
            job.result()

            logger.info(f"✅ Loaded {len(rows)} CFTC COT records to {table_id}")
            return len(rows)

        except Exception as e:
            logger.error(f"❌ BigQuery load failed: {e}")
            return 0

    def run(self, weeks: int = 52, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 1000) -> Dict:
        logger.info(f"🚀 Starting CFTC COT scraper (last {weeks} weeks)")

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()

        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = end_dt - timedelta(weeks=weeks)

        raw_data = self.fetch_cot_data(
            start_date=start_dt.strftime('%Y-%m-%d'),
            end_date=end_dt.strftime('%Y-%m-%d'),
            limit=limit
        )

        if not raw_data:
            return {
                'status': 'NO_DATA',
                'rows_loaded': 0,
                'message': 'No soybean oil COT data found'
            }

        transformed = self.transform_to_schema(raw_data)
        unique_by_date = {}
        for row in transformed:
            report_date = row.get('report_date')
            if report_date and report_date not in unique_by_date:
                unique_by_date[report_date] = row
        deduped_rows = list(unique_by_date.values())
        rows_loaded = self.load_to_bigquery(deduped_rows)

        return {
            'status': 'SUCCESS' if rows_loaded > 0 else 'FAILED',
            'rows_loaded': rows_loaded,
            'weeks_requested': weeks,
            'date_range': f"{start_dt.date()} to {end_dt.date()}"
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CFTC positioning scraper")
    parser.add_argument('--weeks', type=int, default=52)
    parser.add_argument('--start-date', type=str, default=None)
    parser.add_argument('--end-date', type=str, default=None)
    parser.add_argument('--limit', type=int, default=1000)
    args = parser.parse_args()

    scraper = CFTCScraper()
    result = scraper.run(weeks=args.weeks, start_date=args.start_date, end_date=args.end_date, limit=args.limit)
    print(json.dumps(result, indent=2))

