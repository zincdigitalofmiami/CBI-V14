---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Quick Deploy - Phase 3.5 Cloud Function

**Status:** Ready to deploy now (automation later)

---

## 🚀 Fast Deployment (5 minutes)

### Step 1: Open Console
**Click this link:**
https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

### Step 2: Basic Settings
- **Function name:** `generate-daily-forecasts`
- **Region:** `us-central1` ✅ (pre-selected)
- **Environment:** `2nd gen` ✅

### Step 3: Trigger Configuration
- **Trigger type:** `HTTP`
- **Authentication:** `Allow unauthenticated invocations` ✅

### Step 4: Runtime Settings
- **Runtime:** `Python 3.11`
- **Entry point:** `generate_daily_forecasts`
- **Timeout:** `540 seconds`
- **Memory:** `512 MB`
- **Max instances:** `1`

### Step 5: Source Code
**Option A: Upload ZIP (Recommended)**
- Click "Upload ZIP file"
- Upload: `/tmp/forecasts-deploy.zip`
- Or download from GCS: `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`

**Option B: Upload Files**
- Upload these 3 files:
  - `main.py` (from `scripts/generate_daily_forecasts.py`)
  - `GENERATE_PRODUCTION_FORECASTS_V3.sql` (from `bigquery_sql/`)
  - `requirements.txt`:
    ```
    google-cloud-bigquery>=3.11.0
    flask>=2.3.0
    ```

### Step 6: Deploy
Click **"Deploy"** button (bottom right)

⏱️ **Wait:** 2-3 minutes for deployment

---

## ✅ Verify Deployment

After deployment completes:

```bash
# Get function URL
gcloud functions describe generate-daily-forecasts \
  --region=us-central1 --gen2 \
  --format="value(serviceConfig.uri)"

# Test function
curl -X POST <FUNCTION_URL>
```

**Expected:** JSON response with `"status": "success"`

---

## 📋 What's Included

✅ Cloud Function code (`main.py`)  
✅ SQL file (`GENERATE_PRODUCTION_FORECASTS_V3.sql`)  
✅ Dependencies (`requirements.txt`)  
✅ Error handling & logging  
✅ Duplicate prevention  
✅ Forecast verification  

---

## 🔄 Automation Later

Once deployed, we'll set up:
- Cloud Scheduler (daily at 2 AM ET)
- Monitoring & alerts
- Backtesting infrastructure

---

**Ready to deploy!** 🚀

