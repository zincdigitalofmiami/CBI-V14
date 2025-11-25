---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🔍 RIN/RFS NULL Investigation Report
**Date**: November 6, 2025  
**Last Reviewed**: November 14, 2025  
**Issue**: RIN/RFS columns are 100% NULL, blocking model retraining

**Note**: BQML deprecated - this investigation was historical. All training now runs locally on Mac M4 via TensorFlow Metal.

---

## Executive Summary

**Problem**: BQML training failed with error "entries in column 'rin_d4_price' are all NULLs"

**Root Cause**: RIN/RFS data was NEVER populated in production_training_data_1m

**Why Not Caught**: 
1. Old bqml_1m model likely trained WITHOUT these columns (auto-excluded by BQML)
2. Our audit focused on "new" features (Yahoo), not existing schema
3. RIN/RFS were in schema but never had data

---

## Investigation Findings

### 1. Current State (100% NULL)

```sql
-- All RIN/RFS columns in production_training_data_1m
+-----------------------+------------+----------+
|      column_name      | total_rows | non_null |
+-----------------------+------------+----------+
| rin_d4_price          |       1404 |        0 |
| rin_d5_price          |       1404 |        0 |
| rin_d6_price          |       1404 |        0 |
| rfs_mandate_biodiesel |       1404 |        0 |
| rfs_mandate_advanced  |       1404 |        0 |
| rfs_mandate_total     |       1404 |        0 |
+-----------------------+------------+----------+
```

**Result**: These columns exist in schema but have NEVER contained data

### 2. Source Tables (Data Exists But Stale)

```sql
-- Source tables DO have data, but only through Sep 10, 2025
+------------------------------+-----------+------------+------------+
|          table_name          | row_count |  min_date  |  max_date  |
+------------------------------+-----------+------------+------------+
| models_v4.rin_prices_daily   |      1347 | 2020-01-06 | 2025-09-10 |
| models_v4.rfs_mandates_daily |      1347 | 2020-01-06 | 2025-09-10 |
+------------------------------+-----------+------------+------------+
```

**Finding**: Source tables have 1,347 rows but stop at Sep 10 (57 days ago)

### 3. Why This Wasn't Caught

#### A. Old Model Training (Nov 4, 2025)
- BQML automatically excludes 100% NULL columns during training
- Old bqml_1m model trained successfully because it ignored RIN/RFS
- Model reported "274 features" but RIN/RFS weren't among them

#### B. Our Audit Blind Spot
From `COMPLEX_FEATURES_AUDIT_REPORT.md`:
```
### Available But Stale
- ⚠️ rin_prices_daily: Through Sep 10 only (stale)
- ⚠️ rfs_mandates_daily: Through Sep 10 only (stale)
```

We KNEW they were stale but didn't realize they were NEVER populated in production!

#### C. Feature Importance Analysis
From `THE_REAL_BIG_HITTERS_DATA_DRIVEN.md`:
- RIN/RFS not mentioned in top 9 correlations
- Biofuels only -0.601 correlation (#6)
- Focus was on Crush Margin (0.961), China (-0.813), Dollar (-0.658)

**Conclusion**: RIN/RFS were deemed "nice to have" not critical

### 4. The Integration Gap

**What Happened**:
1. Schema created with RIN/RFS columns (aspirational)
2. Source tables created and partially populated
3. Integration script NEVER written to join them
4. Production tables have columns but no data
5. Old model trained anyway (auto-excluded NULLs)

**The Miss**:
- Our consolidation focused on dates (Sep 11 - Nov 6)
- We didn't check if base columns had ANY data
- Assumed if column exists, it has historical data

---

## Why BQML Failed Now But Not Before

### Old Model (bqml_1m) - Nov 4, 2025
```sql
SELECT * EXCEPT(date, target_1w, target_3m, target_6m)
FROM production_training_data_1m
WHERE target_1m IS NOT NULL
```
- BQML silently dropped NULL columns
- Trained with ~274 features (not 290)
- RIN/RFS never included

### New Model Attempt (bqml_1m_v2) - Nov 6, 2025
```sql
SELECT * EXCEPT(
  target_1w, target_1m, target_3m, target_6m, 
  date, yahoo_data_source, volatility_regime,
  -- We only excluded KNOWN null columns
  social_sentiment_volatility, news_article_count, ...
)
```
- We didn't exclude RIN/RFS (didn't know they were NULL)
- BQML tried to use them
- Failed with "all NULLs" error

