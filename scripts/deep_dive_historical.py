#!/usr/bin/env python3
"""
Deep Dive Historical Data Search
Thoroughly checks all potential historical data sources
"""
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 DEEP DIVE: HISTORICAL DATA SEARCH")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Priority targets
TARGETS = {
    'yahoo_finance_comprehensive': {
        'description': 'Yahoo Finance comprehensive dataset - might have historical prices',
        'tables': []
    },
    'models': {
        'description': 'Models dataset - FINAL_TRAINING_DATASET_COMPLETE had schema error',
        'tables': ['FINAL_TRAINING_DATASET_COMPLETE']
    },
    'archive': {
        'description': 'Archive dataset - might contain historical snapshots',
        'tables': []
    },
    'bkp': {
        'description': 'Backup dataset - check all backup tables',
        'tables': []
    },
    'archive_consolidation_nov6': {
        'description': 'Archive consolidation - might have historical data',
        'tables': []
    }
}

# Step 1: Get all tables in target datasets
print("\n" + "="*80)
print("STEP 1: DISCOVERING TABLES IN TARGET DATASETS")
print("="*80)

for dataset_id in TARGETS.keys():
    try:
        query = f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            TARGETS[dataset_id]['tables'] = result['table_name'].tolist()
            print(f"\n📊 {dataset_id}: {len(TARGETS[dataset_id]['tables'])} tables")
            for table in TARGETS[dataset_id]['tables'][:10]:
                print(f"   - {table}")
            if len(TARGETS[dataset_id]['tables']) > 10:
                print(f"   ... and {len(TARGETS[dataset_id]['tables']) - 10} more")
    except Exception as e:
        print(f"\n⚠️  {dataset_id}: Error - {e}")

# Step 2: Check yahoo_finance_comprehensive thoroughly
print("\n" + "="*80)
print("STEP 2: DEEP DIVE INTO yahoo_finance_comprehensive")
print("="*80)

if TARGETS['yahoo_finance_comprehensive']['tables']:
    for table in TARGETS['yahoo_finance_comprehensive']['tables']:
        table_path = f"{PROJECT_ID}.yahoo_finance_comprehensive.{table}"
        
        try:
            # Get schema first
            schema_query = f"""
            SELECT column_name, data_type
            FROM `{PROJECT_ID}.yahoo_finance_comprehensive.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
            """
            schema_result = client.query(schema_query).to_dataframe()
            
            if not schema_result.empty:
                # Find date columns
                date_cols = schema_result[
                    schema_result['column_name'].str.contains('date|time|timestamp', case=False, na=False) |
                    schema_result['data_type'].isin(['DATE', 'DATETIME', 'TIMESTAMP'])
                ]
                
                if not date_cols.empty:
                    date_col = date_cols.iloc[0]['column_name']
                    col_type = date_cols.iloc[0]['data_type']
                    
                    if col_type in ['TIMESTAMP', 'DATETIME']:
                        date_expr = f"DATE({date_col})"
                    else:
                        date_expr = date_col
                    
                    # Get stats
                    stats_query = f"""
                    SELECT 
                        COUNT(*) as row_count,
                        MIN({date_expr}) as earliest,
                        MAX({date_expr}) as latest,
                        DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as days,
                        COUNT(DISTINCT {date_expr}) as unique_dates
                    FROM `{table_path}`
                    WHERE {date_col} IS NOT NULL
                    """
                    stats_result = client.query(stats_query).to_dataframe()
                    
                    if not stats_result.empty and stats_result.iloc[0]['earliest']:
                        row = stats_result.iloc[0]
                        rows = int(row['row_count'])
                        earliest = row['earliest']
                        latest = row['latest']
                        days = int(row['days']) if row['days'] else 0
                        years = days / 365.25
                        unique_dates = int(row['unique_dates'])
                        
                        # Check for pre-2020
                        pre2020_query = f"""
                        SELECT COUNT(*) as pre2020_count
                        FROM `{table_path}`
                        WHERE {date_col} < '2020-01-01'
                        """
                        pre2020_result = client.query(pre2020_query).to_dataframe()
                        pre2020_count = int(pre2020_result.iloc[0]['pre2020_count']) if not pre2020_result.empty else 0
                        
                        print(f"\n✅ {table}")
                        print(f"   Rows: {rows:,}")
                        print(f"   Date Range: {earliest} to {latest}")
                        print(f"   Span: {years:.1f} years")
                        print(f"   Unique Dates: {unique_dates:,}")
                        
                        if pre2020_count > 0:
                            print(f"   🎯 PRE-2020 DATA: {pre2020_count:,} rows")
                        else:
                            print(f"   ⚠️  No pre-2020 data")
                        
                        # Show column names
                        all_cols = schema_result['column_name'].tolist()
                        print(f"   Columns: {', '.join(all_cols[:10])}")
                        if len(all_cols) > 10:
                            print(f"   ... and {len(all_cols) - 10} more columns")
        except Exception as e:
            print(f"\n❌ {table}: Error - {e}")

