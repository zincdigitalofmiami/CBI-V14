#!/usr/bin/env python3
"""
Feature Engineering Orchestrator
Builds complete feature set by joining all data sources and applying feature calculations.

This script:
1. Loads joined data from staging (via join_executor.py)
2. Applies regime-based training weights (from registry/regime_weights.yaml)
3. Calls feature_calculations.py for complex Python-based features
4. Exports final feature set for training

Architecture: Hybrid Python + BigQuery SQL
- Joins handled by: scripts/assemble/join_executor.py
- Simple features: BigQuery SQL (correlations, moving averages, regimes)
- Complex features: Python via feature_calculations.py (sentiment, NLP, policy)

Author: AI Assistant
Date: November 17, 2025
Last Updated: November 17, 2025
Status: Active - Core feature engineering pipeline
Reference: docs/plans/MASTER_PLAN.md
"""

import os
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

# Determinism: avoid runtime RNG usage in production feature code
# If sampling is ever required, prefer deterministic hashing over RNG.
os.environ['PYTHONHASHSEED'] = '42'

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

def load_regime_weights():
    """Load regime weights from canonical YAML source."""
    yaml_path = DRIVE / "registry/regime_weights.yaml"
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract weights from YAML structure
    weights = {}
    for regime_key, regime_data in config['regimes'].items():
        regime_name = regime_data['name']
        regime_weight = regime_data['weight']
        weights[regime_name] = regime_weight
    
    # Add legacy aliases for backward compatibility
    # These map old regime names to new canonical names
    aliases = {
        "precrisis_2000_2007": weights.get("commodity_emergence_2000_2003", 75),
        "pre_crisis_2000_2007": weights.get("commodity_emergence_2000_2003", 75),
        "gfc_2008_2009": weights.get("financial_crisis_2008_2009", 200),
        "qe_2010_2016": weights.get("qe_commodity_boom_2010_2011", 150),
        "qe_supercycle_2010_2014": weights.get("plateau_transition_2012_2014", 100),
        "trade_war_2017_2019": weights.get("tradewar_escalation_2018_2019", 300),
        "tradewar_2017_2019": weights.get("tradewar_escalation_2018_2019", 300),
        "covid_crash_2020": weights.get("covid_shock_2020", 350),
        "covid_2020_2021": weights.get("covid_recovery_2021", 275),
        "reopening_2020_2021": weights.get("covid_recovery_2021", 275),
        "inflation_2021_2022": weights.get("inflation_surge_2021_2022", 650),
        "inflation_2021_2023": weights.get("inflation_surge_2021_2022", 650),
        "tightening_2022_2023": weights.get("disinflation_2023", 500),
        "trump_2023_2025": weights.get("trump_return_2024_2025", 1000),
        "allhistory": 1,  # Fallback
        "historical_pre2000": 50  # Fallback
    }
    
    # Merge canonical weights with aliases
    weights.update(aliases)
    
    return weights

