#!/usr/bin/env python3
"""
Argentina Port Logistics Scraper
Scrapes Argentina port logistics data (vessel queues, port throughput)
Sources:
- Port of Rosario: https://www.bcr.com.ar/en/markets/grain-market
- TradingEconomics: https://tradingeconomics.com/argentina/container-port-traffic-teu-20-foot-equivalent-units-wb-data.html
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone, timedelta
import uuid
import logging
import time
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "argentina_crisis_tracker"

class ArgentinaPortLogisticsScraper:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def scrape_tradingeconomics(self):
        """Scrape TradingEconomics for Argentina port throughput"""
        url = "https://tradingeconomics.com/argentina/container-port-traffic-teu-20-foot-equivalent-units-wb-data.html"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Try to parse tables
            from io import StringIO
            tables = pd.read_html(StringIO(response.text))
            
            port_data = []
            for table in tables:
                # Look for port throughput data
                if any(col in str(table.columns).upper() for col in ['DATE', 'VALUE', 'TEU', 'CONTAINER']):
                    logger.info(f"Found port throughput table with {len(table)} rows")
                    
                    # Standardize columns
                    table.columns = [str(col).strip().upper() for col in table.columns]
                    
                    # Find date and value columns
                    date_col = None
                    value_col = None
                    for col in table.columns:
                        if 'DATE' in col:
                            date_col = col
                        elif 'VALUE' in col or 'TEU' in col:
                            value_col = col
                    
                    if date_col and value_col:
                        for _, row in table.iterrows():
                            try:
                                date_str = str(row[date_col])
                                date = pd.to_datetime(date_str, errors='coerce')
                                if pd.isna(date):
                                    continue
                                
                                value = row[value_col]
                                if pd.notna(value):
                                    try:
                                        teu = float(str(value).replace(',', ''))
                                        
                                        port_data.append({
                                            'date': date.date(),
                                            'argentina_port_throughput_teu': teu,
                                            'source_name': 'TRADINGECONOMICS_SCRAPED',
                                            'confidence_score': 0.80,
                                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                                            'provenance_uuid': str(uuid.uuid4())
                                        })
                                    except:
                                        pass
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
            
            logger.info(f"Extracted {len(port_data)} port throughput records")
            return port_data
            
        except Exception as e:
            logger.error(f"Error scraping TradingEconomics: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def scrape_port_rosario(self):
        """Scrape Port of Rosario vessel line-up (placeholder - may require Selenium)"""
        # Port of Rosario often requires JavaScript rendering
        # For now, return empty - can be enhanced with Selenium later
        logger.info("Port of Rosario scraping requires Selenium - skipping for now")
        return []
    
    def load_to_bigquery(self, port_data):
        """Load port logistics data to BigQuery"""
        if not port_data:
            logger.warning("No port logistics data to load")
            return 0
        
        try:
            df = pd.DataFrame(port_data)
            
            # Add required columns for argentina_crisis_tracker
            if 'argentina_export_tax' not in df.columns:
                df['argentina_export_tax'] = None
            if 'argentina_china_sales_mt' not in df.columns:
                df['argentina_china_sales_mt'] = None
            if 'argentina_competitive_threat' not in df.columns:
                df['argentina_competitive_threat'] = None
            if 'argentina_vessel_queue_count' not in df.columns:
                df['argentina_vessel_queue_count'] = None
            
            df['date'] = pd.to_datetime(df['date'])
            
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(port_data)} port logistics records to {table_id}")
            return len(port_data)
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def run(self):
        """Run Argentina port logistics scraper"""
        logger.info("🚀 Starting Argentina port logistics scraper...")
        
        port_data = self.scrape_tradingeconomics()
        # port_data.extend(self.scrape_port_rosario())  # Enable when Selenium ready
        
        if port_data:
            rows_loaded = self.load_to_bigquery(port_data)
            return {'status': 'SUCCESS', 'rows_loaded': rows_loaded}
        else:
            return {'status': 'NO_DATA', 'rows_loaded': 0}

if __name__ == "__main__":
    scraper = ArgentinaPortLogisticsScraper()
    result = scraper.run()
    print(f"Result: {result}")

