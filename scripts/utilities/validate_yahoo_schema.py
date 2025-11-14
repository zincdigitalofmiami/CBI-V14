#!/usr/bin/env python3
"""
Yahoo Finance Schema Validation
CRITICAL: Run BEFORE integration to detect schema mismatches
"""
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = 'cbi-v14'
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🔬 YAHOO FINANCE SCHEMA VALIDATION")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

issues_found = []
warnings_found = []

# Check 1: Symbol standardization
print("\n" + "="*80)
print("CHECK 1: SYMBOL STANDARDIZATION")
print("="*80)

query = """
SELECT DISTINCT 
    symbol, 
    symbol_name, 
    COUNT(*) as cnt
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol LIKE '%ZL%' 
   OR symbol_name LIKE '%Soybean Oil%'
   OR symbol_name LIKE '%Soy Oil%'
GROUP BY symbol, symbol_name
ORDER BY cnt DESC
"""

try:
    symbols = client.query(query).to_dataframe()
    print("\n📊 Yahoo Symbols Found:")
    print(symbols.to_string())
    
    # Check if primary symbol is 'ZL'
    expected_symbols = ['ZL', 'ZL=F', 'ZL.1']
    found_symbols = symbols['symbol'].tolist()
    
    print(f"\n✅ Found {len(found_symbols)} symbol(s) related to Soybean Oil")
    
    # Flag non-standard symbols
    for symbol in found_symbols:
        if symbol not in expected_symbols:
            warning = f"Non-standard symbol found: {symbol}"
            warnings_found.append(warning)
            print(f"⚠️  {warning}")
    
except Exception as e:
    issue = f"Symbol check failed: {e}"
    issues_found.append(issue)
    print(f"❌ {issue}")

# Check 2: Price range validation
print("\n" + "="*80)
print("CHECK 2: PRICE RANGE VALIDATION")
print("="*80)

# First, get the actual symbol from check 1
if 'symbols' in locals() and not symbols.empty:
    primary_symbol = symbols.iloc[0]['symbol']
    print(f"\nUsing primary symbol: {primary_symbol}")
    
    query = f"""
    SELECT 
        MIN(close) as min_price,
        MAX(close) as max_price,
        AVG(close) as avg_price,
        STDDEV(close) as std_price,
        COUNT(*) as total_rows,
        COUNTIF(close IS NULL) as null_prices,
        COUNTIF(close <= 0) as zero_or_negative_prices
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = '{primary_symbol}'
    """
    
    try:
        prices = client.query(query).to_dataframe()
        print("\n📊 Yahoo Price Statistics:")
        print(prices.to_string())
        
        min_price = float(prices.iloc[0]['min_price'])
        max_price = float(prices.iloc[0]['max_price'])
        avg_price = float(prices.iloc[0]['avg_price'])
        null_prices = int(prices.iloc[0]['null_prices'])
        zero_prices = int(prices.iloc[0]['zero_or_negative_prices'])
        
        print(f"\n📈 Expected ZL range: $25-90/cwt")
        print(f"📈 Actual range: ${min_price:.2f} - ${max_price:.2f}")
        
        # Validate range
        if min_price < 10 or min_price > 100:
            issue = f"Min price out of expected range: ${min_price:.2f} (expected $25-90)"
            issues_found.append(issue)
            print(f"❌ {issue}")
        else:
            print(f"✅ Min price within reasonable range")
        
        if max_price < 10 or max_price > 200:
            issue = f"Max price out of expected range: ${max_price:.2f} (expected $25-90)"
            issues_found.append(issue)
            print(f"❌ {issue}")
        else:
            print(f"✅ Max price within reasonable range")
        
        if null_prices > 0:
            warning = f"Found {null_prices} NULL prices"
            warnings_found.append(warning)
            print(f"⚠️  {warning}")
        
        if zero_prices > 0:
            issue = f"Found {zero_prices} zero or negative prices"
            issues_found.append(issue)
            print(f"❌ {issue}")
        
    except Exception as e:
        issue = f"Price validation failed: {e}"
        issues_found.append(issue)
        print(f"❌ {issue}")

# Check 3: Date overlap detection
print("\n" + "="*80)
print("CHECK 3: DATE OVERLAP DETECTION")
print("="*80)

