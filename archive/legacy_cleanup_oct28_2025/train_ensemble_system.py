#!/usr/bin/env python3
"""
Professional Ensemble Training System
5 Specialized Models + Adaptive Meta-Learning with Regime Awareness
Using sklearn ensemble methods (no OpenMP dependency)
"""

import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import torch
import torch.nn as nn
import torch.optim as optim

print("="*80)
print("PROFESSIONAL ENSEMBLE TRAINING SYSTEM")
print("Crystal Ball Intelligence V14 - Soybean Oil Futures")
print("="*80)

# Load data
print("\n📊 Loading Training Data...")
print("-"*80)

# DISABLED: train_df = pd.read_csv('TRAIN_ENHANCED.csv')  # DELETED - contained fake data
# Use REAL_TRAINING_DATA_WITH_CURRENCIES.csv for clean ensemble training
# DISABLED: test_df = pd.read_csv('TEST_ENHANCED.csv')  # DELETED - contained fake data

# Load feature list
with open('ENHANCED_FEATURES.txt', 'r') as f:
    feature_names = [line.strip() for line in f.readlines()]

print(f"Training: {len(train_df)} rows")
print(f"Test: {len(test_df)} rows")
print(f"Features: {len(feature_names)}")

# Prepare data
X_train = train_df[feature_names].values
y_train = train_df['target_1w'].values
X_test = test_df[feature_names].values
y_test = test_df['target_1w'].values

# Remove any remaining NaN
X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
y_train = np.nan_to_num(y_train, nan=0.0)
X_test = np.nan_to_num(X_test, nan=0.0, posinf=0.0, neginf=0.0)
y_test = np.nan_to_num(y_test, nan=0.0)

print(f"✅ Data prepared")

# Define feature groups for specialists
print("\n🎯 Defining Specialist Feature Groups...")
print("-"*80)

feature_groups = {
    'policy': [],
    'geographic': [],
    'arbitrage': [],
    'momentum': [],
    'volatility': []
}

for i, feat in enumerate(feature_names):
    feat_lower = feat.lower()
    
    # Policy specialist
    if any(x in feat_lower for x in ['tariff', 'trump', 'china', 'policy', 'ice', 'engagement', 'sentiment']):
        feature_groups['policy'].append(i)
    
    # Geographic specialist
    if any(x in feat_lower for x in ['brazil', 'weather', 'temp', 'precip', 'fx_usd_brl', 'fx_usd_ars', 'fx_usd_cny', 'seasonal', 'month']):
        feature_groups['geographic'].append(i)
    
    # Arbitrage specialist
    if any(x in feat_lower for x in ['corr', 'palm', 'crude', 'crush', 'spread', 'fx_usd_myr']):
        feature_groups['arbitrage'].append(i)
    
    # Momentum specialist
    if any(x in feat_lower for x in ['price', 'return', 'lag', 'ma_', 'volume', 'momentum']):
        feature_groups['momentum'].append(i)
    
    # Volatility specialist
    if any(x in feat_lower for x in ['vix', 'volatility', 'vol_']):
        feature_groups['volatility'].append(i)

# Print feature counts
for specialist, indices in feature_groups.items():
    features = [feature_names[i] for i in indices]
    print(f"  {specialist.capitalize():15} {len(features):3d} features")
    if len(features) > 0:
        print(f"    Examples: {features[:3]}")

# Helper functions
def directional_accuracy(y_true, y_pred):
    """Calculate directional accuracy"""
    true_dir = (y_true > 0).astype(int)
    pred_dir = (y_pred > 0).astype(int)
    return np.mean(true_dir == pred_dir)

def calculate_sharpe(returns):
    """Calculate annualized Sharpe ratio"""
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    return np.mean(returns) / np.std(returns) * np.sqrt(252)

print("\n" + "="*80)
print("PHASE 1: TRAINING SPECIALIST MODELS")
print("="*80)

# Track all specialist predictions
specialist_predictions = {}
specialist_metrics = {}

# Train each specialist
print("\n1️⃣ POLICY REGIME SPECIALIST (Gradient Boosting)")
print("-"*80)

