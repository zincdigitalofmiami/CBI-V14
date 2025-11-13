#!/usr/bin/env python3
"""
FULL SYSTEM AUDIT - Post-Integration & Backfill
Comprehensive check of all data, tables, and integrations
"""

from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("FULL SYSTEM AUDIT - POST-INTEGRATION & BACKFILL")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

issues = []
warnings = []
successes = []

# 1. CORE COMMODITY PRICES AUDIT
print("\n" + "="*80)
print("1. CORE COMMODITY PRICES AUDIT")
print("="*80)

core_commodities = {
    'soybean_oil_prices': ('time', 'DATETIME', 2000, 2025),
    'soybean_prices': ('time', 'DATETIME', 2000, 2025),
    'corn_prices': ('time', 'DATETIME', 2000, 2025),
    'wheat_prices': ('time', 'DATETIME', 2000, 2025),
    'soybean_meal_prices': ('time', 'TIMESTAMP', 2000, 2025),
}

for table, (date_col, expected_type, min_year, max_year) in core_commodities.items():
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(DATE({date_col})) as min_date,
            MAX(DATE({date_col})) as max_date,
            COUNTIF(DATE({date_col}) < '2020-01-01') as pre_2020_rows,
            COUNTIF(source_name = 'yahoo_finance_comprehensive_historical') as yahoo_backfill,
            COUNTIF(DATE({date_col}) >= '{min_year}-01-01' AND DATE({date_col}) <= '{max_year}-12-31') as expected_range_rows
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        status = "✅" if row.total_rows > 5000 and row.pre_2020_rows > 1000 else "⚠️"
        print(f"{status} {table:25} | {row.total_rows:7,} rows | {row.min_date} to {row.max_date} | "
              f"Pre-2020: {row.pre_2020_rows:5,} | Yahoo: {row.yahoo_backfill:5,}")
        
        if row.total_rows < 1000:
            issues.append(f"{table}: Only {row.total_rows} rows (expected >5000)")
        elif row.pre_2020_rows < 1000:
            warnings.append(f"{table}: Only {row.pre_2020_rows} pre-2020 rows")
        else:
            successes.append(f"{table}: {row.total_rows:,} rows with {row.pre_2020_rows:,} historical")
            
    except Exception as e:
        print(f"❌ {table:25} | ERROR: {str(e)[:60]}")
        issues.append(f"{table}: Query failed - {str(e)[:100]}")

# 2. ENERGY & METALS AUDIT
print("\n" + "="*80)
print("2. ENERGY & METALS AUDIT")
print("="*80)

energy_metals = {
    'crude_oil_prices': ('time', 'DATE', 2000, 2025),
    'natural_gas_prices': ('time', 'DATE', 2000, 2025),
    'gold_prices': ('time', 'DATE', 2000, 2025),
    'silver_prices': ('time', 'DATE', 2000, 2025),
    'copper_prices': ('time', 'DATE', 2000, 2025),
}

for table, (date_col, expected_type, min_year, max_year) in energy_metals.items():
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date,
            COUNTIF({date_col} < DATE('2020-01-01')) as pre_2020_rows,
            COUNTIF(source_name = 'yahoo_finance_comprehensive_historical') as yahoo_backfill
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        status = "✅" if row.total_rows > 4000 and row.pre_2020_rows > 1000 else "⚠️"
        print(f"{status} {table:25} | {row.total_rows:7,} rows | {row.min_date} to {row.max_date} | "
              f"Pre-2020: {row.pre_2020_rows:5,} | Yahoo: {row.yahoo_backfill:5,}")
        
        if row.total_rows < 1000:
            issues.append(f"{table}: Only {row.total_rows} rows")
        elif row.pre_2020_rows < 1000:
            warnings.append(f"{table}: Only {row.pre_2020_rows} pre-2020 rows")
        else:
            successes.append(f"{table}: {row.total_rows:,} rows with {row.pre_2020_rows:,} historical")
            
    except Exception as e:
        print(f"❌ {table:25} | ERROR: {str(e)[:60]}")
        issues.append(f"{table}: Query failed - {str(e)[:100]}")

