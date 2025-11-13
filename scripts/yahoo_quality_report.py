#!/usr/bin/env python3
"""
Yahoo Finance Comprehensive - Data Quality Audit
Checks for gaps, volatility issues, and data corruption
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

PROJECT_ID = 'cbi-v14'
client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("📊 YAHOO FINANCE COMPREHENSIVE - DATA QUALITY AUDIT")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

quality_issues = []

# Get primary symbol first
symbol_query = """
SELECT DISTINCT symbol, COUNT(*) as cnt
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol LIKE '%ZL%' OR symbol_name LIKE '%Soybean Oil%'
GROUP BY symbol
ORDER BY cnt DESC
LIMIT 1
"""

try:
    symbol_result = client.query(symbol_query).to_dataframe()
    primary_symbol = symbol_result.iloc[0]['symbol']
    print(f"\n🎯 Using primary symbol: {primary_symbol}")
except Exception as e:
    print(f"❌ Could not determine primary symbol: {e}")
    sys.exit(1)

# Quality Check 1: Data Gaps
print("\n" + "="*80)
print("QUALITY CHECK 1: DATA GAPS")
print("="*80)

gaps_query = f"""
WITH date_series AS (
    SELECT DATE_ADD('2000-01-01', INTERVAL day DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 9500)) as day
    WHERE DATE_ADD('2000-01-01', INTERVAL day DAY) <= CURRENT_DATE()
      AND EXTRACT(DAYOFWEEK FROM DATE_ADD('2000-01-01', INTERVAL day DAY)) NOT IN (1, 7)
),
yahoo_data AS (
    SELECT DISTINCT date
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = '{primary_symbol}'
)
SELECT 
    COUNT(*) as trading_days_expected,
    COUNT(y.date) as trading_days_found,
    COUNT(*) - COUNT(y.date) as missing_days,
    ROUND((COUNT(*) - COUNT(y.date)) / COUNT(*) * 100, 2) as missing_pct
FROM date_series d
LEFT JOIN yahoo_data y USING(date)
"""

try:
    gaps = client.query(gaps_query).to_dataframe()
    print("\n📊 Data Gaps Analysis:")
    print(gaps.to_string())
    
    missing_days = int(gaps.iloc[0]['missing_days'])
    missing_pct = float(gaps.iloc[0]['missing_pct'])
    
    if missing_days > 500:
        issue = f"CRITICAL: {missing_days} missing trading days ({missing_pct:.1f}%)"
        quality_issues.append(issue)
        print(f"❌ {issue}")
    elif missing_days > 100:
        issue = f"WARNING: {missing_days} missing trading days ({missing_pct:.1f}%)"
        quality_issues.append(issue)
        print(f"⚠️  {issue}")
    else:
        print(f"✅ Acceptable gap count: {missing_days} missing days ({missing_pct:.1f}%)")
    
    # Get sample of gaps
    gaps_sample_query = f"""
    WITH date_series AS (
        SELECT DATE_ADD('2000-01-01', INTERVAL day DAY) as date
        FROM UNNEST(GENERATE_ARRAY(0, 9500)) as day
        WHERE DATE_ADD('2000-01-01', INTERVAL day DAY) <= CURRENT_DATE()
          AND EXTRACT(DAYOFWEEK FROM DATE_ADD('2000-01-01', INTERVAL day DAY)) NOT IN (1, 7)
    ),
    yahoo_data AS (
        SELECT DISTINCT date
        FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
        WHERE symbol = '{primary_symbol}'
    ),
    gaps AS (
        SELECT d.date
        FROM date_series d
        LEFT JOIN yahoo_data y USING(date)
        WHERE y.date IS NULL
    )
    SELECT 
        MIN(date) as gap_start,
        MAX(date) as gap_end,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as gap_length
    FROM (
        SELECT 
            date,
            DATE_SUB(date, INTERVAL ROW_NUMBER() OVER (ORDER BY date) DAY) as grp
        FROM gaps
    )
    GROUP BY grp
    ORDER BY gap_length DESC
    LIMIT 10
    """
    
    gaps_sample = client.query(gaps_sample_query).to_dataframe()
    if not gaps_sample.empty:
        print(f"\n📊 Top 10 largest gaps:")
        print(gaps_sample.to_string())
    
except Exception as e:
    issue = f"Gap analysis failed: {e}"
    quality_issues.append(issue)
    print(f"❌ {issue}")

# Quality Check 2: Price Volatility
print("\n" + "="*80)
print("QUALITY CHECK 2: PRICE VOLATILITY")
print("="*80)

volatility_query = f"""
WITH price_changes AS (
    SELECT 
        date,
        close,
        LAG(close) OVER (ORDER BY date) as prev_close,
        ABS(close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) as pct_change
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = '{primary_symbol}'
    ORDER BY date
)
SELECT 
    MAX(pct_change) as max_daily_move,
    AVG(pct_change) as avg_daily_move,
    STDDEV(pct_change) as std_daily_move,
    COUNTIF(pct_change > 0.10) as days_with_10pct_moves,
    COUNTIF(pct_change > 0.20) as days_with_20pct_moves
