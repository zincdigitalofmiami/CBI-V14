#!/usr/bin/env python3
"""
Data Quality Audit Script
Checks for contamination, duplicates, and anomalies
SAFETY FIRST - Read-only operations
"""

from google.cloud import bigquery
import sys

client = bigquery.Client(project='cbi-v14')

def check_data_quality():
    """Comprehensive data quality audit"""
    
    print('=' * 80)
    print('DATA QUALITY AUDIT - PROTECTING OUR APPLICATION')
    print('=' * 80)
    
    issues_found = []
    
    # 1. Check soybean oil prices for symbol contamination
    query = """
    SELECT 
        symbol,
        COUNT(*) as row_count,
        MIN(DATE(time)) as earliest_date,
        MAX(DATE(time)) as latest_date
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    GROUP BY symbol
    ORDER BY row_count DESC
    """
    
    print('\n1. SOYBEAN OIL PRICES - Symbol Contamination Check:')
    try:
        result = client.query(query).result()
        for row in result:
            if row.symbol == 'ZL':
                print(f'   ✅ Symbol: {row.symbol} - {row.row_count} rows ({row.earliest_date} to {row.latest_date})')
            else:
                print(f'   ❌ CONTAMINATION: Symbol: {row.symbol} - {row.row_count} rows')
                issues_found.append(f'Symbol contamination: {row.symbol}')
    except Exception as e:
        print(f'   Error: {e}')
        issues_found.append(f'Query error: {str(e)[:100]}')
    
    # 2. Check for duplicate dates
    query = """
    SELECT 
        DATE(time) as date,
        COUNT(*) as duplicate_count
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    GROUP BY DATE(time)
    HAVING COUNT(*) > 1
    ORDER BY duplicate_count DESC
    LIMIT 10
    """
    
    print('\n2. DUPLICATE DATES Check:')
    try:
        result = client.query(query).result()
        duplicates = list(result)
        if duplicates:
            print('   ❌ DUPLICATES FOUND:')
            for row in duplicates:
                print(f'      {row.date}: {row.duplicate_count} entries')
                issues_found.append(f'Duplicate date: {row.date}')
        else:
            print('   ✅ No duplicate dates found')
    except Exception as e:
        print(f'   Error: {e}')
        issues_found.append(f'Duplicate check error: {str(e)[:100]}')
    
    # 3. Check for price anomalies
    query = """
    WITH price_changes AS (
        SELECT 
            DATE(time) as date,
            close_price,
            LAG(close_price) OVER (ORDER BY time) as prev_price,
            ABS((close_price - LAG(close_price) OVER (ORDER BY time)) / 
                NULLIF(LAG(close_price) OVER (ORDER BY time), 0)) as pct_change
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    )
    SELECT 
        date,
        close_price,
        prev_price,
        ROUND(pct_change * 100, 2) as pct_change
    FROM price_changes
    WHERE pct_change > 0.15
    ORDER BY pct_change DESC
    LIMIT 10
    """
    
    print('\n3. PRICE ANOMALIES Check (>15% daily moves):')
    try:
        result = client.query(query).result()
        anomalies = list(result)
        if anomalies:
            print('   ⚠️ LARGE PRICE MOVES DETECTED (may be legitimate):')
            for row in anomalies:
                print(f'      {row.date}: ${row.prev_price:.2f} → ${row.close_price:.2f} ({row.pct_change}%)')
                if row.pct_change > 25:
                    issues_found.append(f'Extreme price move: {row.date} ({row.pct_change}%)')
        else:
            print('   ✅ No extreme price anomalies found')
    except Exception as e:
        print(f'   Error: {e}')
    
    # 4. Check other critical tables
    tables_to_check = [
        'crude_oil_prices',
        'palm_oil_prices',
        'social_sentiment',
        'weather_data'
    ]
    
    print('\n4. OTHER TABLES - Row Count & Freshness:')
    for table in tables_to_check:
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MAX(DATE(COALESCE(time, date, timestamp))) as latest_date,
            DATE_DIFF(CURRENT_DATE(), MAX(DATE(COALESCE(time, date, timestamp))), DAY) as days_stale
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        try:
            result = list(client.query(query).result())[0]
            status = '✅' if result.days_stale <= 2 else '⚠️'
            print(f'   {status} {table}: {result.row_count} rows, latest: {result.latest_date} ({result.days_stale} days old)')
            if result.days_stale > 7:
                issues_found.append(f'{table} is stale: {result.days_stale} days')
        except Exception as e:
            print(f'   ❌ {table}: Error - {str(e)[:50]}')
    
    # 5. Check training view column issues
    print('\n5. TRAINING VIEW COLUMN CHECK:')
    query = """
    SELECT column_name, data_type
    FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'vw_neural_training_dataset_v2_FIXED'
    AND column_name IN ('zl_price', 'zl_price_current', 'corr_zl_crude_7d')
    """
    try:
        result = client.query(query).result()
        columns_found = {row.column_name: row.data_type for row in result}
        
        if 'zl_price' in columns_found:
            print('   ✅ zl_price column exists')
        else:
            print('   ❌ zl_price column NOT found (likely zl_price_current instead)')
            issues_found.append('Column name mismatch: zl_price missing')
        
        if 'corr_zl_crude_7d' in columns_found:
            print(f'   ✅ corr_zl_crude_7d exists ({columns_found["corr_zl_crude_7d"]})')
        else:
            print('   ❌ corr_zl_crude_7d NOT found')
            issues_found.append('Missing correlation column')
    except Exception as e:
        print(f'   Error: {e}')
    
    # Summary
    print('\n' + '=' * 80)
    print('AUDIT SUMMARY:')
    print('=' * 80)
    
    if issues_found:
        print(f'❌ {len(issues_found)} ISSUES FOUND:')
        for i, issue in enumerate(issues_found, 1):
            print(f'   {i}. {issue}')
        return False
    else:
        print('✅ ALL CHECKS PASSED - Data appears clean')
        return True

if __name__ == "__main__":
    success = check_data_quality()
    sys.exit(0 if success else 1)
