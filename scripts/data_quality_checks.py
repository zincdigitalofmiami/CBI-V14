#!/usr/bin/env python3
"""
Comprehensive data quality validation for training data exports.
Run BEFORE starting any model training.
"""
import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Tuple
import warnings

warnings.filterwarnings('ignore')

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / ".git").exists() or (parent / "src").exists():
            return parent
    return current_path.parent.parent

def audit_training_file(file_path: Path, horizon: str) -> Dict:
    """
    Comprehensive quality audit of a single training file.
    
    Args:
        file_path: Path to Parquet file
        horizon: Horizon label (1w, 1m, etc.)
    
    Returns:
        Dict with audit results
    """
    results = {
        'horizon': horizon,
        'file': str(file_path),
        'status': 'UNKNOWN',
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    try:
        # 1. Load file
        print(f"\n{'='*80}")
        print(f"AUDITING: {horizon.upper()} Horizon")
        print(f"{'='*80}")
        print(f"File: {file_path}")
        
        df = pd.read_parquet(file_path)
        
        # 2. Basic stats
        print(f"\n1. BASIC STATS")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        
        results['info']['rows'] = len(df)
        results['info']['columns'] = len(df.columns)
        
        # 3. Date validation
        print(f"\n2. DATE COLUMN")
        if 'date' not in df.columns:
            error = "Missing 'date' column"
            print(f"   ❌ {error}")
            results['errors'].append(error)
            results['status'] = 'FAIL'
            return results
        
        print(f"   ✅ Present")
        print(f"   Type: {df['date'].dtype}")
        print(f"   Range: {df['date'].min()} to {df['date'].max()}")
        
        # Check date dtype
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            warning = f"Date column is {df['date'].dtype}, not datetime"
            print(f"   ⚠️  {warning}")
            results['warnings'].append(warning)
        
        days_span = (df['date'].max() - df['date'].min()).days
        print(f"   Days span: {days_span}")
        
        results['info']['date_min'] = str(df['date'].min())
        results['info']['date_max'] = str(df['date'].max())
        results['info']['date_span_days'] = days_span
        
        # Expected minimum: 20 years = ~7300 days
        if days_span < 7000:
            warning = f"Date span only {days_span} days (expected ~7300+ for 20 years)"
            print(f"   ⚠️  {warning}")
            results['warnings'].append(warning)
        
        # 4. Target column validation
        print(f"\n3. TARGET COLUMN")
        target_col = f'zl_price_{horizon}'
        
        if target_col not in df.columns:
            error = f"Missing target column: {target_col}"
            print(f"   ❌ {error}")
            results['errors'].append(error)
        else:
            print(f"   ✅ Present: {target_col}")
            
            # Check nulls
            null_count = df[target_col].isna().sum()
            null_pct = (null_count / len(df)) * 100
            
            print(f"   Nulls: {null_count} ({null_pct:.1f}%)")
            
            if null_pct > 5:
                warning = f"Target has {null_pct:.1f}% nulls (>5% threshold)"
                print(f"   ⚠️  {warning}")
                results['warnings'].append(warning)
            
            # Check value range
            if null_count < len(df):
                print(f"   Range: ${df[target_col].min():.2f} to ${df[target_col].max():.2f}")
                print(f"   Mean: ${df[target_col].mean():.2f}")
                print(f"   Median: ${df[target_col].median():.2f}")
                
                results['info']['target_min'] = float(df[target_col].min())
                results['info']['target_max'] = float(df[target_col].max())
                results['info']['target_mean'] = float(df[target_col].mean())
                results['info']['target_nulls_pct'] = float(null_pct)
        
        # 5. Feature completeness
        print(f"\n4. FEATURE COMPLETENESS")
        null_pct_per_col = (df.isna().sum() / len(df) * 100).sort_values(ascending=False)
        
        critical_nulls = null_pct_per_col[null_pct_per_col > 10]
        moderate_nulls = null_pct_per_col[(null_pct_per_col > 5) & (null_pct_per_col <= 10)]
        
        print(f"   Total features: {len(df.columns)}")
        print(f"   Features >10% null: {len(critical_nulls)}")
        print(f"   Features 5-10% null: {len(moderate_nulls)}")
        
        results['info']['features_total'] = len(df.columns)
        results['info']['features_critical_nulls'] = len(critical_nulls)
        results['info']['features_moderate_nulls'] = len(moderate_nulls)
        
        if len(critical_nulls) > 0:
            print(f"\n   ⚠️  HIGH NULL FEATURES (>10%):")
            for col, pct in critical_nulls.head(15).items():
                print(f"      {col[:60]:60s}: {pct:5.1f}%")
                
            if len(critical_nulls) > 50:
                warning = f"{len(critical_nulls)} features have >10% nulls (consider feature selection)"
                results['warnings'].append(warning)
        
        # 6. Date continuity
        print(f"\n5. DATE CONTINUITY")
        df_sorted = df.sort_values('date')
        date_diffs = df_sorted['date'].diff()
        
        gaps = (date_diffs.dt.days > 1).sum()
        max_gap = date_diffs.dt.days.max() if len(date_diffs) > 0 else 0
        
        print(f"   Gaps >1 day: {gaps}")
        print(f"   Max gap: {max_gap} days")
        
        results['info']['date_gaps'] = int(gaps)
        results['info']['date_max_gap'] = int(max_gap)
        
        if gaps > 100:
            warning = f"{gaps} date gaps found (>100 threshold)"
            print(f"   ⚠️  {warning}")
            results['warnings'].append(warning)
        
        # 7. Regime coverage
        print(f"\n6. REGIME COVERAGE")
        if 'regime' in df.columns:
            regime_counts = df['regime'].value_counts()
            print(f"   ✅ Regime column present")
            print(f"   Unique regimes: {len(regime_counts)}")
            
            results['info']['regime_count'] = len(regime_counts)
            
            for regime, count in regime_counts.items():
                print(f"      {str(regime)[:40]:40s}: {count:4d} rows ({count/len(df)*100:5.1f}%)")
        else:
            warning = "No 'regime' column found"
            print(f"   ⚠️  {warning}")
            results['warnings'].append(warning)
        
        # 8. Key features check
        print(f"\n7. KEY FEATURES CHECK")
        expected_features = [
            'zl_price_current',
            'vix_close',
            'crude_oil_price',
            'palm_oil_price',
            'soybean_price',
            'usd_index'
        ]
        
        missing_features = [f for f in expected_features if f not in df.columns]
        present_features = [f for f in expected_features if f in df.columns]
        
        print(f"   Expected key features: {len(expected_features)}")
        print(f"   Present: {len(present_features)}")
        print(f"   Missing: {len(missing_features)}")
        
        if missing_features:
            print(f"\n   ⚠️  MISSING KEY FEATURES:")
            for feat in missing_features:
                print(f"      - {feat}")
            
            if len(missing_features) > 2:
                warning = f"{len(missing_features)} key features missing"
                results['warnings'].append(warning)
        
        # 9. Summary
        print(f"\n8. VALIDATION SUMMARY")
        
        if len(results['errors']) == 0 and len(results['warnings']) == 0:
            results['status'] = 'PASS'
            print(f"   ✅ PASS - No critical issues")
        elif len(results['errors']) == 0:
            results['status'] = 'WARN'
            print(f"   ⚠️  PASS WITH WARNINGS - {len(results['warnings'])} warnings")
        else:
            results['status'] = 'FAIL'
            print(f"   ❌ FAIL - {len(results['errors'])} errors")
        
        return results
        
    except Exception as e:
        print(f"\n❌ EXCEPTION during audit: {e}")
        import traceback
        traceback.print_exc()
        results['status'] = 'ERROR'
        results['errors'].append(f"Exception: {str(e)}")
        return results

def audit_all_training_data(export_dir: Path = None) -> Dict:
    """
    Audit all training data files.
    
    Args:
        export_dir: Directory containing exports (default: TrainingData/exports)
    
    Returns:
        Dict with all results
    """
    if export_dir is None:
        repo_root = get_repo_root()
        export_dir = repo_root / "TrainingData" / "exports"
    
    horizons = ['1w', '1m', '3m', '6m', '12m']
    
    print("="*80)
    print("COMPREHENSIVE TRAINING DATA QUALITY AUDIT")
    print("="*80)
    print(f"Export Directory: {export_dir}")
    print()
    
    all_results = {}
    
    for horizon in horizons:
        file_path = export_dir / f"zl_training_prod_allhistory_{horizon}.parquet"
        
        if not file_path.exists():
            print(f"\n⚠️  SKIPPING {horizon}: File not found - {file_path}")
            all_results[horizon] = {
                'status': 'MISSING',
                'file': str(file_path),
                'errors': ['File not found']
            }
            continue
        
        result = audit_training_file(file_path, horizon)
        all_results[horizon] = result
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    
    pass_count = sum(1 for r in all_results.values() if r['status'] == 'PASS')
    warn_count = sum(1 for r in all_results.values() if r['status'] == 'WARN')
    fail_count = sum(1 for r in all_results.values() if r['status'] in ['FAIL', 'ERROR', 'MISSING'])
    
    print(f"\nResults:")
    print(f"  ✅ PASS: {pass_count}/{len(horizons)}")
    print(f"  ⚠️  WARN: {warn_count}/{len(horizons)}")
    print(f"  ❌ FAIL: {fail_count}/{len(horizons)}")
    
    # Detail failures
    if fail_count > 0:
        print(f"\nFailed/Missing Files:")
        for horizon, result in all_results.items():
            if result['status'] in ['FAIL', 'ERROR', 'MISSING']:
                print(f"  - {horizon}: {result['status']}")
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"      • {error}")
    
    # Training readiness
    print(f"\n{'='*80}")
    if fail_count == 0 and warn_count == 0:
        print("✅ TRAINING READY - All files passed validation")
        print("="*80)
        return all_results
    elif fail_count == 0:
        print("⚠️  TRAINING READY WITH WARNINGS - Review warnings before training")
        print("="*80)
        return all_results
    else:
        print("🚨 NOT READY FOR TRAINING - Fix errors first")
        print("="*80)
        return all_results

def main():
    """Run comprehensive data quality audit."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate training data quality")
    parser.add_argument("--horizon", choices=["1w", "1m", "3m", "6m", "12m", "all"],
                       default="all", help="Horizon to audit")
    parser.add_argument("--export-dir", type=str, help="Export directory")
    
    args = parser.parse_args()
    
    export_dir = Path(args.export_dir) if args.export_dir else None
    
    if args.horizon == "all":
        results = audit_all_training_data(export_dir)
        
        # Exit code based on results
        fail_count = sum(1 for r in results.values() if r['status'] in ['FAIL', 'ERROR', 'MISSING'])
        sys.exit(1 if fail_count > 0 else 0)
    else:
        if export_dir is None:
            repo_root = get_repo_root()
            export_dir = repo_root / "TrainingData" / "exports"
        
        file_path = export_dir / f"zl_training_prod_allhistory_{args.horizon}.parquet"
        result = audit_training_file(file_path, args.horizon)
        
        sys.exit(0 if result['status'] in ['PASS', 'WARN'] else 1)

if __name__ == "__main__":
    main()



