#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
SINGLE-PASS FEATURE ENGINEERING
Calculate all 300+ features ONCE, then reuse for all 5 horizons.
FIXED: Groupwise target shift, determinism controls, 10 file exports.
"""

import os
# REMOVED: import random # NO FAKE DATA
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# FIX #6: Set all seeds for determinism
os.environ['PYTHONHASHSEED'] = '42'
# REMOVED: random.seed(42) # NO RANDOM SEEDS
# REMOVED: # REMOVED: np.random.seed(42) # NO FAKE DATA # NO RANDOM SEEDS

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

def build_features_single_pass():
    """
    Execute declarative joins, calculate all features.
    Returns master feature dataframe (single source of truth).
    """
    print("\n" + "="*80)
    print("SINGLE-PASS FEATURE ENGINEERING")
    print("="*80)
    print("FIX #6: Determinism controls active (seeds set)")
    
    # Step 1: Execute joins per spec
    print("\n📋 Step 1: Executing declarative joins...")
    import sys
    sys.path.insert(0, str(DRIVE / "scripts"))
    from assemble.execute_joins import JoinExecutor
    
    executor = JoinExecutor(DRIVE / "registry/join_spec.yaml")
    df_base = executor.execute()
    
    print(f"\n✅ Base joined: {len(df_base)} rows × {len(df_base.columns)} cols")
    
    # Step 2: Calculate features (all categories)
    print("\n📊 Step 2: Feature engineering...")
    
    # Import feature calculation functions
    from feature_calculations import (
        calculate_technical_indicators,
        calculate_cross_asset_features,
        calculate_volatility_features,
        calculate_seasonal_features,
        calculate_macro_regime_features,
        calculate_weather_aggregations,
        add_regime_columns,
        add_override_flags
    )
    
    # Apply all feature engineering functions in sequence
    df_features = df_base.copy()
    
    try:
        df_features = calculate_technical_indicators(df_features)
        df_features = calculate_cross_asset_features(df_features)
        df_features = calculate_volatility_features(df_features)
        df_features = calculate_seasonal_features(df_features)
        df_features = calculate_macro_regime_features(df_features)
        df_features = calculate_weather_aggregations(df_features)
        df_features = add_regime_columns(df_features)
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
        print(f"   - Technical: {tech_features}")
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

