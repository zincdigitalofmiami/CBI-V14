#!/usr/bin/env python3
"""
EPA RIN Prices Scraper
Scrapes weekly RIN (Renewable Identification Number) prices from EPA website
Sources:
- RIN Trades: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rin-trades-and-price-information
- RIN Generation: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/spreadsheet-rin-generation-data-renewable-fuel
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone, timedelta
import uuid
import logging
import time
from bs4 import BeautifulSoup
import re
from typing import List, Optional, Dict
from io import StringIO
from requests import Response, exceptions as req_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "biofuel_prices"

MIN_VALID_PRICE = 0.0
MAX_VALID_PRICE = 10.0  # conservative bound to reject obvious garbage
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_RETRY_ATTEMPTS = 3
REQUEST_RETRY_SLEEP_SECONDS = 2

class EPARINScraper:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.base_url = "https://www.epa.gov"
        
    def scrape_rin_trades_page(self):
        """Scrape RIN trades and price information page"""
        url = "https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rin-trades-and-price-information"
        
        try:
            response = self._fetch_with_retries(url)
            if response is None:
                logger.error("Failed to fetch EPA RIN page after retries")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            # Pandas parses all tables from the page text
            tables = pd.read_html(StringIO(response.text))

            rin_records: List[Dict] = []
            candidate_tables = 0
            for table in tables:
                # Standardize column names
                table.columns = [str(col).strip().upper() for col in table.columns]
                if not self._looks_like_rin_table(table.columns):
                    continue
                candidate_tables += 1

                week_col = self._find_week_column(table.columns)
                if week_col is None:
                    continue

                for _, row in table.iterrows():
                    record = self._parse_row(row, week_col)
                    if record is not None:
                        rin_records.append(record)

            if candidate_tables == 0:
                logger.warning("No candidate RIN price tables found on page")

            # Dedupe by date (keep last occurrence in case of duplicates)
            deduped: Dict[datetime, Dict] = {}
            for rec in rin_records:
                deduped[rec['date']] = rec

            rin_data = list(deduped.values())
            logger.info(
                f"Extracted {len(rin_data)} valid RIN price records "
                f"from {candidate_tables} candidate tables"
            )
            return rin_data

        except Exception as e:
            logger.error(f"Error scraping RIN trades page: {e}")
            return []
    
    def _extract_price(self, row, rin_type):
        """Extract RIN price from row"""
        for col in row.index:
            if rin_type in str(col).upper():
                value = row[col]
                if pd.notna(value):
                    try:
                        # Remove $ and commas, convert to float
                        price_str = str(value).replace('$', '').replace(',', '').strip()
                        price_val = float(price_str)
                        if self._is_valid_price(price_val):
                            return price_val
                    except:
                        pass
        return None
    
    def _is_valid_price(self, value: float) -> bool:
        return MIN_VALID_PRICE <= value <= MAX_VALID_PRICE

    def _looks_like_rin_table(self, columns: List[str]) -> bool:
        """Heuristic: table must include a date/week column AND at least one of D4/D5/D6/D3/D7."""
        cols = [str(c).upper() for c in columns]
        has_week = any(('WEEK' in c) or ('DATE' in c) for c in cols)
        has_rin = any(r in ''.join(cols) for r in ['D4', 'D5', 'D6', 'D3', 'D7'])
        return has_week and has_rin

    def _find_week_column(self, columns: List[str]) -> Optional[str]:
        for col in columns:
            u = str(col).upper()
            if 'WEEK' in u or 'DATE' in u:
                return col
        return None

    def _parse_row(self, row: pd.Series, week_col: str) -> Optional[Dict]:
        """Parse a single row into a normalized record; returns None if invalid."""
        try:
            week_str = str(row[week_col])
            date = pd.to_datetime(week_str, errors='coerce')
            if pd.isna(date):
                return None

            rin_d4 = self._extract_price(row, 'D4')
            rin_d5 = self._extract_price(row, 'D5')
            rin_d6 = self._extract_price(row, 'D6')
            rin_d3 = self._extract_price(row, 'D3')
            rin_d7 = self._extract_price(row, 'D7')

            if not any(self._is_valid_price(p) for p in [rin_d4, rin_d5, rin_d6, rin_d3, rin_d7] if p is not None):
                return None

            return {
                'date': date.date(),
                'rin_d4_price': rin_d4,
                'rin_d5_price': rin_d5,
                'rin_d6_price': rin_d6,
                'rin_d3_price': rin_d3,
                'rin_d7_price': rin_d7
            }
        except Exception as e:
            logger.debug(f"Row parse error: {e}")
            return None
    
    def _fetch_with_retries(self, url: str) -> Optional[Response]:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/119.0.0.0 Safari/537.36'
            )
        }
        for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
            try:
                resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
                resp.raise_for_status()
                return resp
            except (req_exceptions.Timeout, req_exceptions.ConnectionError) as e:
                logger.warning(f"Request attempt {attempt} failed: {e}")
                if attempt < REQUEST_RETRY_ATTEMPTS:
                    time.sleep(REQUEST_RETRY_SLEEP_SECONDS)
            except req_exceptions.HTTPError as e:
                logger.error(f"HTTP error {e}; aborting")
                return None
            except Exception as e:
                logger.error(f"Unexpected request error: {e}")
                if attempt < REQUEST_RETRY_ATTEMPTS:
                    time.sleep(REQUEST_RETRY_SLEEP_SECONDS)
        return None
    
    def load_to_bigquery(self, rin_data):
        """Load RIN data to BigQuery"""
        if not rin_data:
            logger.warning("No RIN data to load")
            return 0
        
        try:
            df = pd.DataFrame(rin_data)
            
            # Add metadata columns
            df['symbol'] = 'RIN_COMPOSITE'
            df['close'] = df['rin_d6_price'].fillna(0)  # Use D6 as primary price
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0
            df['source_name'] = 'EPA_SCRAPED'
            df['confidence_score'] = 0.85
            df['ingest_timestamp_utc'] = datetime.now(timezone.utc)
            df['provenance_uuid'] = [str(uuid.uuid4()) for _ in range(len(df))]
            
            # Convert date to datetime for BigQuery
            df['date'] = pd.to_datetime(df['date'])
            
            # Basic intra-batch dedupe by date to ensure idempotency
            before = len(df)
            df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
            after = len(df)
            if after < before:
                logger.info(f"De-duplicated {before - after} rows within batch (by date)")
            
            # Load to BigQuery (append mode)
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(df)} RIN price records to {table_id}")
            return len(df)
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def run(self):
        """Run RIN scraper"""
        logger.info("🚀 Starting EPA RIN prices scraper...")
        
        rin_data = self.scrape_rin_trades_page()
        
        if rin_data:
            rows_loaded = self.load_to_bigquery(rin_data)
            return {'status': 'SUCCESS', 'rows_loaded': rows_loaded}
        else:
            return {'status': 'NO_DATA', 'rows_loaded': 0}

if __name__ == "__main__":
    scraper = EPARINScraper()
    result = scraper.run()
    print(f"Result: {result}")