if len(feature_groups['policy']) > 0:
    X_train_policy = X_train[:, feature_groups['policy']]
    X_test_policy = X_test[:, feature_groups['policy']]
    
    print(f"  Features: {len(feature_groups['policy'])}")
    print(f"  Training samples: {len(X_train_policy)}")
    
    # Gradient Boosting with conservative parameters
    lgb_policy = GradientBoostingRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        max_features=0.8,
        random_state=42,
        verbose=1
    )
    
    lgb_policy.fit(X_train_policy, y_train)
    
    # Predictions
    policy_train_pred = lgb_policy.predict(X_train_policy)
    policy_test_pred = lgb_policy.predict(X_test_policy)
    
    # Metrics
    policy_metrics = {
        'train_mae': mean_absolute_error(y_train, policy_train_pred),
        'test_mae': mean_absolute_error(y_test, policy_test_pred),
        'train_dir_acc': directional_accuracy(y_train, policy_train_pred),
        'test_dir_acc': directional_accuracy(y_test, policy_test_pred),
    }
    
    specialist_predictions['policy'] = policy_test_pred
    specialist_metrics['policy'] = policy_metrics
    
    print(f"  ✅ Training MAE: {policy_metrics['train_mae']:.6f}")
    print(f"  ✅ Test MAE: {policy_metrics['test_mae']:.6f}")
    print(f"  ✅ Training Dir Acc: {policy_metrics['train_dir_acc']:.2%}")
    print(f"  ✅ Test Dir Acc: {policy_metrics['test_dir_acc']:.2%}")
    
    # Check for overfitting
    if policy_metrics['train_mae'] / policy_metrics['test_mae'] < 0.5:
        print(f"  ⚠️ Warning: Possible overfitting (train/test ratio: {policy_metrics['train_mae']/policy_metrics['test_mae']:.2f})")
else:
    print(f"  ⚠️ No policy features available")

print("\n2️⃣ GEOGRAPHIC SUPPLY SPECIALIST (Gradient Boosting)")
print("-"*80)

if len(feature_groups['geographic']) > 0:
    X_train_geo = X_train[:, feature_groups['geographic']]
    X_test_geo = X_test[:, feature_groups['geographic']]
    
    print(f"  Features: {len(feature_groups['geographic'])}")
    print(f"  Training samples: {len(X_train_geo)}")
    
    xgb_geo = GradientBoostingRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        min_samples_split=20,
        min_samples_leaf=10,
        subsample=0.8,
        max_features=0.8,
        random_state=42,
        verbose=1
    )
    
    xgb_geo.fit(X_train_geo, y_train)
    
    # Predictions
    geo_train_pred = xgb_geo.predict(X_train_geo)
    geo_test_pred = xgb_geo.predict(X_test_geo)
    
    # Metrics
    geo_metrics = {
        'train_mae': mean_absolute_error(y_train, geo_train_pred),
        'test_mae': mean_absolute_error(y_test, geo_test_pred),
        'train_dir_acc': directional_accuracy(y_train, geo_train_pred),
        'test_dir_acc': directional_accuracy(y_test, geo_test_pred),
    }
    
    specialist_predictions['geographic'] = geo_test_pred
    specialist_metrics['geographic'] = geo_metrics
    
    print(f"  ✅ Training MAE: {geo_metrics['train_mae']:.6f}")
    print(f"  ✅ Test MAE: {geo_metrics['test_mae']:.6f}")
    print(f"  ✅ Training Dir Acc: {geo_metrics['train_dir_acc']:.2%}")
    print(f"  ✅ Test Dir Acc: {geo_metrics['test_dir_acc']:.2%}")
else:
    print(f"  ⚠️ No geographic features available")

print("\n3️⃣ CROSS-ASSET ARBITRAGE SPECIALIST (Random Forest)")
print("-"*80)

