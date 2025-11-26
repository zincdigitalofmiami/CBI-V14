#!/usr/bin/env python3
"""
EXPERIMENTAL ONLY – Quick ZL Baseline (Directional / Return-Based Targets)
==========================================================================

This script is for RESEARCH ONLY. It intentionally deviates from the
production specification in docs/plans/ZL_PRODUCTION_SPEC.md:

- Targets here are forward RETURNS / DIRECTIONAL LABELS, not price levels.
- It uses ad-hoc feature construction from BigQuery tables.
- Outputs (if saved) must go under TrainingData/models/zl_baselines/experiments/.

Nothing in this file should ever be wired directly into production forecasts
or dashboards. For production ZL baselines, use scripts/train/train_zl_baselines.py.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
from dataclasses import asdict

from cbi_v14.backtest.specs import DatasetSpec, ModelSpec, BacktestResult, BacktestRun

# Configuration
PROJECT_ID = "cbi-v14"
SYMBOLS = ['ZL', 'ZS', 'ZM', 'CL', 'HO']
HORIZONS = {'5d': 5, '21d': 21, '63d': 63}  # 1 week, 1 month, 3 months

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")
EXPERIMENTS_DIR = DRIVE / "models/zl_baselines/experiments"

def load_data_from_bq():
    """Load daily OHLCV + fundamental features from BigQuery."""
    print("📊 Loading data from BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Load price data
    price_query = f"""
    SELECT 
        date,
        symbol,
        open,
        high,
        low,
        close,
        volume
    FROM `{PROJECT_ID}.market_data.databento_futures_ohlcv_1d`
    WHERE symbol IN ('ZL', 'ZS', 'ZM', 'CL', 'HO')
    ORDER BY date, symbol
    """
    df_price = client.query(price_query).to_dataframe()
    df_price['date'] = pd.to_datetime(df_price['date'])
    print(f"   Price data: {len(df_price):,} rows")
    
    # Load macro features
    macro_query = f"""
    SELECT 
        date,
        fed_funds_rate,
        treasury_10y,
        treasury_2y,
        treasury_3m,
        yield_curve_10y_2y,
        yield_curve_10y_3m,
        wti_crude,
        brent_crude,
        nat_gas_henry_hub,
        wti_ret_1d,
        wti_vol_21d,
        fed_rate_change,
        curve_inverted_10y_2y,
        curve_inverted_10y_3m
    FROM `{PROJECT_ID}.features.macro_features_daily`
    """
    df_macro = client.query(macro_query).to_dataframe()
    df_macro['date'] = pd.to_datetime(df_macro['date'])
    print(f"   Macro features: {len(df_macro):,} rows")
    
    # Load FX features
    fx_query = f"""
    SELECT 
        date,
        usd_brl,
        usd_cny,
        usd_jpy,
        eur_usd,
        dxy_broad,
        usd_brl_ret_1d,
        usd_cny_ret_1d,
        dxy_ret_1d,
        dxy_vol_21d,
        dxy_z_60d,
        soy_fx_stress,
        usd_regime
    FROM `{PROJECT_ID}.features.fx_features_daily`
    """
    df_fx = client.query(fx_query).to_dataframe()
    df_fx['date'] = pd.to_datetime(df_fx['date'])
    print(f"   FX features: {len(df_fx):,} rows")
    
    # Load volatility signals
    vol_query = f"""
    SELECT 
        date,
        vix_close,
        hy_spread,
        ig_spread,
        ted_spread,
        yield_curve_slope,
        vix_z_60d,
        z_hy_spread,
        z_ig_spread,
        curve_inversion_flag,
        risk_sentiment_index
    FROM `{PROJECT_ID}.features.volatility_signals`
    """
    df_vol = client.query(vol_query).to_dataframe()
    df_vol['date'] = pd.to_datetime(df_vol['date'])
    print(f"   Vol signals: {len(df_vol):,} rows")
    
    return df_price, df_macro, df_fx, df_vol


def pivot_and_create_features(df_price, df_macro, df_fx, df_vol):
    """Pivot price data and merge with fundamental features."""
    print("🔧 Creating features...")
    
    # Pivot price data: one row per date, columns for each symbol's OHLCV
    dfs = []
    for symbol in SYMBOLS:
        sym_df = df_price[df_price['symbol'] == symbol][['date', 'open', 'high', 'low', 'close', 'volume']].copy()
        sym_df = sym_df.rename(columns={
            'open': f'{symbol}_open',
            'high': f'{symbol}_high', 
            'low': f'{symbol}_low',
            'close': f'{symbol}_close',
            'volume': f'{symbol}_volume'
        })
        dfs.append(sym_df.set_index('date'))
    
    # Join all symbols on date
    wide = dfs[0]
    for d in dfs[1:]:
        wide = wide.join(d, how='outer')
    
    wide = wide.sort_index().reset_index()
    wide = wide.rename(columns={'index': 'date'})
    
    # Forward fill missing values (holidays, gaps)
    wide = wide.ffill()
    
    # ===== PRICE-BASED FEATURES =====
    features = pd.DataFrame({'date': wide['date']})
    
    for symbol in SYMBOLS:
        close = wide[f'{symbol}_close']
        high = wide[f'{symbol}_high']
        low = wide[f'{symbol}_low']
        volume = wide[f'{symbol}_volume']
        
        # Returns
        features[f'{symbol}_ret_1d'] = close.pct_change(1)
        features[f'{symbol}_ret_5d'] = close.pct_change(5)
        features[f'{symbol}_ret_21d'] = close.pct_change(21)
        
        # Moving averages
        features[f'{symbol}_sma_5'] = close.rolling(5).mean()
        features[f'{symbol}_sma_21'] = close.rolling(21).mean()
        features[f'{symbol}_sma_50'] = close.rolling(50).mean()
        
        # Price relative to MAs
        features[f'{symbol}_close_vs_sma5'] = close / features[f'{symbol}_sma_5'] - 1
        features[f'{symbol}_close_vs_sma21'] = close / features[f'{symbol}_sma_21'] - 1
        
        # Volatility
        features[f'{symbol}_vol_5d'] = close.pct_change().rolling(5).std()
        features[f'{symbol}_vol_21d'] = close.pct_change().rolling(21).std()
        
        # Range
        features[f'{symbol}_range'] = (high - low) / close
        features[f'{symbol}_range_5d'] = features[f'{symbol}_range'].rolling(5).mean()
        
        # Volume ratio
        features[f'{symbol}_vol_ratio'] = volume / volume.rolling(21).mean()
    
    # Cross-symbol features (ZL vs related)
    features['zl_vs_zs'] = wide['ZL_close'] / wide['ZS_close']
    features['zl_vs_zm'] = wide['ZL_close'] / wide['ZM_close']
    features['zl_vs_cl'] = wide['ZL_close'] / wide['CL_close']
    features['zl_vs_ho'] = wide['ZL_close'] / wide['HO_close']
    
    # CRUSH MARGIN PROXY (key ZL driver!)
    # Crush = Revenue from products - Cost of beans
    # Simplified: ZL + ZM - ZS (oil + meal - beans)
    features['crush_margin'] = wide['ZL_close'] + wide['ZM_close'] - wide['ZS_close']
    features['crush_margin_5d_chg'] = features['crush_margin'].pct_change(5)
    features['crush_margin_21d_chg'] = features['crush_margin'].pct_change(21)
    features['crush_margin_z'] = (features['crush_margin'] - features['crush_margin'].rolling(63).mean()) / features['crush_margin'].rolling(63).std()
    
    # Energy spread (ZL vs crude - biodiesel economics)
    features['zl_energy_spread'] = wide['ZL_close'] - wide['CL_close'] * 0.01  # Scale crude
    
    # ZL close for targets
    features['ZL_close'] = wide['ZL_close']
    
    print(f"   Price features: {len(features.columns) - 2}")
    
    # ===== MERGE FUNDAMENTAL FEATURES =====
    # Macro features
    features = features.merge(df_macro, on='date', how='left')
    print(f"   + Macro: {len(df_macro.columns) - 1} features")
    
    # FX features (CRITICAL: Dollar strength crushes commodities)
    features = features.merge(df_fx, on='date', how='left')
    print(f"   + FX: {len(df_fx.columns) - 1} features")
    
    # Volatility signals
    features = features.merge(df_vol, on='date', how='left')
    print(f"   + Vol: {len(df_vol.columns) - 1} features")
    
    # Forward fill any gaps from joins
    features = features.ffill()
    
    total_features = len(features.columns) - 2  # Exclude date, ZL_close
    print(f"   TOTAL: {total_features} features")
    
    return features


def create_targets(df, horizons):
    """Create directional targets (up/down classification, not price levels)."""
    print("🎯 Creating targets...")
    
    for name, days in horizons.items():
        # Forward return: (future_close - current_close) / current_close
        forward_ret = df['ZL_close'].shift(-days) / df['ZL_close'] - 1
        
        # DIRECTION TARGET: 1 if up, 0 if down (classification, not regression)
        df[f'target_{name}'] = (forward_ret > 0).astype(int)
        
        # Also store the magnitude for analysis (but don't predict it)
        df[f'target_{name}_magnitude'] = forward_ret
    
    return df


def train_baseline(df, horizon_name, horizon_days):
    """Train LightGBM baseline for a single horizon with proper train/val/test."""
    print(f"\n{'='*60}")
    print(f"Training ZL Baseline: {horizon_name} ({horizon_days} days)")
    print(f"{'='*60}")
    
    target_col = f'target_{horizon_name}'
    
    # Drop rows with null target or features
    df_clean = df.dropna().copy()
    
    # Feature columns (exclude date, ZL_close, all targets, metadata)
    exclude = ['date', 'ZL_close', 'processed_at', 'usd_regime', 'vol_regime'] + [c for c in df_clean.columns if c.startswith('target_')]
    feature_cols = [c for c in df_clean.columns if c not in exclude and df_clean[c].dtype in ['float64', 'float32', 'int64', 'int32', 'bool']]
    
    # Walk-forward split: 70% train, 15% val, 15% test (HOLDOUT)
    df_clean = df_clean.sort_values('date').reset_index(drop=True)
    train_end = int(len(df_clean) * 0.70)
    val_end = int(len(df_clean) * 0.85)
    
    train = df_clean.iloc[:train_end]
    val = df_clean.iloc[train_end:val_end]
    test = df_clean.iloc[val_end:]  # TRUE HOLDOUT - never seen during training
    
    print(f"Train: {len(train):,} rows ({train['date'].min().date()} → {train['date'].max().date()})")
    print(f"Val:   {len(val):,} rows ({val['date'].min().date()} → {val['date'].max().date()})")
    print(f"TEST:  {len(test):,} rows ({test['date'].min().date()} → {test['date'].max().date()}) [HOLDOUT]")
    print(f"Features: {len(feature_cols)}")
    
    X_train = train[feature_cols]
    y_train = train[target_col]
    X_val = val[feature_cols]
    y_val = val[target_col]
    
    # REGIME-AWARE SAMPLE WEIGHTS: exponentially favor recent data
    # This helps model adapt to changing market dynamics
    days_from_end = (train['date'].max() - train['date']).dt.days
    decay_rate = 0.001  # ~2.7x weight for most recent vs 3 years ago
    sample_weights = np.exp(-decay_rate * days_from_end)
    sample_weights = sample_weights / sample_weights.sum() * len(sample_weights)  # Normalize
    print(f"Sample weights: oldest={sample_weights.iloc[0]:.2f}, newest={sample_weights.iloc[-1]:.2f}")
    
    # LightGBM - BINARY CLASSIFICATION (up/down direction)
    params = {
        'objective': 'binary',  # Classification, not regression
        'metric': ['binary_logloss', 'auc'],
        'boosting_type': 'gbdt',
        'num_leaves': 15,  # Smaller = more regularization
        'learning_rate': 0.01,  # Slower learning
        'feature_fraction': 0.6,  # More feature dropout
        'bagging_fraction': 0.7,
        'bagging_freq': 1,
        'min_data_in_leaf': 50,  # Prevent overfitting
        'lambda_l1': 0.1,  # L1 regularization
        'lambda_l2': 1.0,  # L2 regularization
        'verbose': -1,
        'seed': 42,
        'n_jobs': -1,
    }
    
    train_data = lgb.Dataset(X_train, label=y_train, weight=sample_weights)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    print("Training (regularized model)...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=2000,  # More rounds with slower learning
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=[
            lgb.early_stopping(200, verbose=False),  # More patience
            lgb.log_evaluation(200)
        ]
    )
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    # TEST SET PREDICTIONS (true holdout)
    X_test = test[feature_cols]
    y_test = test[target_col]
    y_pred_test = model.predict(X_test)
    
    # Classification metrics (predictions are probabilities, need to threshold at 0.5)
    def calc_metrics(y_true, y_pred_proba):
        y_pred = (y_pred_proba > 0.5).astype(int)
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        try:
            auc = roc_auc_score(y_true, y_pred_proba)
        except:
            auc = 0.5  # If only one class present
        return {'acc': acc, 'precision': prec, 'recall': rec, 'f1': f1, 'auc': auc}
    
    train_metrics = calc_metrics(y_train, y_pred_train)
    val_metrics = calc_metrics(y_val, y_pred_val)
    test_metrics = calc_metrics(y_test, y_pred_test)
    
    print(f"\nTrain: Acc={train_metrics['acc']:.1%}, F1={train_metrics['f1']:.3f}, AUC={train_metrics['auc']:.3f}")
    print(f"Val:   Acc={val_metrics['acc']:.1%}, F1={val_metrics['f1']:.3f}, AUC={val_metrics['auc']:.3f}")
    print(f"🧪 TEST: Acc={test_metrics['acc']:.1%}, F1={test_metrics['f1']:.3f}, AUC={test_metrics['auc']:.3f}")
    
    # Top features
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 10 Features:")
    for i, row in importance.head(10).iterrows():
        print(f"   {row['feature']}: {row['importance']:.0f}")
    
    # Backtest record (explicitly marked experimental)
    dataset_spec = DatasetSpec(
        name=f"zl_{horizon_name}_directional_experiment",
        bq_table="(price + macro + fx + vol feature queries; see quick_zl_baseline.py)",
        symbol="ZL",
        horizon=horizon_name,
        train_start=str(train['date'].min().date()),
        train_end=str(train['date'].max().date()),
        val_start=str(val['date'].min().date()),
        val_end=str(val['date'].max().date()),
        test_start=str(test['date'].min().date()),
        test_end=str(test['date'].max().date()),
    )

    model_spec = ModelSpec(
        name=f"lgb_zl_{horizon_name}_directional_baseline",
        algorithm="lightgbm_binary_classification",
        target_col=target_col,
        feature_cols=feature_cols,
        params=params,
    )

    backtest_result = BacktestResult(
        metrics_train=train_metrics,
        metrics_val=val_metrics,
        metrics_test=test_metrics,
        top_features=importance.head(20).to_dict('records'),
    )

    backtest_run = BacktestRun(
        dataset=dataset_spec,
        model=model_spec,
        result=backtest_result,
        notes="Experimental directional baseline (returns-based target); not production.",
    )

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    backtest_path = EXPERIMENTS_DIR / f"quick_zl_directional_{horizon_name}_backtest.json"
    with open(backtest_path, 'w') as f:
        import json
        json.dump(asdict(backtest_run), f, indent=2)

    return {
        'horizon': horizon_name,
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'test_metrics': test_metrics,
        'best_iteration': model.best_iteration,
        'top_features': importance.head(10)['feature'].tolist()
    }


def main():
    """Run baseline training."""
    print("="*60)
    print("ZL DIRECTIONAL CLASSIFICATION BASELINE")
    print("Target: Up/Down Direction (NOT Price Levels)")
    print("="*60)
    
    # Load data
    df_price, df_macro, df_fx, df_vol = load_data_from_bq()
    
    # Create features
    features = pivot_and_create_features(df_price, df_macro, df_fx, df_vol)
    
    # Create targets
    features = create_targets(features, HORIZONS)
    
    # Train for each horizon
    results = []
    for horizon_name, horizon_days in HORIZONS.items():
        result = train_baseline(features, horizon_name, horizon_days)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("DIRECTIONAL CLASSIFICATION BASELINE - HOLDOUT TEST RESULTS")
    print("="*80)
    print(f"{'Horizon':<10} {'Test Acc':<12} {'Test F1':<12} {'Test AUC':<12} {'Val Acc':<12} {'Iters':<8}")
    print("-"*66)
    for r in results:
        print(f"{r['horizon']:<10} {r['test_metrics']['acc']:<12.1%} {r['test_metrics']['f1']:<12.3f} {r['test_metrics']['auc']:<12.3f} {r['val_metrics']['acc']:<12.1%} {r['best_iteration']:<8}")
    
    print("\n✅ Baseline training complete!")
    return results


if __name__ == "__main__":
    main()