# 3. MARKET INDICATORS AUDIT
print("\n" + "="*80)
print("3. MARKET INDICATORS AUDIT")
print("="*80)

indicators = {
    'vix_daily': ('date', 'DATE', 2000, 2025),
    'sp500_prices': ('time', 'DATETIME', 2000, 2025),
    'usd_index_prices': ('time', 'DATE', 2000, 2025),
}

for table, (date_col, expected_type, min_year, max_year) in indicators.items():
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date,
            COUNTIF({date_col} < DATE('2020-01-01')) as pre_2020_rows
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        status = "✅" if row.total_rows > 3000 else "⚠️"
        print(f"{status} {table:25} | {row.total_rows:7,} rows | {row.min_date} to {row.max_date} | "
              f"Pre-2020: {row.pre_2020_rows:5,}")
        
        if row.total_rows < 1000:
            issues.append(f"{table}: Only {row.total_rows} rows")
        else:
            successes.append(f"{table}: {row.total_rows:,} rows")
            
    except Exception as e:
        print(f"❌ {table:25} | ERROR: {str(e)[:60]}")
        issues.append(f"{table}: Query failed - {str(e)[:100]}")

# 4. PRODUCTION TRAINING TABLES AUDIT
print("\n" + "="*80)
print("4. PRODUCTION TRAINING TABLES AUDIT")
print("="*80)

training_tables = [
    'production_training_data_1w',
    'production_training_data_1m',
    'production_training_data_3m',
    'production_training_data_6m',
    'production_training_data_12m',
]

for table in training_tables:
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNTIF(date < '2020-01-01') as pre_2020_rows,
            COUNTIF(date >= '2000-01-01' AND date < '2020-01-01') as historical_rows
        FROM `cbi-v14.models_v4.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        if row.historical_rows > 0:
            status = "✅"
        elif row.pre_2020_rows > 0:
            status = "⚠️"
        else:
            status = "❌"
            
        print(f"{status} {table:35} | {row.total_rows:7,} rows | {row.min_date} to {row.max_date} | "
              f"Historical: {row.historical_rows:5,}")
        
        if row.historical_rows == 0:
            warnings.append(f"{table}: No historical data (2000-2019) - needs rebuild")
        else:
            successes.append(f"{table}: {row.total_rows:,} rows with {row.historical_rows:,} historical")
            
    except Exception as e:
        print(f"❌ {table:35} | ERROR: {str(e)[:60]}")
        issues.append(f"{table}: Query failed - {str(e)[:100]}")

# 5. REGIME TABLES AUDIT
print("\n" + "="*80)
print("5. HISTORICAL REGIME TABLES AUDIT")
print("="*80)

regime_tables = [
    'pre_crisis_2000_2007_historical',
    'crisis_2008_historical',
    'recovery_2010_2016_historical',
    'trade_war_2017_2019_historical',
]

for table in regime_tables:
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM `cbi-v14.models_v4.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        status = "✅" if row.total_rows > 100 else "⚠️"
        print(f"{status} {table:40} | {row.total_rows:6,} rows | {row.min_date} to {row.max_date}")
        
        if row.total_rows < 100:
            warnings.append(f"{table}: Only {row.total_rows} rows")
        else:
            successes.append(f"{table}: {row.total_rows:,} rows")
            
    except Exception as e:
        print(f"❌ {table:40} | ERROR: {str(e)[:60]}")
        issues.append(f"{table}: Query failed - {str(e)[:100]}")

# 6. YAHOO FINANCE COMPREHENSIVE AUDIT
print("\n" + "="*80)
print("6. YAHOO FINANCE COMPREHENSIVE SOURCE AUDIT")
print("="*80)

