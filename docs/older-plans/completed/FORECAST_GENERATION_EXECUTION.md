# Forecast Generation Execution: All at Once vs. One by One

**Date:** November 4, 2025  
**Topic:** How final forecast generation works

---

## TL;DR: All at Once (Single Query Execution)

**Answer:** Forecast generation runs **ALL 4 MODELS IN ONE EXECUTION**.

The `GENERATE_PRODUCTION_FORECASTS_V3.sql` file uses CTEs (Common Table Expressions) to run all 4 models in parallel within a single BigQuery job.

---

## How It Works

### Single SQL Execution (Recommended)

**File:** `bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql`

**Structure:**
```sql
WITH latest_data AS (...),         -- Get latest features ONCE
     big8_metadata AS (...),        -- Get Big 8 signals ONCE
     
     -- All 4 models run in parallel
     forecast_1w AS (SELECT * FROM ML.PREDICT(MODEL bqml_1w, ...)),
     forecast_1m AS (SELECT * FROM ML.PREDICT(MODEL bqml_1m, ...)),
     forecast_3m AS (SELECT * FROM ML.PREDICT(MODEL bqml_3m, ...)),
     forecast_6m AS (SELECT * FROM ML.PREDICT(MODEL bqml_6m, ...)),
     
     all_forecasts AS (UNION ALL 4 forecasts),
     regime_adjustments AS (...),
     final_forecasts AS (...)

INSERT INTO production_forecasts
SELECT * FROM final_forecasts;
```

**What Happens:**
1. BigQuery reads `latest_data` ONCE
2. BigQuery reads `big8_metadata` ONCE
3. BigQuery runs ML.PREDICT() on all 4 models **in parallel**
4. Results are combined, adjusted, and inserted in **one transaction**

**Execution Time:** ~30-60 seconds (all 4 models)

**Cost:** ~$0.01-0.02 (single BigQuery job)

**Pros:**
- ✅ Atomic: All forecasts or none (no partial state)
- ✅ Faster: Parallel execution
- ✅ Cheaper: Single BigQuery job
- ✅ Simpler: One SQL file, one execution
- ✅ Consistent: All forecasts use same `latest_data` and `big8_metadata`

**Cons:**
- ❌ If one model fails, entire job fails (but this is usually desired)

---

## Alternative: One by One (Not Recommended)

**Structure:** 4 separate SQL files
```sql
-- File 1: GENERATE_FORECAST_1W.sql
INSERT INTO production_forecasts
SELECT * FROM ML.PREDICT(MODEL bqml_1w, ...);

-- File 2: GENERATE_FORECAST_1M.sql
INSERT INTO production_forecasts
SELECT * FROM ML.PREDICT(MODEL bqml_1m, ...);

-- ... repeat for 3M, 6M
```

**Execution:** Run 4 separate queries sequentially

**Execution Time:** ~2-4 minutes (sequential)

**Cost:** ~$0.04-0.08 (4 separate BigQuery jobs)

**Pros:**
- ✅ One model failure doesn't block others
- ✅ Can debug individual models more easily

**Cons:**
- ❌ Slower: Sequential execution
- ❌ More expensive: 4 separate jobs
- ❌ More complex: 4 files to maintain
- ❌ Inconsistent: Each model might use different `latest_data` if data updates between runs
- ❌ Partial state risk: 2 forecasts succeed, 2 fail → incomplete forecast set

---

## Recommended Approach: All at Once

**Use:** `GENERATE_PRODUCTION_FORECASTS_V3.sql` (single file, all 4 models)

**Execution Methods:**

### Method 1: BigQuery Scheduled Query (Best)
- Create scheduled query in BigQuery console
- Schedule: Daily at 4:00 PM ET (after market close)
- Query: Copy/paste `GENERATE_PRODUCTION_FORECASTS_V3.sql`
- Cost: Free (scheduled queries are free, only pay for query execution)
- Reliability: Automatic retries, email notifications on failure

