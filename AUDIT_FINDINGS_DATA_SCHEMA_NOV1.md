# DATA FRESHNESS & SCHEMA COMPATIBILITY AUDIT - NOVEMBER 1, 2025
**READ-ONLY AUDIT - NO CHANGES MADE**

---

## 📊 DATA FRESHNESS FINDINGS

### ✅ **FRESH DATA (≤2 days old):**
- ✅ **soybean_oil_prices**: Latest 2025-10-30 (2 days old) - 1,269 rows
- ✅ **corn_prices**: Latest 2025-10-30 (2 days old) - 1,269 rows  
- ✅ **weather_data**: Latest 2025-10-31 (1 day old) - 13,885 rows

### ⚠️ **STALE DATA (3-7 days old):**
- ⚠️ **currency_data**: Latest 2025-10-27 (5 days old) - 59,102 rows
- ⚠️ **palm_oil_prices**: Latest 2025-10-24 (8 days old) - 1,278 rows

### ❌ **VERY STALE DATA (8+ days old):**
- ❌ **crude_oil_prices**: Latest 2025-10-21 (11 days old) - 1,258 rows
- ❌ **vix_daily**: Latest 2025-10-21 (11 days old) - 2,717 rows
- ❌ **training_dataset_super_enriched**: Latest 2025-10-13 (19 days old) - 1,251 rows **← CRITICAL BLOCKER**

### ❌ **SCHEMA ISSUES:**
- ❌ **news_intelligence**: No 'date' column (uses 'timestamp' or similar)
- ❌ **social_sentiment**: No 'date' column (uses 'timestamp' or similar)

---

## 🔍 SCHEMA COMPATIBILITY FINDINGS

### ✅ **PRODUCTION SCHEMA (training_dataset_super_enriched):**
- **Total columns:** 210 (205 features + 1 date + 4 targets)
- **Feature columns:** 205
- **Feature types:**
  - FLOAT64: 160
  - INT64: 43
  - STRING: 2 ⚠️ (market_regime, volatility_regime)

### ⚠️ **STRING COLUMNS ISSUE:**
- **market_regime**: STRING with values: BULL (418), BEAR (417), NEUTRAL (416)
- **volatility_regime**: STRING with values: HIGH (646), MEDIUM (558), LOW (47)
- **Impact:** BQML BOOSTED_TREE supports STRING features, but they must be categorical
- **Status:** ✅ ACCEPTABLE (these are categorical, not text blobs)

### ✅ **SCHEMA COMPATIBILITY:**
- **Production features:** All numeric except 2 categorical STRINGs ✅
- **No NULLs in recent data:** ✅ (all key columns populated)
- **No constant values:** ✅ (all features have variance)

---

## 🗂️ SOURCE TABLE SCHEMA ISSUES

### ⚠️ **DATE/TIMESTAMP INCONSISTENCY:**
| Table | Date Column | Type | Issue |
|-------|-------------|------|-------|
| soybean_oil_prices | `time` | DATETIME | ⚠️ Must CAST to DATE for joins |
| corn_prices | `time` | DATETIME | ⚠️ Must CAST to DATE for joins |
| crude_oil_prices | `time` | DATE | ✅ Compatible |
| palm_oil_prices | `time` | DATETIME | ⚠️ Must CAST to DATE for joins |
| vix_daily | `date` | DATE | ✅ Compatible |
| currency_data | `date` | DATE | ✅ Compatible |
| weather_data | `date` | DATE | ✅ Compatible |
| training_dataset_super_enriched | `date` | DATE | ✅ (reference) |

**Issue:** Some tables use `time` (DATETIME), others use `date` (DATE). Training dataset expects `date` (DATE).

### ❌ **MISSING COLUMNS:**
- **currency_data**: Missing `pair` and `close_rate` columns (expected by training dataset)
- **Status:** Need to verify what columns currency_data actually has vs what training dataset expects

---

## 🔧 WHY CURRENT SCHEMA WORKS

### **Production Training Dataset:**
1. **Built from:** Multiple source tables joined on `date` (DATE type)
2. **Source tables:** Use `DATE(time)` casting for DATETIME columns
3. **Feature engineering:** All features computed from source tables
4. **String handling:** 2 categorical STRING columns (regimes) - acceptable for BQML
5. **NULL handling:** COALESCE used to fill missing values (typically 0.0 for numeric)

### **Why Existing Models Work:**
1. **Models trained:** October 28, 2025
2. **Data used:** training_dataset_super_enriched up to 2025-10-13
3. **Schema:** Models expect exactly 205 features (matches current schema)
4. **Feature types:** Models accept FLOAT64, INT64, STRING (categorical)
5. **Prediction test:** ✅ Models successfully predict with current schema

