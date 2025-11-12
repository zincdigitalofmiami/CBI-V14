# Deployment Status - Phase 3.5

**Date:** November 5, 2025  
**Status:** ⚠️ **AUTOMATED DEPLOYMENT BLOCKED**

---

## ❌ Blocking Issues

1. **gcloud CLI Bug:** `TypeError: NoneType` - Confirmed in SDK 546.0.0
2. **REST API:** Requires build service account with specific format (Org Policy)
3. **Python SDK:** Not installed/configured

---

## ✅ What's Ready

- ✅ **Code:** `scripts/generate_daily_forecasts.py` (fixed, imports OK)
- ✅ **SQL:** `bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql` (uses SHORT model names)
- ✅ **Dependencies:** `requirements.txt` (minimal, correct)
- ✅ **Source ZIP:** `/tmp/forecasts-deploy-fixed.zip` (5.8K, uploaded to GCS)
- ✅ **GCS Location:** `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`

---

## 🚀 Manual Deployment Required (5 minutes)

**The automated deployment is blocked, but manual deployment via Console is straightforward:**

### Step 1: Open Console
https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

### Step 2: Configure
- **Name:** `generate-daily-forecasts`
- **Environment:** `2nd gen`
- **Runtime:** `Python 3.11`
- **Entry Point:** `generate_daily_forecasts`
- **Trigger:** HTTP (Allow unauthenticated)
- **Timeout:** 540s
- **Memory:** 512MB

### Step 3: Upload Source
**Option A:** Download from GCS:
```bash
gsutil cp gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip /tmp/
```
Then upload `/tmp/forecasts-function-source.zip` in Console

**Option B:** Upload files directly:
- `main.py` (copy from `scripts/generate_daily_forecasts.py`)
- `GENERATE_PRODUCTION_FORECASTS_V3.sql` (copy from `bigquery_sql/`)
- `requirements.txt`:
  ```
  google-cloud-bigquery>=3.11.0
  flask>=2.3.0
  ```

### Step 4: Deploy
Click **Deploy** - wait 2-3 minutes

---

## ✅ After Deployment - Setup Scheduler

Once function is deployed, run:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

# Create scheduler
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

## 🔍 Verify Deployment

```bash
# Test function
curl -X POST <FUNCTION_URL>

# Check logs
gcloud functions logs read generate-daily-forecasts \
  --region=us-central1 --gen2 --limit=50

# Verify forecasts
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

**Next:** Once deployed, I can set up the scheduler automatically! 🚀