try:
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNTIF(date < '2020-01-01') as pre_2020_rows
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    """
    result = client.query(query).result()
    row = list(result)[0]
    
    print(f"✅ yahoo_normalized | {row.total_rows:10,} rows | {row.unique_symbols} symbols | "
          f"{row.min_date} to {row.max_date} | Pre-2020: {row.pre_2020_rows:8,}")
    
    if row.total_rows > 300000:
        successes.append(f"Yahoo Finance source: {row.total_rows:,} rows available")
    else:
        warnings.append(f"Yahoo Finance source: Only {row.total_rows:,} rows")
        
except Exception as e:
    print(f"❌ yahoo_normalized | ERROR: {str(e)[:60]}")
    issues.append(f"Yahoo Finance source: Query failed - {str(e)[:100]}")

# 7. VIEWS AUDIT
print("\n" + "="*80)
print("7. VIEWS AUDIT")
print("="*80)

views = [
    'yahoo_finance_historical',
    'soybean_oil_prices_historical_view',
]

for view in views:
    try:
        query = f"""
        SELECT COUNT(*) as total_rows
        FROM `cbi-v14.forecasting_data_warehouse.{view}`
        LIMIT 1
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        print(f"✅ {view:40} | {row.total_rows:10,} rows")
        successes.append(f"View {view}: Accessible with {row.total_rows:,} rows")
        
    except Exception as e:
        print(f"❌ {view:40} | ERROR: {str(e)[:60]}")
        issues.append(f"View {view}: Query failed - {str(e)[:100]}")

# 8. CRITICAL GAPS CHECK
print("\n" + "="*80)
print("8. CRITICAL GAPS CHECK")
print("="*80)

critical_tables = {
    'cftc_cot': ('report_date', 2006, 2025),
    'china_soybean_imports': ('date', 2017, 2025),
    'baltic_dry_index': ('date', 2000, 2025),
}

for table, (date_col, min_year, max_year) in critical_tables.items():
    try:
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN({date_col}) as min_date,
            MAX({date_col}) as max_date
        FROM `cbi-v14.forecasting_data_warehouse.{table}`
        """
        result = client.query(query).result()
        row = list(result)[0]
        
        if row.total_rows < 100:
            status = "❌"
            issues.append(f"{table}: CRITICAL GAP - Only {row.total_rows} rows (need {min_year}-{max_year})")
        else:
            status = "⚠️" if row.total_rows < 1000 else "✅"
            
        print(f"{status} {table:30} | {row.total_rows:6,} rows | {row.min_date} to {row.max_date}")
        
    except Exception as e:
        if "Not found: Table" in str(e):
            print(f"❌ {table:30} | MISSING - Table does not exist")
            issues.append(f"{table}: MISSING - Table does not exist")
        else:
            print(f"❌ {table:30} | ERROR: {str(e)[:60]}")
            issues.append(f"{table}: Query failed - {str(e)[:100]}")

# SUMMARY
print("\n" + "="*80)
print("AUDIT SUMMARY")
print("="*80)

print(f"\n✅ SUCCESSES: {len(successes)}")
for success in successes[:10]:  # Show first 10
    print(f"   • {success}")
if len(successes) > 10:
    print(f"   ... and {len(successes) - 10} more")

print(f"\n⚠️ WARNINGS: {len(warnings)}")
for warning in warnings:
    print(f"   • {warning}")

print(f"\n❌ ISSUES: {len(issues)}")
for issue in issues:
    print(f"   • {issue}")

# FINAL STATUS
print("\n" + "="*80)
print("FINAL STATUS")
print("="*80)

if len(issues) == 0 and len(warnings) < 5:
    print("✅ SYSTEM HEALTH: EXCELLENT")
    print("   All critical components operational")
    print("   Historical data integrated successfully")
    print("   Minor warnings only")
elif len(issues) == 0:
    print("⚠️ SYSTEM HEALTH: GOOD")
    print("   Core functionality working")
    print("   Some warnings need attention")
else:
    print("❌ SYSTEM HEALTH: NEEDS ATTENTION")
    print(f"   {len(issues)} critical issues found")
    print("   Review issues above")

print("\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)

# Exit with error code if issues found
if len(issues) > 0:
    sys.exit(1)
elif len(warnings) > 10:
    sys.exit(2)
else:
    sys.exit(0)
