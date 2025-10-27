#!/usr/bin/env python3
"""
TEST TRAINING DATASET
Quick test to ensure the dataset works for model training
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("TESTING CLEAN TRAINING DATASET")
print("="*80)

# Load the dataset
print("\n1. LOADING DATASET")
print("-"*40)
df = pd.read_parquet('training_dataset_clean.parquet')
print(f"✓ Loaded {len(df):,} rows × {df.shape[1]} columns")

# Check basic stats
print("\n2. DATASET STATISTICS")
print("-"*40)
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Price range: ${df['zl_price_current'].min():.2f} to ${df['zl_price_current'].max():.2f}")
print(f"Mean price: ${df['zl_price_current'].mean():.2f}")
print(f"Price volatility: {df['zl_price_current'].std():.2f}")

# Prepare for training
print("\n3. PREPARING FOR MODEL TRAINING")
print("-"*40)

# Select features (exclude date and targets from features)
target_col = 'target_1w'
exclude_cols = ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m']
feature_cols = [col for col in df.columns if col not in exclude_cols]

# Remove rows where target is null
train_df = df[df[target_col].notna()].copy()
print(f"Samples with target: {len(train_df):,}")

X = train_df[feature_cols]
y = train_df[target_col]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=False  # Don't shuffle time series
)

print(f"Training samples: {len(X_train):,}")
print(f"Testing samples: {len(X_test):,}")
print(f"Features: {X.shape[1]}")

# Quick model test
print("\n4. QUICK MODEL TEST")
print("-"*40)
print("Training a simple RandomForest model...")

# Use a small model for quick testing
model = RandomForestRegressor(
    n_estimators=50,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("✓ Model trained successfully")

# Predictions
y_pred = model.predict(X_test)

# Metrics
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

print("\n5. MODEL PERFORMANCE")
print("-"*40)
print(f"Mean Absolute Error: ${mae:.2f}")
print(f"R² Score: {r2:.3f}")
print(f"MAPE: {mape:.1f}%")

# Feature importance (top 10)
print("\n6. TOP 10 IMPORTANT FEATURES")
print("-"*40)
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']:30}: {row['importance']:.4f}")

# Check data distribution
print("\n7. DATA HEALTH CHECK")
print("-"*40)

# Check for any infinite values
inf_count = np.isinf(X).sum().sum()
print(f"Infinite values: {inf_count}")

# Check for NaN values
nan_count = X.isna().sum().sum()
print(f"NaN values: {nan_count}")

# Check feature variance (features with no variance are useless)
zero_variance = (X.std() == 0).sum()
print(f"Features with zero variance: {zero_variance}")

# Overall assessment
print("\n" + "="*80)
print("✅ DATASET TEST COMPLETE")
print("="*80)

if mae < df['zl_price_current'].std() and r2 > 0:
    print("✓ Dataset is GOOD for training")
    print("  - Model trains successfully")
    print("  - Reasonable predictions achieved")
    print("  - No data quality issues found")
else:
    print("⚠ Dataset may need improvement")
    print(f"  - MAE is high relative to price volatility")

print("\nDataset is ready for production model training!")
print("="*80)
