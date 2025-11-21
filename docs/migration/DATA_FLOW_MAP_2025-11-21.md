# 🔍 EXACT DATA FLOW: Databento → daily_ml_matrix
**Date:** November 21, 2025  
**Status:** 🟡 READ-ONLY MAPPING  
**Purpose:** Map actual flow before any new builds

---

## ✅ WHAT'S ALREADY BUILT (Day 1 & 2)

### **Day 1: BigQuery Infrastructure**
- ✅ `training.regime_calendar` (1,908 rows, 2023-11-01 → 2029-01-20)
- ✅ `training.regime_weights` (2 rows: trump_anticipation_2024=400, trump_second_term=600)
- ✅ `features.daily_ml_matrix` (denormalized table, partitioned/clustered, 0 rows)
- ✅ `ops.databento_load_state` (load tracking, 0 rows)

### **Day 2: Ingestion Pipeline**
- ✅ `scripts/ingestion/ingest_features_hybrid.py` (580 lines, tested)
- ✅ `scripts/tests/test_100_row_batch.py` (280 lines, passed)
- ✅ `RegimeCache`: Loads regime_calendar + weights into memory, O(1) lookup
- ✅ `IngestionPipeline`: Transforms flat DataFrame → denormalized BQ rows

**Key Finding:** The ingestion pipeline expects a **FLAT Pandas DataFrame** with ALL features already calculated as columns.

---

## 🔴 WHAT'S MISSING (The Gap)

### **Missing Component: Feature Consolidation Layer**

The ingestion pipeline (`ingest_features_hybrid.py`) expects this input:

```python
# Expected DataFrame columns:
- symbol, data_date, timestamp
- open, high, low, close, volume, vwap, realized_vol_1h
- P, R1, R2, S1, S2, distance_to_P, distance_to_nearest_pivot, weekly_pivot_distance, price_above_P
- trump_action_prob, trump_expected_zl_move, ... (16 policy features)
- golden_zone_state, swing_high, swing_low, fib_50, fib_618, vol_decay_slope, qualified_trigger
- (optional) vol_percentile, k_vol
```

**But we don't have a script that creates this DataFrame from Databento raw data yet.**

---

## 📋 COMPLETE FLOW MAP (Current vs Needed)

### **LAYER 1: Data Acquisition**

| Step | Component | Status | Location |
|------|-----------|--------|----------|
| **1.1** | Download from Databento Portal | ❌ **MISSING** | Need: API or manual download |
| **1.2** | Store raw Databento files | ⚠️ **SCRATCH ONLY** | `/Volumes/Satechi Hub/.../databento_*` (DO NOT USE) |
| **1.3** | Load to `market_data.databento_*` | ❌ **MISSING** | Need: Idempotent loader with MERGE |

**Output:** Raw Databento OHLCV in BigQuery tables

---

### **LAYER 2: Raw Data Storage (BigQuery)**

| Table | Schema | Rows | Status |
|-------|--------|------|--------|
| `market_data.databento_futures_ohlcv_1d` | date, root, symbol, open, high, low, close, settle, volume, open_interest, is_spread | 0 | ✅ Created, empty |
| `market_data.databento_futures_ohlcv_1h` | (need to create) | 0 | ❌ **MISSING** |
| `market_data.databento_futures_ohlcv_1m` | ts_event, root, symbol, open, high, low, close, volume, ... | 0 | ✅ Created, empty |

**Output:** Databento OHLCV in BigQuery, queryable

---

### **LAYER 3: Feature Calculation**

| Feature Family | Calculator | Input | Output | Status |
|----------------|-----------|-------|--------|--------|
| **Market Data** | None (passthrough) | Databento OHLCV | open, high, low, close, volume | ✅ Direct from Databento |
| **VWAP/Realized Vol** | ❌ **MISSING** | Databento OHLCV | vwap, realized_vol_1h | ❌ Need calculator |
| **Pivot Points** | `cloud_function_pivot_calculator.py` (exists) | Databento OHLCV | P, R1, R2, S1, S2, distances | ⚠️ Exists but not wired |
| **Trump/Policy** | `trump_action_predictor.py`, `zl_impact_predictor.py` (exist) | Historical news/social | 16 policy features | ⚠️ Exists but not wired |
| **Golden Zone (MES)** | ❌ **MISSING** | Databento MES OHLCV | 7 golden zone features | ❌ Need to build |
| **Regime Lookup** | `RegimeCache` (exists in ingestion pipeline) | data_date | regime name, weight | ✅ Built in Day 2 |

**Output:** Calculated features (NOT in BQ yet, need consolidation script)

---

### **LAYER 4: Feature Consolidation (THE MISSING PIECE)**

**Status:** ❌ **COMPLETELY MISSING**

**What's Needed:** `scripts/features/build_consolidated_features.py`

**What It Must Do:**
1. Read from `market_data.databento_futures_ohlcv_*` (BigQuery)
2. For each (symbol, date):
   - Get OHLCV (direct from Databento table)
   - Calculate VWAP, realized vol
   - Calculate pivot points (call pivot calculator function)
   - Get Trump/policy features (lookup or calculate)
   - Get golden zone features (MES only)
3. Output: Flat Pandas DataFrame with ALL columns
4. Pass to `IngestionPipeline` for loading

**Output:** Flat DataFrame ready for ingestion

---

### **LAYER 5: Ingestion to daily_ml_matrix**

