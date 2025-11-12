# TRAINING DATASET AUDIT REPORT
**Date:** November 5, 2025  
**Type:** Quick & Dirty Full Audit  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

**CRITICAL FINDING:** The training dataset structure has been significantly altered. The base table `training_dataset_super_enriched` now contains only 11 feature columns with NO target columns, while training views (`train_1w`, `train_1m`, `train_3m`, `train_6m`) contain the full dataset with 206 columns including targets.

**Training Data Sources:**
- **Base Table:** `cbi-v14.models_v4.training_dataset_super_enriched` (11 columns, NO targets)
- **Training Views:** `train_1w`, `train_1m`, `train_3m`, `train_6m` (206 columns, WITH targets)
- **BQML Models:** `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (status unknown - cannot query)
- **Vertex AI Models:** 3 models (1W, 3M, 6M) via AutoML endpoints

---

## PART 1: TRAINING DATASET STRUCTURE

### 1.1 Base Table: `training_dataset_super_enriched`

| Metric | Value | Status |
|--------|-------|--------|
| **Total Rows** | 2,136 | ✅ |
| **Date Range** | 2020-01-01 to 2025-11-05 | ✅ Current |
| **Unique Dates** | 2,136 | ✅ No duplicates |
| **Total Columns** | **11** | ⚠️ **CRITICAL: Only features, NO targets** |

**Column Structure:**
1. `date` (DATE)
2. `feature_vix_stress` (FLOAT64)
3. `feature_harvest_pace` (FLOAT64)
4. `feature_china_relations` (FLOAT64)
5. `feature_tariff_threat` (FLOAT64)
6. `feature_geopolitical_volatility` (FLOAT64)
7. `feature_biofuel_cascade` (FLOAT64)
8. `feature_hidden_correlation` (FLOAT64)
9. `feature_biofuel_ethanol` (FLOAT64)
10. `big8_composite_score` (FLOAT64)
11. `market_regime` (STRING)

**⚠️ CRITICAL ISSUE:** This table has NO target columns (`target_1w`, `target_1m`, `target_3m`, `target_6m`). The BQML training SQL files reference this table expecting targets that don't exist.

### 1.2 Training Views

**View Structure:**
- `train_1w`: 206 columns (includes `target_1w` + 205 features)
- `train_1m`: 206 columns (includes `target_1m` + 205 features)
- `train_3m`: 206 columns (includes `target_3m` + 205 features)
- `train_6m`: 206 columns (includes `target_6m` + 205 features)

**Features Included in Views:**
- Price features (zl_price_current, lags, returns, moving averages)
- Volatility features (30d, correlations)
- Cross-asset correlations (crude, palm, vix, dxy, corn, wheat)
- Seasonal features (seasonal_index, monthly_zscore)
- Crush margin features
- China sentiment features
- Brazil harvest features
- Trump/policy features
- Event features (WASDE, FOMC, holidays)
- Lag features (palm, crude, vix, dxy, corn, wheat)
- Lead correlation features (temporal leakage potential)

**Row Counts:** (Not verified - views may filter differently)

---

## PART 2: DATA DISTRIBUTION

### 2.1 Year Distribution

| Year | Rows | Percentage | Notes |
|------|------|------------|-------|
| **2025** | 309 | 14.5% | Current year (Nov 5, 2025) |
| **2024** | 366 | 17.1% | Low-volatility period |
| **2023** | 365 | 17.1% | Transition period |
| **Historical (2020-2022)** | 1,096 | 51.3% | COVID/Energy crisis volatility |

**Key Finding:** 51.3% of training data is from 2020-2022 (high-volatility periods), but only 14.5% from 2025 (current high-volatility period).

### 2.2 Target Availability

**Status:** Cannot determine from base table (no target columns exist).  
**Expected (from training views):**
- Targets are available only where future prices are known
- Recent dates (Nov 1-5, 2025) likely have NULL targets for longer horizons
- Training filters use `WHERE target_X IS NOT NULL`

**Expected Training Windows:**
- **1W Model:** Trained on dates where target_1w IS NOT NULL (likely through Oct 28, 2025)
- **1M Model:** Trained on dates where target_1m IS NOT NULL (likely through Oct 6, 2025)
- **3M Model:** Trained on dates where target_3m IS NOT NULL (likely through Aug 7, 2025)
- **6M Model:** Trained on dates where target_6m IS NOT NULL (likely through May 8, 2025)

---

## PART 3: BQML MODELS STATUS

### 3.1 Model Existence Check

**Models Attempted:**
- `bqml_1w`
- `bqml_1m`
- `bqml_3m`
- `bqml_6m`

**Status:** ❌ **Cannot query model metadata** - BigQuery INFORMATION_SCHEMA.MODELS not accessible in this location.

**Training SQL Files:**
- `bigquery-sql/BQML_1W.sql` - References `training_dataset_super_enriched` with `target_1w`
- `bigquery-sql/BQML_3M.sql` - References `training_dataset_super_enriched` with `target_3m`
- `bigquery-sql/BQML_6M.sql` - References `training_dataset_super_enriched` with `target_6m`

**⚠️ CRITICAL MISMATCH:** Training SQL files reference `training_dataset_super_enriched` expecting target columns that don't exist in the base table.

### 3.2 Training Configuration (from SQL files)

**Model Parameters (All Models):**
```sql
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_X'],
  max_iterations=100,
  learn_rate=0.1,
  early_stop=False
)
```

**Feature Counts (from SQL comments):**
- **1W Model:** 276 numeric features (excludes 8 NULL columns + targets + date + volatility_regime)
- **3M Model:** 268 numeric features (excludes 18 columns - 8 standard + 7 news + 1 trump)
- **6M Model:** 258 numeric features (excludes 28 columns - 8 standard + 7 news + 11 trump)

**Excluded Columns (common):**
- All target columns (target_1w, target_1m, target_3m, target_6m)
- `date`
- `volatility_regime` (STRING type)
- NULL columns: `social_sentiment_volatility`, `bullish_ratio`, `bearish_ratio`, `social_sentiment_7d`, `social_volume_7d`, `trump_policy_7d`, `trump_events_7d`, `news_intelligence_7d`, `news_volume_7d`
- News columns (100% NULL for longer horizons)

---

## PART 4: VERTEX AI MODELS

### 4.1 Model Registry

| Model | Model ID | Type | Status |
|-------|----------|------|--------|
| **1W** | 575258986094264320 | Vertex AI AutoML | ✅ |
| **3M** | 3157158578716934144 | Vertex AI AutoML | ✅ |
| **6M** | 3788577320223113216 | Vertex AI AutoML | ✅ |

**Training Data Source:** Unknown - requires Vertex AI console access to verify.

**Note:** These are Vertex AI AutoML endpoints, not BQML models. They use the Vertex AI prediction API, not `ML.PREDICT()` on BigQuery tables.

---

## PART 5: DATASET ARCHIVE STATUS

### 5.1 Archived Tables Found

**Multiple archived versions of training dataset:**
- `_ARCHIVED_archive_training_dataset_20251027_pre_update`
- `_ARCHIVED_archive_training_dataset_DUPLICATES_20251027`
- `_ARCHIVED_archive_training_dataset_super_enriched_20251027_final`
- `_ARCHIVED_training_dataset_backup_20251028`
- `_ARCHIVED_training_dataset_baseline_clean`
- `_ARCHIVED_training_dataset_baseline_complete`
- `_ARCHIVED_training_dataset_clean`
- `_ARCHIVED_training_dataset_snapshot_20251028_pre_update`

**Backup Tables:**
- `training_dataset_pre_coverage_fix_backup`
- `training_dataset_pre_forwardfill_backup`
- `training_dataset_pre_integration_backup`
- `training_dataset_super_enriched_backup`

**Conclusion:** The training dataset has been modified/truncated multiple times. The current version is feature-only with no targets.

---

## PART 6: CRITICAL ISSUES IDENTIFIED

### Issue #1: Base Table Missing Targets
**Severity:** 🔴 **CRITICAL**

**Problem:** `training_dataset_super_enriched` table has only 11 columns and NO target columns.

**Impact:**
- BQML training SQL files cannot execute (target columns don't exist)
- Models cannot be retrained using current SQL files
- Training views exist but may not be used by BQML training

**Root Cause:** Table was likely truncated/modified after initial training, removing target columns.

### Issue #2: Training SQL Mismatch
**Severity:** 🔴 **CRITICAL**

**Problem:** BQML training SQL files reference `training_dataset_super_enriched` expecting targets that don't exist.

**Impact:**
- Training scripts will fail
- Cannot verify if models were trained successfully
- Cannot retrain models with current configuration

### Issue #3: Training Views Not Used
**Severity:** 🟡 **WARNING**

**Problem:** Training views (`train_1w`, `train_1m`, `train_3m`, `train_6m`) contain full dataset with targets but are not referenced in BQML training SQL files.

**Impact:**
- Views may be orphaned or unused
- Potential training data source mismatch

### Issue #4: Cannot Verify Model Status
**Severity:** 🟡 **WARNING**

**Problem:** Cannot query BQML model metadata via INFORMATION_SCHEMA.MODELS.

**Impact:**
- Cannot verify if models exist
- Cannot check training timestamps
- Cannot verify training data used

### Issue #5: Vertex AI Training Data Unknown
**Severity:** 🟡 **WARNING**

**Problem:** Vertex AI model training data source cannot be verified without console access.

**Impact:**
- Cannot audit what data was used for Vertex AI training
- Cannot verify data freshness

---

## PART 7: RECOMMENDATIONS

### Immediate Actions (Priority 1)

1. **Restore Target Columns to Base Table**
   - Restore `target_1w`, `target_1m`, `target_3m`, `target_6m` to `training_dataset_super_enriched`
   - Use archived backup tables if targets were removed
   - Verify target columns match training view structure

2. **Verify BQML Model Status**
   - Check BigQuery console directly for model existence
   - Verify models can make predictions
   - Check model creation timestamps

3. **Align Training SQL with Actual Data Source**
   - Update BQML training SQL to use correct table/view
   - Either restore base table targets OR update SQL to use training views
   - Ensure consistency between training and prediction data sources

### Short-Term Actions (Priority 2)

4. **Audit Training Views**
   - Verify view definitions match expected structure
   - Check if views are actively used
   - Document view creation and update process

5. **Verify Vertex AI Training Data**
   - Check Vertex AI console for training data source
   - Verify training data freshness
   - Document training data pipeline for Vertex AI

6. **Clean Up Archive Tables**
   - Consolidate or remove redundant archived tables
   - Document which archive contains valid targets if base table needs restoration

### Long-Term Actions (Priority 3)

7. **Implement Data Lineage Tracking**
   - Track changes to training dataset
   - Version control for training data
   - Alert on schema changes

8. **Automated Training Data Validation**
   - Pre-training checks for required columns
   - Target availability validation
   - Feature completeness checks

---

## PART 8: KEY METRICS SUMMARY

### Training Dataset Metrics

| Metric | Current | Expected | Status |
|--------|---------|----------|--------|
| Total Rows | 2,136 | 2,000+ | ✅ |
| Date Range | 2020-2025 | 2020-2025 | ✅ |
| Latest Date | Nov 5, 2025 | Current | ✅ |
| **Base Table Columns** | **11** | **200+** | ❌ **CRITICAL** |
| **Target Columns in Base** | **0** | **4** | ❌ **CRITICAL** |
| Training View Columns | 206 | 200+ | ✅ |
| Training View Targets | 4 (one per view) | 4 | ✅ |

### Model Status Metrics

| Model Type | Models | Status | Verifiable |
|------------|--------|--------|------------|
| BQML Models | 4 (1w, 1m, 3m, 6m) | Unknown | ❌ Cannot query |
| Vertex AI Models | 3 (1w, 3m, 6m) | Active | ⚠️ Console only |

---

## CONCLUSION

**Summary:**
- Base training table has been truncated to 11 feature columns with NO targets
- Training views exist with full dataset (206 columns including targets)
- BQML training SQL files reference base table expecting targets that don't exist
- Cannot verify BQML model status or training data used
- Vertex AI models exist but training data source unknown

**Status:** 🔴 **CRITICAL ISSUES IDENTIFIED** - Training dataset structure mismatch, cannot verify model training status

**Next Steps:**
1. Restore target columns to base table OR update SQL to use training views
2. Verify BQML model existence via BigQuery console
3. Document training data lineage and restoration process

---

**Report Generated:** 2025-11-05 12:06:26  
**Audit Method:** Direct BigQuery queries + SQL file analysis







