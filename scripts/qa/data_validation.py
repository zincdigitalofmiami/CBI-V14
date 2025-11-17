#!/usr/bin/env python3
"""
Data validation functions for 25-year data enrichment plan.
Includes Fed Funds basis point validation and VIX floor checks.

Author: AI Assistant
Date: November 16, 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")


def validate_jumps_bps(df, col, threshold_bps=50, sigma=4, lookback=60, verbose=True):
    """
    Flag extreme jumps using volatility-aware rules (rolling z-score > 4σ).
    Prevents false positives from legitimate volatility spikes (VIX, Fed Funds).
    
    Uses instrument-specific thresholds:
    - Rate columns: basis points with volatility-aware threshold
    - Price columns: percentage with volatility-aware threshold
    - VIX: higher threshold (volatility can spike legitimately)
    
    Args:
        df: DataFrame with the column to validate
        col: Column name to check
        threshold_bps: Base threshold in basis points for rate columns (default 50)
        sigma: Number of standard deviations for volatility-aware threshold (default 4)
        lookback: Rolling window for volatility calculation (default 60 days)
        verbose: Whether to print results
        
    Returns:
        tuple: (clean_df, quarantine_df)
            - clean_df: DataFrame without flagged jumps
            - quarantine_df: DataFrame with flagged jumps
    """
    if col not in df.columns:
        if verbose:
            print(f"⚠️ Column {col} not found in DataFrame")
        return df, pd.DataFrame()
    
    # Make a copy and ensure sorted by date
    df = df.copy()
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    # Determine if this is a rate column
    rate_columns = ['fed_funds_rate', 'treasury_10y', 'treasury_2y', 
                    'libor_3m', 'sofr', 'prime_rate', 'mortgage_rate_30y']
    
    # Special handling for VIX (higher volatility expected)
    is_vix = 'vix' in col.lower()
    
    if col in rate_columns or 'rate' in col.lower() or 'yield' in col.lower():
        # Rate column: use basis points with volatility-aware threshold
        if verbose:
            print(f"Validating {col} as rate column (volatility-aware, σ={sigma})")
        
        # Calculate returns (basis points)
        returns = df[col].diff() * 100  # Convert to basis points
        
        # Calculate rolling volatility
        rolling_std = returns.rolling(window=lookback, min_periods=lookback//2).std()
        
        # Dynamic threshold: base threshold OR 4σ, whichever is higher
        dynamic_threshold = np.maximum(
            threshold_bps,
            rolling_std * sigma
        )
        
        # Flag extreme moves
        mask = returns.abs() > dynamic_threshold.fillna(np.inf)
        
        if verbose and mask.sum() > 0:
            print(f"  Found {mask.sum()} extreme jumps (>{sigma}σ or >{threshold_bps}bps)")
            print(f"  Max jump: {returns.abs().max():.1f} bps")
            print(f"  Max threshold: {dynamic_threshold.max():.1f} bps")
    
    elif is_vix:
        # VIX: Use percentage with higher volatility tolerance
        if verbose:
            print(f"Validating {col} as VIX (volatility-aware, σ={sigma}, higher tolerance)")
        
        # Calculate returns (percentage)
        returns = df[col].pct_change()
        
        # Calculate rolling volatility
        rolling_std = returns.rolling(window=lookback, min_periods=lookback//2).std()
        
        # Dynamic threshold: 4σ (VIX can spike legitimately)
        dynamic_threshold = rolling_std * sigma
        
        # Flag extreme moves
        mask = returns.abs() > dynamic_threshold.fillna(np.inf)
        
        if verbose and mask.sum() > 0:
            print(f"  Found {mask.sum()} extreme VIX moves (>{sigma}σ)")
            print(f"  Max move: {returns.abs().max()*100:.1f}%")
            print(f"  Max threshold: {dynamic_threshold.max()*100:.1f}%")
    
    else:
        # Price column: use percentage with volatility-aware threshold
        if verbose:
            print(f"Validating {col} as price column (volatility-aware, σ={sigma})")
        
        # Calculate returns (percentage)
        returns = df[col].pct_change()
        
        # Calculate rolling volatility
        rolling_std = returns.rolling(window=lookback, min_periods=lookback//2).std()
        
        # Dynamic threshold: 4σ (prevents false positives from normal volatility)
        dynamic_threshold = rolling_std * sigma
        
        # Flag extreme moves
        mask = returns.abs() > dynamic_threshold.fillna(np.inf)
        
        if verbose and mask.sum() > 0:
            print(f"  Found {mask.sum()} extreme price moves (>{sigma}σ)")
            print(f"  Max move: {returns.abs().max()*100:.1f}%")
            print(f"  Max threshold: {dynamic_threshold.max()*100:.1f}%")
    
    # Split into clean and quarantine
    clean_df = df[~mask]
    quarantine_df = df[mask]
    
    if verbose:
        print(f"  Clean rows: {len(clean_df):,} ({len(clean_df)/len(df)*100:.1f}%)")
        print(f"  Quarantined rows: {len(quarantine_df):,} ({len(quarantine_df)/len(df)*100:.1f}%)")
    
    return clean_df, quarantine_df


def validate_vix_floor(df, vix_col=None, floor=0.0, verbose=True):
    """
    Ensure VIX values are non-negative.
    Flag any negative VIX values for quarantine.
    
    Args:
        df: DataFrame with VIX data
        vix_col: VIX column name (auto-detects if None)
        floor: Minimum allowed VIX value (default 0.0)
        verbose: Whether to print results
        
    Returns:
        tuple: (clean_df, quarantine_df)
            - clean_df: DataFrame without negative VIX
            - quarantine_df: DataFrame with negative VIX
    """
    # Auto-detect VIX column if not specified
    if vix_col is None:
        vix_candidates = ['vix', 'vix_close', 'vix_level', 'vol_vix_level']
        for candidate in vix_candidates:
            if candidate in df.columns:
                vix_col = candidate
                break
    
    if vix_col is None or vix_col not in df.columns:
        if verbose:
            print("⚠️ No VIX column found in DataFrame")
        return df, pd.DataFrame()
    
    # Make a copy
    df = df.copy()
    
    if verbose:
        print(f"Validating VIX floor for column: {vix_col}")
    
    # Check for values below floor
    mask = df[vix_col] < floor
    
    if mask.sum() > 0:
        if verbose:
            print(f"  ⚠️ Found {mask.sum()} VIX values below {floor}")
            print(f"  Min VIX value: {df[vix_col].min():.2f}")
            
            # Show examples
            negative_examples = df[mask].head(3)
            for idx in negative_examples.index:
                print(f"    {df.loc[idx, 'date']}: VIX = {df.loc[idx, vix_col]:.2f}")
    else:
        if verbose:
            print(f"  ✅ All VIX values >= {floor}")
    
    # Also check for unreasonably high VIX values
    vix_ceiling = 100.0
    high_mask = df[vix_col] > vix_ceiling
    
    if high_mask.sum() > 0 and verbose:
        print(f"  ⚠️ Found {high_mask.sum()} VIX values above {vix_ceiling}")
        print(f"  Max VIX value: {df[vix_col].max():.2f}")
    
    # Combine masks for quarantine
    quarantine_mask = mask | high_mask
    
    # Split data
    clean_df = df[~quarantine_mask]
    quarantine_df = df[quarantine_mask]
    
    if verbose:
        print(f"  Clean rows: {len(clean_df):,}")
        print(f"  Quarantined rows: {len(quarantine_df):,}")
    
    return clean_df, quarantine_df


def validate_all_columns(df, verbose=True):
    """
    Run all validation checks on relevant columns.
    
    Args:
        df: DataFrame to validate
        verbose: Whether to print results
        
    Returns:
        dict: Validation results with clean and quarantine DataFrames
    """
    if verbose:
        print("\n" + "="*80)
        print("RUNNING DATA VALIDATION")
        print("="*80)
        print(f"Input rows: {len(df):,}")
    
    # Track quarantined indices
    quarantine_indices = set()
    validation_results = {}
    
    # 1. Validate rate columns for basis point jumps
    rate_columns = ['fed_funds_rate', 'treasury_10y', 'treasury_2y', 
                    'libor_3m', 'sofr', 'prime_rate']
    
    for col in rate_columns:
        if col in df.columns:
            if verbose:
                print(f"\n📊 Checking {col}...")
            clean_df, quarantine_df = validate_jumps_bps(df, col, threshold_bps=50, verbose=verbose)
            quarantine_indices.update(quarantine_df.index)
            validation_results[f'{col}_jumps'] = len(quarantine_df)
    
    # 2. Validate VIX floor
    if verbose:
        print("\n📊 Checking VIX floor...")
    clean_df, quarantine_df = validate_vix_floor(df, verbose=verbose)
    quarantine_indices.update(quarantine_df.index)
    validation_results['vix_floor_violations'] = len(quarantine_df)
    
    # 3. Validate price columns for percentage jumps
    price_columns = ['zl_price_current', 'close', 'price', 'palm_oil_price', 
                     'crude_oil_price', 'corn_price', 'wheat_price']
    
    for col in price_columns:
        if col in df.columns:
            if verbose:
                print(f"\n📊 Checking {col}...")
            clean_df, quarantine_df = validate_jumps_bps(df, col, verbose=False)
            if len(quarantine_df) > 0 and verbose:
                print(f"  Found {len(quarantine_df)} extreme price jumps (>30%)")
            quarantine_indices.update(quarantine_df.index)
            validation_results[f'{col}_jumps'] = len(quarantine_df)
    
    # Create final clean and quarantine DataFrames
    clean_df = df[~df.index.isin(quarantine_indices)]
    quarantine_df = df[df.index.isin(quarantine_indices)]
    
    if verbose:
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"Total rows: {len(df):,}")
        print(f"Clean rows: {len(clean_df):,} ({len(clean_df)/len(df)*100:.1f}%)")
        print(f"Quarantined rows: {len(quarantine_df):,} ({len(quarantine_df)/len(df)*100:.1f}%)")
        
        if len(quarantine_df) > 0:
            print("\nQuarantine reasons:")
            for key, count in validation_results.items():
                if count > 0:
                    print(f"  - {key}: {count} rows")
    
    return {
        'clean_df': clean_df,
        'quarantine_df': quarantine_df,
        'validation_results': validation_results,
        'quarantine_rate': len(quarantine_df) / len(df) if len(df) > 0 else 0
    }


def save_validation_results(clean_df, quarantine_df, source_name, output_dir=None):
    """
    Save validated data to staging and quarantine directories.
    
    Args:
        clean_df: Clean DataFrame
        quarantine_df: Quarantined DataFrame
        source_name: Name for the output files
        output_dir: Output directory (defaults to DRIVE/staging)
    """
    if output_dir is None:
        output_dir = DRIVE
    else:
        output_dir = Path(output_dir)
    
    # Create directories if needed
    staging_dir = output_dir / "staging"
    quarantine_dir = output_dir / "quarantine"
    
    staging_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    
    # Save clean data
    if len(clean_df) > 0:
        clean_path = staging_dir / f"{source_name}_validated.parquet"
        clean_df.to_parquet(clean_path, compression='zstd')
        print(f"\n✅ Saved clean data: {clean_path}")
        print(f"   Rows: {len(clean_df):,}")
    
    # Save quarantine data
    if len(quarantine_df) > 0:
        quarantine_path = quarantine_dir / f"{source_name}_quarantine.parquet"
        quarantine_df.to_parquet(quarantine_path, compression='zstd')
        print(f"\n⚠️ Saved quarantine data: {quarantine_path}")
        print(f"   Rows: {len(quarantine_df):,}")
        
        # Also save a sample for inspection
        sample_path = quarantine_dir / f"{source_name}_quarantine_sample.csv"
        quarantine_df.head(100).to_csv(sample_path, index=False)
        print(f"   Sample (first 100 rows): {sample_path}")


if __name__ == "__main__":
    # Example usage
    print("Data validation functions ready")
    print("\nAvailable functions:")
    print("  validate_jumps_bps(df, col)  # Validate rate jumps in basis points")
    print("  validate_vix_floor(df)  # Validate VIX floor")
    print("  validate_all_columns(df)  # Run all validations")
    print("  save_validation_results(clean_df, quarantine_df, 'source_name')  # Save results")
