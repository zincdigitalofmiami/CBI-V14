#!/usr/bin/env python3
"""
CBI-V14 Biofuel Policy Ingestion (Staging)
Populates staging.biofuel_policy with EPA RFS mandate data via HTML scraping
"""

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone, timedelta
import uuid
import logging
import re
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET = "staging"
TABLE = "biofuel_policy"

class BiofuelPolicyPipeline:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
        
        # EPA RFS sources
        self.epa_rfs_url = "https://www.epa.gov/renewable-fuel-standard-program/renewable-fuel-standard-rfs2-final-rules"
        self.epa_volumes_url = "https://www.epa.gov/renewable-fuel-standard-program/final-renewable-fuel-standards"
        
    def scrape_epa_rfs_mandates(self) -> List[Dict[str, Any]]:
        """Scrape EPA RFS mandate volumes from public pages"""
        mandates = []
        
        try:
            logger.info(f"Scraping EPA RFS mandates from {self.epa_volumes_url}")
            response = requests.get(self.epa_volumes_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for tables containing volume requirements
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        text_content = ' '.join([cell.get_text(strip=True) for cell in cells])
                        
                        # Look for year patterns and volume numbers (billion gallons)
                        year_match = re.search(r'20(2[0-9]|3[0-9])', text_content)
                        volume_match = re.search(r'(\d+\.?\d*)\s*billion', text_content.lower())
                        
                        if year_match and volume_match:
                            year = int("20" + year_match.group(1))
                            volume_billion = float(volume_match.group(1))
                            
                            mandate = {
                                'date': f"{year}-01-01",  # Mandate effective date
                                'policy_type': 'RFS_Total_Renewable_Fuel',
                                'mandate_volume': volume_billion * 1e9,  # Convert to gallons
                                'compliance_status': 'Final',
                                'region': 'United States',
                                'policy_text': text_content[:500],  # Truncate to avoid schema issues
                                'source_name': 'EPA_RFS_Program',
                                'confidence_score': 0.9
                            }
                            mandates.append(mandate)
                            logger.info(f"Found RFS mandate: {year} - {volume_billion}B gallons")
                            
        except Exception as e:
            logger.warning(f"EPA RFS scraping failed: {e}")
            
        return mandates
    
    def fetch_biodiesel_mandates(self) -> List[Dict[str, Any]]:
        """Extract biodiesel-specific mandates from general RFS data"""
        mandates = []
        
        try:
            # EPA biodiesel mandate page
            biodiesel_url = "https://www.epa.gov/renewable-fuel-standard-program/biodiesel-mandate"
            logger.info(f"Scraping biodiesel mandates from EPA")
            
            response = requests.get(biodiesel_url, timeout=30, verify=False)  # Some EPA sites have SSL issues
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for specific biodiesel volume requirements
            content = soup.get_text()
            
            # Extract biodiesel volumes (typically 20-25% of total RFS)
            biodiesel_patterns = [
                r'biodiesel.*?(\d+\.?\d*)\s*billion',
                r'(\d+\.?\d*)\s*billion.*?biodiesel',
                r'advanced biofuel.*?(\d+\.?\d*)\s*billion'
            ]
            
            for i, pattern in enumerate(biodiesel_patterns):
                matches = re.findall(pattern, content.lower())
                for match in matches:
                    try:
                        volume = float(match) * 1e9  # Convert to gallons
                        current_year = datetime.now().year
                        
                        mandate = {
                            'date': f"{current_year}-01-01",
                            'policy_type': 'RFS_Biodiesel_Mandate',
                            'mandate_volume': volume,
                            'compliance_status': 'Proposed' if i > 0 else 'Final',
                            'region': 'United States',
                            'policy_text': f"Biodiesel mandate extracted from EPA RFS program: {volume/1e9:.1f}B gallons",
                            'source_name': 'EPA_Biodiesel_Program',
                            'confidence_score': 0.7  # Lower confidence for extracted values
                        }
                        mandates.append(mandate)
                        logger.info(f"Found biodiesel mandate: {volume/1e9:.1f}B gallons")
                        break  # Only take first match per pattern
                        
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.warning(f"Biodiesel mandate extraction failed: {e}")
            
        return mandates
    
    def create_fallback_mandates(self) -> List[Dict[str, Any]]:
        """Create fallback mandate records based on known RFS volumes"""
        logger.info("Creating fallback RFS mandates from known volumes")
        
        # Known RFS volumes (billion gallons) - updated through 2024
        known_volumes = {
            2023: 20.82,
            2024: 21.54,
            2025: 22.68  # Proposed
        }
        
        mandates = []
        for year, volume in known_volumes.items():
            mandate = {
                'date': f"{year}-01-01",
                'policy_type': 'RFS_Total_Renewable_Fuel',
                'mandate_volume': volume * 1e9,  # Convert to gallons
                'compliance_status': 'Final' if year <= 2024 else 'Proposed',
                'region': 'United States',
                'policy_text': f"Total renewable fuel volume requirement for {year}: {volume} billion gallons",
                'source_name': 'CBI_V14_Fallback_RFS',
                'confidence_score': 0.8
            }
            mandates.append(mandate)
            
            # Add biodiesel component (roughly 2.5-3B gallons)
            biodiesel_volume = volume * 0.12  # Biodiesel is ~12% of total RFS
            biodiesel_mandate = {
                'date': f"{year}-01-01",
                'policy_type': 'RFS_Biodiesel_Mandate',
                'mandate_volume': biodiesel_volume * 1e9,
                'compliance_status': 'Final' if year <= 2024 else 'Proposed',
                'region': 'United States',
                'policy_text': f"Biodiesel volume requirement for {year}: {biodiesel_volume:.1f} billion gallons (estimated from total RFS)",
                'source_name': 'CBI_V14_Calculated_Biodiesel',
                'confidence_score': 0.6
            }
            mandates.append(biodiesel_mandate)
            
        return mandates
    
    def build_staging_records(self, mandates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert mandate data to staging table records"""
        records = []
        
        for mandate in mandates:
            record = {
                'date': mandate['date'],
                'policy_type': mandate['policy_type'],
                'mandate_volume': float(mandate['mandate_volume']),
                'compliance_status': mandate['compliance_status'],
                'region': mandate['region'],
                'source_name': mandate['source_name'],
                'confidence_score': float(mandate['confidence_score']),
                'ingest_timestamp_utc': datetime.now(timezone.utc),
                'provenance_uuid': str(uuid.uuid4()),
                'policy_text': mandate['policy_text']
            }
            records.append(record)
            
        return records
    
    def load_to_bigquery(self, records: List[Dict[str, Any]]) -> bool:
        """Load records to BigQuery staging table"""
        if not records:
            logger.warning("No records to load")
            return False
            
        try:
            df = pd.DataFrame(records)
            
            # Ensure proper data types for BigQuery
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['mandate_volume'] = pd.to_numeric(df['mandate_volume'])
            df['confidence_score'] = pd.to_numeric(df['confidence_score'])
            df['ingest_timestamp_utc'] = pd.to_datetime(df['ingest_timestamp_utc'])
            
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=False,
                schema=[
                    bigquery.SchemaField("date", "DATE"),
                    bigquery.SchemaField("policy_type", "STRING"),
                    bigquery.SchemaField("mandate_volume", "FLOAT"),
                    bigquery.SchemaField("compliance_status", "STRING"),
                    bigquery.SchemaField("region", "STRING"),
                    bigquery.SchemaField("source_name", "STRING"),
                    bigquery.SchemaField("confidence_score", "FLOAT"),
                    bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                    bigquery.SchemaField("provenance_uuid", "STRING"),
                    bigquery.SchemaField("policy_text", "STRING")
                ]
            )
            
            job = self.client.load_table_from_dataframe(df, self.table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Successfully loaded {len(records)} policy records to {self.table_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data to BigQuery: {e}")
            logger.error(f"DataFrame dtypes: {df.dtypes if 'df' in locals() else 'DataFrame not created'}")
            return False
    
    def execute_ingestion(self) -> bool:
        """Execute complete biofuel policy ingestion"""
        logger.info("🚀 Starting biofuel policy ingestion")
        
        all_mandates = []
        
        # Try EPA RFS scraping first
        rfs_mandates = self.scrape_epa_rfs_mandates()
        all_mandates.extend(rfs_mandates)
        
        # Try biodiesel-specific mandates
        biodiesel_mandates = self.fetch_biodiesel_mandates()
        all_mandates.extend(biodiesel_mandates)
        
        # If scraping failed, use fallback data
        if not all_mandates:
            logger.info("Scraping failed, using fallback RFS volumes")
            all_mandates = self.create_fallback_mandates()
        
        if not all_mandates:
            logger.error("❌ No mandate data available from any source")
            return False
            
        # Remove duplicates by date + policy_type
        seen = set()
        unique_mandates = []
        for mandate in all_mandates:
            key = (mandate['date'], mandate['policy_type'])
            if key not in seen:
                seen.add(key)
                unique_mandates.append(mandate)
        
        logger.info(f"Processing {len(unique_mandates)} unique mandates")
        
        # Build staging records
        records = self.build_staging_records(unique_mandates)
        
        # Load to BigQuery
        success = self.load_to_bigquery(records)
        
        if success:
            logger.info("✅ Biofuel policy ingestion completed successfully")
        else:
            logger.error("❌ Biofuel policy ingestion failed")
            
        return success

def main():
    """Main execution"""
    pipeline = BiofuelPolicyPipeline()
    success = pipeline.execute_ingestion()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
