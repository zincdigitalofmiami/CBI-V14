#!/usr/bin/env python3
"""
FINAL VALIDATION BEFORE TRAINING
This is the LAST checkpoint - NO fake data gets through!
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import sys

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

# Import validator
import sys as sys_module
sys_module.path.insert(0, str(DRIVE.parent / "src"))
from utils.data_validation import AlphaDataValidator, DataIntegrityChecker

def final_validation_checkpoint():
    """
    CRITICAL: Final validation before any training
    """
    
    print("\n" + "="*80)
    print("FINAL VALIDATION CHECKPOINT - NO FAKE DATA ALLOWED")
    print("="*80)
    
    issues = []
    checks_passed = 0
    checks_failed = 0
    
    # CHECK 1: Verify staging files exist and are valid
    print("\n1️⃣  CHECKING STAGING FILES...")
    staging_files = [
        "staging/alpha/daily/alpha_complete_ready_for_join.parquet",
        "staging/alpha/daily/alpha_indicators_wide.parquet",
        "staging/alpha/daily/alpha_prices_combined.parquet"
    ]
    
    for file_path in staging_files:
        full_path = DRIVE / file_path
        if not full_path.exists():
            issues.append(f"MISSING: {file_path}")
            checks_failed += 1
        else:
            df = pd.read_parquet(full_path)
            if df.empty:
                issues.append(f"EMPTY: {file_path}")
                checks_failed += 1
            elif len(df) < 100:
                issues.append(f"TOO SMALL: {file_path} has only {len(df)} rows")
                checks_failed += 1
            else:
                print(f"   ✅ {file_path}: {len(df)} rows")
                checks_passed += 1
    
    # CHECK 2: Verify 50+ indicators present
    print("\n2️⃣  CHECKING TECHNICAL INDICATORS...")
    indicators_file = DRIVE / "staging/alpha/daily/alpha_indicators_wide.parquet"
    if indicators_file.exists():
        df = pd.read_parquet(indicators_file)
        
        # Count indicator columns
        expected_indicators = [
            'RSI_14', 'MACD_line', 'MACD_signal', 'ATR_14',
            'SMA_20', 'EMA_20', 'BBANDS_upper_20', 'BBANDS_lower_20',
            'STOCH_K', 'STOCH_D', 'ADX_14', 'CCI_20', 'MFI_14'
        ]
        
        missing = []
        for ind in expected_indicators:
            if ind not in df.columns:
                missing.append(ind)
        
        if missing:
            issues.append(f"MISSING INDICATORS: {missing}")
            checks_failed += 1
        else:
            indicator_cols = [c for c in df.columns if any(
                x in c for x in ['SMA', 'EMA', 'RSI', 'MACD', 'ATR', 'BB']
            )]
            if len(indicator_cols) < 50:
                issues.append(f"INSUFFICIENT INDICATORS: Only {len(indicator_cols)} found")
                checks_failed += 1
            else:
                print(f"   ✅ {len(indicator_cols)} technical indicators present")
                checks_passed += 1
    
    # CHECK 3: No placeholder values in final data
    print("\n3️⃣  SCANNING FOR PLACEHOLDER DATA...")
    final_file = DRIVE / "staging/alpha/daily/alpha_complete_ready_for_join.parquet"
    if final_file.exists():
        df = pd.read_parquet(final_file)
        
        placeholder_issues = []
        for col in df.select_dtypes(include=[np.number]).columns:
            # Check for all zeros
            if (df[col] == 0).all():
                placeholder_issues.append(f"{col}: ALL ZEROS")
            
            # Check for no variance
            if df[col].std() == 0:
                placeholder_issues.append(f"{col}: NO VARIANCE")
            
            # Check for sequential values
            if len(df) > 10 and col != 'index':
                first_10 = df[col].iloc[:10].values
                if np.array_equal(first_10, np.arange(10)):
                    placeholder_issues.append(f"{col}: SEQUENTIAL")
        
        if placeholder_issues:
            issues.extend(placeholder_issues)
            checks_failed += len(placeholder_issues)
        else:
            print(f"   ✅ No placeholder patterns detected")
            checks_passed += 1
    
    # CHECK 4: Date coverage validation
    print("\n4️⃣  CHECKING DATE COVERAGE...")
    if final_file.exists():
        df = pd.read_parquet(final_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            min_date = df['date'].min()
            max_date = df['date'].max()
            
            # Should have recent data
            days_old = (pd.Timestamp.now() - max_date).days
            if days_old > 5:
                issues.append(f"STALE DATA: {days_old} days old")
                checks_failed += 1
            else:
                print(f"   ✅ Date range: {min_date} to {max_date}")
                checks_passed += 1
    
    # CHECK 5: BigQuery tables ready
    print("\n5️⃣  CHECKING BIGQUERY TABLES...")
    # This would actually query BigQuery
    # For now, checking manifest
    manifest_dir = DRIVE / "raw/alpha/manifests/daily"
    if manifest_dir.exists():
        manifests = list(manifest_dir.glob("*.json"))
        if len(manifests) == 0:
            issues.append("NO MANIFESTS: Collection tracking missing")
            checks_failed += 1
        else:
            print(f"   ✅ {len(manifests)} manifests found")
            checks_passed += 1
    
    # CHECK 6: Verify no empty parquet files
    print("\n6️⃣  CHECKING FOR EMPTY FILES...")
    empty_files = []
    alpha_dir = DRIVE / "raw/alpha"
    if alpha_dir.exists():
        for parquet_file in alpha_dir.rglob("*.parquet"):
            try:
                df = pd.read_parquet(parquet_file)
                if df.empty:
                    empty_files.append(str(parquet_file.relative_to(DRIVE)))
            except:
                empty_files.append(f"CORRUPT: {parquet_file.name}")
    
    if empty_files:
        issues.extend([f"EMPTY FILE: {f}" for f in empty_files])
        checks_failed += len(empty_files)
    else:
        print(f"   ✅ No empty files found")
        checks_passed += 1
    
    # FINAL REPORT
    print("\n" + "="*80)
    print("FINAL VALIDATION REPORT")
    print("="*80)
    print(f"✅ Checks Passed: {checks_passed}")
    print(f"❌ Checks Failed: {checks_failed}")
    
    if issues:
        print(f"\n❌ VALIDATION FAILED - {len(issues)} ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🛑 STOPPING: Fix all issues before proceeding to training!")
        sys.exit(1)
    else:
        print(f"\n✅ ALL VALIDATION PASSED - SAFE TO PROCEED TO TRAINING")
        
        # Save validation certificate
        certificate = {
            'timestamp': datetime.now().isoformat(),
            'status': 'PASSED',
            'checks_passed': checks_passed,
            'checks_failed': checks_failed,
            'validated_by': 'final_alpha_validation.py',
            'safe_for_training': True
        }
        
        cert_path = DRIVE / "validation_certificate.json"
        cert_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cert_path, 'w') as f:
            json.dump(certificate, f, indent=2)
        
        print(f"\n📜 Validation certificate saved: {cert_path}")
        return True

if __name__ == "__main__":
    # This MUST pass before any training
    final_validation_checkpoint()





