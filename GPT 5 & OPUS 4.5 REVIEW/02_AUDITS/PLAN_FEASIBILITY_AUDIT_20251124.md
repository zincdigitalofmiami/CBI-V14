# 🔴 CRITICAL PLAN FEASIBILITY AUDIT
**Date:** November 24, 2025  
**Status:** 🔴 MAJOR ISSUES FOUND - PLAN NEEDS REVISION  
**Auditor:** Reverse-engineered from actual BigQuery state

---

## 📊 ACTUAL BIGQUERY STATE vs PLAN ASSUMPTIONS

### ✅ What EXISTS and WORKS:

| Component | Status | Details |
|-----------|--------|---------|
| `market_data.databento_futures_ohlcv_1d` | ✅ **6,034 rows** | ZL (3,998) + MES (2,036) - 2010-2025 |
| Dataset structure | ✅ Created | 10 datasets properly structured |
| Table schemas | ✅ Defined | STRUCTs for daily_ml_matrix exist |
| Partitioning | ✅ Configured | `data_date` partition on key tables |
| Clustering | ✅ Configured | `symbol, regime_name` on features |

### 🔴 CRITICAL ISSUES FOUND:

---

## 🔴 ISSUE #1: DUPLICATE REGIME CALENDARS (SCHEMA MISMATCH)

**Problem:** TWO regime_calendar tables exist with DIFFERENT schemas!

| Table | Schema | Partitioned | Status |
|-------|--------|-------------|--------|
| `training.regime_calendar` | `date, regime, valid_from, valid_to` | YES (date) | ❌ 0 rows |
| `features.regime_calendar` | `date, regime, training_weight` | NO | ❌ 0 rows |

**Plan Error:** The execution plan targets `features.regime_calendar` with columns `(date, regime, weight, description)` but:
- `features.regime_calendar` has `training_weight` not `weight`
- `features.regime_calendar` has NO `description` column
- `training.regime_calendar` expects `valid_from, valid_to` not `weight, description`

**Impact:** INSERT statements will FAIL with column mismatch errors.

**Fix Required:** 
1. Decide which is canonical (recommend `training.regime_calendar`)
2. Update plan SQL to match actual schema
3. Consider: should regime_calendar be denormalized into daily_ml_matrix?

---

## 🔴 ISSUE #2: LEGACY VIEW USES 10 LEFT JOINs (VIOLATES NO-JOIN RULE)

**Problem:** `features.master_features_all` is a VIEW with 10 LEFT JOINs!

```sql
-- ACTUAL VIEW DEFINITION (EXPENSIVE!)
SELECT y.*, f.* EXCEPT(date), w.* EXCEPT(date), ...
FROM `market_data.yahoo_historical_prefixed` y  -- ❌ YAHOO DATA!
LEFT JOIN `raw_intelligence.fred_economic` f USING(date)
LEFT JOIN `raw_intelligence.weather_segmented` w USING(date)
LEFT JOIN `raw_intelligence.cftc_positioning` c USING(date)
LEFT JOIN `raw_intelligence.usda_granular` u USING(date)
LEFT JOIN `raw_intelligence.eia_biofuels` e USING(date)
LEFT JOIN `raw_intelligence.volatility_daily` v USING(date)
LEFT JOIN `raw_intelligence.palm_oil_daily` p USING(date)
LEFT JOIN `raw_intelligence.policy_events` pol USING(date)
LEFT JOIN `market_data.es_futures_daily` es USING(date)
LEFT JOIN `features.regime_calendar` r USING(date)
```

**Violations:**
1. ❌ Uses Yahoo data (we said NO YAHOO)
2. ❌ 10 LEFT JOINs (we said NO JOINS at query time)
3. ❌ References `yahoo_historical_prefixed` which DOESN'T EXIST
4. ❌ All joined tables are EMPTY (0 rows each)

**Impact:** This view is BROKEN and unusable.

**Fix Required:**
1. DELETE this view - it's useless
2. Use `features.daily_ml_matrix` (denormalized STRUCT approach) instead
3. Populate daily_ml_matrix via Python ingestion, not SQL joins

---

## 🔴 ISSUE #3: TRAINING TABLE SCHEMA MISMATCH

**Problem:** Training tables have MINIMAL schemas - only 5 columns!

**Actual `training.zl_training_prod_allhistory_1m` schema:**
```
date (DATE)
regime (STRING)
training_weight (INTEGER)
target_1w (FLOAT)  -- ❌ WRONG! Should be target_1m for _1m table!
as_of (TIMESTAMP)
```

