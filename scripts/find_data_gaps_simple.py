#!/usr/bin/env python3
"""
Find data gaps and thin datasets - simplified version
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("DATA GAPS ANALYSIS - SIMPLIFIED")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Tables to check
tables_to_check = [
    # Core prices
    ('forecasting_data_warehouse', 'soybean_oil_prices', 'time'),
    ('forecasting_data_warehouse', 'palm_oil_prices', 'time'),
    ('forecasting_data_warehouse', 'canola_oil_prices', 'date'),
    ('forecasting_data_warehouse', 'corn_prices', 'time'),
    ('forecasting_data_warehouse', 'soybean_prices', 'time'),
    ('forecasting_data_warehouse', 'soybean_meal_prices', 'time'),
    ('forecasting_data_warehouse', 'wheat_prices', 'time'),
    
    # Energy
    ('forecasting_data_warehouse', 'crude_oil_prices', 'date'),
    ('forecasting_data_warehouse', 'natural_gas_prices', 'date'),
    ('forecasting_data_warehouse', 'biofuel_prices', 'date'),
    
    # Market indicators
    ('forecasting_data_warehouse', 'vix_daily', 'date'),
    ('forecasting_data_warehouse', 'sp500_prices', 'time'),
    ('forecasting_data_warehouse', 'usd_index_prices', 'date'),
    ('forecasting_data_warehouse', 'treasury_prices', 'time'),
    
    # CFTC
    ('forecasting_data_warehouse', 'cftc_cot', 'report_date'),
    
    # Economic
    ('forecasting_data_warehouse', 'economic_indicators', 'time'),
    
    # China/Trade
    ('forecasting_data_warehouse', 'china_soybean_imports', 'date'),
    
    # News/Sentiment
    ('forecasting_data_warehouse', 'news_intelligence', 'processed_timestamp'),
    ('forecasting_data_warehouse', 'news_advanced', 'published_date'),
    ('forecasting_data_warehouse', 'social_sentiment', 'timestamp'),
    ('forecasting_data_warehouse', 'trump_policy_intelligence', 'created_at'),
    
    # Weather
    ('forecasting_data_warehouse', 'weather_data', 'date'),
    
    # Baltic/Shipping
    ('forecasting_data_warehouse', 'baltic_dry_index', 'date'),
    
    # Production training tables
    ('models_v4', 'production_training_data_1m', 'date'),
    ('models_v4', 'trump_rich_2023_2025', 'date'),
]

results = []

print("\nChecking tables...")
print("-"*80)

for dataset, table, date_col in tables_to_check:
    try:
        query = f"""
        SELECT 
            '{table}' as table_name,
            COUNT(*) as row_count,
            MIN(DATE({date_col})) as min_date,
            MAX(DATE({date_col})) as max_date
        FROM `cbi-v14.{dataset}.{table}`
        """
        
        result = client.query(query).result()
        for row in result:
            status = "✅" if row.row_count > 100 else "⚠️"
            print(f"{status} {table:35} | Rows: {row.row_count:8,} | {row.min_date} to {row.max_date}")
            
            results.append({
                'table': table,
                'rows': row.row_count,
                'min_date': row.min_date,
                'max_date': row.max_date,
                'status': 'OK' if row.row_count > 100 else 'THIN'
            })
            
    except Exception as e:
        error_msg = str(e)
        if "Not found: Table" in error_msg:
            print(f"❌ {table:35} | MISSING - Table does not exist")
            results.append({
                'table': table,
                'status': 'MISSING'
            })
        else:
            print(f"❌ {table:35} | ERROR - {error_msg[:50]}")
            results.append({
                'table': table,
                'status': 'ERROR',
                'error': error_msg[:100]
            })

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

missing = [r for r in results if r.get('status') == 'MISSING']
thin = [r for r in results if r.get('status') == 'THIN']
ok = [r for r in results if r.get('status') == 'OK']

print(f"\n✅ OK Tables: {len(ok)}")
print(f"⚠️ Thin Tables (< 100 rows): {len(thin)}")
print(f"❌ Missing Tables: {len(missing)}")

if missing:
    print("\n❌ MISSING TABLES:")
    for m in missing:
        print(f"  - {m['table']}")

if thin:
    print("\n⚠️ THIN TABLES:")
    for t in thin:
        print(f"  - {t['table']}: {t.get('rows', 0)} rows")

print("\n" + "="*80)
print("DONE")
print("="*80)
