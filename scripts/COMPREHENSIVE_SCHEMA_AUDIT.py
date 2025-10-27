#!/usr/bin/env python3
"""
COMPREHENSIVE SCHEMA AUDIT - FIND ALL MISMATCHES
Check EVERYTHING: names, schemas, columns, data types, wiring
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("COMPREHENSIVE SCHEMA AND DATA AUDIT")
print("=" * 80)

# 1. Check all price tables for schema consistency
print("\n1. PRICE TABLES SCHEMA AUDIT")
print("-" * 40)

price_tables = [
    'soybean_oil_prices',
    'soybean_prices', 
    'corn_prices',
    'wheat_prices',
    'cotton_prices',
    'crude_oil_prices',
    'palm_oil_prices',
    'treasury_prices',
    'vix_daily',
    'biofuel_prices',
    'canola_oil_prices',
    'rapeseed_oil_prices',
    'soybean_meal_prices',
    'usd_index_prices'
]

table_schemas = {}
for table in price_tables:
    try:
        query = f"""
        SELECT column_name, data_type, ordinal_position
        FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
        """
        columns = []
        for row in client.query(query):
            columns.append(f"{row.column_name}:{row.data_type}")
        
        if columns:
            table_schemas[table] = columns
            print(f"\n{table}:")
            
            # Check for critical columns
            has_date = any('date' in col.lower() for col in columns)
            has_time = any('time' in col.lower() for col in columns) 
            has_close = any('close' in col.lower() for col in columns)
            has_symbol = any('symbol' in col.lower() for col in columns)
            
            print(f"  ✓ Date column: {has_date}")
            print(f"  ✓ Time column: {has_time}")
            print(f"  ✓ Close price: {has_close}")
            print(f"  ✓ Symbol column: {has_symbol}")
            
            # Show first 3 columns
            print(f"  Columns: {', '.join(columns[:3])}...")
    except Exception as e:
        print(f"\n{table}: NOT FOUND")

# 2. Check for data contamination - wrong symbols in tables
print("\n" + "=" * 80)
print("2. DATA CONTAMINATION CHECK")
print("-" * 40)

contamination_checks = [
    ('soybean_oil_prices', 'ZL', 'symbol'),
    ('crude_oil_prices', ['CL', 'BRENT', 'WTI'], 'symbol'),
    ('palm_oil_prices', ['PALM', 'FCPO'], 'symbol'),
    ('corn_prices', ['C', 'CORN'], 'symbol'),
    ('wheat_prices', ['W', 'WHEAT'], 'symbol')
]

for table, expected_symbols, symbol_col in contamination_checks:
    try:
        # First check if table exists and has symbol column
        check_col_query = f"""
        SELECT column_name 
        FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}' AND column_name = '{symbol_col}'
        """
        has_symbol = list(client.query(check_col_query))
        
        if has_symbol:
            query = f"""
            SELECT DISTINCT {symbol_col} as symbol, COUNT(*) as row_count
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            GROUP BY {symbol_col}
            """
            print(f"\n{table} symbols:")
            for row in client.query(query):
                if isinstance(expected_symbols, list):
                    status = "✓" if row.symbol in expected_symbols else "❌ CONTAMINATION!"
                else:
                    status = "✓" if row.symbol == expected_symbols else "❌ CONTAMINATION!"
                print(f"  {status} {row.symbol}: {row.row_count} rows")
        else:
            print(f"\n{table}: No symbol column")
    except Exception as e:
        print(f"\n{table}: Error checking - {str(e)[:50]}")

# 3. Check view dependencies and references
print("\n" + "=" * 80)
print("3. VIEW DEPENDENCIES AUDIT")
print("-" * 40)

# Check which views reference staging vs main tables
query = """
SELECT 
    table_name as view_name,
    ddl
FROM `cbi-v14.models.INFORMATION_SCHEMA.VIEWS`
WHERE table_name LIKE '%training%' OR table_name LIKE '%correlation%'
"""

print("\nViews referencing STAGING (BAD!):")
for row in client.query(query):
    if 'staging.' in row.ddl.lower():
        print(f"  ❌ {row.view_name} -> references staging")
        
print("\nViews referencing MAIN tables (GOOD):")
for row in client.query(query):
    if 'forecasting_data_warehouse.' in row.ddl.lower() and 'staging.' not in row.ddl.lower():
        print(f"  ✓ {row.view_name}")

# 4. Check for duplicate/similar named objects
print("\n" + "=" * 80)
print("4. DUPLICATE/SIMILAR OBJECTS")
print("-" * 40)

all_objects = []
datasets = ['models', 'signals', 'neural', 'api', 'curated', 'forecasting_data_warehouse', 'staging']

for dataset in datasets:
    query = f"""
    SELECT table_name, table_type
    FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES`
    """
    try:
        for row in client.query(query):
            all_objects.append(f"{dataset}.{row.table_name}")
    except:
        pass

# Find similar names
print("\nPotential duplicates:")
for i, obj1 in enumerate(all_objects):
    for obj2 in all_objects[i+1:]:
        # Check if names are very similar
        name1 = obj1.split('.')[-1].lower()
        name2 = obj2.split('.')[-1].lower()
        if name1 in name2 or name2 in name1:
            if name1 != name2:
                print(f"  ? {obj1} <-> {obj2}")

# 5. Check data date ranges for consistency
print("\n" + "=" * 80)
print("5. DATA DATE RANGE CONSISTENCY")
print("-" * 40)

date_checks = [
    ('soybean_oil_prices', 'DATE(time)', 'symbol = "ZL"'),
    ('crude_oil_prices', 'date', '1=1'),
    ('palm_oil_prices', 'DATE(time)', '1=1'),
    ('social_sentiment', 'DATE(timestamp)', '1=1'),
    ('weather_data', 'date', '1=1')
]

for table, date_col, where_clause in date_checks:
    try:
        query = f"""
        SELECT 
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date,
            COUNT(*) as row_count,
            COUNT(DISTINCT {date_col}) as unique_days
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        WHERE {where_clause}
        """
        for row in client.query(query):
            print(f"\n{table}:")
            print(f"  Range: {row.min_date} to {row.max_date}")
            print(f"  Rows: {row.row_count}, Days: {row.unique_days}")
            
            # Check for gaps
            if row.unique_days and row.min_date and row.max_date:
                import datetime
                expected_days = (row.max_date - row.min_date).days + 1
                gap_pct = ((expected_days - row.unique_days) / expected_days * 100) if expected_days > 0 else 0
                if gap_pct > 10:
                    print(f"  ⚠️ DATA GAPS: {gap_pct:.1f}% missing days!")
    except Exception as e:
        print(f"\n{table}: Error - {str(e)[:50]}")

print("\n" + "=" * 80)
print("CRITICAL FINDINGS:")
print("=" * 80)
print("Look for:")
print("  • Tables with different date/time column names")
print("  • Symbol contamination (wrong symbols in tables)")
print("  • Views still referencing staging")
print("  • Duplicate objects with similar names")
print("  • Data gaps in date ranges")
print("=" * 80)
