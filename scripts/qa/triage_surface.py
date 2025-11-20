#!/usr/bin/env python3
"""Quick surface quality check - verify training surface is correct"""

import pandas as pd
from pathlib import Path
import sys

def check_surface(export_path):
    """Verify training surface meets requirements"""
    
    print("\n" + "="*80)
    print(f"TRAINING SURFACE TRIAGE: {export_path.name}")
    print("="*80)
    
    if not export_path.exists():
        print(f"❌ File doesn't exist: {export_path}")
        return False
    
    df = pd.read_parquet(export_path)
    
    # Basic stats
    print(f"\n📊 Basic Stats:")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Date range: {df['date'].min()} → {df['date'].max()}")
    
    passed = True
    
    # Check 1: Date coverage (must start from 2000, not 2020!)
    print(f"\n📅 Date Coverage:")
    expected_start = pd.Timestamp("2000-01-03")
    actual_start = pd.to_datetime(df['date']).min()
    
    if actual_start > expected_start:
        print(f"  ❌ Start date {actual_start} > expected {expected_start}")
        print(f"  ❌ MISSING 20 YEARS OF DATA (2000-2019)!")
        passed = False
    else:
        date_span_years = (pd.to_datetime(df['date']).max() - pd.to_datetime(df['date']).min()).days / 365.25
        print(f"  ✅ Start date OK: {actual_start}")
        print(f"  ✅ Coverage: {date_span_years:.1f} years")
    
    # Check 2: Regime coverage (must have 7+ regimes, not just "allhistory")
    print(f"\n🏛️  Regime Coverage:")
    
    if 'market_regime' not in df.columns:
        print(f"  ❌ market_regime column MISSING!")
        passed = False
    else:
        regimes = df['market_regime'].nunique()
        print(f"  Unique regimes: {regimes}")
        
        regime_dist = df['market_regime'].value_counts()
        print("\n  Distribution:")
        for regime, count in regime_dist.items():
            pct = count / len(df) * 100
            print(f"    {regime:30s}: {count:5d} rows ({pct:5.1f}%)")
        
        if regimes < 7:
            print(f"\n  ❌ Only {regimes} regimes, expected 7+")
            passed = False
        elif regime_dist.get('allhistory', 0) / len(df) > 0.10:
            allhist_pct = regime_dist['allhistory'] / len(df) * 100
            print(f"\n  ⚠️  WARNING: {allhist_pct:.1f}% rows are 'allhistory' (should be <10%)")
            print(f"  This suggests regime_calendar join failed")
            passed = False
        else:
            print(f"  ✅ Regime count OK: {regimes}")
    
    # Check 3: Training weights (must be 50-1000, not all 1!)
    print(f"\n⚖️  Training Weights:")
    
    if 'training_weight' not in df.columns:
        print(f"  ❌ training_weight column MISSING!")
        passed = False
    else:
        min_w = df['training_weight'].min()
        max_w = df['training_weight'].max()
        
        print(f"  Range: {min_w:.0f} to {max_w:.0f}")
        
        # Check for broken weights
        if min_w == 1 and max_w == 1:
            print(f"  ❌ ALL weights = 1 (regime weights not applied!)")
            passed = False
        elif min_w < 50:
            print(f"  ❌ Minimum weight {min_w:.0f} < 50")
            passed = False
        elif max_w > 1000:
            print(f"  ⚠️  Maximum weight {max_w:.0f} > 1000 (should use updated 50-1000 scale)")
            # Don't fail - just warn (might have old 5000 scale)
        else:
            print(f"  ✅ Weights OK: {min_w:.0f}-{max_w:.0f}")
            
            # Show weight distribution
            unique_weights = sorted(df['training_weight'].unique())
            print(f"  Unique weights: {unique_weights}")
    
    # Check 4: Target coverage (must be >95%)
    print(f"\n🎯 Target Coverage:")
    
    if 'target' in df.columns:
        target_pct = df['target'].notna().sum() / len(df) * 100
        print(f"  Coverage: {target_pct:.1f}%")
        
        if target_pct < 95:
            print(f"  ❌ Target coverage {target_pct:.1f}% < 95%")
            passed = False
        else:
            print(f"  ✅ Target coverage OK")
    else:
        print(f"  ⚠️  No 'target' column (might be multi-horizon export)")
    
    # Check 5: Feature count
    print(f"\n🔧 Features:")
    
    feature_count = len(df.columns)
    if feature_count < 150:
        print(f"  ❌ Only {feature_count} columns (expected 150-500)")
        passed = False
    elif feature_count > 500:
        print(f"  ⚠️  {feature_count} columns (very high, but OK for full surface)")
    else:
        print(f"  ✅ Feature count OK: {feature_count}")
    
    # Final result
    print("\n" + "="*80)
    if passed:
        print("✅ ALL CHECKS PASSED - Surface is GOOD")
    else:
        print("❌ CHECKS FAILED - Surface needs repair")
    print("="*80 + "\n")
    
    return passed

def main():
    """Check all training surfaces"""
    
    root = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports")
    
    if not root.exists():
        print(f"❌ Exports folder doesn't exist: {root}")
        print("Run: python3 scripts/features/build_all_features.py")
        return False
    
    # Check representative export (1m)
    export_file = root / "zl_training_prod_allhistory_1m.parquet"
    
    if not export_file.exists():
        print(f"❌ Export file doesn't exist: {export_file}")
        print("\nExpected exports:")
        print("  - zl_training_prod_allhistory_{1w,1m,3m,6m,12m}.parquet")
        print("\nRun: python3 scripts/features/build_all_features.py")
        return False
    
    passed = check_surface(export_file)
    
    # Optionally check all exports
    if passed:
        print("\n📋 Checking all exports...")
        for horizon in ['1w', '3m', '6m', '12m']:
            export = root / f"zl_training_prod_allhistory_{horizon}.parquet"
            if export.exists():
                # Quick check
                df = pd.read_parquet(export)
                regimes = df['market_regime'].nunique() if 'market_regime' in df.columns else 0
                weights_ok = False
                if 'training_weight' in df.columns:
                    weights_ok = df['training_weight'].min() >= 50 and df['training_weight'].max() <= 1000
                date_ok = pd.to_datetime(df['date']).min() <= pd.Timestamp("2000-01-03")
                
                status = "✅" if (regimes >= 7 and weights_ok and date_ok) else "❌"
                print(f"  {status} {export.name}: {len(df)} rows, {regimes} regimes")
    
    return passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)





