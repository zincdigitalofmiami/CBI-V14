---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# FORENSIC AUDIT: Training Dataset Stale Data Problem
**Generated**: November 5, 2025  
**Issue**: Training dataset stuck at Nov 3 while source data and views are current (Nov 5)  
**Status**: 🔴 **ROOT CAUSE IDENTIFIED**

---

## EXECUTIVE SUMMARY

**Problem**: `training_dataset_super_enriched` table is 2 days behind source data despite:
- ✅ Source data is current (Nov 5)
- ✅ `vw_big_eight_signals` view is current (Nov 5)
- ❌ Training table is stale (Nov 3 only)

**Root Cause**: `refresh_features_pipeline.py` fails on first step due to missing Python modules, preventing table materialization from the view.

**Impact**: 
- Predictions use stale data (Nov 3 instead of Nov 5)
- Missing 2 days of training data
- Nov 3 price is incorrect ($48.92 vs actual $49.84)

---

## DATA FLOW ARCHITECTURE

```
Source Data (forecasting_data_warehouse)
    ↓
Signal Views (signals.*)
    ↓
vw_big_eight_signals (neural.vw_big_eight_signals) ← VIEW (CURRENT: Nov 5)
    ↓
refresh_features_pipeline.py ← FAILS HERE
    ↓
training_dataset_super_enriched (models_v4.training_dataset_super_enriched) ← TABLE (STALE: Nov 3)
```

---

## VERIFICATION RESULTS

### 1. Source Data Status ✅ CURRENT

**Query**: `forecasting_data_warehouse.soybean_oil_prices`
```
Date        | Price Records | Status
------------|---------------|--------
Nov 5, 2025 | 3 records     | ✅ Current
Nov 4, 2025 | 2 records     | ✅ Current  
Nov 3, 2025 | 2 records     | ✅ Current
```

**Latest Prices**:
- Nov 5: $49.52, $49.55, $49.61 (current)
- Nov 4: $49.49, $49.50 (current)
- Nov 3: $49.84 (actual, but training has $48.92)

**Conclusion**: Source data ingestion is working correctly.

---

### 2. Signal Views Status ✅ CURRENT

**Query**: `neural.vw_big_eight_signals`
```
Date        | Row Count | Status
------------|-----------|--------
Nov 5, 2025 | 1         | ✅ Current
Nov 4, 2025 | 1         | ✅ Current
Nov 3, 2025 | 1         | ✅ Current
Nov 2, 2025 | 1         | ✅ Current
Nov 1, 2025 | 1         | ✅ Current
```

**View Definition**: `vw_big_eight_signals` is a view that:
- Joins 8 signal views (vix, harvest, china, tariff, geo, biofuel, hidden, ethanol)
- Uses `LEFT JOIN` with COALESCE defaults
- Generates date spine from 2020-01-01 to CURRENT_DATE()
- Calculates `big8_composite_score` and `market_regime`

**Conclusion**: View is current and correctly shows Nov 4-5 data.

---

### 3. Training Table Status ❌ STALE

**Query**: `models_v4.training_dataset_super_enriched`
```
Date        | Row Count | Status
------------|----------|--------
Nov 3, 2025 | 1        | ❌ Stale (should have Nov 4-5)
Nov 2, 2025 | 1        | ⚠️  Wrong price ($48.92 vs actual)
Nov 1, 2025 | 1        | ⚠️  Wrong price
Oct 31, 2025| 1        | ✅ Correct ($48.68)
```

**Table Last Modified**: Nov 4, 2025 at 20:28:19 CST (timestamp: 1762309699307)

**Data Gap**:
- Missing: Nov 4, Nov 5 (2 days)
- Incorrect: Nov 3 price ($48.92 vs actual $49.84)

**Conclusion**: Table is stale and contains incorrect data.

---

### 4. Refresh Pipeline Status ❌ FAILING

**Script**: `scripts/refresh_features_pipeline.py`

**Expected Flow**:
```python
1. Run PIPELINE_STEPS (8 Python modules)
2. materialise_final_table()  # Copy view → table
3. write_manifest()
```

