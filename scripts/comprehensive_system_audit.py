#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM AUDIT
Reviews all tables, ingestions, gaps, integrations, and system health
"""

from google.cloud import bigquery
from datetime import datetime
import os
import sys
from pathlib import Path

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE SYSTEM AUDIT")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

issues = []
warnings = []
successes = []
info = []

# 1. DISCOVER ALL TABLES IN RAW_INTELLIGENCE
print("\n" + "="*80)
print("1. RAW_INTELLIGENCE - ALL TABLES")
print("="*80)

try:
    query = """
    SELECT table_name, 
           COUNT(*) as column_count,
           MAX(CASE WHEN column_name = 'time' OR column_name = 'date' THEN data_type END) as date_type
    FROM `cbi-v14.raw_intelligence.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name NOT LIKE '%_backup%'
      AND table_name NOT LIKE '%_ARCHIVED%'
    GROUP BY table_name
    ORDER BY table_name
    """
    result = client.query(query).result()
    
    fw_tables = []
    for row in result:
        fw_tables.append(row.table_name)
        print(f"  📊 {row.table_name:40} | {row.column_count:3} cols | Date type: {row.date_type or 'N/A'}")
    
    info.append(f"Found {len(fw_tables)} tables in raw_intelligence")
    
except Exception as e:
    print(f"❌ Error listing tables: {str(e)[:100]}")
    issues.append(f"Could not list raw_intelligence tables: {str(e)[:100]}")

# 2. DISCOVER ALL TABLES IN TRAINING & FEATURES
print("\n" + "="*80)
print("2. TRAINING & FEATURES - ALL TABLES")
print("="*80)

for dataset in ['training', 'features']:
    try:
        query = f"""
        SELECT table_name, 
               COUNT(*) as column_count
        FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name NOT LIKE '%_backup%'
          AND table_name NOT LIKE '%_ARCHIVED%'
        GROUP BY table_name
        ORDER BY table_name
        """
        result = client.query(query).result()
        
        tables_in_dataset = []
        for row in result:
            tables_in_dataset.append(row.table_name)
            print(f"  📊 {dataset}.{row.table_name:50} | {row.column_count:3} cols")
        
        info.append(f"Found {len(tables_in_dataset)} tables in {dataset}")
        
    except Exception as e:
        print(f"❌ Error listing tables in {dataset}: {str(e)[:100]}")
        issues.append(f"Could not list {dataset} tables: {str(e)[:100]}")

# 3. CHECK ALL INGESTION SCRIPTS
print("\n" + "="*80)
print("3. INGESTION SCRIPTS AUDIT")
print("="*80)

ingestion_dir = Path("src/ingestion")
if ingestion_dir.exists():
    ingestion_files = list(ingestion_dir.glob("*.py"))
    print(f"\nFound {len(ingestion_files)} ingestion scripts:")
    
    for script in sorted(ingestion_files):
        # Check if script has main function or is executable
        try:
            with open(script, 'r') as f:
                content = f.read()
                has_main = 'if __name__' in content or 'def main' in content
                status = "✅" if has_main else "⚠️"
                print(f"  {status} {script.name:50}")
                
                if not has_main:
                    warnings.append(f"Ingestion script {script.name} may not be executable")
        except Exception as e:
            print(f"  ❌ {script.name:50} | Error reading: {str(e)[:50]}")
            issues.append(f"Cannot read ingestion script {script.name}")
    
    info.append(f"Found {len(ingestion_files)} ingestion scripts")
else:
    warnings.append("Ingestion directory src/ingestion not found")
    print("  ⚠️ Ingestion directory not found")

# 4. DETAILED TABLE DATA AUDIT
print("\n" + "="*80)
print("4. DETAILED TABLE DATA AUDIT")
print("="*80)

# Key tables to audit in detail
key_tables = {
    'raw_intelligence': [
        # Mapped from forecasting_data_warehouse
        'shipping_baltic_dry_index', 'policy_biofuel', 'trade_china_soybean_imports',
        'commodity_crude_oil_prices', 'macro_economic_indicators', 'news_sentiments',
        'commodity_palm_oil_prices' 
    ],
    'training': [
        # Mapped from models_v4
        'zl_training_prod_all_1w', 'zl_training_prod_all_1m',
        'zl_training_prod_all_3m', 'zl_training_prod_all_6m',
        'zl_training_prod_all_12m', 'zl_training_prod_trump_all',
        'zl_training_full_precrisis_all', 'zl_training_full_crisis_all',
        'zl_training_full_recovery_all', 'zl_training_full_tradewar_all'
    ],
    'features': [
        'feature_metadata', 'market_regimes'
    ]
}

for dataset, tables in key_tables.items():
    print(f"\n{dataset.upper()}:")
    print("-"*80)
    
    for table in tables:
        try:
            # Try to get row count and date range
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                MIN(COALESCE(time, date, report_date, processed_timestamp, created_at, timestamp)) as min_date,
                MAX(COALESCE(time, date, report_date, processed_timestamp, created_at, timestamp)) as max_date
            FROM `cbi-v14.{dataset}.{table}`
            """
            result = client.query(query).result()
            row = list(result)[0]
            
            if row.total_rows > 0:
                status = "✅" if row.total_rows > 100 else "⚠️"
                print(f"  {status} {table:40} | {row.total_rows:8,} rows | {row.min_date} to {row.max_date}")
                
                if row.total_rows < 100:
                    warnings.append(f"{dataset}.{table}: Only {row.total_rows} rows")
                else:
                    successes.append(f"{dataset}.{table}: {row.total_rows:,} rows")
            else:
                print(f"  ⚠️ {table:40} | EMPTY")
                warnings.append(f"{dataset}.{table}: Empty table")
                
        except Exception as e:
            error_msg = str(e)
            if "Not found: Table" in error_msg:
                print(f"  ❌ {table:40} | MISSING")
                issues.append(f"{dataset}.{table}: Table does not exist")
            else:
                print(f"  ❌ {table:40} | ERROR: {error_msg[:50]}")
                warnings.append(f"{dataset}.{table}: Query error - {error_msg[:100]}")

# 5. CHECK VIEWS
print("\n" + "="*80)
print("5. VIEWS AUDIT")
print("="*80)

try:
    query = """
    SELECT table_name
    FROM `cbi-v14.features.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'VIEW'
    ORDER BY table_name
    """
    result = client.query(query).result()
    
    views = []
    for row in result:
        views.append(row.table_name)
        try:
            # Test if view is accessible
            test_query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.features.{row.table_name}` LIMIT 1"
            test_result = client.query(test_query).result()
            test_row = list(test_result)[0]
            print(f"  ✅ {row.table_name:50} | {test_row.cnt:,} rows")
            successes.append(f"View {row.table_name}: Accessible")
        except Exception as e:
            print(f"  ❌ {row.table_name:50} | ERROR: {str(e)[:50]}")
            issues.append(f"View {row.table_name}: Not accessible - {str(e)[:100]}")
    
    info.append(f"Found {len(views)} views in features")
    
except Exception as e:
    print(f"❌ Error listing views: {str(e)[:100]}")
    issues.append(f"Could not list views: {str(e)[:100]}")

# 6. CHECK YAHOO FINANCE COMPREHENSIVE DATASET
print("\n" + "="*80)
print("6. YAHOO FINANCE COMPREHENSIVE DATASET")
print("="*80)

try:
    query = """
    SELECT table_name, 
           COUNT(*) as column_count
    FROM `cbi-v14.yahoo_finance_comprehensive.INFORMATION_SCHEMA.COLUMNS`
    GROUP BY table_name
    ORDER BY table_name
    """
    result = client.query(query).result()
    
    yahoo_tables = []
    for row in result:
        yahoo_tables.append(row.table_name)
        print(f"  📊 {row.table_name:50} | {row.column_count:3} cols")
    
    # Check main table
    try:
        main_query = """
        SELECT COUNT(*) as total_rows,
               COUNT(DISTINCT symbol) as symbols,
               MIN(date) as min_date,
               MAX(date) as max_date
        FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
        """
        main_result = client.query(main_query).result()
        main_row = list(main_result)[0]
        print(f"\n  ✅ yahoo_normalized: {main_row.total_rows:,} rows, {main_row.symbols} symbols")
        print(f"     Date range: {main_row.min_date} to {main_row.max_date}")
        successes.append(f"Yahoo Finance source: {main_row.total_rows:,} rows available")
    except Exception as e:
        print(f"  ❌ Error querying yahoo_normalized: {str(e)[:100]}")
        issues.append(f"Yahoo Finance yahoo_normalized: Query failed")
    
    info.append(f"Found {len(yahoo_tables)} tables in yahoo_finance_comprehensive")
    
except Exception as e:
    print(f"❌ Error listing yahoo_finance_comprehensive: {str(e)[:100]}")
    issues.append(f"Could not list yahoo_finance_comprehensive: {str(e)[:100]}")

# 7. CHECK SIGNALS DATASET
print("\n" + "="*80)
print("7. SIGNALS DATASET")
print("="*80)

try:
    query = """
    SELECT table_name, table_type
    FROM `cbi-v14.features.INFORMATION_SCHEMA.TABLES`
    WHERE table_name NOT LIKE '%_ARCHIVED%'
    ORDER BY table_type, table_name
    """
    result = client.query(query).result()
    
    signal_tables = []
    signal_views = []
    for row in result:
        if row.table_type == 'VIEW':
            signal_views.append(row.table_name)
        else:
            signal_tables.append(row.table_name)
        print(f"  📊 {row.table_name:50} | {row.table_type}")
    
    info.append(f"Found {len(signal_tables)} tables and {len(signal_views)} views in features")
    
except Exception as e:
    if "Not found: Dataset" in str(e):
        print("  ⚠️ features dataset does not exist")
        warnings.append("features dataset not found")
    else:
        print(f"❌ Error listing features: {str(e)[:100]}")
        warnings.append(f"Could not list features dataset: {str(e)[:100]}")

# 8. CHECK VERTEX AI DIRECTORY
print("\n" + "="*80)
print("8. VERTEX AI DIRECTORY STRUCTURE")
print("="*80)

vertex_dirs = ['training', 'deployment', 'data', 'evaluation', 'prediction']
for dir_name in vertex_dirs:
    dir_path = Path(f"vertex-ai/{dir_name}")
    if dir_path.exists():
        files = list(dir_path.glob("*.py"))
        subdirs = [d for d in dir_path.iterdir() if d.is_dir()]
        print(f"  ✅ {dir_name:15} | {len(files):3} Python files | {len(subdirs):2} subdirs")
        if len(files) > 0:
            successes.append(f"Vertex AI {dir_name}: {len(files)} scripts")
    else:
        print(f"  ⚠️ {dir_name:15} | Directory not found")
        warnings.append(f"Vertex AI {dir_name} directory missing")

# 9. CHECK TRAINING SCRIPTS
print("\n" + "="*80)
print("9. TRAINING SCRIPTS AUDIT")
print("="*80)

training_paths = [
    "src/training",
    "scripts",
    "vertex-ai/training"
]

for base_path in training_paths:
    path = Path(base_path)
    if path.exists():
        scripts = list(path.rglob("*.py"))
        if scripts:
            print(f"\n{base_path}:")
            for script in sorted(scripts)[:10]:  # Show first 10
                rel_path = script.relative_to(Path("."))
                print(f"  📝 {rel_path}")
            if len(scripts) > 10:
                print(f"  ... and {len(scripts) - 10} more")
            info.append(f"Found {len(scripts)} Python scripts in {base_path}")
    else:
        warnings.append(f"Training path {base_path} not found")

# 10. CHECK SQL SCRIPTS
print("\n" + "="*80)
print("10. SQL SCRIPTS AUDIT")
print("="*80)

sql_path = Path("config/bigquery/bigquery-sql")
if sql_path.exists():
    sql_files = list(sql_path.rglob("*.sql"))
    print(f"\nFound {len(sql_files)} SQL files:")
    
    # Group by directory
    by_dir = {}
    for sql_file in sql_files:
        rel_path = sql_file.relative_to(sql_path)
        dir_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(rel_path.name)
    
    for dir_name, files in sorted(by_dir.items()):
        print(f"\n  {dir_name}:")
        for file in sorted(files)[:5]:  # Show first 5 per dir
            print(f"    📄 {file}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
    
    info.append(f"Found {len(sql_files)} SQL scripts")
else:
    warnings.append("SQL directory not found")

# 11. CRITICAL GAPS ANALYSIS
print("\n" + "="*80)
print("11. CRITICAL GAPS ANALYSIS")
print("="*80)

critical_checks = [
    ('trade_china_soybean_imports', 'raw_intelligence', 'date', 2017, 2025, 500),
    ('shipping_baltic_dry_index', 'raw_intelligence', 'date', 2000, 2025, 5000)
]

for table, dataset, date_col, min_year, max_year, min_rows in critical_checks:
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date
        FROM `cbi-v14.{dataset}.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        if row.total_rows < min_rows:
            status = "❌"
            issues.append(f"{dataset}.{table}: CRITICAL GAP - Only {row.total_rows} rows (need {min_year}-{max_year}, min {min_rows} rows)")
        else:
            status = "✅"
            successes.append(f"{dataset}.{table}: {row.total_rows:,} rows")
        
        print(f"  {status} {table:30} | {row.total_rows:6,} rows | {row.min_date} to {row.max_date}")
        
    except Exception as e:
        if "Not found: Table" in str(e):
            print(f"  ❌ {table:30} | MISSING")
            issues.append(f"{dataset}.{table}: MISSING - Table does not exist")
        else:
            print(f"  ❌ {table:30} | ERROR: {str(e)[:50]}")
            warnings.append(f"{dataset}.{table}: Query error")

# SUMMARY
print("\n" + "="*80)
print("AUDIT SUMMARY")
print("="*80)

print(f"\n✅ SUCCESSES: {len(successes)}")
for success in successes[:15]:
    print(f"   • {success}")
if len(successes) > 15:
    print(f"   ... and {len(successes) - 15} more")

print(f"\n⚠️ WARNINGS: {len(warnings)}")
for warning in warnings:
    print(f"   • {warning}")

print(f"\n❌ ISSUES: {len(issues)}")
for issue in issues:
    print(f"   • {issue}")

print(f"\nℹ️ INFO: {len(info)}")
for item in info:
    print(f"   • {item}")

# FINAL STATUS
print("\n" + "="*80)
print("FINAL STATUS")
print("="*80)

if len(issues) == 0 and len(warnings) < 10:
    print("✅ SYSTEM HEALTH: EXCELLENT")
    status_code = 0
elif len(issues) == 0:
    print("⚠️ SYSTEM HEALTH: GOOD")
    print("   Some warnings need attention")
    status_code = 2
else:
    print(f"❌ SYSTEM HEALTH: NEEDS ATTENTION")
    print(f"   {len(issues)} critical issues found")
    status_code = 1

print("\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)

sys.exit(status_code)