| Component | Status | Location |
|-----------|--------|----------|
| `RegimeCache` | ✅ Built | `ingest_features_hybrid.py` lines 70-104 |
| `DataQualityChecker` | ✅ Built | `ingest_features_hybrid.py` lines 107-149 |
| `IngestionPipeline` | ✅ Built | `ingest_features_hybrid.py` lines 152-381 |
| `transform_row_to_bq_format()` | ✅ Built | Lines 195-297 (creates STRUCTs) |
| `validate_and_enrich()` | ✅ Built | Lines 299-361 (adds regime) |
| `load_batch()` | ✅ Built | Lines 363-381 (micro-batch to BQ) |

**Input:** Flat DataFrame with all features
**Output:** Rows in `features.daily_ml_matrix` (denormalized, with STRUCTs)

---

### **LAYER 6: Training & Dashboard**

| Component | Status |
|-----------|--------|
| Training tables (`training.zl_*`, `training.mes_*`) | ✅ Created, empty |
| Dashboard queries | ⏳ Future |
| Model training | ⏳ Future |

**Input:** `features.daily_ml_matrix`
**Output:** Predictions, dashboards

---

## 🎯 THE MISSING LINKS (Priority Order)

### **Priority 1: Databento → BigQuery Raw Loader**

**Need:** `scripts/ingestion/load_databento_to_bq.py`

**What it does:**
1. Read Databento data (from Portal API or downloaded files)
2. Parse JSON/Parquet/CSV
3. Use MERGE (not INSERT) to load into `market_data.databento_*`
4. Track in `ops.databento_load_state`
5. Verify no duplicates

**Input:** Databento data (source TBD)
**Output:** Populated `market_data.databento_*` tables

**Dependencies:**
- Need to decide: API download or manual download?
- Need to create `market_data.databento_futures_ohlcv_1h` table (doesn't exist yet)

---

### **Priority 2: Feature Consolidation Script**

**Need:** `scripts/features/build_consolidated_features.py`

**What it does:**
1. Query `market_data.databento_*` for OHLCV
2. Calculate features:
   - VWAP: `SUM(close * volume) / SUM(volume)` over rolling window
   - Realized vol: Standard deviation of returns
   - Pivots: Call existing `cloud_function_pivot_calculator.py` logic
   - Trump/policy: Lookup from existing predictors or set NULL for pre-2023
   - Golden zone: Calculate Fib levels, swing detection (MES only)
3. Create flat DataFrame with ALL required columns
4. Save to staging or pass directly to ingestion pipeline

**Input:** `market_data.databento_*` (BigQuery)
**Output:** Flat DataFrame ready for `IngestionPipeline`

**Dependencies:**
- Priority 1 must be complete (need raw data in BQ)
- Need to extract pivot calculation logic from `cloud_function_pivot_calculator.py`
- Need to wire Trump predictors or accept NULLs

---

### **Priority 3: Integration & Testing**

**What it does:**
1. Run consolidation script on 10 rows (test)
2. Pass to `IngestionPipeline` (already tested)
3. Verify data in `features.daily_ml_matrix`
4. Run bulk load (all historical data)

---

## 🔍 CRITICAL QUESTIONS TO ANSWER

### **Q1: Databento Data Source**

**Question:** How do we get Databento data into `market_data.databento_*`?

**Options:**
- **A)** Download from Databento Portal manually → Load from files
- **B)** Use Databento API to download directly → Load immediately
- **C)** Use existing external drive files (ZL 1h, MES 1h only)

**Recommendation:** Option B (API download directly to BQ) for clean, repeatable flow

**Codex/Kirk decision needed:**
- Which option?
- What date ranges? (uniform across all symbols?)
- What symbols? (from COMPLETE_DATABENTO_DOWNLOAD_LIST.md?)

---

### **Q2: Feature Calculation Location**

**Question:** Where do feature calculations happen?

**Current understanding:**
- Market data (OHLCV): Direct from Databento ✅
- VWAP/realized vol: Need to calculate (SQL or Python?)
- Pivots: Existing Python function `cloud_function_pivot_calculator.py`
- Trump/policy: Existing Python predictors (need to wire or accept NULL)
- Golden zone: Need to build (Python)

**Recommendation:** All calculations in Python consolidation script, reading from BQ

**Codex/Kirk decision needed:**
- Confirm this approach?
- Trump features: backfill pre-2023 or NULL?

---

### **Q3: Schema Mapping**

**Question:** Databento → daily_ml_matrix field mapping

**Databento has:**
```
date, root, symbol, open, high, low, close, settle, volume, open_interest, is_spread
```

**daily_ml_matrix needs:**
```
symbol, data_date, timestamp, 
market_data.{open, high, low, close, volume, vwap, realized_vol_1h},
pivots.{P, R1, R2, S1, S2, distances, ...},
policy.{16 Trump features},
golden_zone.{7 MES features},
regime.{name, weight, ...}
```

**Transformation needed:**
- `date` → `data_date` (rename)
- `open, high, low, close, volume` → `market_data.{...}` (STRUCT)
- Calculate missing: `vwap`, `realized_vol_1h`, all pivots, policy, golden_zone
- Lookup regime from cache (already built in Day 2)

**Recommendation:** This happens in the consolidation script (Priority 2)

---

## ✅ NEXT STEP (AWAITING APPROVAL)

**Recommended sequence:**

1. **Freeze this mapping** (get Codex/Kirk approval)
2. **Answer Q1-Q3** (Databento source, calc location, confirm approach)
3. **Build Priority 1** (Databento → BQ loader with MERGE)
4. **Build Priority 2** (Feature consolidation script)
5. **Test end-to-end** (10 rows)
6. **Bulk load** (all historical data)

**I will NOT build anything until:**
- ✅ This flow map is approved
- ✅ Q1-Q3 are answered
- ✅ Explicit "proceed" from Kirk/Codex

---

**Status:** 🛑 AWAITING APPROVAL & DECISIONS

