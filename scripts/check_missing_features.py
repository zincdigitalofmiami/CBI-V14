#!/usr/bin/env python3
"""
Check why 131 features are missing from the model
Analyze NULL values, constant values, and feature variance
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
VIEW_NAME = "train_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔍 ANALYZING MISSING FEATURES")
print("="*70)

# First get the list of features that ARE in the model
print("\n1️⃣  Getting features in model...")
try:
    query = f"""
    SELECT feature
    FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.bqml_1w_mean`)
    """
    model_features_df = client.query(query).to_dataframe()
    model_features = set(model_features_df['feature'].tolist())
    print(f"  ✅ Found {len(model_features)} features in model")
except Exception as e:
    print(f"  ❌ Error: {e}")
    model_features = set()

# Get all columns from view
print("\n2️⃣  Getting all columns from view...")
try:
    query = f"""
    SELECT column_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    """
    all_columns_df = client.query(query).to_dataframe()
    all_columns = set(all_columns_df['column_name'].tolist())
    
    # Expected exclusions
    exclusions = {
        'date', 'target_1w', 'target_1m', 'target_3m', 'target_6m',
        'treasury_10y_yield', 'econ_gdp_growth', 'econ_unemployment_rate',
        'news_article_count', 'news_avg_score',
        'crude_lead1_correlation', 'dxy_lead1_correlation',
        'vix_lead1_correlation', 'palm_lead2_correlation',
        'leadlag_zl_price', 'lead_signal_confidence',
        'days_to_next_event', 'post_event_window',
        'event_impact_level', 'event_vol_mult', 'tradewar_event_vol_mult'
    }
    
    expected_features = all_columns - exclusions
    missing_features = expected_features - model_features
    
    print(f"  ✅ Found {len(expected_features)} expected features")
    print(f"  📊 Missing: {len(missing_features)} features")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
    missing_features = set()

if not missing_features:
    print("\n✅ No missing features to analyze")
    exit(0)

# Sample missing features to analyze
sample_missing = list(missing_features)[:50]
print(f"\n3️⃣  Analyzing sample of {len(sample_missing)} missing features...")

# Check for NULL values and constant values
query = f"""
WITH feature_stats AS (
  SELECT
    {', '.join([f'''
    COUNT(*) as total_rows,
    COUNT({col}) as non_null_count_{col},
    COUNT(DISTINCT {col}) as distinct_count_{col},
    MIN({col}) as min_{col},
    MAX({col}) as max_{col},
    STDDEV({col}) as stddev_{col}
    ''' for col in sample_missing[:20]])}
  FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
  WHERE target_1w IS NOT NULL
)
SELECT * FROM feature_stats
"""

# Instead, check each feature individually
print(f"\n4️⃣  Checking NULL/constant status for missing features...")
feature_analysis = []

for feat in list(missing_features)[:50]:  # Check first 50
    try:
        query = f"""
        SELECT 
          COUNT(*) as total_rows,
          COUNT({feat}) as non_null_count,
          COUNT(DISTINCT {feat}) as distinct_count,
          MIN({feat}) as min_val,
          MAX({feat}) as max_val,
          STDDEV({feat}) as stddev_val
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
        WHERE target_1w IS NOT NULL
        """
        stats = client.query(query).to_dataframe().iloc[0]
        
        total = int(stats['total_rows'])
        non_null = int(stats['non_null_count'])
        distinct = int(stats['distinct_count'])
        stddev = float(stats['stddev_val']) if stats['stddev_val'] is not None else 0
        
        null_pct = (1 - non_null/total) * 100 if total > 0 else 100
        is_constant = distinct <= 1
        is_zero_variance = stddev == 0 or (stddev is None)
        
        feature_analysis.append({
            'feature': feat,
            'null_pct': null_pct,
            'is_null_only': non_null == 0,
            'is_constant': is_constant,
            'is_zero_variance': is_zero_variance,
            'distinct_count': distinct
        })
        
    except Exception as e:
        feature_analysis.append({
            'feature': feat,
            'error': str(e)[:50]
        })

# Summarize
print("\n5️⃣  SUMMARY OF MISSING FEATURES:")
null_only = [f for f in feature_analysis if f.get('is_null_only', False)]
constant = [f for f in feature_analysis if f.get('is_constant', False) and not f.get('is_null_only', False)]
zero_var = [f for f in feature_analysis if f.get('is_zero_variance', False) and not f.get('is_null_only', False)]
other = [f for f in feature_analysis if not f.get('is_null_only', False) and not f.get('is_constant', False) and not f.get('is_zero_variance', False) and 'error' not in f]

print(f"\n  📊 Analysis of {len(feature_analysis)} sampled features:")
print(f"     NULL-only: {len(null_only)}")
print(f"     Constant (single value): {len(constant)}")
print(f"     Zero variance: {len(zero_var)}")
print(f"     Other (have variance): {len(other)}")
print(f"     Errors: {len([f for f in feature_analysis if 'error' in f])}")

if null_only:
    print(f"\n  ❌ NULL-ONLY FEATURES ({len(null_only)}):")
    for f in null_only[:10]:
        print(f"     - {f['feature']}")
    if len(null_only) > 10:
        print(f"     ... and {len(null_only) - 10} more")

if constant:
    print(f"\n  ⚠️  CONSTANT FEATURES ({len(constant)}):")
    for f in constant[:10]:
        print(f"     - {f['feature']}")
    if len(constant) > 10:
        print(f"     ... and {len(constant) - 10} more")

if other:
    print(f"\n  🔍 FEATURES WITH VARIANCE (should be in model):")
    for f in other[:20]:
        print(f"     - {f['feature']} (distinct: {f.get('distinct_count', 'N/A')})")
    if len(other) > 20:
        print(f"     ... and {len(other) - 20} more")
    print(f"\n  ⚠️  These {len(other)} features have variance but were still excluded!")

print("\n" + "="*70)
print(f"Total Missing: {len(missing_features)}")
print(f"Analyzed: {len(feature_analysis)}")
print(f"NULL/Constant: {len(null_only) + len(constant) + len(zero_var)}")
print(f"Valid but Excluded: {len(other)}")
print("="*70)









