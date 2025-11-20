---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Data Source Strategy: Keep Working Sources, Google as Backup

**Date**: November 16, 2025  
**Status**: ✅ ACTIVE POLICY  
**Principle**: **DO NOT REPLACE WORKING SOURCES WITH GOOGLE MARKETPLACE**

---

## CRITICAL PRINCIPLE

**Google Marketplace = Backup & Gap Filler, NOT Replacement**

If we have good, reliable data coming in without issues, **KEEP IT**.  
Only use Google Marketplace for:
1. **Backup** - When APIs fail or timeout
2. **Gaps** - Data we don't have access to elsewhere

---

## ✅ KEEP USING (APIs Working - DO NOT REPLACE)

### 1. FRED Economic Data
- **Source**: FRED API (`scripts/ingest/collect_fred_comprehensive.py`)
- **Status**: ✅ 34/35 series collected successfully
- **Action**: **KEEP USING API**
- **Google Alternative**: None (FRED not in BigQuery)

### 2. Yahoo Finance
- **Source**: Yahoo Finance API (`scripts/ingest/collect_yahoo_finance_comprehensive.py`)
- **Status**: ✅ 74/79 symbols collected successfully
- **Action**: **KEEP USING API**
- **Google Alternative**: None (Yahoo Finance not in BigQuery)

### 3. INMET Brazil Weather
- **Source**: INMET API (`src/ingestion/ingest_brazil_weather_inmet.py`)
- **Status**: ✅ We have access, script exists
- **Action**: **KEEP USING INMET API**
- **Google Alternative**: `bigquery-public-data.noaa_gsod` (backup only if INMET fails)

---

## ⚠️ TRY API FIRST, USE GOOGLE AS BACKUP

### 1. NOAA Weather (US/Argentina)
- **Primary**: NOAA API (`scripts/ingest/collect_noaa_comprehensive.py`)
- **Backup**: `bigquery-public-data.noaa_gsod`
- **Strategy**: 
  ```python
  try:
      df = collect_noaa_api_data()  # Try API first
  except (TimeoutError, APIError):
      df = query_bigquery_noaa_gsod()  # Fallback to BigQuery
  ```
- **Action**: Try API first, use BigQuery ONLY if API fails

### 2. CFTC COT Data
- **Primary**: Legacy CFTC URLs (from `archive/oct31_2025_cleanup/scripts_legacy/`)
- **Backup**: Check if available in BigQuery
- **Action**: Try legacy URLs first, use BigQuery if available as backup

---

## ✅ USE GOOGLE FOR DATA WE DON'T HAVE (No API Access)

### 1. GDELT Events
- **Source**: `gdelt-bq.gdeltv2.events`
- **Reason**: We don't have GDELT API access
- **Action**: **USE BIGQUERY AS PRIMARY** (no alternative)
- **Use Case**: China-US trade events, tariff monitoring, sentiment analysis

### 2. FEC Campaign Finance
- **Source**: `bigquery-public-data.fec`
- **Reason**: We don't have FEC API access
- **Action**: **USE BIGQUERY AS PRIMARY** (no alternative)
- **Use Case**: Agricultural lobby tracking, policy influence analysis

### 3. BLS Economic Data
- **Source**: `bigquery-public-data.bls`
- **Reason**: Supplement to FRED (not replacement)
- **Action**: **USE AS SUPPLEMENT** (FRED is primary)
- **Use Case**: Additional CPI/unemployment indicators not in FRED

---

## ⚠️ STILL NEED APIs (No BigQuery Alternative)

### 1. USDA Agricultural Data
- **Source**: USDA API (`scripts/ingest/collect_usda_comprehensive.py`)
- **Status**: Script fixed, needs testing
- **Action**: Use USDA API (no BigQuery alternative)

### 2. EIA Biofuel Data
- **Source**: EIA API v1 or CSV downloads
- **Status**: Endpoint changes, exploring alternatives
- **Action**: Use EIA API/CSV (no BigQuery alternative)

---

## DATA SOURCE DECISION TREE

```
Do we have working API access?
├─ YES → USE API (KEEP IT)
│   └─ Does API fail/timeout?
│       ├─ YES → Fallback to Google Marketplace (BACKUP)
│       └─ NO → Continue using API
│
└─ NO → Use Google Marketplace (PRIMARY)
    └─ Examples: GDELT, FEC (no API access)
```

---

## VERIFICATION

Run daily verification to ensure:
1. ✅ Working APIs are still working (FRED, Yahoo, INMET)
2. ✅ Google Marketplace datasets are accessible (for backup/supplement)
3. ⚠️ If API fails, verify Google backup is ready

**Script**: `scripts/ingest/verify_daily_updates.py`

---

## SUMMARY

| Data Source | Primary | Backup | Status |
|------------|---------|--------|--------|
| FRED Economic | ✅ API | N/A | KEEP |
| Yahoo Finance | ✅ API | N/A | KEEP |
| INMET Brazil | ✅ API | Google GSOD | KEEP |
| NOAA Weather | ⚠️ API | ✅ Google GSOD | Try API first |
| CFTC COT | ⚠️ Legacy URLs | Google (if available) | Try URLs first |
| GDELT Events | ✅ Google | N/A | No API access |
| FEC Finance | ✅ Google | N/A | No API access |
| BLS Economic | ✅ Google | N/A | Supplement to FRED |
| USDA | ⚠️ API | N/A | No Google alternative |
| EIA Biofuel | ⚠️ API/CSV | N/A | No Google alternative |

---

**Remember**: If it works, don't fix it. Google Marketplace is our safety net, not our primary source.

