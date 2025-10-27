#!/usr/bin/env python3
"""
Create Main Tables for CFTC and USDA Data with Full Audit
Ensures proper wiring and naming conventions
"""

from google.cloud import bigquery
client = bigquery.Client()

print('📋 PRE-CREATION AUDIT')
print('=' * 80)

# 1. Check what views depend on these staging tables
print('\n1. VIEWS DEPENDING ON STAGING TABLES:')
print('-' * 40)

views_to_check = [
    ('curated', 'vw_cftc_positions_oilseeds_weekly'),
    ('curated', 'vw_cftc_soybean_oil_weekly'),
    ('curated', 'vw_usda_export_sales_soy_weekly')
]

for dataset, view in views_to_check:
    try:
        query = f'''
        SELECT view_definition
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.VIEWS`
        WHERE table_name = '{view}'
        '''
        result = client.query(query).to_dataframe()
        if not result.empty:
            definition = result.iloc[0]['view_definition']
            if 'staging.cftc_cot' in definition:
                print(f'  {dataset}.{view} → references staging.cftc_cot')
            if 'staging.usda_export_sales' in definition:
                print(f'  {dataset}.{view} → references staging.usda_export_sales')
    except Exception as e:
        print(f'  Error checking {dataset}.{view}: {e}')

# 2. Get full schema of staging tables
print('\n2. STAGING TABLE SCHEMAS:')
print('-' * 40)

staging_tables = {
    'cftc_cot': None,
    'usda_export_sales': None
}

for table in staging_tables:
    query = f'''
    SELECT 
        column_name,
        data_type,
        is_nullable
    FROM `cbi-v14.staging.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table}'
    ORDER BY ordinal_position
    '''
    schema = client.query(query).to_dataframe()
    staging_tables[table] = schema
    print(f'\n{table} schema:')
    for _, row in schema.iterrows():
        nullable = 'NULLABLE' if row['is_nullable'] == 'YES' else 'REQUIRED'
        print(f'  {row["column_name"]}: {row["data_type"]} ({nullable})')

# 3. Create main tables with same schema
print('\n' + '=' * 80)
print('📊 CREATING MAIN TABLES')
print('=' * 80)

# Create CFTC COT main table
print('\n3. CREATING forecasting_data_warehouse.cftc_cot:')
try:
    create_cftc_sql = '''
    CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.cftc_cot`
    (
        report_date DATE,
        commodity STRING,
        contract_code STRING,
        managed_money_long FLOAT64,
        managed_money_short FLOAT64,
        managed_money_net FLOAT64,
        commercial_long FLOAT64,
        commercial_short FLOAT64,
        commercial_net FLOAT64,
        open_interest FLOAT64,
        source_name STRING,
        confidence_score FLOAT64,
        ingest_timestamp_utc TIMESTAMP,
        provenance_uuid STRING
    )
    PARTITION BY report_date
    CLUSTER BY commodity, contract_code
    '''
    
    job = client.query(create_cftc_sql)
    job.result()
    print('  ✅ Created cftc_cot table')
    
    # Migrate data from staging
    migrate_sql = '''
    INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
    SELECT 
        report_date,
        commodity,
        contract_code,
        managed_money_long,
        managed_money_short,
        managed_money_net,
        commercial_long,
        commercial_short,
        commercial_net,
        open_interest,
        source_name,
        confidence_score,
        ingest_timestamp_utc,
        provenance_uuid
    FROM `cbi-v14.staging.cftc_cot`
    WHERE NOT EXISTS (
        SELECT 1 
        FROM `cbi-v14.forecasting_data_warehouse.cftc_cot` main
        WHERE main.report_date = `cbi-v14.staging.cftc_cot`.report_date
        AND main.commodity = `cbi-v14.staging.cftc_cot`.commodity
    )
    '''
    
    job = client.query(migrate_sql)
    result = job.result()
    print(f'  ✅ Migrated {result.num_dml_affected_rows} rows from staging')
    
except Exception as e:
    print(f'  ❌ Error: {e}')

