#!/usr/bin/env python3
"""
Week 0 Day 4: Backfill Prefixed BigQuery Tables
Load staging files into the new prefixed table architecture.
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def backfill_yahoo_historical(client: bigquery.Client):
    """Backfill yahoo_historical_prefixed from staging."""
    
    print("\n" + "="*60)
    print("BACKFILL YAHOO HISTORICAL")
    print("="*60)
    
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    df = pd.read_parquet(staging_file)
    
    print(f"\nStaging file: {len(df)} rows, {df['symbol'].nunique()} symbols")
    print(f"Symbols: {sorted(df['symbol'].unique())}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Ensure date is proper type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.yahoo_historical_prefixed"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    print(f"\nLoading to {table_id}...")
    load_job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config, location=LOCATION
    )
    load_job.result()
    
    # Verify
    query = f"SELECT COUNT(*) as count, COUNT(DISTINCT symbol) as symbols FROM `{table_id}`"
    result = list(client.query(query, location=LOCATION).result())[0]
    
    print(f"✓ Loaded {result.count} rows, {result.symbols} symbols")
    
    return result.count

def backfill_fred_macro(client: bigquery.Client):
    """Backfill fred_macro_expanded from staging."""
    
    print("\n" + "="*60)
    print("BACKFILL FRED MACRO")
    print("="*60)
    
    staging_file = DRIVE / "staging/fred_macro_expanded.parquet"
    df = pd.read_parquet(staging_file)
    
    print(f"\nStaging file: {len(df)} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns: {len([c for c in df.columns if c.startswith('fred_')])} fred_ columns")
    
    # Ensure date is proper type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.fred_macro_expanded"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    print(f"\nLoading to {table_id}...")
    load_job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config, location=LOCATION
    )
    load_job.result()
    
    # Verify
    query = f"SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date FROM `{table_id}`"
    result = list(client.query(query, location=LOCATION).result())[0]
    
    print(f"✓ Loaded {result.count} rows ({result.min_date} to {result.max_date})")
    
    return result.count

def backfill_weather_granular(client: bigquery.Client):
    """Backfill weather_granular from staging."""
    
    print("\n" + "="*60)
    print("BACKFILL WEATHER GRANULAR")
    print("="*60)
    
    staging_file = DRIVE / "staging/weather_granular_daily.parquet"
    df = pd.read_parquet(staging_file)
    
    print(f"\nStaging file: {len(df)} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns: {len([c for c in df.columns if c.startswith('weather_')])} weather_ columns")
    
    # Ensure date is proper type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.weather_granular"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    print(f"\nLoading to {table_id}...")
    load_job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config, location=LOCATION
    )
    load_job.result()
    
    # Verify
    query = f"SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date FROM `{table_id}`"
    result = list(client.query(query, location=LOCATION).result())[0]
    
    print(f"✓ Loaded {result.count} rows ({result.min_date} to {result.max_date})")
    
    return result.count

def backfill_eia_energy(client: bigquery.Client):
    """Backfill eia_energy_granular from staging."""
    
    print("\n" + "="*60)
    print("BACKFILL EIA ENERGY")
    print("="*60)
    
    staging_file = DRIVE / "staging/eia_energy_granular.parquet"
    df = pd.read_parquet(staging_file)
    
    print(f"\nStaging file: {len(df)} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns: {len([c for c in df.columns if c.startswith('eia_')])} eia_ columns")
    
    # Ensure date is proper type
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.eia_energy_granular"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    print(f"\nLoading to {table_id}...")
    load_job = client.load_table_from_dataframe(
        df, table_id, job_config=job_config, location=LOCATION
    )
    load_job.result()
    
    # Verify
    query = f"SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date FROM `{table_id}`"
    result = list(client.query(query, location=LOCATION).result())[0]
    
    print(f"✓ Loaded {result.count} rows ({result.min_date} to {result.max_date})")
    
    return result.count

def verify_all_tables(client: bigquery.Client):
    """Verify all prefixed tables have data."""
    
    print("\n" + "="*60)
    print("VERIFICATION - ALL PREFIXED TABLES")
    print("="*60)
    
    tables_to_check = [
        "forecasting_data_warehouse.yahoo_historical_prefixed",
        "forecasting_data_warehouse.fred_macro_expanded",
        "forecasting_data_warehouse.weather_granular",
        "forecasting_data_warehouse.eia_energy_granular",
        "features.regime_calendar",
    ]
    
    print("\nRow counts:")
    total_rows = 0
    for table in tables_to_check:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{table}`"
        result = list(client.query(query, location=LOCATION).result())[0]
        print(f"  {table:60s} {result.count:,} rows")
        total_rows += result.count
    
    print(f"\nTotal rows across all tables: {total_rows:,}")
    
    # Check empty tables (should be Alpha tables until Week 2)
    empty_tables = [
        "forecasting_data_warehouse.alpha_commodities_daily",
        "forecasting_data_warehouse.alpha_es_intraday",
        "forecasting_data_warehouse.alpha_fx_daily",
        "forecasting_data_warehouse.alpha_indicators_daily",
        "forecasting_data_warehouse.alpha_news_sentiment",
        "forecasting_data_warehouse.alpha_options_snapshot",
        "forecasting_data_warehouse.cftc_commitments",
        "forecasting_data_warehouse.usda_reports_granular",
    ]
    
    print("\nEmpty tables (pending data collection):")
    for table in empty_tables:
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{table}`"
        result = list(client.query(query, location=LOCATION).result())[0]
        status = "✓ Empty (expected)" if result.count == 0 else f"⚠ {result.count} rows"
        print(f"  {table:60s} {status}")

def test_sample_queries(client: bigquery.Client):
    """Test that data can be queried and joined."""
    
    print("\n" + "="*60)
    print("SAMPLE QUERY TESTS")
    print("="*60)
    
    # Test 1: Yahoo data with regime weights
    print("\n1. Testing Yahoo + Regime join (ZL only):")
    query = """
    SELECT 
        y.date,
        y.symbol,
        y.yahoo_close,
        r.regime,
        r.training_weight
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed` y
    LEFT JOIN `cbi-v14.features.regime_calendar` r ON y.date = r.date
    WHERE y.symbol = 'ZL=F'
    ORDER BY y.date DESC
    LIMIT 5
    """
    result = client.query(query, location=LOCATION).result()
    rows = list(result)
    
    if rows:
        print("  ✓ Join successful - Sample rows:")
        for row in rows:
            print(f"    {row.date}: ${row.yahoo_close:.2f}, {row.regime} (weight={row.training_weight})")
    else:
        print("  ✗ No results")
    
    # Test 2: FRED data
    print("\n2. Testing FRED macro data:")
    query = """
    SELECT 
        date,
        fred_fed_funds_rate,
        fred_crude_oil_wti
    FROM `cbi-v14.forecasting_data_warehouse.fred_macro_expanded`
    ORDER BY date DESC
    LIMIT 5
    """
    result = client.query(query, location=LOCATION).result()
    rows = list(result)
    
    if rows:
        print("  ✓ Data accessible - Sample rows:")
        for row in rows:
            print(f"    {row.date}: Fed Funds={row.fred_fed_funds_rate}, Oil=${row.fred_crude_oil_wti}")
    else:
        print("  ✗ No results")
    
    # Test 3: Multi-table join
    print("\n3. Testing multi-source join (Yahoo + FRED + Weather + Regime):")
    query = """
    SELECT 
        y.date,
        y.yahoo_close as zl_price,
        f.fred_fed_funds_rate,
        w.weather_us_iowa_TAVG,
        r.training_weight
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed` y
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.fred_macro_expanded` f ON y.date = f.date
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_granular` w ON y.date = w.date
    LEFT JOIN `cbi-v14.features.regime_calendar` r ON y.date = r.date
    WHERE y.symbol = 'ZL=F'
      AND y.date >= '2024-01-01'
    ORDER BY y.date DESC
    LIMIT 5
    """
    result = client.query(query, location=LOCATION).result()
    rows = list(result)
    
    if rows:
        print("  ✓ Multi-source join successful - Sample rows:")
        for row in rows:
            print(f"    {row.date}: ZL=${row.zl_price:.2f}, Fed={row.fred_fed_funds_rate}, Iowa Temp={row.weather_us_iowa_TAVG}, Weight={row.training_weight}")
    else:
        print("  ✗ No results")

def main():
    """Execute Week 0 Day 4 backfill."""
    
    print("\n" + "="*70)
    print("WEEK 0 DAY 4: BACKFILL PREFIXED BIGQUERY TABLES")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    total_rows = 0
    
    # Backfill each staging file
    total_rows += backfill_yahoo_historical(client)
    total_rows += backfill_fred_macro(client)
    total_rows += backfill_weather_granular(client)
    total_rows += backfill_eia_energy(client)
    
    # Verify all tables
    verify_all_tables(client)
    
    # Test sample queries
    test_sample_queries(client)
    
    # Summary
    print("\n" + "="*70)
    print("✓ BACKFILL COMPLETE")
    print("="*70)
    print(f"\nTotal rows loaded: {total_rows:,}")
    print("\nTables populated:")
    print("  ✓ yahoo_historical_prefixed (ZL, palm, crude)")
    print("  ✓ fred_macro_expanded (16 economic series)")
    print("  ✓ weather_granular (60 region columns)")
    print("  ✓ eia_energy_granular (2 energy series)")
    print("  ✓ regime_calendar (already loaded)")
    
    print("\nPending (no raw data yet):")
    print("  ⏳ Alpha Vantage tables (Week 2)")
    print("  ⏳ USDA/CFTC tables (Week 0 Day 5)")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Week 0 Day 3 (resume): Fix 6 failed views now that data is loaded")
    print("2. Week 0 Day 5: Replace contaminated USDA/CFTC data")
    print("3. Week 0 Day 6-7: QA schemas for unprefixed columns")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    exit(main())

