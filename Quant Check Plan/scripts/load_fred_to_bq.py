"""
Load FRED Economic Data to BigQuery
Source: External drive parquet file
Target: raw_intelligence.fred_economic

NO YAHOO - Uses FRED parquet from external drive
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime

# Config
PROJECT = 'cbi-v14'
TARGET_TABLE = f'{PROJECT}.raw_intelligence.fred_economic'

# Source file
FRED_FILE = '/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/fred/combined/fred_all_series_20251117.parquet'

# Column mapping (FRED name -> BQ column)
COLUMN_MAP = {
    'date': 'date',
    'Federal Funds Rate': 'fred_fed_funds_rate',
    '10-Year Treasury Constant Maturity Rate': 'fred_10y_yield',
    '2-Year Treasury Constant Maturity Rate': 'fred_2y_yield',
    '10-Year Treasury Constant Maturity Minus 2-Year': 'fred_yield_curve_10y_2y',
    'CBOE Volatility Index: VIX': 'fred_vix',
    'Trade Weighted U.S. Dollar Index: Broad, Goods': 'fred_usd_index',
    'Consumer Price Index for All Urban Consumers': 'fred_cpi',
    'Unemployment Rate': 'fred_unemployment',
    'Crude Oil Prices: West Texas Intermediate (WTI)': 'fred_crude_oil_wti',
    'U.S. / Euro Foreign Exchange Rate': 'fred_usd_eur_rate',
    'China / U.S. Foreign Exchange Rate': 'fred_usd_cny_rate',
    'Brazil / U.S. Foreign Exchange Rate': 'fred_usd_brl_rate',
    'Industrial Production Index': 'fred_industrial_production',
    'TED Spread': 'fred_ted_spread',
    'St. Louis Fed Financial Stress Index': 'fred_financial_stress',
}

def main():
    print("=" * 60)
    print("FRED DATA LOAD TO BIGQUERY")
    print("=" * 60)
    
    # 1. Read parquet
    print("\n1. Reading FRED parquet file...")
    df = pd.read_parquet(FRED_FILE)
    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    # 2. Select and rename columns
    print("\n2. Selecting relevant columns...")
    available_cols = [c for c in COLUMN_MAP.keys() if c in df.columns]
    missing_cols = [c for c in COLUMN_MAP.keys() if c not in df.columns]
    
    if missing_cols:
        print(f"   Missing columns: {missing_cols}")
    
    df_selected = df[available_cols].copy()
    df_selected = df_selected.rename(columns=COLUMN_MAP)
    print(f"   Selected {len(df_selected.columns)} columns")
    
    # 3. Convert date
    print("\n3. Converting date column...")
    df_selected['date'] = pd.to_datetime(df_selected['date']).dt.date
    
    # 4. Drop duplicates (keep first per date)
    print("\n4. Removing duplicates...")
    before = len(df_selected)
    df_selected = df_selected.drop_duplicates(subset=['date'], keep='first')
    print(f"   Removed {before - len(df_selected)} duplicates")
    print(f"   Final rows: {len(df_selected)}")
    
    # 5. Add metadata
    df_selected['load_ts'] = datetime.utcnow()
    
    # 6. Show sample
    print("\n5. Sample data:")
    print(df_selected.head(3).to_string())
    
    # 7. Check for VIX
    vix_count = df_selected['fred_vix'].notna().sum()
    print(f"\n   VIX values: {vix_count} non-null")
    
    # 8. Load to BigQuery
    print(f"\n6. Loading to {TARGET_TABLE}...")
    client = bigquery.Client(project=PROJECT)
    
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',
    )
    
    job = client.load_table_from_dataframe(df_selected, TARGET_TABLE, job_config=job_config)
    job.result()
    print("   Done!")
    
    # 9. Verify
    result = client.query(f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNTIF(fred_vix IS NOT NULL) as vix_rows,
            COUNTIF(fred_fed_funds_rate IS NOT NULL) as fed_rows,
            COUNTIF(fred_usd_index IS NOT NULL) as usd_rows
        FROM `{TARGET_TABLE}`
    """).to_dataframe()
    
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"   Total rows: {result['total_rows'].iloc[0]}")
    print(f"   Date range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
    print(f"   VIX rows: {result['vix_rows'].iloc[0]}")
    print(f"   Fed Funds rows: {result['fed_rows'].iloc[0]}")
    print(f"   USD Index rows: {result['usd_rows'].iloc[0]}")
    print("\n✅ FRED LOAD COMPLETE")

if __name__ == '__main__':
    main()





