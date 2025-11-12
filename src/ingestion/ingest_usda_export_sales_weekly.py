#!/usr/bin/env python3
"""
USDA Export Sales Weekly Scraper
Scrapes USDA FAS weekly export sales data for China soybean imports
Sources:
- Weekly Export Sales: https://apps.fas.usda.gov/export-sales/h801.htm
- Complete Report: https://apps.fas.usda.gov/export-sales/complete.htm
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
TABLE_ID = "china_soybean_imports"

class USDAExportSalesScraper:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def scrape_weekly_report(self):
        """Scrape USDA weekly export sales report"""
        url = "https://apps.fas.usda.gov/export-sales/complete.htm"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Try to parse tables
            from io import StringIO
            tables = pd.read_html(StringIO(response.text))
            
            china_data = []
            for table in tables:
                # Look for China soybean data
                if any(col in str(table.columns).upper() for col in ['CHINA', 'SOYBEAN', 'COUNTRY', 'NET SALES', 'CANCELLATIONS']):
                    logger.info(f"Found export sales table with {len(table)} rows")
                    
                    # Standardize columns
                    table.columns = [str(col).strip().upper() for col in table.columns]
                    
                    # Find China rows
                    for _, row in table.iterrows():
                        try:
                            country = str(row.get('COUNTRY', '')).upper()
                            commodity = str(row.get('COMMODITY', '')).upper()
                            
                            if 'CHINA' in country and 'SOYBEAN' in commodity:
                                # Extract week ending date
                                week_col = None
                                for col in row.index:
                                    if 'WEEK' in str(col).upper() or 'DATE' in str(col).upper():
                                        week_col = col
                                        break
                                
                                week_str = str(row[week_col]) if week_col else None
                                date = pd.to_datetime(week_str, errors='coerce') if week_str else datetime.now().date()
                                
                                if pd.isna(date):
                                    date = datetime.now().date()
                                else:
                                    date = date.date()
                                
                                # Extract sales and cancellations
                                net_sales = self._extract_value(row, 'NET SALES', 'SALES')
                                cancellations = self._extract_value(row, 'CANCELLATIONS', 'CANCEL')
                                
                                if net_sales or cancellations:
                                    china_data.append({
                                        'date': date,
                                        'china_weekly_cancellations_mt': cancellations or 0,
                                        'source_name': 'USDA_FAS_SCRAPED',
                                        'confidence_score': 0.90,
                                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                                        'provenance_uuid': str(uuid.uuid4())
                                    })
                        except Exception as e:
                            logger.warning(f"Error parsing row: {e}")
                            continue
            
            logger.info(f"Extracted {len(china_data)} China export sales records")
            return china_data
            
        except Exception as e:
            logger.error(f"Error scraping USDA export sales: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _extract_value(self, row, *keywords):
        """Extract numeric value from row"""
        for col in row.index:
            col_upper = str(col).upper()
            if any(kw in col_upper for kw in keywords):
                value = row[col]
                if pd.notna(value):
                    try:
                        # Remove commas, convert to float (metric tons)
                        val_str = str(value).replace(',', '').strip()
                        return float(val_str)
                    except:
                        pass
        return None
    
    def load_to_bigquery(self, china_data):
        """Load China export sales data to BigQuery"""
        if not china_data:
            logger.warning("No China export sales data to load")
            return 0
        
        try:
            df = pd.DataFrame(china_data)
            df['date'] = pd.to_datetime(df['date'])
            
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(china_data)} China export sales records to {table_id}")
            return len(china_data)
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def run(self):
        """Run USDA export sales scraper"""
        logger.info("🚀 Starting USDA export sales scraper...")
        
        china_data = self.scrape_weekly_report()
        
        if china_data:
            rows_loaded = self.load_to_bigquery(china_data)
            return {'status': 'SUCCESS', 'rows_loaded': rows_loaded}
        else:
            return {'status': 'NO_DATA', 'rows_loaded': 0}

if __name__ == "__main__":
    scraper = USDAExportSalesScraper()
    result = scraper.run()
    print(f"Result: {result}")

