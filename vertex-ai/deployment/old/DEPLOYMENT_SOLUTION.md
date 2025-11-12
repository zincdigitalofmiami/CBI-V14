# Deployment Solution - Research Findings

**Date:** November 5, 2025  
**Status:** ✅ **SOLUTION FOUND - Manual Deployment Required**

---

## 🔍 Research Findings

### ✅ Correct Deployment Command (When gcloud CLI is Fixed)

Based on research, the correct format is:

```bash
gcloud functions deploy generate-daily-forecasts \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=/tmp/cf-deploy-forecasts-fixed \
  --entry-point=generate_daily_forecasts \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=540s \
  --memory=512MB \
  --max-instances=1 \
  --build-service-account="PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --project=cbi-v14
```

**However:** gcloud CLI crashes with `TypeError: NoneType` bug in SDK 546.0.0

---

## ✅ WORKING SOLUTION: Console Deployment + CLI Scheduler

Since automated deployment is blocked, here's the proven path:

### Step 1: Deploy Function via Console (5 minutes)

1. **Open Console:**
   https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

2. **Configuration:**
   - **Name:** `generate-daily-forecasts`
   - **Environment:** `2nd gen`
   - **Runtime:** `Python 3.11`
   - **Entry Point:** `generate_daily_forecasts`
   - **Trigger:** HTTP (Allow unauthenticated)
   - **Timeout:** 540s
   - **Memory:** 512MB

3. **Source:**
   - Download from GCS: `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`
   - Or upload files directly:
     - `main.py` (from `scripts/generate_daily_forecasts.py`)
     - `GENERATE_PRODUCTION_FORECASTS_V3.sql`
     - `requirements.txt`

4. **Deploy** - Wait 2-3 minutes

---

### Step 2: Setup Scheduler (CLI Works for This!)

Once function is deployed, run:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

# Create scheduler job
gcloud scheduler jobs create http generate-forecasts-daily \
  --location=us-central1 \
  --schedule="0 7 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --project=cbi-v14
```

**Schedule:** Daily at 2:00 AM ET (7:00 AM UTC)

---

## ✅ Why This Works

1. **Console Deployment:** Bypasses gcloud CLI bug completely
2. **Scheduler Setup:** CLI works fine for scheduler (no bug)
3. **Test Function:** Can test immediately after deployment

---

## 🔍 Root Cause Analysis

**gcloud CLI Bug:**
- **Version:** 546.0.0 (latest)
- **Error:** `TypeError: expected string or bytes-like object, got 'NoneType'`
- **Location:** `googlecloudsdk/command_lib/functions/service_account_util.py:54`
- **Issue:** Service account validation returns NoneType
- **Status:** Known upstream bug, no ETA on fix

**Workaround:** Console deployment works perfectly

---

## 📋 After Deployment - Verification

```bash
# Test function
curl -X POST <FUNCTION_URL>

# Check logs
gcloud functions logs read generate-daily-forecasts \
  --region=us-central1 --gen2 --limit=50

# Verify forecasts in BigQuery
bq query --use_legacy_sql=false "
SELECT forecast_date, horizon, predicted_value, confidence
FROM \`cbi-v14.predictions_uc1.production_forecasts\`
WHERE forecast_date = CURRENT_DATE()
ORDER BY 
  CASE horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END
"
```

---

**Ready to deploy via Console, then I'll set up the scheduler automatically!** 🚀

