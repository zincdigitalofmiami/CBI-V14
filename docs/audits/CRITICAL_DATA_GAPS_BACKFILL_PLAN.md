# Critical Data Gaps Backfill Plan
**Created:** November 12, 2025  
**Status:** Ready for Execution

## Overview

Three critical data gaps have been identified that require immediate backfill:

1. **CFTC COT**: Only 86 rows (need 2006-2025) — URGENT
2. **China Soybean Imports**: Only 22 rows (need 2017-2025) — URGENT  
3. **Baltic Dry Index**: Missing completely — HIGH

## Backfill Scripts Created

### 1. CFTC COT Historical Backfill
**Script:** `scripts/backfill_cftc_cot_historical.py`

- **Coverage:** 2006-2025 (19 years)
- **Method:** Year-by-year processing via CFTC API
- **Data Source:** CFTC Public Reporting API
  - Disaggregated endpoint (2023+): `https://publicreporting.cftc.gov/resource/jun7-fc8e.json`
  - Legacy endpoint (pre-2023): `https://publicreporting.cftc.gov/resource/6dca-aqww.json`
- **Target Table:** `forecasting_data_warehouse.cftc_cot`
- **Expected Rows:** ~988 rows (52 weeks/year × 19 years)
- **Rate Limiting:** 5 seconds between years

**Usage:**
```bash
python3 scripts/backfill_cftc_cot_historical.py [start_year] [end_year]
# Default: 2006-2025
```

### 2. China Soybean Imports Historical Backfill
**Script:** `scripts/backfill_china_imports_historical.py`

- **Coverage:** 2017-2025 (8+ years)
- **Method:** Month-by-month processing via UN Comtrade API
- **Data Source:** UN Comtrade API
  - Endpoint: `https://comtrade.un.org/api/get`
  - HS Code: 1201 (Soybeans)
  - Country: China (156)
  - Trade Flow: Imports (rg=1)
- **Target Table:** `forecasting_data_warehouse.economic_indicators`
- **Indicator:** `cn_soybean_imports_mmt` (Million Metric Tons)
- **Expected Rows:** ~96 rows (12 months/year × 8 years)
- **Rate Limiting:** 3 seconds between months
- **Deduplication:** Checks existing data before loading

**Usage:**
```bash
python3 scripts/backfill_china_imports_historical.py [start_year] [end_year]
# Default: 2017-2025
```

### 3. Baltic Dry Index Historical Backfill
**Script:** `scripts/backfill_baltic_dry_index_historical.py`

- **Coverage:** 2006-2025 (19 years)
- **Method:** 
  - Primary: Attempts real data sources (Trading Economics, Investing.com, FRED)
  - Fallback: Generates estimated values based on historical patterns
- **Data Sources:**
  - Trading Economics API (requires subscription)
  - Investing.com (web scraping)
  - FRED Economic Data (if available)
  - Estimated values (low confidence: 0.50)
- **Target Table:** `forecasting_data_warehouse.freight_logistics`
- **Expected Rows:** ~6,935 rows (365 days/year × 19 years)
- **Confidence:** 
  - Real data: 0.90
  - Estimated data: 0.50 (marked as `ESTIMATED_HISTORICAL`)

**Usage:**
```bash
python3 scripts/backfill_baltic_dry_index_historical.py [start_year] [end_year] [use_estimates]
# Default: 2006-2025 true
# Set use_estimates=false to skip estimated data
```

### 4. Unified Backfill Runner
**Script:** `scripts/backfill_critical_data_gaps.py`

- **Purpose:** Runs all three backfill scripts sequentially
- **Features:**
  - Sequential execution with progress logging
  - Error handling and timeout protection (1 hour per script)
  - JSON results output
  - Summary report
- **Output:** `Logs/backfill_results.json`

**Usage:**
```bash
python3 scripts/backfill_critical_data_gaps.py
```

## Execution Plan

