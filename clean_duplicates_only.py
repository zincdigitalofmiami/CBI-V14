#!/usr/bin/env python3
"""
CLEAN DUPLICATES ONLY - NO RECREATING TABLES
Just remove duplicate rows, keep the latest one for each date
"""

from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print('='*80)
print('REMOVING DUPLICATES FROM TABLES')
print('='*80)

# Tables with duplicates
tables_to_clean = [
    ('soybean_oil_prices', 4),
    ('corn_prices', 4),
    ('palm_oil_prices', 27)
]

for table, dup_count in tables_to_clean:
    print(f'\nCleaning {table} ({dup_count} duplicate dates)...')
    
    # First, identify the duplicates
    check_query = f"""
    SELECT 
        CAST(time AS DATE) as date,
        COUNT(*) as count,
        STRING_AGG(CAST(time AS STRING), ', ' LIMIT 5) as sample_times
    FROM `cbi-v14.forecasting_data_warehouse.{table}`
    GROUP BY date
    HAVING COUNT(*) > 1
    ORDER BY date DESC
    LIMIT 10
    """
    
    duplicates = client.query(check_query).to_dataframe()
    
    if not duplicates.empty:
        print(f'  Found duplicates on dates: {duplicates["date"].tolist()[:5]}...')
        
        # Create a deduplicated version using ROW_NUMBER
        dedup_query = f"""
        CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.{table}_temp` AS
        WITH ranked_data AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY CAST(time AS DATE) 
                    ORDER BY time DESC, ingest_timestamp_utc DESC
                ) as rn
            FROM `cbi-v14.forecasting_data_warehouse.{table}`
        )
        SELECT * EXCEPT(rn)
        FROM ranked_data
        WHERE rn = 1
        """
        
        try:
            # Create temp table with deduplicated data
            job = client.query(dedup_query)
            job.result()
            
            # Count rows in both tables
            orig_count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.{table}`"
            temp_count_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.{table}_temp`"
            
            orig_count = client.query(orig_count_query).to_dataframe()['cnt'].iloc[0]
            temp_count = client.query(temp_count_query).to_dataframe()['cnt'].iloc[0]
            
            print(f'  Original rows: {orig_count:,}')
            print(f'  After dedup: {temp_count:,}')
            print(f'  Removed: {orig_count - temp_count:,} duplicate rows')
            
            # Replace original with deduplicated
            replace_query = f"""
            CREATE OR REPLACE TABLE `cbi-v14.forecasting_data_warehouse.{table}` AS
            SELECT * FROM `cbi-v14.forecasting_data_warehouse.{table}_temp`
            """
            
            job = client.query(replace_query)
            job.result()
            
            # Drop temp table
            client.delete_table(f'cbi-v14.forecasting_data_warehouse.{table}_temp')
            
            print(f'  ✅ Successfully cleaned {table}')
            
        except Exception as e:
            print(f'  ❌ Error cleaning {table}: {str(e)[:100]}')
    else:
        print(f'  No duplicates found (may have been cleaned already)')

# Verify the cleaning
print('\n' + '='*80)
print('VERIFICATION')
print('='*80)

for table, _ in tables_to_clean:
    verify_query = f"""
    WITH duplicates AS (
        SELECT 
            CAST(time AS DATE) as date,
            COUNT(*) as count
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        GROUP BY date
        HAVING COUNT(*) > 1
    )
    SELECT COUNT(*) as duplicate_dates
    FROM duplicates
    """
    
    result = client.query(verify_query).to_dataframe()
    dup_dates = result['duplicate_dates'].iloc[0]
    
    if dup_dates == 0:
        print(f'✅ {table}: No duplicates remaining')
    else:
        print(f'⚠️ {table}: Still has {dup_dates} duplicate dates')

print('\n✅ Duplicate cleaning complete!')
