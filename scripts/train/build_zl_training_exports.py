#!/usr/bin/env python3
"""
Build ZL Training Exports - Price Level Targets
================================================
Creates per-horizon training exports for ZL (Soybean Oil Futures).

Target Definition (Price Level):
- target_zl_1w:  Future price 5 trading days forward (shift(-5))
- target_zl_1m:  Future price 20 trading days forward (shift(-20))
- target_zl_3m:  Future price 60 trading days forward (shift(-60))
- target_zl_6m:  Future price 120 trading days forward (shift(-120))
- target_zl_12m: Future price 240 trading days forward (shift(-240))

Inputs:
- TrainingData/features/master_features_2000_2025.parquet (or execute joins first)
- registry/regime_calendar.parquet

Outputs:
- TrainingData/exports/zl_training_prod_allhistory_{horizon}.parquet

Author: CBI-V14 System
Date: November 25, 2025
"""

import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")
REPO = Path("/Users/zincdigital/CBI-V14")
STAGING = DRIVE / "staging"
FEATURES = DRIVE / "features"
EXPORTS = DRIVE / "exports"
REGISTRY = REPO / "registry"

# Horizon definitions (trading days)
HORIZONS = {
    '1w': 5,
    '1m': 20,
    '3m': 60,
    '6m': 120,
    '12m': 240
}

# Price column to use for targets
PRICE_COL = 'databento_zl_close'  # Primary: DataBento
FALLBACK_PRICE_COLS = ['yahoo_close', 'zl_close', 'close']  # Fallbacks


def load_master_features() -> pd.DataFrame:
    """Load master features table."""
    master_path = FEATURES / "master_features_2000_2025.parquet"
    
    if not master_path.exists():
        logger.warning(f"Master features not found at {master_path}")
        logger.info("Attempting to load from staging and execute joins...")
        return None
    
    logger.info(f"Loading master features from {master_path}")
    df = pd.read_parquet(master_path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} columns")
    return df


def load_regime_calendar() -> pd.DataFrame:
    """Load regime calendar with training weights."""
    regime_path = REGISTRY / "regime_calendar.parquet"
    
    if not regime_path.exists():
        logger.error(f"Regime calendar not found at {regime_path}")
        return None
    
    logger.info(f"Loading regime calendar from {regime_path}")
    df = pd.read_parquet(regime_path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"Loaded {len(df):,} regime assignments across {df['regime'].nunique()} regimes")
    return df


def find_price_column(df: pd.DataFrame) -> str:
    """Find the appropriate price column for targets."""
    if PRICE_COL in df.columns:
        return PRICE_COL
    
    for col in FALLBACK_PRICE_COLS:
        if col in df.columns:
            logger.warning(f"Primary price column '{PRICE_COL}' not found, using fallback '{col}'")
            return col
    
    # Search for any close price column
    close_cols = [c for c in df.columns if 'close' in c.lower()]
    if close_cols:
        logger.warning(f"Using discovered close column: '{close_cols[0]}'")
        return close_cols[0]
    
    raise ValueError("No price column found for target calculation")


def add_targets(df: pd.DataFrame, price_col: str) -> pd.DataFrame:
    """Add all horizon targets to dataframe."""
    logger.info("Adding target columns...")
    df = df.sort_values('date').reset_index(drop=True)
    
    for horizon, days in HORIZONS.items():
        target_col = f'target_zl_{horizon}'
        # Price level: future price at horizon (shift negative = look forward)
        df[target_col] = df[price_col].shift(-days)
        non_null = df[target_col].notna().sum()
        logger.info(f"  {target_col}: {non_null:,} non-null values (shift -{days} days)")
    
    return df


def export_horizon(df: pd.DataFrame, horizon: str, price_col: str) -> dict:
    """Export training data for a single horizon."""
    target_col = f'target_zl_{horizon}'
    days = HORIZONS[horizon]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Exporting horizon: {horizon} ({days} trading days)")
    
    # Copy and filter to rows with valid target
    export_df = df.copy()
    valid_mask = export_df[target_col].notna()
    export_df = export_df[valid_mask].reset_index(drop=True)
    
    logger.info(f"  Rows with valid target: {len(export_df):,}")
    
    if len(export_df) == 0:
        logger.error(f"  No valid rows for horizon {horizon}!")
        return None
    
    # Keep only this horizon's target (drop other targets)
    other_targets = [f'target_zl_{h}' for h in HORIZONS if h != horizon]
    export_df = export_df.drop(columns=[c for c in other_targets if c in export_df.columns], errors='ignore')
    
    # Add metadata
    export_df['horizon'] = horizon
    export_df['horizon_days'] = days
    export_df['as_of_date'] = datetime.now().strftime('%Y-%m-%d')
    export_df['price_col_used'] = price_col
    
    # Export
    EXPORTS.mkdir(parents=True, exist_ok=True)
    output_path = EXPORTS / f"zl_training_prod_allhistory_{horizon}.parquet"
    export_df.to_parquet(output_path, index=False)
    
    # Stats
    stats = {
        'horizon': horizon,
        'days': days,
        'rows': len(export_df),
        'columns': len(export_df.columns),
        'date_min': export_df['date'].min().strftime('%Y-%m-%d'),
        'date_max': export_df['date'].max().strftime('%Y-%m-%d'),
        'target_min': export_df[target_col].min(),
        'target_max': export_df[target_col].max(),
        'target_mean': export_df[target_col].mean(),
        'output_path': str(output_path)
    }
    
    logger.info(f"  ✅ Saved to: {output_path}")
    logger.info(f"  Rows: {stats['rows']:,}, Columns: {stats['columns']}")
    logger.info(f"  Date range: {stats['date_min']} to {stats['date_max']}")
    logger.info(f"  Target range: {stats['target_min']:.2f} to {stats['target_max']:.2f}")
    
    # Check for regime and weight columns
    if 'regime' in export_df.columns:
        regimes = export_df['regime'].nunique()
        logger.info(f"  Regimes: {regimes}")
    else:
        logger.warning(f"  ⚠️ No 'regime' column found")
    
    if 'training_weight' in export_df.columns:
        weight_range = f"{export_df['training_weight'].min():.0f} to {export_df['training_weight'].max():.0f}"
        logger.info(f"  Training weights: {weight_range}")
    else:
        logger.warning(f"  ⚠️ No 'training_weight' column found")
    
    return stats


