#!/usr/bin/env python3
"""
EPA RFS Mandates Scraper
Scrapes EPA Renewable Fuel Standard (RFS) mandate volumes
Sources:
- Final Rule 2023-2025: https://www.epa.gov/renewable-fuel-standard/final-renewable-fuels-standards-rule-2023-2024-and-2025
- Annual Standards: https://www.epa.gov/renewable-fuel-standard/renewable-fuel-annual-standards
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone
import uuid
import logging
import time
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "biofuel_policy"

class EPARFSMandateScraper:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def scrape_annual_standards(self):
        """Scrape EPA annual RFS standards"""
        url = "https://www.epa.gov/renewable-fuel-standard/renewable-fuel-annual-standards"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Try to parse tables
            from io import StringIO
            tables = pd.read_html(StringIO(response.text))
            
            rfs_data = []
            for table in tables:
                # Look for RFS mandate table
                if any(col in str(table.columns).upper() for col in ['BIODIESEL', 'ADVANCED', 'TOTAL', 'YEAR']):
                    logger.info(f"Found RFS mandate table with {len(table)} rows")
                    
                    # Standardize columns
                    table.columns = [str(col).strip().upper() for col in table.columns]
                    
                    # Find year and mandate columns
                    year_col = None
                    for col in table.columns:
                        if 'YEAR' in col:
                            year_col = col
                            break
                    
                    if year_col:
                        for _, row in table.iterrows():
                            try:
                                year = int(row[year_col]) if pd.notna(row[year_col]) else None
                                if not year:
                                    continue
                                
                                # Extract mandate volumes
                                biodiesel = self._extract_mandate(row, 'BIODIESEL', 'BIOMASS')
                                advanced = self._extract_mandate(row, 'ADVANCED')
                                total = self._extract_mandate(row, 'TOTAL', 'RENEWABLE')
                                
                                if any([biodiesel, advanced, total]):
                                    # Use Jan 1 of the year as date
                                    date = datetime(year, 1, 1).date()
                                    
                                    rfs_data.append({
                                        'date': date,
                                        'policy_type': 'RFS_MANDATE',
                                        'mandate_volume': total or 0,
                                        'rfs_mandate_biodiesel': biodiesel,
                                        'rfs_mandate_advanced': advanced,
                                        'rfs_mandate_total': total,
                                        'compliance_status': 'ACTIVE',
                                        'region': 'US',
                                        'source_name': 'EPA_RFS_SCRAPED',
                                        'confidence_score': 0.90,
                                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                                        'provenance_uuid': str(uuid.uuid4()),
                                        'policy_text': f'RFS Annual Standard {year}'
                                    })
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
            
            logger.info(f"Extracted {len(rfs_data)} RFS mandate records")
            return rfs_data
            
        except Exception as e:
            logger.error(f"Error scraping RFS standards: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _extract_mandate(self, row, *keywords):
        """Extract mandate volume from row"""
        for col in row.index:
            col_upper = str(col).upper()
            if any(kw in col_upper for kw in keywords):
                value = row[col]
                if pd.notna(value):
                    try:
                        # Remove commas, convert to float (billion gallons)
                        vol_str = str(value).replace(',', '').strip()
                        return float(vol_str)
                    except:
                        pass
        return None
    
    def load_to_bigquery(self, rfs_data):
        """Load RFS data to BigQuery"""
        if not rfs_data:
            logger.warning("No RFS data to load")
            return 0
        
        try:
            df = pd.DataFrame(rfs_data)
            df['date'] = pd.to_datetime(df['date'])
            
            table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema_update_options=['ALLOW_FIELD_ADDITION']
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(rfs_data)} RFS mandate records to {table_id}")
            return len(rfs_data)
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def run(self):
        """Run RFS mandate scraper"""
        logger.info("🚀 Starting EPA RFS mandates scraper...")
        
        rfs_data = self.scrape_annual_standards()
        
        if rfs_data:
            rows_loaded = self.load_to_bigquery(rfs_data)
            return {'status': 'SUCCESS', 'rows_loaded': rows_loaded}
        else:
            return {'status': 'NO_DATA', 'rows_loaded': 0}

if __name__ == "__main__":
    scraper = EPARFSMandateScraper()
    result = scraper.run()
    print(f"Result: {result}")

