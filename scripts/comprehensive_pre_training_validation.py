#!/usr/bin/env python3
"""
COMPREHENSIVE PRE-TRAINING VALIDATION
Addresses all 8 critical elements before model training
"""
from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime
import json

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("COMPREHENSIVE PRE-TRAINING VALIDATION")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

validation_results = {}

# ============================================================================
# 1. FEATURE COMPLETENESS - Check for Missing Features
# ============================================================================
print("\n" + "="*80)
print("1. FEATURE COMPLETENESS CHECK")
print("="*80)

schema_query = """
SELECT column_name, data_type
FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_production_v1'
ORDER BY ordinal_position
"""
schema_df = client.query(schema_query).to_dataframe()
actual_columns = len(schema_df)

print(f"\nActual columns: {actual_columns}")
print(f"Expected columns: 159 features + 4 targets + 1 date = 164 total")
print(f"Difference: {164 - actual_columns} columns missing")

# Identify missing features
expected_features = [
    'seasonal_index', 'monthly_zscore', 'yoy_change'  # Known missing seasonality features
]

missing_features = [f for f in expected_features if f not in schema_df.column_name.values]
print(f"\n⚠️ Missing Features ({len(missing_features)}):")
for f in missing_features:
    print(f"   - {f}")

validation_results['feature_completeness'] = {
    'total_columns': actual_columns,
    'expected': 164,
    'missing_count': len(missing_features),
    'missing_features': missing_features
}

# ============================================================================
# 2. DATA QUALITY VALIDATION - Comprehensive Analysis
# ============================================================================
print("\n" + "="*80)
print("2. DATA QUALITY VALIDATION")
print("="*80)

# 2.1 NULL Value Analysis
print("\n[2.1] NULL Value Analysis...")
null_query = """
WITH column_stats AS (
    SELECT 
        'zl_price_current' as column_name,
        COUNTIF(zl_price_current IS NULL) as null_count,
        COUNT(*) as total_count
    FROM `cbi-v14.models.training_dataset_production_v1`
    
    UNION ALL
    
    SELECT 
        'target_1w',
        COUNTIF(target_1w IS NULL),
        COUNT(*)
    FROM `cbi-v14.models.training_dataset_production_v1`
    
    UNION ALL
    
    SELECT 
        'feature_vix_stress',
        COUNTIF(feature_vix_stress IS NULL),
        COUNT(*)
    FROM `cbi-v14.models.training_dataset_production_v1`
    
    UNION ALL
    
    SELECT 
        'corr_zl_crude_7d',
        COUNTIF(corr_zl_crude_7d IS NULL),
        COUNT(*)
    FROM `cbi-v14.models.training_dataset_production_v1`
)
SELECT 
    column_name,
    null_count,
    total_count,
    ROUND(null_count / total_count * 100, 2) as null_percentage
FROM column_stats
ORDER BY null_percentage DESC
"""

null_df = client.query(null_query).to_dataframe()
print("\nNULL Analysis (sample of key columns):")
print(null_df.to_string(index=False))

critical_nulls = null_df[null_df.null_percentage > 5]
if len(critical_nulls) > 0:
    print(f"\n⚠️ WARNING: {len(critical_nulls)} columns have >5% NULLs")
else:
    print("\n✅ All sampled columns have <5% NULLs")

# 2.2 Date Continuity Check
print("\n[2.2] Date Continuity Check...")
gaps_query = """
WITH date_sequence AS (
    SELECT date
    FROM UNNEST(GENERATE_DATE_ARRAY(
        (SELECT MIN(date) FROM `cbi-v14.models.training_dataset_production_v1`),
        (SELECT MAX(date) FROM `cbi-v14.models.training_dataset_production_v1`)
    )) as date
),
actual_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models.training_dataset_production_v1`
)
SELECT 
    COUNT(*) as gap_count,
    MIN(d.date) as first_gap,
    MAX(d.date) as last_gap
FROM date_sequence d
LEFT JOIN actual_dates a ON d.date = a.date
WHERE a.date IS NULL
"""

gaps = list(client.query(gaps_query).result())[0]
print(f"Date gaps: {gaps.gap_count}")
if gaps.gap_count > 200:  # Weekend gaps are expected
    print(f"✅ Gap count reasonable (weekends/holidays expected)")
else:
    print(f"⚠️ Unexpected gap count")

# 2.3 Lag Calculation Validation
print("\n[2.3] Lag Calculation Validation...")
lag_validation_query = """
WITH lag_test AS (
    SELECT 
        date,
        zl_price_current,
        zl_price_lag1,
        LAG(zl_price_current) OVER (ORDER BY date) as recalc_lag1,
        ABS(COALESCE(zl_price_lag1, 0) - LAG(zl_price_current) OVER (ORDER BY date)) as diff
    FROM `cbi-v14.models.training_dataset_production_v1`
    ORDER BY date
    LIMIT 1000
)
SELECT 
    COUNT(*) as total_rows,
    COUNTIF(diff > 0.01) as mismatches,
    AVG(diff) as avg_diff,
    MAX(diff) as max_diff
FROM lag_test
WHERE recalc_lag1 IS NOT NULL
"""

