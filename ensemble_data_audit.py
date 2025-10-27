#!/usr/bin/env python3
"""
COMPREHENSIVE DATA AUDIT FOR ENSEMBLE TRAINING
Check for duplicates, schema issues, data quality
NO RECREATING - JUST AUDITING!
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print('='*80)
print('COMPREHENSIVE DATA AUDIT FOR ENSEMBLE TRAINING')
print('='*80)

# Critical tables for ensemble
tables = ['soybean_oil_prices', 'corn_prices', 'crude_oil_prices', 'palm_oil_prices']

# 1. DUPLICATE CHECK
print('\n1. DUPLICATE CHECK')
print('-'*60)

duplicate_issues = []
for table in tables:
    query = f"""
    WITH duplicates AS (
        SELECT 
            CAST(time AS DATE) as date,
            COUNT(*) as count
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        GROUP BY date
        HAVING COUNT(*) > 1
    )
    SELECT 
        COUNT(*) as duplicate_dates,
        SUM(count) as total_duplicate_rows
    FROM duplicates
    """
    
    result = client.query(query).to_dataframe()
    dup_dates = result['duplicate_dates'].iloc[0] if not result.empty else 0
    dup_rows = result['total_duplicate_rows'].iloc[0] if not result.empty else 0
    
    if dup_dates > 0:
        print(f'⚠️ {table:20} {dup_dates} dates with duplicates ({dup_rows} total duplicate rows)')
        duplicate_issues.append(table)
    else:
        print(f'✅ {table:20} No duplicates')

# 2. SCHEMA CHECK
print('\n2. SCHEMA CONSISTENCY CHECK')
print('-'*60)

schema_info = {}
for table in tables:
    table_ref = client.get_table(f'cbi-v14.forecasting_data_warehouse.{table}')
    columns = [field.name for field in table_ref.schema]
    schema_info[table] = columns
    
    required_cols = ['time', 'close', 'volume', 'high', 'low']
    missing = [col for col in required_cols if col not in columns]
    
    if missing:
        print(f'⚠️ {table:20} Missing columns: {missing}')
    else:
        print(f'✅ {table:20} All required columns present ({len(columns)} total)')

# 3. DATA QUALITY CHECK
print('\n3. DATA QUALITY CHECK')
print('-'*60)

quality_issues = []
for table in tables:
    query = f"""
    SELECT 
        COUNT(*) as total_rows,
        SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
        SUM(CASE WHEN close = 0 THEN 1 ELSE 0 END) as zero_close,
        SUM(CASE WHEN close < 0 THEN 1 ELSE 0 END) as negative_close,
        MIN(close) as min_price,
        MAX(close) as max_price,
        AVG(close) as avg_price,
        STDDEV(close) as std_price
    FROM `cbi-v14.forecasting_data_warehouse.{table}`
    """
    
    result = client.query(query).to_dataframe()
    r = result.iloc[0]
    
    issues = []
    if r['null_close'] > 0:
        issues.append(f"{int(r['null_close'])} nulls")
    if r['zero_close'] > 0:
        issues.append(f"{int(r['zero_close'])} zeros")
    if r['negative_close'] > 0:
        issues.append(f"{int(r['negative_close'])} negatives")
    
    if issues:
        print(f'⚠️ {table:20} Issues: {", ".join(issues)}')
        quality_issues.append(table)
    else:
        print(f'✅ {table:20} Clean data | Range: ${r["min_price"]:.2f}-${r["max_price"]:.2f}')

# 4. DATE CONTINUITY
print('\n4. DATE CONTINUITY (Last 30 trading days)')
print('-'*60)

continuity_issues = []
for table in tables:
    query = f"""
    WITH trading_days AS (
        SELECT date
        FROM UNNEST(GENERATE_DATE_ARRAY(
            DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY),
            CURRENT_DATE()
        )) as date
        WHERE EXTRACT(DAYOFWEEK FROM date) NOT IN (1, 7)
    ),
    actual_days AS (
        SELECT DISTINCT CAST(time AS DATE) as date
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    )
    SELECT 
        COUNT(DISTINCT t.date) as expected_days,
        COUNT(DISTINCT a.date) as actual_days,
        COUNT(DISTINCT t.date) - COUNT(DISTINCT a.date) as missing_days,
        STRING_AGG(CAST(t.date AS STRING), ', ' LIMIT 5) as sample_missing
    FROM trading_days t
    LEFT JOIN actual_days a ON t.date = a.date
    WHERE a.date IS NULL
    """
    
    result = client.query(query).to_dataframe()
    r = result.iloc[0]
    
    if r['missing_days'] > 0:
        print(f'⚠️ {table:20} Missing {int(r["missing_days"])}/{int(r["expected_days"])} days')
        if pd.notna(r['sample_missing']):
            print(f'   Missing dates: {r["sample_missing"]}...')
        continuity_issues.append(table)
    else:
        print(f'✅ {table:20} Complete ({int(r["actual_days"])}/{int(r["expected_days"])} trading days)')

# 5. CROSS-TABLE ALIGNMENT
print('\n5. CROSS-TABLE DATE ALIGNMENT')
print('-'*60)

query = """
WITH all_dates AS (
    SELECT DISTINCT CAST(time AS DATE) as date 
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),
corn_dates AS (
    SELECT DISTINCT CAST(time AS DATE) as date 
    FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
    WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),
