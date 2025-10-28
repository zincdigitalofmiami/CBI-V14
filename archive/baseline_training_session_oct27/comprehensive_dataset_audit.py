#!/usr/bin/env python3
"""
COMPREHENSIVE DATASET AUDIT - NO DELETIONS
Audit everything before making ANY changes
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("COMPREHENSIVE DATASET AUDIT - TRUTHFUL ASSESSMENT")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Basic stats
print("1. BASIC STATISTICS")
print("-" * 40)

query = """
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    MIN(date) as earliest,
    MAX(date) as latest,
    DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

df = client.query(query).to_dataframe()
row = df.iloc[0]

print(f"Total rows: {row['total_rows']:,}")
print(f"Unique dates: {row['unique_dates']:,}")
print(f"Duplicates: {row['total_rows'] - row['unique_dates']}")
print(f"Date range: {row['earliest']} to {row['latest']}")
print(f"Days behind: {row['days_behind']}")
print()

# 2. Duplicate analysis
if row['total_rows'] > row['unique_dates']:
    print("2. DUPLICATE ANALYSIS")
    print("-" * 40)
    
    dup_query = """
    SELECT date, COUNT(*) as count, 
           STRING_AGG(CAST(RAND() as STRING) LIMIT 1) as sample_data
    FROM `cbi-v14.models_v4.training_dataset_super_enriched` 
    GROUP BY date 
    HAVING COUNT(*) > 1 
    ORDER BY count DESC
    """
    
    dup_df = client.query(dup_query).to_dataframe()
    print(f"Dates with duplicates: {len(dup_df)}")
    print(f"Total duplicate rows: {(dup_df['count'] - 1).sum()}")
    print()
    print("Duplicate dates:")
    for _, row in dup_df.iterrows():
        print(f"  {row['date']}: {row['count']} rows")
    print()
    
# 3. Critical data coverage
print("3. CRITICAL DATA COVERAGE")
print("-" * 40)

coverage_query = """
SELECT 
    COUNT(*) as total,
    COUNT(palm_price) as palm_count,
    COUNT(crude_price) as crude_count,
    COUNT(vix_level) as vix_count,
    COUNT(usd_brl_rate) as brl_count,
    COUNT(feature_vix_stress) as vix_stress_count,
    COUNT(feature_harvest_pace) as harvest_count,
    COUNT(feature_hidden_correlation) as hidden_corr_count,
    COUNT(corr_zl_palm_30d) as palm_corr_count,
    COUNT(crush_margin) as crush_count,
    COUNT(china_mentions) as china_count,
    COUNT(brazil_temperature_c) as weather_count
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

cov_df = client.query(coverage_query).to_dataframe()
row = cov_df.iloc[0]
total = row['total']

for col in cov_df.columns:
    if col != 'total':
        count = row[col]
        pct = count / total * 100
        status = "✅" if pct == 100 else "⚠️" if pct > 95 else "❌"
        print(f"{col:30s}: {count:4d}/{total} ({pct:5.1f}%) {status}")

print()

# 4. Data quality checks
print("4. DATA QUALITY CHECKS")
print("-" * 40)

quality_query = """
SELECT 
    MIN(palm_price) as min_palm,
    MAX(palm_price) as max_palm,
    AVG(palm_price) as avg_palm,
    MIN(crude_price) as min_crude,
    MAX(crude_price) as max_crude,
    AVG(crude_price) as avg_crude,
    MIN(vix_level) as min_vix,
    MAX(vix_level) as max_vix,
    AVG(vix_level) as avg_vix,
    MIN(zl_price_current) as min_zl,
    MAX(zl_price_current) as max_zl,
    AVG(zl_price_current) as avg_zl
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE palm_price IS NOT NULL
"""

qual_df = client.query(quality_query).to_dataframe()
row = qual_df.iloc[0]

print(f"Palm Oil:  ${row['min_palm']:.2f} - ${row['max_palm']:.2f} (avg: ${row['avg_palm']:.2f})")
print(f"Crude Oil: ${row['min_crude']:.2f} - ${row['max_crude']:.2f} (avg: ${row['avg_crude']:.2f})")
print(f"VIX:       {row['min_vix']:.2f} - {row['max_vix']:.2f} (avg: {row['avg_vix']:.2f})")
print(f"Soy Oil:   ${row['min_zl']:.2f} - ${row['max_zl']:.2f} (avg: ${row['avg_zl']:.2f})")
print()

# 5. Check for placeholder values
print("5. PLACEHOLDER/CONSTANT VALUE CHECK")
print("-" * 40)

placeholder_query = """
SELECT 
    COUNT(DISTINCT feature_vix_stress) as unique_vix_stress,
    COUNT(DISTINCT feature_harvest_pace) as unique_harvest,
    COUNT(DISTINCT brazil_temperature_c) as unique_temp,
    COUNT(DISTINCT avg_sentiment) as unique_sentiment,
    COUNT(DISTINCT seasonal_index) as unique_seasonal
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

plac_df = client.query(placeholder_query).to_dataframe()
row = plac_df.iloc[0]

print(f"Unique VIX stress values: {row['unique_vix_stress']}")
print(f"Unique harvest pace values: {row['unique_harvest']}")
print(f"Unique Brazil temps: {row['unique_temp']}")
print(f"Unique sentiment values: {row['unique_sentiment']}")
print(f"Unique seasonal index values: {row['unique_seasonal']}")
print()

if row['unique_harvest'] < 20:
    print(f"⚠️ WARNING: Harvest pace has only {row['unique_harvest']} unique values")
if row['unique_sentiment'] < 20:
    print(f"⚠️ WARNING: Sentiment has only {row['unique_sentiment']} unique values")

print()

# 6. Target coverage
print("6. TARGET VARIABLE COVERAGE")
print("-" * 40)

target_query = """
SELECT 
    COUNT(target_1w) as t1w_count,
    COUNT(target_1m) as t1m_count,
    COUNT(target_3m) as t3m_count,
    COUNT(target_6m) as t6m_count,
    COUNT(*) as total
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
"""

targ_df = client.query(target_query).to_dataframe()
row = targ_df.iloc[0]
total = row['total']

for col in ['t1w_count', 't1m_count', 't3m_count', 't6m_count']:
    count = row[col]
    pct = count / total * 100
    horizon = col.replace('_count', '').replace('t', 'target_')
    print(f"{horizon:15s}: {count:4d}/{total} ({pct:5.1f}%)")

print()

# Summary
print("=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)

issues = []
duplicates = df.iloc[0]['total_rows'] - df.iloc[0]['unique_dates']
days_behind = df.iloc[0]['days_behind']

if duplicates > 0:
    issues.append(f"Duplicates: {duplicates} rows")
if days_behind > 7:
    issues.append(f"Stale data: {days_behind} days behind")

if issues:
    print("⚠️ ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ No critical issues")

print()
print("RECOMMENDATION:")
if row['total_rows'] > row['unique_dates']:
    print("  - Deduplicate dataset before training")
if row['days_behind'] > 7:
    print("  - Refresh to current date")

print()
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
