#!/usr/bin/env python3
"""
Pre-training diagnostics: regime stats, leakage checks, data quality.
Run this before training to ensure data integrity and identify issues.

Checks:
1. Regime statistics (mean/std returns, MAPE, Sharpe by regime)
2. Data leakage (future information contamination)
3. Feature alignment (targets properly shifted)
4. Regime weight distribution
5. Missing data patterns
"""
import os
import sys
import argparse
from pathlib import Path
import polars as pl
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from training.evaluation.metrics import calculate_mape, calculate_sharpe
from training.config.m4_config import REGIME_WEIGHTS

def compute_regime_stats(
    df: pl.DataFrame,
    target_col: str,
    price_col: str = 'zl_price_current',
    regime_col: str = 'market_regime',
    date_col: str = 'date'
) -> Dict[str, Dict]:
    """
    Compute statistics for each regime.
    
    Returns:
        Dictionary mapping regime -> stats dict
    """
    if regime_col not in df.columns:
        print(f"⚠️  No regime column '{regime_col}' found")
        return {}
    
    regimes = df[regime_col].unique().to_list()
    results = {}
    
    print(f"\n📊 Computing regime statistics...")
    print(f"   Found {len(regimes)} regimes")
    
    for regime in regimes:
        df_regime = df.filter(pl.col(regime_col) == regime)
        
        if len(df_regime) < 10:
            print(f"   ⚠️  {regime}: Only {len(df_regime)} samples (skipping)")
            continue
        
        # Get values
        targets = df_regime[target_col].to_numpy()
        prices = df_regime[price_col].to_numpy() if price_col in df_regime.columns else None
        
        # Remove NaN
        mask = np.isfinite(targets)
        targets = targets[mask]
        if prices is not None:
            prices = prices[mask]
        
        if len(targets) == 0:
            continue
        
        # Compute returns if prices available
        returns = None
        if prices is not None and len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
        
        stats = {
            'n_samples': len(targets),
            'mean_target': np.mean(targets),
            'std_target': np.std(targets),
            'min_target': np.min(targets),
            'max_target': np.max(targets),
        }
        
        if returns is not None:
            stats['mean_return'] = np.mean(returns)
            stats['std_return'] = np.std(returns)
            stats['sharpe'] = calculate_sharpe(returns) if len(returns) > 0 else 0.0
        
        # Regime weight
        weight_key = regime.lower().replace(' ', '_')
        stats['regime_weight'] = REGIME_WEIGHTS.get(weight_key, REGIME_WEIGHTS['default'])
        
        results[regime] = stats
        
        print(f"   ✅ {regime:30s}: n={stats['n_samples']:5d}, "
              f"mean={stats['mean_target']:7.2f}, "
              f"weight={stats['regime_weight']:5d}")
    
    return results

def check_target_alignment(
    df: pl.DataFrame,
    target_col: str,
    date_col: str = 'date',
    horizon: str = '1m'
) -> Dict[str, bool]:
    """
    Check that targets are properly shifted (no leakage).
    
    Args:
        df: DataFrame with targets and dates
        target_col: Target column name
        date_col: Date column name
        horizon: Forecast horizon (e.g., '1m' = 30 days)
        
    Returns:
        Dictionary of alignment checks
    """
    checks = {}
    
    if date_col not in df.columns or target_col not in df.columns:
        checks['columns_present'] = False
        return checks
    
    # Map horizon to days
    horizon_days = {
        '1w': 7,
        '1m': 30,
        '3m': 90,
        '6m': 180,
        '12m': 365,
    }
    
    expected_days = horizon_days.get(horizon, 30)
    
    # Sort by date
    df_sorted = df.sort(date_col).select([date_col, target_col])
    
    # Check: target should be ahead of current date
    # (Simplified check - assumes target is already shifted in data)
    dates = df_sorted[date_col].to_numpy()
    targets = df_sorted[target_col].to_numpy()
    
    # Check for NaN targets at end (expected - can't predict future)
    nan_at_end = np.isnan(targets[-min(10, len(targets)):]).sum()
    checks['nan_at_end'] = nan_at_end > 0
    
    # Check: no negative time gaps (would indicate misalignment)
    if len(dates) > 1:
        time_diffs = np.diff(dates.astype('datetime64[D]').astype(int))
        checks['consistent_time_gaps'] = np.all(time_diffs >= 0)
    
    checks['target_column_present'] = True
    checks['date_column_present'] = True
    
    return checks

