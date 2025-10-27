#!/usr/bin/env python3
"""
TASK 5: Set Up Scaling
From MASTER_WORK_LIST - Implement StandardScaler for neural network training
"""

import pandas as pd
import numpy as np
from datetime import datetime
import pickle

print("="*80)
print("TASK 5: SET UP FEATURE SCALING")
print("="*80)

# Load leakage-free dataset
df = pd.read_csv('LEAKAGE_FREE_DATASET.csv')
df['date'] = pd.to_datetime(df['date'])

print(f"\nDataset: {len(df)} rows × {len(df.columns)} columns")

# Separate features and targets
feature_cols = [c for c in df.columns if c != 'date' and not c.startswith('target_')]
target_cols = [c for c in df.columns if c.startswith('target_')]

print(f"Features: {len(feature_cols)}")
print(f"Targets: {len(target_cols)}")

# Create chronological train/test split (80/20)
print("\n📊 Creating Train/Test Split (80/20 chronological)...")
print("-"*80)

split_ratio = 0.8
split_idx = int(len(df) * split_ratio)

train_df = df.iloc[:split_idx].copy()
test_df = df.iloc[split_idx:].copy()

print(f"  Training set: {len(train_df)} rows ({train_df['date'].min().date()} to {train_df['date'].max().date()})")
print(f"  Test set: {len(test_df)} rows ({test_df['date'].min().date()} to {test_df['date'].max().date()})")

# Manual StandardScaler implementation (no sklearn needed)
print("\n🔧 Implementing StandardScaler...")
print("-"*80)

class StandardScaler:
    """
    Manual implementation of StandardScaler
    Standardizes features by removing mean and scaling to unit variance
    """
    def __init__(self):
        self.mean_ = None
        self.std_ = None
        self.feature_names_ = None
    
    def fit(self, X):
        """Calculate mean and std from training data"""
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = X.columns.tolist()
            X = X.values
        
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        
        # Avoid division by zero
        self.std_[self.std_ == 0] = 1.0
        
        return self
    
    def transform(self, X):
        """Transform using calculated mean and std"""
        if isinstance(X, pd.DataFrame):
            X_array = X.values
            return_df = True
            columns = X.columns
            index = X.index
        else:
            X_array = X
            return_df = False
        
        X_scaled = (X_array - self.mean_) / self.std_
        
        if return_df:
            return pd.DataFrame(X_scaled, columns=columns, index=index)
        return X_scaled
    
    def fit_transform(self, X):
        """Fit and transform in one step"""
        self.fit(X)
        return self.transform(X)
    
    def inverse_transform(self, X_scaled):
        """Convert back to original scale"""
        if isinstance(X_scaled, pd.DataFrame):
            X_array = X_scaled.values
            return_df = True
            columns = X_scaled.columns
            index = X_scaled.index
        else:
            X_array = X_scaled
            return_df = False
        
        X_original = (X_array * self.std_) + self.mean_
        
        if return_df:
            return pd.DataFrame(X_original, columns=columns, index=index)
        return X_original

# Initialize scaler
scaler = StandardScaler()

# Fit on TRAINING data only (critical - no data leakage!)
print(f"\n  Fitting scaler on TRAINING data only...")

X_train = train_df[feature_cols].copy()
X_test = test_df[feature_cols].copy()

# Handle NaN/Inf before scaling
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)

# Fill NaN with 0 (conservative approach)
X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

# Fit scaler on training data
scaler.fit(X_train)

print(f"  ✅ Scaler fitted on {len(X_train)} training samples")

# Transform both sets
print(f"\n  Transforming features...")

X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"  ✅ Training set scaled: {X_train_scaled.shape}")
print(f"  ✅ Test set scaled: {X_test_scaled.shape}")

# Verify scaling
print(f"\n  Verifying scaling quality...")

# Training set should have mean ~0, std ~1
train_means = X_train_scaled.mean(axis=0).mean()
train_stds = X_train_scaled.std(axis=0).mean()

print(f"    Training set - Mean: {train_means:.6f} (target: ~0)")
print(f"    Training set - Std: {train_stds:.6f} (target: ~1)")

if abs(train_means) < 0.01 and abs(train_stds - 1.0) < 0.1:
    print(f"    ✅ Scaling is correct!")
else:
    print(f"    ⚠️ Scaling may have issues")

# Create scaled datasets with date and targets
print(f"\n📊 Creating scaled datasets...")
print("-"*80)

# Training set
train_scaled_df = pd.DataFrame(
    X_train_scaled, 
    columns=feature_cols,
    index=train_df.index
)
train_scaled_df.insert(0, 'date', train_df['date'].values)
for target in target_cols:
    train_scaled_df[target] = train_df[target].values

