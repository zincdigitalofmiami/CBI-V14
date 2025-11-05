# Deploy via Console - Exact Steps

**Status:** ✅ Ready to deploy

---

## 🚀 Step 1: Deploy Function via Console

**Open this link:**
https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

### Fill in EXACTLY:

| Field | Value |
|-------|-------|
| **Name** | `generate-daily-forecasts` |
| **Region** | `us-central1` |
| **Environment** | `2nd generation` |
| **Runtime** | `Python 3.11` |
| **Trigger** | `HTTP` |
| **Allow unauthenticated** | ✅ (checked) |
| **Entry point** | `generate_daily_forecasts` |
| **Source** | `From Cloud Storage` → paste: `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip` |
| **Build service account** | `1065708057795@cloudbuild.gserviceaccount.com` |
| **Execution service account** | (leave default) |
| **Memory** | `512 MB` |
| **Timeout** | `540s` |

### Click **Deploy**

⏱️ Wait 2-3 minutes for deployment

---

## 🔗 Step 2: Get Function URL

After deployment, the function URL will be:
```
https://us-central1-cbi-v14.cloudfunctions.net/generate-daily-forecasts
```

Or find it in the function overview page.

---

## ⏰ Step 3: Setup Scheduler (After Deployment)

Once function is deployed, run:

```bash
cd /Users/zincdigital/CBI-V14
./scripts/setup_scheduler_after_deploy.sh
```

Or manually:

```bash
gcloud scheduler jobs create http generate-forecasts-daily \
  --location=us-central1 \
  --schedule="0 7 * * *" \
  --uri="https://us-central1-cbi-v14.cloudfunctions.net/generate-daily-forecasts" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --project=cbi-v14
```

**Schedule:** Daily at 2:00 AM ET (7:00 AM UTC)

---

## ✅ Step 4: Test & Verify

### Test Function:
```bash
curl -X POST https://us-central1-cbi-v14.cloudfunctions.net/generate-daily-forecasts
```

### Verify Forecasts in BigQuery:
```sql
SELECT 
  forecast_date,
  horizon,
  predicted_value,
  confidence,
  model_name
FROM `cbi-v14.predictions_uc1.production_forecasts`
ORDER BY created_at DESC
LIMIT 10;
```

**Expected:** 4 rows (one for each horizon: 1W, 1M, 3M, 6M)

---

## ✅ Status Checklist

- [x] Function code ready (`generate_daily_forecasts.py`)
- [x] SQL file ready (`GENERATE_PRODUCTION_FORECASTS_V3.sql`)
- [x] Dependencies ready (`requirements.txt`)
- [x] Source ZIP uploaded to GCS
- [x] All errors fixed (imports, requirements)
- [x] Scheduler setup script ready
- [ ] Function deployed via Console ← **YOU ARE HERE**
- [ ] Scheduler created
- [ ] Function tested
- [ ] Forecasts verified

---

**Ready to deploy!** 🚀

