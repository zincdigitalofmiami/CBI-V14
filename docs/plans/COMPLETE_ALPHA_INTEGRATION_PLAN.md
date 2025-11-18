# Complete Alpha Vantage Integration Plan
**Date:** November 17, 2025  
**Status:** Ready for Execution  
**Priority:** CRITICAL - Training Surface Must Be Fixed First

---

## Executive Summary

**Two-Phase Approach:**
1. **Phase 1 (URGENT):** Fix broken training surface (4-6 hours)
2. **Phase 2:** Integrate Alpha Vantage data (4-5 weeks)

**Critical Finding:** Training tables are broken (missing 2000-2019 data, wrong regimes). Must fix BEFORE Alpha Vantage integration to avoid reprocessing.

---

## PHASE 1: FIX TRAINING SURFACE (Do First - 4-6 Hours)

### Root Cause Diagnosis

**Problem:** `scripts/assemble/execute_joins.py` ignores `join_spec.yaml` directives:
- Ignores `null_policy` → Old data gets dropped
- Ignores `fill_method: ffill` → NULLs not filled
- Ignores regime assertions → Regimes default to "allhistory"
- Weights never applied → All rows get weight=1

**Result:**
- Training tables: 2020-2025 only (missing 20 years)
- Regimes: "allhistory" only (missing 8 regimes)
- Weights: 1 (should be 50-1000)
- Features folder: EMPTY
- Exports folder: EMPTY

---

### Fix 1: Patch Join Executor (2-3 hours)

**File:** `scripts/assemble/execute_joins.py`

**Add null_policy implementation:**

```python
# After merge operation, add this:
np = join.get('null_policy', {})
if np:
    # Get columns added from right table
    right_cols = [c for c in right_df.columns if c not in join['on']]
    
    # Forward fill if requested
    if np.get('fill_method') == 'ffill':
        current_df = current_df.sort_values('date')
        current_df[right_cols] = current_df[right_cols].ffill()
    
    # Static fill values
    if 'fill' in np:
        current_df.fillna(value=np['fill'], inplace=True)
    
    # Assert no nulls if not allowed
    if np.get('allow') is False:
        any_null = current_df[right_cols].isnull().any().any()
        assert not any_null, f"{name}: Nulls remain in {right_cols} with allow:false"
```

**Add missing tests:**

```python
# In run_tests method, add:
elif 'expect_total_rows_gte' in test:
    min_rows = test['expect_total_rows_gte']
    assert len(df) >= min_rows, f"Only {len(df)} rows, need {min_rows}+"

elif 'expect_total_cols_gte' in test:
    min_cols = test['expect_total_cols_gte']
    assert len(df.columns) >= min_cols, f"Only {len(df.columns)} cols, need {min_cols}+"

elif 'expect_no_duplicate_dates' in test:
    dups = df['date'].duplicated().sum()
    assert dups == 0, f"Found {dups} duplicate dates"

elif 'expect_date_range' in test:
    expected_start, expected_end = test['expect_date_range']
    lo, hi = pd.Timestamp(expected_start), pd.Timestamp(expected_end)
    actual_start, actual_end = df['date'].min(), df['date'].max()
    assert actual_start <= lo, f"Start {actual_start} > expected {lo}"
    assert actual_end >= hi, f"End {actual_end} < expected {hi}"
```

---

### Fix 2: Add Regime Weights Step (1 hour)

**File:** `scripts/features/build_all_features.py`

**Add AFTER all joins, BEFORE export:**

```python
# Regime weights (FINAL - updated from 5000)
REGIME_WEIGHTS = {
    "historical_pre2000": 50,
    "pre_crisis_2000_2007": 120,
    "gfc_2008_2009": 300,
    "qe_2010_2016": 180,
    "trade_war_2017_2019": 500,
    "covid_crash_2020": 350,
    "reopening_2020_2021": 400,
    "inflation_2021_2022": 650,
    "tightening_2022_2023": 480,
    "trump_2023_2025": 1000
}

# Assert every date has a regime
assert df['market_regime'].notna().all(), "Missing regime assignments"

# Apply weights
df['training_weight'] = df['market_regime'].map(REGIME_WEIGHTS).astype('float64')

# Assert all weights applied
assert df['training_weight'].notna().all(), "Missing training_weight mapping"

# Verify weight range
assert df['training_weight'].min() >= 50, f"Weight too low: {df['training_weight'].min()}"
assert df['training_weight'].max() <= 1000, f"Weight too high: {df['training_weight'].max()}"

print(f"✅ Regime weights applied: {df['training_weight'].min()}-{df['training_weight'].max()}")
print(f"✅ Regimes present: {df['market_regime'].nunique()}")
```

