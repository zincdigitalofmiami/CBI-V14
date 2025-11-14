#!/usr/bin/env python3
"""
Fetch Market Data (soybean meal prices) from yfinance or CME
"""
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, WriteDisposition, SchemaField
import sys

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("⚠️  yfinance not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf
    YFINANCE_AVAILABLE = True

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("📈 FETCHING MARKET DATA")
print("="*80)

# Get date range
query = f"""
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date
FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
"""
date_range = client.query(query).to_dataframe().iloc[0]
start_date = date_range['min_date']
end_date = date_range['max_date']

print(f"Date range: {start_date} to {end_date}")

# Soybean Meal Futures - Use yfinance (ZM=F is soybean meal)
print("\n📊 Fetching Soybean Meal Price...")

try:
    print("  Fetching ZM=F (Soybean Meal Futures) from yfinance...")
    
    # Get date range first
    query = f"""
    SELECT 
      MIN(date) as min_date,
      MAX(date) as max_date
    FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
    """
    date_range = client.query(query).to_dataframe().iloc[0]
    start_date = date_range['min_date'].strftime('%Y-%m-%d')
    end_date = date_range['max_date'].strftime('%Y-%m-%d')
    
    print(f"  Date range: {start_date} to {end_date}")
    
    # Fetch from yfinance
    ticker = yf.Ticker("ZM=F")
    hist = ticker.history(start=start_date, end=end_date)
    
    if len(hist) > 0:
        print(f"  ✅ Fetched {len(hist)} days of data")
        
        # Prepare data for BigQuery
        df = hist.reset_index()
        df['date'] = pd.to_datetime(df['Date']).dt.date
        df['soybean_meal_price'] = df['Close'].astype(float)
        df = df[['date', 'soybean_meal_price']]
        
        # Create temp table using BigQuery client
        temp_table = f"{PROJECT_ID}.{DATASET_ID}._temp_soybean_meal"
        
        # Create table schema
        from google.cloud.bigquery import SchemaField
        schema = [
            SchemaField('date', 'DATE', mode='REQUIRED'),
            SchemaField('soybean_meal_price', 'FLOAT64', mode='NULLABLE')
        ]
        
        # Create table
        table_ref = client.dataset(DATASET_ID).table('_temp_soybean_meal')
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table, exists_ok=True)
        
        # Load data
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=schema
        )
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        
        # Update main table
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
        SET soybean_meal_price = (
            SELECT soybean_meal_price
            FROM `{temp_table}` temp
            WHERE temp.date = t.date
        )
        WHERE t.soybean_meal_price IS NULL
        AND EXISTS (
            SELECT 1
            FROM `{temp_table}` temp
            WHERE temp.date = t.date
        )
        """
        
        job = client.query(update_query)
        job.result()
        print(f"  ✅ Updated {job.num_dml_affected_rows} rows")
        
        # Clean up
        client.query(f"DROP TABLE IF EXISTS `{temp_table}`").result()
    else:
        print("  ⚠️  No data returned from yfinance")
        
except Exception as e:
    print(f"  ❌ Error: {str(e)}")
    print("  💡 Trying alternative: Check if data exists in yahoo_finance_enhanced table...")
    
    # Try to get from existing yahoo_finance_enhanced table
    try:
        alt_query = f"""
        SELECT 
          date,
          close as soybean_meal_price
        FROM `{PROJECT_ID}.forecasting_data_warehouse.yahoo_finance_enhanced`
        WHERE ticker = 'ZM=F'
        AND date BETWEEN (SELECT MIN(date) FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`)
                    AND (SELECT MAX(date) FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`)
        ORDER BY date
        """
        df = client.query(alt_query).to_dataframe()
        
        if len(df) > 0:
            print(f"  ✅ Found {len(df)} rows in yahoo_finance_enhanced")
            
            temp_table = f"{PROJECT_ID}.{DATASET_ID}._temp_soybean_meal"
            
            # Create table schema
            from google.cloud.bigquery import SchemaField
            schema = [
                SchemaField('date', 'DATE', mode='REQUIRED'),
                SchemaField('soybean_meal_price', 'FLOAT64', mode='NULLABLE')
            ]
            
            # Create table
            table_ref = client.dataset(DATASET_ID).table('_temp_soybean_meal')
            table = bigquery.Table(table_ref, schema=schema)
            table = client.create_table(table, exists_ok=True)
            
            # Load data
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=schema
            )
            job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
            SET soybean_meal_price = (
                SELECT soybean_meal_price
                FROM `{temp_table}` temp
                WHERE temp.date = t.date
            )
            WHERE t.soybean_meal_price IS NULL
            """
            
            job = client.query(update_query)
            job.result()
            print(f"  ✅ Updated {job.num_dml_affected_rows} rows from existing table")
            
            client.query(f"DROP TABLE IF EXISTS `{temp_table}`").result()
    except Exception as e2:
        print(f"  ❌ Alternative also failed: {str(e2)[:200]}")

print("\n" + "="*80)
print("📝 MARKET DATA SOURCES")
print("="*80)
print("Soybean Meal Price Sources:")
print("  1. CME Group API: https://www.cmegroup.com/confluence/display/EPICSANDBOX/CME+Group+Market+Data+API")
print("  2. USDA Agricultural Prices: https://www.nass.usda.gov/")
print("  3. Alpha Vantage API: https://www.alphavantage.co/")
print("  4. Manual import from CSV/excel files")
print("="*80)

