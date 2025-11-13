#!/usr/bin/env python3
"""
Check specific historical data sources found
"""
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

# Key historical sources to check
HISTORICAL_SOURCES = [
    ('models_v4', 'currency_complete', 'date'),  # 24.2 years found
    ('models_v4', 'economic_indicators_daily_complete', 'date'),
    ('models_v4', 'yahoo_finance_weekend_complete', 'date'),
    ('models_v4', 'usd_cny_daily_complete', 'date'),
    ('models_v4', 'treasury_10y_yahoo_complete', 'date'),
    ('models_v4', 'palm_price_daily_complete', 'date'),
    ('models', 'FINAL_TRAINING_DATASET_COMPLETE', 'date'),
    ('models', 'training_data_complete_all_intelligence', 'date'),
    ('bkp', 'soybean_oil_prices_backup_20251021_152417', 'time'),
    ('bkp', 'soybean_oil_prices_backup_20251021_152537', 'time'),
]

print("="*80)
print("🔍 CHECKING HISTORICAL DATA SOURCES")
print("="*80)

for dataset, table, date_col in HISTORICAL_SOURCES:
    table_path = f"{PROJECT_ID}.{dataset}.{table}"
    
    try:
        # Check if table exists and get stats
        if date_col == 'time':
            date_expr = f"DATE({date_col})"
        else:
            date_expr = date_col
        
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MIN({date_expr}) as earliest,
            MAX({date_expr}) as latest,
            DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as days,
            COUNT(DISTINCT {date_expr}) as unique_dates
        FROM `{table_path}`
        WHERE {date_col} IS NOT NULL
        """
        result = client.query(query).to_dataframe()
        
        if not result.empty and result.iloc[0]['earliest']:
            row = result.iloc[0]
            rows = int(row['row_count'])
            earliest = row['earliest']
            latest = row['latest']
            days = int(row['days']) if row['days'] else 0
            years = days / 365.25
            unique_dates = int(row['unique_dates'])
            
            print(f"\n✅ {dataset}.{table}")
            print(f"   Rows: {rows:,}")
            print(f"   Date Range: {earliest} to {latest}")
            print(f"   Span: {years:.1f} years ({days:,} days)")
            print(f"   Unique Dates: {unique_dates:,}")
            
            # Check for pre-2020 data
            pre2020_query = f"""
            SELECT COUNT(*) as pre2020_count
            FROM `{table_path}`
            WHERE {date_col} < '2020-01-01'
            """
            pre2020_result = client.query(pre2020_query).to_dataframe()
            pre2020_count = int(pre2020_result.iloc[0]['pre2020_count']) if not pre2020_result.empty else 0
            
            if pre2020_count > 0:
                print(f"   🎯 PRE-2020 DATA: {pre2020_count:,} rows")
            else:
                print(f"   ⚠️  No pre-2020 data")
    except Exception as e:
        print(f"\n❌ {dataset}.{table}: Error - {e}")

# Check backup tables for historical soybean oil prices
print("\n" + "="*80)
print("🔍 CHECKING BACKUP TABLES FOR HISTORICAL SOYBEAN OIL DATA")
print("="*80)

backup_tables = [
    ('bkp', 'soybean_oil_prices_backup_20251021_152417'),
    ('bkp', 'soybean_oil_prices_backup_20251021_152537'),
    ('bkp', 'soybean_oil_prices_20251010T231754Z'),
]

for dataset, table in backup_tables:
    table_path = f"{PROJECT_ID}.{dataset}.{table}"
    try:
        # Try different date column names
        for date_col in ['time', 'date', 'timestamp']:
            try:
                if date_col == 'time':
                    date_expr = f"DATE({date_col})"
                else:
                    date_expr = date_col
                
                query = f"""
                SELECT 
                    COUNT(*) as row_count,
                    MIN({date_expr}) as earliest,
                    MAX({date_expr}) as latest,
                    DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as days
                FROM `{table_path}`
                WHERE {date_col} IS NOT NULL
                """
                result = client.query(query).to_dataframe()
                
                if not result.empty and result.iloc[0]['earliest']:
                    row = result.iloc[0]
                    rows = int(row['row_count'])
                    earliest = row['earliest']
                    latest = row['latest']
                    days = int(row['days']) if row['days'] else 0
                    years = days / 365.25
                    
                    print(f"\n✅ {dataset}.{table} (using {date_col})")
                    print(f"   Rows: {rows:,}")
                    print(f"   Date Range: {earliest} to {latest}")
                    print(f"   Span: {years:.1f} years")
                    break
            except:
                continue
    except Exception as e:
        print(f"\n❌ {dataset}.{table}: Error - {e}")

print("\n" + "="*80)

