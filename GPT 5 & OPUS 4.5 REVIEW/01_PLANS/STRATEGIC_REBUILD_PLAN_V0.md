# 🎯 STRATEGIC REBUILD PLAN v0
**Date:** November 24, 2025  
**Status:** 🔵 STRATEGIC REVIEW  
**Purpose:** Validate the minimal spine approach is correct before execution

---

## 📊 STRATEGIC ANALYSIS

### The Core Question
> "Is stripping down to minimal spine the BEST strategy, or are we creating future technical debt?"

### Answer: **YES, MINIMAL SPINE IS CORRECT**

**Reasoning:**

1. **We've been in "BQ hell" for 4+ months** - complexity killed us
2. **Every table except Databento is 0 rows** - we have nothing to lose
3. **The denormalized architecture is already approved** (QUAD-CHECK Section 13)
4. **v0 establishes the pattern** - v1+ extends it without changing structure
5. **A working baseline is worth 100x more than a perfect plan**

---

## 🔍 STRATEGIC GAPS IDENTIFIED

### Gap 1: Regime Location Inconsistency

**Problem:** Documentation conflicts on WHERE regime data lives:
- QUAD-CHECK says: `training.regime_calendar` (canonical)
- Feasibility Audit says: `training.regime_weights` (simpler)
- Dataform Structure says: `reference.regime_calendar` + `reference.regime_weights`

**Actual BQ State:**
- `training.regime_calendar` EXISTS (schema: `date, regime, valid_from, valid_to`) - 0 rows
- `training.regime_weights` EXISTS (schema: `regime, weight, description, research_rationale, created_at`) - 0 rows
- `features.regime_calendar` EXISTS (schema: `date, regime, training_weight`) - 0 rows

**Strategic Decision:**

For v0, use **`training.regime_weights`** as the ONLY regime source:
- Simple key-value: regime_name → weight
- Python does the date→regime lookup (not BQ)
- Stamps regime STRUCT at ingestion time
- NO daily calendar table needed for v0

**Rationale:**
- Avoids partition limit issues (6,960 days)
- Matches the "stamp at ingestion" pattern
- Can always add date-level calendar in v1 if needed
- Simpler = faster = working baseline sooner

---

### Gap 2: Schema vs Reality Mismatch

**Problem:** `features.daily_ml_matrix` exists but has different STRUCT fields than some docs suggest.

**Actual Schema (verified):**
```
market_data STRUCT<open, high, low, close, volume, vwap, realized_vol_1h>
pivots STRUCT<P, R1, R2, S1, S2, distance_to_P, distance_to_nearest_pivot, weekly_pivot_distance, price_above_P>
policy STRUCT<trump_action_prob, trump_expected_zl_move, trump_score, trump_score_signed, trump_confidence, trump_sentiment_7d, trump_tariff_intensity, trump_procurement_alert, trump_mentions, trumpxi_china_mentions, trumpxi_sentiment_volatility, trumpxi_policy_impact, trumpxi_volatility_30d_ma, trump_soybean_sentiment_7d, policy_trump_topic_multiplier, policy_trump_recency_decay>
golden_zone STRUCT<state, swing_high, swing_low, fib_50, fib_618, vol_decay_slope, qualified_trigger>
regime STRUCT<name, weight, vol_percentile, k_vol>
```

**Strategic Decision:**

For v0, **USE THE EXISTING TABLE** but only populate:
- `market_data` STRUCT (partial - OHLCV + basic TA)
- `regime` STRUCT (name + weight only)
- Leave `pivots`, `policy`, `golden_zone` as NULLs

**Rationale:**
- Don't recreate the table - it's already correct
- Just populate what we need for v0
- Schema is already denormalized (good!)
- Extend in v1 without schema changes

---

### Gap 3: Missing TA Fields in market_data STRUCT

**Problem:** The existing `market_data` STRUCT has:
```
open, high, low, close, volume, vwap, realized_vol_1h
```

But we need for v0:
```
open, high, low, close, volume
return_1d, return_5d, return_21d
ma_5, ma_21, ma_63
volatility_21d
rsi_14
```

**Strategic Decision:**

**Option A (Recommended):** Calculate TA in Python, store in a **FLAT** structure alongside the STRUCT
- Add columns: `return_1d`, `return_5d`, `return_21d`, `ma_5`, `ma_21`, `ma_63`, `volatility_21d`, `rsi_14`
- Keep `market_data` STRUCT for raw OHLCV
- Avoids ALTER TABLE on STRUCT (complex)

