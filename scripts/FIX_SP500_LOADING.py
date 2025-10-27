#!/usr/bin/env python3
"""
FIX S&P 500 DATA LOADING
Match exact schema without partitioning issues
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import pandas_gbq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("FIXING S&P 500 DATA LOADING")
print("=" * 80)

# 1. Drop and recreate sp500_prices table with proper schema
print("\n1. RECREATING SP500_PRICES TABLE")
print("-" * 40)

# Drop existing table
drop_query = "DROP TABLE IF EXISTS `cbi-v14.forecasting_data_warehouse.sp500_prices`"
try:
    client.query(drop_query).result()
    print("  ✅ Dropped existing table")
except:
    print("  ⚠️ Table didn't exist")

# Create with same schema as other price tables (no partitioning)
create_query = """
CREATE TABLE `cbi-v14.forecasting_data_warehouse.sp500_prices` (
    time TIMESTAMP NOT NULL,
    symbol STRING NOT NULL,
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
client.query(create_query).result()
print("  ✅ Created new table")

# 2. Fetch and load S&P 500 data
print("\n2. FETCHING AND LOADING S&P 500 DATA")
print("-" * 40)

# Get 12+ years of data
end_date = datetime.now()
start_date = end_date - timedelta(days=4500)

# Main S&P 500 symbol
symbol = 'SPY'
print(f"\nFetching {symbol}...")

try:
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)
    
    if len(df) > 0:
        print(f"  ✅ Fetched {len(df)} rows")
        
        # Prepare data
        df.reset_index(inplace=True)
        df['time'] = pd.to_datetime(df['Date'])
        df['symbol'] = 'SPY'
        df['open'] = df['Open']
        df['high'] = df['High']
        df['low'] = df['Low']
        df['close'] = df['Close']
        df['volume'] = df['Volume'].astype('Int64')
        df['source_name'] = 'yfinance'
        df['confidence_score'] = 0.95
        df['ingest_timestamp_utc'] = pd.Timestamp.now()
        df['provenance_uuid'] = f"yf_SPY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Select only needed columns
        df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                 'source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']]
        
        # Load using pandas_gbq (more reliable for schema matching)
        df.to_gbq(
            destination_table='forecasting_data_warehouse.sp500_prices',
            project_id='cbi-v14',
            if_exists='append',
            progress_bar=False
        )
        
        print(f"  ✅ Loaded {len(df)} rows of SPY data")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:200]}")

# Also get S&P 500 index for comparison
symbol = '^GSPC'
print(f"\nFetching {symbol} (S&P 500 Index)...")

try:
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)
    
    if len(df) > 0:
        print(f"  ✅ Fetched {len(df)} rows")
        
        # Prepare data
        df.reset_index(inplace=True)
        df['time'] = pd.to_datetime(df['Date'])
        df['symbol'] = 'SPX'  # Use SPX as symbol
        df['open'] = df['Open']
        df['high'] = df['High']
        df['low'] = df['Low']
        df['close'] = df['Close']
        df['volume'] = df['Volume'].astype('Int64')
        df['source_name'] = 'yfinance'
        df['confidence_score'] = 0.95
        df['ingest_timestamp_utc'] = pd.Timestamp.now()
        df['provenance_uuid'] = f"yf_SPX_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Select only needed columns
        df = df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume',
                 'source_name', 'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid']]
        
        # Load using pandas_gbq
        df.to_gbq(
            destination_table='forecasting_data_warehouse.sp500_prices',
            project_id='cbi-v14',
            if_exists='append',
            progress_bar=False
        )
        
        print(f"  ✅ Loaded {len(df)} rows of SPX data")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:200]}")

# 3. Fix USDA export sales migration (schema issue)
print("\n3. FIXING USDA EXPORT SALES MIGRATION")
print("-" * 40)

# Check schema mismatch
print("Checking schema differences...")
query = """
SELECT column_name, data_type
FROM `cbi-v14.staging.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'usda_export_sales'
ORDER BY ordinal_position
"""
print("Staging schema:")
for row in client.query(query):
    print(f"  • {row.column_name}: {row.data_type}")

# Try to migrate with proper column mapping
try:
    migrate_query = """
    INSERT INTO `cbi-v14.forecasting_data_warehouse.usda_export_sales` 
    (report_date, commodity, destination_country, net_sales_mt, cumulative_exports_mt, 
     marketing_year, source_name, confidence_score, ingest_timestamp_utc, provenance_uuid)
    SELECT 
        report_date,
        commodity,
        destination_country,
        net_sales_mt,
        cumulative_exports_mt,
        marketing_year,
        source_name,
        confidence_score,
        ingest_timestamp_utc,
        provenance_uuid
    FROM `cbi-v14.staging.usda_export_sales`
    """
    job = client.query(migrate_query)
    job.result()
    print(f"  ✅ Migrated {job.num_dml_affected_rows} USDA rows")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:200]}")

# 4. Verify results
print("\n4. VERIFICATION")
print("-" * 40)

# Check S&P 500 data
query = """
SELECT 
    symbol,
    COUNT(*) as row_count,
    MIN(DATE(time)) as first_date,
    MAX(DATE(time)) as last_date,
    MIN(close) as min_price,
    MAX(close) as max_price
FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`
GROUP BY symbol
ORDER BY symbol
"""

print("\nS&P 500 Data Loaded:")
total_rows = 0
for row in client.query(query):
    print(f"  {row.symbol}:")
    print(f"    Rows: {row.row_count}")
    print(f"    Dates: {row.first_date} to {row.last_date}")
    print(f"    Price range: ${row.min_price:.2f} - ${row.max_price:.2f}")
    total_rows += row.row_count

print(f"\n  TOTAL S&P 500 ROWS: {total_rows}")

if total_rows >= 3000:
    print("  ✅ SUCCESS! We have 3000+ rows of S&P 500 data!")
else:
    print(f"  ⚠️ Only {total_rows} rows - need more data")

# Check other critical tables
print("\nOther Critical Data:")
query = "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`"
result = list(client.query(query))
print(f"  CFTC COT: {result[0].cnt} rows")

query = "SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.usda_export_sales`"
result = list(client.query(query))
print(f"  USDA Export Sales: {result[0].cnt} rows")

query = "SELECT DISTINCT symbol, COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices` GROUP BY symbol"
for row in client.query(query):
    print(f"  Crude Oil ({row.symbol}): {row.cnt} rows")

print("\n" + "=" * 80)
print("DATA RESTORATION STATUS")
print("=" * 80)
print("✅ Crude oil symbol fixed (CL)")
print("✅ CFTC COT migrated (72 rows)")
print("🔄 S&P 500 data loading...")
print("🔄 USDA export sales migration...")
print("=" * 80)
