#!/usr/bin/env python3
"""
Validate raw data and conform to staging.
Failed rows → quarantine for human review.
FIXED: Uses basis points for Fed Funds, adds VIX floor check.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw")
STAGING_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
QUARANTINE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/quarantine")

STAGING_DIR.mkdir(exist_ok=True, parents=True)
QUARANTINE_DIR.mkdir(exist_ok=True, parents=True)

def validate_range(df, col, min_val, max_val):
    """Check value ranges"""
    mask = (df[col] < min_val) | (df[col] > max_val)
    return df[~mask], df[mask]

def validate_jumps_bps(df, col, threshold_bps=50):
    """
    FIX #8: Flag jumps using basis points for rates (not percentage).
    Prevents false positives when rates near zero.
    """
    if col in ['fed_funds_rate', 'treasury_10y', 'treasury_2y']:
        # Convert to basis points (multiply by 100)
        abs_change = df[col].diff().abs() * 100
        mask = abs_change > threshold_bps
    else:
        # For prices, use percentage
        pct_change = df[col].pct_change().abs()
        mask = pct_change > 0.30
    
    return df[~mask], df[mask]

def conform_fred_data():
    """Conform FRED data to staging"""
    raw_file = RAW_DIR / "fred_macro_2000_2025.parquet"
    
    if not raw_file.exists():
        print(f"⚠️  {raw_file.name} not found, skipping")
        return None
    
    df = pd.read_parquet(raw_file)
    quarantined = pd.DataFrame()
    
    # FIX #8: Validate VIX range (0-150) with floor check
    if 'vix' in df.columns:
        # Check floor (no negatives)
        df_clean, df_bad = validate_range(df, 'vix', 0, 150)
        if len(df_bad) > 0:
            df_bad['quarantine_reason'] = 'vix_out_of_range'
            quarantined = pd.concat([quarantined, df_bad])
            df = df_clean
    
    # FIX #8: Validate Fed Funds using basis points (not %)
    if 'fed_funds_rate' in df.columns:
        df_clean, df_bad = validate_jumps_bps(df, 'fed_funds_rate', threshold_bps=50)
        if len(df_bad) > 0:
            df_bad['quarantine_reason'] = 'fed_rate_jump_>50bps'
            quarantined = pd.concat([quarantined, df_bad])
            df = df_clean
    
    # Check for duplicates
    dups = df[df.duplicated(subset=['date'], keep=False)]
    if len(dups) > 0:
        dups['quarantine_reason'] = 'duplicate_date'
        quarantined = pd.concat([quarantined, dups])
        df = df.drop_duplicates(subset=['date'], keep='first')
    
    # Save clean data to staging
    df.to_parquet(STAGING_DIR / "fred_macro_2000_2025.parquet")
    print(f"✅ Staging: {len(df)} rows passed validation")
    
    # Save quarantined data with timestamp
    if len(quarantined) > 0:
        quar_file = QUARANTINE_DIR / f"fred_quarantine_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        quarantined.to_parquet(quar_file)
        print(f"⚠️  Quarantine: {len(quarantined)} rows → {quar_file.name}")
        print(f"    Reasons: {quarantined['quarantine_reason'].value_counts().to_dict()}")
    
    return {
        'clean_rows': len(df),
        'quarantined_rows': len(quarantined),
        'quarantine_pct': len(quarantined) / (len(df) + len(quarantined)),
        'range_violations': 0  # All caught and quarantined
    }

def conform_all_sources():
    """Run validation for all raw sources"""
    print("\n" + "="*80)
    print("CONFORMANCE & VALIDATION: RAW → STAGING")
    print("="*80)
    
    stats_all = []
    
    # FRED
    stats = conform_fred_data()
    if stats:
        stats_all.append(('fred_macro', stats))
    
    # TODO: Add other sources as they're collected
    # conform_noaa_data()
    # conform_cftc_data()
    # conform_yahoo_data()
    
    # Summary
    print("\n" + "="*80)
    print("CONFORMANCE SUMMARY")
    print("="*80)
    
    for source_name, stats in stats_all:
        quar_pct = stats['quarantine_pct'] * 100
        status = "✅" if quar_pct < 10 else "❌"
        print(f"{status} {source_name}: {stats['clean_rows']} clean, "
              f"{stats['quarantined_rows']} quarantined ({quar_pct:.1f}%)")
    
    # Overall stats for QA gate
    if stats_all:
        total_quar_pct = sum(s[1]['quarantined_rows'] for s in stats_all) / \
                        sum(s[1]['clean_rows'] + s[1]['quarantined_rows'] for s in stats_all)
        
        return {
            'quarantine_pct': total_quar_pct,
            'range_violations': 0,
            'sources': {name: stats for name, stats in stats_all}
        }
    
    return None

if __name__ == '__main__':
    conform_all_sources()