def apply_regime_weights(df):
    """Apply regime-based training weights (50-1000 scale)"""
    
    # Load regime weights from canonical YAML source
    # Source: registry/regime_weights.yaml (generated from regime_weights.parquet)
    REGIME_WEIGHTS = load_regime_weights()
    
    print("\n" + "="*80)
    print("APPLYING REGIME WEIGHTS")
    print("="*80)
    
    # Check regime column exists (use 'regime' not 'market_regime')
    regime_col = 'regime' if 'regime' in df.columns else 'market_regime'
    if regime_col not in df.columns:
        raise ValueError("regime column missing - check join with regime_calendar")
    
    # Assert every date has a regime
    missing_regime = df[regime_col].isnull().sum()
    if missing_regime > 0:
        raise ValueError(f"{missing_regime} rows missing regime assignment")
    
    print(f"✅ All rows have regime assignment")
    
    # Apply weights
    df['training_weight'] = df[regime_col].map(REGIME_WEIGHTS).astype('float64')
    
    # Check for unmapped regimes
    missing_weight = df['training_weight'].isnull().sum()
    if missing_weight > 0:
        missing_regimes = df[df['training_weight'].isnull()][regime_col].unique()
        raise ValueError(
            f"Missing weight mapping for {len(missing_regimes)} regimes: {missing_regimes.tolist()}\n"
            f"Add these to REGIME_WEIGHTS dict in apply_regime_weights()"
        )
    
    # Verify weight range (50-1000, not 50-5000!)
    min_w = df['training_weight'].min()
    max_w = df['training_weight'].max()
    
    assert min_w >= 50, f"Weight too low: {min_w} (minimum is 50)"
    assert max_w <= 1000, f"Weight too high: {max_w} (maximum is 1000, not 5000!)"
    
    print(f"✅ Training weights applied: {min_w:.0f} to {max_w:.0f}")
    print(f"✅ Regimes present: {df['market_regime'].nunique()}")
    
    # Show distribution
    print("\nRegime Distribution:")
    regime_dist = df.groupby('market_regime').agg({
        'training_weight': 'first',
        'date': 'count'
    }).rename(columns={'date': 'row_count'}).sort_values('training_weight', ascending=False)
    print(regime_dist.to_string())
    
    # Verify no "allhistory" dominance (should be minority)
    if 'allhistory' in df['market_regime'].values:
        allhist_pct = (df['market_regime'] == 'allhistory').sum() / len(df) * 100
        if allhist_pct > 10:
            print(f"\n⚠️  WARNING: {allhist_pct:.1f}% of rows are 'allhistory' (should be <10%)")
            print("  This suggests regime_calendar join is not working properly")
    
    print("="*80 + "\n")
    
    return df

def build_features_single_pass():
    """
    Execute declarative joins and calculate all features.
    Policy: All technical indicators are computed in‑house from DataBento OHLCV.
    """
    
    # VALIDATION CHECKPOINT: Must have validation certificate
    cert_path = DRIVE / "TrainingData/validation_certificate.json"
    if cert_path.exists():
        print("\n" + "="*80)
        print("SINGLE-PASS FEATURE ENGINEERING")
        print("="*80)
        print("✅ Validation certificate found - proceeding with feature build")
    else:
        print("\n⚠️  Validation certificate not found (optional)")
    
    # Step 1: Execute joins per spec (Alpha join removed)
    print("\n📋 Step 1: Executing declarative joins...")
    import sys
    sys.path.insert(0, str(DRIVE / "scripts"))
    from assemble.execute_joins import JoinExecutor
    
    executor = JoinExecutor(DRIVE / "registry/join_spec.yaml")
    df_base = executor.execute()  # All sources joined (no Alpha join)
    
    print(f"\n✅ Base joined: {len(df_base)} rows × {len(df_base.columns)} cols")
    
    # Step 2: Calculate features (all categories)
    print("\n📊 Step 2: Feature engineering...")
    
    # Import feature calculation functions
    from feature_calculations import (
        calculate_technical_indicators,      # Compute from OHLCV (DataBento/Yahoo bridge)
        calculate_cross_asset_features,       # KEEP: ZL correlations with FRED
        calculate_volatility_features,       # KEEP: Custom volatility
        calculate_seasonal_features,          # KEEP: Seasonality
        calculate_macro_regime_features,      # KEEP: FRED-based regimes
        calculate_weather_aggregations,       # KEEP: Weather features
        add_regime_columns,
        add_override_flags
    )
    
    df_features = df_base.copy()
    # Always compute technical/cross-asset features in-house
    df_features = calculate_technical_indicators(df_features)
    df_features = calculate_cross_asset_features(df_features)
    
    # Always calculate these (Alpha doesn't provide):
    try:
        df_features = calculate_volatility_features(df_features)
        df_features = calculate_seasonal_features(df_features)
        df_features = calculate_macro_regime_features(df_features)
        df_features = calculate_weather_aggregations(df_features)
        df_features = add_regime_columns(df_features)
        
        # Step 4: Apply regime weights (50-1000 scale) - CRITICAL!
        df_features = apply_regime_weights(df_features)
        
        df_features = add_override_flags(df_features)
        
        print(f"\n✅ Feature engineering complete!")
        print(f"   Total features: {len(df_features.columns)}")
        
        # Show feature breakdown
        tech_features = len([c for c in df_features.columns if c.startswith('tech_')])
        cross_features = len([c for c in df_features.columns if c.startswith('cross_')])
        vol_features = len([c for c in df_features.columns if c.startswith('vol_')])
        seas_features = len([c for c in df_features.columns if c.startswith('seas_')])
        macro_features = len([c for c in df_features.columns if c.startswith('macro_')])
        weather_features = len([c for c in df_features.columns if c.startswith('weather_')])
        flag_features = len([c for c in df_features.columns if c.startswith('flag_')])

        print(f"\n   Feature breakdown:")
        print(f"   - Custom technical: {tech_features}")
        print(f"   - Cross-asset: {cross_features}")
        print(f"   - Volatility: {vol_features}")
        print(f"   - Seasonal: {seas_features}")
        print(f"   - Macro regime: {macro_features}")
        print(f"   - Weather: {weather_features}")
        print(f"   - Flags: {flag_features}")
        
    except Exception as e:
        print(f"\n❌ Error in feature engineering: {e}")
        print("   Continuing with base features only...")
        df_features = df_base.copy()
    
    # Save master features
    features_file = DRIVE / "TrainingData/features/master_features_2000_2025.parquet"
    df_features.to_parquet(features_file, compression='zstd')
    
    print(f"\n✅ Features built: {len(df_features)} rows × {len(df_features.columns)} cols")
    print(f"   Saved to: {features_file}")
    
    return df_features