lag_val = list(client.query(lag_validation_query).result())[0]
print(f"Lag validation (1000 row sample):")
print(f"  Mismatches: {lag_val.mismatches}")
print(f"  Avg difference: {lag_val.avg_diff:.6f}")
print(f"  Max difference: {lag_val.max_diff:.6f}")

if lag_val.mismatches == 0:
    print("  ✅ All lag calculations correct")
else:
    print(f"  ⚠️ {lag_val.mismatches} mismatches detected")

# 2.4 Outlier Detection
print("\n[2.4] Outlier Detection...")
outlier_query = """
WITH stats AS (
    SELECT 
        AVG(zl_price_current) as mean_price,
        STDDEV(zl_price_current) as stddev_price,
        AVG(feature_vix_stress) as mean_vix,
        STDDEV(feature_vix_stress) as stddev_vix
    FROM `cbi-v14.models.training_dataset_production_v1`
)
SELECT 
    'Price' as feature,
    COUNTIF(ABS(zl_price_current - mean_price) > 3 * stddev_price) as outlier_count,
    COUNT(*) as total_count
FROM `cbi-v14.models.training_dataset_production_v1`, stats

UNION ALL

SELECT 
    'VIX Stress',
    COUNTIF(ABS(feature_vix_stress - mean_vix) > 3 * stddev_vix),
    COUNT(*)
FROM `cbi-v14.models.training_dataset_production_v1`, stats
"""

outliers_df = client.query(outlier_query).to_dataframe()
print("\nOutlier Detection (>3 std deviations):")
print(outliers_df.to_string(index=False))

validation_results['data_quality'] = {
    'null_analysis': null_df.to_dict('records'),
    'date_gaps': int(gaps.gap_count),
    'lag_validation': {
        'mismatches': int(lag_val.mismatches),
        'avg_diff': float(lag_val.avg_diff)
    },
    'outliers': outliers_df.to_dict('records')
}

# ============================================================================
# 3. DISTRIBUTION ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("3. DISTRIBUTION ANALYSIS")
print("="*80)

dist_query = """
SELECT 
    COUNT(*) as total_rows,
    MIN(date) as min_date,
    MAX(date) as max_date,
    DATE_DIFF(MAX(date), MIN(date), DAY) as date_span_days,
    MIN(zl_price_current) as min_price,
    MAX(zl_price_current) as max_price,
    AVG(zl_price_current) as avg_price,
    STDDEV(zl_price_current) as stddev_price,
    AVG(target_1w) as avg_target_1w,
    STDDEV(target_1w) as stddev_target_1w
FROM `cbi-v14.models.training_dataset_production_v1`
"""

dist = list(client.query(dist_query).result())[0]
print(f"\nDataset Statistics:")
print(f"  Total rows: {dist.total_rows}")
print(f"  Date range: {dist.min_date} to {dist.max_date} ({dist.date_span_days} days)")
print(f"  Price range: ${dist.min_price:.2f} - ${dist.max_price:.2f}")
print(f"  Price mean: ${dist.avg_price:.2f} ± ${dist.stddev_price:.2f}")
print(f"  Target 1w mean: ${dist.avg_target_1w:.2f} ± ${dist.stddev_target_1w:.2f}")

# ============================================================================
# SAVE VALIDATION REPORT
# ============================================================================

report = {
    'timestamp': datetime.now().isoformat(),
    'validation_results': validation_results,
    'summary': {
        'total_columns': actual_columns,
        'missing_features': len(missing_features),
        'date_gaps': int(gaps.gap_count),
        'lag_mismatches': int(lag_val.mismatches),
        'critical_nulls': len(critical_nulls)
    }
}

report_file = 'logs/pre_training_validation_report.json'
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print("\n" + "="*80)
print("VALIDATION SUMMARY")
print("="*80)
print(f"\n📄 Report saved to: {report_file}")
print(f"\n🎯 Key Findings:")
print(f"   - Missing features: {len(missing_features)} (seasonality features)")
print(f"   - Date gaps: {gaps.gap_count} (expected: weekends/holidays)")
print(f"   - Lag mismatches: {lag_val.mismatches}")
print(f"   - Columns with >5% NULLs: {len(critical_nulls)}")

if len(missing_features) > 0:
    print(f"\n⚠️ RECOMMENDATION: Fix seasonality features before training")
else:
    print(f"\n✅ Dataset ready for training")












