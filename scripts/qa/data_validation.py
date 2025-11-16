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


def validate_jumps_bps(df, col, threshold_bps=50, verbose=True):
    """
    Flag jumps >50 basis points (not percentage) for rate columns.
    Prevents false positives when rates are near zero.
    
    For price columns, uses percentage threshold.
    
    Args:
        df: DataFrame with the column to validate
        col: Column name to check
        threshold_bps: Threshold in basis points for rate columns (default 50)
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
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Determine if this is a rate column
    rate_columns = ['fed_funds_rate', 'treasury_10y', 'treasury_2y', 
                    'libor_3m', 'sofr', 'prime_rate', 'mortgage_rate_30y']
    
    if col in rate_columns or 'rate' in col.lower() or 'yield' in col.lower():
        # Convert to basis points for rate columns
        if verbose:
            print(f"Validating {col} as rate column (basis points threshold: {threshold_bps})")
        
        # Calculate absolute change in basis points
        abs_change = df[col].diff().abs() * 100  # Convert to basis points
        mask = abs_change > threshold_bps
        
        if verbose and mask.sum() > 0:
            print(f"  Found {mask.sum()} jumps > {threshold_bps} bps")
            print(f"  Max jump: {abs_change.max():.1f} bps")
            
            # Show examples
            jump_examples = df[mask].head(3)
            for idx in jump_examples.index:
                if idx > 0:
                    prev_val = df.loc[idx-1, col]
                    curr_val = df.loc[idx, col]
                    change_bps = abs(curr_val - prev_val) * 100
                    print(f"    {df.loc[idx, 'date']}: {prev_val:.3f} → {curr_val:.3f} ({change_bps:.1f} bps)")
    else:
        # Use percentage threshold for price columns
        threshold_pct = 0.30  # 30% threshold for prices
        if verbose:
            print(f"Validating {col} as price column (percentage threshold: {threshold_pct*100:.0f}%)")
        
        # Calculate percentage change
        pct_change = df[col].pct_change().abs()
        mask = pct_change > threshold_pct
        
        if verbose and mask.sum() > 0:
            print(f"  Found {mask.sum()} jumps > {threshold_pct*100:.0f}%")
            print(f"  Max jump: {pct_change.max()*100:.1f}%")
    
    # Split into clean and quarantine
    clean_df = df[~mask]
    quarantine_df = df[mask]
    
    if verbose:
        print(f"  Clean rows: {len(clean_df):,}")
        print(f"  Quarantined rows: {len(quarantine_df):,}")
    
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
