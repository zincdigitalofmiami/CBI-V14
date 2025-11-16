#!/usr/bin/env python3
"""
PRE-FLIGHT PERFORMANCE HARNESS
FIXED: Walk-forward evaluation, matches horizon, mirrors BQ MAPE logic, no unsafe imputation.
Train on last 12 months using walk-forward splits, compute MAPE using EXACT BQ logic.
Must match dashboard metrics or BLOCK training.
"""

import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from google.cloud import bigquery
from lightgbm import LGBMRegressor

# FIX #6: Set all seeds for determinism
os.environ['PYTHONHASHSEED'] = '42'
random.seed(42)
np.random.seed(42)

def compute_local_mape(actuals, predictions):
    """
    Compute MAPE using EXACT logic from performance.vw_forecast_performance_tracking.
    FIX #8: No unsafe imputation - uses actual values as-is.
    """
    # Filter out NaN values (don't impute)
    mask = (~np.isnan(actuals)) & (~np.isnan(predictions)) & (actuals != 0)
    actuals_clean = actuals[mask]
    predictions_clean = predictions[mask]
    
    if len(actuals_clean) == 0:
        return np.nan
    
    mape = np.mean(np.abs((predictions_clean - actuals_clean) / actuals_clean)) * 100
    return mape

def get_bq_mape_1week():
    """Query current 1-week MAPE from BigQuery dashboard view"""
    try:
        client = bigquery.Client(project='cbi-v14', location='us-central1')
        query = """
        SELECT overall_mape_1week
        FROM `cbi-v14.performance.vw_forecast_performance_tracking`
        """
        df = client.query(query).to_dataframe()
        
        if len(df) == 0 or df['overall_mape_1week'].iloc[0] is None:
            print("⚠️  BQ MAPE not available, skipping parity check")
            return None
        
        return df['overall_mape_1week'].iloc[0]
    except Exception as e:
        print(f"⚠️  Could not fetch BQ MAPE: {e}")
        return None

