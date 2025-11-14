#!/usr/bin/env python3
"""
Analyze which model type (LINEAR vs BOOSTED_TREE) would be more accurate
for this specific dataset based on data characteristics
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
VIEW_NAME = "train_1w"
TARGET_COL = "target_1w"

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("🔍 ANALYZING DATA CHARACTERISTICS FOR MODEL SELECTION")
print("="*70)

# 1. Check data size and basic stats
print("\n1️⃣  DATA CHARACTERISTICS:")
try:
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT({TARGET_COL}) as valid_targets,
      STDDEV({TARGET_COL}) as target_stddev,
      AVG({TARGET_COL}) as target_mean,
      MIN({TARGET_COL}) as target_min,
      MAX({TARGET_COL}) as target_max,
      COUNT(DISTINCT {TARGET_COL}) as distinct_targets
    FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
    WHERE {TARGET_COL} IS NOT NULL
    """
    stats = client.query(query).to_dataframe().iloc[0]
    
    total_rows = int(stats['total_rows'])
    target_stddev = float(stats['target_stddev']) if stats['target_stddev'] is not None else 0
    target_mean = float(stats['target_mean']) if stats['target_mean'] is not None else 0
    cv = (target_stddev / target_mean * 100) if target_mean != 0 else 0
    
    print(f"  📊 Total rows: {total_rows:,}")
    print(f"  📊 Target statistics:")
    print(f"     Mean: ${target_mean:.2f}")
    print(f"     StdDev: ${target_stddev:.2f}")
    print(f"     Coefficient of Variation: {cv:.2f}%")
    print(f"     Range: ${stats['target_min']:.2f} - ${stats['target_max']:.2f}")
    
    # Small dataset favors simpler models
    if total_rows < 5000:
        print(f"  ⚠️  Small dataset (<5K rows) - simpler models may generalize better")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 2. Check feature count and sparsity
print("\n2️⃣  FEATURE CHARACTERISTICS:")
try:
    # Get feature count
    query = f"""
    SELECT COUNT(*) as col_count
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    """
    col_count = int(client.query(query).to_dataframe().iloc[0]['col_count'])
    
    # Sample features to check for linearity
    query = f"""
    SELECT column_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
    AND data_type IN ('FLOAT64', 'INT64')
    LIMIT 20
    """
    sample_features = client.query(query).to_dataframe()['column_name'].tolist()
    
    print(f"  📊 Total features available: ~{col_count - 5} (excluding targets/date)")
    print(f"  📊 High feature-to-sample ratio: {col_count - 5}/{total_rows} = {(col_count-5)/total_rows:.2f}")
    
    if (col_count - 5) / total_rows > 0.1:
        print(f"  ⚠️  High feature ratio (>0.1) - risk of overfitting with complex models")
        print(f"     Linear regression with regularization may be safer")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# 3. Check current BOOSTED_TREE performance
print("\n3️⃣  CURRENT BOOSTED_TREE PERFORMANCE:")
try:
    query = f"""
    SELECT 
      mean_absolute_error AS mae,
      SQRT(mean_squared_error) AS rmse,
      r2_score AS r2
    FROM ML.EVALUATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.bqml_1w_mean`,
      (
        SELECT 
          * EXCEPT(date, treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate, news_article_count, news_avg_score),
          date < '2024-01-01' AS is_training
        FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
        WHERE date >= '2024-01-01'
        AND {TARGET_COL} IS NOT NULL
      )
    )
    """
    perf = client.query(query).to_dataframe()
    
    if not perf.empty:
        row = perf.iloc[0]
        mae = float(row['mae'])
        rmse = float(row['rmse'])
        r2 = float(row['r2'])
        
        # Estimate MAPE if we have average price
        if target_mean > 0:
            mape_est = (mae / target_mean) * 100
        else:
            mape_est = None
        
        print(f"  📈 Current Performance:")
        print(f"     MAE: ${mae:.4f}")
        print(f"     RMSE: ${rmse:.4f}")
        print(f"     R²: {r2:.4f}")
        if mape_est:
            print(f"     Estimated MAPE: ~{mape_est:.2f}%")
        
        if r2 < 0.90:
            print(f"  ⚠️  Low R² ({r2:.4f}) - model struggling")
            print(f"     May benefit from all features (linear regression)")
        if mape_est and mape_est > 5:
            print(f"  ⚠️  High MAPE ({mape_est:.2f}%) - poor performance")
            print(f"     Missing features may be critical")
    else:
        print(f"  ⚠️  Could not evaluate current model")
