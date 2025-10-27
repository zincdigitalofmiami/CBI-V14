#!/usr/bin/env python3
"""
CHECK EVERY FUCKING TABLE'S SCHEMA
Because NOTHING is consistent - every table uses different column names!
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"CHECKING ALL TABLE SCHEMAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Finding out what column names each table ACTUALLY uses")
print("="*80)

# Tables we need to check for the training dataset
tables_to_check = [
    'cftc_cot',
    'treasury_prices',
    'economic_indicators',
    'news_intelligence',
    'vix_daily',
    'currency_data',
    'usda_export_sales',
    'usda_harvest_progress',
    'biofuel_prices',
    'social_sentiment',
    'trump_policy_intelligence',
    'volatility_data',
    'soybean_oil_prices',
    'weather_data'
]

schema_info = {}

for table in tables_to_check:
    print(f"\n{table}:")
    print("-"*40)
    
    try:
        # Get first row to see actual columns
        query = f"SELECT * FROM `cbi-v14.forecasting_data_warehouse.{table}` LIMIT 1"
        df = client.query(query).to_dataframe()
        
        columns = list(df.columns)
        schema_info[table] = columns
        
        # Find date/time column
        date_cols = [c for c in columns if 'date' in c.lower() or 'time' in c.lower()]
        value_cols = [c for c in columns if 'value' in c.lower() or 'close' in c.lower() or 'price' in c.lower()]
        
        print(f"  Total columns: {len(columns)}")
        print(f"  Date/Time columns: {date_cols}")
        print(f"  Value columns: {value_cols}")
        print(f"  All columns: {', '.join(columns[:10])}")
        if len(columns) > 10:
            print(f"    ... and {len(columns)-10} more")
            
    except Exception as e:
        print(f"  ERROR: {str(e)[:100]}")

print("\n" + "="*80)
print("SCHEMA INCONSISTENCIES FOUND:")
print("="*80)

# Analyze inconsistencies
date_columns_used = {}
value_columns_used = {}

for table, columns in schema_info.items():
    # Find what they call their date column
    for col in columns:
        if 'date' in col.lower() or 'time' in col.lower():
            if col not in date_columns_used:
                date_columns_used[col] = []
            date_columns_used[col].append(table)
    
    # Find what they call their value column
    for col in columns:
        if 'value' in col.lower() or 'close' in col.lower() or 'price' in col.lower():
            if col not in value_columns_used:
                value_columns_used[col] = []
            value_columns_used[col].append(table)

print("\nDATE/TIME COLUMN NAMES USED:")
for col_name, tables in sorted(date_columns_used.items()):
    print(f"  '{col_name}': {len(tables)} tables")
    for table in tables[:3]:
        print(f"    - {table}")

print("\nVALUE/PRICE COLUMN NAMES USED:")
for col_name, tables in sorted(value_columns_used.items())[:10]:  # Show first 10
    print(f"  '{col_name}': {len(tables)} tables")
    for table in tables[:2]:
        print(f"    - {table}")

print("\n" + "="*80)
print("MAPPING REQUIRED FOR EACH TABLE:")
print("="*80)

# Create mapping for each table
for table in tables_to_check:
    if table in schema_info:
        columns = schema_info[table]
        
        # Find date column
        date_col = None
        for col in columns:
            if 'date' in col.lower():
                date_col = col
                break
            elif 'time' in col.lower():
                date_col = col
                break
        
        # Find value column
        value_col = None
        for col in columns:
            if table in ['economic_indicators'] and col == 'value':
                value_col = 'value'
                break
            elif 'close' in col:
                value_col = col
                break
            elif 'price' in col:
                value_col = col
                break
            elif 'value' in col:
                value_col = col
                break
        
        print(f"\n{table}:")
        print(f"  Date column: {date_col}")
        print(f"  Value column: {value_col}")

print("\n" + "="*80)
print("THIS IS WHY NOTHING WORKS!")
print("="*80)
print("Every table uses different column names!")
print("We need to handle EACH table's specific schema!")