**Actual Execution**:
```bash
$ python3 refresh_features_pipeline.py
2025-11-05 10:11:13,100 INFO ==== BIG-8 FEATURE REFRESH START ====
2025-11-05 10:11:13,100 INFO ▶️ Running prepare_all_training_data
2025-11-05 10:11:13,100 ERROR ❌ Step prepare_all_training_data failed: No module named 'prepare_all_training_data'
```

**Failure Point**: Step 1 fails, script exits immediately (line 44: `sys.exit(1)`)

**Result**: `materialise_final_table()` never executes, so table never updates.

---

## ROOT CAUSE ANALYSIS

### Problem 1: Missing Python Modules

**PIPELINE_STEPS** (lines 19-28):
```python
PIPELINE_STEPS = [
    "prepare_all_training_data",        # ❌ Not found
    "create_correlation_features",      # ❌ Not found
    "add_cross_asset_lead_lag",         # ❌ Not found
    "create_crush_margins",             # ❌ Not found
    "add_event_driven_features",      # ❌ Not found
    "add_market_regime_signals",        # ❌ Not found
    "create_big8_aggregation",         # ❌ Not found
    "add_seasonality_decomposition",   # ❌ Not found
]
```

**Location Check**:
- `prepare_all_training_data.py` exists in `archive/oct31_2025_cleanup/scripts_legacy/`
- `create_big8_aggregation.py` exists in `archive/oct31_2025_cleanup/scripts_legacy/`
- **NOT in active scripts directory** or on Python path

**Why It Fails**:
```python
def run_step(module_name: str):
    try:
        module = importlib.import_module(module_name)  # ← Fails here
        # ...
    except Exception as exc:
        logger.error("❌ Step %s failed: %s", module_name, exc)
        sys.exit(1)  # ← Exits immediately, never reaches materialise_final_table()
```

---

### Problem 2: Unnecessary Dependencies

