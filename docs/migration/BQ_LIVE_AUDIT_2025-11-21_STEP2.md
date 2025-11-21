# BigQuery Full Audit - November 21, 2025
**Status:** READ-ONLY AUDIT  
**Project:** cbi-v14  
**Purpose:** Pre-Day 1 Execution Assessment

---

## DATASETS (8 total)

| Dataset | Status | Tables/Views | Purpose |
|---------|--------|--------------|---------|
| `api` | ✅ Exists | (not audited) | API layer |
| `features` | ✅ Exists | 3 objects | Feature engineering |
| `market_data` | ✅ Exists | 13 objects | Market OHLCV data |
| `monitoring` | ✅ Exists | 1 table | Model performance tracking |
| `predictions` | ✅ Exists | 0 tables | Model predictions (empty) |
| `raw_intelligence` | ✅ Exists | 11 tables | Macro/weather/news data |
| `training` | ✅ Exists | 19 tables | Training datasets |
| `z_archive_20251119` | ✅ Exists | (not audited) | Archive |

---

## CRITICAL FINDINGS

### 🔴 REGIME TABLES (BOTH EMPTY)

**training.regime_calendar:**
- Schema: `date, regime, valid_from, valid_to`
- Rows: **0** ❌
- Partitioned: YES (by date)
- **Status:** EMPTY - NEEDS POPULATION

**training.regime_weights:**
- Schema: `regime, weight, description, research_rationale, created_at`
- Rows: **0** ❌
- **Status:** EMPTY - NEEDS POPULATION

**⚠️ IMPACT:** Both regime tables are empty. Day 1 Step 2 SQL will work (no conflicts), but we're starting fresh.

---

## TRAINING DATASET (19 tables)

### ZL Training Tables (5 tables)
| Table | Partitioned | Clustered | Status |
|-------|-------------|-----------|--------|
| `zl_training_prod_allhistory_1w` | YES (date) | regime | ✅ Created |
| `zl_training_prod_allhistory_1m` | NO | - | ✅ Created |
| `zl_training_prod_allhistory_3m` | NO | - | ✅ Created |
| `zl_training_prod_allhistory_6m` | NO | - | ✅ Created |
| `zl_training_prod_allhistory_12m` | NO | - | ✅ Created |

