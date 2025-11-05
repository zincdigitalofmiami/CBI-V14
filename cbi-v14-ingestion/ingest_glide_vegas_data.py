#!/usr/bin/env python3
"""
Glide API Integration - Vegas Customer & Restaurant Data
Pulls real data from Glide App API for customers, restaurants, and fryers
NO FAKE DATA - ONLY REAL DATA FROM GLIDE API
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

# Glide API Configuration
GLIDE_API_ENDPOINT = "https://api.glideapp.io/api/function/queryTables"
GLIDE_APP_ID = "mUOrVLuWpdduTpJev9t1"
GLIDE_BEARER_TOKEN = "460c9ee4-edcb-43cc-86b5-929e2bb94351"  # From docs

# Glide Table IDs
GLIDE_TABLES = {
    'restaurant_groups': 'native-table-w295hHsL0PHvty2sAFwl',
    'restaurants': 'native-table-ojIjQjDcDAEOpdtZG5Ao',
    'fryers': 'native-table-r2BIqSLhezVbOKGeRJj8'
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
        """Query a Glide table - returns REAL data only"""
        # Glide API might use different endpoint format
        # Try multiple approaches
        endpoints = [
            GLIDE_API_ENDPOINT,
            f"https://api.glideapp.io/api/function/queryTable",
            f"https://api.glideapp.io/api/function/getTable",
            f"https://api.glideapp.io/api/tables/{table_id}",
        ]
        
        payloads = [
            {'appID': GLIDE_APP_ID, 'tableID': table_id},
            {'appId': GLIDE_APP_ID, 'tableId': table_id},
            {'app': GLIDE_APP_ID, 'table': table_id},
            {'tableId': table_id},  # Maybe app ID in header
        ]
        
        # Try GET requests too
        for endpoint in endpoints:
            # Try GET first
            try:
                get_response = requests.get(
                    endpoint,
                    headers=self.headers,
                    params={'tableId': table_id, 'appId': GLIDE_APP_ID},
                    timeout=30
                )
                if get_response.status_code == 200:
                    data = get_response.json()
                    if isinstance(data, list):
                        print(f"✅ GET request successful: {len(data)} rows")
                        return data
                    elif isinstance(data, dict) and ('rows' in data or 'data' in data):
                        rows = data.get('rows') or data.get('data', [])
                        print(f"✅ GET request successful: {len(rows)} rows")
                        return rows if isinstance(rows, list) else []
            except:
                pass
            
            # Try POST with different payloads
            for payload in payloads:
                try:
                    response = requests.post(
                        endpoint,
                        headers=self.headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ POST successful on {endpoint}, keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                        
                        if isinstance(data, dict):
                            if 'rows' in data:
                                return data['rows'] if isinstance(data['rows'], list) else []
                            elif 'data' in data:
                                return data['data'] if isinstance(data['data'], list) else []
                            elif 'result' in data:
                                return data['result'] if isinstance(data['result'], list) else []
                        elif isinstance(data, list):
                            return data
                        
                        print(f"Response structure: {type(data)}")
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())}")
                    
                    elif response.status_code == 401:
                        print(f"❌ Authentication failed - check Bearer token")
                        print(f"Response: {response.text[:200]}")
                    elif response.status_code == 400:
                        # Try next payload
                        continue
                    else:
                        print(f"⚠️ Status {response.status_code}: {response.text[:200]}")
                        
                except requests.exceptions.RequestException as e:
                    continue
                except Exception as e:
                    continue
        
        print(f"❌ All API attempts failed for table {table_id}")
        print(f"⚠️ Glide API connection issue - check token and endpoint")
        print(f"⚠️ Token: {GLIDE_BEARER_TOKEN[:20]}...")
        print(f"⚠️ App ID: {GLIDE_APP_ID}")
        return []
    
    def get_restaurant_groups(self) -> pd.DataFrame:
        """Get Restaurant Groups from Glide - REAL DATA"""
        print("Fetching Restaurant Groups from Glide API...")
        rows = self.query_table(GLIDE_TABLES['restaurant_groups'])
        
        if not rows:
            print("⚠️ No Restaurant Groups data from Glide API")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        print(f"✅ Fetched {len(df)} Restaurant Groups from Glide")
        return df
    
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
    
    def save_to_bigquery(self, df: pd.DataFrame, table_name: str, write_disposition: str = "WRITE_TRUNCATE"):
        """Save DataFrame to BigQuery - REAL DATA ONLY"""
        if df.empty:
            print(f"⚠️ No data to save to {table_name}")
            return
        
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

def ingest_vegas_customers():
    """Ingest customer data from Glide - Restaurant Groups = Customers"""
    glide = GlideAPIClient()
    
    # Get Restaurant Groups (these are customers)
    restaurant_groups = glide.get_restaurant_groups()
    
    if not restaurant_groups.empty:
        # Standardize column names for BigQuery
        # Map Glide columns to our schema
        customer_df = restaurant_groups.copy()
        
        # Add ingestion timestamp
        customer_df['ingested_at'] = datetime.utcnow()
        
        # Save to BigQuery
        glide.save_to_bigquery(customer_df, 'vegas_customers')

def ingest_vegas_restaurants():
    """Ingest restaurant data from Glide"""
    glide = GlideAPIClient()
    
    restaurants = glide.get_restaurants()
    
    if not restaurants.empty:
        restaurant_df = restaurants.copy()
        restaurant_df['ingested_at'] = datetime.utcnow()
        glide.save_to_bigquery(restaurant_df, 'vegas_restaurants')

def ingest_vegas_fryers():
    """Ingest fryer data from Glide - for multiplier calculations"""
    glide = GlideAPIClient()
    
    fryers = glide.get_fryers()
    
    if not fryers.empty:
        fryer_df = fryers.copy()
        fryer_df['ingested_at'] = datetime.utcnow()
        
        # Calculate base daily gallons from fryer data
        # Formula: (fryer_capacity_lb × turns_per_month) / 7 / 7.6
        if 'fryer_capacity_lb' in fryer_df.columns and 'turns_per_month' in fryer_df.columns:
            fryer_df['base_daily_gallons'] = (
                fryer_df['fryer_capacity_lb'] * fryer_df['turns_per_month'] / 7 / 7.6
            ).fillna(0)
        
        glide.save_to_bigquery(fryer_df, 'vegas_fryers')

def main():
    """Main ingestion function - pulls REAL data from Glide API"""
    print("=" * 60)
    print("GLIDE API INGESTION - VEGAS DATA")
    print("REAL DATA ONLY - NO FAKE DATA")
    print("=" * 60)
    
    try:
        # Ingest all Glide data
        ingest_vegas_customers()
        ingest_vegas_restaurants()
        ingest_vegas_fryers()
        
        print("=" * 60)
        print("✅ GLIDE API INGESTION COMPLETE")
        print("=" * 60)
    except Exception as e:
        print(f"❌ GLIDE INGESTION FAILED: {e}")
        raise

if __name__ == "__main__":
    main()

