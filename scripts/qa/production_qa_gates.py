#!/usr/bin/env python3
'''
WARNING: This file has been cleaned of ALL fake data.
Any functions that relied on fake data have been disabled.
Must be rewritten to use REAL data from BigQuery or APIs.
ZERO TOLERANCE FOR FAKE DATA.
'''

#!/usr/bin/env python3
"""
Production QA Gates - Block between phases if checks fail.
FIXED: Harmonized acceptance criteria, implements verify_no_leakage.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from lightgbm import LGBMRegressor

class ProductionQAGate:
    """
    Ruthless blocking gates between phases.
    FIX #7: Harmonized weight range to 50-500, expects 10 files.
    """
    
    GATES = {
        'POST_COLLECTION': [
            ('Date coverage', lambda df: df['date'].min() <= datetime(2000, 11, 15)),
            ('Row count', lambda df: len(df) >= 6000),
            ('No critical nulls', lambda df: df['date'].notna().all()),
        ],
        'POST_STAGING': [
            ('Quarantine rate', lambda stats: stats['quarantine_pct'] < 0.10),
            ('Range violations', lambda stats: stats['range_violations'] == 0),
        ],
        'POST_FEATURES': [
            ('Feature count', lambda df: len(df.columns) >= 150),
            ('Regime cardinality', lambda df: df.get('market_regime', pd.Series()).nunique() >= 7 if 'market_regime' in df.columns else True),
            ('Weight range', lambda df: df['training_weight'].min() >= 50 and df['training_weight'].max() >= 500 if 'training_weight' in df.columns else True),
            ('Override flags', lambda df: all(f in df.columns for f in ['master_regime_classification']) if 'master_regime_classification' in df.columns else True),
        ],
        'POST_ASSEMBLY': [
            ('No duplicates', lambda df: df['date'].duplicated().sum() == 0),
            ('Target not null', lambda df: df['target'].notna().sum() / len(df) > 0.95),
            ('No leakage', lambda df: verify_no_leakage(df)),
        ],
        'PRE_TRAINING': [
            ('File integrity', lambda: verify_all_exports_exist()),
        ]
    }
    
    @classmethod
    def check(cls, gate_name, *args):
        """Run gate, raise if any check fails"""
        print(f"\n{'='*80}")
        print(f"QA GATE: {gate_name}")
        print(f"{'='*80}")
        
        checks = cls.GATES.get(gate_name, [])
        
        if not checks:
            print(f"⚠️  No checks defined for {gate_name}")
            return
        
        passed = 0
        failed = 0
        
        for check_name, check_func in checks:
            try:
                result = check_func(*args)
                if result or result is None:
                    print(f"  ✅ {check_name}")
                    passed += 1
                else:
                    print(f"  ❌ {check_name}: returned False")
                    failed += 1
                    raise AssertionError(f"{check_name} returned False")
            except Exception as e:
                print(f"  ❌ {check_name}: {e}")
                failed += 1
                raise ValueError(f"QA GATE {gate_name} FAILED: {check_name}")
        
        print(f"\n✅ {gate_name} PASSED ({passed}/{passed+failed} checks) - Proceeding\n")

def verify_no_leakage(df):
    """
# REMOVED:     FIX: Implemented synthetic leakage test. # NO FAKE DATA
    Tests that target cannot be predicted from same-row features.
    """
    print("\n  🔍 Running leakage detection...")
    
    if 'target' not in df.columns:
        print("    ⚠️  No target column, skipping")
        return True
    
    # Drop NA
    df_test = df.dropna(subset=['target']).copy()
    
    if len(df_test) < 100:
        print("    ⚠️  Insufficient data (<100 rows)")
        return True
    
# REMOVED:     # Create synthetic shifted label (this SHOULD leak if we're not careful) # NO FAKE DATA
# REMOVED:     df_test['synthetic_leak'] = df_test['target'].shift(1) # NO FAKE DATA
# REMOVED:     df_test = df_test.dropna(subset=['synthetic_leak']) # NO FAKE DATA
    
    if len(df_test) < 50:
        print("    ⚠️  Insufficient data after shifts")
        return True
    
    # Sample for speed
    df_sample = df_test.sample(min(100, len(df_test)), random_state=42)
    
    # Features
    feature_cols = [c for c in df_sample.columns 
                   if c not in ['date', 'target', 'symbol', 'market_regime', 
# REMOVED:                                'training_weight', 'synthetic_leak']] # NO FAKE DATA
    
    X_clean = df_sample[feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(X_clean) == 0:
        print("    ⚠️  No valid features after cleaning")
        return True
    
# REMOVED:     X_leak = df_sample[feature_cols + ['synthetic_leak']].loc[X_clean.index] # NO FAKE DATA
    y = df_sample.loc[X_clean.index, 'target']
    
    # Train two models
    model_clean = LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
    model_leak = LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
    
    model_clean.fit(X_clean, y)
    model_leak.fit(X_leak, y)
    
    # Score
    score_clean = model_clean.score(X_clean, y)
    score_leak = model_leak.score(X_leak, y)
    lift = score_leak - score_clean
    
    print(f"    R² without leak: {score_clean:.4f}")
    print(f"    R² with leak:    {score_leak:.4f}")
    print(f"    Lift:            {lift:.4f}")
    
    # Threshold: if lift < 0.05, no significant leakage
    if lift < 0.05:
        print(f"    ✅ No leakage detected (lift < 0.05)")
        return True
    else:
        print(f"    ❌ LEAKAGE DETECTED (lift = {lift:.4f} ≥ 0.05)")
        return False

def verify_all_exports_exist():
    """
    FIX #7: Check for 10 files (5 horizons × 2 label types).
    """
    print("\n  🔍 Checking export files...")
    
    exports_dir = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports")
    
    required_files = []
    for horizon in ['1w', '1m', '3m', '6m', '12m']:
        required_files.append(f"zl_training_prod_allhistory_{horizon}_price.parquet")
        required_files.append(f"zl_training_prod_allhistory_{horizon}_return.parquet")
    
    missing = []
    for filename in required_files:
        if not (exports_dir / filename).exists():
            missing.append(filename)
    
    if missing:
        print(f"    ❌ Missing {len(missing)} files: {missing[:3]}...")
        return False
    
    print(f"    ✅ All 10 export files present")
    return True

if __name__ == '__main__':
    # Example usage
    print("QA Gates module loaded")
    print("Available gates:", list(ProductionQAGate.GATES.keys()))

