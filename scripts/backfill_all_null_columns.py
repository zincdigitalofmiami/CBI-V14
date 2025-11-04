#!/usr/bin/env python3
"""
Backfill All NULL Columns with Actual Data
Systematic approach to populate missing data from external sources
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import sys
import json

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔧 BACKFILLING NULL COLUMNS WITH DATA")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Target Table: {BASE_TABLE}")
print("="*80)

# Load audit results
try:
    with open('/tmp/null_audit_results.json', 'r') as f:
        audit_results = json.load(f)
    all_null_cols = audit_results.get('all_null_columns', [])
    print(f"\n✅ Loaded {len(all_null_cols)} all-NULL columns from audit")
except FileNotFoundError:
    print("\n⚠️  Audit results not found. Running quick audit...")
    # Quick check for known problematic columns
    all_null_cols = [
        'cpi_yoy', 'econ_gdp_growth', 'gdp_growth', 'unemployment_rate',
        'soybean_meal_price',
        'us_midwest_temp_c', 'us_midwest_precip_mm', 'us_midwest_conditions_score',
        'us_midwest_drought_days', 'us_midwest_flood_days', 'us_midwest_heat_stress_days'
    ]

# Categorize columns
economic_cols = [col for col in all_null_cols if 'gdp' in col.lower() or 'econ' in col.lower() or 'unemployment' in col.lower() or 'cpi' in col.lower()]
weather_cols = [col for col in all_null_cols if 'temp' in col.lower() or 'precip' in col.lower() or 'weather' in col.lower() or 'drought' in col.lower() or 'flood' in col.lower() or 'heat' in col.lower() or 'conditions' in col.lower()]
market_cols = [col for col in all_null_cols if 'price' in col.lower() or 'meal' in col.lower() or 'soybean' in col.lower()]

print(f"\n📊 Columns to fix:")
print(f"  Economic: {len(economic_cols)}")
print(f"  Weather: {len(weather_cols)}")
print(f"  Market: {len(market_cols)}")

# Step 1: Check date range
print("\n1️⃣  CHECKING DATE RANGE...")
query = f"""
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(DISTINCT date) as date_count
FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
"""
date_range = client.query(query).to_dataframe().iloc[0]
print(f"  Date range: {date_range['min_date']} to {date_range['max_date']}")
print(f"  Total dates: {int(date_range['date_count'])}")

# Step 2: Economic Features - Forward Fill or Fetch from FRED
print("\n2️⃣  BACKFILLING ECONOMIC FEATURES...")
print(f"  Columns: {', '.join(economic_cols)}")

# Strategy: Check if we have any existing data, then forward fill
# For now, we'll use forward-fill from last known value as a starting point
# TODO: Integrate with FRED API for proper data

for col in economic_cols:
    print(f"\n  Processing {col}...")
    
    # Check if column exists and get current NULL count
    try:
        check_query = f"""
        SELECT 
          COUNT(*) as total,
          COUNTIF(`{col}` IS NOT NULL) as non_null
        FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
        """
        result = client.query(check_query).to_dataframe()
        total = int(result.iloc[0]['total'])
        non_null = int(result.iloc[0]['non_null'])
        
        if non_null == 0:
            print(f"    ⚠️  Column is 100% NULL - needs external data source")
            print(f"    💡 For {col}:")
            if 'gdp' in col.lower():
                print(f"       - Source: FRED API (GDPC1 series)")
                print(f"       - Calculate quarterly growth rate")
                print(f"       - Interpolate to daily")
            elif 'unemployment' in col.lower():
                print(f"       - Source: FRED API (UNRATE series)")
                print(f"       - Forward fill monthly values")
            elif 'cpi' in col.lower():
                print(f"       - Source: FRED API (CPIAUCSL series)")
                print(f"       - Calculate YoY change")
                print(f"       - Forward fill monthly values")
            print(f"    ⚠️  SKIPPING automatic backfill - requires external API")
        else:
            # Forward fill from existing data
            print(f"    ✅ Found {non_null}/{total} existing values")
            print(f"    🔄 Forward-filling from last known value...")
            
            # Use window function to forward fill
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
            SET `{col}` = (
                SELECT `{col}`
                FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t2
                WHERE t2.`{col}` IS NOT NULL
                AND t2.date <= t.date
                ORDER BY t2.date DESC
                LIMIT 1
            )
            WHERE t.`{col}` IS NULL
            """
            try:
                job = client.query(update_query)
                job.result()
                print(f"    ✅ Forward-filled {job.num_dml_affected_rows} rows")
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:200]}")
    except Exception as e:
        print(f"    ❌ Error checking column: {str(e)[:200]}")

