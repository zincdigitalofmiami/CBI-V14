# Prerequisites Checklist - Before Forecast Generation

**Date:** November 4, 2025  
**Status:** Pre-execution verification  
**Purpose:** Ensure all requirements met before running clean forecast script

---

## ✅ VERIFIED REQUIREMENTS

### 1. Models
- ✅ `bqml_1w` - Tested, returns prediction
- ⚠️ Need to verify: `bqml_1m`, `bqml_3m`, `bqml_6m`

### 2. Training Data
- ✅ Latest row exists: 2025-11-03
- ✅ Row count: 1,454 rows
- ⚠️ Need to verify: All models can predict from latest row

### 3. SQL Script
- ✅ `GENERATE_CLEAN_FORECASTS.sql` created
- ✅ Syntax verified
- ✅ Idempotent (safe to re-run)

### 4. Table Creation
- ✅ CREATE TABLE IF NOT EXISTS in script
- ✅ Table structure defined

---

## ⚠️ POTENTIAL ISSUES TO CHECK

### 1. Dataset Existence
**Check:** Does `predictions_uc1` dataset exist?

**If missing:**
```sql
CREATE SCHEMA IF NOT EXISTS `cbi-v14.predictions_uc1`
OPTIONS(
  location="us-central1"
);
```

**Status:** ⚠️ Need to verify

### 2. All 4 Models Accessible
**Check:** Can all 4 models run ML.PREDICT()?

**Test each:**
- `bqml_1w` ✅ Verified
- `bqml_1m` ⚠️ Need to test
- `bqml_3m` ⚠️ Need to test
- `bqml_6m` ⚠️ Need to test

**If model missing:** Training needed

### 3. Latest Row Features
**Check:** Does latest row have all required features for all models?

**Potential issues:**
- NULL values in critical features
- Missing features that models expect
- Date mismatch (latest row might not have all features)

**Status:** ⚠️ Need to verify feature completeness

### 4. Permissions
**Check:** Do we have permissions to:
- Create table in `predictions_uc1`
- Run ML.PREDICT() on all models
- Insert into `production_forecasts`

**Status:** ⚠️ Need to verify (usually fine if we can query)

### 5. EXCEPT Clause Compatibility
**Check:** Does `* EXCEPT(target_1w, target_1m, target_3m, target_6m, date)` work correctly?

**Potential issue:** Some models might expect different column sets

**Status:** ⚠️ Need to verify (script uses this pattern)

---

## 🔍 VERIFICATION QUERIES

### Test All 4 Models
```sql
-- Test 1W (already verified)
SELECT predicted_target_1w 
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w`, 
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date) 
   FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   LIMIT 1));

-- Test 1M
SELECT predicted_target_1m 
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m`, 
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date) 
   FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   LIMIT 1));

-- Test 3M
SELECT predicted_target_3m 
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m`, 
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date) 
   FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   LIMIT 1));

-- Test 6M
SELECT predicted_target_6m 
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m`, 
  (SELECT * EXCEPT(target_1w, target_1m, target_3m, target_6m, date) 
   FROM `cbi-v14.models_v4.training_dataset_super_enriched`
   WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
   LIMIT 1));
```

### Check Dataset Exists
```sql
SELECT schema_name 
FROM `cbi-v14.INFORMATION_SCHEMA.SCHEMATA`
WHERE schema_name = 'predictions_uc1';
```

### Check Latest Row Completeness
```sql
-- Get latest row with feature count
SELECT 
  date,
  COUNT(*) as total_columns,
  COUNTIF(value IS NULL) as null_count
FROM (
  SELECT date, * 
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
  LIMIT 1
) 
UNPIVOT (value FOR column_name IN (*))
GROUP BY date;
```

---

## 🚨 CRITICAL MISSING ITEMS

### If Dataset Missing
**Action:** Create dataset before running script
```sql
CREATE SCHEMA IF NOT EXISTS `cbi-v14.predictions_uc1`
OPTIONS(location="us-central1");
```

### If Models Missing
**Action:** Train missing models first
- Check which models exist
- Train missing ones using existing SQL files (BQML_1W.sql, etc.)

### If Latest Row Has Issues
**Action:** Use previous row or fix data
- Check if second-to-last row has better data
- Or handle NULLs in script

---

## ✅ RECOMMENDATION

**Before executing:**
1. ✅ Run verification queries above
2. ✅ Confirm all 4 models work
3. ✅ Confirm dataset exists (or create it)
4. ✅ Confirm latest row has sufficient data

**Then execute:**
- Run `GENERATE_CLEAN_FORECASTS.sql`
- Verify output
- Proceed with enhancements

**Status:** ⚠️ **Run verification queries first, then proceed**

