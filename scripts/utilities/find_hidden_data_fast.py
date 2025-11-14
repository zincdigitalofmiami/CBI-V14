#!/usr/bin/env python3
"""
Fast Hidden Data Discovery - Focused on Historical Data
Samples tables efficiently to find hidden historical data sources
"""
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔍 FAST HIDDEN DATA DISCOVERY")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Known datasets to check
KNOWN_DATASETS = [
    'forecasting_data_warehouse',
    'models_v4',
    'models_v5',
    'neural',
    'signals',
    'archive',
    'market_data',
    'weather',
    'predictions',
    'dashboard'
]

# Discover all datasets
print("\n" + "="*80)
print("STEP 1: DISCOVERING ALL DATASETS")
print("="*80)

all_datasets = []
try:
    for dataset in client.list_datasets(project=PROJECT_ID):
        all_datasets.append(dataset.dataset_id)
    all_datasets.sort()
    print(f"\n📊 Found {len(all_datasets)} datasets:")
    for ds in all_datasets:
        print(f"   - {ds}")
except Exception as e:
    print(f"⚠️  Error listing datasets: {e}")
    all_datasets = KNOWN_DATASETS

# Quick table discovery - just get table names
print("\n" + "="*80)
print("STEP 2: QUICK TABLE DISCOVERY")
print("="*80)

all_tables = {}
for dataset_id in all_datasets:
    try:
        query = f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = client.query(query).to_dataframe()
        if not result.empty:
            tables = result['table_name'].tolist()
            all_tables[dataset_id] = tables
            print(f"📊 {dataset_id}: {len(tables)} tables")
    except Exception as e:
        print(f"  ⚠️  {dataset_id}: Error - {e}")

total_tables = sum(len(tables) for tables in all_tables.values())
print(f"\n📊 Total tables found: {total_tables}")

# Look for tables with keywords that suggest historical data
print("\n" + "="*80)
print("STEP 3: FINDING POTENTIAL HISTORICAL DATA SOURCES")
print("="*80)

keywords_historical = [
    'historical', 'archive', 'backup', 'old', 'legacy', 'snapshot',
    'complete', 'full', 'all', 'entire', 'backfill'
]

keywords_prices = [
    'price', 'prices', 'futures', 'commodity', 'oil', 'corn', 'wheat',
    'soy', 'crude', 'gold', 'gas', 'palm', 'canola'
]

potential_historical = []
potential_prices = []

for dataset, tables in all_tables.items():
    for table in tables:
        table_lower = table.lower()
        
        # Check for historical keywords
        if any(keyword in table_lower for keyword in keywords_historical):
            potential_historical.append((dataset, table))
        
        # Check for price keywords
        if any(keyword in table_lower for keyword in keywords_prices):
            potential_prices.append((dataset, table))

print(f"\n📦 Potential Historical Data Tables ({len(potential_historical)}):")
for dataset, table in potential_historical[:30]:
    print(f"   - {dataset}.{table}")

print(f"\n💰 Potential Price/Commodity Tables ({len(potential_prices)}):")
for dataset, table in potential_prices[:30]:
    print(f"   - {dataset}.{table}")

# Sample check - look for tables with "complete" or "full" in name
print("\n" + "="*80)
print("STEP 4: CHECKING COMPLETE/FULL TABLES FOR HISTORICAL DATA")
print("="*80)

complete_tables = []
for dataset, tables in all_tables.items():
    for table in tables:
        if any(word in table.lower() for word in ['complete', 'full', 'entire', 'all_data']):
            complete_tables.append((dataset, table))

print(f"\nFound {len(complete_tables)} 'complete' tables - checking for historical data...")

historical_findings = []

for dataset, table in complete_tables[:20]:  # Limit to first 20
    table_path = f"{PROJECT_ID}.{dataset}.{table}"
    
    try:
        # Quick check - get row count and try to find date range
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `{table_path}`
        """
        result = client.query(query).to_dataframe()
        row_count = int(result.iloc[0]['row_count']) if not result.empty else 0
        
        if row_count > 100:  # Only check tables with substantial data
            # Try to find date columns
            schema_query = f"""
            SELECT column_name, data_type
            FROM `{PROJECT_ID}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table}'
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
                
                # Get date range
                if col_type in ['TIMESTAMP', 'DATETIME']:
                    date_expr = f"DATE({date_col})"
                else:
                    date_expr = date_col
                
                date_query = f"""
                SELECT 
                    MIN({date_expr}) as earliest,
                    MAX({date_expr}) as latest,
                    DATE_DIFF(MAX({date_expr}), MIN({date_expr}), DAY) as days
                FROM `{table_path}`
                WHERE {date_col} IS NOT NULL
                """
                date_result = client.query(date_query).to_dataframe()
                
                if not date_result.empty and date_result.iloc[0]['earliest']:
                    earliest = date_result.iloc[0]['earliest']
                    latest = date_result.iloc[0]['latest']
                    days = int(date_result.iloc[0]['days']) if date_result.iloc[0]['days'] else 0
                    years = days / 365.25
                    
                    if years > 1:  # At least 1 year of data
                        historical_findings.append({
                            'dataset': dataset,
                            'table': table,
                            'rows': row_count,
                            'earliest': earliest,
                            'latest': latest,
                            'years': years
                        })
                        
                        print(f"  ✅ {dataset}.{table}: {row_count:,} rows, {years:.1f} years ({earliest} to {latest})")
    except Exception as e:
        pass  # Skip errors

# Check models_v4 for archived/backup tables
print("\n" + "="*80)
print("STEP 5: CHECKING ARCHIVED/BACKUP TABLES IN models_v4")
print("="*80)

if 'models_v4' in all_tables:
    archived = [t for t in all_tables['models_v4'] if '_ARCHIVED' in t or 'backup' in t.lower() or 'snapshot' in t.lower()]
    
    print(f"\nFound {len(archived)} archived/backup tables in models_v4:")
    for table in archived[:20]:
        print(f"   - {table}")
        
        # Quick check
        try:
            table_path = f"{PROJECT_ID}.models_v4.{table}"
            query = f"SELECT COUNT(*) as cnt FROM `{table_path}`"
            result = client.query(query).to_dataframe()
            count = int(result.iloc[0]['cnt']) if not result.empty else 0
            if count > 0:
                print(f"      → {count:,} rows")
        except:
            pass

# Summary
print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)

print(f"\n📊 Total datasets: {len(all_datasets)}")
print(f"📊 Total tables: {total_tables}")
print(f"📊 Potential historical tables: {len(potential_historical)}")
print(f"📊 Potential price tables: {len(potential_prices)}")
print(f"📊 Complete/full tables checked: {len(complete_tables)}")
print(f"📊 Historical data sources found: {len(historical_findings)}")

if historical_findings:
    print(f"\n🎯 HISTORICAL DATA SOURCES FOUND:")
    for finding in sorted(historical_findings, key=lambda x: x['years'], reverse=True):
        print(f"   📅 {finding['dataset']}.{finding['table']}: {finding['years']:.1f} years ({finding['earliest']} to {finding['latest']}), {finding['rows']:,} rows")

print("="*80)