**Option B:** Alter `market_data` STRUCT to add fields
- More complex DDL
- Risk of breaking existing schema

**Rationale for Option A:**
- BQ allows mixed STRUCT + flat columns
- Easier to add/remove features
- Training view just SELECTs what it needs
- No STRUCT surgery required

---

### Gap 4: VIX Data Strategy

**Problem:** We have historical VIX (6,283 rows, 2000-2025) but it's from Yahoo cache.

**Data Available:**
- `cache/yahoo_finance_complete/volatility_complete.csv` - 6,283 rows
- Includes: OHLC, RSI, MACD, MAs, Bollinger Bands

**Strategic Decision:**

For v0, **DO NOT USE VIX** - pure ZL baseline first.

For v1.5:
- Load VIX to `raw_intelligence.volatility_daily`
- Join to daily_ml_matrix by date
- This is the ONE exception to "no Yahoo" - VIX is VIX, source doesn't matter for index data

**Rationale:**
- v0 should prove the pipeline works with minimal data
- VIX adds value but isn't required for baseline
- Adding VIX in v1.5 lets us measure its impact

---

## ✅ STRATEGIC VALIDATION

### Is This The Best Strategy?

| Alternative | Why NOT to do it |
|-------------|------------------|
| Build everything at once | 4 months of failure proves this doesn't work |
| Start with MES | MES has only 2,036 rows vs ZL's 3,998 |
| Include all features | Can't debug if everything fails |
| Use SQL JOINs | Violates approved architecture |
| Recreate all tables | Existing schemas are mostly correct |

### What Could Go Wrong?

| Risk | Mitigation |
|------|------------|
| v0 too minimal to learn anything | 10-15 features is enough for baseline |
| Regime stamping breaks | Test on 100 rows first |
| Schema needs changes in v1 | ADD COLUMN is cheap; STRUCT changes are not |
| VIX absence hurts model | VIX is v1.5; baseline should work without it |

---

## 🏗️ FINAL v0 ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
├─────────────────────────────────────────────────────────────────────┤
│ market_data.databento_futures_ohlcv_1d                              │
│   └── ZL: 3,998 rows (2010-06-06 → 2025-11-14)                      │
│                                                                      │
│ training.regime_weights (to be populated)                           │
│   └── 7 regimes with weights                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     PYTHON INGESTION                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Read Databento OHLCV from BQ                                     │
│ 2. Calculate in Pandas:                                             │
│    - return_1d, return_5d, return_21d                               │
│    - ma_5, ma_21, ma_63                                             │
│    - volatility_21d                                                 │
│    - rsi_14                                                         │
│ 3. Lookup regime by date (Python dict from regime_weights)          │
│ 4. Build row with:                                                  │
│    - market_data STRUCT (OHLCV only)                                │
│    - regime STRUCT (name, weight)                                   │
│    - FLAT TA columns (return_*, ma_*, vol, rsi)                     │
│    - pivots/policy/golden_zone = NULL                               │
│ 5. MERGE into features.daily_ml_matrix                              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  features.daily_ml_matrix                            │
├─────────────────────────────────────────────────────────────────────┤
│ - data_date (DATE) [PARTITION KEY]                                  │
│ - symbol (STRING) [CLUSTER KEY]                                     │
│ - market_data STRUCT<open, high, low, close, volume, ...>           │
│ - regime STRUCT<name, weight, ...>                                  │
│ - return_1d, return_5d, return_21d (FLOAT64)                        │
│ - ma_5, ma_21, ma_63 (FLOAT64)                                      │
│ - volatility_21d (FLOAT64)                                          │
│ - rsi_14 (FLOAT64)                                                  │
│ - pivots STRUCT (NULL for v0)                                       │
│ - policy STRUCT (NULL for v0)                                       │
│ - golden_zone STRUCT (NULL for v0)                                  │
│ - ingestion_ts (TIMESTAMP)                                          │
│                                                                      │
│ Expected: ~3,800 rows after QA                                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              training.vw_zl_1m_flat (VIEW)                          │
├─────────────────────────────────────────────────────────────────────┤
│ SELECT                                                              │
│   data_date,                                                        │
│   market_data.close,                                                │
│   return_1d, return_5d, return_21d,                                 │
│   ma_5, ma_21, ma_63,                                               │
│   volatility_21d,                                                   │
│   rsi_14,                                                           │
│   regime.name AS regime_name,                                       │
│   regime.weight AS sample_weight,                                   │
│   -- Target: 21 trading days forward                                │
│   (LEAD(market_data.close, 21) OVER w - market_data.close)          │
│     / market_data.close AS target_1m,                               │
│   CASE WHEN data_date < '2023-01-01' THEN 'train' ELSE 'test' END   │
│ FROM features.daily_ml_matrix                                       │
│ WHERE symbol = 'ZL'                                                 │
│ WINDOW w AS (ORDER BY data_date)                                    │
│                                                                      │
│ NO JOINS. EVER.                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      MAC TRAINING                                    │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Export: bq extract → CSV                                         │
│ 2. Load: pd.read_csv()                                              │
│ 3. Train: LightGBM with TimeSeriesSplit                             │
│ 4. Validate: Feature importances, CV stability                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 v0 EXECUTION CHECKLIST

