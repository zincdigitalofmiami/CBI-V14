#!/usr/bin/env python3
"""
BACKFILL ALL DATA TO MINIMUM 2 YEARS
Check all tables and ensure minimum 2 years of historical data
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
print("CHECKING ALL DATA FOR 2-YEAR MINIMUM")
print("=" * 80)

# Two years = ~504 trading days
MIN_ROWS = 504
TWO_YEARS_AGO = datetime.now() - timedelta(days=730)

# 1. Check all price tables
print("\n1. CHECKING PRICE TABLES")
print("-" * 40)

price_tables = [
    ('soybean_oil_prices', 'ZL', 'ZL=F'),
    ('soybean_prices', 'ZS', 'ZS=F'),
    ('corn_prices', 'ZC', 'ZC=F'),
    ('wheat_prices', 'ZW', 'ZW=F'),
    ('cotton_prices', 'CT', 'CT=F'),
    ('crude_oil_prices', 'CL', 'CL=F'),
    ('palm_oil_prices', 'PALM', 'FCPO.KL'),
    ('soybean_meal_prices', 'ZM', 'ZM=F'),
    ('gold_prices', 'GC', 'GC=F'),
    ('natural_gas_prices', 'NG', 'NG=F'),
    ('vix_daily', 'VIX', '^VIX'),
    ('treasury_prices', 'TNX', '^TNX'),
    ('usd_index_prices', 'DXY', 'DX-Y.NYB'),
    ('cftc_cot', None, None),  # Can't get from yfinance
    ('usda_export_sales', None, None),  # Can't get from yfinance
]

tables_needing_data = []

for table, expected_symbol, yf_symbol in price_tables:
    try:
        # Get row count and date range
        if 'time' in ['time', 'timestamp']:  # Most tables use 'time'
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MIN(DATE(time)) as first_date,
                MAX(DATE(time)) as last_date
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            WHERE time IS NOT NULL
            """
        else:  # Some use 'date'
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            WHERE date IS NOT NULL
            """
        
        try:
            result = list(client.query(query))
        except:
            # Try with date column
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            WHERE date IS NOT NULL
            """
            try:
                result = list(client.query(query))
            except:
                # Try report_date for CFTC/USDA
                query = f"""
                SELECT 
                    COUNT(*) as row_count,
                    MIN(report_date) as first_date,
                    MAX(report_date) as last_date
                FROM `cbi-v14.forecasting_data_warehouse.{table}`
                WHERE report_date IS NOT NULL
                """
                result = list(client.query(query))
        
        if result:
            row_count = result[0].row_count
            first_date = result[0].first_date
            last_date = result[0].last_date
            
            print(f"\n{table}:")
            print(f"  Rows: {row_count}")
            print(f"  Date range: {first_date} to {last_date}")
            
            if row_count < MIN_ROWS and yf_symbol:
                print(f"  ⚠️ NEEDS MORE DATA! Only {row_count} rows, need {MIN_ROWS}")
                tables_needing_data.append((table, expected_symbol, yf_symbol, row_count))
            elif row_count < MIN_ROWS:
                print(f"  ⚠️ NEEDS MORE DATA but no yfinance symbol available")
            else:
                print(f"  ✅ Has sufficient data")
                
    except Exception as e:
        print(f"\n{table}: Error - {str(e)[:100]}")

