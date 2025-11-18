# CBI-V14 Training Surface Fix + Alpha Vantage Integration - MASTER PLAN
**Date:** November 17, 2025  
**Status:** Ready for Execution  
**Architecture:** Mac M4 (All Training) + BigQuery (Storage/Scheduling) + Alpha Vantage (Consolidated Data)

---

## 🛡️ CRITICAL: DATA VALIDATION THROUGHOUT

### NO FAKE DATA OR PLACEHOLDERS ALLOWED

This plan includes **MANDATORY validation checkpoints** to prevent any fake/placeholder data:

1. **Collection Validation** - Every API response validated (Task 2.4.5)
2. **Save Validation** - Data validated before writing to disk
3. **Staging Validation** - Data validated during transformation (Task 2.7)
4. **BigQuery Sync Validation** - Data validated before cloud upload (Task 2.8)
5. **Join Validation** - Data validated during joins
6. **Final Validation** - Complete validation before training (Task 2.16)

**Key Validation Rules:**
- ❌ **NO empty DataFrames** (will raise error)
- ❌ **NO placeholder values** (0, -999, sequential numbers)
- ❌ **NO static columns** (must have variance)
- ❌ **NO impossible values** (RSI outside 0-100, High < Low)
- ❌ **NO stale data** (>5 days old for daily)
- ✅ **MINIMUM 100 rows** for daily data
- ✅ **MINIMUM 50+ indicators** from Alpha Vantage
- ✅ **VALIDATION CERTIFICATE** required before training

**Validation Scripts:**
- `src/utils/data_validation.py` - Core validation framework
- `scripts/validation/final_alpha_validation.py` - Final checkpoint

**MANDATORY:** Run `final_alpha_validation.py` before ANY training!

---

## Philosophy (Consolidated from architecture-lock.plan.md)

**"Fix the broken foundation first, then build Alpha Vantage on solid ground"**

- **Mac M4** = ALL training + ALL feature engineering (local, deterministic, full control)
- **BigQuery** = Storage + Scheduling + Dashboard (NOT training, NOT feature engineering)
- **External Drive** = PRIMARY data storage + Backup + Audit trail
- **Alpha Vantage** = Single source for commodities (non-ZL), FX, sentiment, options, ES data
- **Dual Storage** = Parquet (external drive) + BigQuery (mirror) from day 1
- **Staging + Quarantine** = No bad data reaches training
- **Declarative joins** = YAML spec with automated tests (currently broken - fix Phase 1)
- **QA gates** = Block between every phase
- **Single-pass feature build** = Efficient (calculate once, use for all horizons)
- **Manifest system** = Provenance tracking for reproducibility

---

## CRITICAL BLOCKER (Fix Before Alpha Vantage)

### Training Pipeline is Broken

**Current State:**
- Training tables: 2020-2025 ONLY (missing 2000-2019 = 20 years!)
- Regimes: "allhistory" ONLY (missing 8 other regimes)
- Weights: ALL = 1 (should be 50-1000)
- Features folder: **EMPTY** (`/Volumes/.../TrainingData/features/`)
- Exports folder: **EMPTY** (`/Volumes/.../TrainingData/exports/`)

**Root Cause:**
- `scripts/assemble/execute_joins.py` **IGNORES** `registry/join_spec.yaml` directives
- Null handling NOT implemented → Old data silently dropped
- Regime join NOT enforced → Defaults to "allhistory"
- Training weights NEVER applied → Stays at 1

**Impact:**
- ❌ Cannot train on 25-year history
- ❌ Cannot use regime-based weighting
- ❌ Cannot export data for Mac training
- ❌ If we add Alpha Vantage data NOW, it will get same broken regimes

**Solution:** Surgical repair (4-6 hours) BEFORE Alpha Vantage

---

## PHASE 1: FIX TRAINING SURFACE (URGENT - Do First)

### Timeline: 6-8 Hours (Must Complete Before Alpha Vantage)

**PRE-REQUISITE:** Create staging files (Task 2.0) BEFORE running join pipeline

---

### Step 1.1: Patch Join Executor (2-3 hours) - CRITICAL

**Problem:** `scripts/assemble/execute_joins.py` ignores `join_spec.yaml`

**File to modify:** `scripts/assemble/execute_joins.py`

**Add method to class:**

```python
def apply_null_policy(self, current_df, join, right_df):
    """Apply null_policy from YAML spec (CURRENTLY NOT IMPLEMENTED)"""
    
    np = join.get('null_policy', {})
    if not np:
        return current_df
    
    # Get columns added from right table
    right_cols = [c for c in right_df.columns if c not in join['on']]
    
    # Forward fill if requested (e.g., FRED data - fill forward for gaps)
    if np.get('fill_method') == 'ffill':
        current_df = current_df.sort_values('date')
        current_df[right_cols] = current_df[right_cols].ffill()
        print(f"    ✅ Applied ffill to {len(right_cols)} columns")
    
    # Static fill values (e.g., regime='allhistory' for missing dates)
    if 'fill' in np:
        for col, val in np['fill'].items():
            if col in current_df.columns:
                before_nulls = current_df[col].isnull().sum()
                current_df[col].fillna(val, inplace=True)
                after_nulls = current_df[col].isnull().sum()
                filled = before_nulls - after_nulls
                if filled > 0:
                    print(f"    ✅ Filled {filled} nulls in {col} with '{val}'")
    
    # Assert no nulls if not allowed (e.g., regime MUST exist for every date)
    if np.get('allow') is False:
        any_null = current_df[right_cols].isnull().any().any()
        if any_null:
            null_cols = [c for c in right_cols if current_df[c].isnull().any()]
            null_counts = {c: current_df[c].isnull().sum() for c in null_cols}
            raise AssertionError(
                f"Nulls remain in {null_cols} with allow:false. Counts: {null_counts}"
            )
    
    return current_df
```

**Update execute() method (find the merge line, add after it):**

```python
# Find this line (around line 530-540):
current_df = current_df.merge(right_df, on=join['on'], how=join['how'])

# ADD IMMEDIATELY AFTER:
current_df = self.apply_null_policy(current_df, join, right_df)

print(f"  Joined {right_path.name}: {self.last_row_count} → {len(current_df)} rows")
```

**Add missing tests to run_tests() method:**

```python
def run_tests(self, df, tests, join_name):
    """Run all tests, raise on failure"""
    print(f"\n  🔍 Testing {join_name}...")
    
    for test in tests:
        # ... existing tests (expect_rows_preserved, expect_columns_present, etc.) ...
        
        # ADD THESE NEW TESTS:
        
        elif 'expect_total_rows_gte' in test:
            min_rows = test['expect_total_rows_gte']
            actual = len(df)
            assert actual >= min_rows, f"Only {actual} rows, need {min_rows}+"
            print(f"    ✅ Total rows: {actual} (>= {min_rows})")
        
        elif 'expect_total_cols_gte' in test:
            min_cols = test['expect_total_cols_gte']
            actual = len(df.columns)
            assert actual >= min_cols, f"Only {actual} cols, need {min_cols}+"
            print(f"    ✅ Total cols: {actual} (>= {min_cols})")
        
        elif 'expect_no_duplicate_dates' in test:
            dups = df['date'].duplicated().sum()
            assert dups == 0, f"Found {dups} duplicate dates"
            print(f"    ✅ No duplicate dates")
        
        elif 'expect_date_range' in test:
            expected_start, expected_end = test['expect_date_range']
            lo = pd.Timestamp(expected_start)
            hi = pd.Timestamp(expected_end)
            actual_start = df['date'].min()
            actual_end = df['date'].max()
            
            # Date range can be within expected (not exact match)
            assert actual_start <= lo, f"Start {actual_start} > expected {lo}"
            assert actual_end >= hi, f"End {actual_end} < expected {hi}"
            print(f"    ✅ Date range: {actual_start} to {actual_end} (covers {lo} to {hi})")
```

**Why this fixes the problem:**
- Forward fill will preserve old data when joining with newer sources (e.g., CFTC since 2006)
- Static fills will ensure regimes exist for all dates
- Tests will BLOCK if data is silently truncated

---

### Step 1.2: Add Regime Weights to Feature Builder (1 hour)

**File to modify:** `scripts/features/build_all_features.py`

**Add function:**

```python
def apply_regime_weights(df):
    """Apply regime-based training weights (50-1000 scale)"""
    
    # UPDATED REGIME WEIGHTS (November 17, 2025)
    # Changed from extreme 50-5000 to moderate 50-1000
    # Rationale: Balanced recency bias without gradient domination
    
    REGIME_WEIGHTS = {
        "historical_pre2000": 50,           # Pattern learning only
        "pre_crisis_2000_2007": 120,        # Baseline patterns
        "precrisis_2000_2007": 120,         # Alias
        "gfc_2008_2009": 300,               # Crisis volatility
        "financial_crisis_2008_2009": 300,  # Alias
        "qe_2010_2016": 180,                # QE era
        "qe_supercycle_2010_2014": 180,     # Alias
        "trade_war_2017_2019": 500,         # HIGH - Policy relevance
        "tradewar_2017_2019": 500,          # Alias
        "covid_crash_2020": 350,            # Supply shock
        "covid_2020_2021": 350,             # Alias
        "reopening_2020_2021": 400,         # Recovery
        "inflation_2021_2022": 650,         # VERY HIGH - Current macro
        "inflation_2021_2023": 650,         # Alias
        "tightening_2022_2023": 480,        # Fed policy
        "trump_2023_2025": 1000,            # MAXIMUM - Current regime
        "commodity_crash_2014_2016": 400,   # Crash dynamics
        "allhistory": 1                     # Fallback (should not be used)
    }
    
    print("\n" + "="*80)
    print("APPLYING REGIME WEIGHTS")
    print("="*80)
    
    # Check regime column exists
    if 'market_regime' not in df.columns:
        raise ValueError("market_regime column missing - check join with regime_calendar")
    
    # Assert every date has a regime
    missing_regime = df['market_regime'].isnull().sum()
    if missing_regime > 0:
        raise ValueError(f"{missing_regime} rows missing regime assignment")
    
    print(f"✅ All rows have regime assignment")
    
    # Apply weights
    df['training_weight'] = df['market_regime'].map(REGIME_WEIGHTS).astype('float64')
    
    # Check for unmapped regimes
    missing_weight = df['training_weight'].isnull().sum()
    if missing_weight > 0:
        missing_regimes = df[df['training_weight'].isnull()]['market_regime'].unique()
        raise ValueError(
            f"Missing weight mapping for {len(missing_regimes)} regimes: {missing_regimes.tolist()}\n"
            f"Add these to REGIME_WEIGHTS dict in apply_regime_weights()"
        )
    
    # Verify weight range (50-1000, not 50-5000!)
    min_w = df['training_weight'].min()
    max_w = df['training_weight'].max()
    
    assert min_w >= 50, f"Weight too low: {min_w} (minimum is 50)"
    assert max_w <= 1000, f"Weight too high: {max_w} (maximum is 1000, not 5000!)"
    
    print(f"✅ Training weights applied: {min_w:.0f} to {max_w:.0f}")
    print(f"✅ Regimes present: {df['market_regime'].nunique()}")
    
    # Show distribution
    print("\nRegime Distribution:")
    regime_dist = df.groupby('market_regime').agg({
        'training_weight': 'first',
        'date': 'count'
    }).rename(columns={'date': 'row_count'}).sort_values('training_weight', ascending=False)
    print(regime_dist.to_string())
    
    # Verify no "allhistory" dominance (should be minority)
    if 'allhistory' in df['market_regime'].values:
        allhist_pct = (df['market_regime'] == 'allhistory').sum() / len(df) * 100
        if allhist_pct > 10:
            print(f"\n⚠️  WARNING: {allhist_pct:.1f}% of rows are 'allhistory' (should be <10%)")
            print("  This suggests regime_calendar join is not working properly")
    
    print("="*80 + "\n")
    
    return df
```

**In main build_features_single_pass() function, add BEFORE saving:**

