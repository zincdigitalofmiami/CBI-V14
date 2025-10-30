#!/usr/bin/env python3
"""
SAFE DATA RESTORATION AND BACKFILL
With extreme caution - backup everything first
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("SAFE DATA RESTORATION AND BACKFILL PLAN")
print("=" * 80)

# 1. FIRST - Create safety backups of current state
print("\n1. CREATING SAFETY BACKUPS")
print("-" * 40)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
critical_tables = [
    'soybean_oil_prices',
    'crude_oil_prices',
    'economic_indicators'
]

for table in critical_tables:
    backup_name = f"bkp.{table}_SAFETY_{timestamp}"
    print(f"  Creating backup: {backup_name}")
    
    try:
        query = f"""
        CREATE TABLE `cbi-v14.{backup_name}` AS
        SELECT * FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        client.query(query).result()
        print(f"    ✅ Backed up successfully")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"    ⚠️ Backup already exists")
        else:
            print(f"    ❌ Error: {str(e)[:50]}")

# 2. Check what S&P 500 data we have in backup
print("\n2. CHECKING EXISTING S&P 500 DATA")
print("-" * 40)

query = """
SELECT 
    symbol,
    COUNT(*) as row_count,
    MIN(DATE(time)) as first_date,
    MAX(DATE(time)) as last_date,
    MIN(close) as min_price,
    MAX(close) as max_price
FROM `cbi-v14.bkp.soybean_oil_prices_backup_20251021_152537`
WHERE symbol IN ('SPY', 'SPX')
GROUP BY symbol
"""

existing_sp500 = {}
for row in client.query(query):
    print(f"  {row.symbol}:")
    print(f"    Rows: {row.row_count}")
    print(f"    Date range: {row.first_date} to {row.last_date}")
    print(f"    Price range: ${row.min_price:.2f} - ${row.max_price:.2f}")
    existing_sp500[row.symbol] = {
        'count': row.row_count,
        'last_date': row.last_date
    }

# 3. Plan to get 3000+ rows of data
print("\n3. DATA BACKFILL PLAN")
print("-" * 40)

# Calculate how much data we need
target_rows = 3000
trading_days_per_year = 252
years_needed = target_rows / trading_days_per_year
print(f"  Target: {target_rows} rows (~{years_needed:.1f} years of data)")

# Show what we'll fetch
end_date = datetime.now()
start_date = end_date - timedelta(days=int(years_needed * 365))
print(f"  Date range: {start_date.date()} to {end_date.date()}")

print("\n4. DATA TO FETCH (using yfinance):")
print("-" * 40)

symbols_to_fetch = {
    'SPY': 'S&P 500 ETF',
    '^GSPC': 'S&P 500 Index', 
    'ES=F': 'E-mini S&P 500 Futures',
    'CL=F': 'Crude Oil Futures (fix symbol issue)',
    '^TNX': '10-Year Treasury Yield',
    '^VIX': 'VIX Volatility Index',
    'GC=F': 'Gold Futures',
    'DX-Y.NYB': 'US Dollar Index',
    'BTC-USD': 'Bitcoin (for crypto correlation)',
    'EURUSD=X': 'EUR/USD Exchange Rate'
}

for symbol, description in symbols_to_fetch.items():
    print(f"  • {symbol}: {description}")

# 5. Show the restoration process
print("\n5. RESTORATION PROCESS (SAFE)")
print("-" * 40)
print("  Step 1: Create new table 'sp500_prices' for S&P data")
print("  Step 2: Restore existing 30 rows from backup")
print("  Step 3: Fetch 3000+ rows using yfinance")
print("  Step 4: Fix crude oil symbol contamination")
print("  Step 5: Migrate CFTC/USDA from staging")
print("  Step 6: Update correlation views")

# 6. Check for conflicts
print("\n6. CHECKING FOR CONFLICTS")
print("-" * 40)

# Check if sp500_prices already exists
query = """
SELECT table_name
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'sp500_prices'
"""
exists = list(client.query(query))
if exists:
    print("  ⚠️ sp500_prices table already exists - will append data")
else:
    print("  ✅ sp500_prices table doesn't exist - safe to create")

# 7. Estimate costs
print("\n7. COST ESTIMATE")
print("-" * 40)
print(f"  New data rows: ~{target_rows * len(symbols_to_fetch)} rows")
print(f"  Storage: ~{target_rows * len(symbols_to_fetch) * 100 / 1024 / 1024:.2f} MB")
print(f"  BigQuery cost: < $0.10 (minimal)")

print("\n" + "=" * 80)
print("READY TO PROCEED?")
print("=" * 80)
print("This script will:")
print("1. Create safety backups")
print("2. Create sp500_prices table")
print("3. Restore 30 rows from backup")
print("4. Fetch 3000+ rows of historical data")
print("5. Fix symbol contamination issues")
print("")
print("Run: python3 scripts/EXECUTE_SAFE_RESTORATION.py")
print("=" * 80)
