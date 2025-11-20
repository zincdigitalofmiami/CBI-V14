---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# DataBento Connection Fix - Status
**Date:** November 20, 2025  
**Status:** ⚠️ Authentication Issue Detected

---

## Current Status

### ✅ What's Working
1. **API Key Retrieval:** API key is successfully found in macOS keychain
   - Location: `databento/databento_api_key`
   - Key format: `db-cSwxrJx...` (32 characters)
   - Key length: Valid

2. **Client Initialization:** DataBento Historical client initializes successfully
   - Gateway: `https://hist.databento.com`
   - Client object created without errors

### ❌ Current Issue
**Authentication Failure:** 401 `auth_authentication_failed`
- Error occurs when calling `client.metadata.list_datasets()`
- API key is found but authentication fails
- Possible causes:
  1. API key expired or deactivated
  2. API key doesn't have access to Historical API
  3. API key format issue (though format looks correct)
  4. Account subscription issue

---

## Fix Steps

### Step 1: Verify API Key Status
1. Go to: https://databento.com/portal/api-keys
2. Check if the key `db-cSwxrJx...` is:
   - ✅ Active (not deactivated)
   - ✅ Has Historical API access enabled
   - ✅ Not expired
   - ✅ Associated with correct account/team

### Step 2: Test with Fresh Key
If key is invalid:
```bash
# Generate new API key in portal
# Then update keychain:
security add-generic-password -a databento -s databento_api_key -w 'NEW_KEY_HERE' -U
```

### Step 3: Test Connection
```bash
python3 scripts/features/calculate_iv30_from_options.py
# Or test directly:
python3 -c "
import databento as db
import subprocess
api_key = subprocess.run(['security', 'find-generic-password', '-w', '-a', 'databento', '-s', 'databento_api_key'], capture_output=True, text=True).stdout.strip()
client = db.Historical(api_key)
datasets = list(client.metadata.list_datasets())
print(f'✅ Connected! Available datasets: {datasets}')
"
```

### Step 4: Check Subscription
Verify subscription includes:
- ✅ GLBX.MDP3 dataset access
- ✅ Historical API access
- ✅ Options data access (if separate subscription needed)

---

## Implementation Status

### ✅ Completed
1. **Connection Code:** Fixed API key retrieval with multiple fallbacks
2. **IV30 Calculation:** Implemented with:
   - Cubic spline interpolation (as recommended)
   - Open interest weighting
   - Bid-ask tightness weighting
   - Quality guardrails (spread, staleness, strike coverage)
3. **Options Data Fetching:** Multiple schema attempts (ohlcv-1d, mbo, definition)
4. **Error Handling:** Comprehensive logging and diagnostics

### ⏳ Pending
1. **Connection Test:** Need valid API key to test
2. **Options Schema Verification:** Need to confirm correct schema for GLBX options
3. **Expiry Parsing:** May need adjustment based on actual symbol format

---

## Next Steps

1. **Immediate:** Verify API key status in portal
2. **If Key Invalid:** Generate new key and update keychain
3. **Test Connection:** Run test script to confirm authentication
4. **Verify Options Access:** Check if subscription includes options data
5. **Test IV30 Calculation:** Run on recent date once connection works

---

## Code Location

- **Main Script:** `scripts/features/calculate_iv30_from_options.py`
- **Daily Scheduler:** `scripts/features/daily_iv30_calculation.py`
- **Documentation:** `docs/features/IV30_CALCULATION_METHODOLOGY.md`

---

**Action Required:** Check API key status in Databento portal and update if needed.
