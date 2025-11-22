# Codex GCP Credentials Setup Guide

**Date:** 2025-01-XX  
**Purpose:** Enable Codex (or other AI assistants) to access BigQuery/GCP

---

## Current Status

✅ **Composer (Current Assistant):** Has full BigQuery access via Application Default Credentials  
⚠️ **Codex:** Needs credentials configured

---

## Quick Setup for Codex

### Option 1: Application Default Credentials (Recommended)

If Codex runs in the same environment, ADC should work automatically:

```bash
# Verify ADC is configured
gcloud auth application-default print-access-token

# If not configured, run:
gcloud auth application-default login
```

**This should work automatically** if Codex runs in the same terminal/environment.

---

### Option 2: Service Account Key (For Separate Environments)

If Codex runs in a different environment or needs explicit credentials:

1. **Create Service Account (if needed):**
   ```bash
   # List existing service accounts
   gcloud iam service-accounts list --project=cbi-v14
   
   # Or create a new one for Codex
   gcloud iam service-accounts create codex-assistant \
     --display-name="Codex AI Assistant" \
     --project=cbi-v14
   ```

2. **Grant Permissions:**
   ```bash
   SERVICE_ACCOUNT="codex-assistant@cbi-v14.iam.gserviceaccount.com"
   
   # For read-only access
   gcloud projects add-iam-policy-binding cbi-v14 \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/bigquery.dataViewer"
   
   # For read/write access
   gcloud projects add-iam-policy-binding cbi-v14 \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/bigquery.dataEditor"
   
   # For full admin access
   gcloud projects add-iam-policy-binding cbi-v14 \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/bigquery.admin"
   ```

3. **Create and Download Key:**
   ```bash
   gcloud iam service-accounts keys create ~/codex-gcp-key.json \
     --iam-account=codex-assistant@cbi-v14.iam.gserviceaccount.com \
     --project=cbi-v14
   ```

4. **Set Environment Variables:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$HOME/codex-gcp-key.json"
   export GCP_PROJECT_ID="cbi-v14"
   ```

5. **Test Access:**
   ```python
   from google.cloud import bigquery
   client = bigquery.Client(project="cbi-v14")
   result = client.query("SELECT 1 as test").result()
   print("✅ Access works:", list(result))
   ```

---

## For Codex in Cursor/IDE

If Codex runs within Cursor or another IDE:

1. **Check if ADC is available:**
   - Cursor should inherit your shell's environment
   - ADC at `~/.config/gcloud/application_default_credentials.json` should work

2. **If ADC doesn't work, set environment variables:**
   - In Cursor settings or `.env` file:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
     GCP_PROJECT_ID=cbi-v14
     ```

3. **Or use the existing service account key:**
   ```bash
   # Check if key exists
   ls -la config/terraform/cbi-v14-gcp-key.json
   
   # If it exists, use it:
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/config/terraform/cbi-v14-gcp-key.json"
   export GCP_PROJECT_ID="cbi-v14"
   ```

---

## Verification

After setup, verify access:

```python
# Test script
from google.cloud import bigquery
import os

print("GCP_PROJECT_ID:", os.getenv("GCP_PROJECT_ID"))
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

try:
    client = bigquery.Client(project="cbi-v14")
    result = client.query("SELECT 1 as test").result()
    print("✅ BigQuery access works!")
    print("Result:", list(result))
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## Current Credentials Status

**Your Account:** `zinc@zincdigital.co`  
**Project:** `cbi-v14`  
**ADC Location:** `~/.config/gcloud/application_default_credentials.json`  
**ADC Status:** ✅ Configured and working

**Service Account Key:** `config/terraform/cbi-v14-gcp-key.json` (if exists)

---

## Alternative: Run SQL Yourself

If Codex can't access BigQuery directly, you can:

1. **Get SQL from Codex** (Codex generates the SQL)
2. **Run it yourself** in BigQuery Console or terminal
3. **Report results back** to Codex

**BigQuery Console:** https://console.cloud.google.com/bigquery?project=cbi-v14

**Or from terminal:**
```bash
bq query --use_legacy_sql=false "YOUR_SQL_HERE"
```

---

## Need Help?

If Codex still can't access BigQuery after setup:
1. Check error messages
2. Verify environment variables are set
3. Test with the verification script above
4. Check IAM permissions for the service account