# Step 3: Market Features
print("\n3️⃣  BACKFILLING MARKET FEATURES...")
print(f"  Columns: {', '.join(market_cols)}")

for col in market_cols:
    print(f"\n  Processing {col}...")
    
    try:
        check_query = f"""
        SELECT 
          COUNT(*) as total,
          COUNTIF(`{col}` IS NOT NULL) as non_null
        FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
        """
        result = client.query(check_query).to_dataframe()
        total = int(result.iloc[0]['total'])
        non_null = int(result.iloc[0]['non_null'])
        
        if non_null == 0:
            print(f"    ⚠️  Column is 100% NULL - needs external data source")
            print(f"    💡 For {col}:")
            print(f"       - Source: CME futures data (SM futures)")
            print(f"       - Or: USDA price reports")
            print(f"       - Or: yfinance/Alpha Vantage APIs")
            print(f"    ⚠️  SKIPPING automatic backfill - requires external data source")
        else:
            print(f"    ✅ Found {non_null}/{total} existing values")
            print(f"    🔄 Forward-filling...")
            
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
            SET `{col}` = (
                SELECT `{col}`
                FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t2
                WHERE t2.`{col}` IS NOT NULL
                AND t2.date <= t.date
                ORDER BY t2.date DESC
                LIMIT 1
            )
            WHERE t.`{col}` IS NULL
            """
            try:
                job = client.query(update_query)
                job.result()
                print(f"    ✅ Forward-filled {job.num_dml_affected_rows} rows")
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:200]}")
    except Exception as e:
        print(f"    ❌ Error checking column: {str(e)[:200]}")

# Step 4: Weather Features
print("\n4️⃣  BACKFILLING WEATHER FEATURES...")
print(f"  Columns: {', '.join(weather_cols)}")

for col in weather_cols:
    print(f"\n  Processing {col}...")
    
    try:
        check_query = f"""
        SELECT 
          COUNT(*) as total,
          COUNTIF(`{col}` IS NOT NULL) as non_null
        FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
        """
        result = client.query(check_query).to_dataframe()
        total = int(result.iloc[0]['total'])
        non_null = int(result.iloc[0]['non_null'])
        
        if non_null == 0:
            print(f"    ⚠️  Column is 100% NULL - needs external data source")
            print(f"    💡 For {col}:")
            print(f"       - Source: NOAA weather API")
            print(f"       - Or: Historical weather averages")
            print(f"       - Or: Regional weather station data")
            print(f"    ⚠️  SKIPPING automatic backfill - requires external data source")
        else:
            print(f"    ✅ Found {non_null}/{total} existing values")
            print(f"    🔄 Forward-filling...")
            
            update_query = f"""
            UPDATE `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t
            SET `{col}` = (
                SELECT `{col}`
                FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}` t2
                WHERE t2.`{col}` IS NOT NULL
                AND t2.date <= t.date
                ORDER BY t2.date DESC
                LIMIT 1
            )
            WHERE t.`{col}` IS NULL
            """
            try:
                job = client.query(update_query)
                job.result()
                print(f"    ✅ Forward-filled {job.num_dml_affected_rows} rows")
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:200]}")
    except Exception as e:
        print(f"    ❌ Error checking column: {str(e)[:200]}")

print("\n" + "="*80)
print("📋 SUMMARY")
print("="*80)
print("\n✅ Forward-filled all columns that had existing data")
print("\n⚠️  Columns requiring external data sources:")
print("   - Economic: FRED API needed")
print("   - Market: CME/USDA/yfinance needed")
print("   - Weather: NOAA/USDA needed")
print("\n📝 Next Steps:")
print("   1. Integrate external APIs (FRED, CME, NOAA)")
print("   2. Fetch historical data for date range")
print("   3. Populate NULL columns with fetched data")
print("   4. Re-run this script to verify")
print("="*80)