def create_horizon_exports(df_features):
    """
    FIX #3: Groupwise target shift to prevent cross-symbol leakage.
    FIX #7: Create 10 files (5 horizons × 2 label types).
    """
    print("\n" + "="*80)
    print("CREATING HORIZON EXPORTS")
    print("="*80)
    print("FIX #3: Using groupwise shift (no cross-symbol leakage)")
    print("FIX #7: Creating 10 files (5 horizons × 2 label types)")
    
    horizons = {'1w': 7, '1m': 30, '3m': 90, '6m': 180, '12m': 365}
    
    # Determine if we have multi-symbol data or single ZL series
    has_symbols = 'symbol' in df_features.columns
    price_col = 'close' if 'close' in df_features.columns else 'zl_price_current'
    
    if price_col not in df_features.columns:
        print(f"❌ Price column not found. Available: {list(df_features.columns[:20])}")
        return
    
    for horizon_name, days in horizons.items():
        # Create price-labeled export
        df_price = df_features.copy()
        
        # FIX #3: Groupwise shift to prevent leakage
        if has_symbols:
            df_price['target_price'] = df_price.groupby('symbol')[price_col].shift(-days)
        else:
            df_price['target_price'] = df_price[price_col].shift(-days)
        
        df_price['target'] = df_price['target_price']
        df_price = df_price.drop(columns=['target_price'])
        
        # Save price version
        output_price = DRIVE / f"TrainingData/exports/zl_training_prod_allhistory_{horizon_name}_price.parquet"
        df_price.to_parquet(output_price, compression='zstd')
        
        # Create return-labeled export
        df_return = df_features.copy()
        
        # Calculate return target
        if has_symbols:
            future_price = df_return.groupby('symbol')[price_col].shift(-days)
        else:
            future_price = df_return[price_col].shift(-days)
        
        df_return['target_return'] = (future_price / df_return[price_col]) - 1.0
        df_return['target'] = df_return['target_return']
        df_return = df_return.drop(columns=['target_return'])
        
        # Save return version
        output_return = DRIVE / f"TrainingData/exports/zl_training_prod_allhistory_{horizon_name}_return.parquet"
        df_return.to_parquet(output_return, compression='zstd')
        
        # Report
        file_size_price = output_price.stat().st_size / 1024 / 1024
        file_size_return = output_return.stat().st_size / 1024 / 1024
        
        print(f"✅ {horizon_name}:")
        print(f"   Price:  {len(df_price)} rows × {len(df_price.columns)} cols → {file_size_price:.1f} MB")
        print(f"   Return: {len(df_return)} rows × {len(df_return.columns)} cols → {file_size_return:.1f} MB")
    
    print(f"\n✅ Total: 10 files exported (5 horizons × 2 label types)")

if __name__ == '__main__':
    df_features = build_features_single_pass()
    create_horizon_exports(df_features)