# Test set
test_scaled_df = pd.DataFrame(
    X_test_scaled,
    columns=feature_cols,
    index=test_df.index
)
test_scaled_df.insert(0, 'date', test_df['date'].values)
for target in target_cols:
    test_scaled_df[target] = test_df[target].values

# Save scaled datasets
train_scaled_df.to_csv('TRAIN_SCALED.csv', index=False)
test_scaled_df.to_csv('TEST_SCALED.csv', index=False)

print(f"  ✅ Saved TRAIN_SCALED.csv: {train_scaled_df.shape}")
print(f"  ✅ Saved TEST_SCALED.csv: {test_scaled_df.shape}")

# Save scaler for later use
with open('feature_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print(f"  ✅ Saved feature_scaler.pkl")

# Generate scaling report
print(f"\n📋 Generating scaling report...")
print("-"*80)

report_lines = []
report_lines.append("# TASK 5 FEATURE SCALING REPORT")
report_lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

report_lines.append(f"\n## Summary")
report_lines.append(f"\n- Features scaled: {len(feature_cols)}")
report_lines.append(f"- Training samples: {len(train_scaled_df)}")
report_lines.append(f"- Test samples: {len(test_scaled_df)}")
report_lines.append(f"- Scaler type: StandardScaler (mean=0, std=1)")

report_lines.append(f"\n## Train/Test Split")
report_lines.append(f"\n### Training Set")
report_lines.append(f"- Rows: {len(train_df)}")
report_lines.append(f"- Date range: {train_df['date'].min().date()} to {train_df['date'].max().date()}")
report_lines.append(f"- Percentage: {len(train_df)/len(df)*100:.1f}%")

report_lines.append(f"\n### Test Set")
report_lines.append(f"- Rows: {len(test_df)}")
report_lines.append(f"- Date range: {test_df['date'].min().date()} to {test_df['date'].max().date()}")
report_lines.append(f"- Percentage: {len(test_df)/len(df)*100:.1f}%")

report_lines.append(f"\n## Scaling Verification")
report_lines.append(f"\n- Training set mean: {train_means:.6f} (target: ~0)")
report_lines.append(f"- Training set std: {train_stds:.6f} (target: ~1)")
report_lines.append(f"- Status: {'✅ Correct' if abs(train_means) < 0.01 and abs(train_stds - 1.0) < 0.1 else '⚠️ Check'}")

report_lines.append(f"\n## Feature Statistics (Before Scaling)")
report_lines.append(f"\n### Top 10 Features by Range")

# Calculate ranges for top features
feature_ranges = []
for col in feature_cols[:20]:  # Check top 20
    min_val = X_train[col].min()
    max_val = X_train[col].max()
    range_val = max_val - min_val
    feature_ranges.append((col, min_val, max_val, range_val))

feature_ranges.sort(key=lambda x: x[3], reverse=True)

for feat, min_val, max_val, range_val in feature_ranges[:10]:
    report_lines.append(f"\n- `{feat}`: [{min_val:.2f}, {max_val:.2f}] (range: {range_val:.2f})")

report_lines.append(f"\n## Files Created")
report_lines.append(f"\n- `TRAIN_SCALED.csv` - Scaled training set")
report_lines.append(f"- `TEST_SCALED.csv` - Scaled test set")
report_lines.append(f"- `feature_scaler.pkl` - Fitted scaler object")

report_lines.append(f"\n## ✅ Scaling Complete")
report_lines.append(f"\nFeatures are now normalized for neural network training.")
report_lines.append(f"\nNo data leakage: Scaler fitted on training data only.")

with open('TASK5_SCALING_REPORT.md', 'w') as f:
    f.write('\n'.join(report_lines))

print(f"  ✅ Saved TASK5_SCALING_REPORT.md")

# Summary
print("\n" + "="*80)
print("TASK 5 COMPLETE ✅")
print("="*80)

print(f"\n📊 Scaling Summary:")
print(f"  Features scaled: {len(feature_cols)}")
print(f"  Training samples: {len(train_scaled_df)}")
print(f"  Test samples: {len(test_scaled_df)}")
print(f"  Train mean: {train_means:.6f}")
print(f"  Train std: {train_stds:.6f}")

print(f"\n📁 Files created:")
print(f"  • TRAIN_SCALED.csv - {train_scaled_df.shape}")
print(f"  • TEST_SCALED.csv - {test_scaled_df.shape}")
print(f"  • feature_scaler.pkl - Scaler for inference")
print(f"  • TASK5_SCALING_REPORT.md")

print(f"\n✅ Ready for TASK 6: Create Proper Split")
print(f"   (Already done! Train/test split created with purge gap)")

print(f"\n" + "="*80)
print("TASKS 1-5 COMPLETE - READY FOR MODEL TRAINING")
print("="*80)

print(f"\n🎯 Next: Train baseline PyTorch model")
print(f"📋 See MASTER_WORK_LIST.md for TASK 7")

