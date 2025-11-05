#!/usr/bin/env python3
"""
Glide API Integration - Vegas Customer & Restaurant Data
Pulls real data from Glide App API for customers, restaurants, and fryers
NO FAKE DATA - ONLY REAL DATA FROM GLIDE API

🚨 CRITICAL: GLIDE IS READ ONLY 🚨
- This script ONLY READS data from Glide API (no writes)
- Glide = US Oil Solutions production system - DO NOT TOUCH
- We query data, load to BigQuery, NEVER write back to Glide
- Data flow: Glide (READ ONLY) → BigQuery → Dashboard
"""

import pandas as pd
import requests
from google.cloud import bigquery
import json
from datetime import datetime
from typing import List, Dict, Any
import os

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

# Glide API Configuration (UPDATED - New App ID and 8 data sources)
GLIDE_API_ENDPOINT = "https://api.glideapp.io/api/function/queryTables"
GLIDE_APP_ID = "6262JQJdNjhra79M25e4"  # NEW App ID
GLIDE_BEARER_TOKEN = os.getenv('GLIDE_BEARER_TOKEN', '460c9ee4-edcb-43cc-86b5-929e2bb94351')

# Glide Table IDs (8 data sources - LOCKED CONFIGURATION)
GLIDE_TABLES = {
    'restaurants': 'native-table-ojIjQjDcDAEOpdtZG5Ao',
    'casinos': 'native-table-Gy2xHsC7urEttrz80hS7',
    'fryers': 'native-table-r2BIqSLhezVbOKGeRJj8',
    'export_list': 'native-table-PLujVF4tbbiIi9fzrWg8',
    'csv_scheduled_reports': 'native-table-pF4uWe5mpzoeGZbDQhPK',
    'shifts': 'native-table-K53E3SQsgOUB4wdCJdAN',
    'shift_casinos': 'native-table-G7cMiuqRgWPhS0ICRRyy',
    'shift_restaurants': 'native-table-QgzI2S9pWL584rkOhWBA'
}

