#!/usr/bin/env python3
"""
CBI-V14 Baltic Dry Index Ingestion
Pulls global shipping costs data for trade activity monitoring
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import pandas as pd
import time
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

class BalticDryIndexCollector:
    """Collect Baltic Dry Index data for shipping cost monitoring"""

    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        # Baltic Exchange API or alternative sources
        self.sources = [
            {
                'name': 'tradingeconomics',
                'url': 'https://api.tradingeconomics.com/markets/historical?c=guest:guest&ind=BDI:IND',
                'frequency': 'daily'
            },
            {
                'name': 'investing_com',
                'url': 'https://api.investing.com/api/financialdata/BDI/historical',
                'frequency': 'daily'
            }
        ]

    def fetch_baltic_data(self) -> pd.DataFrame:
        """Fetch Baltic Dry Index data from multiple sources"""
        all_data = []
        
        # Try web scraping from public sources (no API key required)
        sources_to_try = [
            self._fetch_from_investing_com,
            self._fetch_from_marketwatch,
        ]
        
        for fetch_func in sources_to_try:
            try:
                logger.info(f"Attempting to fetch Baltic data from {fetch_func.__name__}")
                data = fetch_func()
                if data and not data.empty:
                    all_data.append(data)
                    logger.info(f"✅ Successfully fetched from {fetch_func.__name__}")
                    break  # Use first successful source
            except Exception as e:
                logger.warning(f"Failed to fetch from {fetch_func.__name__}: {e}")
                time.sleep(2)  # Rate limiting between failed attempts
                continue
        
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
            # Remove duplicates by date (keep first)
            df = df.drop_duplicates(subset=['date'], keep='first')
            logger.info(f"Collected {len(df)} Baltic Dry Index records")
            return df
        else:
            logger.error("❌ No Baltic data collected from any source")
            logger.warning("⚠️  Consider implementing Trading Economics API with credentials")
            return pd.DataFrame()
    
    def _fetch_from_investing_com(self) -> pd.DataFrame:
        """Fetch BDI from Investing.com (web scraping)"""
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.investing.com/indices/baltic-dry"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for current BDI value (Investing.com structure)
            bdi_value = None
            bdi_change = None
            bdi_change_pct = None
            
            # Try multiple selectors for BDI value
            value_selectors = [
                '#last_last',
                '.text-2xl',
                '[data-test="instrument-price-last"]',
                '.instrument-price_last__'
            ]
            
            for selector in value_selectors:
                elem = soup.select_one(selector)
                if elem:
                    try:
                        bdi_value = float(elem.get_text().replace(',', ''))
                        break
                    except:
                        continue
            
            # Try to find change
            change_elem = soup.select_one('[data-test="instrument-price-change"]')
            if change_elem:
                change_text = change_elem.get_text()
                try:
                    bdi_change = float(change_text.split()[0])
                    if '%' in change_text:
                        bdi_change_pct = float(change_text.split()[1].replace('%', '').replace('(', '').replace(')', ''))
                except:
                    pass
            
            if bdi_value and 300 <= bdi_value <= 4000:  # Validate range
                return pd.DataFrame([{
                    'date': datetime.now().date(),
                    'bdi_value': bdi_value,
                    'bdi_change': bdi_change or 0.0,
                    'bdi_change_pct': bdi_change_pct or 0.0,
                    'source': 'investing_com',
                    'timestamp': datetime.utcnow()
                }])
            else:
                logger.warning(f"BDI value out of range: {bdi_value}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching from Investing.com: {e}")
            return pd.DataFrame()
    
    def _fetch_from_marketwatch(self) -> pd.DataFrame:
        """Fetch BDI from MarketWatch (web scraping fallback)"""
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.marketwatch.com/investing/index/bdi"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # MarketWatch structure
            value_elem = soup.select_one('.intraday__price, .value')
            if value_elem:
                try:
                    bdi_value = float(value_elem.get_text().replace(',', ''))
                    if 300 <= bdi_value <= 4000:
                        return pd.DataFrame([{
                            'date': datetime.now().date(),
                            'bdi_value': bdi_value,
                            'bdi_change': 0.0,  # MarketWatch may not show change
                            'bdi_change_pct': 0.0,
                            'source': 'marketwatch',
                            'timestamp': datetime.utcnow()
                        }])
                except:
                    pass
            
            return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching from MarketWatch: {e}")
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate Baltic data quality"""
        if df.empty:
            return df

        # Validate BDI range (historical range: ~300-4000)
        df = df[df['bdi_value'].between(300, 4000)]

        # Remove duplicates by date
        df = df.drop_duplicates(subset=['date'])

        # Add metadata
        df['ingest_timestamp'] = datetime.utcnow()
        df['data_quality_score'] = 0.85  # High quality shipping data

        return df

    def store_to_bigquery(self, df: pd.DataFrame) -> bool:
        """Store validated data to BigQuery"""
        if df.empty:
            logger.info("No new Baltic data to store")
            return True

        try:
            # Store to both existing table and new freight_logistics table
            table_id_legacy = f"{PROJECT_ID}.forecasting_data_warehouse.baltic_dry_index"
            table_id_new = f"{PROJECT_ID}.forecasting_data_warehouse.freight_logistics"
            
            # Prepare data for new freight_logistics table
            freight_df = df.copy()
            freight_df['baltic_dry_index'] = freight_df['bdi_value']
            freight_df['freight_soybean_mentions'] = 0  # Can be enhanced with FreightWaves scraping
            freight_df['source_name'] = 'BALTIC_EXCHANGE'
            freight_df['confidence_score'] = 0.90
            freight_df['ingest_timestamp_utc'] = pd.to_datetime(freight_df['ingest_timestamp'])
            freight_df['provenance_uuid'] = [str(uuid.uuid4()) for _ in range(len(freight_df))]
            freight_df = freight_df[['date', 'baltic_dry_index', 'freight_soybean_mentions', 'source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']]
            
            # Store to new table
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            job = self.client.load_table_from_dataframe(freight_df, table_id_new, job_config=job_config)
            job.result()
            logger.info(f"✅ Loaded {len(freight_df)} records to {table_id_new}")
            
            # Also store to legacy table if it exists
            table_id = table_id_legacy

            # Check for duplicates
            existing_dates = set()
            try:
                query = f"SELECT DISTINCT date FROM `{table_id}` WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
                existing = self.client.query(query).to_dataframe()
                existing_dates = set(existing['date'].dt.date) if not existing.empty else set()
            except:
                pass  # Table might not exist yet

            # Filter out existing dates
            df['date_only'] = df['date'].dt.date
            df = df[~df['date_only'].isin(existing_dates)]
            df = df.drop('date_only', axis=1)

            if df.empty:
                logger.info("All Baltic data already exists")
                return True

            # Store new data
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()

            logger.info(f"✅ Stored {len(df)} Baltic Dry Index records")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to store Baltic data: {e}")
            return False

    def run_collection(self) -> bool:
        """Run complete Baltic data collection pipeline"""
        logger.info("🚢 Starting Baltic Dry Index collection...")

        # Fetch data
        raw_data = self.fetch_baltic_data()
        if raw_data.empty:
            return False

        # Validate data
        validated_data = self.validate_data(raw_data)

        # Store data
        success = self.store_to_bigquery(validated_data)

        logger.info("✅ Baltic Dry Index collection complete" if success else "❌ Baltic collection failed")
        return success

if __name__ == "__main__":
    collector = BalticDryIndexCollector()
    success = collector.run_collection()
    exit(0 if success else 1)


