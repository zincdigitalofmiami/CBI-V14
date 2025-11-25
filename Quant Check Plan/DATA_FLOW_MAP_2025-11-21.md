# 🔍 EXACT DATA FLOW: Databento → daily_ml_matrix
**Date:** November 21, 2025 (Updated: November 24, 2025)  
**Status:** 🟢 SCRIPTS LOCATED - READY FOR EXECUTION  
**Purpose:** Map actual flow with verified scripts

---

## ✅ CURRENT STATE (Nov 24, 2025)

### **BigQuery Data Present:**
| Table | Rows | Date Range | Symbols |
|-------|------|------------|---------|
| `market_data.databento_futures_ohlcv_1d` | **6,034** | 2010-06-06 → 2025-11-16 | ZL (3,998), MES (2,036) |
| All other tables | **0** | N/A | N/A |

### **Scripts Located (CBI-V14.architecture workspace):**
All calculation scripts are in `/Users/zincdigital/Documents/GitHub/CBI-V14.architecture/scripts/`:

| Script | Location | Purpose | Status |
|--------|----------|---------|--------|
| `cloud_function_pivot_calculator.py` | `features/` | Daily/Weekly/Monthly pivot points | ✅ READY |
| `cloud_function_fibonacci_calculator.py` | `features/` | Fibonacci retracements/extensions | ✅ READY |
| `trump_action_predictor.py` | `predictions/` | Trump policy action prediction | ✅ READY |
| `zl_impact_predictor.py` | `predictions/` | ZL market impact from Trump | ✅ READY |
| `ingest_features_hybrid.py` | `ingestion/` | Hybrid feature ingestion pipeline | ✅ READY |
| `load_databento_raw.py` | `ingestion/` | Raw Databento data loader | ✅ READY |
| `build_forex_features.py` | `features/` | FX feature calculations | ✅ READY |
| `build_mes_all_features.py` | `features/` | MES all-horizon features | ✅ READY |
| `calculate_rin_proxies.py` | `features/` | RIN/biofuel proxies | ✅ READY |

---

## 📋 COMPLETE FLOW MAP (UPDATED)

### **LAYER 1: Data Acquisition**

| Step | Component | Status | Location |
|------|-----------|--------|----------|
| **1.1** | Databento data in BQ | ✅ **6,034 rows** | `market_data.databento_futures_ohlcv_1d` |
| **1.2** | ZL coverage | ✅ **3,998 rows** | 2010-06-06 → 2025-11-14 |
| **1.3** | MES coverage | ✅ **2,036 rows** | 2019-05-05 → 2025-11-16 |

**Output:** Raw Databento OHLCV in BigQuery ✅

---

### **LAYER 2: Raw Data Storage (BigQuery)**

| Table | Schema | Rows | Status |
|-------|--------|------|--------|
| `market_data.databento_futures_ohlcv_1d` | date, symbol, open, high, low, close, settle, volume, open_interest | **6,034** | ✅ POPULATED |
| `market_data.databento_futures_ohlcv_1m` | ts_event, symbol, open, high, low, close, volume | **0** | ⏸️ Empty |

---

### **LAYER 3: Feature Calculation**

| Feature Family | Calculator | Input | Output | Status |
|----------------|-----------|-------|--------|--------|
| **Market Data** | Passthrough | Databento OHLCV | open, high, low, close, volume | ✅ Direct from BQ |
| **Pivot Points** | `cloud_function_pivot_calculator.py` | Databento OHLCV | P, R1-R4, S1-S4, M1-M8, distances | ✅ Script ready |
| **Fibonacci** | `cloud_function_fibonacci_calculator.py` | Databento OHLCV | Fib levels, extensions | ✅ Script ready |
| **Trump/Policy** | `trump_action_predictor.py` | Truth Social, Policy events | 16 policy features | ✅ Script ready |
| **ZL Impact** | `zl_impact_predictor.py` | Trump predictions | Expected ZL moves | ✅ Script ready |
| **FX Features** | `build_forex_features.py` | FX data | RSI, MACD, correlations | ✅ Script ready |
| **MES Features** | `build_mes_all_features.py` | MES OHLCV | All MES horizons | ✅ Script ready |
| **RIN Proxies** | `calculate_rin_proxies.py` | Biofuel data | RIN/RFS features | ✅ Script ready |