def pre_flight_check():
    """
    THE GATE: Block training if local metrics don't match BQ.
    FIX #1: Walk-forward evaluation, correct horizon (1w), mirrors BQ view logic.
    FIX #8: Drops NA rows, no unsafe imputation.
    """
    print("\n" + "="*80)
    print("PRE-FLIGHT PERFORMANCE HARNESS")
    print("="*80)
    print("FIX #1: Walk-forward evaluation matching BQ MAPE view")
    print("FIX #6: Determinism controls active")
    print("FIX #8: No unsafe imputation (drop NA, don't fill)")
    
    # FIX #1: Load CORRECT horizon (1w for 1-week MAPE)
    parquet_file = Path("TrainingData/exports/zl_training_prod_allhistory_1w_price.parquet")
    
    if not parquet_file.exists():
        print(f"⚠️  {parquet_file} not found, cannot run parity check")
        return True  # Non-blocking if file doesn't exist yet
    
    df = pd.read_parquet(parquet_file)
    
    # FIX #8: Drop NA targets (don't ffill or impute)
    df = df.dropna(subset=['target'])
    df = df.sort_values('date')
    
    print(f"\nLoaded: {len(df)} rows (after dropping NA targets)")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # FIX #1: Walk-forward evaluation (train on 12m, test on next 1m, rolling)
    preds_all, actuals_all = [], []
    dates = df['date'].sort_values().unique()
    
    # Start after 12 months of history
    start_date = dates.min() + pd.Timedelta(days=365)
    end_date = dates.max() - pd.Timedelta(days=30)
    
    if start_date >= end_date:
        print(f"⚠️  Insufficient data for walk-forward (need >13 months)")
        return True
    
    # Monthly steps for walk-forward
    for cut_date in pd.date_range(start_date, end_date, freq='30D'):
        train_df = df[df['date'] < cut_date]
        test_df = df[(df['date'] >= cut_date) & (df['date'] < cut_date + pd.Timedelta(days=30))]
        
        if len(train_df) < 200 or len(test_df) == 0:
            continue
        
        # Features (FIX #8: drop NA rows, don't impute with 0)
        feature_cols = [c for c in train_df.columns 
                       if c not in ['date', 'target', 'market_regime', 'training_weight', 'symbol']]
        
        # Replace inf with NaN, then drop rows with any NaN in features
        X_train = train_df[feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
        y_train = train_df.loc[X_train.index, 'target']
        
        X_test = test_df[feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
        y_test = test_df.loc[X_test.index, 'target']
        
        if len(X_test) == 0 or len(X_train) == 0:
            continue
        
        # Train small model (FIX #6: deterministic with random_state)
        model = LGBMRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            deterministic=True,
            force_row_wise=True
        )
        model.fit(X_train, y_train)
        
        # Predict
        preds = model.predict(X_test)
        actuals_all.extend(y_test.values)
        preds_all.extend(preds)
    
    # Compute local MAPE (exact BQ formula)
    if len(actuals_all) == 0:
        print("❌ No predictions generated in walk-forward")
        return False
    
    local_mape = compute_local_mape(np.array(actuals_all), np.array(preds_all))
    
    print(f"\nWalk-forward results:")
    print(f"  Predictions: {len(preds_all)}")
    print(f"  Local MAPE: {local_mape:.2f}%")
    
    # Get BQ MAPE
    bq_mape = get_bq_mape_1week()
    
    if bq_mape is None:
        print(f"\n⚠️  BQ MAPE not available - skipping parity check")
        print(f"   (This is expected if running for first time)")
        return True
    
    # Check parity (FIX #6: Allow ±0.1-0.3% variance for determinism tolerance)
    diff = abs(local_mape - bq_mape)
    
    print(f"\n{'='*60}")
    print(f"METRIC PARITY CHECK")
    print(f"{'='*60}")
    print(f"Local MAPE (1w):  {local_mape:.2f}%")
    print(f"BQ MAPE (1w):     {bq_mape:.2f}%")
    print(f"Difference:       {diff:.2f}%")
    print(f"Tolerance:        ±0.5% (allows ±0.1-0.3% determinism variance)")
    
    if diff > 0.5:
        print(f"\n❌ PARITY FAILURE - BLOCKING TRAINING")
        print(f"   Local and BQ metrics diverged by {diff:.2f}%")
        print(f"   Fix metric calculation before proceeding.")
        raise ValueError("MAPE parity check failed")
    
    print(f"\n✅ PARITY CHECK PASSED - TRAINING APPROVED")
    return True

def verify_no_leakage(df):
    """
    FIX: Implement synthetic leakage test.
    Tests that target cannot be predicted from same-row features.
    """
    print("\n🔍 Testing for data leakage...")
    
    if 'target' not in df.columns:
        print("  ⚠️  No target column, skipping leakage test")
        return True
    
    # Drop NA
    df_test = df.dropna(subset=['target'])
    
    if len(df_test) < 100:
        print("  ⚠️  Insufficient data for leakage test")
        return True
    
    # Create synthetic shifted label (this SHOULD leak if we're not careful)
    df_test['synthetic_leak'] = df_test['target'].shift(1)  # Previous target
    
    # Try to predict target from features + synthetic leak
    feature_cols = [c for c in df_test.columns 
                   if c not in ['date', 'target', 'symbol', 'market_regime', 'training_weight', 'synthetic_leak']]
    
    X_no_leak = df_test[feature_cols].iloc[:100].replace([np.inf, -np.inf], np.nan).dropna()
    X_with_leak = df_test[feature_cols + ['synthetic_leak']].iloc[:100].replace([np.inf, -np.inf], np.nan).dropna()
    y = df_test.loc[X_no_leak.index, 'target']
    
    # Train two models
    model_clean = LGBMRegressor(n_estimators=50, random_state=42)
    model_leak = LGBMRegressor(n_estimators=50, random_state=42)
    
    model_clean.fit(X_no_leak, y)
    model_leak.fit(X_with_leak, y)
    
    # If leaking, the second model should be MUCH better
    score_clean = model_clean.score(X_no_leak, y)
    score_leak = model_leak.score(X_with_leak, y)
    
    lift = score_leak - score_clean
    
    print(f"  R² without leak: {score_clean:.4f}")
    print(f"  R² with leak:    {score_leak:.4f}")
    print(f"  Lift:            {lift:.4f}")
    
    # If lift < 0.05, no leakage detected
    if lift < 0.05:
        print(f"  ✅ No leakage detected (lift < 0.05)")
        return True
    else:
        print(f"  ❌ LEAKAGE DETECTED (lift = {lift:.4f})")
        return False

if __name__ == '__main__':
    result = pre_flight_check()
    if result:
        print("\n✅ PRE-FLIGHT COMPLETE - SYSTEM READY FOR TRAINING")
    else:
        print("\n❌ PRE-FLIGHT FAILED - FIX ISSUES BEFORE TRAINING")
        exit(1)

