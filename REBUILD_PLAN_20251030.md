# REBUILD PLAN - training_dataset_super_enriched to 209 Columns
**Date:** October 30, 2025  
**Status:** ⚠️ AUDIT COMPLETE - READY TO EXECUTE WITH CAUTIONS

---

## AUDIT FINDINGS

### Current State:
- **Backup table**: `training_dataset_backup_20251028` has **207 columns** (not 209)
- **Latest data**: 2025-10-13 (17 days old)
- **Total rows**: 1,251

### Feature Breakdown (207 columns):
- **Target columns**: 4 (target_1w, target_1m, target_3m, target_6m)
- **Big-8 features**: 8 (feature_*)
- **Correlations**: 36 (corr_zl_* across 7d, 30d, 90d, 180d, 365d)
- **FX columns**: **ONLY 5** (usd_brl_rate, usd_brl_7d_change, usd_cny_rate, usd_cny_7d_change, is_major_usda_day)
- **Other features**: ~154 columns (price, volume, seasonality, fundamentals, etc.)

### ⚠️ CRITICAL GAPS IDENTIFIED:

#### 1. Missing Currency Pairs
**Available in currency_data table:**
- ✅ USD/ARS (6,169 dates, latest: 2025-10-15)
- ✅ USD/BRL (6,262 dates, latest: 2025-10-15) 
- ✅ USD/CNY (5,141 dates, latest: 2025-10-15)
- ✅ USD/MYR (6,260 dates, latest: 2025-10-27)

**Currently in model:**
- ✅ USD/BRL (present)
- ✅ USD/CNY (present)
- ❌ USD/ARS (MISSING)
- ❌ USD/MYR (MISSING)

**Action Required:** Add USD/ARS and USD/MYR features to rebuild

#### 2. Stale Currency Data
- Latest currency data: **2025-10-15** (15 days old)
- Need to update currency_data table to latest dates

#### 3. Missing Columns (207 vs 209)
- Backup has 207 columns, models expect 209
- Need to identify the 2 missing columns

---

## REBUILD APPROACH

### Step 1: Capture Schema Contract
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4._feature_contract_207` AS
SELECT column_name, data_type
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_backup_20251028'
  AND column_name NOT IN ('_PARTITIONTIME','_PARTITIONDATE');
```

### Step 2: Update Currency Data First
- Pull latest currency data for all 4 pairs (USD/ARS, USD/BRL, USD/CNY, USD/MYR)
- Compute FX features: rates, 7d changes, rolling averages
- **Add missing USD/ARS and USD/MYR features**

### Step 3: Build Feature Ingredient Views
- `vw_price_core` - Soybean oil prices
- `vw_big8` - Big-8 features (already have these)
- `vw_fx` - **EXPANDED** to include all 4 currency pairs
- `vw_correlations` - From volatility_derived_features
- `vw_fundamentals` - From fundamentals_derived_features
- `vw_seasonality` - Seasonal features
- `vw_other` - All other feature families

### Step 4: Reconstruct Wide Table
- Join all ingredient views on date
- Cast to exact types from contract
- Include all 207 columns (plus 2 missing = 209)

### Step 5: Add Target Columns
- Compute targets using LEAD() from price
- Merge into labeled table

### Step 6: Recreate Filtered Views
- `training_dataset_1w_filtered` - EXCEPT(target_1m, target_3m, target_6m)
- `training_dataset_1m_filtered` - EXCEPT(target_1w, target_3m, target_6m)
- `training_dataset_3m_filtered` - EXCEPT(target_1w, target_1m, target_6m)
- `training_dataset_6m_filtered` - EXCEPT(target_1w, target_1m, target_3m)

### Step 7: Create Predict Frame
- Latest row, EXCEPT all targets

---

## EXECUTION ORDER

1. ✅ **AUDIT** - Complete (this document)
2. ⏳ **UPDATE CURRENCY DATA** - Pull latest for all 4 pairs
3. ⏳ **CAPTURE CONTRACT** - Save 207-column schema
4. ⏳ **BUILD INGREDIENT VIEWS** - All feature families
5. ⏳ **RECONSTRUCT TABLE** - Join + cast to contract
6. ⏳ **ADD TARGETS** - Compute + merge
7. ⏳ **RECREATE VIEWS** - Filtered training views
8. ⏳ **CREATE PREDICT_FRAME** - Latest row, no targets
9. ⏳ **GENERATE PREDICTIONS** - All 4 horizons

---

## RISKS & MITIGATIONS

### Risk 1: Missing 2 Columns
- **Mitigation**: Compare backup schema to model training schema
- **Action**: Identify missing columns before rebuild

### Risk 2: Stale Currency Data
- **Mitigation**: Update currency_data table first
- **Action**: Pull latest currency data before rebuild

### Risk 3: Type Mismatches
- **Mitigation**: Explicit CAST to contract types
- **Action**: Match exact types from backup

### Risk 4: Missing Feature Sources
- **Mitigation**: Check all source tables exist
- **Action**: Verify each ingredient view can be built

---

## QUESTIONS BEFORE EXECUTION

1. **Currency Data**: Should I update currency_data table first, or rebuild with existing data?
2. **Missing Columns**: Do we know what the 2 missing columns are (207 vs 209)?
3. **Target Computation**: Are targets computed as LEAD(price, N days) or from a different source?
4. **Execution Order**: Proceed with rebuild now, or wait for currency data update?

---

**READY TO EXECUTE** once currency data is updated and missing columns identified.

