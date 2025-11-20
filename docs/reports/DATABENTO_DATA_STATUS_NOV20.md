# DataBento Data Status Report
**Date**: November 20, 2025  
**Time**: 3:40 AM CST

## Executive Summary

✅ **Good news**: We already have substantial DataBento data from November 18 downloads
🔄 **In Progress**: 35 new batch jobs submitted today (6 done, 29 processing)
⚠️ **Key Gap**: ZL 1-minute data still missing but jobs are submitted

## What We Already Have

### MES (Micro E-mini S&P 500)
- **Coverage**: 2019-04-14 to 2025-11-16
- **Timeframes**: 1-minute, 1-hour, daily
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_mes/`
- **Batch Jobs**: 
  - GLBX-20251118-FEFDCP5HXU
  - GLBX-20251118-H3DTWEWHUN
  - GLBX-20251118-R6DHL7G583
- **Files**: 209 JSON files

### ZL (Soybean Oil)
- **Coverage**: 2010-06-06 to 2025-11-18
- **Timeframes**: ✅ 1-hour, ✅ daily, ❌ 1-minute (missing)
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/`
- **Batch Jobs**:
  - GLBX-20251118-6KKCTK5KY3
  - GLBX-20251118-FRGDM3B7UG
  - GLBX-20251118-TAAH7VN45V

### Forex
- **Coverage**: Various dates
- **Files**: 
  - `6a_daily_2010-06-06_2025-11-20.parquet`
  - Multiple currency pairs
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_forex/`

### VIX
- **Coverage**: Daily OPRA data
- **Files**: `vix_daily_opra.parquet`
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_vix/`

## New Jobs Submitted (November 20)

### Priority 1: Soy Complex 1-Minute Data
| Symbol | Schema | Job ID | Status |
|--------|--------|--------|--------|
| ZL | ohlcv-1m | GLBX-20251120-CQRNQQM89S | Processing |
| ZS | ohlcv-1m | GLBX-20251120-VEA67JYDQG | Processing |
| ZM | ohlcv-1m | GLBX-20251120-6E4MPH5KHJ | Processing |

### All Submitted Jobs
- **Total**: 35 jobs
- **Completed**: 6 jobs ✅
- **Processing**: 29 jobs ⏳
- **Symbols Covered**: 26 (ZL, ZS, ZM, ES, CL, HO, NG, RB, ZC, ZW, NQ, MNQ, RTY, M2K, GC, SI, HG, BZ, QM, PA, PL, ZR, ZO, LE, GF, HE)

## Why ZL 1-Minute Failed Previously

The ZL 1-minute download failed multiple times due to API errors:
1. Wrong API method (`timeseries` vs `batch`)
2. Invalid parameters (`packaging="zip"`)
3. Wrong split duration (`"1M"` vs `"month"`)
4. Incorrect symbology (`"ZL"` vs `"ZL.FUT"`)

All issues have been fixed in the current scripts.

## Data We DON'T Need to Download Again

✅ **MES**: Complete (all timeframes 2019-2025)
✅ **ZL Daily**: Complete (2010-2025)
✅ **ZL Hourly**: Complete (2010-2025)
✅ **Forex**: Have recent data
✅ **VIX**: Have OPRA data

## Critical Gaps Being Filled

1. **ZL 1-minute**: Essential for microstructure features
2. **ZS/ZM 1-minute**: Soy complex correlation
3. **ES daily**: Main equity index
4. **Energy complex daily**: CL, HO, NG, RB
5. **Grains daily**: ZC, ZW
6. **Other indices**: NQ, MNQ, RTY, M2K
7. **Metals**: GC, SI, HG, PA, PL

## Continuous Contracts

All downloads use **parent symbology** (`stype_in="parent"`) with `.FUT` suffix:
- Creates continuous front-month contracts
- Automatic roll handling by DataBento
- No calendar spreads (excluded by design)

## Next Steps

### Immediate (Within 1 Hour)
1. **Monitor Jobs**: Check https://databento.com/portal/batch/jobs
2. **Download Ready Jobs**: 
   ```bash
   python3 scripts/ingest/check_databento_jobs.py
   ```

### When Downloads Complete
1. **Extract Files**: Unzip to appropriate directories
2. **Process ZL 1-minute**: 
   ```bash
   python3 scripts/ingest/aggregate_zl_intraday.py
   ```
3. **Load to BigQuery**:
   ```bash
   python3 scripts/ingest/load_databento_to_bigquery.py
   ```

## Storage Estimates

- **Already Have**: ~2-3 GB (MES, ZL hourly/daily, forex, VIX)
- **New Downloads**: ~8-10 GB (all symbols, focus on 1-minute data)
- **Total After Complete**: ~12-13 GB

## Cost

- **Historical Data**: $0 (included in CME MDP 3.0 plan)
- **API Calls**: Within plan limits
- **No Extra Charges**: Standard historical backfill covered

## Recommendations

1. ✅ **Don't Re-download**: MES data, ZL hourly/daily
2. ⏳ **Wait for Processing**: 29 jobs still in queue
3. 📥 **Priority Download**: ZL 1-minute when ready
4. 🔄 **Automate Monitoring**: Set up cron job for checking job status

## Conclusion

We have most of the critical data already (MES complete, ZL hourly/daily complete). The main gap is **ZL 1-minute data**, which is now submitted and processing. Once these jobs complete, we'll have comprehensive historical coverage for all 26 symbols needed for training.







