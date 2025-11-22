# GCP & BigQuery Connection Troubleshooting Guide

**Date:** 2025-01-XX  
**Status:** Active troubleshooting guide

---

## Quick Diagnostic

Run the diagnostic script:
```bash
python3 scripts/utilities/diagnose_gcp_connections.py
```

---

## Common Issues & Solutions

### Issue 1: "Read-Only" Access Error

**Symptoms:**
- Queries work but writes fail
- Error: "Permission denied" or "Access Denied"

**Diagnosis:**
```bash
# Check your IAM roles
gcloud projects get-iam-policy cbi-v14 --flatten="bindings[].members" --format="table(bindings.role,bindings.members)" | grep your-email

# Test write access
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); job = client.query('CREATE OR REPLACE VIEW \`cbi-v14.ops.test_write\` AS SELECT 1 as test'); job.result(); print('✅ Write works')"
```

**Solutions:**

1. **If you have `roles/bigquery.admin` or `roles/owner`:**
   - ✅ You should have full access
   - Check if there's a dataset-level permission issue:
   ```bash
   # Check dataset permissions
   bq show --format=prettyjson cbi-v14:dataset_name
   ```

2. **If you're missing permissions:**
   ```bash
   # Request these roles from project admin:
   # - roles/bigquery.admin (full access)
   # - OR roles/bigquery.dataEditor (read/write data)
   # - OR roles/bigquery.dataViewer (read-only)
   ```

3. **If using Application Default Credentials:**
   ```bash
   # Refresh ADC
   gcloud auth application-default login
   ```

---

### Issue 2: Authentication Not Working

**Symptoms:**
- `gcloud` commands fail
- BigQuery client creation fails
- Error: "Could not automatically determine credentials"

**Diagnosis:**
```bash
# Check current auth
gcloud auth list

# Check active account
gcloud config get-value account

# Check project
gcloud config get-value project

# Test access token
gcloud auth print-access-token
```

**Solutions:**

1. **Re-authenticate:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Set active account:**
   ```bash
   gcloud config set account your-email@domain.com
   ```

3. **Set project:**
   ```bash
   gcloud config set project cbi-v14
   ```

4. **If using service account key:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

---

### Issue 3: BigQuery Client Creation Fails

**Symptoms:**
- Python `bigquery.Client()` fails
- Error: "Project not found" or "Permission denied"

**Diagnosis:**
```python
from google.cloud import bigquery
import os

# Check environment
print("GCP_PROJECT_ID:", os.getenv("GCP_PROJECT_ID"))
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Try creating client
try:
    client = bigquery.Client(project="cbi-v14")
    print("✅ Client created")
except Exception as e:
    print(f"❌ Error: {e}")
```

**Solutions:**

1. **Set project explicitly:**
   ```python
   client = bigquery.Client(project="cbi-v14")
   ```

2. **Use environment variable:**
   ```bash
   export GCP_PROJECT_ID=cbi-v14
   ```

3. **Check credentials:**
   ```bash
   # Verify ADC exists
   ls -la ~/.config/gcloud/application_default_credentials.json
   
   # Or set service account key
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

---

### Issue 4: Service Account Issues

**Symptoms:**
- Scripts fail when using service accounts
- Error: "Service account does not have permission"

**Diagnosis:**
```bash
# List service accounts
gcloud iam service-accounts list --project=cbi-v14

# Check service account permissions
gcloud projects get-iam-policy cbi-v14 --flatten="bindings[].members" | grep serviceAccount
```

**Solutions:**

1. **Grant necessary roles to service account:**
   ```bash
   SERVICE_ACCOUNT="your-sa@cbi-v14.iam.gserviceaccount.com"
   
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

2. **Check dataset-level permissions:**
   ```bash
   # Grant access to specific dataset
   bq grant --role=roles/bigquery.dataEditor \
     --serviceAccount=your-sa@cbi-v14.iam.gserviceaccount.com \
     cbi-v14:dataset_name
   ```

---

### Issue 5: Environment Variables Not Set

**Symptoms:**
- Scripts can't find project ID
- Credentials not found

**Diagnosis:**
```bash
# Check environment variables
echo "GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
```

**Solutions:**

1. **Set in shell profile (~/.zshrc or ~/.bash_profile):**
   ```bash
   export GCP_PROJECT_ID=cbi-v14
   # Optional: if using service account key
   # export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

2. **Set for current session:**
   ```bash
   export GCP_PROJECT_ID=cbi-v14
   ```

3. **Use gcloud config (recommended):**
   ```bash
   gcloud config set project cbi-v14
   # This is automatically used by BigQuery client
   ```

---

## Verification Checklist

After fixing issues, verify everything works:

```bash
# 1. Check gcloud auth
gcloud auth list
gcloud config get-value project

# 2. Test BigQuery read
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); result = client.query('SELECT 1 as test').result(); print('✅ Read works:', list(result))"

# 3. Test BigQuery write (if needed)
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='cbi-v14'); job = client.query('CREATE OR REPLACE VIEW \`cbi-v14.ops.test_write\` AS SELECT CURRENT_TIMESTAMP() as ts'); job.result(); client.delete_table('cbi-v14.ops.test_write'); print('✅ Write works')"

# 4. Run full diagnostic
python3 scripts/utilities/diagnose_gcp_connections.py
```

---

## Current Status (as of diagnostic run)

✅ **gcloud authentication:** Working  
✅ **BigQuery read access:** Working  
✅ **BigQuery write access:** Working  
✅ **IAM permissions:** Owner + BigQuery Admin  
✅ **Application Default Credentials:** Configured  

**Your account:** `zinc@zincdigital.co`  
**Project:** `cbi-v14`  
**Roles:** Owner, BigQuery Admin, and 13 other admin roles

---

## If Issues Persist

1. **Check specific error messages:**
   - Copy the exact error text
   - Check which command/script is failing
   - Note the context (local vs. remote, which tool, etc.)

2. **Review logs:**
   ```bash
   # Check gcloud logs
   gcloud logging read "resource.type=bigquery_project" --limit=10
   
   # Check BigQuery job history
   bq ls -j --max_results=10
   ```

3. **Contact project admin:**
   - If permissions need to be granted
   - If service accounts need to be created
   - If there are project-level restrictions

---

## Related Documentation

- `src/utils/gcp_utils.py` - GCP utility functions
- `scripts/setup/validate_system.py` - System validation script
- `docs/reports/bigquery/BIGQUERY_VERCEL_CONNECTION_REVIEW.md` - Vercel connection guide




