#!/usr/bin/env python3
"""
Systematic Diagnosis of Model Performance Issues
Following the diagnostic framework provided
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pickle

print("="*80)
print("SYSTEMATIC MODEL DIAGNOSIS")
print("="*80)

# Load data
# DISABLED: train_df = pd.read_csv('TRAIN_ENHANCED.csv')  # DELETED - contained fake data
# Use REAL_TRAINING_DATA.csv instead
# DISABLED: test_df = pd.read_csv('TEST_ENHANCED.csv')  # DELETED - contained fake data

with open('ENHANCED_FEATURES.txt', 'r') as f:
    feature_names = [line.strip() for line in f.readlines()]

X_train = train_df[feature_names].values
y_train = train_df['target_1w'].values
X_test = test_df[feature_names].values
y_test = test_df['target_1w'].values

# Get current prices for directional accuracy
# Unscale zl_price_current
with open('scaler_enhanced.pkl', 'rb') as f:
    scaler = pickle.load(f)

zl_price_idx = feature_names.index('zl_price_current')
train_current_price = X_train[:, zl_price_idx] * scaler['std']['zl_price_current'] + scaler['mean']['zl_price_current']
test_current_price = X_test[:, zl_price_idx] * scaler['std']['zl_price_current'] + scaler['mean']['zl_price_current']

X_train = np.nan_to_num(X_train, 0)
X_test = np.nan_to_num(X_test, 0)

print(f"\nData loaded:")
print(f"  Train: {X_train.shape}")
print(f"  Test: {X_test.shape}")
print(f"  Features: {len(feature_names)}")

# 1. FIX DIRECTIONAL ACCURACY CALCULATION
print("\n" + "="*80)
print("1. CORRECT DIRECTIONAL ACCURACY CALCULATION")
print("="*80)

def directional_accuracy_correct(current_prices, future_prices, predictions):
    """
    Calculate if prediction correctly captured price movement direction
    """
    actual_direction = future_prices > current_prices  # Did price go up?
    predicted_direction = predictions > current_prices  # Did we predict it would go up?
    accuracy = np.mean(actual_direction == predicted_direction)
    
    # Also calculate percentage that went up vs down
    pct_up_actual = np.mean(actual_direction)
    pct_up_pred = np.mean(predicted_direction)
    
    return accuracy, pct_up_actual, pct_up_pred

print("✅ Correct directional accuracy function defined")

# 2. BASELINE: SIMPLE LINEAR MODEL
print("\n" + "="*80)
print("2. BASELINE - SIMPLE LINEAR REGRESSION")
print("="*80)

linear_model = LinearRegression()
linear_model.fit(X_train, y_train)

linear_train_pred = linear_model.predict(X_train)
linear_test_pred = linear_model.predict(X_test)

linear_train_mae = mean_absolute_error(y_train, linear_train_pred)
linear_test_mae = mean_absolute_error(y_test, linear_test_pred)
linear_train_mape = np.mean(np.abs((y_train - linear_train_pred) / y_train)) * 100
linear_test_mape = np.mean(np.abs((y_test - linear_test_pred) / y_test)) * 100

# Correct directional accuracy
linear_dir_acc, actual_up_pct, pred_up_pct = directional_accuracy_correct(
    test_current_price, y_test, linear_test_pred
)

print(f"Linear Regression Performance:")
print(f"  Train MAE: ${linear_train_mae:.2f}")
print(f"  Test MAE: ${linear_test_mae:.2f}")
print(f"  Train MAPE: {linear_train_mape:.2f}%")
print(f"  Test MAPE: {linear_test_mape:.2f}%")
print(f"  Directional Accuracy: {linear_dir_acc:.2%}")
print(f"  Actual price went up: {actual_up_pct:.2%} of time")
print(f"  Model predicts up: {pred_up_pct:.2%} of time")

# Top 10 most important features
coef_abs = [(feature_names[i], linear_model.coef_[i]) for i in range(len(feature_names))]
coef_sorted = sorted(coef_abs, key=lambda x: abs(x[1]), reverse=True)

print(f"\n📊 Top 10 Features (Linear Coefficients):")
for feat, coef in coef_sorted[:10]:
    print(f"  {feat[:40]:40} {coef:+.6f}")

# 3. FEATURE IMPORTANCE ANALYSIS
print("\n" + "="*80)
print("3. FEATURE IMPORTANCE - GRADIENT BOOSTING")
print("="*80)

gb_model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=5,
    random_state=42,
    verbose=0
)

gb_model.fit(X_train, y_train)

gb_train_pred = gb_model.predict(X_train)
gb_test_pred = gb_model.predict(X_test)

gb_test_mae = mean_absolute_error(y_test, gb_test_pred)
gb_test_mape = np.mean(np.abs((y_test - gb_test_pred) / y_test)) * 100

gb_dir_acc, _, _ = directional_accuracy_correct(test_current_price, y_test, gb_test_pred)

print(f"Gradient Boosting Performance:")
print(f"  Test MAE: ${gb_test_mae:.2f}")
print(f"  Test MAPE: {gb_test_mape:.2f}%")
print(f"  Directional Accuracy: {gb_dir_acc:.2%}")

# Feature importance
feature_importance = list(zip(feature_names, gb_model.feature_importances_))
importance_sorted = sorted(feature_importance, key=lambda x: x[1], reverse=True)

print(f"\n📊 Top 15 Most Important Features:")
for feat, imp in importance_sorted[:15]:
    print(f"  {feat[:45]:45} {imp:.6f}")

# Check new features specifically
print(f"\n🔍 New Feature Importance:")
new_feature_keywords = ['crush', 'fx_usd_brl', 'fx_usd_cny', 'fx_usd_ars', 'fx_usd_myr', 
                       'tariff', 'trump', 'china_mentions', 'policy', 'engagement']

for keyword in new_feature_keywords:
    matching_features = [(f, imp) for f, imp in importance_sorted if keyword in f.lower()]
    if matching_features:
        total_importance = sum(imp for _, imp in matching_features)
        print(f"  {keyword:20} {len(matching_features)} features, total importance: {total_importance:.6f}")
        for f, imp in matching_features[:2]:
            print(f"     - {f[:35]:35} {imp:.6f}")

# 4. COMPARE TO BASELINE
print("\n" + "="*80)
print("4. COMPARISON TO EXISTING V4 MODEL")
print("="*80)

print(f"Performance comparison:")
print(f"  Existing V4 Enriched:  MAE $1.55, MAPE 3.09%")
print(f"  Our Linear Model:      MAE ${linear_test_mae:.2f}, MAPE {linear_test_mape:.2f}%")
print(f"  Our Gradient Boosting: MAE ${gb_test_mae:.2f}, MAPE {gb_test_mape:.2f}%")

if gb_test_mae < 1.55:
    print(f"  ✅ BEATS V4! Improvement: ${1.55 - gb_test_mae:.2f}")
elif gb_test_mae < 2.0:
    print(f"  ⚠️ Close to V4 (within $0.50)")
else:
    print(f"  ❌ Worse than V4 by ${gb_test_mae - 1.55:.2f}")

# 5. CHECK FOR PREPROCESSING ISSUES
print("\n" + "="*80)
print("5. PREPROCESSING DIAGNOSTICS")
print("="*80)

# Check for NaN/Inf in data
print(f"Data quality:")
print(f"  NaN in X_train: {np.isnan(X_train).sum()}")
print(f"  Inf in X_train: {np.isinf(X_train).sum()}")
print(f"  NaN in y_train: {np.isnan(y_train).sum()}")

# Check scaling
print(f"\nFeature scaling check (X_train should be ~0 mean, ~1 std):")
print(f"  Mean: {X_train.mean():.6f}")
print(f"  Std: {X_train.std():.6f}")

# Check for features with zero variance
zero_var_features = []
for i, feat in enumerate(feature_names):
    if X_train[:, i].std() == 0:
        zero_var_features.append(feat)

if zero_var_features:
    print(f"\n⚠️ Features with zero variance:")
    for feat in zero_var_features:
        print(f"  - {feat}")
else:
    print(f"  ✅ All features have variance")

# 6. ERROR PATTERN ANALYSIS
print("\n" + "="*80)
print("6. ERROR PATTERN ANALYSIS")
print("="*80)

gb_errors = y_test - gb_test_pred
abs_errors = np.abs(gb_errors)

print(f"Error statistics:")
print(f"  Mean error (bias): ${gb_errors.mean():.2f}")
print(f"  Median error: ${np.median(gb_errors):.2f}")
print(f"  Max overestimate: ${gb_errors.min():.2f}")
print(f"  Max underestimate: ${gb_errors.max():.2f}")

# Check if underpredicting
if gb_errors.mean() > 0.5:
    print(f"  🚨 SYSTEMATIC UNDERPREDICTION: Model predicts ${gb_errors.mean():.2f} too low on average")
elif gb_errors.mean() < -0.5:
    print(f"  🚨 SYSTEMATIC OVERPREDICTION: Model predicts ${abs(gb_errors.mean()):.2f} too high on average")
else:
    print(f"  ✅ No systematic bias")

# Save diagnostic results
results = pd.DataFrame({
    'model': ['Linear', 'GradientBoosting', 'V4_Enriched (baseline)'],
    'test_mae': [linear_test_mae, gb_test_mae, 1.55],
    'test_mape': [linear_test_mape, gb_test_mape, 3.09],
    'directional_acc': [linear_dir_acc, gb_dir_acc, np.nan]
})

results.to_csv('MODEL_DIAGNOSTIC_RESULTS.csv', index=False)

# Save feature importance
imp_df = pd.DataFrame(importance_sorted, columns=['feature', 'importance'])
imp_df.to_csv('FEATURE_IMPORTANCE_DIAGNOSTIC.csv', index=False)

print(f"\n💾 Saved:")
print(f"  • MODEL_DIAGNOSTIC_RESULTS.csv")
print(f"  • FEATURE_IMPORTANCE_DIAGNOSTIC.csv")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)

print(f"\n🎯 KEY FINDINGS:")
print(f"  1. Linear baseline MAE: ${linear_test_mae:.2f}")
print(f"  2. Gradient Boosting MAE: ${gb_test_mae:.2f}")
print(f"  3. V4 target to beat: $1.55")
print(f"  4. Directional accuracy: {gb_dir_acc:.2%}")

if gb_test_mae > linear_test_mae:
    print(f"  ⚠️ GB worse than linear - possible overfitting")
    print(f"     Try: reduce max_depth, increase min_samples")

if gb_errors.mean() > 1.0:
    print(f"  ⚠️ Systematic underprediction of ${gb_errors.mean():.2f}")
    print(f"     Possible causes: train/test domain shift, missing important features")

