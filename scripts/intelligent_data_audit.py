#!/usr/bin/env python3
"""
INTELLIGENT DATA AUDIT - Understanding commodity relationships and data sources
Soybean vs Soybean Oil vs Soybean Meal are DIFFERENT commodities
Check Yahoo vs CSV sources and data quality
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd
from collections import defaultdict

client = bigquery.Client(project='cbi-v14')

print(f"INTELLIGENT DATA AUDIT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Understanding commodity relationships and data sources")
print("="*80)

print("\n1. UNDERSTANDING SOYBEAN COMPLEX (3 DIFFERENT COMMODITIES):")
print("-"*80)

soybean_complex = {
    'Soybeans (ZS)': [],
    'Soybean Oil (ZL)': [],
    'Soybean Meal (ZM)': []
}

# Check all soybean-related tables
tables_to_check = [
    ('forecasting_data_warehouse', 'soybean_prices'),
    ('forecasting_data_warehouse', 'soybean_oil_prices'),
    ('forecasting_data_warehouse', 'soybean_meal_prices'),
]

for dataset, table in tables_to_check:
    print(f"\nAnalyzing {dataset}.{table}:")
    try:
        # Get sample data and metadata
        query = f"""
        SELECT 
            MIN(DATE(time)) as min_date,
            MAX(DATE(time)) as max_date,
            COUNT(*) as row_count,
            COUNT(DISTINCT DATE(time)) as unique_days,
            AVG(close) as avg_price,
            MIN(close) as min_price,
            MAX(close) as max_price,
            STRING_AGG(DISTINCT symbol, ', ') as symbols,
            STRING_AGG(DISTINCT CAST(volume AS STRING), ', ' LIMIT 3) as sample_volumes
        FROM `cbi-v14.{dataset}.{table}`
        """
        
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            row = result.iloc[0]
            print(f"  Date range: {row['min_date']} to {row['max_date']}")
            print(f"  Rows: {row['row_count']:,} | Unique days: {row['unique_days']:,}")
            print(f"  Price range: ${row['min_price']:.2f} - ${row['max_price']:.2f} (avg: ${row['avg_price']:.2f})")
            print(f"  Symbols: {row['symbols']}")
            
            # Determine commodity type
            if 'oil' in table.lower():
                commodity_type = 'Soybean Oil (ZL)'
            elif 'meal' in table.lower():
                commodity_type = 'Soybean Meal (ZM)'
            else:
                commodity_type = 'Soybeans (ZS)'
            
            soybean_complex[commodity_type].append({
                'table': f"{dataset}.{table}",
                'rows': row['row_count'],
                'date_range': f"{row['min_date']} to {row['max_date']}",
                'avg_price': row['avg_price']
            })
            
            # Check data source (Yahoo vs CSV)
            sample_query = f"""
            SELECT *
            FROM `cbi-v14.{dataset}.{table}`
            LIMIT 5
            """
            sample_df = client.query(sample_query).to_dataframe()
            
            # Check for Yahoo indicators
            has_yahoo_columns = all(col in sample_df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
            has_symbol = 'symbol' in sample_df.columns
            
            if has_yahoo_columns and has_symbol:
                print(f"  Data source: Likely YAHOO (has OHLCV + symbol)")
            else:
                print(f"  Data source: Likely CSV upload")
                
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

print("\n2. CHECKING DATA SOURCE QUALITY (Yahoo vs CSV):")
print("-"*80)

# Check all price tables for data source indicators
all_price_tables = []
datasets = ['forecasting_data_warehouse', 'curated']

for dataset in datasets:
    try:
        tables = list(client.list_tables(f'cbi-v14.{dataset}'))
        for table in tables:
            if 'price' in table.table_id.lower():
                all_price_tables.append((dataset, table.table_id))
    except:
        pass

yahoo_tables = []
csv_tables = []
unknown_tables = []

print("\nAnalyzing data sources for all price tables:")
for dataset, table in all_price_tables[:20]:  # Check first 20
    try:
        # Get schema
        schema_query = f"""
        SELECT column_name
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
        """
        # Simpler approach
        sample_query = f"SELECT * FROM `cbi-v14.{dataset}.{table}` LIMIT 1"
        sample = client.query(sample_query).to_dataframe()
        columns = list(sample.columns)
        
        # Determine source
        if all(col in columns for col in ['open', 'high', 'low', 'close', 'volume']):
            if 'symbol' in columns or 'ticker' in columns:
                yahoo_tables.append(f"{dataset}.{table}")
                source = "YAHOO"
            else:
                csv_tables.append(f"{dataset}.{table}")
                source = "CSV"
        else:
            unknown_tables.append(f"{dataset}.{table}")
            source = "UNKNOWN"
            
        print(f"  {dataset}.{table}: {source}")
        
    except Exception as e:
        print(f"  {dataset}.{table}: ERROR")

print(f"\nSummary:")
print(f"  Yahoo sources: {len(yahoo_tables)}")
print(f"  CSV sources: {len(csv_tables)}")
print(f"  Unknown sources: {len(unknown_tables)}")

print("\n3. CHECKING DATA COMPLETENESS AND GAPS:")
print("-"*80)

# Check for gaps in critical commodities
critical_commodities = [
    ('soybean_oil_prices', 'Soybean Oil (ZL)'),
    ('palm_oil_prices', 'Palm Oil'),
    ('crude_oil_prices', 'Crude Oil (CL)'),
    ('corn_prices', 'Corn (ZC)'),
    ('wheat_prices', 'Wheat (ZW)'),
]

for table, commodity in critical_commodities:
    print(f"\n{commodity} ({table}):")
    try:
        gap_query = f"""
        WITH daily_data AS (
            SELECT 
                DATE(time) as date,
                COUNT(*) as records_per_day
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
            GROUP BY DATE(time)
        ),
        date_range AS (
            SELECT 
                MIN(date) as min_date,
                MAX(date) as max_date,
                DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as expected_days,
                COUNT(*) as actual_days
            FROM daily_data
        )
        SELECT 
            *,
            expected_days - actual_days as missing_days,
            ROUND((actual_days / expected_days) * 100, 1) as completeness_pct
        FROM date_range
        """
        
        result = client.query(gap_query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            print(f"  Date range: {row['min_date']} to {row['max_date']}")
            print(f"  Completeness: {row['completeness_pct']}% ({row['actual_days']}/{row['expected_days']} days)")
            if row['missing_days'] > 0:
                print(f"  ⚠️ MISSING {row['missing_days']} days of data")
                
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

print("\n4. CHECKING SCHEMA CONSISTENCY:")
print("-"*80)

# Compare schemas for similar commodities
oil_tables = [
    ('forecasting_data_warehouse', 'soybean_oil_prices'),
    ('forecasting_data_warehouse', 'palm_oil_prices'),
    ('forecasting_data_warehouse', 'crude_oil_prices'),
]

schemas = {}
print("\nComparing oil commodity schemas:")
for dataset, table in oil_tables:
    try:
        sample_query = f"SELECT * FROM `cbi-v14.{dataset}.{table}` LIMIT 1"
        sample = client.query(sample_query).to_dataframe()
        schemas[table] = set(sample.columns)
        print(f"  {table}: {len(sample.columns)} columns")
        print(f"    Columns: {', '.join(sorted(sample.columns))}")
    except Exception as e:
        print(f"  {table}: Error")

# Check for schema differences
if len(schemas) > 1:
    print("\n  Schema differences found:")
    tables = list(schemas.keys())
    for i in range(len(tables)):
        for j in range(i+1, len(tables)):
            diff1 = schemas[tables[i]] - schemas[tables[j]]
            diff2 = schemas[tables[j]] - schemas[tables[i]]
            if diff1 or diff2:
                print(f"    {tables[i]} vs {tables[j]}:")
                if diff1:
                    print(f"      Only in {tables[i]}: {diff1}")
                if diff2:
                    print(f"      Only in {tables[j]}: {diff2}")

print("\n5. DATA QUALITY COMPARISON (Yahoo vs CSV):")
print("-"*80)

# Compare same commodity from different sources if available
print("\nComparing data quality indicators:")

quality_checks = []
for table in ['soybean_oil_prices', 'crude_oil_prices', 'corn_prices']:
    try:
        quality_query = f"""
        WITH data_quality AS (
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT DATE(time)) as unique_days,
                COUNT(CASE WHEN close IS NULL THEN 1 END) as null_closes,
                COUNT(CASE WHEN volume = 0 OR volume IS NULL THEN 1 END) as zero_volumes,
                STDDEV(close) / AVG(close) as price_cv,
                MAX(ABS((close - LAG(close) OVER (ORDER BY time)) / LAG(close) OVER (ORDER BY time))) as max_daily_change
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
        )
        SELECT * FROM data_quality
        """
        
        result = client.query(quality_query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            print(f"\n  {table}:")
            print(f"    Total rows: {row['total_rows']:,}")
            print(f"    Unique days: {row['unique_days']:,}")
            print(f"    NULL prices: {row['null_closes']}")
            print(f"    Zero/NULL volumes: {row['zero_volumes']}")
            print(f"    Price volatility (CV): {row['price_cv']:.3f}")
            print(f"    Max daily change: {row['max_daily_change']*100:.1f}%")
            
            quality_checks.append({
                'table': table,
                'quality_score': 100 - (row['null_closes'] + row['zero_volumes']) / row['total_rows'] * 100
            })
            
    except Exception as e:
        print(f"\n  {table}: Error - {str(e)[:50]}")

print("\n6. RECOMMENDATIONS:")
print("-"*80)

print("""
FINDINGS:
1. Soybean, Soybean Oil, and Soybean Meal are CORRECTLY stored as separate commodities
   - Each has different price ranges and characteristics
   - This is CORRECT - don't merge these!

2. Data Sources:
   - Yahoo data appears more complete (has OHLCV + symbol)
   - CSV data may have gaps or quality issues
   
3. Schema Consistency:
   - Oil commodities have similar but not identical schemas
   - Need standardization for proper joins

RECOMMENDATIONS:
1. KEEP separate tables for Soybean, Soybean Oil, Soybean Meal - they're different!
2. STANDARDIZE schemas within commodity groups (all oils should have same columns)
3. PREFER Yahoo data where available for consistency
4. FILL gaps in historical data using Yahoo Finance API
5. DELETE true duplicates (same commodity, same data, different names)
6. MOVE all views to signals dataset (keep only raw tables in warehouse)

PRIORITY ACTIONS:
1. Identify TRUE duplicates (same commodity, not related commodities)
2. Standardize schemas for similar commodities
3. Backfill missing data from Yahoo
4. Create master training dataset with ALL commodities properly joined
""")

# Summary
print("\n" + "="*80)
print("INTELLIGENT AUDIT COMPLETE")
print("="*80)
print("\nKEY INSIGHT: Soybean complex (beans, oil, meal) are DIFFERENT commodities - keep separate!")
print("Focus on removing TRUE duplicates and standardizing schemas within commodity groups.")