---

### **LAYER 4: Feature Consolidation**

**Script:** `ingest_features_hybrid.py` (580 lines, tested)

**What It Does:**
1. Reads from `market_data.databento_futures_ohlcv_*` (BigQuery)
2. For each (symbol, date):
   - Gets OHLCV (direct from Databento table)
   - Calculates VWAP, realized vol
   - Calculates pivot points (calls pivot calculator)
   - Gets Trump/policy features (lookup or calculate)
   - Gets golden zone features (MES only)
3. Output: Flat Pandas DataFrame with ALL columns
4. Passes to `IngestionPipeline` for loading

**Components Built:**
- ✅ `RegimeCache`: Loads regime_calendar + weights into memory, O(1) lookup
- ✅ `DataQualityChecker`: Validates data before loading
- ✅ `IngestionPipeline`: Transforms flat DataFrame → denormalized BQ rows
- ✅ `transform_row_to_bq_format()`: Creates STRUCTs
- ✅ `validate_and_enrich()`: Adds regime
- ✅ `load_batch()`: Micro-batch to BQ

---

### **LAYER 5: Ingestion to daily_ml_matrix**

| Component | Status | Location |
|-----------|--------|----------|
| `RegimeCache` | ✅ Built | `ingest_features_hybrid.py` |
| `DataQualityChecker` | ✅ Built | `ingest_features_hybrid.py` |
| `IngestionPipeline` | ✅ Built | `ingest_features_hybrid.py` |

**Input:** Flat DataFrame with all features
**Output:** Rows in `features.daily_ml_matrix` (denormalized, with STRUCTs)

---

### **LAYER 6: Training & Dashboard**

| Component | Status |
|-----------|--------|
| Training tables (`training.zl_*`, `training.mes_*`) | ⏸️ Created, empty |
| Dashboard queries | ⏳ Future |
| Model training on Mac | ⏳ Future |

---

## 🎯 EXECUTION SEQUENCE (READY TO RUN)

### **Phase 1: Copy Scripts to Current Workspace**
```bash
# Copy calculation scripts from architecture workspace
cp -r /Users/zincdigital/Documents/GitHub/CBI-V14.architecture/scripts/features/* /Users/zincdigital/CBI-V14/scripts/features/
cp -r /Users/zincdigital/Documents/GitHub/CBI-V14.architecture/scripts/predictions/* /Users/zincdigital/CBI-V14/scripts/predictions/
cp -r /Users/zincdigital/Documents/GitHub/CBI-V14.architecture/scripts/ingestion/* /Users/zincdigital/CBI-V14/scripts/ingestion/
```

### **Phase 2: Run Pivot Calculator**
```bash
cd /Users/zincdigital/CBI-V14
python scripts/features/cloud_function_pivot_calculator.py
```

### **Phase 3: Run Feature Consolidation**
```bash
python scripts/ingestion/ingest_features_hybrid.py --test-batch 100
```

### **Phase 4: Populate Training Tables**
```sql
-- Once features.daily_ml_matrix is populated
INSERT INTO training.zl_training_prod_allhistory_1w
SELECT * FROM features.daily_ml_matrix WHERE symbol = 'ZL';
```

---

## ✅ STATUS SUMMARY

| Component | Old Status | Current Status |
|-----------|------------|----------------|
| Databento data in BQ | ❌ MISSING | ✅ **6,034 rows** |
| Pivot calculator | ⚠️ Not wired | ✅ Script located |
| Trump predictor | ⚠️ Not wired | ✅ Script located |
| Feature ingestion | ❌ MISSING | ✅ Script located |
| Training tables | ❌ Empty | ⏸️ Ready for population |

---

**Status:** 🟢 READY FOR EXECUTION
**Next Step:** Copy scripts and run feature calculations