```python
def build_features_single_pass():
    """Execute declarative joins, calculate all features"""
    
    # Step 1: Execute joins per spec
    from scripts.assemble.execute_joins import JoinExecutor
    executor = JoinExecutor(DRIVE / "registry/join_spec.yaml")
    df_base = executor.execute()  # All sources joined
    
    # Step 2: Calculate features (all categories)
    df_features = calculate_technical_indicators(df_base)
    df_features = calculate_cross_asset_features(df_features)
    df_features = calculate_volatility_features(df_features)
    df_features = calculate_seasonal_features(df_features)
    df_features = calculate_macro_regime_features(df_features)
    df_features = calculate_weather_aggregations(df_features)
    
    # Step 3: Add regime columns
    df_features = add_regime_columns(df_features)
    
    # Step 4: ADD THIS - Apply regime weights (50-1000 scale)
    df_features = apply_regime_weights(df_features)
    
    # Step 5: Add override flags
    df_features = add_override_flags(df_features)
    
    # Step 6: Save to features/ (single source of truth)
    df_features.to_parquet(DRIVE / "TrainingData/features/master_features_2000_2025.parquet")
    
    print(f"✅ Features built: {len(df_features)} rows × {len(df_features.columns)} cols")
    return df_features
```

---

### Step 1.3: Create Regime Weights Registry (30 min)

**File to create:** `registry/regime_weights.yaml`

```yaml
version: "2.0"
description: "Regime-based training weights - UPDATED Nov 17, 2025"
last_updated: "2025-11-17"

# IMPORTANT: Changed from 50-5000 to 50-1000
# Reason: 5000 was too extreme, caused gradient domination
# New scale: 20x differential (moderate recency bias)

scale:
  min: 50
  max: 1000
  differential: "20x (not 100x)"

regimes:
  historical_pre2000:
    weight: 50
    start_date: "1990-01-01"
    end_date: "1999-12-31"
    description: "Pre-2000 historical - pattern learning only"
    rationale: "Oldest data, least relevant to current regime"
    
  pre_crisis_2000_2007:
    weight: 120
    start_date: "2000-01-01"
    end_date: "2007-12-31"
    description: "Pre-crisis baseline patterns"
    rationale: "Stable period, baseline for normal conditions"
    
  gfc_2008_2009:
    weight: 300
    start_date: "2008-01-01"
    end_date: "2009-12-31"
    description: "Global Financial Crisis - volatility learning"
    rationale: "Extreme volatility, correlation breakdown, crisis patterns"
    
  qe_2010_2016:
    weight: 180
    start_date: "2010-01-01"
    end_date: "2016-12-31"
    description: "QE era - commodity supercycle"
    rationale: "Zero rates, China boom, biofuel expansion"
    
  trade_war_2017_2019:
    weight: 500
    start_date: "2017-01-01"
    end_date: "2019-12-31"
    description: "US-China trade war - HIGH policy relevance"
    rationale: "Most similar to current Trump 2.0, tariff impacts, ag trade disruption"
    
  covid_crash_2020:
    weight: 350
    start_date: "2020-01-01"
    end_date: "2020-12-31"
    description: "COVID crash - supply chain disruption"
    rationale: "Supply shocks, demand destruction, volatility spikes"
    
  reopening_2020_2021:
    weight: 400
    start_date: "2020-01-01"
    end_date: "2021-12-31"
    description: "Post-COVID reopening"
    rationale: "Recovery patterns, supply normalization"
    
  inflation_2021_2022:
    weight: 650
    start_date: "2021-01-01"
    end_date: "2022-12-31"
    description: "Inflation surge - VERY HIGH macro relevance"
    rationale: "Current macro regime, high relevance to commodity prices"
    
  tightening_2022_2023:
    weight: 480
    start_date: "2022-01-01"
    end_date: "2023-12-31"
    description: "Fed tightening cycle"
    rationale: "Rate hikes, dollar strength, commodity pressure"
    
  trump_2023_2025:
    weight: 1000
    start_date: "2023-01-01"
    end_date: "2025-12-31"
    description: "Trump 2.0 era - MAXIMUM (current regime)"
    rationale: "Current regime, highest recency, maximum relevance"

# Effective weight distribution (with 6,200 total rows):
# Trump ~700 rows × 1000 = 700,000 effective
# Trade War ~750 rows × 500 = 375,000 effective
# Inflation ~500 rows × 650 = 325,000 effective
# Other ~4,250 rows × avg 250 = 1,062,500 effective
# ------------------------------------------------
# Total: ~2,462,500 effective rows
# Trump influence: ~28% (was ~50% with 5000 weight - more balanced now)
```

---

### Step 1.4: Create Surface Verification Script (30 min)

**File to create:** `scripts/qa/triage_surface.py`

```python
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
    actual_start = df['date'].min()
    
    if actual_start > expected_start:
        print(f"  ❌ Start date {actual_start} > expected {expected_start}")
        print(f"  ❌ MISSING 20 YEARS OF DATA (2000-2019)!")
        passed = False
    else:
        date_span_years = (df['date'].max() - df['date'].min()).days / 365.25
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
                regimes = df['market_regime'].nunique()
                weights_ok = df['training_weight'].min() >= 50 and df['training_weight'].max() <= 1000
                date_ok = df['date'].min() <= pd.Timestamp("2000-01-03")
                
                status = "✅" if (regimes >= 7 and weights_ok and date_ok) else "❌"
                print(f"  {status} {export.name}: {len(df)} rows, {regimes} regimes")
    
    return passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

---

### Step 1.5: Rebuild Training Surface (2-3 hours)

**PRE-REQUISITE:** Create staging files first!

**Execute the rebuild:**

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"

# STEP 0: Create missing staging files (CRITICAL!)
echo "📋 Step 0: Creating staging files from raw data..."
python3 scripts/staging/create_staging_files.py

# Backup current (broken) state
mkdir -p TrainingData/backup_20251117
cp -r TrainingData/features TrainingData/backup_20251117/ 2>/dev/null || true
cp -r TrainingData/exports TrainingData/backup_20251117/ 2>/dev/null || true

# Rebuild with patched executor
echo "🔧 Rebuilding training surface with fixed executor..."
python3 scripts/features/build_all_features.py

# Create horizon exports
echo "📦 Creating horizon-specific exports..."
python3 scripts/features/create_horizon_exports.py  # If separate script

# Verify
echo "✅ Running verification..."
python3 scripts/qa/triage_surface.py
```

**Expected output from triage:**
```
==================================================================================
TRAINING SURFACE TRIAGE: zl_training_prod_allhistory_1m.parquet
==================================================================================

📊 Basic Stats:
  Rows: 6,227
  Columns: 305
  Date range: 2000-11-13 → 2025-11-06

📅 Date Coverage:
  ✅ Start date OK: 2000-11-13
  ✅ Coverage: 25.0 years

🏛️  Regime Coverage:
  Unique regimes: 9

  Distribution:
    trump_2023_2025              :   700 rows ( 11.2%)
    inflation_2021_2022          :   500 rows (  8.0%)
    trade_war_2017_2019          :   750 rows ( 12.0%)
    covid_2020_2021              :   250 rows (  4.0%)
    pre_crisis_2000_2007         :  1750 rows ( 28.1%)
    gfc_2008_2009                :   250 rows (  4.0%)
    qe_2010_2016                 :  1500 rows ( 24.1%)
    historical_pre2000           :   500 rows (  8.0%)
    allhistory                   :    27 rows (  0.4%)

  ✅ Regime count OK: 9

⚖️  Training Weights:
  Range: 50 to 1000
  ✅ Weights OK: 50-1000
  Unique weights: [50, 120, 180, 300, 350, 400, 500, 650, 1000]

🎯 Target Coverage:
  Coverage: 97.2%
  ✅ Target coverage OK

🔧 Features:
  ✅ Feature count OK: 305

==================================================================================
✅ ALL CHECKS PASSED - Surface is GOOD
==================================================================================
```

**If checks FAIL:**
- Review execute_joins.py patches applied correctly
- Check join_spec.yaml is correct
- Verify regime_calendar table has all dates (1990-2025)
- Debug null_policy implementation
- Re-run build

---

### Step 1.6: Verify Files Created (15 min)

**Check folders are populated:**

```bash
# Check features folder
echo "📁 Features folder:"
ls -lh "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/features/"
# Expected: master_features_2000_2025.parquet (~50-100 MB)

# Check exports folder
echo "📁 Exports folder:"
ls -lh "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/"
# Expected: zl_training_prod_allhistory_{1w,1m,3m,6m,12m}.parquet (10 files total)

# Quick row count check
echo "📊 Export row counts:"
for f in /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/exports/zl_training_prod_*.parquet; do
    python3 -c "import pandas as pd; df=pd.read_parquet('$f'); print(f'$(basename $f): {len(df)} rows, {df[\"date\"].min()} to {df[\"date\"].max()}')"
done
```

**Success criteria:**
- ✅ `features/master_features_2000_2025.parquet` exists
- ✅ 10 export files exist (5 prod + 5 full surface)
- ✅ All files have ~6,000-6,200 rows (not 1,400!)
- ✅ All files have 2000-2025 date range (not 2020-2025!)
- ✅ Triage script passes

---

### Phase 1 Complete Checklist

- [ ] `execute_joins.py` patched with null_policy support
- [ ] `execute_joins.py` has all missing tests implemented
- [ ] `build_all_features.py` has apply_regime_weights() function
- [ ] `build_all_features.py` calls apply_regime_weights() before export
- [ ] `registry/regime_weights.yaml` created with 50-1000 scale
- [ ] `scripts/qa/triage_surface.py` created
- [ ] Surface rebuilt successfully
- [ ] Triage script passes all checks
- [ ] Features folder populated
- [ ] Exports folder has 10 files
- [ ] All files have 2000-2025 range
- [ ] All files have 7+ regimes
- [ ] All files have weights 50-1000

**When ALL checked:** ✅ Training surface is FIXED. Proceed to Phase 2.

---

## PHASE 2: ALPHA VANTAGE INTEGRATION (After Phase 1 Complete)

### Overview

**Now that training surface is fixed, integrate Alpha Vantage data.**

**Strategy:**
- Replace Yahoo commodities/FX/indices with Alpha (consolidation)
- Replace NewsAPI with Alpha NEWS_SENTIMENT (consolidation)
- Add ES futures data (new capability)
- Add options data (new capability)
- Use local TA + weekly Alpha validation (hybrid approach)

**Critical:** Phase 1 must be complete BEFORE starting. Otherwise Alpha data will get broken regimes.

---

### Data Source Final Split

#### KEEP:
- **Yahoo Finance:** ZL=F ONLY
- **FRED:** ALL 30+ economic series (shared by ZL and ES)
- **Weather:** NOAA, INMET, SMN (ZL agricultural forecasting)
- **Government:** CFTC, USDA, EIA (ZL agricultural data)

#### REPLACE with Alpha Vantage:
- **Commodities:** Yahoo ZS,ZM,ZC,ZW,CL,NG,CT,GC,SI → Alpha CORN,WHEAT,WTI,NATURAL_GAS,COTTON,etc.
- **FX:** Yahoo USD/BRL,USD/CNY,etc. → Alpha FX_DAILY
- **Indices:** Yahoo SPY,DIA,QQQ → Alpha TIME_SERIES_DAILY
- **Sentiment:** NewsAPI → Alpha NEWS_SENTIMENT

#### ADD (New from Alpha):
- **ES Futures (Private Trading Page):** ES=F (S&P 500 E-mini futures contract) - Multi-timeframe intraday
  - Intraday: 5min, 15min, 1hr, 4hr, 8hr
  - Daily+: 1day, 3day, 7day, 30day
  - Longer-term: 3mo, 6mo
  - Total: 11 horizons for intensive forecasting
- **Options:** SOYB, CORN, WEAT, DBA (agricultural) + SPY (for ES correlation) options chains
- **Extended FX:** USD/INR, USD/MYR, USD/IDR, USD/RUB (not in Yahoo)
- **Additional Commodities:** Brent, Sugar, Coffee, Copper, Aluminum

---

### ES Futures Naming (Matches ZL Convention)