# 2. Backfill tables that need more data
if tables_needing_data:
    print("\n" + "=" * 80)
    print("2. BACKFILLING TABLES WITH < 2 YEARS DATA")
    print("-" * 40)
    
    for table, db_symbol, yf_symbol, current_rows in tables_needing_data:
        print(f"\nBackfilling {table} (currently {current_rows} rows)...")
        
        try:
            # Fetch 3 years to be safe
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1095)  # 3 years
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if len(df) > 0:
                print(f"  ✅ Fetched {len(df)} rows from yfinance")
                
                # Prepare data
                df.reset_index(inplace=True)
                df['time'] = pd.to_datetime(df['Date'])
                df['symbol'] = db_symbol if db_symbol else yf_symbol.replace('=F', '').replace('^', '')
                df['open'] = df['Open']
                df['high'] = df['High']
                df['low'] = df['Low']
                df['close'] = df['Close']
                df['volume'] = df['Volume'].astype('Int64')
                df['source_name'] = 'yfinance_backfill'
                df['confidence_score'] = 0.95
                df['ingest_timestamp_utc'] = pd.Timestamp.now()
                df['provenance_uuid'] = f"backfill_{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Handle special cases
                if table == 'crude_oil_prices':
                    # Has different schema
                    df.rename(columns={'close': 'close_price', 'open': 'open_price', 
                                      'high': 'high_price', 'low': 'low_price'}, inplace=True)
                    df['date'] = df['time'].dt.date
                    
                # Check for existing data to avoid duplicates
                if table == 'crude_oil_prices':
                    date_col = 'date'
                else:
                    date_col = 'time'
                    
                query = f"""
                SELECT DISTINCT DATE({date_col}) as existing_date
                FROM `cbi-v14.forecasting_data_warehouse.{table}`
                """
                existing_dates = set()
                for row in client.query(query):
                    existing_dates.add(row.existing_date)
                
                # Filter out existing dates
                df['check_date'] = df['time'].dt.date
                df = df[~df['check_date'].isin(existing_dates)]
                df = df.drop('check_date', axis=1)
                
                if len(df) > 0:
                    print(f"  Loading {len(df)} new rows (after deduplication)...")
                    
                    # Load to BigQuery
                    df.to_gbq(
                        destination_table=f'forecasting_data_warehouse.{table}',
                        project_id='cbi-v14',
                        if_exists='append',
                        progress_bar=False
                    )
                    
                    print(f"  ✅ Loaded {len(df)} new rows to {table}")
                else:
                    print(f"  ℹ️ No new data to load (all dates already exist)")
                    
        except Exception as e:
            print(f"  ❌ Error backfilling {table}: {str(e)[:150]}")

# 3. Special handling for low-data tables
print("\n" + "=" * 80)
print("3. SPECIAL CASES")
print("-" * 40)

# CFTC COT - only 72 rows, need weekly data for 2 years (104 weeks)
print("\nCFTC COT:")
print("  Current: 72 rows (weekly data)")
print("  ⚠️ Need more historical CFTC data (not available via yfinance)")
print("  → Would need to get from CFTC.gov historical downloads")

# USDA Export Sales - only 12 rows
print("\nUSDA Export Sales:")
print("  Current: 12 rows")
print("  ⚠️ Need more historical USDA data (not available via yfinance)")
print("  → Would need to get from USDA FAS historical reports")

# 4. Final verification
print("\n" + "=" * 80)
print("4. FINAL DATA STATUS")
print("-" * 40)

critical_tables = [
    'soybean_oil_prices',
    'sp500_prices',
    'crude_oil_prices',
    'vix_daily',
    'economic_indicators'
]

for table in critical_tables:
    try:
        if table == 'economic_indicators':
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                COUNT(DISTINCT DATE(time)) as unique_days
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
        elif 'time' in ['time']:
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                COUNT(DISTINCT DATE(time)) as unique_days
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
        else:
            query = f"""
            SELECT 
                COUNT(*) as row_count,
                COUNT(DISTINCT date) as unique_days
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            """
        
        result = list(client.query(query))
        if result:
            row_count = result[0].row_count
            unique_days = result[0].unique_days
            status = "✅" if unique_days >= MIN_ROWS else "⚠️"
            print(f"{status} {table}: {row_count:,} rows ({unique_days} unique days)")
    except:
        print(f"❌ {table}: Error checking")

print("\n" + "=" * 80)
print("BACKFILL COMPLETE!")
print("=" * 80)
