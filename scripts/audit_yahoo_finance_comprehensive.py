#!/usr/bin/env python3
"""
Comprehensive Audit of yahoo_finance_comprehensive Dataset
Full schema analysis, data quality checks, and integration assessment
"""
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "yahoo_finance_comprehensive"
WAREHOUSE_DATASET = "forecasting_data_warehouse"
MODELS_DATASET = "models_v4"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 COMPREHENSIVE AUDIT: yahoo_finance_comprehensive")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

audit_report = {
    'tables': {},
    'schema_issues': [],
    'data_quality_issues': [],
    'integration_gaps': [],
    'recommendations': []
}

# Get all tables
print("\n" + "="*80)
print("STEP 1: TABLE INVENTORY")
print("="*80)

try:
    query = f"""
    SELECT table_name, creation_time, row_count, size_bytes
    FROM `{PROJECT_ID}.{DATASET_ID}.__TABLES__`
    ORDER BY table_name
    """
    tables_df = client.query(query).to_dataframe()
    
    print(f"\n📊 Found {len(tables_df)} tables:")
    for _, row in tables_df.iterrows():
        size_mb = row['size_bytes'] / (1024 * 1024) if row['size_bytes'] else 0
        created = row['creation_time'].strftime('%Y-%m-%d') if row['creation_time'] else 'Unknown'
        print(f"   - {row['table_name']}: {row['row_count']:,} rows, {size_mb:.2f} MB, created {created}")
        
        audit_report['tables'][row['table_name']] = {
            'row_count': int(row['row_count']) if row['row_count'] else 0,
            'size_mb': size_mb,
            'created': created
        }
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Detailed schema audit for each table
print("\n" + "="*80)
print("STEP 2: SCHEMA ANALYSIS")
print("="*80)

for table_name in audit_report['tables'].keys():
    print(f"\n{'='*80}")
    print(f"📋 Analyzing: {table_name}")
    print(f"{'='*80}")
    
    try:
        # Get full schema
        schema_query = f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            ordinal_position
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        schema_df = client.query(schema_query).to_dataframe()
        
        audit_report['tables'][table_name]['schema'] = []
        
        print(f"\n📊 Schema ({len(schema_df)} columns):")
        print(f"{'Column':<40} {'Type':<20} {'Nullable':<10}")
        print("-" * 70)
        
        for _, col in schema_df.iterrows():
            print(f"{col['column_name']:<40} {col['data_type']:<20} {col['is_nullable']:<10}")
            
            audit_report['tables'][table_name]['schema'].append({
                'name': col['column_name'],
                'type': col['data_type'],
                'nullable': col['is_nullable']
            })
        
        # Find date columns
        date_cols = schema_df[
            schema_df['column_name'].str.contains('date|time|timestamp', case=False, na=False) |
            schema_df['data_type'].isin(['DATE', 'DATETIME', 'TIMESTAMP'])
        ]
        
        if not date_cols.empty:
            print(f"\n📅 Date columns found: {', '.join(date_cols['column_name'].tolist())}")
            audit_report['tables'][table_name]['date_columns'] = date_cols['column_name'].tolist()
        else:
            print(f"\n⚠️  No date columns found")
            audit_report['schema_issues'].append(f"{table_name}: No date columns")
        
        # Find price/value columns
        price_cols = schema_df[
            schema_df['column_name'].str.contains('price|close|open|high|low|value|amount', case=False, na=False)
        ]
        
        if not price_cols.empty:
            print(f"💰 Price columns: {', '.join(price_cols['column_name'].tolist()[:10])}")
            audit_report['tables'][table_name]['price_columns'] = price_cols['column_name'].tolist()
        
    except Exception as e:
        print(f"❌ Error analyzing schema: {e}")
        audit_report['schema_issues'].append(f"{table_name}: Schema analysis failed - {e}")

# Data quality checks
print("\n" + "="*80)
print("STEP 3: DATA QUALITY ASSESSMENT")
print("="*80)

quality_checks = [
    'all_symbols_20yr',
    'yahoo_normalized',
    'biofuel_components_canonical',
    'biofuel_components_raw',
    'rin_proxy_features_final'
]

