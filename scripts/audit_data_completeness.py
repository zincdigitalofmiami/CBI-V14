#!/usr/bin/env python3
"""
DATA COMPLETENESS AUDIT FOR CBI-V14
Checks all tables for data completeness before running ingestion
"""

from google.cloud import bigquery
import pandas as pd

def audit_table_data(client, project_id, dataset, table_name):
    """Audit a single table for data completeness"""
    try:
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MIN(time) as earliest_date,
            MAX(time) as latest_date,
            COUNT(DISTINCT DATE(time)) as unique_days
        FROM `{project_id}.{dataset}.{table_name}`
        """
        
        result = client.query(query).to_dataframe()
        row = result.iloc[0]
        
        return {
            'table_name': table_name,
            'row_count': int(row['row_count']),
            'earliest_date': str(row['earliest_date']),
            'latest_date': str(row['latest_date']),
            'unique_days': int(row['unique_days']),
            'status': '✅ GOOD' if row['row_count'] > 100 else '❌ LOW' if row['row_count'] > 0 else '🚨 EMPTY'
        }
        
    except Exception as e:
        return {
            'table_name': table_name,
            'row_count': 0,
            'earliest_date': 'ERROR',
            'latest_date': 'ERROR', 
            'unique_days': 0,
            'status': f'💥 ERROR: {str(e)[:50]}'
        }

def main():
    """Run comprehensive data audit"""
    print("=" * 80)
    print("🔍 CBI-V14 DATA COMPLETENESS AUDIT")
    print("=" * 80)
    
    client = bigquery.Client(project='cbi-v14')
    project_id = 'cbi-v14'
    dataset = 'forecasting_data_warehouse'
    
    # Critical tables to audit
    critical_tables = [
        'soybean_oil_prices',
        'soybean_prices', 
        'soybean_meal_prices',
        'palm_oil_prices',
        'corn_prices',
        'wheat_prices',
        'cotton_prices',
        'crude_oil_prices',
        'treasury_prices',
        'vix_daily',
        'usd_index_prices',
        'weather_data',
        'economic_indicators',
        'harvest_progress',
        'biofuel_metrics',
        'social_sentiment',
        'news_intelligence',
        'volatility_data'
    ]
    
    print(f"📊 Auditing {len(critical_tables)} critical tables...")
    print()
    
    results = []
    empty_tables = []
    low_data_tables = []
    good_tables = []
    
    for table_name in critical_tables:
        result = audit_table_data(client, project_id, dataset, table_name)
        results.append(result)
        
        if result['status'] == '🚨 EMPTY':
            empty_tables.append(table_name)
        elif result['status'] == '❌ LOW':
            low_data_tables.append(table_name)
        else:
            good_tables.append(table_name)
    
    # Print results
    print("📊 AUDIT RESULTS:")
    print("-" * 80)
    print(f"{'Table Name':<25} {'Rows':<8} {'Days':<6} {'Status':<15} {'Date Range'}")
    print("-" * 80)
    
    for result in results:
        date_range = f"{result['earliest_date'][:10]} to {result['latest_date'][:10]}" if result['earliest_date'] != 'ERROR' else 'ERROR'
        print(f"{result['table_name']:<25} {result['row_count']:<8} {result['unique_days']:<6} {result['status']:<15} {date_range}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 AUDIT SUMMARY")
    print("=" * 80)
    print(f"✅ Good Tables ({len(good_tables)}): {', '.join(good_tables[:5])}{'...' if len(good_tables) > 5 else ''}")
    print(f"❌ Low Data Tables ({len(low_data_tables)}): {', '.join(low_data_tables)}")
    print(f"🚨 Empty Tables ({len(empty_tables)}): {', '.join(empty_tables)}")
    
    # Recommendations
    print("\n🎯 RECOMMENDATIONS:")
    if empty_tables:
        print(f"🚨 CRITICAL: Run ingestion for empty tables: {', '.join(empty_tables)}")
    if low_data_tables:
        print(f"⚠️  WARNING: Enhance data for low-data tables: {', '.join(low_data_tables)}")
    
    if not empty_tables and not low_data_tables:
        print("🎉 ALL TABLES HAVE SUFFICIENT DATA!")
    
    return {
        'empty_tables': empty_tables,
        'low_data_tables': low_data_tables,
        'good_tables': good_tables
    }

if __name__ == "__main__":
    main()
