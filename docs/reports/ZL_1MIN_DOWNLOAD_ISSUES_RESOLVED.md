# ZL 1-Minute Download Issues - Root Cause Analysis
**Date**: November 20, 2025  
**Status**: ✅ RESOLVED

## Executive Summary
Multiple attempts to download ZL 1-minute data from DataBento failed due to incorrect API usage in the download scripts. All issues have been identified and fixed.

## Root Cause Analysis

### Issue 1: Wrong API Endpoint
**Problem**: Scripts used `client.timeseries.submit_job()` which doesn't exist
**Fix**: Changed to `client.batch.submit_job()` for batch downloads
**Reason**: DataBento's timeseries API is for small, immediate data requests. Large historical downloads require the batch API.

### Issue 2: Invalid Parameter
**Problem**: Scripts included `packaging="zip"` parameter
**Fix**: Removed this parameter entirely
**Reason**: The batch API doesn't support a `packaging` parameter; it automatically packages downloads.

### Issue 3: Incorrect Split Duration
**Problem**: Scripts used `split_duration="1M"` or `"1d"`
**Fix**: Changed to `split_duration="month"` for 1-minute data, `"day"` for daily data
**Reason**: DataBento only accepts specific values: ['day', 'week', 'month', 'none']

### Issue 4: Wrong Symbology Format
**Problem**: Scripts used `symbols=["ZL"]` with `stype_in="continuous"` or `stype_in="parent"`
**Fix**: Changed to `symbols=["ZL.FUT"]` with `stype_in="parent"`
**Reason**: Parent symbology requires the `.FUT` suffix for futures contracts

## Scripts Fixed

### 1. `download_zl_1min_databento.py`
- ✅ Updated to use batch API
- ✅ Fixed all parameters
- ✅ Added proper parent symbology

### 2. `download_ALL_databento_historical.py`
- ✅ Fixed for all 26 symbols
- ✅ Includes ZL 1-minute in Tier 1 priority
- ✅ Currently running and submitting jobs successfully

## Why Previous Attempts Failed

Each time the ZL 1-minute download was attempted, it would fail with one of these errors:
1. `AttributeError: 'TimeseriesHttpAPI' object has no attribute 'submit_job'`
2. `TypeError: BatchHttpAPI.submit_job() got an unexpected keyword argument 'packaging'`
3. `ValueError: The split_duration was not a valid value of SplitDuration`
4. `400 symbology_invalid_symbol: Invalid format for parent symbol 'ZL'`

These cascading errors prevented the job from ever being submitted successfully.

## Current Status

✅ **FIXED**: All download scripts now use the correct API parameters
🔄 **IN PROGRESS**: `download_ALL_databento_historical.py` is actively submitting batch jobs
📦 **INCLUDES**: ZL 1-minute data as Tier 1 priority (will be among first downloads)

## Estimated Timeline

1. **Job Submission**: ~5-10 minutes (currently running)
2. **DataBento Processing**: 15-60 minutes (for batch job completion)
3. **Download Time**: ~30 minutes (8-10 GB total)
4. **ZL 1-minute Availability**: Within 2 hours from now

## Verification Steps

Once downloads complete:

```bash
# 1. Check for ZL 1-minute files
ls -la /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/raw/databento_zl_1min/

# 2. Count the data files
find /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/raw/databento_zl_1min/ -name "*.json" | wc -l

# 3. Verify date coverage (should be 2010-06-06 to present)
ls /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/raw/databento_zl_1min/ | head -5
ls /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/raw/databento_zl_1min/ | tail -5
```

## Next Steps

1. **Monitor** batch job completion at https://databento.com/portal/batch/jobs
2. **Download** completed files using:
   ```bash
   python3 scripts/ingest/check_databento_jobs.py
   ```
3. **Process** the data:
   ```bash
   python3 scripts/ingest/aggregate_zl_intraday.py
   ```
4. **Load to BigQuery** for analysis and feature generation

## Lessons Learned

1. Always check API documentation for correct method names and parameters
2. Test with small date ranges first before submitting large batch jobs
3. DataBento's batch API has strict parameter requirements that differ from their streaming API
4. Parent symbology requires specific formatting (`.FUT`, `.OPT`, `.SPOT` suffixes)

## Contact

For DataBento API issues:
- Documentation: https://databento.com/docs/api
- Support: support@databento.com
- Portal: https://databento.com/portal/batch/jobs







