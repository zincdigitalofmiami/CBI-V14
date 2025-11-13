#!/usr/bin/env python3
"""
Audit Newly Backfilled Historical Data
Verify the 55,937 historical rows and 12 commodities mentioned in QUICK_REFERENCE.txt
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT_ID = "cbi-v14"
client = bigquery.Client(project=PROJECT_ID)

print("=" * 80)
print("🔍 AUDITING NEWLY BACKFILLED HISTORICAL DATA")
print("=" * 80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("=" * 80)

# Define commodity columns to check
commodities = {
    'Soybean Oil': ['zl_price_current', 'soybean_oil_price'],
    'Soybeans': ['soybeans_price', 'zs_price'],
    'Corn': ['corn_price', 'zc_price'],
    'Wheat': ['wheat_price', 'zw_price'],
    'Soybean Meal': ['soybean_meal_price', 'zm_price'],
    'Crude Oil': ['crude_oil_price', 'cl_price'],
    'Natural Gas': ['natural_gas_price', 'ng_price'],
    'Gold': ['gold_price', 'gc_price'],
    'USD Index': ['usd_index', 'dx_price'],
    'S&P 500': ['sp500_price', 'es_price'],
    'VIX': ['vix_index', 'vix_price'],
    'Silver': ['silver_price', 'si_price'],
    'Copper': ['copper_price', 'hg_price']
}

def check_commodity_coverage(table_path):
    """Check coverage for each commodity in a table"""
    results = {}
    
    for commodity_name, possible_columns in commodities.items():
        for col in possible_columns:
            try:
                query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(CASE WHEN date >= '2000-01-01' AND date < '2020-01-01' THEN 1 END) as historical_rows,
                    COUNT(CASE WHEN date >= '2020-01-01' THEN 1 END) as recent_rows,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(DISTINCT date) as unique_dates
                FROM `{table_path}`
                WHERE `{col}` IS NOT NULL
                """
                
                result = client.query(query).to_dataframe()
                if result.iloc[0]['total_rows'] > 0:
                    results[commodity_name] = {
                        'column': col,
                        'total_rows': int(result.iloc[0]['total_rows']),
                        'historical_rows': int(result.iloc[0]['historical_rows']),
                        'recent_rows': int(result.iloc[0]['recent_rows']),
                        'earliest_date': str(result.iloc[0]['earliest_date']),
                        'latest_date': str(result.iloc[0]['latest_date']),
                        'unique_dates': int(result.iloc[0]['unique_dates'])
                    }
                    break  # Found data for this commodity
            except Exception as e:
                continue
    
    return results

# Check main training tables
print("\n📊 CHECKING PRODUCTION TRAINING TABLES")
print("-" * 70)

horizons = ['1w', '1m', '3m', '6m', '12m']
all_results = {}

for horizon in horizons:
    table = f"cbi-v14.models_v4.production_training_data_{horizon}"
    print(f"\nChecking {horizon} horizon table...")
    
    try:
        # First get basic stats
        stats_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(CASE WHEN date >= '2000-01-01' AND date < '2020-01-01' THEN 1 END) as historical_rows,
            COUNT(CASE WHEN date >= '2020-01-01' THEN 1 END) as recent_rows,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM `{table}`
        """
        
        stats = client.query(stats_query).to_dataframe()
        
        print(f"  Total rows: {stats.iloc[0]['total_rows']:,}")
        print(f"  Historical (pre-2020): {stats.iloc[0]['historical_rows']:,}")
        print(f"  Recent (2020+): {stats.iloc[0]['recent_rows']:,}")
        print(f"  Date range: {stats.iloc[0]['earliest_date']} to {stats.iloc[0]['latest_date']}")
        
        # Check commodity coverage
        commodity_coverage = check_commodity_coverage(table)
        all_results[horizon] = commodity_coverage
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:200]}")

# Check forecasting_data_warehouse tables
print("\n📊 CHECKING FORECASTING DATA WAREHOUSE")
print("-" * 70)

warehouse_tables = [
    'cbi-v14.forecasting_data_warehouse.soybean_oil_prices',
    'cbi-v14.forecasting_data_warehouse.corn_prices',
    'cbi-v14.forecasting_data_warehouse.soybeans_prices',
    'cbi-v14.forecasting_data_warehouse.wheat_prices',
    'cbi-v14.forecasting_data_warehouse.crude_oil_prices',
    'cbi-v14.forecasting_data_warehouse.natural_gas_prices'
]

for table in warehouse_tables:
    try:
        print(f"\nChecking {table.split('.')[-1]}...")
        
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(CASE WHEN date >= '2000-01-01' AND date < '2020-01-01' THEN 1 END) as historical_rows,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM `{table}`
        """
        
        result = client.query(query).to_dataframe()
        print(f"  Total: {result.iloc[0]['total_rows']:,} rows")
        print(f"  Historical: {result.iloc[0]['historical_rows']:,} rows")
        print(f"  Range: {result.iloc[0]['earliest_date']} to {result.iloc[0]['latest_date']}")
        
    except Exception as e:
        if "Not found" not in str(e):
            print(f"  ❌ Error: {str(e)[:100]}")

# Summary report
print("\n" + "=" * 80)
print("📈 COMMODITY COVERAGE SUMMARY")
print("=" * 80)

if all_results:
    # Get the most complete horizon (likely all have same data)
    best_horizon = max(all_results.keys(), key=lambda h: len(all_results[h]))
    coverage = all_results[best_horizon]
    
    print(f"\nData from production_training_data_{best_horizon}:")
    print("-" * 70)
    
    total_historical = 0
    commodities_with_data = []
    
    for commodity, data in sorted(coverage.items()):
        print(f"\n{commodity}:")
        print(f"  Column: {data['column']}")
        print(f"  Total rows: {data['total_rows']:,}")
        print(f"  Historical (pre-2020): {data['historical_rows']:,}")
        print(f"  Date range: {data['earliest_date']} to {data['latest_date']}")
        
        total_historical += data['historical_rows']
        if data['historical_rows'] > 0:
            commodities_with_data.append(commodity)
    
    print("\n" + "=" * 80)
    print("✅ BACKFILL VERIFICATION")
    print("=" * 80)
    print(f"Total historical rows backfilled: {total_historical:,}")
    print(f"Commodities with complete coverage: {len(commodities_with_data)}")
    print(f"Commodities: {', '.join(commodities_with_data)}")
    
    # Compare with QUICK_REFERENCE.txt claims
    print("\n📋 COMPARING WITH QUICK_REFERENCE.txt CLAIMS:")
    print("-" * 70)
    print("Claimed: 55,937 historical rows backfilled")
    print(f"Found: {total_historical:,} historical rows")
    print(f"Difference: {total_historical - 55937:+,}")
    print(f"\nClaimed: 12 commodities complete")
    print(f"Found: {len(commodities_with_data)} commodities with historical data")

print("\n" + "=" * 80)
print("Audit complete!")
