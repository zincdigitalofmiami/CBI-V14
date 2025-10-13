#!/usr/bin/env python3
"""
FRED Economic Data Deployment
Using FRED API key: dc195c8658c46ee1df83bcd4fd8a690b
Populates economic_indicators and fed_rates tables
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from bigquery_utils import safe_load_to_bigquery
import time

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
FRED_API_KEY = "dc195c8658c46ee1df83bcd4fd8a690b"

# Economic series that impact commodity prices (15-20% variance)
FRED_SERIES = {
    'DGS10': 'ten_year_treasury',        # Inventory carrying costs
    'DTWEXBGS': 'dollar_index',          # Export competitiveness  
    'CPIAUCSL': 'cpi_inflation',         # Food commodity demand
    'DFEDTARU': 'fed_funds_rate',        # Financing costs
    'DCOILWTICO': 'crude_oil_wti',       # Biofuel correlation
    'DEXCHUS': 'usd_cny_rate',           # China import costs
    'DEXBZUS': 'usd_brl_rate'            # Brazil export competitiveness
}

class FREDEconomicDeployment:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def collect_fred_series(self, series_id, indicator_name, years_back=2):
        """Collect data for a specific FRED series"""
        print(f"Collecting {indicator_name}...")
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        start_date = (datetime.now() - timedelta(days=years_back*365)).strftime('%Y-%m-%d')
        
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'observation_start': start_date
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data:
                    records = []
                    for obs in data['observations']:
                        if obs['value'] != '.':  # FRED uses '.' for missing data
                            records.append({
                                'time': pd.to_datetime(obs['date']),
                                'indicator': indicator_name,
                                'value': float(obs['value'])
                            })
                    
                    print(f"   ✓ {indicator_name}: {len(records)} observations")
                    return records
                else:
                    print(f"   ✗ No observations in response for {indicator_name}")
                    return []
            else:
                print(f"   ✗ API error {response.status_code} for {indicator_name}")
                return []
                
        except Exception as e:
            print(f"   ✗ Error collecting {indicator_name}: {e}")
            return []
    
    def deploy_all_economic_data(self):
        """Deploy all FRED economic indicators"""
        print("=" * 60)
        print("FRED ECONOMIC DATA DEPLOYMENT")
        print(f"Started: {datetime.now()}")
        print("=" * 60)
        
        all_data = []
        
        for series_id, indicator_name in FRED_SERIES.items():
            data = self.collect_fred_series(series_id, indicator_name)
            all_data.extend(data)
            time.sleep(0.5)  # Rate limiting
        
        # Load to BigQuery
        if all_data:
            df = pd.DataFrame(all_data)
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.economic_indicators"
            
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            safe_load_to_bigquery(self.client, df, table_ref, job_config)
            
            print(f"\n✓ SUCCESS: Loaded {len(all_data)} economic indicators")
            print(f"Populated table: {table_ref}")
        else:
            print("\n✗ No data collected")
        
        return all_data

if __name__ == "__main__":
    fred = FREDEconomicDeployment()
    fred.deploy_all_economic_data()