# Step 3: Check models.FINAL_TRAINING_DATASET_COMPLETE with different date columns
print("\n" + "="*80)
print("STEP 3: INVESTIGATING models.FINAL_TRAINING_DATASET_COMPLETE")
print("="*80)

table_path = f"{PROJECT_ID}.models.FINAL_TRAINING_DATASET_COMPLETE"

try:
    # Get schema
    schema_query = f"""
    SELECT column_name, data_type
    FROM `{PROJECT_ID}.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'FINAL_TRAINING_DATASET_COMPLETE'
    ORDER BY ordinal_position
    """
    schema_result = client.query(schema_query).to_dataframe()
    
    if not schema_result.empty:
        print(f"\n📊 Schema: {len(schema_result)} columns")
        
        # Find all potential date columns
        date_cols = schema_result[
            schema_result['column_name'].str.contains('date|time|timestamp', case=False, na=False) |
            schema_result['data_type'].isin(['DATE', 'DATETIME', 'TIMESTAMP', 'STRING'])
        ]
        
        print(f"\n📅 Potential date columns found: {len(date_cols)}")
        for _, row in date_cols.iterrows():
            print(f"   - {row['column_name']} ({row['data_type']})")
        
        # Try each date column
        for _, date_row in date_cols.iterrows():
            date_col = date_row['column_name']
            col_type = date_row['data_type']
            
            try:
                if col_type == 'STRING':
                    # Try parsing as date
                    date_expr = f"PARSE_DATE('%Y-%m-%d', {date_col})"
                    max_expr = f"MAX(PARSE_DATE('%Y-%m-%d', {date_col}))"
                elif col_type in ['TIMESTAMP', 'DATETIME']:
                    date_expr = f"DATE({date_col})"
                    max_expr = f"MAX(DATE({date_col}))"
                else:
                    date_expr = date_col
                    max_expr = f"MAX({date_col})"
                
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
                    
                    print(f"\n✅ Using column '{date_col}':")
                    print(f"   Rows: {rows:,}")
                    print(f"   Date Range: {earliest} to {latest}")
                    print(f"   Span: {years:.1f} years")
                    
                    # Check pre-2020
                    pre2020_query = f"""
                    SELECT COUNT(*) as pre2020_count
                    FROM `{table_path}`
                    WHERE {date_expr} < '2020-01-01'
                    """
                    pre2020_result = client.query(pre2020_query).to_dataframe()
                    pre2020_count = int(pre2020_result.iloc[0]['pre2020_count']) if not pre2020_result.empty else 0
                    
                    if pre2020_count > 0:
                        print(f"   🎯 PRE-2020 DATA: {pre2020_count:,} rows")
                    break
            except Exception as e:
                continue  # Try next column
                
except Exception as e:
    print(f"❌ Error: {e}")

# Step 4: Check all backup tables for historical data
print("\n" + "="*80)
print("STEP 4: CHECKING ALL BACKUP TABLES FOR HISTORICAL DATA")
print("="*80)