**Setup:**
1. Go to BigQuery Console → Scheduled Queries
2. Click "Create Scheduled Query"
3. Paste SQL from `GENERATE_PRODUCTION_FORECASTS_V3.sql`
4. Set schedule: Daily at 21:00 UTC (4 PM ET)
5. Enable email notifications
6. Save

### Method 2: Manual Execution
- Run `GENERATE_PRODUCTION_FORECASTS_V3.sql` in BigQuery console
- Use for testing or one-off forecast generation
- Click "Run" button

**Command-line:**
```bash
bq query --use_legacy_sql=false < bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql
```

### Method 3: Cloud Function (If Needed)
- Only use if you need custom logic or external triggers
- More complex, higher maintenance
- Not recommended unless scheduled query doesn't meet needs

---

## What About Model Training? (Different Process)

**Model Training** (one-time or periodic retraining) is DIFFERENT from forecast generation.

### Model Training: One by One (Recommended)

**Why:** Each model takes 5-15 minutes to train. Running sequentially prevents resource contention.

**Files:**
- `bigquery_sql/BQML_1W.sql` - Train 1W model
- `bigquery_sql/BQML_1M.sql` - Train 1M model
- `bigquery_sql/BQML_3M.sql` - Train 3M model
- `bigquery_sql/BQML_6M.sql` - Train 6M model

**Execution:**
```bash
# Train one at a time
bq query --use_legacy_sql=false < bigquery_sql/BQML_1W.sql
# Wait for completion (~5-15 min)

bq query --use_legacy_sql=false < bigquery_sql/BQML_1M.sql
# Wait for completion (~5-15 min)

# ... repeat for 3M, 6M
```

**Why Not All at Once?**
- Training is resource-intensive
- Running 4 models in parallel can cause:
  - Slot contention (slower execution)
  - Potential failures due to resource limits
  - Harder to monitor individual model progress

**Training Schedule:** Weekly or monthly (not daily like forecasts)

---

## Summary Table

| Task | Method | Frequency | Duration | Cost |
|------|--------|-----------|----------|------|
| **Forecast Generation** | All at once | Daily | 30-60s | $0.01-0.02 |
| **Model Training** | One by one | Weekly/Monthly | 20-60 min total | $0.10-0.20 |

---

## Final Execution Plan

### Daily Forecast Generation (Automated)
1. BigQuery Scheduled Query runs at 4:00 PM ET
2. Executes `GENERATE_PRODUCTION_FORECASTS_V3.sql`
3. Generates forecasts for all 4 horizons in one execution
4. Inserts into `production_forecasts` table
5. Dashboard views automatically show new forecasts

### Weekly Model Retraining (Manual or Scheduled)
1. Run `BQML_1W.sql` → Wait for completion
2. Run `BQML_1M.sql` → Wait for completion
3. Run `BQML_3M.sql` → Wait for completion
4. Run `BQML_6M.sql` → Wait for completion
5. Compare new MAPE to old MAPE
6. Deploy if performance improves

---

## Current Status

**Models:** ✅ Trained (bqml_1w, bqml_1m, bqml_3m, bqml_6m)

**Forecast Generation:** ✅ SQL ready (`GENERATE_PRODUCTION_FORECASTS_V3.sql`)

**Tier 1 Reasoning:** ✅ Views ready (`CREATE_DASHBOARD_VIEWS_STAGE6_WITH_REASONING.sql`)

**Next Step:** 
1. Create `production_forecasts` table (run `CREATE_PRODUCTION_FORECASTS_TABLE.sql`)
2. Run forecast generation once to test (run `GENERATE_PRODUCTION_FORECASTS_V3.sql`)
3. Create views with reasoning (run `CREATE_DASHBOARD_VIEWS_STAGE6_WITH_REASONING.sql`)
4. Set up daily scheduled query
5. Done

**No retraining needed.** Models are ready. Just generate forecasts and add Tier 1 reasoning.