**Plan assumes:** Full feature columns (ma_5, ma_21, rsi_14, volatility_21d, etc.)

**Issues:**
1. ❌ Only 5 columns - NO FEATURES stored
2. ❌ `target_1w` in the `_1m` table (copy-paste error in DDL)
3. ❌ No price data, no technical indicators
4. ❌ Would require JOINs to get features at training time

**Impact:** Cannot train models - no features in training tables!

**Fix Required:**
1. Either: Add feature columns to training tables (denormalized)
2. Or: Use `features.daily_ml_matrix` directly for training (better approach)
3. Fix target column names to match horizon

---

## 🔴 ISSUE #4: features.master_features HAS YAHOO COLUMNS

**Problem:** `features.master_features` schema includes Yahoo columns:

```
yahoo_zl_open, yahoo_zl_high, yahoo_zl_low, yahoo_zl_close
yahoo_zl_volume, yahoo_zl_rsi_14, yahoo_zl_macd
yahoo_zl_sma_50, yahoo_zl_sma_200
yahoo_zl_bollinger_upper, yahoo_zl_bollinger_lower
```

**We explicitly said:** NO YAHOO DATA - Databento only!

**Impact:** This table design is incompatible with our data strategy.

**Fix Required:**
1. Use `features.daily_ml_matrix` which has proper STRUCT-based design
2. Ignore `features.master_features` - it's legacy
3. Calculate TA indicators from Databento data only

---

## 🔴 ISSUE #5: PARTITION LIMIT ERROR (Already Hit)

**Problem:** Phase 0 INSERT failed with:
```
Too many partitions produced by query, allowed 4000, query produces at least 6960 partitions
```

**Root Cause:** 
- `training.regime_calendar` is partitioned by `date`
- INSERT tried to create 6,960 daily partitions (2010-2029)
- BigQuery limit is 4,000 partitions per operation