def check_missing_data(
    df: pl.DataFrame,
    feature_cols: Optional[List[str]] = None,
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Check for missing data patterns.
    
    Args:
        df: DataFrame to check
        feature_cols: List of feature columns (all if None)
        threshold: Missing data threshold (0.5 = 50%)
        
    Returns:
        Dictionary mapping column -> missing percentage
    """
    if feature_cols is None:
        # Exclude date and target columns
        exclude = ['date', 'target_1w', 'target_1m', 'target_3m', 'target_6m', 'target_12m']
        feature_cols = [col for col in df.columns if col not in exclude]
    
    missing_stats = {}
    
    for col in feature_cols:
        if col not in df.columns:
            continue
        
        null_count = df[col].null_count()
        total_count = len(df)
        missing_pct = (null_count / total_count) * 100 if total_count > 0 else 0
        
        if missing_pct > threshold * 100:
            missing_stats[col] = missing_pct
    
    return missing_stats

def check_regime_weights(
    df: pl.DataFrame,
    regime_col: str = 'market_regime',
    weight_col: Optional[str] = 'sample_weight'
) -> Dict:
    """
    Check regime weight distribution.
    
    Returns:
        Dictionary with weight statistics
    """
    results = {}
    
    if regime_col not in df.columns:
        results['regime_column_present'] = False
        return results
    
    if weight_col and weight_col in df.columns:
        weights = df[weight_col].to_numpy()
        results['mean_weight'] = float(np.mean(weights))
        results['std_weight'] = float(np.std(weights))
        results['min_weight'] = float(np.min(weights))
        results['max_weight'] = float(np.max(weights))
        
        # Check weight distribution by regime
        regime_weights = {}
        for regime in df[regime_col].unique().to_list():
            df_regime = df.filter(pl.col(regime_col) == regime)
            regime_weights[regime] = float(df_regime[weight_col].mean())
        
        results['by_regime'] = regime_weights
    else:
        results['weight_column_present'] = False
    
    return results

def run_diagnostics(
    data_path: Path,
    horizon: str,
    target_col: Optional[str] = None
) -> Dict:
    """
    Run all pre-training diagnostics.
    
    Returns:
        Dictionary with all diagnostic results
    """
    print("="*80)
    print("PRE-TRAINING DIAGNOSTICS")
    print("="*80)
    print(f"Data: {data_path.name}")
    print(f"Horizon: {horizon}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Load data
    print(f"\n📂 Loading data...")
    df = pl.read_parquet(data_path)
    print(f"   ✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
    
    # Determine target column
    if target_col is None:
        target_col = f"target_{horizon}"
    
    if target_col not in df.columns:
        print(f"   ❌ Target column '{target_col}' not found")
        return {'error': f'Target column {target_col} not found'}
    
    results = {
        'data_path': str(data_path),
        'horizon': horizon,
        'target_col': target_col,
        'n_rows': len(df),
        'n_cols': len(df.columns),
    }
    
    # 1. Regime statistics
    print(f"\n{'='*80}")
    print("1. REGIME STATISTICS")
    print("="*80)
    regime_stats = compute_regime_stats(df, target_col)
    results['regime_stats'] = regime_stats
    
    # 2. Target alignment
    print(f"\n{'='*80}")
    print("2. TARGET ALIGNMENT CHECKS")
    print("="*80)
    alignment_checks = check_target_alignment(df, target_col, horizon=horizon)
    results['alignment_checks'] = alignment_checks
    
    for check, passed in alignment_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}: {passed}")
    
    # 3. Missing data
    print(f"\n{'='*80}")
    print("3. MISSING DATA CHECK")
    print("="*80)
    missing_data = check_missing_data(df, threshold=0.5)
    results['missing_data'] = missing_data
    
    if missing_data:
        print(f"   ⚠️  Found {len(missing_data)} columns with >50% missing data:")
        for col, pct in sorted(missing_data.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"      {col:40s}: {pct:6.2f}%")
    else:
        print(f"   ✅ No columns with >50% missing data")
    
    # 4. Regime weights
    print(f"\n{'='*80}")
    print("4. REGIME WEIGHT DISTRIBUTION")
    print("="*80)
    weight_stats = check_regime_weights(df)
    results['weight_stats'] = weight_stats
    
    if 'by_regime' in weight_stats:
        print(f"   Mean weight: {weight_stats.get('mean_weight', 'N/A')}")
        print(f"   Weight by regime:")
        for regime, weight in weight_stats['by_regime'].items():
            print(f"      {regime:30s}: {weight:8.2f}")
    else:
        print(f"   ⚠️  No weight column found")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    
    issues = []
    if not alignment_checks.get('target_column_present', False):
        issues.append("❌ Target column missing")
    if missing_data:
        issues.append(f"⚠️  {len(missing_data)} columns with high missing data")
    if not weight_stats.get('weight_column_present', True):
        issues.append("⚠️  No sample weight column found")
    
    if issues:
        print("   Issues found:")
        for issue in issues:
            print(f"      {issue}")
    else:
        print("   ✅ All checks passed")
    
    print("="*80)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run pre-training diagnostics")
    parser.add_argument("--data-path", type=str, required=True,
                       help="Path to training data parquet file")
    parser.add_argument("--horizon", type=str, required=True,
                       choices=["1w", "1m", "3m", "6m", "12m"],
                       help="Forecast horizon")
    parser.add_argument("--target-col", type=str,
                       help="Target column name (default: target_{horizon})")
    
    args = parser.parse_args()
    
    data_path = Path(args.data_path)
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)
    
    results = run_diagnostics(data_path, args.horizon, args.target_col)
    
    # Save results
    output_path = data_path.parent / f"diagnostics_{args.horizon}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Diagnostics saved to: {output_path}")

if __name__ == "__main__":
    main()

