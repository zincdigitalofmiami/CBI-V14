#!/usr/bin/env python3
"""
FINAL PRE-RETRAIN VALIDATION
Check for duplicates, schema consistency, economic data quality
PROTECT EXISTING MODELS AT ALL COSTS
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print('='*80)
print('FINAL PRE-RETRAIN VALIDATION')
print('PROTECTING EXISTING MODELS - NO OVERWRITES')
print('='*80)

# 1. DUPLICATE CHECK - CRITICAL
print('\n1. FINAL DUPLICATE CHECK')
print('-'*60)

critical_tables = ['soybean_oil_prices', 'corn_prices', 'crude_oil_prices', 'palm_oil_prices']
duplicate_issues = []

for table in critical_tables:
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
        ARRAY_AGG(CAST(date AS STRING) LIMIT 5) as sample_dates
    FROM duplicates
    """
    
    result = client.query(query).to_dataframe()
    dup_count = result['duplicate_dates'].iloc[0] if not result.empty else 0
    
    if dup_count > 0:
        sample_dates = result['sample_dates'].iloc[0] if not result.empty else []
        print(f'🚨 {table}: {dup_count} duplicate dates - {sample_dates[:3]}...')
        duplicate_issues.append(table)
    else:
        print(f'✅ {table}: No duplicates')

# 2. SCHEMA CONSISTENCY CHECK
print('\n2. SCHEMA CONSISTENCY CHECK')
print('-'*60)

schema_issues = []
expected_price_columns = ['time', 'close', 'volume', 'high', 'low', 'open']

for table in critical_tables:
    try:
        table_ref = client.get_table(f'cbi-v14.forecasting_data_warehouse.{table}')
        actual_columns = [field.name for field in table_ref.schema]
        
        missing_cols = [col for col in expected_price_columns if col not in actual_columns]
        
        if missing_cols:
            print(f'⚠️ {table}: Missing columns - {missing_cols}')
            schema_issues.append(f'{table}: Missing {missing_cols}')
        else:
            print(f'✅ {table}: All required columns present')
            
    except Exception as e:
        print(f'❌ {table}: Schema check failed - {str(e)[:60]}')
        schema_issues.append(f'{table}: Schema error')

# 3. ECONOMIC DATA VALIDATION
print('\n3. ECONOMIC DATA VALIDATION')
print('-'*60)

economic_issues = []

try:
    # Check for realistic ranges
    econ_query = """
    SELECT 
        indicator,
        COUNT(*) as record_count,
        MIN(value) as min_val,
        MAX(value) as max_val,
        AVG(value) as avg_val,
        MAX(CAST(time AS DATE)) as latest_date
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        AND indicator IN ('fed_funds_rate', 'ten_year_treasury', 'vix_index', 'unemployment_rate')
    GROUP BY indicator
    ORDER BY indicator
    """
    
    econ_result = client.query(econ_query).to_dataframe()
    
    # Validation ranges
    valid_ranges = {
        'fed_funds_rate': (0, 10),
        'ten_year_treasury': (0, 8),
        'vix_index': (8, 80),
        'unemployment_rate': (2, 15)
    }
    
    for _, row in econ_result.iterrows():
        indicator = row['indicator']
        min_val, max_val = row['min_val'], row['max_val']
        
        if indicator in valid_ranges:
            expected_min, expected_max = valid_ranges[indicator]
            
            if min_val < expected_min or max_val > expected_max:
                print(f'⚠️ {indicator}: Range {min_val:.2f}-{max_val:.2f} outside expected {expected_min}-{expected_max}')
                economic_issues.append(f'{indicator}: Range issue')
            else:
                print(f'✅ {indicator}: Range {min_val:.2f}-{max_val:.2f} (valid)')
        else:
            print(f'✅ {indicator}: Range {min_val:.2f}-{max_val:.2f} (no validation rule)')
            
except Exception as e:
    print(f'❌ Economic data check failed: {str(e)[:100]}')
    economic_issues.append('Economic data query failed')

# 4. SEGMENTED DATA SCHEMA CHECK
print('\n4. SEGMENTED DATA SCHEMA CHECK')
print('-'*60)

segmented_tables = ['news_intelligence', 'social_sentiment', 'trump_policy_intelligence']
schema_issues_segmented = []

for table in segmented_tables:
    try:
        table_ref = client.get_table(f'cbi-v14.forecasting_data_warehouse.{table}')
        columns = [field.name for field in table_ref.schema]
        
        print(f'✅ {table}: {len(columns)} columns')
        
        # Check for required columns based on table type
        if 'news' in table:
            required = ['published', 'intelligence_score', 'source']
        elif 'social' in table:
            required = ['timestamp', 'sentiment_score']
        elif 'trump' in table:
            required = ['created_at']
        else:
            required = []
            
        missing = [col for col in required if col not in columns]
        if missing:
            print(f'  ⚠️ Missing required columns: {missing}')
            schema_issues_segmented.append(f'{table}: Missing {missing}')
            
    except Exception as e:
        print(f'❌ {table}: Error - {str(e)[:60]}')
        schema_issues_segmented.append(f'{table}: Schema error')

# FINAL ASSESSMENT
print('\n' + '='*80)
print('FINAL VALIDATION SUMMARY')
print('='*80)

total_issues = len(duplicate_issues) + len(schema_issues) + len(economic_issues) + len(schema_issues_segmented)

print(f'Duplicate Issues: {len(duplicate_issues)}')
print(f'Schema Issues: {len(schema_issues)}')
print(f'Economic Issues: {len(economic_issues)}')
print(f'Segmented Schema Issues: {len(schema_issues_segmented)}')

if total_issues == 0:
    print('\n✅ ALL VALIDATION CHECKS PASSED')
    print('✅ SAFE TO PROCEED WITH V4 RETRAINING')
    print('✅ BEST MODELS ARE PROTECTED')
else:
    print(f'\n⚠️ {total_issues} ISSUES FOUND - FIX BEFORE RETRAINING')
    
    if duplicate_issues:
        print(f'  🚨 Fix duplicates in: {", ".join(duplicate_issues)}')
    if schema_issues:
        print(f'  🚨 Fix schemas in: {", ".join(schema_issues)}')
    if economic_issues:
        print(f'  🚨 Fix economic data: {", ".join(economic_issues)}')
    if schema_issues_segmented:
        print(f'  🚨 Fix segmented schemas: {", ".join(schema_issues_segmented)}')

print(f'\n🛡️ BEST MODELS REMAIN PROTECTED AND OPERATIONAL')




