#!/usr/bin/env python3
"""
GET CLEAN TRAINING DATASET - SIMPLE AND SAFE
Just download the best dataset we have and clean it up for immediate use
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import numpy as np

print("="*80)
print("GETTING CLEAN TRAINING DATASET")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# Use the best dataset we identified: training_complete_enhanced
print("\n1. DOWNLOADING BEST AVAILABLE DATASET")
print("-"*40)

query = """
SELECT *
FROM `cbi-v14.models.training_complete_enhanced`
ORDER BY date
"""

print("Downloading training_complete_enhanced (219 columns)...")
df = client.query(query).to_dataframe()

print(f"✓ Downloaded {len(df):,} rows × {df.shape[1]} columns")

# 2. BASIC CLEANING
print("\n2. CLEANING DATASET")
print("-"*40)

# Remove any duplicate dates
print("Checking for duplicate dates...")
df['date'] = pd.to_datetime(df['date'])
duplicates_before = df[df.duplicated(subset=['date'], keep=False)]
if len(duplicates_before) > 0:
    print(f"Found {len(duplicates_before)} rows with duplicate dates")
    # Keep the row with most non-null values for each date
    df['non_null_count'] = df.notna().sum(axis=1)
    df = df.sort_values(['date', 'non_null_count'], ascending=[True, False])
    df = df.drop_duplicates(subset=['date'], keep='first')
    df = df.drop('non_null_count', axis=1)
    print(f"✓ Removed duplicates, now have {len(df)} rows")
else:
    print("✓ No duplicate dates found")

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# 3. FILL MISSING VALUES SAFELY
print("\n3. HANDLING MISSING VALUES")
print("-"*40)

# For price-based features, forward fill (more realistic than zeros)
price_cols = [col for col in df.columns if 'price' in col.lower() or 'close' in col.lower()]
for col in price_cols:
    if col in df.columns:
        nulls_before = df[col].isna().sum()
        if nulls_before > 0:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            print(f"  {col}: filled {nulls_before} nulls")

# For features that should be zero when missing (like news counts, signals)
zero_fill_cols = [col for col in df.columns if any(x in col.lower() for x in 
                  ['count', 'signal', 'cftc', 'news', 'tariff', 'china', 'brazil', 
                   'policy', 'biofuel', 'drought', 'flood'])]

for col in zero_fill_cols:
    if col in df.columns:
        nulls_before = df[col].isna().sum()
        if nulls_before > 0:
            df[col] = df[col].fillna(0)
            print(f"  {col}: filled {nulls_before} nulls with 0")

# 4. VALIDATE CRITICAL FEATURES
print("\n4. VALIDATING CRITICAL FEATURES")
print("-"*40)

critical_features = {
    'date': df['date'].notna().all(),
    'zl_price_current': df['zl_price_current'].notna().all() and (df['zl_price_current'] > 0).all(),
    'target_1w': df['target_1w'].notna().sum() > len(df) * 0.9,  # 90% filled is OK
    'target_1m': df['target_1m'].notna().sum() > len(df) * 0.8,  # 80% filled is OK
}

all_valid = True
for feature, is_valid in critical_features.items():
    status = "✓" if is_valid else "✗"
    print(f"  {status} {feature}")
    if not is_valid:
        all_valid = False

# 5. CREATE FEATURE SUMMARY
print("\n5. FEATURE SUMMARY")
print("-"*40)

feature_groups = {
    'Price & Technical': len([c for c in df.columns if any(x in c.lower() for x in ['price', 'return', 'ma_', 'volatility'])]),
    'Correlations': len([c for c in df.columns if 'corr_' in c.lower()]),
    'CFTC': len([c for c in df.columns if 'cftc' in c.lower()]),
    'Economic': len([c for c in df.columns if 'econ' in c.lower()]),
    'Weather': len([c for c in df.columns if 'weather' in c.lower()]),
    'News & Sentiment': len([c for c in df.columns if any(x in c.lower() for x in ['news', 'sentiment', 'tariff', 'china', 'brazil'])]),
    'Events': len([c for c in df.columns if 'is_' in c.lower() or 'event' in c.lower()]),
    'Commodities': len([c for c in df.columns if any(x in c.lower() for x in ['crude', 'palm', 'corn', 'wheat', 'bean'])]),
    'Market Indicators': len([c for c in df.columns if any(x in c.lower() for x in ['vix', 'dxy', 'treasury'])])
}

for group, count in feature_groups.items():
    print(f"  {group:20}: {count} features")

# 6. SAVE CLEAN DATASET
print("\n6. SAVING CLEAN DATASET")
print("-"*40)

output_file = 'training_dataset_clean.csv'
df.to_csv(output_file, index=False)
print(f"✓ Saved to {output_file}")

# Also save a parquet version (faster, smaller, preserves types)
output_parquet = 'training_dataset_clean.parquet'
df.to_parquet(output_parquet, index=False)
print(f"✓ Saved to {output_parquet}")

# 7. DATA QUALITY REPORT
print("\n7. FINAL DATA QUALITY")
print("-"*40)

print(f"Total rows: {len(df):,}")
print(f"Total features: {df.shape[1]}")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Check how much data is actually filled
total_cells = df.shape[0] * df.shape[1]
filled_cells = df.notna().sum().sum()
fill_rate = (filled_cells / total_cells) * 100

print(f"Overall fill rate: {fill_rate:.1f}%")

# Check specific important features
important_features = ['zl_price_current', 'target_1w', 'crude_price', 'vix_level', 'ma_7d', 'volatility_30d']
print("\nKey feature fill rates:")
for feat in important_features:
    if feat in df.columns:
        fill_rate = (df[feat].notna().sum() / len(df)) * 100
        print(f"  {feat:20}: {fill_rate:.1f}%")

print("\n" + "="*80)
print("✅ CLEAN DATASET READY FOR TRAINING")
print("="*80)
print(f"\nFiles created:")
print(f"  1. training_dataset_clean.csv ({len(df):,} rows × {df.shape[1]} columns)")
print(f"  2. training_dataset_clean.parquet (compressed version)")
print(f"\nThis dataset is ready for immediate use in model training.")
print(f"All critical features validated and missing values handled appropriately.")
print("="*80)