### MES Training Tables (12 tables)
| Table | Partitioned | Clustered | Status |
|-------|-------------|-----------|--------|
| `mes_training_prod_allhistory_1min` | YES (ts_event) | regime | ✅ Created |
| `mes_training_prod_allhistory_5min` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_15min` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_30min` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_1hr` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_4hr` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_1d` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_7d` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_1m` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_3m` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_6m` | NO | - | ✅ Created |
| `mes_training_prod_allhistory_12m` | NO | - | ✅ Created |

### Regime Tables (2 tables)
| Table | Rows | Status |
|-------|------|--------|
| `regime_calendar` | **0** | ❌ EMPTY |
| `regime_weights` | **0** | ❌ EMPTY |

---

## FEATURES DATASET (3 objects)

| Object | Type | Partitioned | Clustered | Status |
|--------|------|-------------|-----------|--------|
| `master_features` | TABLE | YES (date) | symbol, regime | ✅ Created |
| `master_features_all` | VIEW | - | - | ✅ Created |
| `regime_calendar` | TABLE | NO | date, regime | ✅ Created |

**⚠️ NOTE:** `features.regime_calendar` exists (separate from `training.regime_calendar`)

---

## MARKET_DATA DATASET (13 objects)

### Key Tables:
| Table | Partitioned | Clustered | Purpose |
|-------|-------------|-----------|---------|
| `databento_futures_ohlcv_1d` | YES (date) | root, symbol, is_spread | Daily OHLCV |
| `databento_futures_ohlcv_1m` | YES (ts_event) | root, is_spread, priority_tier | 1-min OHLCV |
| `databento_futures_continuous_1d` | YES (date) | root, cont_id | Continuous contracts |
| `yahoo_historical_prefixed` | NO | date, symbol | Yahoo historical data |
| `yahoo_zl_historical_2000_2010` | YES (date) | - | ZL stitching source |
| `fx_daily` | YES (date) | pair, source | FX pairs |
| `orderflow_1m` | YES (ts_minute) | root | Order flow (2.7mo expiry) |
| `roll_calendar` | YES (roll_date) | root, method | Contract roll dates |

---

## RAW_INTELLIGENCE DATASET (11 tables)

| Table | Purpose | Status |
|-------|---------|--------|
| `cftc_positioning` | COT reports | ✅ Created |
| `eia_biofuels` | EIA energy data | ✅ Created |
| `fred_economic` | Economic indicators | ✅ Created |
| `news_bucketed` | Bucketed news | ✅ Created |
| `news_intelligence` | News analysis | ✅ Created |
| `palm_oil_daily` | Palm oil prices | ✅ Created |
| `policy_events` | Policy events | ✅ Created |
| `usda_granular` | USDA reports | ✅ Created |
| `volatility_daily` | VIX/volatility | ✅ Created |
| `weather_segmented` | Weather by region | ✅ Created |
| `weather_weighted` | Weighted weather | ✅ Created |

---

## MONITORING DATASET (1 table)

| Table | Partitioned | Purpose |
|-------|-------------|---------|
| `model_performance` | YES (evaluation_date) | Model eval tracking |

---

## PREDICTIONS DATASET

**Status:** ❌ EMPTY (no tables)

---

## DAY 1 EXECUTION IMPLICATIONS

### ✅ SAFE TO PROCEED:

1. **Step 1: regime_weights.yaml** → ✅ COMPLETED (committed f1e52d2)

2. **Step 2: Regime Calendar SQL**
   - `training.regime_calendar` is EMPTY
   - No conflicts with old data
   - Safe to insert trump_anticipation_2024 + trump_second_term
   - **ACTION:** Populate both `training.regime_calendar` AND `training.regime_weights`

3. **Step 3: Create features.daily_ml_matrix**
   - Table does NOT exist yet
   - Safe to create with corrected DDL
   - **ACTION:** Run DDL to create table

4. **Step 4: Pivot Handshake**
   - Depends on `scripts/features/cloud_function_pivot_calculator.py`
   - **ACTION:** Test calculator output

---

## SCHEMA NOTES

### training.regime_calendar (actual schema)
```
date         DATE REQUIRED
regime       STRING REQUIRED  
valid_from   DATE
valid_to     DATE
```

### training.regime_weights (actual schema)
```
regime              STRING REQUIRED
weight              INTEGER REQUIRED
description         STRING
research_rationale  STRING
created_at          TIMESTAMP (default: CURRENT_TIMESTAMP)
```

**⚠️ MISMATCH WITH DAY 1 SQL:**
Day 1 SQL tries to insert into `regime_calendar` with columns: `(regime, weight, start_date, end_date, description)`

But actual schema is: `(date, regime, valid_from, valid_to)`

**🔧 CORRECTION NEEDED:** Update Day 1 Step 2 SQL to match actual schema

---

## SUMMARY

**✅ Good News:**
- All datasets exist
- Training tables created (19 tables)
- Market data infrastructure ready
- Raw intelligence tables ready
- No conflicting regime data (both empty)

**⚠️ Action Required:**
- Populate `training.regime_calendar` (0 rows)
- Populate `training.regime_weights` (0 rows)
- Create `features.daily_ml_matrix` (doesn't exist)
- Fix Day 1 Step 2 SQL to match actual schema

**🔴 Schema Mismatch:**
- Day 1 SQL assumes wrong column names for `regime_calendar`
- Must use: `date, regime, valid_from, valid_to` (NOT `start_date, end_date`)

---

**End of Audit**

