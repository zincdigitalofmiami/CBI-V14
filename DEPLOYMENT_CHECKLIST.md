# Deployment Checklist - 1M Forecasting System

**Date:** 2025-01-XX  
**Status:** Pre-Deployment Review Complete

---

## Pre-Deployment Verification

### 1. Code Review ✅
- [x] All scripts pass linting
- [x] All imports are correct
- [x] File paths match infrastructure
- [x] BigQuery queries use correct dataset names
- [x] API routes use `@/lib/bigquery` helper

### 2. Infrastructure Matching ✅
- [x] All paths use `cbi-v14` (not `cbi_v14`)
- [x] All datasets match: `forecasting_data_warehouse`, `models_v4`
- [x] All API routes use `executeBigQueryQuery()` helper
- [x] Python scripts use `bigquery.Client(project="cbi-v14")`

### 3. Fixes Applied ✅
- [x] Multi-output model wrapper (returns [30, 3])
- [x] 1W signal pivot SQL (MAX(CASE WHEN...))
- [x] Gate blend D+1-7 only (range(7))
- [x] Output flattening (.tolist())
- [x] API route parameterization fixed
- [x] BigQuery DELETE queries fixed (no params needed)

---

## Deployment Steps

### Step 1: Create BigQuery Tables
```bash
# Option A: Run helper script
python scripts/create_all_tables.py

# Option B: Manual creation
bq query --use_legacy_sql=false < bigquery_sql/create_predictions_1m_table.sql
bq query --use_legacy_sql=false < bigquery_sql/create_signals_1w_table.sql
bq query --use_legacy_sql=false < bigquery_sql/create_shap_drivers_table.sql
```

**Verify:**
```sql
SELECT table_name FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('predictions_1m', 'signals_1w', 'shap_drivers')
```

### Step 2: Train and Deploy Model
```bash
python scripts/train_distilled_quantile_1m.py
```

**Verify:**
- [ ] Model uploaded to GCS: `gs://cbi-v14-models/1m/distilled_quantile_1m.pkl`
- [ ] Vertex AI model created
- [ ] Endpoint deployed with traffic_split=100%
- [ ] Config file created: `config/vertex_1m_config.json`

**Health Check:**
```bash
python scripts/health_check.py
```

### Step 3: Test Feature Assembly
```bash
python scripts/1m_feature_assembler.py
```

**Verify:**
- [ ] Features file created: `features_1m_latest.json`
- [ ] 213 features total (209 + 4 1W signals)
- [ ] Schema validation passes

### Step 4: Test 1W Signal Computation
```bash
python scripts/1w_signal_computer.py
```

**Verify:**
```sql
SELECT * FROM `cbi-v14.forecasting_data_warehouse.signals_1w`
ORDER BY as_of_timestamp DESC LIMIT 10
-- Should return 5 rows (4 signals + 1 rolled forecast)
```

### Step 5: Test Predictor Job
```bash
python scripts/1m_predictor_job.py
```

**Verify:**
```sql
SELECT COUNT(*) as row_count, 
       MIN(future_day) as min_day, 
       MAX(future_day) as max_day
FROM `cbi-v14.forecasting_data_warehouse.predictions_1m`
WHERE DATE(as_of_timestamp) = CURRENT_DATE()
-- Should return: row_count=30, min_day=1, max_day=30
```

### Step 6: Run Aggregator
```bash
bq query --use_legacy_sql=false < bigquery_sql/create_agg_1m_latest.sql
```

**Verify:**
```sql
SELECT * FROM `cbi-v14.forecasting_data_warehouse.agg_1m_latest`
ORDER BY future_day
-- Should return 30 rows
```

### Step 7: Test SHAP Calculation
```bash
python scripts/calculate_shap_drivers.py
```

**Verify:**
```sql
SELECT COUNT(DISTINCT future_day) as days_count
FROM `cbi-v14.forecasting_data_warehouse.shap_drivers`
WHERE DATE(as_of_timestamp) = CURRENT_DATE()
-- Should return: days_count=30
```

### Step 8: Configure Cloud Scheduler

**Create jobs:**

1. **1m-predictor:**
   ```bash
   gcloud scheduler jobs create http 1m-predictor \
     --schedule="0 * * * *" \
     --uri="https://YOUR-CLOUD-RUN-URL/predict" \
     --http-method=POST \
     --time-zone="America/New_York"
   ```

2. **1w-signal-computer:**
   ```bash
   gcloud scheduler jobs create http 1w-signal-computer \
     --schedule="5 * * * *" \
     --uri="https://YOUR-CLOUD-RUN-URL/signals" \
     --http-method=POST \
     --time-zone="America/New_York"
   ```

3. **aggregator (daily):**
   ```bash
   gcloud scheduler jobs create http 1m-aggregator \
     --schedule="5 1 * * *" \
     --uri="https://YOUR-CLOUD-RUN-URL/aggregate" \
     --http-method=POST \
     --time-zone="America/New_York"
   ```

### Step 9: Test API Routes

**Local testing:**
```bash
# Start Next.js dev server
cd dashboard-nextjs
npm run dev

# Test routes
curl http://localhost:3000/api/forecast
curl http://localhost:3000/api/volatility
curl http://localhost:3000/api/v4/forward-curve
```

**Production testing:**
```bash
curl https://YOUR-VERCEL-URL.vercel.app/api/forecast
```

---

## Post-Deployment Verification (24h)

### Hourly Checks (First 24h)

- [ ] Predictor job runs every hour (check Cloud Scheduler logs)
- [ ] 1W signals updated every hour (5 rows/hour)
- [ ] Predictions written (30 rows/hour)
- [ ] No errors in Cloud Logging

### Daily Checks

- [ ] Aggregator ran successfully (check `agg_1m_latest` refreshed)
- [ ] SHAP drivers populated (600 rows/day minimum)
- [ ] Vertex AI costs < $100/month
- [ ] API routes respond < 2s

### Weekly Checks

- [ ] Review MAPE accuracy (target: < 2%)
- [ ] Check for schema drift (run `health_check.py`)
- [ ] Verify BigQuery storage costs
- [ ] Review Cloud Monitoring alerts

---

## Rollback Plan

If critical issues occur:

1. **Stop Scheduler Jobs:**
   ```bash
   gcloud scheduler jobs pause 1m-predictor
   gcloud scheduler jobs pause 1w-signal-computer
   gcloud scheduler jobs pause 1m-aggregator
   ```

2. **Revert to Legacy Routes:**
   - Dashboard will fall back to `predictions.daily_forecasts` if `agg_1m_latest` empty

3. **Undeploy Vertex Endpoint:**
   ```bash
   # Keep model, just undeploy endpoint
   gcloud ai endpoints undeploy-model ENDPOINT_ID --deployed-model-id MODEL_ID
   ```

---

## Success Criteria

✅ **Go-Live Ready:**
- All tables created and populated
- Model deployed and health check passes
- Predictor job runs successfully
- API routes return data
- Forward curve displays correctly
- Dashboard shows forecasts with q10/q90 bands

✅ **Production Stable (7 days):**
- Zero prediction job failures
- MAPE < 2%
- Vertex costs < $80/month
- API response times < 2s
- No schema mismatches

---

## Support

- **Operational Runbook:** `docs/OPERATIONAL_RUNBOOK.md`
- **Training Plan:** `MASTER_TRAINING_PLAN.md`
- **Health Check:** `python scripts/health_check.py`

