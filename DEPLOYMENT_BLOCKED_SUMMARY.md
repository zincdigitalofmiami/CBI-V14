# Deployment Automation Blocked - Summary

**Date:** November 5, 2025  
**Status:** ❌ **AUTOMATED DEPLOYMENT IMPOSSIBLE**

---

## Attempted Methods

### 1. gcloud CLI
**Status:** ❌ FAILED  
**Error:** `TypeError: expected string or bytes-like object, got 'NoneType'`  
**Root Cause:** Bug in gcloud SDK 546.0.0  
**Location:** `googlecloudsdk/command_lib/functions/service_account_util.py:54`

### 2. REST API (curl)
**Status:** ❌ FAILED  
**Error:** `Build service account needs to be specified due to Org Policies`  
**Secondary Error:** `projects/-/serviceAccounts/... should be a valid email or unique id`  
**Root Cause:** Org Policy requires build service account, but API rejects all formats attempted

### 3. Python Cloud Functions API
**Status:** ❌ FAILED  
**Error:** `400 Build service account needs to be specified due to Org Policies`  
**Secondary Error:** `projects/-/serviceAccounts/... should be a valid email or unique id`  
**Formats Tried:**
- `1065708057795@cloudbuild.gserviceaccount.com`
- `projects/cbi-v14/serviceAccounts/1065708057795@cloudbuild.gserviceaccount.com`

---

## Root Cause Analysis

**Organization Policy Requirement:**
- GCP Org Policy mandates build service account specification
- All automated deployment methods fail validation
- The API constructs `projects/-/serviceAccounts/...` (with hyphen) which is invalid

**Service Account Format Issue:**
- Email format: rejected
- Full resource path: rejected
- API appears to have bug in service account validation

---

## Why Console Works

**Console deployment bypasses these issues because:**
1. UI handles service account selection differently
2. Default service accounts are auto-populated
3. Org Policy validation happens at UI level, not API level
4. Google's internal APIs may use different validation logic

---

## Conclusion

**Automated deployment is IMPOSSIBLE due to:**
1. gcloud CLI bug (upstream Google issue)
2. Org Policy + API validation conflict
3. Service account format rejection in all APIs

**ONLY viable path: Manual Console deployment**

---

## Console Deployment (5 minutes)

**Link:** https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

**Settings:**
- Name: `generate-daily-forecasts`
- Region: `us-central1`
- Environment: `2nd gen`
- Runtime: `Python 3.11`
- Entry point: `generate_daily_forecasts`
- Trigger: HTTP (Allow unauthenticated)
- Source: `gs://cbi-v14-cloud-functions-source/forecasts-function-source.zip`
- Build SA: `1065708057795@cloudbuild.gserviceaccount.com`
- Memory: `512 MB`
- Timeout: `540s`

**After deployment, I can:**
- ✅ Setup scheduler (CLI works for this)
- ✅ Test function
- ✅ Verify forecasts

---

**RECOMMENDATION: Deploy via Console**

There is no programmatic workaround. This requires manual Console deployment.