**Create:** `registry/regime_weights.yaml`

```yaml
version: "1.0"
description: "Regime-based training weights (updated Nov 17, 2025)"
last_updated: "2025-11-17"

# Scale: 50-1000 (20x differential)
# Rationale: Strong recency bias without extreme values
regimes:
  historical_pre2000:
    weight: 50
    start_date: "1990-01-01"
    end_date: "1999-12-31"
    description: "Pre-2000 historical - pattern learning only"
    
  pre_crisis_2000_2007:
    weight: 120
    start_date: "2000-01-01"
    end_date: "2007-12-31"
    description: "Pre-crisis baseline patterns"
    
  gfc_2008_2009:
    weight: 300
    start_date: "2008-01-01"
    end_date: "2009-12-31"
    description: "Global Financial Crisis - volatility learning"
    
  qe_2010_2016:
    weight: 180
    start_date: "2010-01-01"
    end_date: "2016-12-31"
    description: "QE era - commodity supercycle"
    
  trade_war_2017_2019:
    weight: 500
    start_date: "2017-01-01"
    end_date: "2019-12-31"
    description: "US-China trade war - high policy relevance"
    
  covid_crash_2020:
    weight: 350
    start_date: "2020-01-01"
    end_date: "2020-12-31"
    description: "COVID crash - supply chain disruption"
    
  reopening_2020_2021:
    weight: 400
    start_date: "2020-01-01"
    end_date: "2021-12-31"
    description: "Post-COVID reopening"
    
  inflation_2021_2022:
    weight: 650
    start_date: "2021-01-01"
    end_date: "2022-12-31"
    description: "Inflation surge - macro regime shift"
    
  tightening_2022_2023:
    weight: 480
    start_date: "2022-01-01"
    end_date: "2023-12-31"
    description: "Fed tightening cycle"
    
  trump_2023_2025:
    weight: 1000
    start_date: "2023-01-01"
    end_date: "2025-12-31"
    description: "Trump 2.0 era - current regime (MAXIMUM)"
```

---

### Fix 3: Rebuild Surface (2-3 hours)

**Run with patched executor:**

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"

# Rebuild with fixed executor
python3 scripts/features/build_all_features.py

# This should now produce:
# - features/master_features_2000_2025.parquet (with proper regimes)
# - exports/zl_training_prod_allhistory_{1w,1m,3m,6m,12m}.parquet