if 'primary_symbol' in locals():
    query = f"""
    WITH yahoo AS (
        SELECT DISTINCT DATE(date) as date
        FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
        WHERE symbol = '{primary_symbol}'
    ),
    prod AS (
        SELECT DISTINCT DATE(time) as date
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    )
    SELECT 
        COUNT(DISTINCT y.date) as yahoo_total_dates,
        COUNT(DISTINCT p.date) as prod_total_dates,
        COUNT(DISTINCT CASE WHEN y.date = p.date THEN y.date END) as overlap_dates,
        MIN(y.date) as yahoo_earliest,
        MAX(y.date) as yahoo_latest,
        MIN(p.date) as prod_earliest,
        MAX(p.date) as prod_latest
    FROM yahoo y
    FULL OUTER JOIN prod p ON y.date = p.date
    """
    
    try:
        overlap = client.query(query).to_dataframe()
        print("\n📊 Date Overlap Analysis:")
        print(overlap.to_string())
        
        overlap_count = int(overlap.iloc[0]['overlap_dates'])
        yahoo_total = int(overlap.iloc[0]['yahoo_total_dates'])
        prod_total = int(overlap.iloc[0]['prod_total_dates'])
        
        print(f"\n📅 Yahoo dates: {yahoo_total}")
        print(f"📅 Production dates: {prod_total}")
        print(f"📅 Overlapping dates: {overlap_count}")
        
        if overlap_count > 0:
            pct_overlap = (overlap_count / yahoo_total) * 100
            warning = f"Found {overlap_count} overlapping dates ({pct_overlap:.1f}% of yahoo data)"
            warnings_found.append(warning)
            print(f"⚠️  {warning}")
            print(f"⚠️  Need conflict resolution strategy!")
            
            # Get sample of overlapping dates
            overlap_sample_query = f"""
            WITH yahoo AS (
                SELECT DATE(date) as date, close as yahoo_close
                FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
                WHERE symbol = '{primary_symbol}'
            ),
            prod AS (
                SELECT DATE(time) as date, close as prod_close
                FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            )
            SELECT 
                y.date,
                y.yahoo_close,
                p.prod_close,
                ABS(y.yahoo_close - p.prod_close) as price_diff,
                ROUND(ABS(y.yahoo_close - p.prod_close) / p.prod_close * 100, 2) as pct_diff
            FROM yahoo y
            JOIN prod p ON y.date = p.date
            ORDER BY pct_diff DESC
            LIMIT 10
            """
            
            overlap_sample = client.query(overlap_sample_query).to_dataframe()
            print(f"\n📊 Top 10 overlapping dates with largest price differences:")
            print(overlap_sample.to_string())
            
            max_diff = overlap_sample['pct_diff'].max()
            if max_diff > 5.0:
                issue = f"Large price differences in overlap ({max_diff:.2f}% max)"
                issues_found.append(issue)
                print(f"❌ {issue}")
        else:
            print(f"✅ No overlapping dates - safe for backfill")
        
    except Exception as e:
        issue = f"Overlap detection failed: {e}"
        issues_found.append(issue)
        print(f"❌ {issue}")

# Check 4: Date type compatibility
print("\n" + "="*80)
print("CHECK 4: DATE TYPE COMPATIBILITY")
print("="*80)

try:
    # Check yahoo schema
    yahoo_schema_query = """
    SELECT column_name, data_type
    FROM `cbi-v14.yahoo_finance_comprehensive.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'yahoo_normalized'
      AND column_name IN ('date', 'close', 'symbol')
    ORDER BY ordinal_position
    """
    
    yahoo_schema = client.query(yahoo_schema_query).to_dataframe()
    print("\n📊 Yahoo schema (relevant columns):")
    print(yahoo_schema.to_string())
    
    # Check production schema
    prod_schema_query = """
    SELECT column_name, data_type
    FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'soybean_oil_prices'
      AND column_name IN ('time', 'close', 'symbol')
    ORDER BY ordinal_position
    """
    
    prod_schema = client.query(prod_schema_query).to_dataframe()
    print("\n📊 Production schema (relevant columns):")
    print(prod_schema.to_string())
    
    # Compare
    yahoo_date_type = yahoo_schema[yahoo_schema['column_name'] == 'date']['data_type'].iloc[0]
    prod_date_type = prod_schema[prod_schema['column_name'] == 'time']['data_type'].iloc[0]
    
    if yahoo_date_type != prod_date_type:
        warning = f"Date type mismatch: yahoo uses {yahoo_date_type}, production uses {prod_date_type}"
        warnings_found.append(warning)
        print(f"⚠️  {warning}")
        print(f"   Note: View handles conversion with TIMESTAMP(date)")
    else:
        print(f"✅ Date types compatible")
    
except Exception as e:
    issue = f"Schema check failed: {e}"
    issues_found.append(issue)
    print(f"❌ {issue}")

# Final Summary
print("\n" + "="*80)
print("📋 VALIDATION SUMMARY")
print("="*80)

print(f"\n❌ Critical Issues: {len(issues_found)}")
if issues_found:
    for issue in issues_found:
        print(f"   - {issue}")

print(f"\n⚠️  Warnings: {len(warnings_found)}")
if warnings_found:
    for warning in warnings_found:
        print(f"   - {warning}")

print("\n" + "="*80)
print("GO/NO-GO DECISION")
print("="*80)

if len(issues_found) == 0 and len(warnings_found) < 3:
    print("✅ SAFE TO PROCEED - No critical issues, minimal warnings")
    print("   Recommendation: Proceed with integration")
    sys.exit(0)
elif len(issues_found) == 0:
    print("⚠️  PROCEED WITH CAUTION - No critical issues but multiple warnings")
    print("   Recommendation: Review warnings, then proceed if acceptable")
    sys.exit(0)
else:
    print("❌ STOP - Critical issues found")
    print("   Recommendation: Fix issues before integration")
    sys.exit(1)

