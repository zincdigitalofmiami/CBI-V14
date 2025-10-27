#!/usr/bin/env python3
"""
FIND AND INTEGRATE ALL MISSING DATA
Comprehensive scan of BigQuery to find all available data
and properly wire it into the training dataset
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

print("="*80)
print("COMPREHENSIVE DATA DISCOVERY AND INTEGRATION")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# 1. DISCOVER ALL AVAILABLE TABLES
print("\n1. DISCOVERING ALL AVAILABLE DATA SOURCES")
print("-"*40)

# Get all datasets
datasets = list(client.list_datasets())
print(f"Found {len(datasets)} datasets in project")

all_tables = {}
for dataset in datasets:
    dataset_id = dataset.dataset_id
    tables = list(client.list_tables(dataset.reference))
    all_tables[dataset_id] = [table.table_id for table in tables]
    print(f"\n{dataset_id}: {len(tables)} tables")
    for table in tables[:10]:  # Show first 10
        print(f"  • {table.table_id}")
    if len(tables) > 10:
        print(f"  ... and {len(tables)-10} more")

# 2. CHECK FORECASTING DATA WAREHOUSE
print("\n2. CHECKING FORECASTING DATA WAREHOUSE")
print("-"*40)

warehouse_tables = all_tables.get('forecasting_data_warehouse', [])
print(f"Found {len(warehouse_tables)} tables in warehouse:")

# Check each table for data coverage
data_inventory = {}

for table_name in warehouse_tables:
    try:
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT DATE(CAST(
                COALESCE(
                    SAFE_CAST(date AS TIMESTAMP),
                    SAFE_CAST(time AS TIMESTAMP),
                    SAFE_CAST(report_date AS TIMESTAMP),
                    SAFE_CAST(timestamp AS TIMESTAMP)
                ) AS TIMESTAMP
            ))) as unique_dates,
            MIN(DATE(CAST(
                COALESCE(
                    SAFE_CAST(date AS TIMESTAMP),
                    SAFE_CAST(time AS TIMESTAMP),
                    SAFE_CAST(report_date AS TIMESTAMP),
                    SAFE_CAST(timestamp AS TIMESTAMP)
                ) AS TIMESTAMP
            ))) as min_date,
            MAX(DATE(CAST(
                COALESCE(
                    SAFE_CAST(date AS TIMESTAMP),
                    SAFE_CAST(time AS TIMESTAMP),
                    SAFE_CAST(report_date AS TIMESTAMP),
                    SAFE_CAST(timestamp AS TIMESTAMP)
                ) AS TIMESTAMP
            ))) as max_date
        FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
        """
        
        result = client.query(query).to_dataframe()
        if not result.empty and result['row_count'].iloc[0] > 0:
            data_inventory[table_name] = {
                'rows': result['row_count'].iloc[0],
                'dates': result['unique_dates'].iloc[0],
                'min_date': result['min_date'].iloc[0],
                'max_date': result['max_date'].iloc[0]
            }
            print(f"\n{table_name}:")
            print(f"  Rows: {result['row_count'].iloc[0]:,}")
            print(f"  Date range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")
            
    except Exception as e:
        # Try without date column
        try:
            query = f"""
            SELECT COUNT(*) as row_count
            FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
            """
            result = client.query(query).to_dataframe()
            if not result.empty and result['row_count'].iloc[0] > 0:
                data_inventory[table_name] = {'rows': result['row_count'].iloc[0]}
                print(f"\n{table_name}: {result['row_count'].iloc[0]:,} rows (no date column)")
        except:
            pass

# 3. CHECK SPECIFIC MISSING DATA
print("\n3. SEARCHING FOR MISSING DATA COMPONENTS")
print("-"*40)

# Check for CFTC managed money data
print("\n🔍 CFTC Managed Money Data:")
cftc_tables = [t for t in warehouse_tables if 'cftc' in t.lower() or 'cot' in t.lower()]
for table in cftc_tables:
    print(f"  Checking {table}...")
    try:
        query = f"""
        SELECT *
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        LIMIT 1
        """
        sample = client.query(query).to_dataframe()
        
        # Look for managed money columns
        managed_cols = [c for c in sample.columns if 'managed' in c.lower() or 'money' in c.lower()]
        if managed_cols:
            print(f"    ✓ Found managed money columns: {managed_cols}")
            
            # Check if data is filled
            query = f"""
            SELECT COUNT(*) as filled
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            WHERE {managed_cols[0]} IS NOT NULL AND {managed_cols[0]} != 0
            """
            filled = client.query(query).to_dataframe()
            print(f"    Data points: {filled['filled'].iloc[0]}")
            
    except Exception as e:
        print(f"    Error: {str(e)[:50]}")

# Check for Treasury data
print("\n🔍 Treasury Yield Data:")
treasury_tables = [t for t in warehouse_tables if 'treasury' in t.lower() or 'yield' in t.lower() or 'bond' in t.lower()]
for table in treasury_tables:
    print(f"  Found: {table}")
    if table in data_inventory:
        print(f"    {data_inventory[table]['rows']:,} rows")

# Check for Economic data
print("\n🔍 Economic Indicators:")
econ_tables = [t for t in warehouse_tables if 'econ' in t.lower() or 'gdp' in t.lower() or 'cpi' in t.lower() or 'unemployment' in t.lower()]
for table in econ_tables:
    print(f"  Found: {table}")
    if table in data_inventory:
        print(f"    {data_inventory[table]['rows']:,} rows")

# Check for Weather data
print("\n🔍 Weather Data:")
weather_tables = [t for t in warehouse_tables if 'weather' in t.lower() or 'temperature' in t.lower() or 'precip' in t.lower()]
for table in weather_tables:
    print(f"  Found: {table}")
    if table in data_inventory:
        print(f"    {data_inventory[table]['rows']:,} rows")

# 4. CHECK SCHEMA OF KEY TABLES
print("\n4. ANALYZING SCHEMA OF KEY DATA SOURCES")
print("-"*40)

key_tables = ['cftc_cot', 'treasury_prices', 'economic_indicators', 'weather_data', 'currency_data']

for table_name in key_tables:
    if table_name in warehouse_tables:
        print(f"\n{table_name} Schema:")
        try:
            table_ref = client.dataset('forecasting_data_warehouse').table(table_name)
            table = client.get_table(table_ref)
            
            for field in table.schema[:10]:  # Show first 10 fields
                print(f"  • {field.name} ({field.field_type})")
            
            if len(table.schema) > 10:
                print(f"  ... and {len(table.schema)-10} more fields")
                
        except Exception as e:
            print(f"  Error: {str(e)[:50]}")

print("\n" + "="*80)
print("DATA DISCOVERY COMPLETE")
print("="*80)