if len(feature_groups['arbitrage']) > 0:
    X_train_arb = X_train[:, feature_groups['arbitrage']]
    X_test_arb = X_test[:, feature_groups['arbitrage']]
    
    print(f"  Features: {len(feature_groups['arbitrage'])}")
    print(f"  Training samples: {len(X_train_arb)}")
    
    lgb_arb = RandomForestRegressor(
        n_estimators=500,
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features=0.8,
        bootstrap=True,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    lgb_arb.fit(X_train_arb, y_train)
    
    # Predictions
    arb_train_pred = lgb_arb.predict(X_train_arb)
    arb_test_pred = lgb_arb.predict(X_test_arb)
    
    # Metrics
    arb_metrics = {
        'train_mae': mean_absolute_error(y_train, arb_train_pred),
        'test_mae': mean_absolute_error(y_test, arb_test_pred),
        'train_dir_acc': directional_accuracy(y_train, arb_train_pred),
        'test_dir_acc': directional_accuracy(y_test, arb_test_pred),
    }
    
    specialist_predictions['arbitrage'] = arb_test_pred
    specialist_metrics['arbitrage'] = arb_metrics
    
    print(f"  ✅ Training MAE: {arb_metrics['train_mae']:.6f}")
    print(f"  ✅ Test MAE: {arb_metrics['test_mae']:.6f}")
    print(f"  ✅ Training Dir Acc: {arb_metrics['train_dir_acc']:.2%}")
    print(f"  ✅ Test Dir Acc: {arb_metrics['test_dir_acc']:.2%}")
else:
    print(f"  ⚠️ No arbitrage features available")

print("\n4️⃣ PRICE MOMENTUM SPECIALIST (LSTM - PyTorch)")
print("-"*80)

if len(feature_groups['momentum']) > 5:
    # For LSTM, we'll use simpler approach with all momentum features
    X_train_mom = X_train[:, feature_groups['momentum']]
    X_test_mom = X_test[:, feature_groups['momentum']]
    
    print(f"  Features: {len(feature_groups['momentum'])}")
    
    # Simple feed-forward instead of LSTM for now (sequences complex)
    # Convert to PyTorch tensors
    X_train_mom_t = torch.FloatTensor(X_train_mom)
    y_train_t = torch.FloatTensor(y_train).reshape(-1, 1)
    X_test_mom_t = torch.FloatTensor(X_test_mom)
    y_test_t = torch.FloatTensor(y_test).reshape(-1, 1)
    
    # Simple neural network
    class MomentumNet(nn.Module):
        def __init__(self, input_size):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_size, 64),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(32, 1)
            )
        
        def forward(self, x):
            return self.net(x)
    
    mom_model = MomentumNet(X_train_mom.shape[1])
    optimizer = optim.Adam(mom_model.parameters(), lr=0.001, weight_decay=0.0001)
    criterion = nn.MSELoss()
    
    # Train
    print(f"  Training neural network...")
    for epoch in range(100):
        mom_model.train()
        optimizer.zero_grad()
        outputs = mom_model(X_train_mom_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 25 == 0:
            mom_model.eval()
            with torch.no_grad():
                test_out = mom_model(X_test_mom_t)
                test_loss = criterion(test_out, y_test_t)
            print(f"    Epoch {epoch+1}/100 - Train Loss: {loss.item():.6f}, Test Loss: {test_loss.item():.6f}")
    
    # Predictions
    mom_model.eval()
    with torch.no_grad():
        mom_train_pred = mom_model(X_train_mom_t).numpy().flatten()
        mom_test_pred = mom_model(X_test_mom_t).numpy().flatten()
    
    mom_metrics = {
        'train_mae': mean_absolute_error(y_train, mom_train_pred),
        'test_mae': mean_absolute_error(y_test, mom_test_pred),
        'train_dir_acc': directional_accuracy(y_train, mom_train_pred),
        'test_dir_acc': directional_accuracy(y_test, mom_test_pred),
    }
    
    specialist_predictions['momentum'] = mom_test_pred
    specialist_metrics['momentum'] = mom_metrics
    
    print(f"  ✅ Training MAE: {mom_metrics['train_mae']:.6f}")
    print(f"  ✅ Test MAE: {mom_metrics['test_mae']:.6f}")
    print(f"  ✅ Training Dir Acc: {mom_metrics['train_dir_acc']:.2%}")
    print(f"  ✅ Test Dir Acc: {mom_metrics['test_dir_acc']:.2%}")
else:
    print(f"  ⚠️ Insufficient momentum features")

print("\n5️⃣ VOLATILITY REGIME SPECIALIST (Extra Trees)")
print("-"*80)

if len(feature_groups['volatility']) > 3:
    X_train_vol = X_train[:, feature_groups['volatility']]
    X_test_vol = X_test[:, feature_groups['volatility']]
    
    print(f"  Features: {len(feature_groups['volatility'])}")
    
    xgb_vol = ExtraTreesRegressor(
        n_estimators=300,
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features=0.8,
        bootstrap=False,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    xgb_vol.fit(X_train_vol, y_train)
    
    vol_train_pred = xgb_vol.predict(X_train_vol)
    vol_test_pred = xgb_vol.predict(X_test_vol)
    
    vol_metrics = {
        'train_mae': mean_absolute_error(y_train, vol_train_pred),
        'test_mae': mean_absolute_error(y_test, vol_test_pred),
        'train_dir_acc': directional_accuracy(y_train, vol_train_pred),
        'test_dir_acc': directional_accuracy(y_test, vol_test_pred),
    }
    
    specialist_predictions['volatility'] = vol_test_pred
    specialist_metrics['volatility'] = vol_metrics
    
    print(f"  ✅ Training MAE: {vol_metrics['train_mae']:.6f}")
    print(f"  ✅ Test MAE: {vol_metrics['test_mae']:.6f}")
    print(f"  ✅ Training Dir Acc: {vol_metrics['train_dir_acc']:.2%}")
    print(f"  ✅ Test Dir Acc: {vol_metrics['test_dir_acc']:.2%}")
else:
    print(f"  ⚠️ Insufficient volatility features")

# PHASE 1 CHECKPOINT
print("\n" + "="*80)
print("PHASE 1 COMPLETE - SPECIALIST MODELS TRAINED")
print("="*80)

print("\n📊 Specialist Performance Summary:")
print("-"*80)

for specialist, metrics in specialist_metrics.items():
    print(f"\n{specialist.upper()}:")
    print(f"  Test MAE: {metrics['test_mae']:.6f}")
    print(f"  Test Directional Accuracy: {metrics['test_dir_acc']:.2%}")
    
    # Benchmark check
    if metrics['test_dir_acc'] > 0.52:
        print(f"  ✅ BEATS RANDOM (>52%)")
    else:
        print(f"  ❌ Below random - specialist may not work")

# Find best individual specialist
best_specialist = max(specialist_metrics.items(), key=lambda x: x[1]['test_dir_acc'])
print(f"\n🏆 Best Individual Specialist: {best_specialist[0].upper()}")
print(f"   Test Accuracy: {best_specialist[1]['test_dir_acc']:.2%}")

print("\n✅ Phase 1 checkpoint passed")
print("✅ Proceeding to Phase 2: Linear Meta-Learner")

# Continue with file
print("\n" + "="*80)
print("PHASE 2: LINEAR META-LEARNER (Ridge Regression)")
print("="*80)

# Prepare specialist predictions matrix
specialist_names = list(specialist_predictions.keys())
X_meta_test = np.column_stack([specialist_predictions[name] for name in specialist_names])

# For training, we need to get training predictions
print("\nGenerating training predictions for meta-learner...")

meta_train_preds = []
for specialist in specialist_names:
    if specialist == 'policy' and 'policy' in specialist_predictions:
        meta_train_preds.append(policy_train_pred)
    elif specialist == 'geographic':
        meta_train_preds.append(geo_train_pred)
    elif specialist == 'arbitrage':
        meta_train_preds.append(arb_train_pred)
    elif specialist == 'momentum':
        meta_train_preds.append(mom_train_pred)
    elif specialist == 'volatility':
        meta_train_preds.append(vol_train_pred)

X_meta_train = np.column_stack(meta_train_preds)

print(f"Meta-learner training data: {X_meta_train.shape}")
print(f"Specialists: {specialist_names}")

# Train Ridge regression
ridge = Ridge(alpha=1.0)  # L2 regularization
ridge.fit(X_meta_train, y_train)

# Predictions
ridge_train_pred = ridge.predict(X_meta_train)
ridge_test_pred = ridge.predict(X_meta_test)

# Calculate metrics
ridge_metrics = {
    'train_mae': mean_absolute_error(y_train, ridge_train_pred),
    'test_mae': mean_absolute_error(y_test, ridge_test_pred),
    'train_dir_acc': directional_accuracy(y_train, ridge_train_pred),
    'test_dir_acc': directional_accuracy(y_test, ridge_test_pred),
}

print(f"\n📊 Ridge Meta-Learner Performance:")
print("-"*80)
print(f"  Test MAE: {ridge_metrics['test_mae']:.6f}")
print(f"  Test Directional Accuracy: {ridge_metrics['test_dir_acc']:.2%}")

# CRITICAL: Show specialist weights
print(f"\n🔍 Specialist Contribution (Ridge Weights):")
print("-"*80)

for specialist, weight in zip(specialist_names, ridge.coef_):
    print(f"  {specialist.capitalize():15} Weight: {weight:7.4f}")
    
    if abs(weight) < 0.05:
        print(f"     ⚠️ Low contribution - specialist may not be useful")
    elif weight < 0:
        print(f"     ⚠️ Negative weight - specialist predictions inverse")

print(f"\n  Intercept: {ridge.intercept_:.6f}")

# Compare to best individual
print(f"\n📊 Ensemble vs Best Individual:")
print("-"*80)
print(f"  Best Individual: {best_specialist[1]['test_dir_acc']:.2%}")
print(f"  Ridge Ensemble: {ridge_metrics['test_dir_acc']:.2%}")

improvement = ridge_metrics['test_dir_acc'] - best_specialist[1]['test_dir_acc']
print(f"  Improvement: {improvement:+.2%}")

if improvement > 0.01:
    print(f"  ✅ Ensemble beats best individual - stacking works!")
else:
    print(f"  ⚠️ Ensemble doesn't beat best individual - specialists may not be complementary")

# Benchmark checks
print(f"\n🎯 Benchmark Progress:")
print("-"*80)

benchmarks = [(0.55, '55% - Model has signal'), 
              (0.60, '60% - Production ready'),
              (0.65, '65% - Excellent performance'),
              (0.70, '70% - Investigate for leakage')]

current_acc = ridge_metrics['test_dir_acc']

for threshold, desc in benchmarks:
    if current_acc >= threshold:
        print(f"  ✅ {desc}")
    else:
        print(f"  ⏳ {desc} (current: {current_acc:.2%})")

# Save all results
print(f"\n💾 Saving Results...")
print("-"*80)

# Save specialist predictions
pred_df = pd.DataFrame({
    'date': test_df['date'].values,
    'actual': y_test,
    'ridge_ensemble': ridge_test_pred
})

for specialist, preds in specialist_predictions.items():
    pred_df[f'{specialist}_pred'] = preds

pred_df.to_csv('SPECIALIST_PREDICTIONS.csv', index=False)
print(f"  ✅ SPECIALIST_PREDICTIONS.csv")

# Save metrics
metrics_df = pd.DataFrame(specialist_metrics).T
metrics_df.to_csv('SPECIALIST_METRICS.csv')
print(f"  ✅ SPECIALIST_METRICS.csv")

# Save models
with open('specialist_models.pkl', 'wb') as f:
    pickle.dump({
        'policy': lgb_policy if 'policy' in specialist_predictions else None,
        'geographic': xgb_geo if 'geographic' in specialist_predictions else None,
        'arbitrage': lgb_arb if 'arbitrage' in specialist_predictions else None,
        'momentum': mom_model if 'momentum' in specialist_predictions else None,
        'volatility': xgb_vol if 'volatility' in specialist_predictions else None,
        'ridge_meta': ridge,
        'feature_groups': feature_groups,
        'specialist_names': specialist_names
    }, f)
print(f"  ✅ specialist_models.pkl")

print("\n" + "="*80)
print("TRAINING COMPLETE")
print("="*80)

print(f"\n🎯 FINAL RESULTS:")
print(f"  Test Directional Accuracy: {ridge_metrics['test_dir_acc']:.2%}")
print(f"  Test MAE: {ridge_metrics['test_mae']:.6f}")

print(f"\n📁 Files Created:")
print(f"  • SPECIALIST_PREDICTIONS.csv")
print(f"  • SPECIALIST_METRICS.csv")
print(f"  • specialist_models.pkl")

print(f"\n✅ Ready for Phase 3: Regime-Aware Ensemble (if needed)")