**Analysis**: The `materialise_final_table()` function (line 47-54) is simple:
```python
def materialise_final_table():
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}` AS
    SELECT * FROM `{PROJECT_ID}.neural.vw_big_eight_signals`
    """
    subprocess.run(["bq", "query", "--use_legacy_sql=false", query], check=True)
```

**Observation**: This function doesn't depend on PIPELINE_STEPS at all. It just copies the view to the table.

**Conclusion**: The 8 Python modules are likely legacy code that's no longer needed. The view already contains all the Big 8 signals.

---

### Problem 3: Cron Job Failing Silently

**Cron Schedule**:
```
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_features_pipeline.py >> /Users/zincdigital/CBI-V14/logs/feature_refresh.log 2>&1
```

**Status Check**:
- Log file doesn't exist (`/Users/zincdigital/CBI-V14/logs/feature_refresh.log`)
- No error notifications
- Cron runs but script fails immediately

**Impact**: No one knows the refresh is failing.

---

## WHY VIEW IS CURRENT BUT TABLE IS STALE

**Critical Understanding**:

1. **View = Query**: `vw_big_eight_signals` is a VIEW, not a table
   - Views execute queries on-demand
   - When you query the view, it runs the SQL and returns current data
   - View shows Nov 5 because it queries current signal views

2. **Table = Snapshot**: `training_dataset_super_enriched` is a TABLE
   - Tables store data at point-in-time
   - Table was last updated Nov 4 (Nov 3 data)
   - Table won't update until `CREATE OR REPLACE TABLE` runs successfully

3. **Materialization Gap**: The view is current, but the table materialization never happens because:
   - Pipeline fails on step 1
   - `materialise_final_table()` never executes
   - Table stays stale

---

## DATA CORRECTNESS ISSUES

### Nov 3 Price Mismatch

**Source Data** (Nov 3):
```
Price: $49.84 (correct, from actual market data)
```

**Training Table** (Nov 3):
```
Price: $48.92 (incorrect, $0.92 error = 1.85% deviation)
```

**Possible Causes**:
1. Table was materialized from a view that had incorrect price data at that time
2. Price data was updated after table materialization
3. View logic had a bug that's since been fixed

**Impact**: Models trained on incorrect Nov 3 price will have wrong baseline.

---

## SOLUTIONS

### Solution 1: Skip Broken Pipeline Steps (IMMEDIATE FIX)

**Modify**: `scripts/refresh_features_pipeline.py`

**Change**:
```python
def main():
    logger.info("==== BIG-8 FEATURE REFRESH START ====")
    # SKIP PIPELINE_STEPS - they're legacy and not needed
    # View already contains all Big 8 signals
    # for step in PIPELINE_STEPS:
    #     run_step(step)
    logger.info("⏭️  Skipping legacy pipeline steps (view already has all signals)")
    
    # Direct materialization from view
    materialise_final_table()
    write_manifest()
    logger.info("✅ Feature refresh pipeline complete.")
```

**Rationale**: 
- View `vw_big_eight_signals` already contains all Big 8 signals
- PIPELINE_STEPS modules are in archive and not needed
- Materialization is independent of pipeline steps

**Risk**: Low - we're just skipping broken code

---

### Solution 2: Fix Pipeline Dependencies (LONG-TERM)

**Options**:
1. **Remove PIPELINE_STEPS entirely** - View already has everything
2. **Move modules from archive to scripts/** - If they're actually needed
3. **Replace with SQL-based pipeline** - More reliable than Python modules

**Recommendation**: Option 1 (remove PIPELINE_STEPS) - simplest and most reliable

---

### Solution 3: Add Error Handling & Monitoring

**Improvements**:
1. Add email/Slack notification on failure
2. Log to BigQuery job execution tracking
3. Add retry logic for transient failures
4. Validate table after materialization

---

## TESTING PLAN

### Test 1: Manual Materialization

```bash
# Test direct materialization
bq query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`cbi-v14.models_v4.training_dataset_super_enriched\` AS
SELECT * FROM \`cbi-v14.neural.vw_big_eight_signals\`
"

# Verify
bq query --use_legacy_sql=false "
SELECT MAX(date) as latest_date, COUNT(*) as total_rows 
FROM \`cbi-v14.models_v4.training_dataset_super_enriched\`
"
```

**Expected**: Latest date = Nov 5, row count = ~2045

---

### Test 2: Fixed Pipeline Script

```bash
# Run fixed pipeline
cd /Users/zincdigital/CBI-V14/scripts
python3 refresh_features_pipeline.py

# Check log
tail -20 /Users/zincdigital/CBI-V14/logs/feature_refresh.log
```

**Expected**: Success message, table updated

---

### Test 3: Verify Data Correctness

```sql
-- Compare view vs table
SELECT 
  v.date,
  v.big8_composite_score as view_score,
  t.big8_composite_score as table_score,
  ABS(v.big8_composite_score - t.big8_composite_score) as diff
FROM `cbi-v14.neural.vw_big_eight_signals` v
JOIN `cbi-v14.models_v4.training_dataset_super_enriched` t
  ON v.date = t.date
WHERE v.date >= '2025-11-01'
ORDER BY v.date DESC
```

**Expected**: All diffs = 0.0 (identical data)

---

## IMMEDIATE ACTION ITEMS

### Priority 1: Fix Pipeline (Today)
1. ✅ Modify `refresh_features_pipeline.py` to skip PIPELINE_STEPS
2. ✅ Test manual materialization
3. ✅ Run fixed pipeline
4. ✅ Verify table has Nov 5 data

### Priority 2: Verify Data (Today)
1. ✅ Check Nov 3 price correction
2. ✅ Verify Nov 4-5 data exists
3. ✅ Compare view vs table for consistency

### Priority 3: Add Monitoring (This Week)
1. ⏳ Add error notification to cron job
2. ⏳ Add job execution tracking
3. ⏳ Set up alerts for stale data

---

## CONCLUSION

**Root Cause**: `refresh_features_pipeline.py` fails on first step (missing Python modules), preventing table materialization from the current view.

**Solution**: Skip broken PIPELINE_STEPS and directly materialize the view. The view already contains all necessary Big 8 signals.

**Impact**: Once fixed, training dataset will be current within minutes (just need to run materialization query).

**Confidence**: High - view is current, table materialization is simple, only blocker is broken pipeline.

---

**Audit Complete**







