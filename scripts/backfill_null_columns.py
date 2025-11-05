#!/usr/bin/env python3
"""
Backfill NULL columns in training_dataset_super_enriched
Focuses on economic, weather, and market features
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔧 BACKFILLING NULL COLUMNS")
print("="*80)

# Load audit results
import json
try:
    with open('/tmp/null_audit_results.json', 'r') as f:
        audit_results = json.load(f)
    all_null_cols = audit_results.get('all_null_columns', [])
    print(f"Loaded {len(all_null_cols)} all-NULL columns from audit")
except FileNotFoundError:
    print("❌ Audit results not found. Run comprehensive_null_audit.py first")
    sys.exit(1)

# Strategy 1: Economic features - forward fill from last known value
print("\n1️⃣  BACKFILLING ECONOMIC FEATURES...")
economic_cols = [col for col in all_null_cols if 'gdp' in col.lower() or 'econ' in col.lower()]
print(f"  Economic columns to fix: {len(economic_cols)}")

for col in economic_cols[:5]:  # Start with first 5
    print(f"\n  Processing {col}...")
    
    # Strategy: Forward fill from last known value, or use default if never populated
    # First check if ANY value exists in any table
    query = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
    WHERE `{col}` IS NOT NULL
    """
    result = client.query(query).to_dataframe()
    has_data = result.iloc[0]['count'] > 0
    
    if has_data:
        # Forward fill
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
        print(f"    ✅ Forward-filling {col}...")
        try:
            job = client.query(update_query)
            job.result()
            print(f"    ✅ Updated {job.num_dml_affected_rows} rows")
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:200]}")
    else:
        print(f"    ⚠️  No existing data found - column may need external source")

# Strategy 2: Weather features - use regional averages or nearby stations
print("\n2️⃣  BACKFILLING WEATHER FEATURES...")
weather_cols = [col for col in all_null_cols if 'temp' in col.lower() or 'precip' in col.lower() or 'weather' in col.lower() or 'drought' in col.lower() or 'flood' in col.lower() or 'heat' in col.lower() or 'conditions' in col.lower()]
print(f"  Weather columns to fix: {len(weather_cols)}")
print(f"  ⚠️  Weather features may require external data sources (NOAA, USDA)")
print(f"  💡 Consider: Use historical averages or impute from nearby regions")

# Strategy 3: Market features - forward fill or use last known price
print("\n3️⃣  BACKFILLING MARKET FEATURES...")
market_cols = [col for col in all_null_cols if 'price' in col.lower() or 'meal' in col.lower() or 'soybean' in col.lower()]
print(f"  Market columns to fix: {len(market_cols)}")

for col in market_cols[:3]:  # Start with first 3
    print(f"\n  Processing {col}...")
    
    # Check if source data exists in other tables
    query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE '%meal%' OR table_name LIKE '%soybean%' OR table_name LIKE '%price%'
    LIMIT 5
    """
    source_tables = client.query(query).to_dataframe()['table_name'].tolist()
    
    if source_tables:
        print(f"    ✅ Found potential source tables: {', '.join(source_tables)}")
        print(f"    💡 Could join from source tables to backfill")
    else:
        print(f"    ⚠️  No source tables found - may need external data feed")

print("\n" + "="*80)
print("📋 SUMMARY")
print("="*80)
print(f"Total all-NULL columns: {len(all_null_cols)}")
print(f"Economic columns: {len(economic_cols)}")
print(f"Weather columns: {len(weather_cols)}")
print(f"Market columns: {len(market_cols)}")

print("\n💡 RECOMMENDATION:")
print("  For immediate training: Add all-NULL columns to EXCEPT clause")
print("  For proper fix: Investigate source data and backfill systematically")
print("="*80)