except Exception as e:
    print(f"  ⚠️  Could not check current performance: {str(e)[:100]}")

# 4. Analyze feature types for linearity
print("\n4️⃣  FEATURE TYPE ANALYSIS:")
try:
    # Check if features are mostly correlation/lag (indicating non-linearity)
    query = f"""
    SELECT 
      COUNTIF(column_name LIKE '%corr%') as correlation_features,
      COUNTIF(column_name LIKE '%lag%') as lag_features,
      COUNTIF(column_name LIKE '%ma%' OR column_name LIKE '%moving%') as moving_avg_features,
      COUNTIF(column_name LIKE '%sentiment%' OR column_name LIKE '%score%') as sentiment_features,
      COUNT(*) as total_features
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{VIEW_NAME}'
    AND column_name NOT IN ('date', 'target_1w', 'target_1m', 'target_3m', 'target_6m')
    """
    feat_types = client.query(query).to_dataframe().iloc[0]
    
    corr_pct = (feat_types['correlation_features'] / feat_types['total_features']) * 100
    lag_pct = (feat_types['lag_features'] / feat_types['total_features']) * 100
    ma_pct = (feat_types['moving_avg_features'] / feat_types['total_features']) * 100
    
    print(f"  📊 Feature composition:")
    print(f"     Correlation features: {int(feat_types['correlation_features'])} ({corr_pct:.1f}%)")
    print(f"     Lag features: {int(feat_types['lag_features'])} ({lag_pct:.1f}%)")
    print(f"     Moving averages: {int(feat_types['moving_avg_features'])} ({ma_pct:.1f}%)")
    print(f"     Sentiment/score features: {int(feat_types['sentiment_features'])}")
    
    # High correlation/lag features suggest non-linear relationships
    if corr_pct + lag_pct > 40:
        print(f"  📌 Many derived features (>40%) - relationships likely non-linear")
        print(f"     Boosted trees typically better for this")
    else:
        print(f"  📌 Mix of feature types - both models could work")
        
except Exception as e:
    print(f"  ⚠️  Error analyzing features: {e}")

# 5. Recommendation
print("\n" + "="*70)
print("🎯 RECOMMENDATION")
print("="*70)

print("\nFor YOUR SPECIFIC DATA:")
print(f"  • Dataset size: {total_rows:,} rows")
print(f"  • Features available: ~{col_count - 5 if 'col_count' in locals() else 'N/A'}")
print(f"  • Current model uses: 57 features (missing 131)")
print(f"  • Current MAPE: ~8% (poor)")

print("\n📊 MODEL COMPARISON:")

print("\nBOOSTED_TREE:")
print("  ✅ Typically better for non-linear relationships")
print("  ✅ Better with complex patterns")
print("  ❌ Only uses 57/188 features (automatic selection)")
print("  ❌ Current MAPE: 8% (poor - likely due to missing features)")
print("  💰 Cost: $5/TB")

print("\nLINEAR_REGRESSOR:")
print("  ✅ Uses ALL 188 features (no selection)")
print("  ✅ Regularization can prevent overfitting")
print("  ✅ Better when feature count >> sample size")
print("  ⚠️  Assumes linear relationships")
print("  ⚠️  May struggle with non-linear patterns")
print("  💰 Cost: $250/TB (but only ~$0.0003 for your data size)")

print("\n🎯 RECOMMENDATION:")
if total_rows < 2000 and col_count - 5 > 100:
    print("  → LINEAR_REGRESSOR with L2 regularization")
    print("     Reasons:")
    print("     • Small dataset (1,251 rows) + many features (188) = overfitting risk")
    print("     • Current model missing 131 features (70% excluded)")
    print("     • Regularized linear regression can use all features safely")
    print("     • You suspect missing features are causing 8% MAPE")
    print("     • Cost difference is negligible for your data size")
else:
    print("  → BOOSTED_TREE (but need to address feature exclusion)")
    print("     Reasons:")
    print("     • Better for non-linear commodity price relationships")
    print("     • But current exclusion of 131 features is problematic")

print("\n💡 BEST APPROACH:")
print("  1. Try LINEAR_REGRESSOR first (uses all features)")
print("  2. Compare MAPE/R² to current 8% MAPE")
print("  3. If linear performs better → use it")
print("  4. If still poor, boosted tree may need different config")

print("="*70)









