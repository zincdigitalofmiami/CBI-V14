# Operational Runbook - 1M Forecasting System

**Last Updated:** 2025-01-XX  
**System:** CBI-V14 Vertex AI Forecasting  
**Architecture:** 1M Core Model + 1W Signal Gate Blend

---

## System Overview

- **Core Model:** Distilled LightGBM-Quantile (1M horizon, 30-day ahead)
- **Signal Layer:** 1W volatility/compliance signals (offline computation)
- **Deployment:** Vertex AI Endpoint (`us-central1`, `n1-standard-2`)
- **Storage:** BigQuery (`forecasting_data_warehouse` dataset)
- **API:** Next.js API routes with ISR caching (Vercel)

---

## Daily Operations

### 1. Predictor Job (Hourly)

**Script:** `scripts/1m_predictor_job.py`  
**Schedule:** Cloud Scheduler - every 60 minutes  
**Steps:**
1. Assemble 213 features (209 + 4 1W signals)
2. Validate schema (hash check)
3. Call Vertex AI endpoint
4. Apply 1W gate blend (D+1-7 only)
5. Write to `predictions_1m` table

**Verification:**
```bash
python scripts/1m_predictor_job.py
# Check: BigQuery → predictions_1m → latest row count = 30
```

### 2. 1W Signal Computation (Hourly)

**Script:** `scripts/1w_signal_computer.py`  
**Schedule:** Cloud Scheduler - every 60 minutes (offset 5min after predictor)  
**Steps:**
1. Fetch price history (30 days)
2. Compute: volatility_score_1w, delta_1w_vs_spot, momentum_1w_7d, short_bias_score_1w
3. Compute rolled 1W forecast (7-day path)
4. Write to `signals_1w` table

**Verification:**
```bash
python scripts/1w_signal_computer.py
# Check: BigQuery → signals_1w → latest 5 rows (4 signals + 1 rolled forecast)
```

### 3. Aggregator Job (Daily)

**Script:** `bigquery_sql/create_agg_1m_latest.sql`  
**Schedule:** Cloud Scheduler - 5 min after hour (1:05 AM daily)  
**Steps:**
1. Aggregate `predictions_1m` → `agg_1m_latest`
2. Compute AVG(mean), AVG(q10), AVG(q90) per future_day
3. Materialized view refresh

**Verification:**
```sql
SELECT * FROM `cbi-v14.forecasting_data_warehouse.agg_1m_latest`
ORDER BY future_day
-- Should return 30 rows
```

### 4. SHAP Calculation (After Predictor)

**Script:** `scripts/calculate_shap_drivers.py`  
**Schedule:** Cloud Scheduler - 10 min after predictor hour  
**Steps:**
1. Load latest features
2. Compute SHAP values (or feature importance fallback)
3. Map to business labels
4. Write to `shap_drivers` table (top 20 per future_day)

**Verification:**
```bash
python scripts/calculate_shap_drivers.py
# Check: BigQuery → shap_drivers → latest 600 rows (30 days × 20 drivers)
```

---

## Monitoring & Alerts

### Health Checks

**Endpoint Health:**
```bash
python scripts/health_check.py
# Validates: 1 deployed model, 100% traffic, correct output shape
```

**Schema Validation:**
```bash
python scripts/1m_schema_validator.py features_1m_latest.json
# Validates: hash match, critical features present
```

### Cloud Monitoring Alerts

**Create Alerts:**

1. **Predictor Job Failure:**
   - Metric: `cloud_scheduler.googleapis.com/job/failed_execution_count`
   - Filter: `job_id="1m-predictor"`
   - Threshold: `> 0`

2. **Zero Rows in predictions_1m:**
   - Metric: BigQuery query
   - Query: `SELECT COUNT(*) FROM predictions_1m WHERE DATE(as_of_timestamp) = CURRENT_DATE()`
   - Threshold: `= 0`

3. **Endpoint Errors:**
   - Metric: `vertex_ai.googleapis.com/prediction/num_prediction_errors`
   - Filter: `endpoint_id="1m_endpoint"`
   - Threshold: `> 10` (per hour)

4. **Budget Alert:**
   - Budget: $100/month
   - Alert: 80% threshold

---

## Troubleshooting

### Issue: Predictor job fails with schema mismatch

