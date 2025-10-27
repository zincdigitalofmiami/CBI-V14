#!/usr/bin/env python3
"""
USDA CROP PROGRESS API SCRAPER
Real harvest pace data for academic rigor

Sources:
- USDA NASS QuickStats API: https://quickstats.nass.usda.gov/api
- Weekly crop progress reports
- Normalized harvest pace vs 5-year average
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USDAHarvestScraper:
    def __init__(self, project_id='cbi-v14'):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.base_url = "https://quickstats.nass.usda.gov/api"
        
        # USDA API parameters for harvest progress
        self.harvest_params = {
            'key': 'YOUR_API_KEY',  # Need to get USDA API key
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'group_desc': 'FIELD CROPS',
            'commodity_desc': 'SOYBEANS',
            'class_desc': 'ALL CLASSES',
            'prodn_practice_desc': 'ALL PRODUCTION PRACTICES',
            'util_practice_desc': 'ALL UTILIZATION PRACTICES',
            'statisticcat_desc': 'PROGRESS',
            'unit_desc': 'PCT HARVESTED',
            'freq_desc': 'WEEKLY',
            'reference_period_desc': 'YEAR'
        }
    
    def get_soybean_harvest_progress(self, year=2025):
        """Get current soybean harvest progress from USDA"""
        params = self.harvest_params.copy()
        params['year'] = year
        
        try:
            response = requests.get(f"{self.base_url}/api_GET", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data:
                df = pd.DataFrame(data['data'])
                logger.info(f"Retrieved {len(df)} USDA harvest progress records")
                return df
            else:
                logger.warning("No harvest progress data in USDA response")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching USDA harvest data: {e}")
            return pd.DataFrame()
    
    def calculate_harvest_pace_vs_average(self, current_df):
        """Calculate current harvest pace vs 5-year average"""
        if current_df.empty:
            return None
            
        try:
            # Get 5-year historical average for same week
            historical_data = []
            current_week = datetime.now().isocalendar()[1]
            
            for year in range(2019, 2024):  # 5-year average
                hist_params = self.harvest_params.copy()
                hist_params['year'] = year
                
                response = requests.get(f"{self.base_url}/api_GET", params=hist_params, timeout=30)
                if response.status_code == 200:
                    hist_data = response.json()
                    if 'data' in hist_data:
                        historical_data.extend(hist_data['data'])
                
                time.sleep(0.5)  # Rate limiting
            
            if not historical_data:
                logger.warning("No historical harvest data available")
                return None
            
            hist_df = pd.DataFrame(historical_data)
            
            # Calculate 5-year average for current week
            hist_df['week'] = pd.to_datetime(hist_df['week_ending']).dt.isocalendar().week
            current_week_avg = hist_df[hist_df['week'] == current_week]['Value'].mean()
            
            # Get current week progress
            current_df['week'] = pd.to_datetime(current_df['week_ending']).dt.isocalendar().week
            current_progress = current_df[current_df['week'] == current_week]['Value'].iloc[0]
            
            # Calculate ratio (current vs 5-year average)
            if current_week_avg > 0:
                harvest_pace_ratio = current_progress / current_week_avg
                return {
                    'current_progress': current_progress,
                    'historical_average': current_week_avg,
                    'harvest_pace_ratio': min(harvest_pace_ratio, 1.5),  # Cap at 1.5
                    'week': current_week
                }
            
        except Exception as e:
            logger.error(f"Error calculating harvest pace ratio: {e}")
            
        return None
    
    def scrape_and_load(self):
        """Main scraping and loading function"""
        logger.info("🚜 Starting USDA harvest progress scraping")
        
        # Get current soybean harvest progress
        current_data = self.get_soybean_harvest_progress()
        
        if current_data.empty:
            logger.error("No current harvest data available")
            return
        
        # Calculate vs historical average
        harvest_analysis = self.calculate_harvest_pace_vs_average(current_data)
        
        if not harvest_analysis:
            logger.error("Could not calculate harvest pace ratio")
            return
        
        # Prepare data for BigQuery
        rows = []
        for _, row in current_data.iterrows():
            rows.append({
                'date': datetime.now().date(),
                'region': row.get('state_name', 'United States'),
                'crop': 'SOYBEANS',
                'progress_pct': float(row.get('Value', 0)),
                'progress_type': 'HARVESTED',
                'vs_5yr_avg': harvest_analysis['harvest_pace_ratio'],
                'historical_avg': harvest_analysis['historical_average'],
                'week_number': harvest_analysis['week'],
                'source_name': 'USDA_NASS_API',
                'confidence_score': 0.98,
                'ingest_timestamp_utc': datetime.utcnow(),
                'provenance_uuid': f"usda_harvest_{int(datetime.now().timestamp())}"
            })
        
        if rows:
            df = pd.DataFrame(rows)
            
            # Load to BigQuery
            table_id = f"{self.project_id}.staging.usda_harvest_progress"
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                schema=[
                    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                    bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("crop", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("progress_pct", "FLOAT", mode="REQUIRED"),
                    bigquery.SchemaField("progress_type", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("vs_5yr_avg", "FLOAT", mode="REQUIRED"),
                    bigquery.SchemaField("historical_avg", "FLOAT"),
                    bigquery.SchemaField("week_number", "INTEGER"),
                    bigquery.SchemaField("source_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("confidence_score", "FLOAT"),
                    bigquery.SchemaField("ingest_timestamp_utc", "TIMESTAMP"),
                    bigquery.SchemaField("provenance_uuid", "STRING")
                ]
            )
            
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            
            logger.info(f"✅ Loaded {len(df)} USDA harvest progress records")
            logger.info(f"Current harvest pace vs 5-year avg: {harvest_analysis['harvest_pace_ratio']:.3f}")
            
            return harvest_analysis
        
        return None


if __name__ == "__main__":
    scraper = USDAHarvestScraper()
    result = scraper.scrape_and_load()
    
    if result:
        print("=" * 60)
        print("USDA HARVEST PROGRESS ANALYSIS")
        print("=" * 60)
        print(f"Current Progress: {result['current_progress']:.1f}%")
        print(f"5-Year Average: {result['historical_average']:.1f}%")
        print(f"Harvest Pace Ratio: {result['harvest_pace_ratio']:.3f}")
        print(f"Week: {result['week']}")
        
        if result['harvest_pace_ratio'] < 0.8:
            print("⚠️  HARVEST PACE BELOW NORMAL - SUPPLY CONCERNS")
        elif result['harvest_pace_ratio'] > 1.2:
            print("✅ HARVEST PACE ABOVE NORMAL - AMPLE SUPPLY")
        else:
            print("📊 HARVEST PACE NORMAL")
    else:
        print("❌ Failed to get USDA harvest data")
