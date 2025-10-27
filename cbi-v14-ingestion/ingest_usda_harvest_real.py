#!/usr/bin/env python3
"""
Real USDA Harvest Data Ingestion
Gets actual soybean harvest progress from USDA API
"""

import requests
import json
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USDAHarvestIngestion:
    def __init__(self, project_id="cbi-v14"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.usda_key = "98AE1A55-11D0-304B-A5A5-F3FF61E86A31"
        
    def get_harvest_data(self):
        """Get soybean harvest progress from USDA API"""
        url = "https://quickstats.nass.usda.gov/api/api_GET"
        
        # Get current year harvest progress
        current_year = datetime.now().year
        
        params = {
            'key': self.usda_key,
            'commodity_desc': 'SOYBEANS',
            'statisticcat_desc': 'PROGRESS',
            'unit_desc': 'PCT PLANTED',
            'year': str(current_year),
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved {len(data.get('data', []))} harvest records")
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error fetching USDA data: {e}")
            return []
    
    def transform_harvest_data(self, raw_data):
        """Transform USDA data for BigQuery"""
        transformed = []
        current_year = datetime.now().year
        
        for record in raw_data:
            try:
                # Extract and clean data
                transformed_record = {
                    'harvest_date': record.get('week_ending', ''),
                    'state': record.get('state_name', ''),
                    'harvest_percentage': float(record.get('Value', 0)) if record.get('Value') else 0.0,
                    'year': int(record.get('year', current_year)),
                    'week': int(record.get('week_ending', '').split('-')[1]) if record.get('week_ending') else None,
                    'created_at': datetime.now().isoformat(),
                    'source': 'USDA_NASS'
                }
                transformed.append(transformed_record)
                
            except Exception as e:
                logger.warning(f"Error transforming record: {e}")
                continue
                
        return transformed
    
    def load_to_bigquery(self, data):
        """Load harvest data to BigQuery"""
        if not data:
            logger.warning("No data to load")
            return
            
        # Create table if it doesn't exist
        table_id = f"{self.project_id}.staging.usda_harvest_progress"
        
        # Define schema
        schema = [
            bigquery.SchemaField("harvest_date", "DATE"),
            bigquery.SchemaField("state", "STRING"),
            bigquery.SchemaField("harvest_percentage", "FLOAT64"),
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
            
            # Load data using insert_rows
            rows_to_insert = []
            for record in data:
                rows_to_insert.append(record)
            
            errors = self.client.insert_rows_json(table, rows_to_insert)
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
            else:
                logger.info(f"Successfully inserted {len(rows_to_insert)} rows")
            
            logger.info(f"Loaded {len(data)} harvest records to {table_id}")
            
        except Exception as e:
            logger.error(f"Error loading to BigQuery: {e}")
    
    def run(self):
        """Main execution"""
        logger.info("Starting USDA harvest data ingestion")
        
        # Get data
        raw_data = self.get_harvest_data()
        if not raw_data:
            logger.error("No harvest data retrieved")
            return
            
        # Transform data
        transformed_data = self.transform_harvest_data(raw_data)
        logger.info(f"Transformed {len(transformed_data)} records")
        
        # Load to BigQuery
        self.load_to_bigquery(transformed_data)
        
        logger.info("USDA harvest ingestion completed")

if __name__ == "__main__":
    ingester = USDAHarvestIngestion()
    ingester.run()