### Phase 0: Foundation (30 min)
- [ ] Populate `training.regime_weights` with 7 regimes
- [ ] Verify regime coverage (2010-2029, no gaps)
- [ ] Delete broken `features.master_features_all` VIEW
- [ ] (Optional) Delete empty `z_archive_20251119` dataset

### Phase 1: Schema Prep (30 min)
- [ ] ALTER `features.daily_ml_matrix` to add flat TA columns
- [ ] Verify partitioning/clustering still works
- [ ] Test 1-row INSERT with all fields

### Phase 2: Python Ingestion (2 hours)
- [ ] Create `ingest_zl_baseline.py` script
- [ ] Read Databento OHLCV from BQ
- [ ] Calculate TA in Pandas
- [ ] Build regime lookup dict
- [ ] Test on 100-row slice (2015 data)
- [ ] Run on full ZL history

### Phase 3: Assertions (30 min)
- [ ] COUNT(*) ≥ 3,800 rows
- [ ] 0 NULL regime names
- [ ] 0 NULL prices
- [ ] Price > 0, RSI 0-100, vol 0-0.5

### Phase 4: Training View (30 min)
- [ ] Create `training.vw_zl_1m_flat` VIEW
- [ ] Verify target_1m calculated correctly
- [ ] Verify split assignment correct
- [ ] COUNT(*) with target ≥ 3,600

### Phase 5: Export & Train (2 hours)
- [ ] Export to CSV
- [ ] Load in Python
- [ ] Train LightGBM baseline
- [ ] Verify CV stability
- [ ] Check feature importances

---

## 🎯 SUCCESS CRITERIA

### v0 is DONE when:

| Metric | Target | Why |
|--------|--------|-----|
| ZL rows in matrix | ≥ 3,800 | Full history minus QA drops |
| NULL regime names | 0 | Every row has regime |
| NULL prices | 0 | No broken data |
| Training rows | ≥ 3,600 | Minus last 21 days for target |
| LightGBM trains | ✅ | No errors |
| CV folds stable | ✅ | No fold blowups |
| Feature importances | Sensible | MAs/vol/returns ranked reasonably |

### v0 is NOT about:
- MAE < X%
- Beating any benchmark
- Perfect directional accuracy
- SHAP analysis
- Trump feature impact

---

## 🚀 PHASE ROADMAP

| Phase | What | When |
|-------|------|------|
| **v0** | ZL + basic TA + regime → baseline | NOW |
| v1 | Add pivots (from calculator) | After v0 works |
| v1.5 | Add VIX/volatility | After v1 works |
| v2 | Add FRED macro (DXY, yields) | After v1.5 works |
| v2.5 | Add weather | After v2 works |
| v3 | Add policy/Trump features | After v2.5 works |
| v4 | Add MES | After v3 works |

Each phase:
1. Add ONE feature family
2. Retrain
3. Measure impact
4. If positive, keep; if negative, investigate

---

## ✅ FINAL STRATEGIC CONFIRMATION

**This is the correct strategy because:**

1. **Minimal viable pipeline** - proves the architecture works
2. **No wasted effort** - only build what we need
3. **Clear success criteria** - data integrity, not model performance
4. **Extensible** - v1+ adds features without changing structure
5. **Aligned with approved architecture** - QUAD-CHECK Section 13
6. **Avoids past failures** - no complex SQL, no JOINs, no 4-month hell

**Ready to execute.**

