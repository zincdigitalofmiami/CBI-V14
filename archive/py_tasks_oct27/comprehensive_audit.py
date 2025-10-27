#!/usr/bin/env python3
"""
COMPREHENSIVE AUDIT OF ALL DATA ASSETS
Complete inventory before making any changes
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import json

print("="*80)
print("COMPREHENSIVE DATA AUDIT")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

audit_report = {
    'timestamp': datetime.now().isoformat(),
    'datasets': {},
    'training_tables': {},
    'data_warehouse': {},
    'views': {},
    'relationships': {},
    'issues': []
}

# 1. AUDIT ALL DATASETS AND TABLES
print("\n1. AUDITING ALL DATASETS AND TABLES")
print("-"*40)

datasets = list(client.list_datasets())
print(f"Total datasets: {len(datasets)}")

for dataset in datasets:
    dataset_id = dataset.dataset_id
    tables = list(client.list_tables(dataset.reference))
    
    audit_report['datasets'][dataset_id] = {
        'table_count': len(tables),
        'tables': []
    }
    
    print(f"\n{dataset_id}: {len(tables)} tables")
    
    for table in tables:
        table_ref = dataset.table(table.table_id)
        try:
            table_obj = client.get_table(table_ref)
            
            # Get basic info
            table_info = {
                'name': table.table_id,
                'type': table_obj.table_type,
                'rows': table_obj.num_rows if table_obj.table_type == 'TABLE' else None,
                'size_mb': table_obj.num_bytes / (1024*1024) if table_obj.num_bytes else 0,
                'created': table_obj.created.isoformat() if table_obj.created else None,
                'modified': table_obj.modified.isoformat() if table_obj.modified else None,
                'schema_fields': len(table_obj.schema) if table_obj.schema else 0
            }
            
            audit_report['datasets'][dataset_id]['tables'].append(table_info)
            
            # Print summary
            if table_obj.table_type == 'TABLE':
                print(f"  • {table.table_id}: {table_obj.num_rows:,} rows, {table_info['size_mb']:.1f} MB")
            else:
                print(f"  • {table.table_id}: VIEW")
                
        except Exception as e:
            print(f"  • {table.table_id}: Error - {str(e)[:50]}")

# 2. AUDIT TRAINING DATASETS SPECIFICALLY
print("\n2. AUDITING TRAINING DATASETS")
print("-"*40)

training_tables = [
    'models.training_dataset',
    'models.training_dataset_enhanced',
    'models.training_complete_enhanced',
    'models.training_dataset_master',
    'models.training_dataset_master_v2',
    'models_v4.training_dataset_v4',
    'models_v4.training_dataset_super_enriched'
]

for table_path in training_tables:
    try:
        dataset_id, table_id = table_path.split('.')
        
        # Check if exists
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(*) as total_columns
        FROM `cbi-v14.{table_path}`
        LIMIT 1
        """
        
        result = client.query(query).to_dataframe()
        
        # Get schema
        table_ref = client.dataset(dataset_id).table(table_id)
        table_obj = client.get_table(table_ref)
        
        # Get date range
        date_query = f"""
        SELECT 
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `cbi-v14.{table_path}`
        WHERE date IS NOT NULL
        """
        
        try:
            date_result = client.query(date_query).to_dataframe()
            min_date = date_result['min_date'].iloc[0]
            max_date = date_result['max_date'].iloc[0]
        except:
            min_date = max_date = "No date column"
        
        audit_report['training_tables'][table_path] = {
            'exists': True,
            'rows': table_obj.num_rows,
            'columns': len(table_obj.schema),
            'size_mb': table_obj.num_bytes / (1024*1024) if table_obj.num_bytes else 0,
            'date_range': f"{min_date} to {max_date}",
            'modified': table_obj.modified.isoformat() if table_obj.modified else None
        }
        
        print(f"\n{table_path}:")
        print(f"  Rows: {table_obj.num_rows:,}")
        print(f"  Columns: {len(table_obj.schema)}")
        print(f"  Size: {audit_report['training_tables'][table_path]['size_mb']:.1f} MB")
        print(f"  Dates: {min_date} to {max_date}")
        print(f"  Modified: {table_obj.modified}")
        
    except Exception as e:
        audit_report['training_tables'][table_path] = {
            'exists': False,
            'error': str(e)[:100]
        }
        print(f"\n{table_path}: NOT FOUND")

# 3. AUDIT DATA WAREHOUSE TABLES
print("\n3. AUDITING DATA WAREHOUSE")
print("-"*40)

warehouse_tables = [
    'cftc_cot',
    'treasury_prices',
    'economic_indicators',
    'weather_data',
    'currency_data',
    'soybean_oil_prices',
    'crude_oil_prices',
    'palm_oil_prices',
    'corn_prices',
    'vix_daily',
    'news_intelligence',
    'social_sentiment'
]