**Symptoms:** Hash validation fails, job aborts

**Fix:**
1. Check feature schema: `cat config/1m_feature_schema.json`
2. Verify training dataset: `SELECT COUNT(*) FROM models_v4.training_dataset_super_enriched`
3. Re-run feature assembler: `python scripts/1m_feature_assembler.py`

### Issue: Gate blend not working (all weights = 1.0)

**Symptoms:** `predictions_1m.blended = FALSE` for D+1-7

**Fix:**
1. Check 1W signals exist: `SELECT * FROM signals_1w ORDER BY as_of_timestamp DESC LIMIT 10`
2. Verify rolled_forecast_7d_json is valid: `SELECT JSON_EXTRACT_ARRAY(rolled_forecast_7d_json) FROM signals_1w WHERE signal_name = 'rolled_forecast_7d'`
3. Re-run 1W signal computer: `python scripts/1w_signal_computer.py`

### Issue: Vertex endpoint redeploys unexpectedly

**Symptoms:** Traffic split changes, endpoint updates

**Fix:**
1. Check endpoint config: `cat config/vertex_1m_config.json`
2. Verify traffic split: `python scripts/health_check.py`
3. Pin endpoint ID: Update Cloud Scheduler job to use exact endpoint ID (not display name)

### Issue: API routes return 503 (no data)

**Symptoms:** `/api/forecast` returns empty or error

**Fix:**
1. Check `agg_1m_latest` has data: `SELECT COUNT(*) FROM agg_1m_latest`
2. Verify aggregator ran: Check Cloud Scheduler logs
3. Manual aggregation: Run `bq query --use_legacy_sql=false < bigquery_sql/create_agg_1m_latest.sql`

---

## Deployment Checklist

### Before Go-Live:

- [ ] All BigQuery tables created (`predictions_1m`, `signals_1w`, `agg_1m_latest`, `shap_drivers`)
- [ ] Vertex endpoint deployed with traffic_split=100%
- [ ] Cloud Scheduler jobs configured (predictor, signal, aggregator, SHAP)
- [ ] Health check passes: `python scripts/health_check.py`
- [ ] Test prediction succeeds: `python scripts/1m_predictor_job.py`
- [ ] API routes return data: `curl https://dashboard.vercel.app/api/forecast`
- [ ] Forward curve displays: Check `/dashboard/forward-curve`
- [ ] Monitoring alerts configured

### Post Go-Live (24h):

- [ ] Verify hourly predictions (30 rows × 24 hours = 720 rows in `predictions_1m`)
- [ ] Check 1W signals updated (5 rows × 24 hours = 120 rows in `signals_1w`)
- [ ] Confirm `agg_1m_latest` refreshed daily
- [ ] Review SHAP drivers populated (600 rows/day)
- [ ] Monitor Vertex AI costs (should be ~$40-60/month)
- [ ] Check Cloud Monitoring for errors

---

## Cost Monitoring

**Expected Monthly Costs:**

- Vertex AI Endpoint: $40-60/month (`n1-standard-2`, min=1)
- BigQuery Storage: $5-10/month (predictions + signals)
- Cloud Scheduler: $0.10/month
- Cloud Run (1W signals): $2-5/month (if using Cloud Run)

**Total: ~$50-75/month**

**Budget Alert:** $100/month (80% threshold = $80)

---

## Rollback Procedure

If system fails catastrophically:

1. **Stop Scheduler Jobs:**
   ```bash
   gcloud scheduler jobs pause 1m-predictor
   gcloud scheduler jobs pause 1w-signal-computer
   ```

2. **Revert to Previous Model:**
   - Update `config/vertex_1m_config.json` with previous model ID
   - Redeploy endpoint: `python scripts/health_check.py`

3. **Use Legacy Routes:**
   - Dashboard will fall back to `predictions.daily_forecasts` if `agg_1m_latest` empty

---

## Support Contacts

- **Model Issues:** Check `MASTER_TRAINING_PLAN.md`
- **Data Issues:** Check BigQuery audit logs
- **Infrastructure:** Check Cloud Console → Vertex AI / BigQuery

---

## Version History

- **v1.0 (2025-01-XX):** Initial deployment - Distilled Quantile Model + 1W Gate Blend

