#!/usr/bin/env python3
"""
EMERGENCY FIX: Update soybean oil prices with real-time data
Market moving 2%+ daily but our data is stale
"""

import yfinance as yf
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import uuid

def emergency_update_zl_prices():
    print('🚨 EMERGENCY FIX: Updating ZL prices to CURRENT...')
    
    # Get latest data
    zl = yf.Ticker('ZL=F')
    hist = zl.history(period='30d')
    
    # Match existing schema exactly
    df = pd.DataFrame({
        'time': hist.index,
        'symbol': 'ZL',
        'open': hist['Open'].values,
        'high': hist['High'].values,
        'low': hist['Low'].values,
        'close': hist['Close'].values,
        'volume': hist['Volume'].astype(int).values,
        'source_name': 'yahoo_realtime_emergency_nov5',
        'confidence_score': 0.95,
        'ingest_timestamp_utc': datetime.now(),
        'provenance_uuid': [str(uuid.uuid4()) for _ in range(len(hist))]
    })
    
    df['time'] = pd.to_datetime(df['time']).dt.tz_localize(None)
    
    print(f'✅ Fetched {len(df)} days')
    print(f'Latest ZL: ${df.iloc[-1]["close"]:.2f} on {df.iloc[-1]["time"].date()}')
    print(f'Range: ${df["close"].min():.2f} - ${df["close"].max():.2f}')
    
    # Upload
    client = bigquery.Client(project='cbi-v14')
    job = client.load_table_from_dataframe(
        df, 
        'cbi-v14.forecasting_data_warehouse.soybean_oil_prices',
        job_config=bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
    )
    job.result()
    
    print(f'🎯 SUCCESS: {len(df)} records uploaded to BigQuery')
    print('✅ Soybean oil prices NOW CURRENT')
    
    return True

if __name__ == '__main__':
    emergency_update_zl_prices()









