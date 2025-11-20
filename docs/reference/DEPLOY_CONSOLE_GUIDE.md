---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Phase 3.5: Cloud Console Deployment Guide

**Status:** ✅ Ready for Immediate Deployment  
**Date:** November 5, 2025

---

## Quick Deployment Steps

### 1. Navigate to Cloud Functions Console
**Direct Link:** https://console.cloud.google.com/functions/create?project=cbi-v14

### 2. Configure Function

| Setting | Value |
|---------|-------|
| **Name** | `generate-daily-forecasts` |
| **Region** | `us-central1` |
| **Generation** | **2nd gen** (must be Gen2) |
| **Trigger** | HTTP (Allow unauthenticated invocations) |
| **Runtime** | Python 3.11 |
| **Entry point** | `generate_daily_forecasts` |

### 3. Upload Source Code

**Method:** Inline Editor or ZIP Upload

**Files to upload:**

#### File 1: `main.py`
Copy contents from: `scripts/generate_daily_forecasts.py`

#### File 2: `GENERATE_PRODUCTION_FORECASTS_V3.sql`
Copy contents from: `bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql`

#### File 3: `requirements.txt`
```
google-cloud-bigquery>=3.11.0
flask>=2.3.0
```

### 4. Configure Resources

- **Timeout:** 540 seconds (9 minutes)
- **Memory:** 512 MB
- **Max instances:** 1
- **Min instances:** 0

### 5. Deploy

Click **Deploy** and wait for deployment to complete (~2-3 minutes)

---

## Post-Deployment: Scheduler Setup

Once function is deployed, run these commands:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

# Verify URL
echo "Function URL: $FUNCTION_URL"

# Create scheduler job
gcloud scheduler jobs create http generate-forecasts-daily \
  --location=us-central1 \
  --schedule="0 7 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --project=cbi-v14

# Verify scheduler
gcloud scheduler jobs describe generate-forecasts-daily \
  --location=us-central1 \
  --project=cbi-v14
```

---

## Verification Steps

### 1. Test Function Manually
```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)")

# Test
curl -X POST "$FUNCTION_URL"
```

### 2. Check Logs
```bash
gcloud functions logs read generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --limit=50
```

### 3. Verify Forecasts Generated
```sql
-- Check forecasts for today
SELECT 
  horizon,
  forecast_date,
  target_date,
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

### 4. Verify Scheduler
```bash
# Check scheduler status
gcloud scheduler jobs describe generate-forecasts-daily \
  --location=us-central1 \
  --project=cbi-v14

# Manually trigger (for testing)
gcloud scheduler jobs run generate-forecasts-daily \
  --location=us-central1 \
  --project=cbi-v14
```

---

## Expected Results

After successful deployment and first run:

✅ Function URL returned (HTTPS endpoint)  
✅ 4 forecasts generated in `production_forecasts` table  
✅ Scheduler job created and scheduled  
✅ Logs show successful execution  

---

## Troubleshooting

**Function not found:**
- Verify deployment completed
- Check function name matches exactly

**Authentication errors:**
- Ensure function allows unauthenticated invocations
- Check IAM permissions for Cloud Functions

**SQL execution errors:**
- Verify SQL file is in same directory as main.py
- Check BigQuery permissions for service account

**Scheduler creation fails:**
- Ensure function is deployed first
- Verify scheduler API is enabled

---

**Last Updated:** November 5, 2025

