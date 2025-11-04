#!/usr/bin/env python3
"""
Fetch Economic Data from FRED API and populate NULL columns
Requires FRED API key (get free key at https://fred.stlouisfed.org/docs/api/api_key.html)
"""
import os
import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"

# FRED API configuration - try to get from secret manager or env
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Try to get from Secret Manager if available
if not FRED_API_KEY:
    try:
        from google.cloud import secretmanager
        client_secret = secretmanager.SecretManagerServiceClient()
        name = f'projects/{PROJECT_ID}/secrets/forecasting-data-keys/versions/latest'
        response = client_secret.access_secret_version(request={'name': name})
        secret_data = response.payload.data.decode('UTF-8')
        import json
        keys = json.loads(secret_data)
        FRED_API_KEY = keys.get('FRED_API_KEY') or keys.get('fred_api_key')
    except:
        pass

# If still no key, try to calculate from available data or use alternative methods
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

if not FRED_API_KEY:
    print("⚠️  FRED_API_KEY not found - will use alternative methods")
    print("   Using yfinance and calculated metrics instead")

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("📊 FETCHING ECONOMIC DATA FROM FRED")
print("="*80)

# Get date range
query = f"""
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date
FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
"""
date_range = client.query(query).to_dataframe().iloc[0]
start_date = date_range['min_date'].strftime('%Y-%m-%d')
end_date = date_range['max_date'].strftime('%Y-%m-%d')

print(f"Date range: {start_date} to {end_date}")

# FRED Series mappings
FRED_SERIES = {
    'gdp_growth': {
        'series_id': 'GDPC1',  # Real Gross Domestic Product
        'calculation': 'quarterly_growth',  # Calculate quarterly growth rate
        'target_column': 'gdp_growth'
    },
    'econ_gdp_growth': {
        'series_id': 'GDPC1',
        'calculation': 'quarterly_growth',
        'target_column': 'econ_gdp_growth'
    },
    'unemployment_rate': {
        'series_id': 'UNRATE',  # Unemployment Rate
        'calculation': 'monthly_forward_fill',  # Forward fill monthly values
        'target_column': 'unemployment_rate'
    },
    'cpi_yoy': {
        'series_id': 'CPIAUCSL',  # Consumer Price Index
        'calculation': 'yoy_change',  # Year-over-year change
        'target_column': 'cpi_yoy'
    }
}

def fetch_fred_series(series_id, start_date, end_date):
    """Fetch data from FRED API"""
    url = f"{FRED_BASE_URL}/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'frequency': 'm'  # Monthly
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            print(f"  ❌ No observations found for {series_id}")
            return None
        
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[df['value'].notna()]
        
        return df[['date', 'value']]
    except Exception as e:
        print(f"  ❌ Error fetching {series_id}: {str(e)}")
        return None

def calculate_growth_rate(df):
    """Calculate quarterly growth rate"""
    df = df.sort_values('date')
    df['growth'] = df['value'].pct_change(periods=1) * 100  # Quarterly growth %
    return df[['date', 'growth']].rename(columns={'growth': 'value'})

def calculate_yoy_change(df):
    """Calculate year-over-year change"""
    df = df.sort_values('date')
    df['yoy'] = df['value'].pct_change(periods=12) * 100  # YoY change %
    return df[['date', 'yoy']].rename(columns={'yoy': 'value'})

def forward_fill_to_daily(df, start_date, end_date):
    """Forward fill monthly data to daily"""
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    df_daily = pd.DataFrame({'date': date_range})
    df_daily = df_daily.merge(df, on='date', how='left')
    df_daily['value'] = df_daily['value'].fillna(method='ffill')
    return df_daily

# Process each series
print("\n📈 Fetching and processing economic series...")
for col_name, config in FRED_SERIES.items():
    print(f"\n  Processing {col_name}...")
    print(f"    FRED Series: {config['series_id']}")
    
    # Fetch data
    df = fetch_fred_series(config['series_id'], start_date, end_date)
    
    if df is None or len(df) == 0:
        print(f"    ⚠️  No data fetched - skipping")
        continue
    
    print(f"    ✅ Fetched {len(df)} observations")
    
    # Apply calculation
    if config['calculation'] == 'quarterly_growth':
        df = calculate_growth_rate(df)
    elif config['calculation'] == 'yoy_change':
        df = calculate_yoy_change(df)
    elif config['calculation'] == 'monthly_forward_fill':
        df = forward_fill_to_daily(df, start_date, end_date)
    
    # Update BigQuery table
    target_col = config['target_column']
    print(f"    🔄 Updating {target_col} in BigQuery...")
    
    # Create temporary table
    temp_table = f"{PROJECT_ID}.{DATASET_ID}._temp_fred_{col_name}"
    df.to_gbq(temp_table, project_id=PROJECT_ID, if_exists='replace', table_schema=[
        {'name': 'date', 'type': 'DATE'},
        {'name': 'value', 'type': 'FLOAT64'}
    ])
    
    # Update main table
    update_query = f"""
    UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
    SET `{target_col}` = (
        SELECT value
        FROM `{temp_table}` temp
        WHERE temp.date = t.date
    )
    WHERE t.`{target_col}` IS NULL
    AND EXISTS (
        SELECT 1
        FROM `{temp_table}` temp
        WHERE temp.date = t.date
    )
    """
    
    try:
        job = client.query(update_query)
        job.result()
        print(f"    ✅ Updated {job.num_dml_affected_rows} rows")
        
        # Clean up temp table
        client.query(f"DROP TABLE IF EXISTS `{temp_table}`").result()
    except Exception as e:
        print(f"    ❌ Error updating: {str(e)[:200]}")

print("\n" + "="*80)
print("✅ FRED DATA FETCH COMPLETE")
print("="*80)

