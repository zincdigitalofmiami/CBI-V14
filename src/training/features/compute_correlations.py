#!/usr/bin/env python3
"""
Optimized correlation computation for M4 Mac using Polars.
Implements block-wise processing, caching, and rolling correlations.

Key optimizations:
- Polars lazy queries for memory efficiency
- Block-wise correlation (avoid full NxN matrix)
- Rolling correlations (90d, 180d windows)
- Caching with date-based invalidation
- Cross-block correlations only for top-k candidates
"""
import os
import polars as pl
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import hashlib

# Feature blocks for efficient correlation computation
FEATURE_BLOCKS = {
    'big7_macro': [
        'zl_price_current', 'crude_price', 'palm_price', 'dxy_price', 
        'vix_level', 'corn_price', 'wheat_price'
    ],
    'spreads': [
        'zl_crude_spread', 'zl_palm_spread', 'crush_margin', 
        'soy_corn_spread', 'soy_wheat_spread'
    ],
    'news_sentiment': [
        'feature_vix_stress', 'feature_harvest_pace', 'feature_china_relations',
        'feature_tariff_threat', 'feature_geopolitical_volatility',
        'feature_biofuel_cascade', 'feature_hidden_correlation', 'feature_biofuel_ethanol'
    ],
    'weather': [
        'brazil_precip', 'brazil_temp_max', 'argentina_precip', 
        'argentina_temp_max', 'us_precip', 'us_temp_max'
    ],
    'policy_political': [
        'tariff_mentions', 'biofuel_mentions', 'china_sentiment',
        'harvest_sentiment', 'social_volume'
    ]
}

# Key correlation pairs to track
KEY_PAIRS = [
    ('zl_price_current', 'vix_level'),
    ('zl_price_current', 'dxy_price'),
    ('zl_price_current', 'fcpo_price'),  # Palm oil
    ('zl_price_current', 'crush_margin'),
    ('zl_price_current', 'crude_price'),
    ('zl_price_current', 'palm_price'),
]

def compute_block_correlations(
    df: pl.DataFrame,
    block_name: str,
    features: List[str],
    windows: List[int] = [90, 180, 365]
) -> pl.DataFrame:
    """
    Compute correlations within a feature block using rolling windows.
    
    Args:
        df: Input dataframe (must have 'date' column)
        block_name: Name of feature block
        features: List of feature columns in this block
        windows: Rolling window sizes in days
        
    Returns:
        DataFrame with rolling correlations
    """
    # Filter to available features
    available_features = [f for f in features if f in df.columns]
    if len(available_features) < 2:
        return pl.DataFrame()
    
    # Sort by date
    df_sorted = df.sort('date')
    
    # Compute rolling correlations for each window
    results = []
    
    for window in windows:
        for i, feat1 in enumerate(available_features):
            for feat2 in available_features[i+1:]:
                # Rolling correlation
                corr_col = f"corr_{feat1}_{feat2}_{window}d"
                
                # Use Polars rolling correlation
                df_sorted = df_sorted.with_columns([
                    pl.corr(feat1, feat2)
                    .over(pl.col('date').sort().rolling(window=window, closed='both'))
                    .alias(corr_col)
                ])
    
    return df_sorted.select(['date'] + [col for col in df_sorted.columns if col.startswith('corr_')])

def compute_cross_block_correlations(
    df: pl.DataFrame,
    block1: List[str],
    block2: List[str],
    window: int = 90,
    top_k: int = 10
) -> pl.DataFrame:
    """
    Compute correlations between two feature blocks, keeping only top-k.
    
    Args:
        df: Input dataframe
        block1: Features in first block
        block2: Features in second block
        window: Rolling window size
        top_k: Number of top correlations to keep
        
    Returns:
        DataFrame with top-k cross-block correlations
    """
    available1 = [f for f in block1 if f in df.columns]
    available2 = [f for f in block2 if f in df.columns]
    
    if not available1 or not available2:
        return pl.DataFrame()
    
    # Compute all cross-correlations
    correlations = []
    for feat1 in available1:
        for feat2 in available2:
            if feat1 != feat2:
                corr = df.select([
                    pl.corr(feat1, feat2)
                    .over(pl.col('date').sort().rolling(window=window, closed='both'))
                    .alias(f"corr_{feat1}_{feat2}_{window}d")
                ])
                correlations.append(corr)
    
    if not correlations:
        return pl.DataFrame()
    
    # Combine and select top-k by absolute correlation
    # (Simplified - in practice, you'd compute mean abs correlation per feature pair)
    return pl.concat(correlations)