class GlideAPIClient:
    """Client for Glide API - pulls REAL data only"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.headers = {
            'Authorization': f'Bearer {GLIDE_BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def query_table(self, table_id: str) -> List[Dict[str, Any]]:
        """
        Query Glide table using EXACT API format from user examples
        Locked configuration - no retry logic needed
        """
        payload = {
            "appID": GLIDE_APP_ID,
            "queries": [
                {
                    "tableName": table_id,
                    "utc": True
                }
            ]
        }
        
        try:
            response = requests.post(
                GLIDE_API_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract rows from response structure: [{"rows": [...]}]
                if isinstance(data, list) and len(data) > 0:
                    if 'rows' in data[0]:
                        rows = data[0]['rows']
                        print(f"✅ Fetched {len(rows)} rows from table {table_id}")
                        return rows if isinstance(rows, list) else []
                print(f"⚠️ Unexpected response structure for {table_id}")
                return []
            else:
                print(f"❌ API Error: Status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ Exception querying {table_id}: {str(e)}")
            return []
    
    def get_restaurants(self) -> pd.DataFrame:
        """Get Restaurants from Glide - REAL DATA"""
        print("Fetching Restaurants from Glide API...")
        rows = self.query_table(GLIDE_TABLES['restaurants'])
        if not rows:
            print("⚠️ No Restaurants data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Restaurants from Glide")
        return df
    
    def get_casinos(self) -> pd.DataFrame:
        """Get Casinos from Glide - REAL DATA"""
        print("Fetching Casinos from Glide API...")
        rows = self.query_table(GLIDE_TABLES['casinos'])
        if not rows:
            print("⚠️ No Casinos data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Casinos from Glide")
        return df
    
    def get_fryers(self) -> pd.DataFrame:
        """Get Fryers from Glide - REAL DATA"""
        print("Fetching Fryers from Glide API...")
        rows = self.query_table(GLIDE_TABLES['fryers'])
        if not rows:
            print("⚠️ No Fryers data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Fryers from Glide")
        return df
    
    def get_export_list(self) -> pd.DataFrame:
        """Get Export List from Glide - REAL DATA"""
        print("Fetching Export List from Glide API...")
        rows = self.query_table(GLIDE_TABLES['export_list'])
        if not rows:
            print("⚠️ No Export List data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Export List rows from Glide")
        return df
    
    def get_csv_scheduled_reports(self) -> pd.DataFrame:
        """Get CSV Scheduled Reports from Glide - REAL DATA"""
        print("Fetching CSV Scheduled Reports from Glide API...")
        rows = self.query_table(GLIDE_TABLES['csv_scheduled_reports'])
        if not rows:
            print("⚠️ No CSV Scheduled Reports data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} CSV Scheduled Reports from Glide")
        return df
    
    def get_shifts(self) -> pd.DataFrame:
        """Get Shifts from Glide - REAL DATA"""
        print("Fetching Shifts from Glide API...")
        rows = self.query_table(GLIDE_TABLES['shifts'])
        if not rows:
            print("⚠️ No Shifts data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Shifts from Glide")
        return df
    
    def get_shift_casinos(self) -> pd.DataFrame:
        """Get Shift Casinos from Glide - REAL DATA"""
        print("Fetching Shift Casinos from Glide API...")
        rows = self.query_table(GLIDE_TABLES['shift_casinos'])
        if not rows:
            print("⚠️ No Shift Casinos data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Shift Casinos from Glide")
        return df
    
    def get_shift_restaurants(self) -> pd.DataFrame:
        """Get Shift Restaurants from Glide - REAL DATA"""
        print("Fetching Shift Restaurants from Glide API...")
        rows = self.query_table(GLIDE_TABLES['shift_restaurants'])
        if not rows:
            print("⚠️ No Shift Restaurants data from Glide API")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Shift Restaurants from Glide")
        return df
    
    def save_to_bigquery(self, df: pd.DataFrame, table_name: str, source_table_id: str, write_disposition: str = "WRITE_TRUNCATE"):
        """Save DataFrame to BigQuery - REAL DATA ONLY with metadata"""
        if df.empty:
            print(f"⚠️ No data to save to {table_name}")
            return
        
        # Copy and sanitize
        df = df.copy()
        
        # Sanitize column names for BigQuery (remove $ prefix, replace invalid chars)
        df.columns = [col.replace('$', 'glide_').replace(' ', '_').replace('-', '_') 
                      for col in df.columns]
        
        # Add metadata fields
        df['ingested_at'] = datetime.utcnow()
        df['source_table_id'] = source_table_id
        
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            autodetect=True
        )
        
        try:
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for job to complete
            print(f"✅ Saved {len(df)} rows to {table_id}")
        except Exception as e:
            print(f"❌ Error saving to BigQuery: {e}")
            raise

def ingest_vegas_restaurants():
    """Ingest restaurant data from Glide"""
    glide = GlideAPIClient()
    restaurants = glide.get_restaurants()
    if not restaurants.empty:
        glide.save_to_bigquery(restaurants, 'vegas_restaurants', GLIDE_TABLES['restaurants'])

def ingest_vegas_casinos():
    """Ingest casino data from Glide"""
    glide = GlideAPIClient()
    casinos = glide.get_casinos()
    if not casinos.empty:
        glide.save_to_bigquery(casinos, 'vegas_casinos', GLIDE_TABLES['casinos'])

def ingest_vegas_fryers():
    """Ingest fryer data from Glide"""
    glide = GlideAPIClient()
    fryers = glide.get_fryers()
    if not fryers.empty:
        glide.save_to_bigquery(fryers, 'vegas_fryers', GLIDE_TABLES['fryers'])

def ingest_vegas_export_list():
    """Ingest export list data from Glide"""
    glide = GlideAPIClient()
    export_list = glide.get_export_list()
    if not export_list.empty:
        glide.save_to_bigquery(export_list, 'vegas_export_list', GLIDE_TABLES['export_list'])

def ingest_vegas_scheduled_reports():
    """Ingest CSV scheduled reports data from Glide"""
    glide = GlideAPIClient()
    reports = glide.get_csv_scheduled_reports()
    if not reports.empty:
        glide.save_to_bigquery(reports, 'vegas_scheduled_reports', GLIDE_TABLES['csv_scheduled_reports'])

def ingest_vegas_shifts():
    """Ingest shifts data from Glide"""
    glide = GlideAPIClient()
    shifts = glide.get_shifts()
    if not shifts.empty:
        glide.save_to_bigquery(shifts, 'vegas_shifts', GLIDE_TABLES['shifts'])

def ingest_vegas_shift_casinos():
    """Ingest shift casinos data from Glide"""
    glide = GlideAPIClient()
    shift_casinos = glide.get_shift_casinos()
    if not shift_casinos.empty:
        glide.save_to_bigquery(shift_casinos, 'vegas_shift_casinos', GLIDE_TABLES['shift_casinos'])

def ingest_vegas_shift_restaurants():
    """Ingest shift restaurants data from Glide"""
    glide = GlideAPIClient()
    shift_restaurants = glide.get_shift_restaurants()
    if not shift_restaurants.empty:
        glide.save_to_bigquery(shift_restaurants, 'vegas_shift_restaurants', GLIDE_TABLES['shift_restaurants'])

def main():
    """Main ingestion function - pulls REAL data from Glide API (ALL 8 SOURCES)"""
    print("=" * 60)
    print("GLIDE API INGESTION - VEGAS DATA (8 SOURCES)")
    print("REAL DATA ONLY - NO FAKE DATA")
    print(f"App ID: {GLIDE_APP_ID}")
    print("=" * 60)
    
    try:
        # Ingest all 8 Glide data sources
        ingest_vegas_restaurants()
        ingest_vegas_casinos()
        ingest_vegas_fryers()
        ingest_vegas_export_list()
        ingest_vegas_scheduled_reports()
        ingest_vegas_shifts()
        ingest_vegas_shift_casinos()
        ingest_vegas_shift_restaurants()
        
        print("=" * 60)
        print("✅ GLIDE API INGESTION COMPLETE - ALL 8 SOURCES")
        print("=" * 60)
    except Exception as e:
        print(f"❌ GLIDE INGESTION FAILED: {e}")
        raise

if __name__ == "__main__":
    main()

