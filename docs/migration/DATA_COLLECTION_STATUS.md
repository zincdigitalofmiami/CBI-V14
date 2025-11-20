---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Data Collection Status Report
**Date:** November 17, 2025  
**Status:** Partial Collection Complete

---

## ✅ COMPLETED DATA SOURCES

### Core Data (Phase 1)
1. **Yahoo Finance (ZL=F)** ✅
   - Status: Complete
   - Files: `staging/yahoo_historical_all_symbols.parquet`
   - Rows: 13,730 (includes ZL=F, CL, CPO, PALM_COMPOSITE)

2. **FRED Economic Data** ✅
   - Status: Complete (52/53 series)
   - Files: `staging/fred_macro_expanded.parquet`
   - Rows: 2,148 × 53 columns
   - Date range: 2020-2025
   - Note: 1 series (`NAPMPI`) removed (doesn't exist)

3. **Alpha Vantage** 🔄 IN PROGRESS
   - Status: Collection running in background
   - Script: `scripts/ingest/collect_alpha_vantage_comprehensive.py`
   - Includes: Technicals, commodities, forex, intraday, sentiment
   - Log: `/tmp/alpha_vantage_full_collection.log`

4. **Palm Oil Historical** ✅
   - Status: Historical data copied and transformed
   - Files: `raw/barchart/palm_oil_historical.parquet`
   - Rows: 1,340
   - Format: `barchart_palm_*` prefixed columns
   - Note: Daily scraping script needs to be created

### Supporting Data (Phase 2)
5. **Weather Data** ✅
   - Status: Complete
   - Files: `staging/weather_granular_daily.parquet`
   - Format: Granular wide format with region-specific prefixes

6. **CFTC COT Data** ✅
   - Status: Complete (2020-2024)
   - Files: `raw/cftc/*.parquet`
   - Rows: 4,176
   - Note: Historical data (2006-2019) needs backfill

7. **USDA Reports** ✅
   - Status: Partial (WASDE complete, exports pending)
   - Files: `raw/usda/*.parquet`
   - WASDE: 3,642 rows (2020-2025 annual)
   - Export Sales: Failed (API issues)

8. **EIA Energy Data** ✅
   - Status: Complete
   - Files: `staging/eia_energy_granular.parquet`
   - Format: Granular wide format with `eia_*` prefixes

---

## ⚠️ REQUIRES MANUAL INTERVENTION

### EPA RIN Prices
- **Status:** Script exists but URLs return 404
- **Script:** `scripts/ingest/collect_epa_rin_prices.py`
- **Issue:** EPA EMTS dashboard CSV export URLs are not directly accessible
- **Options:**
  1. Manual download from EPA EMTS dashboard
  2. Alternative source (OPIS, Argus - paywalled)
  3. EPA API access (if available)
- **Action Required:** Manual download or API access setup

### World Bank Pink Sheet
- **Status:** Script exists but URLs return 404
- **Script:** `scripts/ingest/collect_worldbank_pinksheet.py`
- **Issue:** World Bank Pink Sheet XLSX URLs are outdated
- **Options:**
  1. Manual download from World Bank commodity markets page
  2. Save to: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/wb_pinksheet/CMO-Historical-Data-Monthly.xlsx`
  3. Re-run script after manual download
- **Action Required:** Manual download

### USDA FAS Export Sales
- **Status:** Script exists but scraping fails
- **Script:** `scripts/ingest/collect_usda_fas_esr.py`
- **Issue:** USDA FAS ESR pages show aggregate data, not country-specific. HTML table parsing fails.
- **Options:**
  1. USDA FAS ESR query interface (requires parameters)
  2. MyMarketNews API (requires authentication)
  3. Use aggregate data as proxy
- **Action Required:** API authentication or different scraping approach

---

## ✅ NEWLY CREATED COLLECTION SCRIPTS

### Volatility & VIX ✅
- **Status:** Script created (`scripts/ingest/collect_volatility_intraday.py`)
- **Features:**
  - VIX from Yahoo Finance (^VIX) + FRED (VIXCLS) for cross-validation
  - Realized volatility for ZL, ES (SPY proxy), Palm (20d, 30d, 60d, 90d windows)
  - Volatility regime classification (low/medium/high/extreme)
  - Percentile ranks (30d, 90d)
- **Prefix:** `vol_*`
- **Status:** Ready for execution

### Policy & Trump Intelligence ✅
- **Status:** Script created (`scripts/ingest/collect_policy_trump.py`)
- **Features:**
  - Truth Social posts from Trump + key accounts (via ScrapeCreators API)
  - Policy feed scraping (USDA announcements, trade news)
  - Sentiment classification (bullish/bearish/neutral for ZL)
  - Policy category tagging (trade, biofuel, agriculture, energy)
- **Prefix:** `policy_trump_*`
- **Status:** Ready for execution (requires ScrapeCreators API key)

### Palm Oil Daily Scraping ✅
- **Status:** Script created (`scripts/ingest/collect_palm_barchart.py`)
- **Features:**
  - Barchart scraping (FCPO futures) - primary source
  - Yahoo Finance fallback (CPO=F, FCPO=F)
  - 20-day realized volatility calculation
  - Merges with historical data automatically
- **Historical:** `raw/barchart/palm_oil_historical.parquet` (1,340 rows)
- **Status:** Ready for daily execution

---

## 📊 COLLECTION SUMMARY

| Source | Status | Rows | Date Range | Notes |
|--------|--------|------|------------|-------|
| Yahoo (ZL=F) | ✅ Complete | 13,730 | 2000-2025 | Includes CL, CPO, PALM_COMPOSITE |
| FRED | ✅ Complete | 2,148 | 2020-2025 | 52/53 series (98.1% success) |
| Alpha Vantage | 🔄 In Progress | - | - | Collection running |
| Palm Historical | ✅ Complete | 1,340 | Historical | Daily scraping script needed |
| Weather | ✅ Complete | - | - | Granular wide format |
| CFTC | ✅ Complete | 4,176 | 2020-2024 | Historical backfill needed |
| USDA WASDE | ✅ Complete | 3,642 | 2020-2025 | Export sales pending |
| EIA | ✅ Complete | - | - | Granular wide format |
| EPA RIN | ⚠️ Manual | - | - | URLs 404, needs manual download |
| World Bank | ⚠️ Manual | - | - | URLs 404, needs manual download |
| USDA FAS | ⚠️ Manual | - | - | Scraping fails, needs API |
| Volatility/VIX | ✅ Script Ready | - | - | `collect_volatility_intraday.py` created |
| Policy/Trump | ✅ Script Ready | - | - | `collect_policy_trump.py` created (needs API key) |
| Palm Daily | ✅ Script Ready | 1,340 | 2020-2025 | `collect_palm_barchart.py` created |

---

## 🎯 NEXT STEPS

1. **Wait for Alpha Vantage collection to complete** (currently running in background)
2. **Execute newly created scripts:**
   - `collect_volatility_intraday.py` - Run to collect VIX + realized vol
   - `collect_policy_trump.py` - Run to collect Truth Social + policy feeds (requires ScrapeCreators API key)
   - `collect_palm_barchart.py` - Run daily for palm futures updates
3. **Wire through staging → join spec → backfill:**
   - Update `scripts/staging/create_staging_files.py` to process volatility, policy, palm data
   - Add join steps to `registry/join_spec.yaml` for new sources
   - Backfill BigQuery tables once Alpha Vantage completes
4. **Manual interventions (non-blocking):**
   - Download EPA RIN prices manually or set up API access
   - Download World Bank Pink Sheet manually
   - Set up USDA FAS API authentication or fix scraping
5. **Backfill historical data:**
   - CFTC: 2006-2019
   - Alpha Vantage: Full 25-year history (if available)
   - Volatility: Historical VIX + realized vol (2000-2025)

---

**Last Updated:** November 17, 2025