def build_from_staging() -> pd.DataFrame:
    """
    Build master features from staging files if master_features doesn't exist.
    This is a simplified version - full pipeline uses execute_joins.py
    """
    logger.info("Building master features from staging files...")
    
    # Start with base prices
    base_files = [
        'yahoo_historical_prefixed.parquet',
        'yahoo_historical_all_symbols.parquet',
        'databento_futures_daily.parquet'
    ]
    
    df = None
    for fname in base_files:
        fpath = STAGING / fname
        if fpath.exists():
            logger.info(f"Loading base: {fname}")
            df = pd.read_parquet(fpath)
            df['date'] = pd.to_datetime(df['date'])
            break
    
    if df is None:
        logger.error("No base price file found in staging!")
        return None
    
    logger.info(f"Base loaded: {len(df):,} rows × {len(df.columns)} columns")
    
    # Join regime calendar
    regime_df = load_regime_calendar()
    if regime_df is not None:
        df = df.merge(regime_df, on='date', how='left')
        logger.info(f"After regime join: {len(df):,} rows × {len(df.columns)} columns")
    
    # Join other staging files
    staging_files = [
        ('fred_macro_expanded.parquet', ['date']),
        ('weather_granular.parquet', ['date']),
        ('cftc_commitments.parquet', ['date']),
        ('usda_reports_granular.parquet', ['date']),
        ('eia_energy_granular.parquet', ['date']),
        ('palm_oil_daily.parquet', ['date']),
        ('volatility_features.parquet', ['date']),
        ('policy_trump_signals.parquet', ['date']),
    ]
    
    for fname, join_keys in staging_files:
        fpath = STAGING / fname
        if fpath.exists():
            try:
                right_df = pd.read_parquet(fpath)
                right_df['date'] = pd.to_datetime(right_df['date'])
                # Only join columns not already in df
                new_cols = [c for c in right_df.columns if c not in df.columns or c in join_keys]
                if len(new_cols) > len(join_keys):
                    df = df.merge(right_df[new_cols], on=join_keys, how='left')
                    logger.info(f"  Joined {fname}: +{len(new_cols) - len(join_keys)} columns")
            except Exception as e:
                logger.warning(f"  Failed to join {fname}: {e}")
    
    logger.info(f"Final features: {len(df):,} rows × {len(df.columns)} columns")
    
    # Forward fill for sparse data
    df = df.sort_values('date')
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64'] and col != 'date':
            null_before = df[col].isnull().sum()
            if null_before > 0 and null_before < len(df) * 0.95:
                df[col] = df[col].ffill()
    
    return df


def main():
    """Main execution."""
    logger.info("="*60)
    logger.info("ZL Training Export Builder")
    logger.info("="*60)
    
    # Load master features
    df = load_master_features()
    
    if df is None:
        logger.info("Master features not found, building from staging...")
        df = build_from_staging()
    
    if df is None:
        logger.error("Failed to load or build features!")
        return
    
    # Find price column
    price_col = find_price_column(df)
    logger.info(f"Using price column: {price_col}")
    
    # Verify price data
    null_prices = df[price_col].isnull().sum()
    if null_prices > 0:
        logger.warning(f"Price column has {null_prices:,} null values ({null_prices/len(df)*100:.1f}%)")
        df = df.dropna(subset=[price_col])
        logger.info(f"After dropping null prices: {len(df):,} rows")
    
    # Add targets
    df = add_targets(df, price_col)
    
    # Export each horizon
    all_stats = []
    for horizon in HORIZONS:
        stats = export_horizon(df, horizon, price_col)
        if stats:
            all_stats.append(stats)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("EXPORT SUMMARY")
    logger.info("="*60)
    for stats in all_stats:
        logger.info(f"  {stats['horizon']}: {stats['rows']:,} rows, {stats['date_min']} to {stats['date_max']}")
    
    logger.info("\n✅ All exports complete!")
    return all_stats


if __name__ == "__main__":
    main()