**Asset:** ES (S&P 500 E-mini Futures Contract) - **NOT SPY**
- ES=F (futures contract) is the primary asset
- SPY (ETF) may be used as data proxy if ES=F not available in Alpha Vantage
- Options: SPY options used for ES correlation (ES options limited availability)

**Pattern:** `es_training_{scope}_{regime}_{horizon}`

**ALL Timeframes Required:**

**Intraday:**
- 5min (5-minute bars)
- 15min (15-minute bars)
- 1hr (1-hour bars)
- 4hr (4-hour bars)
- 8hr (8-hour bars)

**Daily+:**
- 1day (daily bars)
- 3day (3-day forecast)
- 7day (weekly forecast)
- 30day (monthly forecast)

**Longer-term:**
- 3mo (3-month forecast)
- 6mo (6-month forecast)

**Total ES Horizons:** 11 timeframes (vs ZL's 5)

---

**BigQuery Tables (ALL 11 horizons):**
```
training.es_training_prod_allhistory_5min
training.es_training_prod_allhistory_15min
training.es_training_prod_allhistory_1hr
training.es_training_prod_allhistory_4hr
training.es_training_prod_allhistory_8hr
training.es_training_prod_allhistory_1day
training.es_training_prod_allhistory_3day
training.es_training_prod_allhistory_7day
training.es_training_prod_allhistory_30day
training.es_training_prod_allhistory_3mo
training.es_training_prod_allhistory_6mo
```

**Local Exports (ALL 11 files):**
```
TrainingData/exports/es_training_prod_allhistory_5min.parquet
TrainingData/exports/es_training_prod_allhistory_15min.parquet
TrainingData/exports/es_training_prod_allhistory_1hr.parquet
TrainingData/exports/es_training_prod_allhistory_4hr.parquet
TrainingData/exports/es_training_prod_allhistory_8hr.parquet
TrainingData/exports/es_training_prod_allhistory_1day.parquet
TrainingData/exports/es_training_prod_allhistory_3day.parquet
TrainingData/exports/es_training_prod_allhistory_7day.parquet
TrainingData/exports/es_training_prod_allhistory_30day.parquet
TrainingData/exports/es_training_prod_allhistory_3mo.parquet
TrainingData/exports/es_training_prod_allhistory_6mo.parquet
```

**Model Paths:**
```
Models/local/es/horizon_5min/prod/baselines/lstm/
Models/local/es/horizon_15min/prod/baselines/xgboost/
Models/local/es/horizon_1hr/prod/baselines/tcn/
Models/local/es/horizon_4hr/prod/advanced/attention/
Models/local/es/horizon_8hr/prod/advanced/lstm_tcn/
Models/local/es/horizon_1day/prod/ensemble/weighted/
Models/local/es/horizon_7day/prod/ensemble/meta/
Models/local/es/horizon_30day/prod/advanced/nbeats/
```

**Shared Infrastructure (ZL + ES - Collect Once, Use Twice):**
- FRED macro data (rates, yields, VIX, dollar) - 100% reused
- Regime calendar and weights - 100% reused
- Alpha news & sentiment - 100% reused
- CFTC positioning data - 100% reused
- **ES reuses ~90% of ZL infrastructure**

**ES-Specific Data:**
- ES=F intraday OHLCV (5min, 15min, 1hr, 4hr, 8hr)
- ES=F daily OHLCV
- SPY options (used for ES volatility signals)
- ES technical indicators (all timeframes)

---

### Alpha Vantage API Call Budget

**Daily Collections (~30 calls):**
- Commodities: 12 calls (CORN, WHEAT, WTI, BRENT, NATURAL_GAS, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM, SOYB, ZM)
- FX: 9 calls (USD/BRL, USD/CNY, USD/ARS, USD/INR, USD/MYR, USD/IDR, USD/RUB, USD/CAD, EUR/USD)
- ES intraday: 3 calls (SPY 5min, 15min, 60min)
- SPY daily: 1 call
- SPY options: 1 call
- News: 2 calls
- **Total: ~28-30 calls/day** ✅ Within Plan75

**Weekly Collections (~50 calls on Sunday):**
- Technical indicator validation: 40-50 calls (sample 10 indicators × 5 symbols)
- Commodity options: 4 calls (SOYB, CORN, WEAT, DBA)
- **Total: ~44-54 calls/week** ✅ Within Plan75

**Plan75 Limit:** 75 calls/minute = 4,500 calls/hour  
**Usage:** ~200-250 calls/week = **Well within limits**

---

### Week 1: Schema Audit + Infrastructure (Day 1-3)

**PRE-REQUISITE: Create Missing Staging Files (Task 2.0)**

Before any Alpha work, ensure existing staging files exist for join pipeline.

**Task 2.0: Create Missing Staging Files (2 hours) - CRITICAL PRE-REQUISITE!**

**PROBLEM:** Join pipeline expects staging files that don't exist yet.

**Create staging files from existing raw data:**

```python
#!/usr/bin/env python3
"""
Create staging files from raw data for join pipeline.
MUST run before execute_joins.py can work!
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def create_yahoo_staging():
    """Create staging/yahoo_historical_all_symbols.parquet"""
    
    print("Creating Yahoo staging file...")
    
    # Read all Yahoo price files
    yahoo_dir = DRIVE / "raw/yahoo_finance/prices"
    all_symbols = []
    
    for category in ['commodities', 'currencies', 'indices', 'etfs']:
        cat_dir = yahoo_dir / category
        if not cat_dir.exists():
            continue
        
        for parquet_file in cat_dir.glob("*.parquet"):
            df = pd.read_parquet(parquet_file)
            # Standardize date column
            if 'Date' in df.columns:
                df['date'] = pd.to_datetime(df['Date']).dt.date
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            all_symbols.append(df)
            print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    # Combine all symbols
    combined = pd.concat(all_symbols, ignore_index=True)
    
    # Save to staging
    staging_file = DRIVE / "staging/yahoo_historical_all_symbols.parquet"
    combined.to_parquet(staging_file, index=False)
    print(f"✅ Created: {staging_file} ({len(combined)} rows)")
    
    return combined

def create_fred_staging():
    """Create staging/fred_macro_2000_2025.parquet"""
    
    print("Creating FRED staging file...")
    
    fred_dir = DRIVE / "raw/fred"
    all_series = []
    
    for parquet_file in fred_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        # Standardize date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        all_series.append(df)
        print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    # Merge all FRED series on date
    if all_series:
        combined = all_series[0]
        for df in all_series[1:]:
            combined = combined.merge(df, on='date', how='outer')
        
        # Filter to 2000-2025
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined[(combined['date'] >= '2000-01-01') & (combined['date'] <= '2025-12-31')]
        combined['date'] = combined['date'].dt.date
        
        staging_file = DRIVE / "staging/fred_macro_2000_2025.parquet"
        combined.to_parquet(staging_file, index=False)
        print(f"✅ Created: {staging_file} ({len(combined)} rows)")
        return combined
    
    print("⚠️  No FRED files found")
    return None

def create_weather_staging():
    """Create staging/noaa_weather_2000_2025.parquet"""
    
    print("Creating NOAA weather staging file...")
    
    # Check if already exists
    staging_file = DRIVE / "staging/weather_2000_2025.parquet"
    if staging_file.exists():
        print(f"✅ Already exists: {staging_file}")
        return pd.read_parquet(staging_file)
    
    noaa_dir = DRIVE / "raw/noaa"
    all_weather = []
    
    for parquet_file in noaa_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        all_weather.append(df)
        print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    if all_weather:
        combined = pd.concat(all_weather, ignore_index=True)
        # Filter to 2000-2025
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined[(combined['date'] >= '2000-01-01') & (combined['date'] <= '2025-12-31')]
        combined['date'] = combined['date'].dt.date
        
        # Rename to match join_spec.yaml
        staging_file = DRIVE / "staging/noaa_weather_2000_2025.parquet"
        combined.to_parquet(staging_file, index=False)
        print(f"✅ Created: {staging_file} ({len(combined)} rows)")
        return combined
    
    print("⚠️  No NOAA files found")
    return None

def create_cftc_staging():
    """Create staging/cftc_cot_2006_2025.parquet"""
    
    print("Creating CFTC staging file...")
    
    cftc_dir = DRIVE / "raw/cftc"
    all_cftc = []
    
    for parquet_file in cftc_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        all_cftc.append(df)
        print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    if all_cftc:
        combined = pd.concat(all_cftc, ignore_index=True)
        # Filter to 2006-2025 (CFTC starts 2006)
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined[(combined['date'] >= '2006-01-01') & (combined['date'] <= '2025-12-31')]
        combined['date'] = combined['date'].dt.date
        
        staging_file = DRIVE / "staging/cftc_cot_2006_2025.parquet"
        combined.to_parquet(staging_file, index=False)
        print(f"✅ Created: {staging_file} ({len(combined)} rows)")
        return combined
    
    print("⚠️  No CFTC files found")
    return None

def create_usda_staging():
    """Create staging/usda_nass_2000_2025.parquet"""
    
    print("Creating USDA staging file...")
    
    usda_dir = DRIVE / "raw/usda"
    all_usda = []
    
    for parquet_file in usda_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        all_usda.append(df)
        print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    if all_usda:
        combined = pd.concat(all_usda, ignore_index=True)
        # Filter to 2000-2025
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined[(combined['date'] >= '2000-01-01') & (combined['date'] <= '2025-12-31')]
        combined['date'] = combined['date'].dt.date
        
        staging_file = DRIVE / "staging/usda_nass_2000_2025.parquet"
        combined.to_parquet(staging_file, index=False)
        print(f"✅ Created: {staging_file} ({len(combined)} rows)")
        return combined
    
    print("⚠️  No USDA files found")
    return None

def create_eia_staging():
    """Create staging/eia_biofuels_2010_2025.parquet"""
    
    print("Creating EIA staging file...")
    
    eia_dir = DRIVE / "raw/eia"
    all_eia = []
    
    for parquet_file in eia_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        all_eia.append(df)
        print(f"  Loaded {parquet_file.name}: {len(df)} rows")
    
    if all_eia:
        combined = pd.concat(all_eia, ignore_index=True)
        # Filter to 2010-2025 (EIA biofuels starts 2010)
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined[(combined['date'] >= '2010-01-01') & (combined['date'] <= '2025-12-31')]
        combined['date'] = combined['date'].dt.date
        
        staging_file = DRIVE / "staging/eia_biofuels_2010_2025.parquet"
        combined.to_parquet(staging_file, index=False)
        print(f"✅ Created: {staging_file} ({len(combined)} rows)")
        return combined
    
    print("⚠️  No EIA files found")
    return None

def main():
    """Create all staging files"""
    
    print("="*80)
    print("CREATING STAGING FILES FOR JOIN PIPELINE")
    print("="*80)
    
    # Ensure staging directory exists
    staging_dir = DRIVE / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # Create all staging files
    create_yahoo_staging()
    create_fred_staging()
    create_weather_staging()
    create_cftc_staging()
    create_usda_staging()
    create_eia_staging()
    
    print("\n" + "="*80)
    print("✅ STAGING FILES CREATED")
    print("="*80)
    print("Ready for join pipeline execution!")

if __name__ == "__main__":
    main()
```

**File:** `scripts/staging/create_staging_files.py`

**Run BEFORE Phase 1 Step 1.5 (Rebuild Training Surface)**

---

**Task 2.1: Audit Existing BigQuery Schemas (4 hours)**

Query all existing tables to understand current patterns:

```sql
-- Check forecasting_data_warehouse dataset structure (PRIMARY DATASET)
SELECT table_name, column_name, data_type, is_partitioning_column
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name LIKE '%commodity%' OR table_name LIKE '%fx%' OR table_name LIKE '%technical%'
ORDER BY table_name, ordinal_position;

-- Check existing commodity tables
SELECT table_name, ddl
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%commodity%' OR table_name LIKE '%prices%';

-- Check existing FX tables
SELECT table_name, ddl
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%fx%' OR table_name LIKE '%currency%';

-- Check existing technical indicator tables (if any)
SELECT table_name, ddl
FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%technical%' OR table_name LIKE '%indicator%';

-- Check if Alpha tables already exist
SELECT table_name, row_count, size_bytes
FROM `cbi-v14.forecasting_data_warehouse.__TABLES__`
WHERE table_name LIKE '%alpha%';
```

**Document findings:**
- Table naming patterns (commodity_crude_oil_prices vs crude_oil_prices)
- Column naming (symbol vs ticker, date vs trading_date)
- Partition strategies (BY date vs BY timestamp)
- Data types (FLOAT64 vs NUMERIC)

**Output:** Create `docs/schemas/EXISTING_BQ_PATTERNS.md` with findings

---

**Task 2.2: Design Alpha Tables Matching Existing Patterns (2 hours)**

**CRITICAL: Use SAME dataset and naming pattern as existing tables**

Based on audit, Alpha tables will use:
- **Dataset:** `forecasting_data_warehouse` (same as existing raw data)
- **Naming Pattern:** `{type}_{source}_{granularity}` (matches existing)

**Existing Pattern Examples:**
- `forecasting_data_warehouse.commodity_crude_oil_prices`
- `forecasting_data_warehouse.economic_indicators`
- `forecasting_data_warehouse.weather_data`

**Alpha Pattern (Matches):**
- `forecasting_data_warehouse.commodity_alpha_daily`
- `forecasting_data_warehouse.fx_alpha_daily`
- `forecasting_data_warehouse.technical_indicators_alpha_daily`
- `forecasting_data_warehouse.intraday_es_alpha`
- `forecasting_data_warehouse.news_sentiment_alpha`
- `forecasting_data_warehouse.options_snapshot_alpha`

**Rationale:** Keep all raw data in same dataset for consistency and easier querying.

---

**Task 2.3: Create BigQuery Tables (2 hours) - EXPANDED FOR 50+ INDICATORS**

Execute DDL after audit confirms patterns:

```sql
-- ==========================================
-- PRICE DATA TABLES
-- ==========================================

-- Commodities (Alpha replaces Yahoo for non-ZL)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.commodity_*
CREATE TABLE forecasting_data_warehouse.commodity_alpha_daily (
  date DATE,
  symbol STRING,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY date
CLUSTER BY symbol;

-- FX (Alpha replaces Yahoo)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.fx_*
CREATE TABLE forecasting_data_warehouse.fx_alpha_daily (
  date DATE,
  pair STRING,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY date
CLUSTER BY pair;

-- ==========================================
-- TECHNICAL INDICATORS (50+ INDICATORS) - CRITICAL NEW TABLE!
-- ==========================================

-- Wide Format for 50+ Daily Technical Indicators (matches current pattern)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.technical_indicators_*
CREATE TABLE forecasting_data_warehouse.technical_indicators_alpha_daily (
  date DATE,
  symbol STRING,
  
  -- Moving Averages (8 types)
  SMA_5 FLOAT64,
  SMA_10 FLOAT64,
  SMA_20 FLOAT64,
  SMA_50 FLOAT64,
  SMA_100 FLOAT64,
  SMA_200 FLOAT64,
  EMA_5 FLOAT64,
  EMA_10 FLOAT64,
  EMA_20 FLOAT64,
  EMA_50 FLOAT64,
  EMA_100 FLOAT64,
  EMA_200 FLOAT64,
  WMA_10 FLOAT64,
  WMA_20 FLOAT64,
  DEMA_20 FLOAT64,
  TEMA_20 FLOAT64,
  TRIMA_20 FLOAT64,
  KAMA_20 FLOAT64,
  MAMA_0_5 FLOAT64,
  FAMA_0_5 FLOAT64,
  T3_5 FLOAT64,
  
  -- Momentum Indicators (15 types)
  RSI_14 FLOAT64,
  MACD_line FLOAT64,
  MACD_signal FLOAT64,
  MACD_histogram FLOAT64,
  STOCH_K FLOAT64,
  STOCH_D FLOAT64,
  STOCHF_K FLOAT64,
  STOCHF_D FLOAT64,
  STOCHRSI_K FLOAT64,
  STOCHRSI_D FLOAT64,
  WILLR_14 FLOAT64,
  ADX_14 FLOAT64,
  ADXR_14 FLOAT64,
  APO_12_26 FLOAT64,
  PPO_12_26 FLOAT64,
  MOM_10 FLOAT64,
  BOP FLOAT64,
  CCI_20 FLOAT64,
  CMO_14 FLOAT64,
  ROC_10 FLOAT64,
  ROCR_10 FLOAT64,
  AROON_UP_14 FLOAT64,
  AROON_DOWN_14 FLOAT64,
  AROONOSC_14 FLOAT64,
  MFI_14 FLOAT64,
  TRIX_15 FLOAT64,
  ULTOSC_7_14_28 FLOAT64,
  DX_14 FLOAT64,
  MINUS_DI_14 FLOAT64,
  PLUS_DI_14 FLOAT64,
  MINUS_DM_14 FLOAT64,
  PLUS_DM_14 FLOAT64,
  
  -- Volatility Indicators (6 types)
  BBANDS_upper_20 FLOAT64,
  BBANDS_middle_20 FLOAT64,
  BBANDS_lower_20 FLOAT64,
  BBANDS_upper_50 FLOAT64,
  BBANDS_middle_50 FLOAT64,
  BBANDS_lower_50 FLOAT64,
  ATR_14 FLOAT64,
  NATR_14 FLOAT64,
  TRANGE FLOAT64,
  
  -- Volume Indicators (5 types)
  AD FLOAT64,
  ADOSC_3_10 FLOAT64,
  OBV FLOAT64,
  VWAP FLOAT64,
  
  -- Pattern Recognition (8 types)
  HT_TRENDLINE FLOAT64,
  HT_SINE_SINE FLOAT64,
  HT_SINE_LEADSINE FLOAT64,
  HT_TRENDMODE FLOAT64,
  HT_DCPERIOD FLOAT64,
  HT_DCPHASE FLOAT64,
  HT_PHASOR_INPHASE FLOAT64,
  HT_PHASOR_QUADRATURE FLOAT64,
  
  -- Price Transform (5 types)
  MIDPOINT_14 FLOAT64,
  MIDPRICE_14 FLOAT64,
  SAR FLOAT64,
  SAREXT FLOAT64,
  
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY date
CLUSTER BY symbol;

-- ES Intraday Multi-Timeframe (11 timeframes)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.intraday_*
CREATE TABLE forecasting_data_warehouse.intraday_es_alpha (
  timestamp TIMESTAMP,
  interval STRING,  -- '5min', '15min', '1hr', '4hr', '8hr'
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY DATE(timestamp)
CLUSTER BY interval;

-- ES Technical Indicators Intraday (Full schema matching daily)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.technical_indicators_*
CREATE TABLE forecasting_data_warehouse.technical_indicators_es_intraday_alpha (
  timestamp TIMESTAMP,
  interval STRING,  -- '5min', '15min', '1hr', '4hr', '8hr'
  
  -- Moving Averages (same as daily)
  SMA_5 FLOAT64, SMA_10 FLOAT64, SMA_20 FLOAT64, SMA_50 FLOAT64, SMA_100 FLOAT64, SMA_200 FLOAT64,
  EMA_5 FLOAT64, EMA_10 FLOAT64, EMA_20 FLOAT64, EMA_50 FLOAT64, EMA_100 FLOAT64, EMA_200 FLOAT64,
  WMA_10 FLOAT64, WMA_20 FLOAT64, DEMA_20 FLOAT64, TEMA_20 FLOAT64, TRIMA_20 FLOAT64,
  KAMA_20 FLOAT64, MAMA_0_5 FLOAT64, FAMA_0_5 FLOAT64, T3_5 FLOAT64,
  
  -- Momentum Indicators
  RSI_14 FLOAT64, MACD_line FLOAT64, MACD_signal FLOAT64, MACD_histogram FLOAT64,
  STOCH_K FLOAT64, STOCH_D FLOAT64, STOCHF_K FLOAT64, STOCHF_D FLOAT64,
  STOCHRSI_K FLOAT64, STOCHRSI_D FLOAT64, WILLR_14 FLOAT64, ADX_14 FLOAT64, ADXR_14 FLOAT64,
  APO_12_26 FLOAT64, PPO_12_26 FLOAT64, MOM_10 FLOAT64, BOP FLOAT64, CCI_20 FLOAT64,
  CMO_14 FLOAT64, ROC_10 FLOAT64, ROCR_10 FLOAT64, AROON_UP_14 FLOAT64, AROON_DOWN_14 FLOAT64,
  AROONOSC_14 FLOAT64, MFI_14 FLOAT64, TRIX_15 FLOAT64, ULTOSC_7_14_28 FLOAT64,
  DX_14 FLOAT64, MINUS_DI_14 FLOAT64, PLUS_DI_14 FLOAT64, MINUS_DM_14 FLOAT64, PLUS_DM_14 FLOAT64,
  
  -- Volatility Indicators
  BBANDS_upper_20 FLOAT64, BBANDS_middle_20 FLOAT64, BBANDS_lower_20 FLOAT64,
  BBANDS_upper_50 FLOAT64, BBANDS_middle_50 FLOAT64, BBANDS_lower_50 FLOAT64,
  ATR_14 FLOAT64, NATR_14 FLOAT64, TRANGE FLOAT64,
  
  -- Volume Indicators
  AD FLOAT64, ADOSC_3_10 FLOAT64, OBV FLOAT64, VWAP FLOAT64,
  
  -- Pattern Recognition
  HT_TRENDLINE FLOAT64, HT_SINE_SINE FLOAT64, HT_SINE_LEADSINE FLOAT64,
  HT_TRENDMODE FLOAT64, HT_DCPERIOD FLOAT64, HT_DCPHASE FLOAT64,
  HT_PHASOR_INPHASE FLOAT64, HT_PHASOR_QUADRATURE FLOAT64,
  
  -- Price Transform
  MIDPOINT_14 FLOAT64, MIDPRICE_14 FLOAT64, SAR FLOAT64, SAREXT FLOAT64,
  
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY DATE(timestamp)
CLUSTER BY interval;

-- News & Sentiment (Alpha replaces NewsAPI)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.news_*
CREATE TABLE forecasting_data_warehouse.news_sentiment_alpha (
  published_at TIMESTAMP,
  title STRING,
  url STRING,
  sentiment_score FLOAT64,
  sentiment_label STRING,
  relevance_score FLOAT64,
  tickers ARRAY<STRING>,
  topics ARRAY<STRING>,
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY DATE(published_at);

-- Options (NEW capability)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.options_*
CREATE TABLE forecasting_data_warehouse.options_snapshot_alpha (
  snapshot_ts TIMESTAMP,
  underlier STRING,
  expiration DATE,
  strike FLOAT64,
  right STRING,
  bid FLOAT64,
  ask FLOAT64,
  last FLOAT64,
  iv FLOAT64,
  delta FLOAT64,
  gamma FLOAT64,
  theta FLOAT64,
  vega FLOAT64,
  open_interest INT64,
  volume INT64,
  source STRING DEFAULT 'alpha_vantage',
  ingestion_ts TIMESTAMP
) PARTITION BY DATE(snapshot_ts)
CLUSTER BY underlier, expiration;

-- Metadata/Manifest Table (NEW)
-- MATCHES EXISTING PATTERN: forecasting_data_warehouse.manifest_*
CREATE TABLE forecasting_data_warehouse.collection_manifest_alpha (
  collection_date DATE,
  collection_ts TIMESTAMP,
  data_type STRING,  -- 'prices', 'indicators', 'options', 'news'
  symbols_collected ARRAY<STRING>,
  indicators_collected ARRAY<STRING>,
  api_calls_used INT64,
  rows_collected INT64,
  errors ARRAY<STRING>,
  validation_status STRING,
  local_file_path STRING,
  bq_table_updated STRING,
  ingestion_ts TIMESTAMP
) PARTITION BY collection_date;
```

---

### Task 2.4: Create Local Folder Structure (30 min) - NEW!

Create the required folder hierarchy for Alpha data:

```bash
# Create Alpha folder structure
mkdir -p "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha/"
cd "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha/"

# Price data folders
mkdir -p prices/{commodities,fx,indices}

# Technical indicators folder (CRITICAL!)
mkdir -p indicators/{daily,intraday}

# ES multi-timeframe folders
mkdir -p es_intraday/{5min,15min,1hr,4hr,8hr,1day,3day,7day,30day,3mo,6mo}

# Options & sentiment
mkdir -p options/{daily_snapshots,chains}
mkdir -p sentiment/daily

# Manifests for tracking
mkdir -p manifests/{daily,weekly,backfill}

# Staging folders for join-ready data
mkdir -p ../../staging/alpha/{daily,intraday}

# CRITICAL: Staging files must match join_spec.yaml naming
# Existing pattern: staging/{source}_{description}_{date_range}.parquet
# Alpha pattern: staging/alpha/daily/alpha_complete_ready_for_join.parquet
# Note: Alpha uses subfolder structure due to multi-timeframe complexity
```

**Expected Structure:**
```
TrainingData/
├── raw/
│   └── alpha/                          # NEW ALPHA ROOT
│       ├── prices/
│       │   ├── commodities/
│       │   │   ├── CORN_daily.parquet
│       │   │   ├── WHEAT_daily.parquet
│       │   │   └── ...
│       │   ├── fx/
│       │   │   ├── USD_BRL_daily.parquet
│       │   │   └── ...
│       │   └── indices/
│       │       └── SPY_daily.parquet
│       ├── indicators/                 # 50+ INDICATORS!
│       │   ├── daily/
│       │   │   ├── CORN_indicators.parquet  # All 50+ cols
│       │   │   ├── WHEAT_indicators.parquet
│       │   │   └── ...
│       │   └── intraday/
│       │       ├── ES_5min_indicators.parquet
│       │       └── ...
│       ├── es_intraday/               # 11 TIMEFRAMES
│       │   ├── 5min/
│       │   ├── 15min/
│       │   ├── 1hr/
│       │   ├── 4hr/
│       │   ├── 8hr/
│       │   ├── 1day/
│       │   ├── 3day/
│       │   ├── 7day/
│       │   ├── 30day/
│       │   ├── 3mo/
│       │   └── 6mo/
│       ├── options/
│       ├── sentiment/
│       └── manifests/                  # TRACKING
│           ├── daily/
│           │   └── 2025-11-17_manifest.json
│           └── weekly/
├── staging/
│   └── alpha/                         # JOIN-READY DATA
│       ├── daily/
│       │   ├── alpha_combined_daily.parquet  # Prices + 50+ indicators
│       │   └── alpha_ready_for_join.parquet
│       └── intraday/
│           ├── es_5min_complete.parquet
│           └── ...
└── exports/                           # FINAL TRAINING DATA
    ├── zl_training_prod_*.parquet    # Existing
    └── es_training_prod_*.parquet    # New (11 files)
```

---

### Task 2.4.5: Data Validation Framework (2 hours) - CRITICAL!

**NO FAKE DATA OR PLACEHOLDERS ALLOWED**

Create comprehensive validation system to prevent any fake/placeholder data:

**File:** `src/utils/data_validation.py`

```python
#!/usr/bin/env python3
"""
CRITICAL DATA VALIDATION FRAMEWORK
Prevents ANY fake/placeholder data from entering the pipeline
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json

class AlphaDataValidator:
    """Validate all Alpha Vantage data - NO PLACEHOLDERS ALLOWED"""
    
    def __init__(self):
        self.validation_log = []
        self.rejection_count = 0
        self.acceptance_count = 0
    
    def validate_dataframe(self, df, data_type, symbol):
        """
        CRITICAL VALIDATION - Reject ANY suspicious data
        """
        
        print(f"\n{'='*60}")
        print(f"VALIDATING {data_type} for {symbol}")
        print(f"{'='*60}")
        
        # CHECK 1: Not empty
        if df.empty:
            self._reject(f"EMPTY DATAFRAME for {symbol}")
            return False
        
        # CHECK 2: Minimum rows
        min_rows = {
            'daily': 100,      # At least 100 trading days
            'intraday': 1000,  # At least 1000 bars
            'indicators': 100   # At least 100 days of indicators
        }
        
        if len(df) < min_rows.get(data_type, 100):
            self._reject(f"INSUFFICIENT DATA: Only {len(df)} rows for {symbol}")
            return False
        
        # CHECK 3: No placeholder values
        suspicious_values = [
            0.0,          # All zeros
            1.0,          # All ones
            -999.0,       # Common placeholder
            999999.0,     # Common placeholder
            np.nan        # NaN values
        ]
        
        for col in df.select_dtypes(include=[np.number]).columns:
            unique_vals = df[col].nunique()
            
            # Check if column has suspiciously low variance
            if unique_vals == 1:
                self._reject(f"STATIC COLUMN {col}: Only one unique value")
                return False
            
            # Check if column is all NaN
            if df[col].isna().all():
                self._reject(f"ALL NaN in column {col}")
                return False
            
            # Check if column has >50% NaN
            nan_pct = df[col].isna().sum() / len(df)
            if nan_pct > 0.5:
                self._reject(f"HIGH NaN RATE in {col}: {nan_pct:.1%}")
                return False
        
        # CHECK 4: Price validation (OHLC logic)
        if 'open' in df.columns and 'close' in df.columns:
            # Prices should vary
            price_variance = df['close'].std()
            if price_variance < 0.01:
                self._reject(f"NO PRICE VARIANCE: std={price_variance}")
                return False
            
            # High should be >= Low
            if 'high' in df.columns and 'low' in df.columns:
                invalid_bars = df[df['high'] < df['low']]
                if len(invalid_bars) > 0:
                    self._reject(f"INVALID BARS: {len(invalid_bars)} with high < low")
                    return False
        
        # CHECK 5: Date validation
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
            # No future dates
            if df['date'].max() > pd.Timestamp.now() + timedelta(days=1):
                self._reject(f"FUTURE DATES FOUND: max={df['date'].max()}")
                return False
            
            # No ancient dates (before 1990)
            if df['date'].min() < pd.Timestamp('1990-01-01'):
                self._reject(f"ANCIENT DATES: min={df['date'].min()}")
                return False
        
        # CHECK 6: Technical indicator validation
        if 'RSI_14' in df.columns:
            # RSI must be 0-100
            invalid_rsi = df[(df['RSI_14'] < 0) | (df['RSI_14'] > 100)]
            if len(invalid_rsi) > 0:
                self._reject(f"INVALID RSI: {len(invalid_rsi)} values outside 0-100")
                return False
        
        # CHECK 7: Volume validation
        if 'volume' in df.columns:
            # Volume should not be negative
            if (df['volume'] < 0).any():
                self._reject(f"NEGATIVE VOLUME found")
                return False
            
            # Volume should vary
            if df['volume'].std() == 0:
                self._reject(f"NO VOLUME VARIANCE")
                return False
        
        # CHECK 8: Symbol consistency
        if 'symbol' in df.columns:
            if df['symbol'].nunique() != 1:
                self._reject(f"MULTIPLE SYMBOLS in single file: {df['symbol'].unique()}")
                return False
        
        # CHECK 9: Data freshness (for daily data)
        if data_type == 'daily' and 'date' in df.columns:
            latest_date = df['date'].max()
            days_old = (pd.Timestamp.now() - latest_date).days
            
            # Weekend-aware check
            if pd.Timestamp.now().weekday() < 5:  # Weekday
                if days_old > 3:
                    self._warn(f"STALE DATA: {days_old} days old")
        
        # CHECK 10: Calculate data hash for tracking
        data_hash = self._calculate_hash(df)
        
        # ALL CHECKS PASSED
        self._accept(f"✅ VALID: {symbol} {data_type} - {len(df)} rows, hash={data_hash[:8]}")
        return True
    
    def _reject(self, reason):
        """Log rejection with reason"""
        self.rejection_count += 1
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'REJECTED',
            'reason': reason
        }
        self.validation_log.append(entry)
        print(f"❌ REJECTED: {reason}")
        raise ValueError(f"Data validation failed: {reason}")
    
    def _accept(self, reason):
        """Log acceptance"""
        self.acceptance_count += 1
        entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'ACCEPTED',
            'reason': reason
        }
        self.validation_log.append(entry)
        print(f"✅ ACCEPTED: {reason}")
    
    def _warn(self, reason):
        """Log warning (doesn't reject)"""
        print(f"⚠️  WARNING: {reason}")
        self.validation_log.append({
            'timestamp': datetime.now().isoformat(),
            'status': 'WARNING',
            'reason': reason
        })
    
    def _calculate_hash(self, df):
        """Calculate hash of dataframe for verification"""
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values
        ).hexdigest()
    
    def save_validation_report(self, path):
        """Save validation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_validations': len(self.validation_log),
            'accepted': self.acceptance_count,
            'rejected': self.rejection_count,
            'log': self.validation_log
        }
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Validation Report:")
        print(f"   Accepted: {self.acceptance_count}")
        print(f"   Rejected: {self.rejection_count}")
        print(f"   Report saved: {path}")


class DataIntegrityChecker:
    """Check data integrity across the entire pipeline"""
    
    @staticmethod
    def check_no_placeholders(directory):
        """
        Scan ALL parquet files for placeholder/fake data
        """
        print("\n" + "="*80)
        print("SCANNING FOR PLACEHOLDER DATA")
        print("="*80)
        
        issues = []
        files_checked = 0
        
        for parquet_file in Path(directory).rglob("*.parquet"):
            files_checked += 1
            print(f"\nChecking: {parquet_file.name}")
            
            try:
                df = pd.read_parquet(parquet_file)
                
                # Check for empty
                if df.empty:
                    issues.append(f"EMPTY: {parquet_file}")
                    continue
                
                # Check for placeholder patterns
                for col in df.select_dtypes(include=[np.number]).columns:
                    # All zeros
                    if (df[col] == 0).all():
                        issues.append(f"ALL ZEROS in {col}: {parquet_file}")
                    
                    # All same value
                    if df[col].nunique() == 1:
                        issues.append(f"STATIC {col}: {parquet_file}")
                    
                    # Sequential integers (likely fake)
                    if len(df) > 10:
                        if (df[col][:10] == range(10)).all():
                            issues.append(f"SEQUENTIAL {col}: {parquet_file}")
                
            except Exception as e:
                issues.append(f"ERROR reading {parquet_file}: {e}")
        
        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE: {files_checked} files checked")
        
        if issues:
            print(f"❌ FOUND {len(issues)} ISSUES:")
            for issue in issues:
                print(f"   - {issue}")
            raise ValueError("Placeholder data detected!")
        else:
            print(f"✅ NO PLACEHOLDERS FOUND")
        
        return True


# Usage in collection pipeline:
def validate_before_save(df, symbol, data_type):
    """MUST call before saving any data"""
    validator = AlphaDataValidator()
    
    # This will RAISE if invalid
    validator.validate_dataframe(df, data_type, symbol)
    
    # Only reaches here if valid
    return True
```

---

### Week 2: Build Collectors (Day 4-8)

**Task 2.5: Build Alpha Vantage Client Wrapper (4 hours) - EXPANDED WITH VALIDATION**

**File:** `src/utils/alpha_vantage_client.py`

```python
#!/usr/bin/env python3
"""Alpha Vantage API client using MCP tools - WITH VALIDATION"""

import time
import pandas as pd
from datetime import datetime
from src.utils.keychain_manager import get_api_key
import numpy as np

class AlphaVantageClient:
    """Wrapper around MCP Alpha Vantage tools with rate limiting"""
    
    def __init__(self):
        self.api_key = get_api_key('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY not found in Keychain.\n"
                "Store with: security add-generic-password -a default "
                "-s cbi-v14.ALPHA_VANTAGE_API_KEY -w <key> -U"
            )
        
        self.call_count = 0
        self.last_call_time = None
        self.rate_limit_calls_per_minute = 75  # Plan75
        self.cache = {}  # Simple daily cache
    
    def _rate_limit(self):
        """Respect 75 calls/minute (Plan75)"""
        if self.last_call_time:
            elapsed = time.time() - self.last_call_time
            min_delay = 60.0 / self.rate_limit_calls_per_minute  # 0.8 seconds
            
            if elapsed < min_delay:
                sleep_time = min_delay - elapsed
                time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        self.call_count += 1
        
        if self.call_count % 10 == 0:
            print(f"  API calls used: {self.call_count}")
    
    def _check_cache(self, cache_key):
        """Check if we already fetched this today"""
        today = datetime.now().date()
        key = f"{today}_{cache_key}"
        return self.cache.get(key)
    
    def _save_cache(self, cache_key, data):
        """Save to daily cache"""
        today = datetime.now().date()
        key = f"{today}_{cache_key}"
        self.cache[key] = data
    
    def commodity_daily(self, symbol, outputsize='full'):
        """
        Get daily commodity prices from Alpha Vantage
        Uses: WTI, BRENT, NATURAL_GAS, WHEAT, CORN, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM
        """
        cache_key = f"commodity_{symbol}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # Map to Alpha endpoint
        # WTI, BRENT, NATURAL_GAS, WHEAT, CORN, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM
        # have dedicated endpoints
        
        # Will implement with actual MCP tool calls when executing
        # For now, structure showing expected implementation:
        """
        if symbol == 'WTI':
            result = mcp_alphavantage_WTI(interval='daily', datatype='csv')
        elif symbol == 'BRENT':
            result = mcp_alphavantage_BRENT(interval='daily', datatype='csv')
        # ... etc for each commodity
        else:
            # Generic equities
            result = mcp_alphavantage_TIME_SERIES_DAILY(symbol=symbol, outputsize=outputsize)
        
        # Parse CSV result into DataFrame
        df = pd.read_csv(io.StringIO(result))
        """
        
        df = pd.DataFrame()  # Placeholder - implement with MCP tools
        
        self._save_cache(cache_key, df)
        return df
    
    def fx_daily(self, from_currency, to_currency, outputsize='full'):
        """
        Get daily FX rates
        Example: from_currency='USD', to_currency='BRL'
        """
        cache_key = f"fx_{from_currency}{to_currency}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # Will use: mcp_alphavantage_FX_DAILY(from_symbol, to_symbol, outputsize)
        df = pd.DataFrame()  # Placeholder
        
        self._save_cache(cache_key, df)
        return df
    
    def news_sentiment(self, topics=None, tickers=None, limit=100):
        """Get news with sentiment scores"""
        cache_key = f"news_{topics}_{tickers}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # Will use: mcp_alphavantage_NEWS_SENTIMENT(topics, tickers, limit)
        df = pd.DataFrame()  # Placeholder
        
        self._save_cache(cache_key, df)
        return df
    
    def options_chain(self, symbol, require_greeks=True):
        """Get options chain with Greeks"""
        # No cache - options change frequently
        
        self._rate_limit()
        
        # Will use: mcp_alphavantage_REALTIME_OPTIONS(symbol, require_greeks)
        df = pd.DataFrame()  # Placeholder
        
        return df
    
    def intraday(self, symbol, interval='5min', outputsize='full'):
        """
        Get intraday data for ES (SPY)
        interval: 1min, 5min, 15min, 30min, 60min
        """
        cache_key = f"intraday_{symbol}_{interval}"
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached
        
        self._rate_limit()
        
        # Will use: mcp_alphavantage_TIME_SERIES_INTRADAY(symbol, interval, outputsize)
        df = pd.DataFrame()  # Placeholder
        
        self._save_cache(cache_key, df)
        return df
    
    def technical_indicator(self, function, symbol, interval='daily', **params):
        """
        Get technical indicator (for weekly validation)
        function: RSI, MACD, BBANDS, SMA, EMA, etc.
        """
        self._rate_limit()
        
        # Will use: mcp_alphavantage_RSI, mcp_alphavantage_MACD, etc.
        # Based on function parameter
        
        df = pd.DataFrame()  # Placeholder
        
        return df
```

---

**Task 2.6: Build Manifest System (2 hours) - EXPANDED**

**File:** `src/utils/manifest_generator.py`

```python
#!/usr/bin/env python3
"""Generate manifests for Alpha Vantage data collection tracking"""

import json
import hashlib
from datetime import datetime
from pathlib import Path

class ManifestGenerator:
    """Track all Alpha data collection for reproducibility"""
    
    def __init__(self, manifest_dir="/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha/manifests"):
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
    
    def create_manifest(self, collection_type, data):
        """Create manifest for a collection run"""
        
        manifest = {
            "collection_date": datetime.now().strftime("%Y-%m-%d"),
            "collection_ts": datetime.now().isoformat(),
            "collection_type": collection_type,  # 'daily', 'indicators', 'backfill'
            "data_summary": {
                "symbols_collected": data.get('symbols', []),
                "indicators_collected": data.get('indicators', []),
                "date_range": data.get('date_range', {}),
                "rows_collected": data.get('row_count', 0),
                "file_size_mb": data.get('file_size', 0) / 1024 / 1024
            },
            "api_usage": {
                "calls_made": data.get('api_calls', 0),
                "rate_limit": "75/min",
                "errors": data.get('errors', [])
            },
            "data_quality": {
                "null_counts": data.get('null_counts', {}),
                "validation_passed": data.get('validation', True),
                "warnings": data.get('warnings', [])
            },
            "file_locations": {
                "local_raw": data.get('local_path'),
                "local_staging": data.get('staging_path'),
                "bq_table": data.get('bq_table')
            },
            "checksums": {
                "raw_data_hash": self._calculate_hash(data.get('local_path')),
                "staging_data_hash": self._calculate_hash(data.get('staging_path'))
            }
        }
        
        # Save manifest
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_file = self.manifest_dir / f"{collection_type}_{date_str}.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Manifest saved: {manifest_file}")
        return manifest
    
    def _calculate_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        if not file_path or not Path(file_path).exists():
            return None
        
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
```

---

**Task 2.7: Build Staging Pipeline (6 hours) - CRITICAL NEW!**

**File:** `scripts/staging/prepare_alpha_for_joins.py`

```python
#!/usr/bin/env python3
"""
Prepare Alpha Vantage data for joining with existing pipeline.
Converts from raw Alpha format to join-ready wide format.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

def prepare_alpha_indicators():
    """
    Convert 50+ indicators from separate files to wide format.
    CRITICAL: Must handle 550 API calls worth of data efficiently.
    NO PLACEHOLDERS ALLOWED!
    """
    
    print("="*80)
    print("PREPARING ALPHA INDICATORS FOR JOINS - WITH VALIDATION")
    print("="*80)
    
    # Import validator
    from src.utils.data_validation import AlphaDataValidator, DataIntegrityChecker
    validator = AlphaDataValidator()
    
    # Step 1: Read all indicator files for each symbol
    indicators_dir = DRIVE / "raw/alpha/indicators/daily"
    staging_dir = DRIVE / "staging/alpha/daily"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    all_symbols_data = []
    
    for symbol in ['CORN', 'WHEAT', 'WTI', 'BRENT', 'NATURAL_GAS', 'COTTON', 'SUGAR', 'COFFEE', 'COPPER', 'ALUMINUM']:
        print(f"\nProcessing {symbol}...")
        
        # Read symbol's indicator file (has all 50+ indicators as columns)
        indicator_file = indicators_dir / f"{symbol}_indicators.parquet"
        if not indicator_file.exists():
            print(f"  ⚠️  Missing indicators for {symbol}")
            continue
        
        df = pd.read_parquet(indicator_file)
        df['symbol'] = symbol
        
        # Ensure date column is consistent
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
        elif 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date']).dt.date
        
        # CRITICAL: Validate before adding to collection
        validator.validate_dataframe(df, 'indicators', symbol)
        
        all_symbols_data.append(df)
        print(f"  ✅ Loaded {len(df)} days, {len(df.columns)} indicators")
    
    # Step 2: Combine all symbols
    combined = pd.concat(all_symbols_data, ignore_index=True)
    print(f"\n✅ Combined: {len(combined)} total rows, {combined['symbol'].nunique()} symbols")
    
    # Step 3: Pivot if needed (if data is in long format)
    # If already wide (each indicator is a column), skip this
    if 'indicator_name' in combined.columns:  # Long format
        print("\nPivoting from long to wide format...")
        combined_wide = combined.pivot_table(
            index=['date', 'symbol'],
            columns='indicator_name',
            values='indicator_value',
            aggfunc='first'
        ).reset_index()
    else:  # Already wide
        combined_wide = combined
        print("\nAlready in wide format")
    
    # Step 4: Validate combined data before saving
    print("\n🔍 Validating combined indicators before saving...")
    validator.validate_dataframe(combined_wide, 'indicators', 'ALL_SYMBOLS')
    
    # Step 5: Save to staging
    output_file = staging_dir / "alpha_indicators_wide.parquet"
    combined_wide.to_parquet(output_file, index=False)
    print(f"\n✅ Saved to staging: {output_file}")
    print(f"   Shape: {combined_wide.shape}")
    
    return combined_wide

def prepare_alpha_prices():
    """Prepare Alpha price data for joining"""
    
    print("\n" + "="*80)
    print("PREPARING ALPHA PRICES")
    print("="*80)
    
    # Import validator
    from src.utils.data_validation import AlphaDataValidator
    validator = AlphaDataValidator()
    
    prices_dir = DRIVE / "raw/alpha/prices/commodities"
    staging_dir = DRIVE / "staging/alpha/daily"
    
    all_prices = []
    
    for price_file in prices_dir.glob("*.parquet"):
        df = pd.read_parquet(price_file)
        symbol = price_file.stem.replace("_daily", "")
        df['symbol'] = symbol
        
        # Standardize date column
        if 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date']).dt.date
        
        # Keep only OHLCV columns
        keep_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        df = df[[c for c in keep_cols if c in df.columns]]
        
        # CRITICAL: Validate each symbol's prices
        validator.validate_dataframe(df, 'daily', symbol)
        
        all_prices.append(df)
        print(f"  {symbol}: {len(df)} days")
    
    combined_prices = pd.concat(all_prices, ignore_index=True)
    
    # Validate combined prices before saving
    print("\n🔍 Validating combined prices before saving...")
    validator.validate_dataframe(combined_prices, 'daily', 'ALL_SYMBOLS')
    
    # Save
    output_file = staging_dir / "alpha_prices_combined.parquet"
    combined_prices.to_parquet(output_file, index=False)
    print(f"\n✅ Saved prices: {output_file}")
    
    return combined_prices

def create_join_ready_file():
    """
    Merge prices + indicators into single join-ready file.
    This is what join_spec.yaml will reference.
    """
    
    print("\n" + "="*80)
    print("CREATING JOIN-READY ALPHA FILE")
    print("="*80)
    
    staging_dir = DRIVE / "staging/alpha/daily"
    
    # Read prepared files
    prices = pd.read_parquet(staging_dir / "alpha_prices_combined.parquet")
    indicators = pd.read_parquet(staging_dir / "alpha_indicators_wide.parquet")
    
    # Merge on date + symbol
    merged = prices.merge(
        indicators,
        on=['date', 'symbol'],
        how='outer'
    )
    
    print(f"Merged shape: {merged.shape}")
    print(f"Columns: {merged.shape[1]} total")
    print(f"  - Price columns: 5 (OHLCV)")
    print(f"  - Indicator columns: {merged.shape[1] - 7} (50+ indicators)")
    
    # CRITICAL: Validate merged data before saving
    from src.utils.data_validation import AlphaDataValidator
    validator = AlphaDataValidator()
    print("\n🔍 Validating final join-ready file before saving...")
    validator.validate_dataframe(merged, 'daily', 'ALPHA_COMPLETE')
    
    # Save final join-ready file
    output_file = staging_dir / "alpha_complete_ready_for_join.parquet"
    merged.to_parquet(output_file, index=False)
    
    print(f"\n✅ Join-ready file created: {output_file}")
    print(f"   This is what join_spec.yaml will use!")
    
    return merged

def main():
    """Run complete staging pipeline"""
    
    # 1. Prepare indicators (wide format)
    indicators_df = prepare_alpha_indicators()
    
    # 2. Prepare prices
    prices_df = prepare_alpha_prices()
    
    # 3. Create join-ready file
    final_df = create_join_ready_file()
    
    print("\n" + "="*80)
    print("STAGING PIPELINE COMPLETE")
    print("="*80)
    print(f"Final dataset: {final_df.shape}")
    print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    print(f"Symbols: {sorted(final_df['symbol'].unique())}")
    print("\nReady for joining with join_spec.yaml!")

if __name__ == "__main__":
    main()
```

---

**Task 2.8: Build BigQuery Sync Pipeline (4 hours) - NEW!**

**File:** `scripts/sync/sync_alpha_to_bigquery.py`

```python
#!/usr/bin/env python3
"""
Sync local Alpha Vantage data to BigQuery tables.
Run after local collection is complete.
"""

import pandas as pd
from pathlib import Path
from google.cloud import bigquery
from datetime import datetime
import json

class AlphaToBigQuerySync:
    """Push local Alpha data to BigQuery"""
    
    def __init__(self):
        self.client = bigquery.Client(project="cbi-v14")
        self.drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")
        
    def sync_technical_indicators(self):
        """Sync 50+ technical indicators to BigQuery"""
        
        print("\n" + "="*80)
        print("SYNCING TECHNICAL INDICATORS TO BIGQUERY")
        print("="*80)
        
        # Read staging file with all indicators
        staging_file = self.drive / "staging/alpha/daily/alpha_indicators_wide.parquet"
        df = pd.read_parquet(staging_file)
        
        # CRITICAL: Validate before BigQuery upload
        from src.utils.data_validation import AlphaDataValidator
        validator = AlphaDataValidator()
        print("🔍 Validating indicators before BigQuery sync...")
        validator.validate_dataframe(df, 'indicators', 'BQ_SYNC')
        
        # Add metadata
        df['source'] = 'alpha_vantage'
        df['ingestion_ts'] = datetime.now()
        
        # BigQuery table (MATCHES EXISTING PATTERN)
        table_id = "cbi-v14.forecasting_data_warehouse.technical_indicators_alpha_daily"
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Replace entire table
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            ),
            clustering_fields=["symbol"]
        )
        
        # Load to BigQuery
        print(f"Loading {len(df)} rows to {table_id}...")
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()  # Wait for completion
        
        print(f"✅ Loaded {job.output_rows} rows to BigQuery")
        
        # Update manifest
        self._update_manifest('indicators', {
            'rows_synced': len(df),
            'bq_table': table_id,
            'sync_time': datetime.now().isoformat()
        })
        
        return job
    
    def sync_prices(self):
        """Sync commodity/FX prices to BigQuery"""
        
        print("\n" + "="*80)
        print("SYNCING PRICES TO BIGQUERY")
        print("="*80)
        
        # Commodity prices
        commodity_file = self.drive / "staging/alpha/daily/alpha_prices_combined.parquet"
        df_commodity = pd.read_parquet(commodity_file)
        
        # CRITICAL: Validate before BigQuery upload
        from src.utils.data_validation import AlphaDataValidator
        validator = AlphaDataValidator()
        print("🔍 Validating prices before BigQuery sync...")
        validator.validate_dataframe(df_commodity, 'daily', 'BQ_SYNC')
        
        df_commodity['source'] = 'alpha_vantage'
        df_commodity['ingestion_ts'] = datetime.now()
        
        # Load commodities (MATCHES EXISTING PATTERN)
        table_id = "cbi-v14.forecasting_data_warehouse.commodity_alpha_daily"
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            ),
            clustering_fields=["symbol"]
        )
        
        print(f"Loading {len(df_commodity)} commodity prices...")
        job = self.client.load_table_from_dataframe(
            df_commodity, table_id, job_config=job_config
        )
        job.result()
        
        print(f"✅ Loaded {job.output_rows} commodity prices")
        
        # Similar for FX, indices...
        
        return job
    
    def sync_es_intraday(self):
        """Sync ES intraday data (11 timeframes)"""
        
        print("\n" + "="*80)
        print("SYNCING ES INTRADAY TO BIGQUERY")
        print("="*80)
        
        es_dir = self.drive / "raw/alpha/es_intraday"
        table_id = "cbi-v14.forecasting_data_warehouse.intraday_es_alpha"
        
        all_intervals = []
        
        for interval_dir in es_dir.iterdir():
            if not interval_dir.is_dir():
                continue
            
            interval = interval_dir.name  # '5min', '15min', etc.
            
            for parquet_file in interval_dir.glob("*.parquet"):
                df = pd.read_parquet(parquet_file)
                df['interval'] = interval
                df['source'] = 'alpha_vantage'
                df['ingestion_ts'] = datetime.now()
                all_intervals.append(df)
                print(f"  {interval}: {len(df)} bars")
        
        # Combine all intervals
        combined = pd.concat(all_intervals, ignore_index=True)
        
        # CRITICAL: Validate before BigQuery upload
        from src.utils.data_validation import AlphaDataValidator
        validator = AlphaDataValidator()
        print("\n🔍 Validating ES intraday before BigQuery sync...")
        validator.validate_dataframe(combined, 'intraday', 'ES_BQ_SYNC')
        
        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            ),
            clustering_fields=["interval"]
        )
        
        print(f"\nLoading {len(combined)} total ES bars...")
        job = self.client.load_table_from_dataframe(
            combined, table_id, job_config=job_config
        )
        job.result()
        
        print(f"✅ Loaded {job.output_rows} ES intraday bars")
        
        return job
    
    def _update_manifest(self, data_type, info):
        """Update collection manifest with sync info"""
        
        manifest_dir = self.drive / "raw/alpha/manifests/daily"
        today = datetime.now().strftime("%Y-%m-%d")
        manifest_file = manifest_dir / f"sync_{today}.json"
        
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
        else:
            manifest = {}
        
        manifest[data_type] = info
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def sync_all(self):
        """Run complete sync pipeline"""
        
        print("\n" + "="*80)
        print("ALPHA VANTAGE → BIGQUERY SYNC")
        print("="*80)
        
        # 1. Sync technical indicators (50+ columns)
        self.sync_technical_indicators()
        
        # 2. Sync prices
        self.sync_prices()
        
        # 3. Sync ES intraday
        self.sync_es_intraday()
        
        print("\n" + "="*80)
        print("✅ ALL DATA SYNCED TO BIGQUERY")
        print("="*80)

if __name__ == "__main__":
    syncer = AlphaToBigQuerySync()
    syncer.sync_all()
```

---

**Task 2.9: Update join_spec.yaml for Alpha Data (1 hour) - CRITICAL!**

Update `registry/join_spec.yaml` to include Alpha data:

**CRITICAL: Alpha join must come AFTER all existing joins to maintain join order**

```yaml
# Add AFTER regime join (last in sequence):
  
  # === JOIN: Alpha Vantage Combined Data (Prices + 50+ Indicators) ===
  # POSITION: After add_regimes (last join before feature engineering)
  - name: "add_alpha_enhanced"
    left: "<<add_regimes>>"  # Join after regimes, not after FRED!
    right: "staging/alpha/daily/alpha_complete_ready_for_join.parquet"
    on: ["date", "symbol"]  # Multi-key join!
    how: "left"
    null_policy:
      allow: true
      fill_method: "ffill"  # Forward fill indicators
    tests:
      - expect_rows_preserved
      - expect_indicators_count_gte: 50  # Verify 50+ indicators added
      - expect_columns_added: ["RSI_14", "MACD_line", "ATR_14", "BBANDS_upper_20"]
      - expect_null_rate_below: {"RSI_14": 0.10}  # <10% nulls after ffill
      - expect_date_range: ["2000-01-01", "2025-12-31"]  # Must maintain date range
```

**Join Order (Final):**
1. base_prices (Yahoo)
2. add_macro (FRED)
3. add_weather (NOAA)
4. add_cftc (CFTC)
5. add_usda (USDA)
6. add_biofuels (EIA)
7. add_regimes (Regime calendar)
8. **add_alpha_enhanced (Alpha Vantage) ← NEW, LAST JOIN**

---

**Task 2.10: Build Alpha Master Collector (8 hours)**

**File:** `scripts/ingest/collect_alpha_master.py`

[Previous code - updated to use new folder structure and manifest system]

---

### Week 3-4: Historical Backfill + Integration

**Task 2.13: Historical Backfill (8-10 hours)**

Run one-time backfill for all Alpha sources:

```bash
# Commodities + FX: 2000-present
python3 scripts/ingest/collect_alpha_master.py --backfill --start-date 2000-01-01

# ES intraday: Last 2 years (Alpha intraday limit)
python3 scripts/ingest/collect_alpha_master.py --backfill --es-only --start-date 2023-01-01
```

---

**Task 2.14: Update Feature Builder for Alpha Sources (6 hours)**

Modify `scripts/features/build_all_features.py` to integrate Alpha data:

**CRITICAL: Add validation certificate check at the start:**

**CRITICAL: Add Alpha Integration Strategy:**

```python
def build_features_single_pass():
    """
    Execute declarative joins, calculate all features.
    INTEGRATES: Existing calculations + Alpha Vantage indicators
    """
    
    # VALIDATION CHECKPOINT: Must have validation certificate
    cert_path = DRIVE / "TrainingData/validation_certificate.json"
    if not cert_path.exists():
        raise ValueError(
            "❌ VALIDATION CERTIFICATE MISSING!\n"
            "Run: python3 scripts/validation/final_alpha_validation.py\n"
            "Training cannot proceed without validation certificate."
        )
    
    print("\n" + "="*80)
    print("SINGLE-PASS FEATURE ENGINEERING")
    print("="*80)
    print("✅ Validation certificate found - proceeding with feature build")
    
    # Step 1: Execute joins per spec (includes Alpha join)
    print("\n📋 Step 1: Executing declarative joins...")
    import sys
    sys.path.insert(0, str(DRIVE / "scripts"))
    from assemble.execute_joins import JoinExecutor
    
    executor = JoinExecutor(DRIVE / "registry/join_spec.yaml")
    df_base = executor.execute()  # All sources joined (including Alpha)
    
    print(f"\n✅ Base joined: {len(df_base)} rows × {len(df_base.columns)} cols")
    print(f"   Includes Alpha indicators: {sum('RSI_14' in c or 'MACD' in c for c in df_base.columns)} columns")
    
    # Step 2: Calculate features (all categories)
    print("\n📊 Step 2: Feature engineering...")
    
    # Import feature calculation functions
    from feature_calculations import (
        calculate_technical_indicators,      # NOTE: May skip if Alpha provides
        calculate_cross_asset_features,       # KEEP: ZL correlations with FRED
        calculate_volatility_features,       # KEEP: Custom volatility
        calculate_seasonal_features,          # KEEP: Seasonality
        calculate_macro_regime_features,      # KEEP: FRED-based regimes
        calculate_weather_aggregations,       # KEEP: Weather features
        add_regime_columns,
        add_override_flags
    )
    
    # INTEGRATION STRATEGY:
    # - Alpha provides 50+ technical indicators (pre-calculated)
    # - Our calculations provide: correlations, volatility, seasonal, macro, weather
    # - Both are needed: Alpha for technicals, ours for custom features
    
    df_features = df_base.copy()
    
    # Check if Alpha indicators already present (from join)
    alpha_indicators_present = any('RSI_14' in c or 'MACD_line' in c for c in df_features.columns)
    
    if alpha_indicators_present:
        print("✅ Alpha technical indicators found in joined data")
        print("   Skipping calculate_technical_indicators() - using Alpha indicators")
        # Still calculate custom technical features that Alpha doesn't provide
        df_features = calculate_cross_asset_features(df_features)
    else:
        print("⚠️  Alpha indicators not found - calculating technical indicators")
        df_features = calculate_technical_indicators(df_features)
        df_features = calculate_cross_asset_features(df_features)
    
    # Always calculate these (Alpha doesn't provide):
    df_features = calculate_volatility_features(df_features)
    df_features = calculate_seasonal_features(df_features)
    df_features = calculate_macro_regime_features(df_features)
    df_features = calculate_weather_aggregations(df_features)
    
    # Step 3: Add regime columns
    df_features = add_regime_columns(df_features)
    
    # Step 4: Apply regime weights (50-1000 scale)
    df_features = apply_regime_weights(df_features)
    
    # Step 5: Add override flags
    df_features = add_override_flags(df_features)
    
    # Step 6: Save to features/ (single source of truth)
    df_features.to_parquet(DRIVE / "TrainingData/features/master_features_2000_2025.parquet")
    
    print(f"✅ Features built: {len(df_features)} rows × {len(df_features.columns)} cols")
    print(f"   Alpha indicators: {sum('RSI_14' in c or 'MACD' in c for c in df_features.columns)}")
    print(f"   Custom features: {sum('cross_corr' in c or 'vol_' in c for c in df_features.columns)}")
    
    return df_features
```

**Update data source references:**

```python
#!/usr/bin/env python3
"""
SINGLE-PASS FEATURE ENGINEERING
Calculate all 300+ features ONCE, then reuse for all 5 horizons.
"""

import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

def build_features_single_pass():
    """
    Execute declarative joins, calculate all features.
    Returns master feature dataframe (single source of truth).
    """
    
    # VALIDATION CHECKPOINT: Must have validation certificate
    cert_path = DRIVE / "TrainingData/validation_certificate.json"
    if not cert_path.exists():
        raise ValueError(
            "❌ VALIDATION CERTIFICATE MISSING!\n"
            "Run: python3 scripts/validation/final_alpha_validation.py\n"
            "Training cannot proceed without validation certificate."
        )
    
    print("\n" + "="*80)
    print("SINGLE-PASS FEATURE ENGINEERING")
    print("="*80)
    print("✅ Validation certificate found - proceeding with feature build")
    
    # ... rest of existing code ...
```

**Data Source Integration:**

```python
# INTEGRATION APPROACH:
# - Join pipeline handles all data sources (Yahoo, FRED, Alpha, etc.)
# - build_all_features.py uses joined data from execute_joins.py
# - No direct file reads needed - join pipeline provides unified dataset

# OLD (if direct reads existed):
# commodities = pd.read_parquet("/Volumes/.../raw/yahoo_finance/prices/commodities/*.parquet")

# NEW (via join pipeline):
# df_base = executor.execute()  # Already includes Alpha data from join_spec.yaml
# No direct file reads - join pipeline handles all sources
```

---

**Task 2.15: Build ES Feature Builder (6 hours)**

Create `scripts/features/build_es_features.py` for multi-timeframe ES training data.

---

### Week 5: Final Validation + Deprecation

**Task 2.16: FINAL VALIDATION CHECKPOINT (4 hours) - CRITICAL!**

**NO DATA PROCEEDS TO TRAINING WITHOUT PASSING ALL CHECKS**

**File:** `scripts/validation/final_alpha_validation.py`

```python
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

from src.utils.data_validation import AlphaDataValidator, DataIntegrityChecker

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
    
    DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")
    
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
    for parquet_file in DRIVE.rglob("alpha/**/*.parquet"):
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
        with open(cert_path, 'w') as f:
            json.dump(certificate, f, indent=2)
        
        print(f"\n📜 Validation certificate saved: {cert_path}")
        return True

if __name__ == "__main__":
    # This MUST pass before any training
    final_validation_checkpoint()
```

**Run before EVERY training:**
```bash
# MANDATORY before training
python3 scripts/validation/final_alpha_validation.py

# Only if above passes:
python3 scripts/features/build_all_features.py
```

---

**Task 2.11: Archive Old Collectors (2 hours)**

Move old Yahoo commodity/FX collectors to archive after Alpha verified.

---

**Task 2.12: Update Documentation (4 hours)**

Update all plans, READMEs, and architecture docs.

---

## Success Criteria

### Phase 1: Training Surface Fixed
- ✅ Training tables: 2000-2025 (25 years, not 5)
- ✅ Regimes: 7+ unique (not just "allhistory")
- ✅ Weights: 50-1000 range (not all 1)
- ✅ Features folder: Populated
- ✅ Exports folder: 10 files, ~6,200 rows each

### Phase 2: Alpha Vantage Integrated
- ✅ Alpha replaces Yahoo for commodities/FX
- ✅ Alpha replaces NewsAPI for sentiment
- ✅ ES data collected (intraday multi-timeframe)
- ✅ Manifests for all files
- ✅ Dual storage working (Parquet + BQ)
- ✅ TA weekly validation passing

---

## Execution Timeline

**TODAY (Phase 1 - URGENT):** 6-8 hours
- Create staging files from raw data (2 hours) - PRE-REQUISITE
- Patch execute_joins.py (2-3 hours)
- Add regime weights to feature builder (1 hour)
- Create verification script (30 min)
- Rebuild surface (2-3 hours)

**Week 1 (Phase 2 Start):** 12-14 hours
- Create missing staging files (Task 2.0: 2 hours) - CRITICAL PRE-REQUISITE
- Audit BQ schemas (Task 2.1: 4 hours)
- Design Alpha tables (Task 2.2: 2 hours)
- Create BQ tables (Task 2.3: 2 hours)
- Create folder structure (Task 2.4: 30 min)
- Build validation framework (Task 2.4.5: 2 hours)

**Week 2:** 20-24 hours
- Build Alpha client (Task 2.5: 4 hours)
- Build manifest system (Task 2.6: 2 hours)
- Build staging pipeline (Task 2.7: 6 hours)
- Build BigQuery sync (Task 2.8: 4 hours)
- Update join_spec.yaml (Task 2.9: 1 hour)
- Build Alpha master collector (Task 2.10: 8 hours)

**Week 3-4:** 20-28 hours
- Historical backfill (Task 2.13: 8-10 hours)
- Update feature builder (Task 2.14: 6 hours)
- Build ES feature builder (Task 2.15: 6 hours)

**Week 5:** 6-8 hours
- Final validation checkpoint (Task 2.16: 4 hours)
- Archive old collectors (Task 2.11: 2 hours)
- Update documentation (Task 2.12: 4 hours)

**Total:** 5-6 weeks, ~47-57 hours

---

## ARCHITECTURAL INTEGRATION STRATEGY

### Data Flow Architecture (Complete)

```
COLLECTION LAYER (Mac M4):
├── Existing Sources (FRED, Yahoo ZL, NOAA, CFTC, USDA, EIA)
│   └── scripts/ingest/collect_*_comprehensive.py
│       └── External Drive: raw/{source}/
│
└── Alpha Vantage (NEW)
    └── scripts/ingest/collect_alpha_master.py
        └── External Drive: raw/alpha/

STAGING LAYER (Mac M4):
├── Existing Sources
│   └── scripts/staging/create_staging_files.py
│       └── External Drive: staging/{source}_{description}_{date_range}.parquet
│
└── Alpha Vantage (NEW)
    └── scripts/staging/prepare_alpha_for_joins.py
        └── External Drive: staging/alpha/daily/alpha_complete_ready_for_join.parquet

JOIN LAYER (Mac M4):
└── scripts/assemble/execute_joins.py
    └── Uses: registry/join_spec.yaml
    └── Output: Joined dataset with ALL sources (including Alpha)

FEATURE ENGINEERING LAYER (Mac M4):
└── scripts/features/build_all_features.py
    ├── Input: Joined dataset from execute_joins.py
    ├── Calculations:
    │   ├── Alpha indicators: Use pre-calculated (from join)
    │   ├── Correlations: calculate_cross_asset_features() (ZL vs FRED)
    │   ├── Volatility: calculate_volatility_features()
    │   ├── Seasonal: calculate_seasonal_features()
    │   ├── Macro: calculate_macro_regime_features()
    │   └── Weather: calculate_weather_aggregations()
    └── Output: External Drive: features/master_features_2000_2025.parquet

DUAL STORAGE SYNC (Mac M4 → BigQuery):
├── Alpha Sync: scripts/sync/sync_alpha_to_bigquery.py
│   └── External Drive staging/alpha/ → BigQuery forecasting_data_warehouse.*
│
└── Training Sync: [Existing mechanism]
    └── External Drive exports/ → BigQuery training.*

TRAINING LAYER (Mac M4):
└── PyTorch (MPS) → Local models → Predictions → BigQuery predictions.*
```

### Storage Architecture (Unified)

**External Drive (Primary Storage):**
```
TrainingData/
├── raw/                    # Immutable source zone
│   ├── {existing_sources}/  # FRED, Yahoo, NOAA, CFTC, USDA, EIA
│   └── alpha/              # NEW: Alpha Vantage data
│
├── staging/                 # Validated, conformed
│   ├── {source}_{description}_{date_range}.parquet  # Existing pattern
│   └── alpha/daily/alpha_complete_ready_for_join.parquet  # Alpha pattern
│
├── features/               # Engineered signals
│   └── master_features_2000_2025.parquet
│
└── exports/                # Final training parquet per horizon
    ├── zl_training_prod_allhistory_*.parquet
    └── es_training_prod_allhistory_*.parquet
```

**BigQuery (Mirror Storage - Same Dataset):**
```
forecasting_data_warehouse (dataset)
├── {existing_tables}       # Existing raw data tables
└── {type}_alpha_{granularity}  # NEW: Alpha tables matching existing pattern
    ├── commodity_alpha_daily
    ├── fx_alpha_daily
    ├── technical_indicators_alpha_daily
    ├── intraday_es_alpha
    ├── news_sentiment_alpha
    └── options_snapshot_alpha
```

### Processing Architecture (Mac-Centric)

**Mac M4 Processing:**
- ✅ Collection: All Python scripts
- ✅ Staging: All transformations
- ✅ Joins: execute_joins.py
- ✅ Feature Engineering: build_all_features.py
- ✅ Training: PyTorch (MPS)
- ✅ Predictions: Local → Upload to BigQuery

**BigQuery Processing:**
- ✅ Storage: Raw tables, training tables, predictions
- ✅ Scheduling: Cron (via Mac M4)
- ✅ Dashboard: Read-only queries
- ❌ NOT used for: Feature engineering, training, calculations

### Calculation Integration Strategy

**Alpha Vantage Provides (Pre-calculated - Use As-Is):**
- 50+ Technical Indicators (RSI, MACD, SMA, EMA, BBANDS, ATR, etc.)
- Store in BigQuery, use from join pipeline
- Don't recalculate - Alpha provides industry-standard values

**Our Calculations Provide (Keep Existing):**
- Cross-asset correlations (ZL vs FRED, VIX, dollar index)
- Volatility features (custom windows, annualization)
- Seasonal features (day-of-week, month effects)
- Macro regime features (Fed regimes, yield curve)
- Weather aggregations (precipitation, temperature)
- Policy/sentiment features (NLP, Trump events)

**Integration Logic:**
1. Join pipeline brings Alpha indicators into base dataset
2. Feature builder detects Alpha indicators present
3. Skip `calculate_technical_indicators()` if Alpha indicators found
4. Always run custom calculations (correlations, volatility, etc.)
5. Final dataset has: Alpha technicals + Our custom features

### Join Order (Final Sequence)

```
1. base_prices (Yahoo - ZL + 54 other symbols)
2. add_macro (FRED - 30+ economic series)
3. add_weather (NOAA - US Midwest weather)
4. add_cftc (CFTC - Positioning data, 2006+)
5. add_usda (USDA - Agricultural reports)
6. add_biofuels (EIA - Biofuel production, 2010+)
7. add_regimes (Regime calendar - 9 regimes, 1990-2025)
8. add_alpha_enhanced (Alpha Vantage - Prices + 50+ indicators) ← NEW, LAST
```

**Rationale:** Alpha joins last because:
- It's symbol-specific (multi-key join: date + symbol)
- It adds the most columns (50+ indicators)
- It's the newest data source
- All other joins are single-date joins

---

---

**CRITICAL: Complete Phase 1 TODAY before starting Phase 2. Otherwise, all Alpha data will inherit broken regimes and need reprocessing.**