### Step 1: Verify Prerequisites
```bash
# Check Google Cloud credentials
gcloud auth application-default login

# Verify API keys in .env.cron
cat .env.cron | grep -E "FRED|NOAA|SCRAPECREATORS"

# Check BigQuery access
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.cftc_cot\`"
```

### Step 2: Run Individual Backfills (Recommended)
Run each backfill separately to monitor progress:

```bash
# 1. CFTC COT (estimated time: 10-15 minutes)
python3 scripts/backfill_cftc_cot_historical.py 2006 2025

# 2. China Imports (estimated time: 5-10 minutes)
python3 scripts/backfill_china_imports_historical.py 2017 2025

# 3. Baltic Dry Index (estimated time: 15-20 minutes)
python3 scripts/backfill_baltic_dry_index_historical.py 2006 2025 true
```

### Step 3: Run Unified Backfill (Alternative)
Run all three at once:

```bash
python3 scripts/backfill_critical_data_gaps.py
```

### Step 4: Verify Results
```bash
# Check CFTC COT
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as total_rows,
  MIN(report_date) as earliest_date,
  MAX(report_date) as latest_date
FROM \`cbi-v14.forecasting_data_warehouse.cftc_cot\`
"

# Check China Imports
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as total_rows,
  MIN(time) as earliest_date,
  MAX(time) as latest_date
FROM \`cbi-v14.forecasting_data_warehouse.economic_indicators\`
WHERE indicator = 'cn_soybean_imports_mmt'
"

# Check Baltic Dry Index
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as total_rows,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNTIF(source_name = 'ESTIMATED_HISTORICAL') as estimated_rows
FROM \`cbi-v14.forecasting_data_warehouse.freight_logistics\`
"
```

## Expected Results

| Data Source | Current Rows | Target Rows | Gap | Status |
|------------|--------------|-------------|-----|--------|
| CFTC COT | 86 | ~988 | 902 rows | URGENT |
| China Imports | 22 | ~96 | 74 rows | URGENT |
| Baltic Dry Index | 0 | ~6,935 | 6,935 rows | HIGH |

## Notes & Warnings

### CFTC COT
- ✅ Real API data (high confidence: 0.95)
- ⚠️  API may have rate limits
- ⚠️  Some historical years may have incomplete data

### China Imports
- ✅ Real UN Comtrade data (high confidence: 0.85)
- ⚠️  UN Comtrade has strict rate limits (3 seconds between requests)
- ⚠️  Some months may be missing in source data

### Baltic Dry Index
- ⚠️  **CRITICAL:** Real data sources may not be available
- ⚠️  Fallback uses estimated values (low confidence: 0.50)
- ⚠️  Estimated values should be replaced with real data when available
- 💡 Consider subscribing to Trading Economics API for real historical BDI data

## Troubleshooting

### CFTC API Errors
- Check network connectivity
- Verify API endpoints are accessible
- Check for API rate limits (wait and retry)

### UN Comtrade Errors
- Verify rate limiting (3+ seconds between requests)
- Check API availability (may be down for maintenance)
- Verify HS code 1201 and country code 156

### Baltic Dry Index
- If real data unavailable, script will use estimates
- Check logs for source availability
- Consider manual data entry from Baltic Exchange

## Next Steps

1. **Execute backfills** using scripts above
2. **Verify data quality** using verification queries
3. **Update training datasets** to include new historical data
4. **Retrain models** with expanded historical coverage
5. **Monitor ongoing ingestion** via cron jobs

## Related Files

- `src/ingestion/ingest_cftc_positioning_REAL.py` - CFTC ingestion script
- `src/ingestion/ingest_china_imports_uncomtrade.py` - China imports ingestion
- `src/ingestion/ingest_baltic_dry_index.py` - Baltic Dry Index ingestion
- `scripts/crontab_setup.sh` - Cron job setup (includes ongoing ingestion)

