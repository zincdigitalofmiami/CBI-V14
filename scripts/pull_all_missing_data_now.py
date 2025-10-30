#!/usr/bin/env python3
"""
EMERGENCY DATA PULL - Fill All Gaps
Pull EVERYTHING we're missing with MAXIMUM coverage
"""

import requests
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
import uuid

client = bigquery.Client(project='cbi-v14')

api_keys = {
    'fred': 'dc195c8658c46ee1df83bcd4fd8a690b',
    'alpha_vantage': 'BA7CQWXKRFBNFY49'
}

print("=" * 80)
print("🚀 MAXIMUM DATA PULL - FILLING ALL GAPS")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

collected_data = []

# 1. Pull ALL exchange rates from Yahoo Finance
print("=" * 80)
print("1. PULLING ALL EXCHANGE RATES")
print("=" * 80)

currencies = [
    ('BRL=X', 'usd_brl_rate'),
    ('CNY=X', 'usd_cny_rate'),
    ('ARS=X', 'usd_ars_rate'),
    ('EUR=X', 'usd_eur_rate'),
    ('JPY=X', 'usd_jpy_rate'),
]

for symbol, indicator in currencies:
    try:
        print(f"Pulling {indicator} ({symbol})...")
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='5y')  # 5 years of history
        
        if not data.empty:
            for date, row in data.iterrows():
                record = {
                    'time': date.to_pydatetime().replace(tzinfo=timezone.utc),
                    'indicator': indicator,
                    'value': float(row['Close']),
                    'source_name': 'Yahoo_Finance',
                    'confidence_score': 0.95,
                    'ingest_timestamp_utc': datetime.now(timezone.utc),
                    'provenance_uuid': str(uuid.uuid4())
                }
                collected_data.append(record)
            
            print(f"✅ {indicator}: {len(data)} data points")
        time.sleep(2)
    except Exception as e:
        print(f"❌ {indicator}: {e}")

# 2. Pull FRED economic data (historical)
print("\n" + "=" * 80)
print("2. PULLING FRED ECONOMIC DATA (HISTORICAL)")
print("=" * 80)

fred_series = [
    ('FEDFUNDS', 'fed_funds_rate'),
    ('DGS10', 'ten_year_treasury'),
    ('DTWEXBGS', 'dollar_index_fred'),
    ('CPIAUCSL', 'cpi_inflation'),
    ('DEXBZUS', 'usd_brl_rate_fred'),
    ('DEXCHUS', 'usd_cny_rate_fred'),
    ('VIXCLS', 'vix_index_fred'),
    ('DCOILWTICO', 'crude_oil_wti'),
    ('UNRATE', 'unemployment_rate'),
]

for series_id, indicator_name in fred_series:
    try:
        print(f"Pulling {indicator_name} ({series_id})...")
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': api_keys['fred'],
            'file_type': 'json',
            'limit': 10000,
            'sort_order': 'asc'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data:
                count = 0
                for obs in data['observations']:
                    if obs['value'] != '.':
                        try:
                            date_obj = datetime.strptime(obs['date'], '%Y-%m-%d')
                            record = {
                                'time': date_obj.replace(tzinfo=timezone.utc),
                                'indicator': indicator_name,
                                'value': float(obs['value']),
                                'source_name': 'FRED',
                                'confidence_score': 0.95,
                                'ingest_timestamp_utc': datetime.now(timezone.utc),
                                'provenance_uuid': str(uuid.uuid4())
                            }
                            collected_data.append(record)
                            count += 1
                        except:
                            pass
                print(f"✅ {indicator_name}: {count} data points")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ {indicator_name}: {e}")

# 3. Save to BigQuery
print("\n" + "=" * 80)
print("3. SAVING TO BIGQUERY")
print("=" * 80)

if collected_data:
    df = pd.DataFrame(collected_data)
    table_id = 'cbi-v14.forecasting_data_warehouse.economic_indicators'
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    
    print(f"Writing {len(df)} records...")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Saved {len(df)} records")
else:
    print("❌ No data collected")

print("\n" + "=" * 80)
print("DATA PULL COMPLETE")
print("=" * 80)
print(f"Total records: {len(collected_data)}")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)












