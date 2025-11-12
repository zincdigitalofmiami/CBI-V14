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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "biofuel_prices"

class EPARINScraper:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.base_url = "https://www.epa.gov"
        
    def scrape_rin_trades_page(self):
        """Scrape RIN trades and price information page"""
        url = "https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rin-trades-and-price-information"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find table with RIN prices
            # EPA typically has tables with Week Ending, D4, D5, D6, D3, D7 columns
            from io import StringIO
            tables = pd.read_html(StringIO(response.text))
            
            rin_data = []
            for table in tables:
                # Look for RIN price table (has D4, D5, D6 columns)
                if any(col in str(table.columns).upper() for col in ['D4', 'D5', 'D6', 'WEEK']):
                    logger.info(f"Found RIN price table with {len(table)} rows")
                    
                    # Standardize column names
                    table.columns = [str(col).strip().upper() for col in table.columns]
                    
                    # Find week ending and price columns
                    week_col = None
                    for col in table.columns:
                        if 'WEEK' in col or 'DATE' in col:
                            week_col = col
                            break
                    
                    if week_col:
                        for _, row in table.iterrows():
                            try:
                                week_str = str(row[week_col])
                                # Parse date
                                date = pd.to_datetime(week_str, errors='coerce')
                                if pd.isna(date):
                                    continue
                                
                                # Extract RIN prices (D4, D5, D6, D3, D7)
                                rin_d4 = self._extract_price(row, 'D4')
                                rin_d5 = self._extract_price(row, 'D5')
                                rin_d6 = self._extract_price(row, 'D6')
                                rin_d3 = self._extract_price(row, 'D3')
                                rin_d7 = self._extract_price(row, 'D7')
                                
                                if any([rin_d4, rin_d5, rin_d6, rin_d3, rin_d7]):
                                    rin_data.append({
                                        'date': date.date(),
                                        'rin_d4_price': rin_d4,
                                        'rin_d5_price': rin_d5,
                                        'rin_d6_price': rin_d6,
                                        'rin_d3_price': rin_d3,
                                        'rin_d7_price': rin_d7
                                    })
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
            
            logger.info(f"Extracted {len(rin_data)} RIN price records")
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
                        return float(price_str)
                    except:
                        pass
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
            
            # Load to BigQuery (append mode)
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(rin_data)} RIN price records to {table_id}")
            return len(rin_data)
            
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

