#!/usr/bin/env python3
"""
CFTC COT (Commitment of Traders) Real Data Scraper
===================================================
NO SYNTHETIC DATA. REAL CFTC API integration.

CFTC provides COT data via:
1. Legacy Reports (pre-2023): https://publicreporting.cftc.gov/resource/6dca-aqww.json
2. Disaggregated Reports (2023+): https://publicreporting.cftc.gov/resource/jun7-fc8e.json
3. Traders in Financial Futures: https://publicreporting.cftc.gov/resource/gpe5-46if.json

Soybean Oil Futures (ZL):
- Contract Market: CHICAGO BOARD OF TRADE
- CFTC Commodity Code: "007601" or look for "SOYBEAN OIL"
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging
from google.cloud import bigquery
from advanced_scraper_base import AdvancedScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT = 'cbi-v14'
DATASET = 'forecasting_data_warehouse'  # Changed from 'staging' to match production table
TABLE = 'cftc_cot'


class CFTCScraper(AdvancedScraper):
    """CFTC COT data scraper - NO SYNTHETIC DATA"""
    
    # CFTC API endpoints
    LEGACY_FUTURES_URL = 'https://publicreporting.cftc.gov/resource/6dca-aqww.json'
    DISAGGREGATED_URL = 'https://publicreporting.cftc.gov/resource/jun7-fc8e.json'
    TFF_URL = 'https://publicreporting.cftc.gov/resource/gpe5-46if.json'
    
    # Soybean Oil identifiers
    SOYBEAN_OIL_NAMES = ['SOYBEAN OIL', 'SOYBEAN_OIL', 'BEAN OIL']
    SOYBEAN_OIL_CODE = '007601'
    
    def __init__(self):
        super().__init__(
            source_name='CFTC',
            base_url='https://publicreporting.cftc.gov',
            min_delay=2.0,  # CFTC allows faster requests
            max_delay=4.0,
            timeout=60
        )
        self.client = bigquery.Client(project=PROJECT)
    
    def fetch_cot_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch COT data from CFTC API.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum records to fetch
        
        Returns:
            List of COT records
        """
        # Default to last 52 weeks if no dates provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Build query parameters for CFTC API
        params = {
            '$where': f"report_date_as_yyyy_mm_dd >= '{start_date}' AND report_date_as_yyyy_mm_dd <= '{end_date}'",
            '$limit': limit,
            '$order': 'report_date_as_yyyy_mm_dd DESC'
        }
        
        logger.info(f"🔍 Fetching CFTC COT data from {start_date} to {end_date}")
        
        # Try disaggregated endpoint first (more granular)
        try:
            response = self.fetch(
                self.DISAGGREGATED_URL,
                method='GET',
                params=params
            )
            
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Fetched {len(data)} total records from disaggregated endpoint")
                
                # Filter for soybean oil
                soy_oil_data = self._filter_soybean_oil(data)
                
                if soy_oil_data:
                    logger.info(f"✅ Found {len(soy_oil_data)} soybean oil records")
                    return soy_oil_data
                else:
                    logger.warning("⚠️ No soybean oil records in disaggregated data, trying legacy...")
        
        except Exception as e:
            logger.error(f"❌ Disaggregated endpoint failed: {e}")
        
        # Fallback to legacy endpoint
        try:
            response = self.fetch(
                self.LEGACY_FUTURES_URL,
                method='GET',
                params=params
            )
            
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Fetched {len(data)} total records from legacy endpoint")
                
                # Filter for soybean oil
                soy_oil_data = self._filter_soybean_oil(data)
                
                if soy_oil_data:
                    logger.info(f"✅ Found {len(soy_oil_data)} soybean oil records")
                    return soy_oil_data
        
        except Exception as e:
            logger.error(f"❌ Legacy endpoint failed: {e}")
        
        logger.warning("⚠️ No CFTC data found for soybean oil")
        return []
    
    def _filter_soybean_oil(self, data: List[Dict]) -> List[Dict]:
        """Filter records for soybean oil only."""
        filtered = []
        
        for record in data:
            # Check commodity name
            commodity = record.get('commodity', '').upper()
            cftc_code = record.get('cftc_commodity_code', '')
            market_name = record.get('market_and_exchange_names', '').upper()
            
            # Match soybean oil by name or code
            is_soybean_oil = (
                any(name in commodity for name in self.SOYBEAN_OIL_NAMES) or
                cftc_code == self.SOYBEAN_OIL_CODE or
                any(name in market_name for name in self.SOYBEAN_OIL_NAMES)
            )
            
            if is_soybean_oil:
                filtered.append(record)
        
        return filtered
    
    def transform_to_schema(self, cftc_records: List[Dict]) -> List[Dict]:
        """
        Transform CFTC API response to EXISTING BigQuery schema.
        
        EXISTING Schema (DO NOT CHANGE):
        - report_date: DATE
        - commodity: STRING
        - contract_code: STRING (NOT cftc_code)
        - open_interest: FLOAT
        - commercial_long: FLOAT
        - commercial_short: FLOAT
        - commercial_net: FLOAT
        - managed_money_long: FLOAT
        - managed_money_short: FLOAT
        - managed_money_net: FLOAT
        """
        transformed = []
        
        for rec in cftc_records:
            try:
                # Parse date - handle both timestamp and date string formats
                report_date_raw = rec.get('report_date_as_yyyy_mm_dd', rec.get('as_of_date_in_form_yymmdd'))
                
                # Extract date from timestamp if needed (format: "2025-09-23T00:00:00.000")
                if isinstance(report_date_raw, str):
                    if 'T' in report_date_raw:
                        report_date = report_date_raw.split('T')[0]  # Extract YYYY-MM-DD from timestamp
                    elif len(report_date_raw) == 8:  # YYMMDD format
                        year = '20' + report_date_raw[:2]
                        month = report_date_raw[2:4]
                        day = report_date_raw[4:6]
                        report_date = f"{year}-{month}-{day}"
                    else:
                        report_date = report_date_raw
                else:
                    report_date = str(report_date_raw)
                
                # Extract positioning data (field names vary by endpoint)
                commercial_long = int(float(rec.get('comm_positions_long_all', rec.get('commercial_long', 0))))
                commercial_short = int(float(rec.get('comm_positions_short_all', rec.get('commercial_short', 0))))
                noncommercial_long = int(float(rec.get('noncomm_positions_long_all', rec.get('noncommercial_long', 0))))
                noncommercial_short = int(float(rec.get('noncomm_positions_short_all', rec.get('noncommercial_short', 0))))
                
                # Managed money (if available)
                managed_money_long = int(float(rec.get('m_money_positions_long_all', 0)))
                managed_money_short = int(float(rec.get('m_money_positions_short_all', 0)))
                
                # Open interest
                open_interest = int(float(rec.get('open_interest_all', rec.get('open_interest', 0))))
                
                # Non-reportable (small traders)
                nonreportable_long = int(float(rec.get('nonrept_positions_long_all', 0)))
                nonreportable_short = int(float(rec.get('nonrept_positions_short_all', 0)))
                
                # Ensure date is in YYYY-MM-DD format
                if report_date and len(report_date) == 8:  # YYMMDD format
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
                    'ingest_timestamp_utc': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'provenance_uuid': str(uuid.uuid4())
                })
            
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"⚠️ Failed to parse record: {e}")
                continue
        
        return transformed
    
    def load_to_bigquery(self, rows: List[Dict]) -> int:
        """Load transformed rows to BigQuery."""
        if not rows:
            logger.warning("⚠️ No rows to load")
            return 0
        
        table_id = f"{PROJECT}.{DATASET}.{TABLE}"
        
        try:
            # Define schema to match existing table EXACTLY
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
            
            # Convert rows to JSON-compatible format
            json_rows = []
            for row in rows:
                json_row = {}
                for key, value in row.items():
                    if key == 'report_date':
                        # DATE field - ensure YYYY-MM-DD format
                        json_row[key] = str(value)
                    elif key == 'ingest_timestamp_utc':
                        # TIMESTAMP field - convert to RFC3339 format
                        if isinstance(value, str):
                            json_row[key] = value
                        else:
                            json_row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        json_row[key] = value
                json_rows.append(json_row)
            
            job = self.client.load_table_from_json(json_rows, table_id, job_config=job_config)
            job.result()
            
            # Check for errors
            if job.errors:
                logger.error(f"❌ BigQuery load errors: {job.errors}")
                return 0

            logger.info(f"✅ Loaded {len(rows)} CFTC COT records to {table_id}")
            return len(rows)

        except Exception as e:
            logger.error(f"❌ BigQuery load failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def run(self, weeks: int = 52) -> Dict:
        """
        Run the CFTC scraper.
        
        Args:
            weeks: Number of weeks of history to fetch
        
        Returns:
            Summary dict
        """
        logger.info(f"🚀 Starting CFTC COT scraper (last {weeks} weeks)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Fetch data
        raw_data = self.fetch_cot_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not raw_data:
            return {
                'status': 'NO_DATA',
                'rows_loaded': 0,
                'message': 'No soybean oil COT data found'
            }
        
        # Transform
        transformed = self.transform_to_schema(raw_data)
        
        # Load to BigQuery
        rows_loaded = self.load_to_bigquery(transformed)
        
        return {
            'status': 'SUCCESS' if rows_loaded > 0 else 'FAILED',
            'rows_loaded': rows_loaded,
            'weeks_requested': weeks,
            'date_range': f"{start_date.date()} to {end_date.date()}"
        }


if __name__ == '__main__':
    scraper = CFTCScraper()
    result = scraper.run(weeks=52)
    
    print(json.dumps(result, indent=2))

