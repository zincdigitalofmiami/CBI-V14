#!/usr/bin/env python3
"""
EXECUTE SAFE DATA RESTORATION
Fetch 3000+ rows of S&P 500 and other critical data
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("EXECUTING SAFE DATA RESTORATION")
print("=" * 80)

# 1. Create sp500_prices table
print("\n1. CREATING SP500_PRICES TABLE")
print("-" * 40)

create_table_query = """
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.sp500_prices` (
    time TIMESTAMP,
    symbol STRING,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    source_name STRING,
    confidence_score FLOAT64,
    ingest_timestamp_utc TIMESTAMP,
    provenance_uuid STRING
)
"""

try:
    client.query(create_table_query).result()
    print("  ✅ Table created/verified")
except Exception as e:
    print(f"  ⚠️ {str(e)[:100]}")

# 2. Restore existing S&P data from backup
print("\n2. RESTORING EXISTING S&P DATA FROM BACKUP")
print("-" * 40)

restore_query = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.sp500_prices`
SELECT 
    time,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    source_name,
    confidence_score,
    ingest_timestamp_utc,
    provenance_uuid
FROM `cbi-v14.bkp.soybean_oil_prices_backup_20251021_152537`
WHERE symbol IN ('SPY', 'SPX')
"""

try:
    job = client.query(restore_query)
    job.result()
    print(f"  ✅ Restored {job.num_dml_affected_rows} rows from backup")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:100]}")

# 3. Fetch historical data using yfinance
print("\n3. FETCHING HISTORICAL DATA")
print("-" * 40)

# Calculate date range for 3000+ rows
end_date = datetime.now()
start_date = end_date - timedelta(days=4500)  # ~12 years to ensure 3000 trading days

symbols_to_fetch = {
    'SPY': 'sp500_prices',      # S&P 500 ETF
    '^GSPC': 'sp500_prices',    # S&P 500 Index (backup)
    'ES=F': 'sp500_prices',     # E-mini futures
    '^VIX': 'vix_daily',        # Update existing VIX
    '^TNX': 'treasury_prices',  # Update 10-year yield
    'CL=F': 'crude_oil_prices', # Update crude with correct symbol
    'GC=F': 'gold_prices',      # Update gold
    'DX-Y.NYB': 'usd_index_prices',  # Dollar index
}

for symbol, target_table in symbols_to_fetch.items():
    print(f"\nFetching {symbol}...")
    
    try:
        # Fetch data from yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if len(df) == 0:
            print(f"  ⚠️ No data returned for {symbol}")
            continue
            
        print(f"  ✅ Fetched {len(df)} rows")
        
        # Prepare data for BigQuery
        df.reset_index(inplace=True)
        df['symbol'] = symbol.replace('=F', '').replace('^', '').replace('-Y.NYB', '')
        df['source_name'] = 'yfinance'
        df['confidence_score'] = 0.95
        df['ingest_timestamp_utc'] = datetime.utcnow()
        df['provenance_uuid'] = f"yf_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Rename columns to match schema
        df.rename(columns={
            'Date': 'time',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Select only needed columns
        columns_to_keep = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                          'source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']
        df = df[columns_to_keep]
        
        # Load to BigQuery
        table_id = f"cbi-v14.forecasting_data_warehouse.{target_table}"
        
        # Check if we should append or replace
        if target_table == 'sp500_prices' or symbol in ['SPY', '^GSPC', 'ES=F']:
            write_disposition = 'WRITE_APPEND'
        else:
            # For existing tables, append new data
            write_disposition = 'WRITE_APPEND'
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            time_partitioning=bigquery.TimePartitioning(field="time"),
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        print(f"  ✅ Loaded {len(df)} rows to {target_table}")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
        
    except Exception as e:
        print(f"  ❌ Error with {symbol}: {str(e)[:150]}")

# 4. Fix crude oil symbol contamination
print("\n4. FIXING CRUDE OIL SYMBOL CONTAMINATION")
print("-" * 40)

fix_crude_query = """
UPDATE `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
SET symbol = 'CL'
WHERE symbol = 'CRUDE_OIL_PRICES'
"""

try:
    job = client.query(fix_crude_query)
    job.result()
    print(f"  ✅ Fixed {job.num_dml_affected_rows} rows with wrong symbol")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:100]}")

# 5. Migrate CFTC and USDA data from staging
print("\n5. MIGRATING STAGING DATA")
print("-" * 40)

# CFTC COT
try:
    migrate_cftc = """
    INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
    SELECT * FROM `cbi-v14.staging.cftc_cot`
    """
    job = client.query(migrate_cftc)
    job.result()
    print(f"  ✅ Migrated {job.num_dml_affected_rows} CFTC COT rows")
except Exception as e:
    print(f"  ❌ CFTC migration error: {str(e)[:100]}")

# USDA Export Sales
try:
    migrate_usda = """
    INSERT INTO `cbi-v14.forecasting_data_warehouse.usda_export_sales`
    SELECT * FROM `cbi-v14.staging.usda_export_sales`
    """
    job = client.query(migrate_usda)
    job.result()
    print(f"  ✅ Migrated {job.num_dml_affected_rows} USDA export sales rows")
except Exception as e:
    print(f"  ❌ USDA migration error: {str(e)[:100]}")

# 6. Verify results
print("\n6. VERIFICATION")
print("-" * 40)

# Check S&P 500 data
query = """
SELECT 
    symbol,
    COUNT(*) as row_count,
    MIN(DATE(time)) as first_date,
    MAX(DATE(time)) as last_date
FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`
GROUP BY symbol
"""

print("\nS&P 500 Data:")
for row in client.query(query):
    print(f"  {row.symbol}: {row.row_count} rows ({row.first_date} to {row.last_date})")

# Check crude oil fix
query = """
SELECT symbol, COUNT(*) as cnt
FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
GROUP BY symbol
"""

print("\nCrude Oil Symbols:")
for row in client.query(query):
    status = "✅" if row.symbol == "CL" else "❌"
    print(f"  {status} {row.symbol}: {row.cnt} rows")

print("\n" + "=" * 80)
print("RESTORATION COMPLETE!")
print("=" * 80)
print("Next steps:")
print("1. Update correlation views to include S&P 500")
print("2. Delete duplicate training view")
print("3. Train models with complete data")
print("=" * 80)