**Fix Required:**
1. Either: Insert in batches (by year)
2. Or: Use non-partitioned table for regime_calendar (it's small)
3. Or: Store regime boundaries only, not every day

---

## 🟡 ISSUE #6: features.daily_ml_matrix MISSING KEY COLUMNS

**Problem:** The STRUCT-based `daily_ml_matrix` is missing technical indicators!

**Current `market_data` STRUCT:**
```
open, high, low, close, volume, vwap, realized_vol_1h
```

**Missing from plan Phase 3 SQL:**
- ❌ `ma_5, ma_21, ma_63` (moving averages)
- ❌ `rsi_14` (RSI)
- ❌ `volatility_21d` (realized vol)
- ❌ `momentum_21d` (momentum)
- ❌ `return_1d, return_5d, return_21d` (returns)

**Impact:** Plan SQL tries to INSERT these into STRUCT but they don't exist in schema.

**Fix Required:**
1. Either: Alter table to add columns to market_data STRUCT
2. Or: Calculate features in Python and insert complete rows
3. Recommend: Python ingestion approach (more flexible)

---

## 🟡 ISSUE #7: z_archive_20251119 IS DEAD WEIGHT

**Finding:** Archive dataset contains 50+ tables but ALL ARE EMPTY (0 rows).

**Tables checked:**
- `archive__legacy_20251114__models_v4__production_training_data_1m` → 0 rows
- `bkp__soybean_oil_prices_SAFETY_20251021_180706` → 0 rows
- `bkp__economic_indicators_SAFETY_20251021_180706` → 0 rows
- All others → 0 rows

**Impact:** 
- Wasted storage metadata
- Confusing for audits
- No recoverable data

**Recommendation:** DELETE entire `z_archive_20251119` dataset - it's useless.

---

## ✅ WHAT THE PLAN GETS RIGHT

1. ✅ Using `features.daily_ml_matrix` with STRUCTs (correct architecture)
2. ✅ Databento as primary data source (6,034 rows ready)
3. ✅ Partitioning by date, clustering by symbol
4. ✅ Regime-based training weights concept
5. ✅ LightGBM baseline approach
6. ✅ Time series CV (not random split)

---

## 🎯 REVISED EXECUTION PLAN

### Phase 0: Fix Foundations (1 hour)

**0.1: Populate regime_weights (not calendar)**
```sql
-- Use training.regime_weights (non-partitioned, simple)
INSERT INTO `cbi-v14.training.regime_weights` (regime, weight, description)
VALUES
    ('normal_pre_2018', 100, 'Pre-trade war normal market conditions'),
    ('trade_war_2018_2019', 300, 'US-China trade war escalation'),
    ('covid_crash_2020', 200, 'COVID-19 market crash'),
    ('covid_recovery_2020', 200, 'Post-COVID recovery'),
    ('inflation_2021_2022', 300, 'High inflation regime'),
    ('trump_anticipation_2024', 400, 'Trump 2.0 anticipation'),
    ('trump_second_term', 600, 'Trump second presidential term');
```

**0.2: Create regime lookup function (Python-side)**
```python
def get_regime(date):
    if date < '2018-03-01': return 'normal_pre_2018', 100
    elif date < '2020-01-01': return 'trade_war_2018_2019', 300
    # ... etc
```

### Phase 1: Python Ingestion Pipeline (2 hours)

**DO NOT USE SQL JOINs - use Python to:**
1. Read Databento data from BQ
2. Calculate TA indicators in Pandas
3. Lookup regime in Python
4. Build complete row with all STRUCTs
5. Insert to `features.daily_ml_matrix`

### Phase 2: Pull External Data (2 hours)

Use existing scripts to populate:
- `raw_intelligence.fred_economic` (FRED API)
- `raw_intelligence.weather_segmented` (NOAA/GSOD)

### Phase 3: Enrich daily_ml_matrix (1 hour)

Update existing rows with macro data (Python UPDATE, not JOIN)

### Phase 4: Export & Train (2 hours)

Export `features.daily_ml_matrix` directly to CSV for Mac training.

---

## 📋 IMMEDIATE ACTIONS REQUIRED

| Priority | Action | Effort |
|----------|--------|--------|
| 🔴 P0 | Fix regime_calendar INSERT (use regime_weights instead) | 15 min |
| 🔴 P0 | Verify daily_ml_matrix schema matches ingestion script | 30 min |
| 🟡 P1 | Delete broken `features.master_features_all` VIEW | 5 min |
| 🟡 P1 | Delete empty `z_archive_20251119` dataset | 5 min |
| 🟡 P1 | Update plan to use Python ingestion, not SQL JOINs | 1 hour |
| 🟢 P2 | Fix training table schemas (add features or use daily_ml_matrix) | 1 hour |

---

## 🏗️ RECOMMENDED ARCHITECTURE (SIMPLIFIED)

```
┌─────────────────────────────────────────────────────────────┐
│ DATA SOURCES (External)                                      │
├─────────────────────────────────────────────────────────────┤
│ Databento API → market_data.databento_futures_ohlcv_1d      │
│ FRED API → raw_intelligence.fred_economic                   │
│ NOAA/GSOD → raw_intelligence.weather_segmented              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PYTHON INGESTION (Mac or Cloud Function)                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Read Databento OHLCV from BQ                             │
│ 2. Calculate TA (RSI, MA, Vol) in Pandas                    │
│ 3. Calculate Pivots (using pivot_calculator.py)             │
│ 4. Lookup regime + weight (Python dict)                     │
│ 5. Read FRED/Weather from BQ (if available)                 │
│ 6. Build complete STRUCT row                                │
│ 7. INSERT to features.daily_ml_matrix                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DENORMALIZED FEATURE STORE                                  │
├─────────────────────────────────────────────────────────────┤
│ features.daily_ml_matrix                                    │
│ - symbol, data_date (keys)                                  │
│ - market_data STRUCT (OHLCV + TA)                           │
│ - pivots STRUCT (P, R1, R2, S1, S2, distances)              │
│ - policy STRUCT (Trump features)                            │
│ - regime STRUCT (name, weight, vol_percentile)              │
│ - NO JOINS AT QUERY TIME                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ TRAINING (Mac M4 Pro)                                       │
├─────────────────────────────────────────────────────────────┤
│ Export: bq extract → CSV/Parquet                            │
│ Load: pd.read_csv() or pd.read_parquet()                    │
│ Train: LightGBM / TFT / XGBoost                             │
│ NO BQ QUERIES DURING TRAINING                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ SIGN-OFF REQUIRED

Before proceeding, confirm:

- [ ] Use `training.regime_weights` (not `features.regime_calendar`) for regime definitions
- [ ] Use Python ingestion to `features.daily_ml_matrix` (not SQL JOINs)
- [ ] Delete broken `features.master_features_all` VIEW
- [ ] Delete empty `z_archive_20251119` dataset
- [ ] Train directly from `features.daily_ml_matrix` export (not from training.* tables)

---

**Status:** 🔴 PLAN NEEDS REVISION BEFORE EXECUTION
**Next Step:** Review this audit and approve revised approach





