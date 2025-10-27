#!/usr/bin/env python3
"""Quick pre-training dataset audit for duplicates, fake data, and errors."""

import pandas as pd
import numpy as np

print("="*80)
print("ENHANCED DATASET AUDIT - PRE-TRAINING VALIDATION")
print("="*80)

# Load dataset
df = pd.read_csv('training_dataset_final_enhanced.csv')
print(f"\n📊 Dataset: {len(df):,} rows × {len(df.columns)} columns")
print(f"   Date range: {df['date'].min()} → {df['date'].max()}")

# 1. DUPLICATES
print("\n🔍 DUPLICATE CHECK:")
exact_dupes = df.duplicated().sum()
date_dupes = df['date'].duplicated().sum()
print(f"   Exact duplicate rows: {exact_dupes}")
print(f"   Duplicate dates: {date_dupes}")

# 2. FAKE DATA (999 placeholders)
print("\n🎭 FAKE DATA DETECTION:")
fake_999 = [(col, (df[col]==999).sum()) for col in df.columns if df[col].dtype in [np.float64, np.int64] and (df[col]==999).sum() > 0]
if fake_999:
    print(f"   ⚠️  Found 999 placeholders in {len(fake_999)} columns:")
    for col, count in fake_999[:10]:
        print(f"      • {col}: {count} rows ({100*count/len(df):.1f}%)")
else:
    print(f"   ✅ No 999 placeholders")

# 3. EXCESSIVE 0.5 (mock sentiment)
print("\n🤖 MOCK SENTIMENT DETECTION:")
half_vals = [(col, (df[col]==0.5).sum()) for col in df.columns if df[col].dtype==np.float64 and (df[col]==0.5).sum() > len(df)*0.5]
if half_vals:
    print(f"   ⚠️  Excessive 0.5 values in {len(half_vals)} columns:")
    for col, count in half_vals[:10]:
        print(f"      • {col}: {count} rows ({100*count/len(df):.1f}%)")
else:
    print(f"   ✅ No excessive 0.5 patterns")

# 4. CONSTANT COLUMNS
print("\n🔒 CONSTANT COLUMNS:")
const_cols = [col for col in df.columns if col != 'date' and df[col].nunique() == 1]
if const_cols:
    print(f"   ⚠️  {len(const_cols)} constant columns:")
    for col in const_cols[:10]:
        print(f"      • {col} = {df[col].iloc[0]}")
else:
    print(f"   ✅ No constant columns")

# 5. MISSING VALUES
print("\n❓ MISSING VALUES:")
missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
if len(missing) > 0:
    print(f"   ⚠️  Missing values in {len(missing)} columns:")
    for col, count in missing.head(10).items():
        print(f"      • {col}: {count} ({100*count/len(df):.1f}%)")
else:
    print(f"   ✅ No missing values")

# 6. NEGATIVE PRICES
print("\n💰 PRICE VALIDATION:")
price_cols = ['zl_price_current', 'crude_price', 'palm_price', 'corn_price', 'wheat_price']
neg_prices = [(col, (df[col] < 0).sum()) for col in price_cols if col in df.columns and (df[col] < 0).sum() > 0]
if neg_prices:
    print(f"   ⚠️  Negative prices found:")
    for col, count in neg_prices:
        print(f"      • {col}: {count} negative values")
else:
    print(f"   ✅ All prices positive")

# SUMMARY
print("\n"+"="*80)
print("📋 FINAL VERDICT:")
issues = exact_dupes + date_dupes + len(fake_999) + len(half_vals) + len(const_cols) + len(missing) + len(neg_prices)
if issues == 0:
    print("✅ ✅ ✅ DATASET READY FOR TRAINING ✅ ✅ ✅")
else:
    print(f"⚠️  TOTAL ISSUES: {issues} - Review required")
print("="*80)




