# Phase 3.5 Deployment - Ready to Deploy

**Status:** ✅ All files ready, deployment blocked by gcloud CLI bug

---

## Current Situation

✅ **Files Ready:**
- `scripts/generate_daily_forecasts.py` - Cloud Function code
- `bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql` - Forecast SQL
- `scripts/requirements.txt` - Dependencies
- Source ZIP created and uploaded to GCS: `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`

❌ **gcloud CLI Bug:**
- Error: `TypeError: expected string or bytes-like object, got 'NoneType'`
- Affects Gen2 Cloud Functions deployment
- Google Cloud SDK version: 546.0.0 (latest)

---

## ✅ RECOMMENDED: Deploy via Cloud Console (5 minutes)

### Step 1: Navigate to Cloud Functions
https://console.cloud.google.com/functions/create?project=cbi-v14

### Step 2: Configure Function
- **Name:** `generate-daily-forecasts`
- **Region:** `us-central1`
- **Environment:** `2nd gen`
- **Trigger Type:** `HTTP`
- **Authentication:** `Allow unauthenticated invocations` ✅

### Step 3: Runtime Settings
- **Runtime:** `Python 3.11`
- **Entry Point:** `generate_daily_forecasts`
- **Timeout:** `540 seconds`
- **Memory:** `512 MB`
- **Max Instances:** `1`

### Step 4: Source Code
- **Source:** `Upload ZIP file`
- **ZIP Location:** Download from `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`
  ```bash
  gsutil cp gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip /tmp/
  ```
- Or upload files directly:
  - `main.py` (copy from `scripts/generate_daily_forecasts.py`)
  - `GENERATE_PRODUCTION_FORECASTS_V3.sql` (copy from `bigquery_sql/`)
  - `requirements.txt`:
    ```
    google-cloud-bigquery>=3.11.0
    flask>=2.3.0
    ```

### Step 5: Deploy
Click **Deploy** and wait ~2-3 minutes

---

## Step 6: Get Function URL

After deployment, get the function URL:

```bash
gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)"
```

Or find it in Console under the function's **Trigger** tab.

---

## Step 7: Create Cloud Scheduler

```bash
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

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

## Step 8: Test Function

```bash
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

curl -X POST "$FUNCTION_URL"
```

**Expected Response:**
```json
{
  "status": "success",
  "forecasts_generated": 4,
  "horizons": "1M,1W,3M,6M",
  "execution_time_seconds": 5.23,
  "timestamp": "2025-11-05T..."
}
```

---

## Step 9: Verify Forecasts

```sql
SELECT 
  forecast_date,
  horizon,
  predicted_value,
  confidence,
  model_name
FROM `cbi-v14.predictions_uc1.production_forecasts`
WHERE forecast_date = CURRENT_DATE()
ORDER BY 
  CASE horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;
```

**Expected:** 4 rows (one for each horizon)

---

## Troubleshooting

### Function Not Found
- Check function name: `generate-daily-forecasts`
- Check region: `us-central1`
- Verify project: `cbi-v14`

### SQL File Not Found
- Ensure `GENERATE_PRODUCTION_FORECASTS_V3.sql` is in the same directory as `main.py`
- Check Cloud Function logs for file path errors

### BigQuery Permission Errors
- Verify Cloud Function service account has BigQuery permissions
- Check: `cbi-v14@appspot.gserviceaccount.com` has `BigQuery Data Editor` role

### Forecasts Not Generated
- Check Cloud Function logs:
  ```bash
  gcloud functions logs read generate-daily-forecasts \
    --region=us-central1 --gen2 --limit=50
  ```

---

## Next Steps After Deployment

1. ✅ Function deployed
2. ✅ Scheduler created
3. ✅ Test successful
4. 🔥 **Phase 3.6:** Implement backtesting infrastructure
5. 🔥 **Phase 3.7:** Implement monitoring & alerts

---

**Last Updated:** November 5, 2025  
**Status:** Ready for Console deployment

