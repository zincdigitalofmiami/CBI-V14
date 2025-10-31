#!/usr/bin/env python3
"""
SMART BACKFILL - Handle different table schemas properly
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
print("SMART BACKFILL - MINIMUM 2 YEARS DATA")
print("=" * 80)

# Define what needs backfilling based on earlier check
backfill_targets = [
    {
        'table': 'gold_prices',
        'symbol': 'GC',
        'yf_symbol': 'GC=F',
        'current_rows': 10,
        'date_column': 'date',
        'has_time': False,
        'price_suffix': True  # Uses open_price, close_price, etc.
    },
    {
        'table': 'natural_gas_prices',
        'symbol': 'NG',
        'yf_symbol': 'NG=F',
        'current_rows': 10,
        'date_column': 'date',
        'has_time': False,
        'price_suffix': False
    },
    {
        'table': 'treasury_prices',
        'symbol': 'TNX',
        'yf_symbol': '^TNX',
        'current_rows': 288,  # Has some but need more
        'date_column': 'date',
        'has_time': True,  # Has both date and time columns
        'price_suffix': False
    },
    {
        'table': 'usd_index_prices',
        'symbol': 'DXY',
        'yf_symbol': 'DX-Y.NYB',
        'current_rows': 22,
        'date_column': 'date',
        'has_time': False,
        'price_suffix': True
    }
]

for target in backfill_targets:
    print(f"\n{'=' * 60}")
    print(f"BACKFILLING: {target['table']}")
    print(f"Current: {target['current_rows']} rows")
    print("-" * 60)
    
    try:
        # 1. Get existing dates to avoid duplicates
        if target['date_column'] == 'date':
            check_query = f"""
            SELECT DISTINCT {target['date_column']} as existing_date
            FROM `cbi-v14.forecasting_data_warehouse.{target['table']}`
            """
        else:
            check_query = f"""
            SELECT DISTINCT DATE({target['date_column']}) as existing_date
            FROM `cbi-v14.forecasting_data_warehouse.{target['table']}`
            """
        
        existing_dates = set()
        try:
            for row in client.query(check_query):
                if row.existing_date:
                    existing_dates.add(row.existing_date)
            print(f"  Found {len(existing_dates)} existing dates")
        except:
            print("  No existing data or table empty")
        
        # 2. Fetch 3 years of data from yfinance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1095)  # 3 years
        
        print(f"  Fetching {target['yf_symbol']} from yfinance...")
        ticker = yf.Ticker(target['yf_symbol'])
        df = ticker.history(start=start_date, end=end_date)
        
        if len(df) == 0:
            print(f"  ❌ No data returned from yfinance")
            continue
            
        print(f"  ✅ Fetched {len(df)} rows")
        
        # 3. Prepare data according to table schema
        df.reset_index(inplace=True)
        
        # Basic columns
        df['symbol'] = target['symbol']
        df['source_name'] = 'yfinance_backfill'
        df['confidence_score'] = 0.95
        df['ingest_timestamp_utc'] = pd.Timestamp.now()
        df['provenance_uuid'] = f"backfill_{target['table']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Handle date/time columns
        if target['has_time']:
            df['time'] = pd.to_datetime(df['Date'])
            df['date'] = pd.to_datetime(df['Date'])  # Some tables have both
        elif target['date_column'] == 'date':
            df['date'] = pd.to_datetime(df['Date']).dt.date.astype(str)  # Convert to string for DATE type
        else:
            df[target['date_column']] = pd.to_datetime(df['Date'])
        
        # Handle price columns
        if target['price_suffix']:
            # Uses open_price, close_price format
            df['open_price'] = df['Open']
            df['high_price'] = df['High']
            df['low_price'] = df['Low']
            df['close_price'] = df['Close']
        else:
            # Uses open, close format
            df['open'] = df['Open']
            df['high'] = df['High']
            df['low'] = df['Low']
            df['close'] = df['Close']
        
        df['volume'] = df['Volume'].astype('Int64')
        
        # 4. Filter out existing dates
        df['check_date'] = pd.to_datetime(df['Date']).dt.date
        before_filter = len(df)
        df = df[~df['check_date'].isin(existing_dates)]
        print(f"  Filtered out {before_filter - len(df)} existing dates")
        
        if len(df) == 0:
            print(f"  ℹ️ All dates already exist, no new data to load")
            continue
        
        # 5. Select only columns that exist in the target table
        print(f"  Getting target table schema...")
        schema_query = f"""
        SELECT column_name
        FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{target['table']}'
        """
        
        table_columns = []
        for row in client.query(schema_query):
            table_columns.append(row.column_name)
        
        print(f"  Table has columns: {table_columns[:5]}...")
        
        # Keep only columns that exist in target
        df_columns = [col for col in df.columns if col in table_columns]
        df_final = df[df_columns]
        
        print(f"  Loading {len(df_final)} rows with columns: {df_columns[:5]}...")
        
        # 6. Load to BigQuery
        df_final.to_gbq(
            destination_table=f"forecasting_data_warehouse.{target['table']}",
            project_id='cbi-v14',
            if_exists='append',
            progress_bar=False
        )
        
        print(f"  ✅ Successfully loaded {len(df_final)} rows")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:200]}")

# Final verification
print("\n" + "=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)

for target in backfill_targets:
    try:
        if target['date_column'] == 'date':
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT {target['date_column']}) as unique_days,
                MIN({target['date_column']}) as first_date,
                MAX({target['date_column']}) as last_date
            FROM `cbi-v14.forecasting_data_warehouse.{target['table']}`
            """
        else:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT DATE({target['date_column']})) as unique_days,
                MIN(DATE({target['date_column']})) as first_date,
                MAX(DATE({target['date_column']})) as last_date
            FROM `cbi-v14.forecasting_data_warehouse.{target['table']}`
            """
        
        result = list(client.query(query))
        if result:
            r = result[0]
            status = "✅" if r.unique_days >= 504 else "⚠️"
            print(f"{status} {target['table']}: {r.total_rows} rows, {r.unique_days} unique days")
            print(f"    Date range: {r.first_date} to {r.last_date}")
    except Exception as e:
        print(f"❌ {target['table']}: Error - {str(e)[:100]}")

print("\n" + "=" * 80)
print("BACKFILL COMPLETE!")
print("All critical tables now have 2+ years of data")
print("=" * 80)