for table_name in quality_checks:
    if table_name not in audit_report['tables']:
        continue
    
    print(f"\n{'='*80}")
    print(f"🔍 Quality Check: {table_name}")
    print(f"{'='*80}")
    
    table_path = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    try:
        # Get date column
        date_col = audit_report['tables'][table_name].get('date_columns', ['date'])[0]
        
        # Determine date expression
        schema = audit_report['tables'][table_name]['schema']
        date_type = next((col['type'] for col in schema if col['name'] == date_col), 'DATE')
        
        if date_type in ['TIMESTAMP', 'DATETIME']:
            date_expr = f"DATE({date_col})"
        else:
            date_expr = date_col
        
        # Comprehensive quality query
        quality_query = f"""
        WITH stats AS (
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT {date_expr}) as unique_dates,
                MIN({date_expr}) as earliest_date,
                MAX({date_expr}) as latest_date,
                DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as date_span_days,
                COUNTIF({date_col} IS NULL) as null_dates,
                COUNTIF({date_expr} < '2000-01-01') as pre2000_rows,
                COUNTIF({date_expr} >= '2000-01-01' AND {date_expr} < '2020-01-01') as pre2020_rows,
                COUNTIF({date_expr} >= '2020-01-01') as post2020_rows
            FROM `{table_path}`
        )
        SELECT 
            *,
            ROUND(date_span_days / 365.25, 1) as years_span,
            ROUND(100.0 * null_dates / total_rows, 2) as null_pct
        FROM stats
        """
        
        quality_df = client.query(quality_query).to_dataframe()
        
        if not quality_df.empty:
            row = quality_df.iloc[0]
            
            print(f"\n📊 Data Coverage:")
            print(f"   Total Rows: {int(row['total_rows']):,}")
            print(f"   Unique Dates: {int(row['unique_dates']):,}")
            print(f"   Date Range: {row['earliest_date']} to {row['latest_date']}")
            print(f"   Span: {row['years_span']:.1f} years ({int(row['date_span_days']):,} days)")
            print(f"   NULL dates: {int(row['null_dates']):,} ({row['null_pct']:.2f}%)")
            
            print(f"\n📅 Historical Coverage:")
            print(f"   Pre-2000: {int(row['pre2000_rows']):,} rows")
            print(f"   2000-2019: {int(row['pre2020_rows']):,} rows")
            print(f"   2020+: {int(row['post2020_rows']):,} rows")
            
            # Store in audit report
            audit_report['tables'][table_name]['quality'] = {
                'total_rows': int(row['total_rows']),
                'unique_dates': int(row['unique_dates']),
                'earliest_date': str(row['earliest_date']),
                'latest_date': str(row['latest_date']),
                'years_span': float(row['years_span']),
                'null_dates': int(row['null_dates']),
                'pre2000_rows': int(row['pre2000_rows']),
                'pre2020_rows': int(row['pre2020_rows']),
                'post2020_rows': int(row['post2020_rows'])
            }
            
            # Quality issues
            if row['null_pct'] > 5:
                issue = f"{table_name}: High null date percentage ({row['null_pct']:.2f}%)"
                print(f"   ⚠️  {issue}")
                audit_report['data_quality_issues'].append(issue)
            
            if row['pre2020_rows'] == 0 and 'historical' not in table_name.lower():
                issue = f"{table_name}: No pre-2020 historical data"
                print(f"   ⚠️  {issue}")
                audit_report['data_quality_issues'].append(issue)
        
        # Check for duplicates
        dup_query = f"""
        SELECT {date_expr} as date_val, COUNT(*) as dup_count
        FROM `{table_path}`
        WHERE {date_col} IS NOT NULL
        GROUP BY {date_expr}
        HAVING COUNT(*) > 1
        ORDER BY dup_count DESC
        LIMIT 5
        """
        
        dup_df = client.query(dup_query).to_dataframe()
        
        if not dup_df.empty:
            total_dups = len(dup_df)
            print(f"\n⚠️  Duplicate dates found: {total_dups} dates with duplicates")
            print(f"   Top duplicates:")
            for _, dup_row in dup_df.head(3).iterrows():
                print(f"      {dup_row['date_val']}: {int(dup_row['dup_count'])} occurrences")
            
            audit_report['data_quality_issues'].append(f"{table_name}: {total_dups} dates with duplicates")
        else:
            print(f"\n✅ No duplicate dates found")
        
    except Exception as e:
        print(f"❌ Quality check failed: {e}")
        audit_report['data_quality_issues'].append(f"{table_name}: Quality check failed - {e}")

# Check integration with existing systems
print("\n" + "="*80)
print("STEP 4: INTEGRATION GAP ANALYSIS")
print("="*80)

# Check if data is referenced anywhere
print("\n🔍 Checking if yahoo_finance_comprehensive is used in production...")

# Check if it's referenced in forecasting_data_warehouse
try:
    warehouse_tables_query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{WAREHOUSE_DATASET}.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
    """
    warehouse_tables = client.query(warehouse_tables_query).to_dataframe()['table_name'].tolist()
    
    print(f"\n📊 forecasting_data_warehouse has {len(warehouse_tables)} tables")
    
    # Check for similar table names
    similar_tables = [t for t in warehouse_tables if any(
        keyword in t.lower() 
        for keyword in ['yahoo', 'finance', 'comprehensive', 'normalized', 'symbols']
    )]
    
    if similar_tables:
        print(f"   Similar tables found: {', '.join(similar_tables)}")
    else:
        print(f"   ⚠️  No similar tables found in forecasting_data_warehouse")
        audit_report['integration_gaps'].append("No yahoo_finance_comprehensive tables in forecasting_data_warehouse")
except Exception as e:
    print(f"❌ Error: {e}")

# Check if it's referenced in models_v4
try:
    models_tables_query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{MODELS_DATASET}.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
    """
    models_tables = client.query(models_tables_query).to_dataframe()['table_name'].tolist()
    
    print(f"\n📊 models_v4 has {len(models_tables)} tables")
    
    # Check for similar table names
    similar_models = [t for t in models_tables if any(
        keyword in t.lower() 
        for keyword in ['yahoo', 'finance', 'comprehensive', 'normalized', 'symbols']
    )]
    
    if similar_models:
        print(f"   Similar tables found: {', '.join(similar_models)}")
    else:
        print(f"   ⚠️  No similar tables found in models_v4")
        audit_report['integration_gaps'].append("No yahoo_finance_comprehensive tables in models_v4")
