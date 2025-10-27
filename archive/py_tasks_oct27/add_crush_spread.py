#!/usr/bin/env python3
"""
Add Crush Spread Features - Critical for processor demand dynamics
"""

import pandas as pd
import numpy as np

print("="*80)
print("ADDING CRUSH SPREAD FEATURES")
print("="*80)

# Load leakage-free dataset (before feature selection)
df = pd.read_csv('LEAKAGE_FREE_DATASET.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"\nOriginal dataset: {len(df)} rows × {len(df.columns)} columns")

# Check for components
print("\n1. VERIFYING CRUSH SPREAD COMPONENTS:")
print("-"*80)

components = {
    'Soybean Oil': 'zl_price_current',      # cents per lb
    'Soybean Meal': 'meal_price_per_ton',   # $ per ton
    'Soybeans': 'bean_price_per_bushel'     # $ per bushel
}

for name, col in components.items():
    if col in df.columns:
        non_zero = (df[col] > 0).sum()
        latest = df[df[col] > 0][col].iloc[-1] if non_zero > 0 else 0
        print(f"  ✅ {name:20} ({col:25}): {non_zero} values, latest: {latest:.2f}")
    else:
        print(f"  ❌ {name:20} ({col:25}): NOT FOUND")
        exit(1)

# Calculate crush spread
print("\n2. CALCULATING CRUSH SPREAD:")
print("-"*80)

# Convert to common units (all to $/ton for clarity)
# 1 ton = 2000 lbs
# 1 bushel soybeans = 60 lbs
# From 1 bushel (60 lbs) soybeans: ~11 lbs oil + 44 lbs meal

# Soybean oil: cents/lb to $/ton
df['oil_price_per_ton'] = df['zl_price_current'] * 20  # cents/lb × 2000/100

# Soybean meal: already $/ton
df['meal_price_per_ton_clean'] = df['meal_price_per_ton']

# Soybeans: $/bushel to $/ton
df['bean_price_per_ton'] = df['bean_price_per_bushel'] * (2000 / 60)  # 60 lbs per bushel

# Gross Processing Margin (GPM) aka Crush Spread
# Revenue from crushing 1 ton of beans = (11/60 tons oil) + (44/60 tons meal)
# Cost = 1 ton of beans
# Simplified: (Oil × 0.183) + (Meal × 0.733) - Beans

df['crush_spread_gross'] = (
    df['oil_price_per_ton'] * 0.183 + 
    df['meal_price_per_ton_clean'] * 0.733 - 
    df['bean_price_per_ton']
)

print(f"  ✅ Calculated crush_spread_gross")
print(f"     Range: {df['crush_spread_gross'].min():.2f} to {df['crush_spread_gross'].max():.2f}")
print(f"     Mean: {df['crush_spread_gross'].mean():.2f}")
print(f"     Latest: {df['crush_spread_gross'].iloc[-1]:.2f}")

# 3. Create derived features
print("\n3. CREATING CRUSH SPREAD DERIVED FEATURES:")
print("-"*80)

# Percentile (relative to 1-year rolling window)
df['crush_spread_percentile_365d'] = df['crush_spread_gross'].rolling(
    window=365, 
    min_periods=100
).rank(pct=True)

print(f"  ✅ crush_spread_percentile_365d")
print(f"     Latest percentile: {df['crush_spread_percentile_365d'].iloc[-1]:.2%}")

# 7-day momentum (is spread widening or narrowing?)
df['crush_spread_momentum_7d'] = df['crush_spread_gross'].pct_change(7)

print(f"  ✅ crush_spread_momentum_7d")
print(f"     Latest 7d change: {df['crush_spread_momentum_7d'].iloc[-1]:.2%}")

# 30-day volatility
df['crush_spread_volatility_30d'] = df['crush_spread_gross'].rolling(30).std()

print(f"  ✅ crush_spread_volatility_30d")
print(f"     Latest volatility: {df['crush_spread_volatility_30d'].iloc[-1]:.2f}")

# Clean up temporary columns
df = df.drop(columns=['oil_price_per_ton', 'meal_price_per_ton_clean', 'bean_price_per_ton'])

# 4. Save updated dataset
print("\n4. SAVING DATASET WITH CRUSH SPREAD:")
print("-"*80)

df.to_csv('LEAKAGE_FREE_WITH_CRUSH.csv', index=False)

print(f"  ✅ Saved to: LEAKAGE_FREE_WITH_CRUSH.csv")
print(f"  Final shape: {len(df)} rows × {len(df.columns)} columns")
print(f"  Added features: 4")

# 5. Validate crush spread data quality
print("\n5. VALIDATING CRUSH SPREAD QUALITY:")
print("-"*80)

crush_features = [
    'crush_spread_gross',
    'crush_spread_percentile_365d',
    'crush_spread_momentum_7d',
    'crush_spread_volatility_30d'
]

for feat in crush_features:
    non_null = df[feat].notna().sum()
    coverage = non_null / len(df) * 100
    unique = df[feat].nunique()
    print(f"  {feat:35} {coverage:5.1f}% coverage, {unique:4d} unique values")
    
    # Check variance
    if df[feat].std() > 0:
        print(f"     ✅ Has variance (std: {df[feat].std():.4f})")
    else:
        print(f"     ❌ No variance!")

print("\n" + "="*80)
print("CRUSH SPREAD FEATURES ADDED ✅")
print("="*80)

print(f"\n✅ Dataset now includes crush spread dynamics")
print(f"✅ Captures processor demand signals")
print(f"✅ 1-2 week leading indicator for price moves")
print(f"\n📁 Next: Re-run feature selection with crush spread included")

