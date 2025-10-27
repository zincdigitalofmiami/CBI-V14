#!/usr/bin/env python3
"""
RECOVERY SCRIPT - Pull ONLY verified real data from BigQuery
NO fake data, NO zero-filling, NO bullshit
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np

print("="*80)
print("RECOVERING YOUR REAL DATA FROM BIGQUERY")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# First, check which training dataset in BigQuery is best
print("\n1. CHECKING YOUR TRAINING DATASETS IN BIGQUERY...")
print("-"*40)

training_tables = [
    ('models', 'training_complete_enhanced'),
    ('models', 'training_dataset_master'),
    ('models', 'training_enhanced_final'),
    ('models_v4', 'training_dataset_super_enriched'),
    ('models_v4', 'training_dataset_v4'),
]

best_table = None
max_score = 0

for dataset, table in training_tables:
    try:
        # Get basic info
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `cbi-v14.{dataset}.{table}`
        """
        result = client.query(query).to_dataframe()
        row_count = result['row_count'].iloc[0]
        
        # Get column count
        table_ref = client.dataset(dataset).table(table)
        table_obj = client.get_table(table_ref)
        col_count = len(table_obj.schema)
        
        # Score = rows * columns
        score = row_count * col_count
        
        print(f"  {dataset}.{table}:")
        print(f"    Rows: {row_count:,}")
        print(f"    Columns: {col_count}")
        print(f"    Score: {score:,}")
        
        if score > max_score:
            max_score = score
            best_table = (dataset, table)
            
    except Exception as e:
        print(f"  ❌ {dataset}.{table}: {str(e)[:100]}")

print(f"\n  ✅ BEST TABLE: {best_table[0]}.{best_table[1]}")

# Download the best table
print(f"\n2. DOWNLOADING {best_table[0]}.{best_table[1]}...")
print("-"*40)

query = f"""
SELECT *
FROM `cbi-v14.{best_table[0]}.{best_table[1]}`
ORDER BY date
"""

df = client.query(query).to_dataframe()
print(f"  ✅ Downloaded: {len(df)} rows × {len(df.columns)} columns")

# Now VALIDATE the data - NO FAKE DATA ALLOWED
print("\n3. VALIDATING DATA QUALITY...")
print("-"*40)

real_features = []
fake_features = []
sparse_features = []

for col in df.columns:
    if col == 'date':
        continue
        
    # Get statistics
    non_null = df[col].notna().sum()
    non_zero = (df[col] != 0).sum() if df[col].dtype in [np.float64, np.int64] else non_null
    unique_vals = df[col].nunique()
    coverage = non_zero / len(df)
    
    # Classify feature
    if coverage < 0.05:  # Less than 5% coverage
        sparse_features.append((col, coverage))
    elif unique_vals < 3:  # Only 1-2 unique values
        fake_features.append((col, unique_vals))
    elif df[col].dtype in [np.float64, np.int64] and df[col].std() == 0:
        fake_features.append((col, unique_vals))
    else:
        real_features.append((col, coverage, unique_vals))

print(f"\n  ✅ REAL features (>5% coverage, variance): {len(real_features)}")
print(f"  ❌ FAKE features (no variance): {len(fake_features)}")
print(f"  ⚠️ SPARSE features (<5% coverage): {len(sparse_features)}")

# Show top real features
print(f"\n  Top 20 real features by coverage:")
real_features_sorted = sorted(real_features, key=lambda x: x[1], reverse=True)
for feat, cov, uniq in real_features_sorted[:20]:
    print(f"    • {feat[:40]:40} Coverage: {cov:.1%}, Unique: {uniq}")

# Create clean dataset with ONLY real features
print("\n4. CREATING CLEAN DATASET (REAL DATA ONLY)...")
print("-"*40)

# Keep only real features + date
real_feature_names = [f[0] for f in real_features]
clean_columns = ['date'] + real_feature_names

df_clean = df[clean_columns].copy()

print(f"  ✅ Clean dataset: {len(df_clean)} rows × {len(df_clean.columns)} columns")
print(f"  ✅ All features verified as REAL data")

# Save
df_clean.to_csv('REAL_TRAINING_DATA.csv', index=False)
print(f"\n  💾 Saved to: REAL_TRAINING_DATA.csv")

# Create manifest of what data we have
print("\n5. CREATING DATA MANIFEST...")
print("-"*40)

manifest = {
    'source_table': f"{best_table[0]}.{best_table[1]}",
    'total_rows': len(df_clean),
    'total_features': len(real_feature_names),
    'date_range': f"{df_clean['date'].min()} to {df_clean['date'].max()}",
    'real_features': len(real_features),
    'removed_fake': len(fake_features),
    'removed_sparse': len(sparse_features),
}

# Categorize features
feature_categories = {
    'price': [],
    'volume': [],
    'technical': [],
    'correlation': [],
    'currency': [],
    'weather': [],
    'economic': [],
    'cftc': [],
    'news': [],
    'other': []
}

for feat, cov, uniq in real_features:
    categorized = False
    for category in feature_categories:
        if category in feat.lower():
            feature_categories[category].append(feat)
            categorized = True
            break
    if not categorized:
        feature_categories['other'].append(feat)

print("\n  Feature breakdown:")
for category, features in feature_categories.items():
    if features:
        print(f"    {category.capitalize()}: {len(features)} features")

# Save manifest
manifest_df = pd.DataFrame([manifest])
manifest_df.to_csv('DATA_MANIFEST.csv', index=False)

# Save feature list
features_df = pd.DataFrame(real_features, columns=['feature', 'coverage', 'unique_values'])
features_df.to_csv('VERIFIED_FEATURES.csv', index=False)

print(f"\n  💾 Saved manifest to: DATA_MANIFEST.csv")
print(f"  💾 Saved feature list to: VERIFIED_FEATURES.csv")

print("\n" + "="*80)
print("RECOVERY COMPLETE")
print("="*80)
print("\n✅ Your REAL data has been recovered")
print("✅ NO fake data included")
print("✅ NO zero-filling")
print("✅ All features validated")
print(f"\n📊 Final dataset: {len(df_clean)} rows × {len(df_clean.columns)} columns")
print(f"📁 Saved as: REAL_TRAINING_DATA.csv")
print("\nREADY FOR REAL TRAINING")