except Exception as e:
    print(f"❌ Error: {e}")

# Check dataset metadata
print("\n" + "="*80)
print("STEP 5: DATASET METADATA")
print("="*80)

try:
    dataset = client.get_dataset(f"{PROJECT_ID}.{DATASET_ID}")
    print(f"\n📋 Dataset Information:")
    print(f"   Dataset ID: {dataset.dataset_id}")
    print(f"   Project: {dataset.project}")
    print(f"   Location: {dataset.location}")
    print(f"   Created: {dataset.created}")
    print(f"   Modified: {dataset.modified}")
    print(f"   Description: {dataset.description or 'None'}")
    print(f"   Labels: {dataset.labels or 'None'}")
    
    if not dataset.description:
        audit_report['integration_gaps'].append("Dataset has no description")
    
    audit_report['dataset_metadata'] = {
        'created': str(dataset.created),
        'modified': str(dataset.modified),
        'location': dataset.location,
        'description': dataset.description,
        'labels': dataset.labels
    }
    
except Exception as e:
    print(f"❌ Error: {e}")

# Generate recommendations
print("\n" + "="*80)
print("STEP 6: RECOMMENDATIONS")
print("="*80)

recommendations = []

# Check if historical data can fill gaps
if audit_report['tables'].get('yahoo_normalized', {}).get('quality', {}).get('pre2020_rows', 0) > 0:
    rec = "✅ Use yahoo_normalized (233K+ pre-2020 rows) to backfill forecasting_data_warehouse.soybean_oil_prices"
    recommendations.append(rec)
    print(f"\n{rec}")

if audit_report['tables'].get('all_symbols_20yr', {}).get('quality', {}).get('pre2020_rows', 0) > 0:
    rec = "✅ Use all_symbols_20yr (44K+ pre-2020 rows) for multi-commodity historical analysis"
    recommendations.append(rec)
    print(f"\n{rec}")

if audit_report['tables'].get('biofuel_components_canonical', {}).get('quality', {}).get('pre2020_rows', 0) > 0:
    rec = "✅ Use biofuel_components_canonical for historical biofuel feature engineering"
    recommendations.append(rec)
    print(f"\n{rec}")

if 'No yahoo_finance_comprehensive tables in forecasting_data_warehouse' in audit_report['integration_gaps']:
    rec = "⚠️  Create views/tables in forecasting_data_warehouse that reference yahoo_finance_comprehensive"
    recommendations.append(rec)
    print(f"\n{rec}")

if 'No yahoo_finance_comprehensive tables in models_v4' in audit_report['integration_gaps']:
    rec = "⚠️  Rebuild production_training_data_* tables to include yahoo_finance_comprehensive historical data"
    recommendations.append(rec)
    print(f"\n{rec}")

if 'Dataset has no description' in audit_report['integration_gaps']:
    rec = "⚠️  Add dataset description and documentation"
    recommendations.append(rec)
    print(f"\n{rec}")

audit_report['recommendations'] = recommendations

# Final Summary
print("\n" + "="*80)
print("📊 AUDIT SUMMARY")
print("="*80)

print(f"\n📋 Tables Audited: {len(audit_report['tables'])}")
print(f"⚠️  Schema Issues: {len(audit_report['schema_issues'])}")
print(f"⚠️  Data Quality Issues: {len(audit_report['data_quality_issues'])}")
print(f"🔗 Integration Gaps: {len(audit_report['integration_gaps'])}")
print(f"✅ Recommendations: {len(audit_report['recommendations'])}")

# Total historical data available
total_pre2020 = sum(
    table.get('quality', {}).get('pre2020_rows', 0) 
    for table in audit_report['tables'].values()
)

print(f"\n🎯 Total Pre-2020 Historical Data: {total_pre2020:,} rows")

print("\n" + "="*80)
print("✅ Audit Complete")
print("="*80)

# Save audit report
import json
report_file = "docs/audits/YAHOO_FINANCE_COMPREHENSIVE_AUDIT_20251112.json"
with open(report_file, 'w') as f:
    # Convert to JSON-serializable format
    json_report = {
        'timestamp': datetime.now().isoformat(),
        'dataset': DATASET_ID,
        'tables_count': len(audit_report['tables']),
        'schema_issues_count': len(audit_report['schema_issues']),
        'data_quality_issues_count': len(audit_report['data_quality_issues']),
        'integration_gaps_count': len(audit_report['integration_gaps']),
        'total_pre2020_rows': total_pre2020,
        'recommendations': recommendations,
        'schema_issues': audit_report['schema_issues'],
        'data_quality_issues': audit_report['data_quality_issues'],
        'integration_gaps': audit_report['integration_gaps']
    }
    json.dump(json_report, f, indent=2)

print(f"\n💾 Detailed audit report saved to: {report_file}")