---

## The Deeper Pattern

### What This Reveals
1. **Schema ≠ Data**: Having columns doesn't mean having data
2. **Silent Failures**: BQML auto-exclusion hides missing data
3. **Incomplete Integration**: Many data sources connected but not flowing
4. **Audit Gaps**: We check dates, not NULL coverage

### Other Potential NULL Columns
Need to check ALL columns for NULL coverage, not just RIN/RFS:
- Argentina port logistics (mentioned as 0% in handover)
- Freight/Baltic Dry (mentioned as 0%)
- Some news features (showing 100% NULL)

---

## Immediate Fix Options

### Option 1: Exclude RIN/RFS (Quick Fix)
```sql
-- Add to EXCEPT clause
* EXCEPT(
  ...existing exclusions...,
  rin_d4_price, rin_d5_price, rin_d6_price,
  rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total
)
```
**Pros**: Train immediately  
**Cons**: Missing biofuel signals

### Option 2: Populate from Source (Better)
```sql
-- Join source data to production
UPDATE production_training_data_1m t
SET 
  rin_d4_price = r.d4_price,
  rin_d5_price = r.d5_price,
  rin_d6_price = r.d6_price
FROM models_v4.rin_prices_daily r
WHERE t.date = r.date
```
**Pros**: Adds biofuel signals (-0.601 correlation)  
**Cons**: Only through Sep 10 (need fresh data)

### Option 3: Get Fresh RIN Data (Best)
- Pull from EPA or market data provider
- Update through Nov 6
- Then populate production

**Pros**: Complete biofuel coverage  
**Cons**: Requires new data source setup

---

## Lessons Learned

### 1. Always Check NULL Coverage
```sql
-- Should have run this for ALL columns
SELECT 
  column_name,
  COUNT(*) - COUNT(column_value) as null_count,
  ROUND((COUNT(*) - COUNT(column_value)) * 100.0 / COUNT(*), 1) as null_pct
FROM production_training_data_1m, 
UNNEST([...all columns...]) as column_value
GROUP BY column_name
HAVING null_pct = 100
```

### 2. Schema Audit ≠ Data Audit
- Column existence doesn't guarantee data
- Need to verify actual values, not just structure

### 3. BQML's Silent Exclusion
- Models can train with missing features
- Need explicit feature tracking
- Can't rely on "successful training" as validation

### 4. Integration Completeness
- Many tables created but not connected
- Need data flow diagram
- Track which sources feed which columns

---

## Recommended Action

### For Immediate Training (Today)
1. **Use Option 1**: Exclude RIN/RFS columns
2. Train bqml_1m_v2 without them
3. Document as known limitation

### For Next Iteration (This Week)
1. Populate RIN/RFS from existing source (through Sep 10)
2. Find data source for Oct-Nov RIN prices
3. Run complete NULL audit on all columns
4. Fix any other 100% NULL columns

### For Long-term (This Month)
1. Implement data completeness monitoring
2. Create integration status dashboard
3. Set up alerts for NULL columns
4. Document all column data sources

---

## NULL Audit Query (Run This!)

```sql
-- Find ALL columns that are 100% NULL
CREATE TEMP FUNCTION check_nulls(col_name STRING, col_data ARRAY<FLOAT64>) AS (
  STRUCT(
    col_name as column_name,
    ARRAY_LENGTH(col_data) as total_rows,
    COUNTIF(x IS NOT NULL) as non_null_rows,
    ROUND(COUNTIF(x IS NOT NULL) * 100.0 / ARRAY_LENGTH(col_data), 1) as coverage_pct
  )
);

WITH null_check AS (
  SELECT 
    check_nulls('rin_d4_price', ARRAY_AGG(rin_d4_price)) as rin_d4,
    check_nulls('rin_d5_price', ARRAY_AGG(rin_d5_price)) as rin_d5,
    -- ... repeat for all numeric columns
  FROM `cbi-v14.models_v4.production_training_data_1m`
)
SELECT * FROM null_check;
```

---

## Conclusion

**Root Cause**: RIN/RFS columns were aspirational - schema created but integration never completed

**Why Not Caught**: 
- Old model auto-excluded them silently
- We audited dates, not NULL coverage
- Assumed schema = data

**Fix**: Exclude for now, populate later

**Lesson**: Always verify data presence, not just schema

---

**Investigation Date**: November 6, 2025  
**Investigator**: AI Assistant  
**Status**: Issue Identified, Fix Ready