# Verify
python3 scripts/qa/triage_surface.py
```

**Expected output:**
```
rows ~6200, cols ~300, 
date 2000-01-03 → 2025-11-17, 
regimes 9-10, 
weights (50, 1000)
✅ All gates passed
```

---

### Fix 4: Sync to BigQuery (Optional - 1 hour)

**If you want BQ tables updated:**

```bash
python3 scripts/predictions/upload_training_surfaces.py
# Uploads repaired surfaces to training.zl_training_* tables
```

---

## PHASE 2: ALPHA VANTAGE INTEGRATION (After Surface Fixed)

### Data Source Consolidation

#### REPLACE with Alpha Vantage:
- **Commodities:** ZS, ZM, ZC, ZW, CL, NG, CT, GC, SI → Use Alpha
- **FX:** USD/BRL, USD/CNY, USD/ARS, etc. → Use Alpha
- **News:** NewsAPI → Alpha NEWS_SENTIMENT
- **Indices:** SPY, DIA, QQQ → Use Alpha
- **Options:** SOYB, CORN, WEAT, DBA, SPY → Use Alpha

#### KEEP:
- **Yahoo:** ZL=F ONLY
- **FRED:** ALL 30+ economic series
- **Weather:** NOAA, INMET, SMN
- **Government:** CFTC, USDA, EIA

---

### ES Futures Naming (Matches ZL Pattern)

**BigQuery Tables:**
```
training.es_training_prod_allhistory_5min
training.es_training_prod_allhistory_15min
training.es_training_prod_allhistory_1hr
training.es_training_prod_allhistory_4hr
training.es_training_prod_allhistory_1day
training.es_training_prod_allhistory_3day
training.es_training_prod_allhistory_7day
training.es_training_prod_allhistory_30day
```

**Local Exports:**
```
TrainingData/exports/es_training_prod_allhistory_5min.parquet
TrainingData/exports/es_training_prod_allhistory_15min.parquet
TrainingData/exports/es_training_prod_allhistory_1hr.parquet
TrainingData/exports/es_training_prod_allhistory_1day.parquet
TrainingData/exports/es_training_prod_allhistory_7day.parquet
TrainingData/exports/es_training_prod_allhistory_30day.parquet
```

**Model Paths:**
```
Models/local/es/horizon_5min/prod/baselines/lstm/
Models/local/es/horizon_15min/prod/baselines/xgboost/
Models/local/es/horizon_1day/prod/advanced/tcn/
```

---

### Alpha Vantage Collection

**Daily (~30 API calls):**
- Commodities: CORN, WHEAT, WTI, BRENT, NATURAL_GAS, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM (~12 calls)
- FX: USD/BRL, USD/CNY, USD/ARS, USD/INR, USD/MYR, USD/IDR, USD/RUB, USD/CAD, EUR/USD (~9 calls)
- ES intraday: SPY 5min, 15min, 60min (~3 calls)
- SPY daily + options (~2 calls)
- News & sentiment (~2 calls)

**Weekly (~50 calls):**
- Technical indicators validation (~40-50 calls)
- Full options chains (~4 calls)

**Well within Plan75 (75 calls/min)**

---

### Implementation Timeline

#### Week 1: Foundation
- Day 1: Patch execute_joins.py (3 hours)
- Day 2: Add regime weights to feature builder (2 hours)
- Day 3: Rebuild surface, verify 2000-2025 (3 hours)
- Day 4: Create Alpha client wrapper (4 hours)
- Day 5: Create manifest system (3 hours)

#### Week 2: Alpha Collection
- Day 1-2: Build collect_alpha_master.py (8 hours)
- Day 3: Build TA validation script (4 hours)
- Day 4: Test dual storage (4 hours)

#### Week 3: Historical Backfill
- Day 1-2: Alpha commodities/FX backfill 2000-present (8 hours)
- Day 3: ES intraday backfill last 2 years (4 hours)
- Day 4: Verify data quality (4 hours)

#### Week 4: Integration
- Day 1-2: Update feature builder for Alpha sources (8 hours)
- Day 3: Build ES feature builder (6 hours)
- Day 4: Test complete pipeline (4 hours)

#### Week 5: Finalization
- Day 1: Verify Alpha quality vs Yahoo (4 hours)
- Day 2: Deprecate old collectors (3 hours)
- Day 3-4: Documentation (6 hours)

**Total:** ~5 weeks, ~45-55 hours

---

## Critical Success Criteria

### Phase 1 Complete When:
- ✅ Training tables: 2000-2025 (not 2020-2025)
- ✅ Regimes: 7+ unique (not just "allhistory")
- ✅ Weights: 50-1000 range (not all 1)
- ✅ Features folder: Populated
- ✅ Exports folder: 10 parquet files

### Phase 2 Complete When:
- ✅ Alpha data replaces Yahoo commodities/FX
- ✅ ZL uses: Yahoo (price) + Alpha (everything else)
- ✅ ES uses: Alpha (all data) + FRED (macro)
- ✅ Manifests generated for all files
- ✅ TA parity validated weekly

---

## Regime Weights (FINAL - Updated)

**Scale:** 50-1000 (20x differential, not 100x)

| Regime | Weight | Rationale |
|--------|--------|-----------|
| historical_pre2000 | 50 | Pattern learning only |
| pre_crisis_2000_2007 | 120 | Baseline patterns |
| gfc_2008_2009 | 300 | Crisis volatility |
| qe_2010_2016 | 180 | QE era patterns |
| trade_war_2017_2019 | 500 | HIGH - Policy relevance |
| covid_crash_2020 | 350 | Supply shock patterns |
| reopening_2020_2021 | 400 | Recovery patterns |
| inflation_2021_2022 | 650 | VERY HIGH - Current macro |
| tightening_2022_2023 | 480 | Fed policy patterns |
| trump_2023_2025 | 1000 | MAXIMUM - Current regime |

**Why NOT 5000:** More moderate recency bias, prevents extreme gradient dominance, allows broader pattern learning.

---

## Next Steps

1. **Review this plan**
2. **Confirm:** Fix surface first, then Alpha? (Or different order?)
3. **Confirm:** Regime weights 50-1000 correct?
4. **Execute:** Phase 1 patches (can start immediately)

---

**Plan File Location:** `docs/plans/COMPLETE_ALPHA_INTEGRATION_PLAN.md`

