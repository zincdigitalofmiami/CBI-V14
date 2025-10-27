#!/usr/bin/env python3
"""
Proper Intelligence Feature Engineering
Capture temporal dynamics, decay, regime effects, and interactions
"""

import pandas as pd
import numpy as np

print("="*80)
print("PROPER INTELLIGENCE FEATURE ENGINEERING")
print("="*80)

# Load dataset
df = pd.read_csv('LEAKAGE_FREE_WITH_CRUSH.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"\nOriginal dataset: {len(df)} rows × {len(df.columns)} columns")

# 1. EVENT DECAY FUNCTIONS
print("\n1️⃣ CREATING EVENT DECAY FUNCTIONS")
print("-"*80)

def create_decay_features(df, event_column, decay_windows=[7, 14, 30, 60]):
    """Transform events into decay functions (market memory)"""
    if event_column not in df.columns:
        return df
    
    for window in decay_windows:
        col_name = f'{event_column}_decay_{window}d'
        df[col_name] = 0.0
        
        # Exponential decay
        for i in range(1, len(df)):
            decay_factor = 1 - 1/window
            df.loc[i, col_name] = df.loc[i-1, col_name] * decay_factor + df.loc[i, event_column]
    
    return df

# Apply to tariff events
if 'tariff_mentions' in df.columns:
    df = create_decay_features(df, 'tariff_mentions', [7, 14, 30, 60])
    print(f"  ✅ Tariff decay features: 7d, 14d, 30d, 60d")

# Apply to China mentions
if 'china_mentions' in df.columns:
    df = create_decay_features(df, 'china_mentions', [14, 30, 60])
    print(f"  ✅ China mentions decay: 14d, 30d, 60d")

# Apply to Trump orders
if 'trump_order_mentions' in df.columns:
    df = create_decay_features(df, 'trump_order_mentions', [7, 30])
    print(f"  ✅ Trump order decay: 7d, 30d")

# 2. CUMULATIVE REGIME FEATURES
print("\n2️⃣ CREATING REGIME FEATURES")
print("-"*80)

def create_regime_features(df, event_column, windows=[30, 90, 180]):
    """Track ongoing policy regimes"""
    if event_column not in df.columns:
        return df
    
    for window in windows:
        # Rolling sum (event frequency)
        df[f'{event_column}_sum_{window}d'] = df[event_column].rolling(window, min_periods=1).sum()
        
        # Rolling max (peak intensity)
        df[f'{event_column}_max_{window}d'] = df[event_column].rolling(window, min_periods=1).max()
    
    # Cumulative event count (total regime memory)
    df[f'{event_column}_cumulative'] = df[event_column].cumsum()
    
    return df

if 'tariff_mentions' in df.columns:
    df = create_regime_features(df, 'tariff_mentions', [30, 90, 180])
    print(f"  ✅ Tariff regime: 30d, 90d, 180d windows + cumulative")

if 'china_mentions' in df.columns:
    df = create_regime_features(df, 'china_mentions', [30, 90])
    print(f"  ✅ China regime: 30d, 90d windows + cumulative")

# 3. LAG FEATURES (Past events impact future)
print("\n3️⃣ CREATING LAG FEATURES")
print("-"*80)

def create_lag_features(df, feature_col, lags=[7, 14, 30]):
    """Past values impact future prices"""
    if feature_col not in df.columns:
        return df
    
    for lag in lags:
        df[f'{feature_col}_lag_{lag}d'] = df[feature_col].shift(lag)
    
    return df

# Lag tariff impact
if 'tariff_mentions' in df.columns:
    df = create_lag_features(df, 'tariff_mentions', [7, 14, 21, 30])
    print(f"  ✅ Tariff lags: 7d, 14d, 21d, 30d (captures delayed impact)")

# Lag engagement (attention leads to action)
if 'total_engagement_score' in df.columns:
    df = create_lag_features(df, 'total_engagement_score', [3, 7, 14])
    print(f"  ✅ Engagement lags: 3d, 7d, 14d")

# 4. INTERACTION FEATURES
print("\n4️⃣ CREATING INTERACTION FEATURES")
print("-"*80)

# Tariffs × China demand
if 'tariff_mentions' in df.columns and 'china_mentions' in df.columns:
    df['tariff_china_interaction'] = df['tariff_mentions'] * df['china_mentions']
    print(f"  ✅ tariff_china_interaction")

# Tariffs × Crush spread
if 'tariff_mentions' in df.columns and 'crush_spread_gross' in df.columns:
    df['tariff_crush_interaction'] = df['tariff_mentions'] * df['crush_spread_percentile_365d']
    print(f"  ✅ tariff_crush_interaction (tariffs affect processing economics)")

# China tension × China FX
if 'china_mentions' in df.columns and 'fx_usd_cny' in df.columns:
    df['china_demand_stress'] = df['china_mentions_sum_30d'] * df['fx_usd_cny'] if 'china_mentions_sum_30d' in df.columns else df['china_mentions'] * df['fx_usd_cny']
    print(f"  ✅ china_demand_stress (tension × FX strength)")

# Brazil weather × FX competitiveness
if 'brazil_temperature_c' in df.columns and 'fx_usd_brl' in df.columns:
    # High temp (drought stress) + weak real = export pressure
    df['brazil_export_pressure'] = (df['brazil_temperature_c'] > df['brazil_temperature_c'].quantile(0.75)).astype(int) * df['fx_usd_brl']
    print(f"  ✅ brazil_export_pressure (weather × FX)")

# Argentina FX extreme × seasonal
if 'fx_usd_ars' in df.columns and 'seasonal_index' in df.columns:
    df['argentina_competitiveness'] = df['fx_usd_ars_pct_change'] * df['seasonal_index'] if 'fx_usd_ars_pct_change' in df.columns else 0
    print(f"  ✅ argentina_competitiveness (FX × season)")

# 5. MARKET STATE CONDITIONING
print("\n5️⃣ CREATING CONDITIONAL FEATURES")
print("-"*80)

# High volatility regime
if 'volatility_30d' in df.columns:
    df['high_vol_regime'] = (df['volatility_30d'] > df['volatility_30d'].quantile(0.8)).astype(int)
    
    # Tariff impact amplified in high vol
    if 'tariff_mentions' in df.columns:
        df['tariff_in_crisis'] = df['tariff_mentions'] * df['high_vol_regime']
        print(f"  ✅ tariff_in_crisis (policy shocks amplified in volatility)")
    
    print(f"  ✅ high_vol_regime (80th percentile threshold)")

# Correlation regime (when correlations break)
if 'corr_zl_crude_30d' in df.columns:
    df['correlation_breakdown'] = (abs(df['corr_zl_crude_30d']) < 0.3).astype(int)
    
    # In breakdown regimes, fundamentals matter more
    if 'crush_spread_momentum_7d' in df.columns:
        df['fundamentals_matter'] = df['correlation_breakdown'] * abs(df['crush_spread_momentum_7d'])
        print(f"  ✅ fundamentals_matter (when correlations break, crush spread matters more)")

# 6. TEMPORAL MOMENTUM FEATURES
print("\n6️⃣ CREATING TEMPORAL MOMENTUM")
print("-"*80)

# Tariff escalation velocity
if 'tariff_mentions_sum_30d' in df.columns:
    df['tariff_escalation'] = df['tariff_mentions_sum_30d'].diff(7)
    print(f"  ✅ tariff_escalation (is policy intensifying?)")

# Engagement acceleration
if 'total_engagement_score' in df.columns:
    df['social_attention_surge'] = df['total_engagement_score'].diff(3) > df['total_engagement_score'].rolling(30).std()
    df['social_attention_surge'] = df['social_attention_surge'].astype(int)
    print(f"  ✅ social_attention_surge (sudden attention spikes)")

# Count new features
initial_cols = pd.read_csv('LEAKAGE_FREE_WITH_CRUSH.csv').shape[1]
new_features = df.shape[1] - initial_cols

print("\n" + "="*80)
print("FEATURE ENGINEERING COMPLETE")
print("="*80)

print(f"\n📊 Summary:")
print(f"  Original features: {initial_cols}")
print(f"  New intelligence features: {new_features}")
print(f"  Total features: {df.shape[1]}")

# List new feature types
new_feat_types = {
    'Decay': len([c for c in df.columns if '_decay_' in c]),
    'Regime Sum': len([c for c in df.columns if '_sum_' in c and 'd' in c]),
    'Regime Max': len([c for c in df.columns if '_max_' in c and 'd' in c]),
    'Cumulative': len([c for c in df.columns if '_cumulative' in c]),
    'Lag': len([c for c in df.columns if '_lag_' in c and c not in pd.read_csv('LEAKAGE_FREE_WITH_CRUSH.csv').columns]),
    'Interaction': len([c for c in df.columns if '_interaction' in c or '_stress' in c or '_pressure' in c or '_competitiveness' in c]),
    'Conditional': len([c for c in df.columns if '_regime' in c or '_crisis' in c or '_breakdown' in c or '_matter' in c or '_surge' in c]),
}

for feat_type, count in new_feat_types.items():
    if count > 0:
        print(f"  • {feat_type:20} {count:3d} features")

# Save
df.to_csv('FINAL_ENGINEERED_DATASET.csv', index=False)

print(f"\n💾 Saved: FINAL_ENGINEERED_DATASET.csv")
print(f"   Shape: {df.shape}")

print(f"\n✅ Intelligence features now capture:")
print(f"   • Temporal decay (events fade over time)")
print(f"   • Regime persistence (ongoing policy environment)")
print(f"   • Lagged effects (events → delayed price impact)")
print(f"   • Interactions (tariffs × China, tariffs × crush, FX × weather)")
print(f"   • Conditional effects (policy impact varies by vol regime)")

print(f"\n🎯 Ready to retrain with properly engineered intelligence features")