FROM price_changes
WHERE pct_change IS NOT NULL
"""

try:
    volatility = client.query(volatility_query).to_dataframe()
    print("\n📊 Volatility Analysis:")
    print(volatility.to_string())
    
    max_move = float(volatility.iloc[0]['max_daily_move']) if volatility.iloc[0]['max_daily_move'] else 0
    days_10pct = int(volatility.iloc[0]['days_with_10pct_moves']) if volatility.iloc[0]['days_with_10pct_moves'] else 0
    days_20pct = int(volatility.iloc[0]['days_with_20pct_moves']) if volatility.iloc[0]['days_with_20pct_moves'] else 0
    
    if max_move > 0.25:
        issue = f"CRITICAL: Suspicious max daily move {max_move*100:.1f}% (>25%)"
        quality_issues.append(issue)
        print(f"❌ {issue}")
    elif max_move > 0.15:
        issue = f"WARNING: Large max daily move {max_move*100:.1f}% (>15%)"
        quality_issues.append(issue)
        print(f"⚠️  {issue}")
    else:
        print(f"✅ Max daily move {max_move*100:.1f}% is reasonable")
    
    if days_20pct > 10:
        issue = f"WARNING: {days_20pct} days with >20% moves (suspicious)"
        quality_issues.append(issue)
        print(f"⚠️  {issue}")
    
    if days_10pct > 100:
        issue = f"WARNING: {days_10pct} days with >10% moves (high volatility)"
        quality_issues.append(issue)
        print(f"⚠️  {issue}")
    else:
        print(f"✅ {days_10pct} days with >10% moves (acceptable)")
    
    # Get samples of extreme moves
    if days_10pct > 0:
        extreme_query = f"""
        WITH price_changes AS (
            SELECT 
                date,
                close,
                LAG(close) OVER (ORDER BY date) as prev_close,
                ROUND(ABS(close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) * 100, 2) as pct_change
            FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
            WHERE symbol = '{primary_symbol}'
            ORDER BY date
        )
        SELECT *
        FROM price_changes
        WHERE pct_change > 10
        ORDER BY pct_change DESC
        LIMIT 10
        """
        
        extreme = client.query(extreme_query).to_dataframe()
        print(f"\n📊 Top 10 extreme price moves:")
        print(extreme.to_string())
    
except Exception as e:
    issue = f"Volatility analysis failed: {e}"
    quality_issues.append(issue)
    print(f"❌ {issue}")

# Quality Check 3: Overlap Comparison (2020-2025)
print("\n" + "="*80)
print("QUALITY CHECK 3: YAHOO vs PRODUCTION COMPARISON (2020-2025)")
print("="*80)

overlap_query = f"""
WITH yahoo_overlap AS (
    SELECT 
        date,
        close as yahoo_close
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = '{primary_symbol}'
      AND date >= '2020-01-01'
),
prod_overlap AS (
    SELECT 
        DATE(time) as date,
        close as prod_close
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE DATE(time) >= '2020-01-01'
)
SELECT 
    COUNT(*) as overlap_count,
    AVG(ABS(y.yahoo_close - p.prod_close)) as avg_price_diff,
    MAX(ABS(y.yahoo_close - p.prod_close)) as max_price_diff,
    AVG(ABS(y.yahoo_close - p.prod_close) / p.prod_close * 100) as avg_pct_diff,
    MAX(ABS(y.yahoo_close - p.prod_close) / p.prod_close * 100) as max_pct_diff,
    COUNTIF(ABS(y.yahoo_close - p.prod_close) / p.prod_close > 0.05) as days_with_5pct_diff