if TARGETS['bkp']['tables']:
    for table in TARGETS['bkp']['tables']:
        table_path = f"{PROJECT_ID}.bkp.{table}"
        
        try:
            # Try common date column names
            for date_col in ['time', 'date', 'timestamp', 'created_at', 'updated_at']:
                try:
                    # Check if column exists
                    col_check = f"""
                    SELECT COUNT(*) as col_exists
                    FROM `{PROJECT_ID}.bkp.INFORMATION_SCHEMA.COLUMNS`
                    WHERE table_name = '{table}' AND column_name = '{date_col}'
                    """
                    col_result = client.query(col_check).to_dataframe()
                    
                    if col_result.iloc[0]['col_exists'] > 0:
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
                            
                            # Check pre-2020
                            pre2020_query = f"""
                            SELECT COUNT(*) as pre2020_count
                            FROM `{table_path}`
                            WHERE {date_expr} < '2020-01-01'
                            """
                            pre2020_result = client.query(pre2020_query).to_dataframe()
                            pre2020_count = int(pre2020_result.iloc[0]['pre2020_count']) if not pre2020_result.empty else 0
                            
                            if years > 1 or pre2020_count > 0:
                                print(f"\n✅ {table} (using {date_col}):")
                                print(f"   Rows: {rows:,}")
                                print(f"   Date Range: {earliest} to {latest}")
                                print(f"   Span: {years:.1f} years")
                                if pre2020_count > 0:
                                    print(f"   🎯 PRE-2020 DATA: {pre2020_count:,} rows")
                            break
                except:
                    continue
        except Exception as e:
            pass

# Step 5: Search for tables with very old earliest dates
print("\n" + "="*80)
print("STEP 5: SEARCHING FOR TABLES WITH OLDEST DATA")
print("="*80)

# Check all datasets for tables with pre-2020 data
all_datasets = []
try:
    for dataset in client.list_datasets(project=PROJECT_ID):
        all_datasets.append(dataset.dataset_id)
except:
    pass

print(f"\nChecking {len(all_datasets)} datasets for oldest data...")

oldest_findings = []

for dataset_id in all_datasets[:15]:  # Limit to avoid timeout
    try:
        # Get tables
        query = f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        LIMIT 20
        """
        tables_result = client.query(query).to_dataframe()
        
        if not tables_result.empty:
            for table_name in tables_result['table_name'].tolist():
                table_path = f"{PROJECT_ID}.{dataset_id}.{table_name}"
                
                # Quick check - try to find date and get earliest
                try:
                    # Get date columns
                    schema_query = f"""
                    SELECT column_name, data_type
                    FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                    WHERE table_name = '{table_name}'
                      AND (
                        LOWER(column_name) LIKE '%date%' 
                        OR LOWER(column_name) LIKE '%time%'
                        OR data_type IN ('DATE', 'DATETIME', 'TIMESTAMP')
                      )
                    LIMIT 1
                    """
                    schema_result = client.query(schema_query).to_dataframe()
                    
                    if not schema_result.empty:
                        date_col = schema_result.iloc[0]['column_name']
                        col_type = schema_result.iloc[0]['data_type']
                        
                        if col_type in ['TIMESTAMP', 'DATETIME']:
                            date_expr = f"DATE({date_col})"
                        else:
                            date_expr = date_col
                        
                        earliest_query = f"""
                        SELECT MIN({date_expr}) as earliest
                        FROM `{table_path}`
                        WHERE {date_col} IS NOT NULL
                        """
                        earliest_result = client.query(earliest_query).to_dataframe()
                        
                        if not earliest_result.empty and earliest_result.iloc[0]['earliest']:
                            earliest = earliest_result.iloc[0]['earliest']
                            
                            # Check if pre-2020
                            if str(earliest) < '2020-01-01':
                                oldest_findings.append({
                                    'dataset': dataset_id,
                                    'table': table_name,
                                    'earliest': earliest
                                })
                except:
                    pass
    except:
        pass

if oldest_findings:
    print(f"\n🎯 Found {len(oldest_findings)} tables with pre-2020 data:")
    # Sort by string representation of date to avoid type errors
    for finding in sorted(oldest_findings, key=lambda x: str(x['earliest'])):
        print(f"   📅 {finding['dataset']}.{finding['table']}: earliest = {finding['earliest']}")
else:
    print("\n⚠️  No additional pre-2020 tables found in quick scan")

print("\n" + "="*80)