---

## ❌ WHAT FAILED BEFORE (ERROR PATTERNS)

### **1. Label Leakage:**
- **Problem:** Models accept rows WITH target columns (target_1w, target_1m, etc.)
- **Why it failed:** AutoML/Vertex AI included targets as features during training
- **Current status:** Models work with clean features (EXCEPT clause), but may have been trained with leakage

### **2. Schema Mismatches:**
- **Problem:** Date column type mismatches (DATETIME vs DATE)
- **Fix:** Use `DATE(time)` casting in joins
- **Status:** ✅ Handled in training dataset build

### **3. Missing Columns:**
- **Problem:** currency_data structure changed (missing `pair`, `close_rate`)
- **Status:** ⚠️ Need to verify actual currency_data schema

### **4. NULL Values:**
- **Problem:** BQML models reject NULLs in features
- **Fix:** COALESCE missing values to 0.0 or appropriate defaults
- **Status:** ✅ Current training dataset handles this

---

## 🚨 CRITICAL FINDINGS

### **1. TRAINING DATASET IS STALE (19 DAYS OLD)**
- **Latest data:** 2025-10-13
- **Current date:** 2025-11-01
- **Impact:** Models trained on old data, missing 19 days of market movements
- **Action Required:** Refresh training_dataset_super_enriched with latest data BEFORE retraining

### **2. SOME SOURCE DATA IS STALE**
- **crude_oil_prices:** 11 days old (last update 2025-10-21)
- **vix_daily:** 11 days old (last update 2025-10-21)
- **palm_oil_prices:** 8 days old (last update 2025-10-24)
- **Impact:** Can't rebuild training dataset with fresh data if sources are stale

### **3. DATE/TIMESTAMP INCONSISTENCY**
- **Issue:** Some tables use `time` (DATETIME), training dataset uses `date` (DATE)
- **Status:** ✅ Currently handled with DATE() casting, but needs verification in rebuild scripts

### **4. CURRENCY_DATA SCHEMA UNKNOWN**
- **Issue:** currency_data missing expected columns (`pair`, `close_rate`)
- **Action Required:** Verify actual currency_data schema and fix joins

---

## ✅ WHAT WORKS

1. **Production schema:** 205 features, all compatible with BQML ✅
2. **Existing models:** Work with current schema ✅
3. **Data types:** FLOAT64/INT64/STRING (categorical) - all supported ✅
4. **No NULLs:** Recent rows have all key features populated ✅
5. **No constants:** All features have variance ✅
6. **Source data:** Most critical tables (soybean, corn, weather) are fresh ✅

---

## 📋 RECOMMENDATIONS

### **IMMEDIATE ACTIONS:**

1. **Update stale source data:**
   - Update crude_oil_prices (11 days stale)
   - Update vix_daily (11 days stale)
   - Update palm_oil_prices (8 days stale)
   - Update currency_data (5 days stale)

2. **Refresh training_dataset_super_enriched:**
   - After source data is fresh
   - Extend from 2025-10-13 to 2025-10-30 (or latest)
   - Verify all 205 features computed correctly

3. **Verify currency_data schema:**
   - Check actual columns in currency_data table
   - Fix training dataset build if columns changed

4. **Retrain models:**
   - Use fresh training dataset (after refresh)
   - Explicit EXCEPT clause (no label leakage)
   - MAX accuracy settings (100 iterations, depth 8)

---

## 🔍 DETAILED SCHEMA VALIDATION

### **Production Schema (205 Features):**
- ✅ All numeric types (FLOAT64, INT64) except 2 categorical STRINGs
- ✅ No nested STRUCTs or ARRAYs
- ✅ No text blobs or free-form strings
- ✅ Compatible with BQML BOOSTED_TREE_REGRESSOR

### **String Columns (2):**
- **market_regime:** Categorical (BULL/BEAR/NEUTRAL) - ✅ ACCEPTABLE
- **volatility_regime:** Categorical (HIGH/MEDIUM/LOW) - ✅ ACCEPTABLE
- **BQML Support:** BOOSTED_TREE handles categorical STRINGs via one-hot encoding ✅

### **Source Table Compatibility:**
- ✅ Most tables use DATE or can CAST DATETIME to DATE
- ⚠️ Need to verify currency_data structure
- ⚠️ Need to check news_intelligence and social_sentiment timestamp columns

---

**AUDIT COMPLETE - READ-ONLY**  
**NEXT ACTION:** Update stale source data, then refresh training_dataset_super_enriched

