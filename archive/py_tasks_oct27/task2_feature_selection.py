#!/usr/bin/env python3
"""
TASK 2: Feature Selection
From MASTER_WORK_LIST - Reduce to optimal 100-120 features
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("TASK 2: FEATURE SELECTION")
print("="*80)

# Load cleaned dataset
df = pd.read_csv('CLEANED_TRAINING_DATA.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"\nCleaned dataset: {len(df)} rows × {len(df.columns)} columns")
print(f"Features to select from: {len(df.columns) - 1}")

# Separate features from target and date
feature_cols = [c for c in df.columns if c != 'date' and not c.startswith('target_')]
target_cols = [c for c in df.columns if c.startswith('target_')]

print(f"Feature columns: {len(feature_cols)}")
print(f"Target columns: {len(target_cols)}")

# Use target_1w as primary target for selection
primary_target = 'target_1w'
print(f"Primary target: {primary_target}")

# 2.1: Calculate correlation matrix
print("\n2.1: Calculating correlation matrix...")
print("-"*80)

# Get numeric features only
X = df[feature_cols].copy()
y = df[primary_target].copy()

# Remove NaN/Inf
X = X.replace([np.inf, -np.inf], np.nan)

# Fill NaN with 0 for correlation calculation only
X_filled = X.fillna(0)
y_filled = y.fillna(0)

# Calculate correlation matrix
corr_matrix = X_filled.corr()
print(f"  ✅ Correlation matrix calculated: {corr_matrix.shape}")

# 2.2: Remove highly correlated pairs (>0.95)
print("\n2.2: Removing highly correlated feature pairs (>0.95)...")
print("-"*80)

# Find highly correlated pairs
high_corr_pairs = []
removed_features = set()

for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if abs(corr_matrix.iloc[i, j]) > 0.95:
            feat1 = corr_matrix.columns[i]
            feat2 = corr_matrix.columns[j]
            corr_val = corr_matrix.iloc[i, j]
            
            # Calculate correlation with target for both
            corr_target1 = abs(X_filled[feat1].corr(y_filled))
            corr_target2 = abs(X_filled[feat2].corr(y_filled))
            
            # Keep the one with higher target correlation
            if corr_target1 >= corr_target2:
                to_remove = feat2
                to_keep = feat1
            else:
                to_remove = feat1
                to_keep = feat2
            
            if to_remove not in removed_features:
                high_corr_pairs.append({
                    'removed': to_remove,
                    'kept': to_keep,
                    'correlation': corr_val,
                    'reason': f'Corr={corr_val:.3f} with {to_keep}'
                })
                removed_features.add(to_remove)
                print(f"  ❌ Removing {to_remove[:40]:40} (corr={corr_val:.3f} with {to_keep[:20]})")

print(f"  Removed {len(removed_features)} highly correlated features")

# Update feature list
feature_cols = [f for f in feature_cols if f not in removed_features]
print(f"  Remaining features: {len(feature_cols)}")

# 2.3: Calculate feature importance metrics
print("\n2.3: Calculating feature importance metrics...")
print("-"*80)

importance_scores = {}

for feat in feature_cols:
    # Variance
    variance = X_filled[feat].var()
    
    # Correlation with target
    target_corr = abs(X_filled[feat].corr(y_filled))
    
    # Unique values ratio
    uniqueness = X_filled[feat].nunique() / len(X_filled)
    
    # Coverage (non-zero %)
    if X[feat].dtype in [np.float64, np.int64]:
        coverage = (X[feat] != 0).sum() / len(X)
    else:
        coverage = X[feat].notna().sum() / len(X)
    
    # Combined score
    # Normalize each metric to 0-1 range
    importance_scores[feat] = {
        'variance': variance,
        'target_corr': target_corr,
        'uniqueness': uniqueness,
        'coverage': coverage
    }

print(f"  ✅ Calculated importance for {len(importance_scores)} features")

# Normalize scores
max_variance = max(s['variance'] for s in importance_scores.values())
for feat in importance_scores:
    norm_variance = importance_scores[feat]['variance'] / (max_variance + 1e-8)
    norm_target_corr = importance_scores[feat]['target_corr']  # Already 0-1
    norm_uniqueness = importance_scores[feat]['uniqueness']  # Already 0-1
    norm_coverage = importance_scores[feat]['coverage']  # Already 0-1
    
    # Weighted combined score
    combined = (
        norm_variance * 0.2 +
        norm_target_corr * 0.4 +
        norm_uniqueness * 0.2 +
        norm_coverage * 0.2
    )
    importance_scores[feat]['combined_score'] = combined

# 2.4: Rank features
print("\n2.4: Ranking features by importance...")
print("-"*80)

ranked_features = sorted(
    importance_scores.items(),
    key=lambda x: x[1]['combined_score'],
    reverse=True
)

print(f"  Top 10 features:")
for i, (feat, scores) in enumerate(ranked_features[:10], 1):
    print(f"  {i:2}. {feat[:45]:45} Score: {scores['combined_score']:.4f}")

# 2.5: Select top 100-120 features
print("\n2.5: Selecting top features...")
print("-"*80)

# Target: 110 features (middle of 100-120 range)
target_count = 110

# Ensure we keep critical features
critical_features = []

# All price features
critical_features.extend([f for f in feature_cols if 'price' in f.lower()])

# All targets (keep for dataset, won't use in training)
critical_features.extend(target_cols)

# Key currency features
critical_features.extend([f for f in feature_cols if any(x in f.lower() for x in ['fx_usd_brl', 'fx_usd_cny', 'fx_usd_ars', 'dxy_level'])])

# Remove duplicates
critical_features = list(set(critical_features))

print(f"  Critical features (must keep): {len([f for f in critical_features if f in feature_cols])}")

# Select top features, ensuring critical ones are included
selected_features = []
for feat, scores in ranked_features:
    if feat in critical_features or len(selected_features) < target_count:
        selected_features.append(feat)
    
    if len(selected_features) >= target_count and all(cf in selected_features for cf in critical_features if cf in feature_cols):
        break

print(f"  ✅ Selected {len(selected_features)} features")

# 2.6: Verify selected features
print("\n2.6: Verifying selected features include key categories...")
print("-"*80)

categories = {
    'Price': [f for f in selected_features if 'price' in f.lower()],
    'Currency/FX': [f for f in selected_features if any(x in f.lower() for x in ['fx', 'dxy', 'currency'])],
    'Correlations': [f for f in selected_features if 'corr' in f.lower()],
    'Weather': [f for f in selected_features if any(x in f.lower() for x in ['weather', 'temp', 'precip', 'brazil'])],
    'Sentiment': [f for f in selected_features if 'sentiment' in f.lower()],
    'Technical': [f for f in selected_features if any(x in f.lower() for x in ['return', 'ma_', 'volatility', 'momentum'])],
    'Seasonal': [f for f in selected_features if any(x in f.lower() for x in ['seasonal', 'month', 'quarter'])],
}

for category, features in categories.items():
    if features:
        print(f"  ✅ {category:15} {len(features):3d} features")

# 2.7: Save feature selection report
print("\n2.7: Saving feature selection report...")
print("-"*80)

report_lines = []
report_lines.append("# TASK 2 FEATURE SELECTION REPORT")
report_lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

report_lines.append(f"\n## Summary")
report_lines.append(f"\n- Input features: {len(feature_cols) + len(removed_features)}")
report_lines.append(f"- Removed (high correlation): {len(removed_features)}")
report_lines.append(f"- Features ranked: {len(feature_cols)}")
report_lines.append(f"- Selected features: {len(selected_features)}")

report_lines.append(f"\n## Highly Correlated Features Removed")
report_lines.append(f"\nTotal: {len(high_corr_pairs)}")
for pair in high_corr_pairs[:20]:
    report_lines.append(f"\n- `{pair['removed']}`: {pair['reason']}")
if len(high_corr_pairs) > 20:
    report_lines.append(f"\n... and {len(high_corr_pairs) - 20} more")

report_lines.append(f"\n## Top 20 Selected Features")
for i, (feat, scores) in enumerate(ranked_features[:20], 1):
    if feat in selected_features:
        report_lines.append(f"\n{i}. `{feat}` - Score: {scores['combined_score']:.4f}")

report_lines.append(f"\n## Selected Features by Category")
for category, features in categories.items():
    if features:
        report_lines.append(f"\n### {category} ({len(features)} features)")
        for f in features[:10]:
            report_lines.append(f"- `{f}`")
        if len(features) > 10:
            report_lines.append(f"- ... and {len(features) - 10} more")

with open('TASK2_FEATURE_SELECTION_REPORT.md', 'w') as f:
    f.write('\n'.join(report_lines))

print(f"  ✅ Saved to: TASK2_FEATURE_SELECTION_REPORT.md")

# 2.8: Save selected feature list
print("\n2.8: Saving selected feature list...")
print("-"*80)

with open('SELECTED_FEATURES.txt', 'w') as f:
    f.write('\n'.join(selected_features))

print(f"  ✅ Saved to: SELECTED_FEATURES.txt")

# 2.9: Create dataset with selected features
print("\n2.9: Creating dataset with selected features...")
print("-"*80)

# Include date and targets
final_columns = ['date'] + selected_features + target_cols
df_final = df[final_columns].copy()

df_final.to_csv('FINAL_FEATURES_DATASET.csv', index=False)

print(f"  ✅ Saved to: FINAL_FEATURES_DATASET.csv")
print(f"  Final shape: {len(df_final)} rows × {len(df_final.columns)} columns")

# Calculate feature/sample ratio
feature_sample_ratio = len(selected_features) / len(df_final)

# Summary
print("\n" + "="*80)
print("TASK 2 COMPLETE ✅")
print("="*80)

print(f"\n📊 Summary:")
print(f"  Initial features: {len(feature_cols) + len(removed_features)}")
print(f"  Removed (correlation): {len(removed_features)}")
print(f"  Selected features: {len(selected_features)}")
print(f"  Target variables: {len(target_cols)}")
print(f"  Feature/Sample ratio: {feature_sample_ratio:.3f} (target: <0.1)")

if feature_sample_ratio < 0.1:
    print(f"  ✅ Ratio is good for ML!")
else:
    print(f"  ⚠️ Ratio still high, consider reducing further")

print(f"\n📁 Files created:")
print(f"  • FINAL_FEATURES_DATASET.csv")
print(f"  • SELECTED_FEATURES.txt")
print(f"  • TASK2_FEATURE_SELECTION_REPORT.md")

print(f"\n✅ Ready for TASK 3: Handle Duplicates")