crude_dates AS (
    SELECT DISTINCT CAST(time AS DATE) as date 
    FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),
palm_dates AS (
    SELECT DISTINCT CAST(time AS DATE) as date 
    FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
)
SELECT 
    COUNT(DISTINCT a.date) as soy_days,
    COUNT(DISTINCT c.date) as corn_days,
    COUNT(DISTINCT cr.date) as crude_days,
    COUNT(DISTINCT p.date) as palm_days,
    COUNT(CASE WHEN c.date IS NOT NULL AND cr.date IS NOT NULL 
               AND p.date IS NOT NULL THEN 1 END) as aligned_days
FROM all_dates a
LEFT JOIN corn_dates c ON a.date = c.date
LEFT JOIN crude_dates cr ON a.date = cr.date
LEFT JOIN palm_dates p ON a.date = p.date
"""

result = client.query(query).to_dataframe()
r = result.iloc[0]

alignment_pct = (r['aligned_days'] / r['soy_days']) * 100 if r['soy_days'] > 0 else 0
print(f'Date alignment: {alignment_pct:.1f}% of days have all 4 commodities')
print(f'  Soy: {int(r["soy_days"])} days')
print(f'  Corn: {int(r["corn_days"])} days')
print(f'  Crude: {int(r["crude_days"])} days')
print(f'  Palm: {int(r["palm_days"])} days')
print(f'  Fully aligned: {int(r["aligned_days"])} days')

# 6. FINAL ASSESSMENT
print('\n' + '='*80)
print('ENSEMBLE TRAINING READINESS ASSESSMENT')
print('='*80)

total_issues = len(duplicate_issues) + len(quality_issues) + len(continuity_issues)

if total_issues == 0 and alignment_pct > 80:
    print('✅ DATA IS READY FOR ENSEMBLE TRAINING')
    print('   - No duplicates found')
    print('   - Schema is consistent')
    print('   - Data quality is good')
    print('   - Date continuity is maintained')
    print(f'   - Cross-table alignment is {alignment_pct:.1f}%')
else:
    print('⚠️ DATA NEEDS CLEANING BEFORE ENSEMBLE TRAINING')
    if duplicate_issues:
        print(f'   - Fix duplicates in: {", ".join(duplicate_issues)}')
    if quality_issues:
        print(f'   - Fix data quality in: {", ".join(quality_issues)}')
    if continuity_issues:
        print(f'   - Fix missing dates in: {", ".join(continuity_issues)}')
    if alignment_pct < 80:
        print(f'   - Improve cross-table alignment (currently {alignment_pct:.1f}%)')

# 7. CHECK TRAINING DATASET
print('\n7. TRAINING DATASET CHECK')
print('-'*60)

try:
    query = """
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(PARSE_DATE('%Y-%m-%d', date)) as earliest,
        MAX(PARSE_DATE('%Y-%m-%d', date)) as latest
    FROM `cbi-v14.models.training_dataset`
    WHERE target_1w IS NOT NULL
    """
    
    result = client.query(query).to_dataframe()
    r = result.iloc[0]
    print(f'Training dataset: {int(r["rows"])} rows, {int(r["unique_dates"])} unique dates')
    print(f'Date range: {r["earliest"]} to {r["latest"]}')
except Exception as e:
    print(f'❌ Error checking training dataset: {str(e)[:100]}')

print('\n' + '='*80)
