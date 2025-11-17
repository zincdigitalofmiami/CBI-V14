#!/usr/bin/env python3
"""
BigQuery Inventory Script
Lists all tables, row counts, date ranges, and identifies gaps/issues
"""

from google.cloud import bigquery
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
PROJECT_ID = 'cbi-v14'
LOCATION = 'us-central1'

# Datasets to inventory
DATASETS = [
    'training',
    'models_v4',
    'forecasting_data_warehouse',
    'raw_intelligence',
    'yahoo_finance_comprehensive',
    'features',
    'predictions',
    'monitoring',
    'archive',
    'staging',
    'market_data',
    'models',
    'neural',
    'vegas_intelligence'
]

def get_table_info(client, dataset_id, table_id):
    """Get detailed information about a table."""
    try:
        table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
        
        # Get row count and basic info
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT date) as unique_dates,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `{table_ref}`
        WHERE date IS NOT NULL
        """
        
        try:
            result = client.query(query).result()
            row = list(result)[0]
            date_info = {
                'row_count': row.row_count,
                'unique_dates': row.unique_dates,
                'min_date': row.min_date.strftime('%Y-%m-%d') if row.min_date else None,
                'max_date': row.max_date.strftime('%Y-%m-%d') if row.max_date else None
            }
        except:
            # If no date column, just get row count
            query_simple = f"SELECT COUNT(*) as row_count FROM `{table_ref}`"
            result = client.query(query_simple).result()
            row = list(result)[0]
            date_info = {
                'row_count': row.row_count,
                'unique_dates': None,
                'min_date': None,
                'max_date': None
            }
        
        # Check for regime issues (for training tables)
        regime_info = None
        if 'training' in dataset_id and 'zl_training' in table_id:
            regime_query = f"""
            SELECT 
                COUNT(DISTINCT market_regime) as unique_regimes,
                MIN(training_weight) as min_weight,
                MAX(training_weight) as max_weight,
                COUNTIF(market_regime = 'allhistory') as allhistory_count,
                COUNTIF(training_weight = 1) as weight_1_count
            FROM `{table_ref}`
            """
            try:
                result = client.query(regime_query).result()
                row = list(result)[0]
                regime_info = {
                    'unique_regimes': row.unique_regimes,
                    'min_weight': row.min_weight,
                    'max_weight': row.max_weight,
                    'allhistory_count': row.allhistory_count,
                    'weight_1_count': row.weight_1_count
                }
            except:
                pass
        
        # Get column count
        table = client.get_table(table_ref)
        
        return {
            'dataset': dataset_id,
            'table': table_id,
            'row_count': date_info['row_count'],
            'column_count': len(table.schema),
            'date_range': {
                'min': date_info['min_date'],
                'max': date_info['max_date']
            } if date_info['min_date'] else None,
            'unique_dates': date_info['unique_dates'],
            'regime_info': regime_info,
            'status': 'OK'
        }
        
    except Exception as e:
        return {
            'dataset': dataset_id,
            'table': table_id,
            'error': str(e),
            'status': 'ERROR'
        }

def check_missing_tables(client):
    """Check for tables referenced in code but missing in BigQuery."""
    
    # Tables referenced in BUILD_TRAINING_TABLES_NEW_NAMING.sql
    expected_tables = [
        'raw_intelligence.commodity_soybean_oil_prices',
        'forecasting_data_warehouse.vix_data',
        'api.vw_ultimate_adaptive_signal'
    ]
    
    missing = []
    for table_ref in expected_tables:
        try:
            client.get_table(f"{PROJECT_ID}.{table_ref}")
        except:
            missing.append(table_ref)
    
    return missing

def analyze_gaps(inventory):
    """Analyze gaps and issues from inventory."""
    
    gaps = {
        'training_issues': [],
        'missing_historical': [],
        'regime_problems': [],
        'missing_tables': [],
        'empty_tables': [],
        'recommendations': []
    }
    
    for item in inventory:
        if item['status'] == 'ERROR':
            continue
            
        # Check for empty tables
        if item['row_count'] == 0:
            gaps['empty_tables'].append(f"{item['dataset']}.{item['table']}")
            continue
        
        # Check training tables
        if 'training' in item['dataset'] and 'zl_training' in item['table']:
            # Check date range
            if item.get('date_range'):
                min_date = pd.to_datetime(item['date_range']['min'])
                if min_date.year >= 2020:
                    gaps['missing_historical'].append({
                        'table': f"{item['dataset']}.{item['table']}",
                        'starts_at': item['date_range']['min'],
                        'missing_years': min_date.year - 2000
                    })
            
            # Check regime issues
            if item.get('regime_info'):
                regime = item['regime_info']
                if regime['unique_regimes'] < 7:
                    gaps['regime_problems'].append({
                        'table': f"{item['dataset']}.{item['table']}",
                        'unique_regimes': regime['unique_regimes'],
                        'expected': '7-11'
                    })
                if regime['allhistory_count'] > 0:
                    gaps['regime_problems'].append({
                        'table': f"{item['dataset']}.{item['table']}",
                        'issue': f"{regime['allhistory_count']} rows with 'allhistory' placeholder"
                    })
                if regime['weight_1_count'] > item['row_count'] * 0.9:
                    gaps['regime_problems'].append({
                        'table': f"{item['dataset']}.{item['table']}",
                        'issue': f"{regime['weight_1_count']}/{item['row_count']} rows have weight=1"
                    })
    
    # Generate recommendations
    if gaps['missing_historical']:
        gaps['recommendations'].append("CRITICAL: Backfill pre-2020 data for training tables")
    
    if gaps['regime_problems']:
        gaps['recommendations'].append("CRITICAL: Fix regime assignments and weights")
    
    if gaps['empty_tables']:
        gaps['recommendations'].append("HIGH: Populate or remove empty tables")
    
    return gaps

def main():
    """Main inventory function."""
    
    print("=" * 60)
    print("BIGQUERY INVENTORY")
    print("=" * 60)
    print()
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    inventory = []
    total_rows = 0
    
    # Inventory each dataset
    for dataset_id in DATASETS:
        print(f"\n📁 Dataset: {dataset_id}")
        
        try:
            dataset = client.get_dataset(dataset_id)
            tables = list(client.list_tables(dataset_id))
            
            print(f"   Tables: {len(tables)}")
            
            dataset_rows = 0
            for table in tables:
                # Skip views
                if table.table_type == 'VIEW':
                    continue
                
                print(f"   Checking {table.table_id}...", end='')
                info = get_table_info(client, dataset_id, table.table_id)
                inventory.append(info)
                
                if info['status'] == 'OK':
                    dataset_rows += info['row_count']
                    print(f" {info['row_count']:,} rows")
                else:
                    print(" ERROR")
            
            total_rows += dataset_rows
            print(f"   Dataset total: {dataset_rows:,} rows")
            
        except Exception as e:
            print(f"   ⚠️ Error accessing dataset: {e}")
    
    # Check for missing tables
    print("\n📋 Checking for missing referenced tables...")
    missing_tables = check_missing_tables(client)
    
    # Analyze gaps
    gaps = analyze_gaps(inventory)
    gaps['missing_tables'] = missing_tables
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 TOTALS:")
    print(f"  Datasets inventoried: {len(DATASETS)}")
    print(f"  Tables found: {len(inventory)}")
    print(f"  Total rows: {total_rows:,}")
    
    # Find largest tables
    sorted_tables = sorted(
        [t for t in inventory if t['status'] == 'OK'],
        key=lambda x: x['row_count'],
        reverse=True
    )
    
    print(f"\n📈 LARGEST TABLES:")
    for table in sorted_tables[:10]:
        print(f"  {table['dataset']}.{table['table']}: {table['row_count']:,} rows")
    
    # Training tables analysis
    training_tables = [t for t in inventory if 'training' in t['dataset'] and 'zl_training' in t['table']]
    
    if training_tables:
        print(f"\n🎯 TRAINING TABLES ANALYSIS:")
        for table in training_tables:
            print(f"\n  {table['table']}:")
            print(f"    Rows: {table['row_count']:,}")
            if table.get('date_range'):
                print(f"    Date range: {table['date_range']['min']} to {table['date_range']['max']}")
            if table.get('regime_info'):
                regime = table['regime_info']
                print(f"    Regimes: {regime['unique_regimes']} unique")
                print(f"    Weight range: {regime['min_weight']}-{regime['max_weight']}")
                if regime['allhistory_count'] > 0:
                    print(f"    ⚠️ ISSUE: {regime['allhistory_count']} rows with 'allhistory'")
    
    # Print critical issues
    print(f"\n⚠️ CRITICAL ISSUES:")
    
    if missing_tables:
        print(f"\n  Missing referenced tables:")
        for table in missing_tables:
            print(f"    - {table}")
    
    if gaps['missing_historical']:
        print(f"\n  Tables missing pre-2020 data:")
        for issue in gaps['missing_historical'][:5]:
            print(f"    - {issue['table']}: starts at {issue['starts_at']}")
    
    if gaps['regime_problems']:
        print(f"\n  Regime assignment problems:")
        for issue in gaps['regime_problems'][:5]:
            print(f"    - {issue['table']}: {issue.get('issue', f'Only {issue.get('unique_regimes')} regimes')}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in gaps['recommendations']:
        print(f"  - {rec}")
    
    # Save detailed report
    report_path = Path("/Users/kirkmusick/Documents/GitHub/CBI-V14/scripts/audits/bigquery_inventory_report.json")
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'datasets': len(DATASETS),
            'tables': len(inventory),
            'total_rows': total_rows,
            'missing_tables': len(missing_tables),
            'training_issues': len(gaps['missing_historical']) + len(gaps['regime_problems'])
        },
        'gaps': gaps,
        'inventory': inventory
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return report

if __name__ == "__main__":
    main()