for table_name in warehouse_tables:
    try:
        # Get row count
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
        """
        
        result = client.query(query).to_dataframe()
        row_count = result['row_count'].iloc[0]
        
        # Get schema sample
        schema_query = f"""
        SELECT *
        FROM `cbi-v14.forecasting_data_warehouse.{table_name}`
        LIMIT 1
        """
        
        sample = client.query(schema_query).to_dataframe()
        
        audit_report['data_warehouse'][table_name] = {
            'rows': row_count,
            'columns': list(sample.columns),
            'column_count': len(sample.columns)
        }
        
        print(f"\n{table_name}:")
        print(f"  Rows: {row_count:,}")
        print(f"  Columns: {len(sample.columns)}")
        print(f"  Key fields: {', '.join(sample.columns[:5])}")
        
    except Exception as e:
        audit_report['data_warehouse'][table_name] = {
            'error': str(e)[:100]
        }
        print(f"\n{table_name}: ERROR - {str(e)[:50]}")

# 4. CHECK VIEWS AND DEPENDENCIES
print("\n4. AUDITING VIEWS")
print("-"*40)

view_query = """
SELECT 
    table_catalog,
    table_schema,
    table_name,
    table_type
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'VIEW'
"""

try:
    views = client.query(view_query).to_dataframe()
    print(f"Total views: {len(views)}")
    
    for _, view in views.iterrows():
        view_name = f"{view['table_schema']}.{view['table_name']}"
        audit_report['views'][view_name] = {
            'type': 'VIEW',
            'dataset': view['table_schema']
        }
        print(f"  • {view_name}")
        
except Exception as e:
    print(f"Error getting views: {str(e)[:100]}")

# 5. CHECK DATA QUALITY METRICS
print("\n5. DATA QUALITY METRICS")
print("-"*40)

# Check the most recent training dataset for quality
quality_checks = []

try:
    # Find the most recent/complete training dataset
    for table_path in ['models.training_complete_enhanced', 'models.training_dataset_enhanced', 'models.training_dataset']:
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT date) as unique_dates,
                SUM(CASE WHEN zl_price_current IS NULL THEN 1 ELSE 0 END) as null_prices,
                SUM(CASE WHEN target_1w IS NULL THEN 1 ELSE 0 END) as null_targets
            FROM `cbi-v14.{table_path}`
            """
            
            quality = client.query(query).to_dataframe()
            
            if quality['total_rows'].iloc[0] > 0:
                print(f"\n{table_path} Quality:")
                print(f"  Total rows: {quality['total_rows'].iloc[0]:,}")
                print(f"  Unique dates: {quality['unique_dates'].iloc[0]:,}")
                print(f"  Null prices: {quality['null_prices'].iloc[0]}")
                print(f"  Null targets: {quality['null_targets'].iloc[0]}")
                
                quality_checks.append({
                    'table': table_path,
                    'metrics': quality.to_dict('records')[0]
                })
                break
                
        except:
            continue
            
except Exception as e:
    print(f"Error in quality checks: {str(e)[:100]}")

audit_report['quality_checks'] = quality_checks

# 6. IDENTIFY ISSUES AND RECOMMENDATIONS
print("\n6. ISSUES AND RECOMMENDATIONS")
print("-"*40)

issues = []
recommendations = []

# Check for duplicate training datasets
training_count = len([t for t in audit_report['training_tables'] if audit_report['training_tables'][t].get('exists', False)])
if training_count > 3:
    issues.append(f"Too many training datasets ({training_count}) - consolidation needed")
    recommendations.append("Identify the best training dataset and archive others")

# Check for missing CFTC data
if 'cftc_cot' in audit_report['data_warehouse']:
    if audit_report['data_warehouse']['cftc_cot'].get('rows', 0) < 100:
        issues.append("CFTC data has very few rows")
        recommendations.append("Load more CFTC historical data")

# Check for data freshness
for table_name, info in audit_report['training_tables'].items():
    if info.get('exists') and info.get('modified'):
        modified_date = datetime.fromisoformat(info['modified'].replace('Z', '+00:00').replace('+00:00', ''))
        days_old = (datetime.now() - modified_date).days
        if days_old > 7:
            issues.append(f"{table_name} is {days_old} days old")

print("\nIssues Found:")
for issue in issues:
    print(f"  ⚠ {issue}")
    
print("\nRecommendations:")
for rec in recommendations:
    print(f"  → {rec}")

audit_report['issues'] = issues
audit_report['recommendations'] = recommendations

# 7. SAVE AUDIT REPORT
print("\n7. SAVING AUDIT REPORT")
print("-"*40)

with open('data_audit_report.json', 'w') as f:
    json.dump(audit_report, f, indent=2, default=str)
    
print("✓ Audit report saved to data_audit_report.json")

# Summary
print("\n" + "="*80)
print("AUDIT SUMMARY")
print("="*80)
print(f"Datasets: {len(audit_report['datasets'])}")
print(f"Training tables found: {sum(1 for t in audit_report['training_tables'].values() if t.get('exists'))}")
print(f"Data warehouse tables: {len(audit_report['data_warehouse'])}")
print(f"Views: {len(audit_report['views'])}")
print(f"Issues identified: {len(issues)}")
print("\nNEXT STEPS:")
print("1. Review data_audit_report.json for complete details")
print("2. Identify the PRIMARY training dataset to use")
print("3. Map data flow from warehouse → training dataset")
print("4. Fix any broken linkages identified")
print("5. Archive redundant tables after confirming backups")
print("="*80)