FROM yahoo_overlap y
JOIN prod_overlap p USING(date)
"""

try:
    overlap_comp = client.query(overlap_query).to_dataframe()
    
    if not overlap_comp.empty and overlap_comp.iloc[0]['overlap_count'] > 0:
        print("\n📊 Overlap Comparison:")
        print(overlap_comp.to_string())
        
        max_pct_diff = float(overlap_comp.iloc[0]['max_pct_diff']) if overlap_comp.iloc[0]['max_pct_diff'] else 0
        avg_pct_diff = float(overlap_comp.iloc[0]['avg_pct_diff']) if overlap_comp.iloc[0]['avg_pct_diff'] else 0
        days_5pct = int(overlap_comp.iloc[0]['days_with_5pct_diff']) if overlap_comp.iloc[0]['days_with_5pct_diff'] else 0
        
        if max_pct_diff > 10:
            issue = f"CRITICAL: Max difference {max_pct_diff:.1f}% between yahoo and production"
            quality_issues.append(issue)
            print(f"❌ {issue}")
        elif max_pct_diff > 5:
            issue = f"WARNING: Max difference {max_pct_diff:.1f}% between sources"
            quality_issues.append(issue)
            print(f"⚠️  {issue}")
        else:
            print(f"✅ Max difference {max_pct_diff:.1f}% is acceptable")
        
        if days_5pct > 20:
            issue = f"WARNING: {days_5pct} days with >5% difference between sources"
            quality_issues.append(issue)
            print(f"⚠️  {issue}")
        
        # Sample of largest differences
        diff_sample_query = f"""
        WITH yahoo_overlap AS (
            SELECT 
                date,
                close as yahoo_close
            FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
            WHERE symbol = '{primary_symbol}'
              AND date >= '2020-01-01'
        ),
        prod_overlap AS (
            SELECT 
                DATE(time) as date,
                close as prod_close
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE DATE(time) >= '2020-01-01'
        )
        SELECT 
            y.date,
            y.yahoo_close,
            p.prod_close,
            ABS(y.yahoo_close - p.prod_close) as price_diff,
            ROUND(ABS(y.yahoo_close - p.prod_close) / p.prod_close * 100, 2) as pct_diff
        FROM yahoo_overlap y
        JOIN prod_overlap p USING(date)
        WHERE ABS(y.yahoo_close - p.prod_close) / p.prod_close > 0.02
        ORDER BY pct_diff DESC
        LIMIT 10
        """
        
        diff_sample = client.query(diff_sample_query).to_dataframe()
        if not diff_sample.empty:
            print(f"\n📊 Top 10 dates with largest differences:")
            print(diff_sample.to_string())
    else:
        print("\n✅ No overlap with production data (2020+)")
    
except Exception as e:
    print(f"⚠️  Overlap comparison not available: {e}")

# Final Summary
print("\n" + "="*80)
print("📋 DATA QUALITY SUMMARY")
print("="*80)

print(f"\n⚠️  Quality Issues Found: {len(quality_issues)}")
if quality_issues:
    for issue in quality_issues:
        print(f"   - {issue}")
else:
    print("   ✅ No quality issues detected")

print("\n" + "="*80)
print("GO/NO-GO DECISION")
print("="*80)

critical_issues = [i for i in quality_issues if 'CRITICAL' in i]
warnings = [i for i in quality_issues if 'WARNING' in i]

if len(critical_issues) > 0:
    print("❌ STOP - Critical data quality issues found")
    print("   Recommendation: Fix data quality before integration")
    sys.exit(1)
elif len(warnings) > 5:
    print("⚠️  PROCEED WITH CAUTION - Multiple warnings detected")
    print("   Recommendation: Review warnings carefully before proceeding")
    sys.exit(0)
else:
    print("✅ DATA QUALITY ACCEPTABLE")
    print("   Recommendation: Safe to proceed with integration")
    sys.exit(0)