# Create USDA Export Sales main table
print('\n4. CREATING forecasting_data_warehouse.usda_export_sales:')
try:
    create_usda_sql = '''
    CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.usda_export_sales`
    (
        report_date DATE,
        commodity STRING,
        destination_country STRING,
        net_sales_mt FLOAT64,
        cumulative_exports_mt FLOAT64,
        outstanding_sales_mt FLOAT64,
        source_name STRING,
        confidence_score FLOAT64,
        ingest_timestamp_utc TIMESTAMP,
        provenance_uuid STRING
    )
    PARTITION BY report_date
    CLUSTER BY commodity, destination_country
    '''
    
    job = client.query(create_usda_sql)
    job.result()
    print('  ✅ Created usda_export_sales table')
    
    # Check if there's data to migrate
    check_sql = 'SELECT COUNT(*) as cnt FROM `cbi-v14.staging.usda_export_sales`'
    result = client.query(check_sql).to_dataframe()
    if result.iloc[0]['cnt'] > 0:
        migrate_sql = '''
        INSERT INTO `cbi-v14.forecasting_data_warehouse.usda_export_sales`
        SELECT * FROM `cbi-v14.staging.usda_export_sales`
        '''
        job = client.query(migrate_sql)
        result = job.result()
        print(f'  ✅ Migrated {result.num_dml_affected_rows} rows from staging')
    else:
        print('  ℹ️ No data to migrate (staging table is empty)')
    
except Exception as e:
    print(f'  ❌ Error: {e}')

# 5. Update views to reference main tables
print('\n' + '=' * 80)
print('🔧 UPDATING VIEWS TO REFERENCE MAIN TABLES')
print('=' * 80)

views_to_update = [
    ('curated', 'vw_cftc_positions_oilseeds_weekly'),
    ('curated', 'vw_cftc_soybean_oil_weekly'),
    ('curated', 'vw_usda_export_sales_soy_weekly')
]

for dataset, view_name in views_to_update:
    try:
        # Get current view definition
        query = f'''
        SELECT view_definition
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.VIEWS`
        WHERE table_name = '{view_name}'
        '''
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            view_definition = result.iloc[0]['view_definition']
            updated_definition = view_definition
            
            # Replace staging references with main table references
            if 'staging.cftc_cot' in view_definition:
                updated_definition = updated_definition.replace(
                    'staging.cftc_cot', 
                    'forecasting_data_warehouse.cftc_cot'
                )
                print(f'\n  Updating {dataset}.{view_name}')
                print(f'    staging.cftc_cot → forecasting_data_warehouse.cftc_cot')
                
            if 'staging.usda_export_sales' in view_definition:
                updated_definition = updated_definition.replace(
                    'staging.usda_export_sales', 
                    'forecasting_data_warehouse.usda_export_sales'
                )
                print(f'\n  Updating {dataset}.{view_name}')
                print(f'    staging.usda_export_sales → forecasting_data_warehouse.usda_export_sales')
            
            if updated_definition != view_definition:
                # Update the view
                update_sql = f'CREATE OR REPLACE VIEW `cbi-v14.{dataset}.{view_name}` AS {updated_definition}'
                job = client.query(update_sql)
                job.result()
                print(f'    ✅ View updated successfully')
            else:
                print(f'\n  ℹ️ {dataset}.{view_name} - No updates needed')
                
    except Exception as e:
        print(f'\n  ❌ Error updating {dataset}.{view_name}: {e}')

# 6. Final verification
print('\n' + '=' * 80)
print('✅ POST-CREATION VERIFICATION')
print('=' * 80)

# Verify main tables exist and have data
print('\nMain Table Status:')
for table in ['cftc_cot', 'usda_export_sales']:
    try:
        query = f'''
        SELECT COUNT(*) as row_count
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        '''
        result = client.query(query).to_dataframe()
        print(f'  forecasting_data_warehouse.{table}: {result.iloc[0]["row_count"]} rows')
    except Exception as e:
        print(f'  forecasting_data_warehouse.{table}: Error - {e}')

# Verify views work
print('\nView Status:')
for dataset, view in views_to_update:
    try:
        query = f'SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.{view}` LIMIT 1'
        result = client.query(query).to_dataframe()
        print(f'  ✅ {dataset}.{view}: Working')
    except Exception as e:
        print(f'  ❌ {dataset}.{view}: {str(e)[:50]}...')

print('\n' + '=' * 80)
print('COMPLETED: Main tables created and views updated')
print('=' * 80)
