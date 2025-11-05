# Phase 3.5 Deployment Issue - gcloud CLI Bug

**Date:** November 5, 2025  
**Status:** ⚠️ **KNOWN ISSUE** - gcloud CLI bug preventing Gen2 deployment

---

## Problem

gcloud CLI crashes with `TypeError: expected string or bytes-like object, got 'NoneType'` when deploying Cloud Functions Gen2.

**Error Location:**
```
File: googlecloudsdk/command_lib/functions/service_account_util.py
Line 54: _ExtractServiceAccountEmail
Issue: Trying to parse None service account value
```

---

## Workaround Options

### Option 1: Deploy via Google Cloud Console (Recommended)

1. Go to: https://console.cloud.google.com/functions
2. Click "Create Function"
3. Select "2nd gen" (Gen2)
4. Configure:
   - **Name:** `generate-daily-forecasts`
   - **Region:** `us-central1`
   - **Trigger:** HTTP (Allow unauthenticated)
   - **Runtime:** Python 3.11
   - **Entry point:** `generate_daily_forecasts`
   - **Source:** Upload ZIP or connect to source repository
5. Upload source files:
   - `main.py` (copy from `scripts/generate_daily_forecasts.py`)
   - `GENERATE_PRODUCTION_FORECASTS_V3.sql` (copy from `bigquery_sql/`)
   - `requirements.txt`:
     ```
     google-cloud-bigquery>=3.11.0
     flask>=2.3.0
     ```
6. Set timeout: 540s, Memory: 512MB
7. Deploy

### Option 2: Use Terraform

Create `terraform/cloud_function.tf`:
```hcl
resource "google_cloudfunctions2_function" "generate_daily_forecasts" {
  name        = "generate-daily-forecasts"
  location    = "us-central1"
  description = "Daily forecast generation"

  build_config {
    runtime     = "python311"
    entry_point = "generate_daily_forecasts"
    source {
      storage_source {
        bucket = "your-source-bucket"
        object = "function-source.zip"
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512M"
    timeout_seconds    = 540
    environment_variables = {
      PROJECT = "cbi-v14"
    }
  }

  https_trigger {}
}
```

### Option 3: Update gcloud CLI

```bash
gcloud components update
```

Or install latest:
```bash
# macOS
brew upgrade google-cloud-sdk

# Or reinstall
gcloud components reinstall
```

### Option 4: Manual Deployment via REST API

Use the Cloud Functions API directly:
```bash
# Get access token
TOKEN=$(gcloud auth print-access-token)

# Create function via API
curl -X POST \
  "https://cloudfunctions.googleapis.com/v2/projects/cbi-v14/locations/us-central1/functions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @function_config.json
```

---

## Files Ready for Deployment

All files are prepared and ready:
- ✅ `scripts/generate_daily_forecasts.py` - Function code
- ✅ `bigquery_sql/GENERATE_PRODUCTION_FORECASTS_V3.sql` - SQL query
- ✅ `scripts/requirements.txt` - Dependencies
- ✅ `scripts/deploy_daily_forecasts.sh` - Deployment script (will work once gcloud bug fixed)

---

## After Deployment

Once function is deployed:

1. **Get Function URL:**
   ```bash
   gcloud functions describe generate-daily-forecasts \
     --region=us-central1 --gen2 \
     --format="value(serviceConfig.uri)"
   ```

2. **Test Function:**
   ```bash
   curl -X POST <FUNCTION_URL>
   ```

3. **Create Scheduler:**
   ```bash
   gcloud scheduler jobs create http generate-forecasts-daily \
     --location=us-central1 \
     --schedule="0 7 * * *" \
     --uri="<FUNCTION_URL>" \
     --http-method=POST \
     --time-zone="America/New_York" \
     --project=cbi-v14
   ```

---

## Next Steps

1. Deploy function via Cloud Console (Option 1) - fastest
2. Set up Cloud Scheduler after deployment
3. Test manually
4. Verify forecasts are generated in `production_forecasts` table

---

**Last Updated:** November 5, 2025

