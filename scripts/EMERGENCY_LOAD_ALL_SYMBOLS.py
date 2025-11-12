#!/usr/bin/env python3
"""
EMERGENCY: Load ALL 224 symbols to BigQuery NOW
"""

import subprocess
import sys
import time

print("🚨 EMERGENCY DATA LOAD - ALL 224 SYMBOLS")
print("="*50)

# Option 1: Run the existing script
print("\n1️⃣ RUNNING pull_224_driver_universe.py...")
print("This will:")
print("- Pull ALL 224 symbols from Yahoo Finance")
print("- Save to cbi-v14.yahoo_finance_comprehensive.all_drivers_224_universe")
print("- Take ~15-20 minutes")

response = input("\nProceed? (y/n): ")
if response.lower() == 'y':
    subprocess.run([sys.executable, 'scripts/pull_224_driver_universe.py'])
else:
    print("\n2️⃣ ALTERNATIVE: Load cached data to BigQuery")
    print("We have 55 symbols cached locally")
    
    import pandas as pd
    from google.cloud import bigquery
    import os
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/zincdigital/gcp-key.json'
    
    # Load cached data
    df = pd.read_csv('cache/yahoo_finance_complete/MASTER_ALL_SYMBOLS.csv')
    print(f"Loaded {len(df)} rows, {df['symbol'].nunique()} symbols")
    
    # Upload to BigQuery
    client = bigquery.Client(project='cbi-v14')
    table_id = 'cbi-v14.forecasting_data_warehouse.yahoo_all_symbols_emergency'
    
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    print(f"✅ Uploaded to {table_id}")

