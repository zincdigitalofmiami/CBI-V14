# Prediction Automation Setup Guide

**Status:** Implementation Complete  
**Date:** November 2025  
**Purpose:** Guide for deploying and using the automated prediction system

---

## Overview

This guide covers the three critical phases implemented to transform "half-assed" predictions into a production-grade system:

1. **Phase 3.5: Daily Prediction Automation** - Automated daily forecast generation
2. **Phase 3.6: Backtesting Infrastructure** - Accuracy tracking and historical comparison
3. **Phase 3.7: Prediction Monitoring** - Quality checks and alerts

---

## Phase 3.5: Daily Prediction Automation

### Files Created
- `scripts/generate_daily_forecasts.py` - Cloud Function for daily forecast generation
- `scripts/deploy_daily_forecasts.sh` - Deployment script for Cloud Function and Scheduler

### Setup Steps

1. **Deploy Cloud Function:**
   ```bash
   cd /Users/zincdigital/CBI-V14
   ./scripts/deploy_daily_forecasts.sh
   ```

2. **Manual Test (Optional):**
   ```bash
   # Get function URL
   FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts --region=us-central1 --gen2 --format="value(serviceConfig.uri)")
   
   # Test it
   curl -X POST $FUNCTION_URL
   ```

3. **Verify Scheduler:**
   ```bash
   gcloud scheduler jobs describe generate-forecasts-daily --location=us-central1
   ```

### What It Does
- Runs daily at 2 AM ET (7 AM UTC)
- Executes `GENERATE_PRODUCTION_FORECASTS_V3.sql`
- Generates forecasts for all 4 horizons (1W, 1M, 3M, 6M)
- Updates prediction accuracy for past forecasts
- Inserts results into `cbi-v14.predictions_uc1.production_forecasts`

---

## Phase 3.6: Backtesting Infrastructure

### Files Created
- `bigquery_sql/CREATE_PREDICTION_ACCURACY_TABLE.sql` - Creates accuracy tracking table
- `bigquery_sql/BACKFILL_PREDICTION_ACCURACY.sql` - Backfills historical accuracy data
- `bigquery_sql/CREATE_ACCURACY_DASHBOARD_VIEW.sql` - Creates dashboard view for accuracy metrics

### Setup Steps

1. **Create Accuracy Table:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_PREDICTION_ACCURACY_TABLE.sql
   ```

2. **Backfill Historical Accuracy:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/BACKFILL_PREDICTION_ACCURACY.sql
   ```

3. **Create Dashboard View:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_ACCURACY_DASHBOARD_VIEW.sql
   ```

4. **Verify Accuracy Data:**
   ```sql
   SELECT * FROM `cbi-v14.api.vw_prediction_accuracy`
   ORDER BY horizon, mean_ape;
   ```

### What It Does
- Tracks prediction accuracy by comparing forecasts vs actuals
- Calculates MAPE, MAE, and confidence interval coverage
- Automatically updates when forecasts reach their target date
- Provides dashboard view for accuracy metrics

---

## Phase 3.7: Prediction Monitoring

### Files Created
- `scripts/monitor_predictions.py` - Cloud Function for daily monitoring
- `scripts/deploy_monitoring.sh` - Deployment script
- `bigquery_sql/CREATE_MONITORING_TABLE.sql` - Creates monitoring checks table
- `bigquery_sql/CREATE_MONITORING_DASHBOARD_VIEW.sql` - Creates dashboard view

### Setup Steps

1. **Create Monitoring Table:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_MONITORING_TABLE.sql
   ```

2. **Deploy Monitoring Function:**
   ```bash
   cd /Users/zincdigital/CBI-V14
   ./scripts/deploy_monitoring.sh
   ```

3. **Create Dashboard View:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_MONITORING_DASHBOARD_VIEW.sql
   ```

4. **Verify Monitoring:**
   ```sql
   SELECT * FROM `cbi-v14.api.vw_prediction_monitoring`
   ORDER BY check_date DESC
   LIMIT 20;
   ```

### What It Does
- Runs 15 minutes after forecast generation (2:15 AM ET)
- Checks for stale predictions
- Validates prediction quality (reasonable price ranges)
- Detects accuracy degradation
- Stores checks in `cbi-v14.predictions_uc1.monitoring_checks`
- Provides dashboard view for monitoring status

---

## Complete Deployment Order

1. **Create Tables:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_PREDICTION_ACCURACY_TABLE.sql
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_MONITORING_TABLE.sql
   ```

2. **Create Views:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_ACCURACY_DASHBOARD_VIEW.sql
   bq query --use_legacy_sql=false < bigquery_sql/CREATE_MONITORING_DASHBOARD_VIEW.sql
   ```

3. **Backfill Historical Accuracy:**
   ```bash
   bq query --use_legacy_sql=false < bigquery_sql/BACKFILL_PREDICTION_ACCURACY.sql
   ```

4. **Deploy Cloud Functions:**
   ```bash
   ./scripts/deploy_daily_forecasts.sh
   ./scripts/deploy_monitoring.sh
   ```

---

## Verification Queries

### Check Daily Forecasts
```sql
SELECT 
  forecast_date,
  COUNT(*) as forecast_count,
  MIN(created_at) as first_forecast,
  MAX(created_at) as last_forecast
FROM `cbi-v14.predictions_uc1.production_forecasts`
WHERE forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY forecast_date
ORDER BY forecast_date DESC;
```

### Check Accuracy Metrics
```sql
SELECT * FROM `cbi-v14.api.vw_prediction_accuracy`
ORDER BY horizon, mean_ape;
```

### Check Monitoring Status
```sql
SELECT * FROM `cbi-v14.api.vw_prediction_monitoring`
ORDER BY check_date DESC
LIMIT 20;
```

---

## Troubleshooting

### Forecast Generation Fails
- Check Cloud Function logs: `gcloud functions logs read generate-daily-forecasts --region=us-central1 --limit=50`
- Verify SQL file exists: `ls -la bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql`
- Check BigQuery permissions

### Monitoring Not Running
- Verify scheduler: `gcloud scheduler jobs describe monitor-predictions-daily --location=us-central1`
- Check Cloud Function logs: `gcloud functions logs read monitor-predictions --region=us-central1 --limit=50`
- Verify monitoring table exists

### Accuracy Not Updating
- Check if accuracy table exists: `bq ls cbi-v14:predictions_uc1 | grep prediction_accuracy`
- Verify forecast dates match target dates: Run verification query above
- Check for actual price data on target dates

---

## Cost Estimates

- **Cloud Functions:** ~$0.40/month (2 functions, daily execution, 5-10 minutes each)
- **Cloud Scheduler:** Free (up to 3 jobs)
- **BigQuery:** ~$0.10/month (storage + queries for monitoring/accuracy)
- **Total:** ~$0.50/month

---

## Next Steps

After deployment:
1. Monitor first few days of execution
2. Review accuracy metrics weekly
3. Set up alerts for monitoring failures (optional)
4. Integrate dashboard views into main dashboard

---

**Last Updated:** November 2025  
**Status:** ✅ Implementation Complete