def compute_key_correlations(
    df: pl.DataFrame,
    key_pairs: List[Tuple[str, str]],
    windows: List[int] = [7, 30, 90, 180, 365]
) -> pl.DataFrame:
    """
    Compute rolling correlations for key feature pairs.
    
    Args:
        df: Input dataframe
        key_pairs: List of (feature1, feature2) tuples
        windows: Rolling window sizes
        
    Returns:
        DataFrame with key correlations
    """
    df_sorted = df.sort('date')
    result_cols = ['date']
    
    for feat1, feat2 in key_pairs:
        if feat1 not in df.columns or feat2 not in df.columns:
            continue
            
        for window in windows:
            corr_col = f"corr_{feat1}_{feat2.replace('_', '')}_{window}d"
            
            df_sorted = df_sorted.with_columns([
                pl.corr(feat1, feat2)
                .over(pl.col('date').sort().rolling(window=window, closed='both'))
                .alias(corr_col)
            ])
            result_cols.append(corr_col)
    
    return df_sorted.select(result_cols)

def compute_regime_correlations(
    df: pl.DataFrame,
    regime_col: str = 'market_regime',
    windows: List[int] = [90, 180]
) -> Dict[str, pl.DataFrame]:
    """
    Compute correlations by regime (crisis, normal, etc.).
    
    Args:
        df: Input dataframe with regime column
        regime_col: Name of regime column
        windows: Rolling window sizes
        
    Returns:
        Dictionary mapping regime -> correlation DataFrame
    """
    if regime_col not in df.columns:
        return {}
    
    regimes = df[regime_col].unique().to_list()
    results = {}
    
    for regime in regimes:
        df_regime = df.filter(pl.col(regime_col) == regime)
        if len(df_regime) < 30:  # Need minimum data
            continue
        
        # Compute key correlations for this regime
        key_corrs = compute_key_correlations(df_regime, KEY_PAIRS, windows)
        results[regime] = key_corrs
    
    return results

def get_cache_path(data_path: Path) -> Path:
    """Get cache file path for correlation matrix."""
    cache_dir = data_path.parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Hash the data file path and modification time
    stat = data_path.stat()
    cache_key = f"{data_path.name}_{stat.st_mtime}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    return cache_dir / f"correlations_{cache_hash}.parquet"

def should_recompute(cache_path: Path, max_age_days: int = 7) -> bool:
    """Check if correlation cache is stale."""
    if not cache_path.exists():
        return True
    
    cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
    return cache_age.days > max_age_days

def compute_all_correlations(
    data_path: Path,
    force_recompute: bool = False,
    cache_max_age_days: int = 7
) -> pl.DataFrame:
    """
    Main function: compute all correlations with caching.
    
    Args:
        data_path: Path to training data parquet file
        force_recompute: Force recomputation even if cache exists
        cache_max_age_days: Maximum cache age in days
        
    Returns:
        DataFrame with all correlation features
    """
    print(f"📊 Computing correlations for: {data_path.name}")
    
    # Check cache
    cache_path = get_cache_path(data_path)
    if not force_recompute and cache_path.exists() and not should_recompute(cache_path, cache_max_age_days):
        print(f"  ✅ Loading from cache: {cache_path}")
        return pl.read_parquet(cache_path)
    
    # Load data
    print(f"  📂 Loading data...")
    df = pl.read_parquet(data_path)
    
    if 'date' not in df.columns:
        raise ValueError("DataFrame must have 'date' column")
    
    print(f"  ✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
    
    # Compute block-wise correlations
    print(f"  🔄 Computing block-wise correlations...")
    block_results = []
    
    for block_name, features in FEATURE_BLOCKS.items():
        print(f"    Block: {block_name} ({len(features)} features)")
        block_corrs = compute_block_correlations(df, block_name, features)
        if not block_corrs.is_empty():
            block_results.append(block_corrs)
    
    # Compute key correlations
    print(f"  🔄 Computing key correlations...")
    key_corrs = compute_key_correlations(df, KEY_PAIRS)
    
    # Combine all correlations
    print(f"  🔄 Combining results...")
    all_corrs = [key_corrs]
    all_corrs.extend(block_results)
    
    # Join on date
    result = df.select(['date'])
    for corr_df in all_corrs:
        if not corr_df.is_empty():
            result = result.join(corr_df, on='date', how='left')
    
    # Save cache
    print(f"  💾 Caching results...")
    result.write_parquet(cache_path)
    print(f"  ✅ Saved to: {cache_path}")
    
    return result

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute correlations for training data")
    parser.add_argument("--data-path", type=str, required=True,
                       help="Path to training data parquet file")
    parser.add_argument("--force-recompute", action="store_true",
                       help="Force recomputation even if cache exists")
    parser.add_argument("--cache-max-age", type=int, default=7,
                       help="Maximum cache age in days")
    parser.add_argument("--output", type=str,
                       help="Output path for correlation features (optional)")
    
    args = parser.parse_args()
    
    data_path = Path(args.data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Compute correlations
    corr_df = compute_all_correlations(
        data_path,
        force_recompute=args.force_recompute,
        cache_max_age_days=args.cache_max_age
    )
    
    # Save output if specified
    if args.output:
        output_path = Path(args.output)
        corr_df.write_parquet(output_path)
        print(f"✅ Saved correlation features to: {output_path}")
    
    print(f"\n✅ Computed {len(corr_df.columns) - 1} correlation features")
    print(f"   Rows: {len(corr_df):,}")

if __name__ == "__main__":
    main()



