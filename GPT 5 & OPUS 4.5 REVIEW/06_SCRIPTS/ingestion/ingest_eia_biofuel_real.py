#!/usr/bin/env python3
"""
Real EIA Biofuel Data Ingestion
Gets actual ethanol production from EIA API
"""

import requests
import json
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EIABiofuelIngestion:
    def __init__(self, project_id="cbi-v14"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.eia_key = "I4XUi5PYnAkfMXPU3GvchRsplERC65DWri1AApqs"
        
    def get_biofuel_data(self):
        """Get ethanol production from EIA API"""
        url = "https://api.eia.gov/v2/petroleum/cons/wpsup/data/"
        
        # Get ethanol production data for current year
        current_year = datetime.now().year
        
        params = {
            'api_key': self.eia_key,
            'frequency': 'weekly',
            'data[0]': 'value',
            'facets[product][]': 'EPOOXE',  # Ethanol production
            'start': f'{current_year}-01-01',
            'end': f'{current_year}-12-31',
            'offset': 0,
            'length': 50  # Get last 50 weeks
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            biofuel_data = data.get('response', {}).get('data', [])
            logger.info(f"Retrieved {len(biofuel_data)} biofuel records")
            return biofuel_data
            
        except Exception as e:
            logger.error(f"Error fetching EIA data: {e}")
            return []
    
    def transform_biofuel_data(self, raw_data):
        """Transform EIA data for BigQuery"""
        transformed = []
        
        for record in raw_data:
            try:
                # Extract and clean data
                transformed_record = {
                    'production_date': record.get('period', ''),
                    'product': record.get('product', ''),
                    'production_value': float(record.get('value', 0)) if record.get('value') else 0.0,
                    'units': record.get('units', 'thousand barrels'),
                    'year': int(record.get('period', '').split('-')[0]) if record.get('period') else None,
                    'week': int(record.get('period', '').split('-')[1]) if record.get('period') else None,
                    'created_at': datetime.now().isoformat(),
                    'source': 'EIA'
                }
                transformed.append(transformed_record)
                
            except Exception as e:
                logger.warning(f"Error transforming record: {e}")
                continue
                
        return transformed
    
    def load_to_bigquery(self, data):
        """Load biofuel data to BigQuery"""
        if not data:
            logger.warning("No data to load")
            return
            
        # Create table if it doesn't exist
        table_id = f"{self.project_id}.staging.eia_biofuel_production"
        
        # Define schema
        schema = [
            bigquery.SchemaField("production_date", "DATE"),
            bigquery.SchemaField("product", "STRING"),
            bigquery.SchemaField("production_value", "FLOAT64"),
            bigquery.SchemaField("units", "STRING"),
            bigquery.SchemaField("year", "INTEGER"),
            bigquery.SchemaField("week", "INTEGER"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("source", "STRING")
        ]
        
        try:
            # Create table
            table = bigquery.Table(table_id, schema=schema)
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Table {table_id} ready")
            
            # Load data
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # Replace data
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
            )
            
            # Convert to JSON lines
            json_data = [json.dumps(record) for record in data]
            
            job = self.client.load_table_from_file(
                json_data, table_id, job_config=job_config
            )
            job.result()  # Wait for completion
            
            logger.info(f"Loaded {len(data)} biofuel records to {table_id}")
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
    
    def run(self):
        """Main execution"""
        logger.info("Starting EIA biofuel data ingestion")
        
        # Get data
        raw_data = self.get_biofuel_data()
        if not raw_data:
            logger.error("No biofuel data retrieved")
            return
            
        # Transform data
        transformed_data = self.transform_biofuel_data(raw_data)
        logger.info(f"Transformed {len(transformed_data)} records")
        
        # Load to BigQuery
        self.load_to_bigquery(transformed_data)
        
        logger.info("EIA biofuel ingestion completed")

if __name__ == "__main__":
    ingester = EIABiofuelIngestion()
    ingester.run()
