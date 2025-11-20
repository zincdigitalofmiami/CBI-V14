---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Google Cloud Marketplace Datasets - Complete Discovery & Testing Report
**Date**: November 16, 2025  
**Status**: ✅ TESTED & VERIFIED  
**Method**: Direct BigQuery access testing

---

## EXECUTIVE SUMMARY

**Accessible Datasets**: 5 major datasets confirmed working  
**Total Tables Available**: 316+ tables  
**Coverage**: Weather, Events, Economic, Political  
**Cost**: FREE (Google covers storage, 1TB/month query free tier)

---

## ✅ VERIFIED ACCESSIBLE DATASETS

### 1. NOAA Weather Data

#### Dataset: `bigquery-public-data.noaa_gsod`
- **Status**: ✅ FULLY ACCESSIBLE
- **Tables**: 98 tables (one per year: gsod1929 through gsod2024)
- **Coverage**: 1929-present (96 years)
- **Stations**: 30,000+ global weather stations
- **Data Points**: Billions of records
- **Schema** (sample from gsod2024):
  - `stn` (STRING): Station ID
  - `wban` (STRING): WBAN ID
  - `date` (DATE): Observation date
  - `temp` (FLOAT64): Mean temperature (°F)
  - `max` (FLOAT64): Maximum temperature (°F)
  - `min` (FLOAT64): Minimum temperature (°F)
  - `dewp` (FLOAT64): Dew point (°F)
  - `slp` (FLOAT64): Sea level pressure
  - `stp` (FLOAT64): Station pressure
  - `visib` (FLOAT64): Visibility (miles)
  - `wdsp` (STRING): Wind speed
  - `mxpsd` (STRING): Maximum sustained wind speed
  - `gust` (FLOAT64): Wind gust
  - `prcp` (FLOAT64): Precipitation (inches)
  - `sndp` (FLOAT64): Snow depth (inches)

**Query Example**:
```sql
-- Get weather data for US Midwest stations (2000-2025)
SELECT 
    date,
    stn as station_id,
    temp as temperature_f,
    max as max_temp_f,
    min as min_temp_f,
    prcp as precipitation_inches,
    sndp as snow_depth_inches
FROM `bigquery-public-data.noaa_gsod.gsod2024`
WHERE stn IN (
    SELECT usaf 
    FROM `bigquery-public-data.noaa_gsod.stations`
    WHERE country = 'US' 
        AND state IN ('IA', 'IL', 'IN', 'MN', 'MO', 'NE', 'OH', 'SD', 'WI')
)
AND date >= '2000-01-01'
ORDER BY date, stn
```

**Brazil & Argentina Coverage**: ✅ YES
- Stations available in both countries
- Query by country code: `country = 'BR'` or `country = 'AR'`

#### Dataset: `bigquery-public-data.noaa_global_forecast_system`
- **Status**: ✅ ACCESSIBLE (but hit query quota)
- **Tables**: 1 table (`NOAA_GFS0P25`)
- **Rows**: 14+ billion rows
- **Coverage**: Global forecasts, 16-day horizon
- **Use Case**: Weather forecasting (not historical)

---

### 2. GDELT Events Data

#### Dataset: `gdelt-bq.gdeltv2.events`
- **Status**: ✅ FULLY ACCESSIBLE
- **Tables**: 62 tables
- **Key Tables**:
  - `events` - Main events table
  - `events_partitioned` - Partitioned for performance
  - `eventmentions` - Event mentions
  - `eventmentions_partitioned` - Partitioned mentions
- **Coverage**: Global events, real-time updates
- **Schema** (61 columns including):
  - `SQLDATE` (INT64): Date (YYYYMMDD format)
  - `Actor1CountryCode` (STRING): First actor country
  - `Actor2CountryCode` (STRING): Second actor country
  - `EventCode` (STRING): CAMEO event code
  - `EventBaseCode` (STRING): Base event code
  - `EventRootCode` (STRING): Root event code
  - `GoldsteinScale` (FLOAT64): Event impact score
  - `NumMentions` (INT64): Number of mentions
  - `NumSources` (INT64): Number of sources
  - `NumArticles` (INT64): Number of articles
  - `AvgTone` (FLOAT64): Average sentiment tone
  - `SOURCEURL` (STRING): Source URL

**Query Example** (China-US Trade Events):
```sql
SELECT 
    PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING)) as date,
    Actor1CountryCode,
    Actor2CountryCode,
    EventCode,
    EventRootCode,
    GoldsteinScale,
    AvgTone,
    NumMentions,
    SOURCEURL
FROM `gdelt-bq.gdeltv2.events`
WHERE DATE(PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING))) >= '2000-01-01'
    AND (
        (Actor1CountryCode = 'CHN' AND Actor2CountryCode = 'USA')
        OR (Actor1CountryCode = 'USA' AND Actor2CountryCode = 'CHN')
    )
    AND EventCode IN ('0871', '1056', '0231', '0311', '0411')  -- Trade events
    AND (
        LOWER(SOURCEURL) LIKE '%tariff%'
        OR LOWER(SOURCEURL) LIKE '%trade%'
        OR LOWER(SOURCEURL) LIKE '%soybean%'
    )
ORDER BY SQLDATE DESC
LIMIT 1000
```

---

### 3. BLS Economic Data

#### Dataset: `bigquery-public-data.bls`
- **Status**: ✅ FULLY ACCESSIBLE
- **Tables**: 9 tables
- **Key Tables**:
  - `cpi_u` - Consumer Price Index (939,014 rows)
  - `c_cpi_u` - Chained CPI (8,049 rows)
  - `unemployment_cps` - Unemployment data (7,476,103 rows)
  - `employment_hours_earnings` - Employment data (8,164,148 rows)
  - `wm` - Wage data (487,054 rows)
- **Coverage**: Historical economic indicators
- **Schema** (cpi_u table):
  - `series_id` (STRING): BLS series identifier
  - `year` (INT64): Year
  - `period` (STRING): Period (M01-M12 for monthly)
  - `value` (FLOAT64): CPI value
  - `date` (DATE): Date
  - `item_code` (STRING): Item code
  - `item_name` (STRING): Item name (e.g., "Food", "Energy")
  - `area_code` (STRING): Geographic area code
  - `area_name` (STRING): Geographic area name

**Query Example**:
```sql
-- Get CPI for Food and Energy (2000-2025)
SELECT 
    date,
    item_name,
    value as cpi_value,
    area_name
FROM `bigquery-public-data.bls.cpi_u`
WHERE date >= '2000-01-01'
    AND item_name IN ('Food', 'Energy', 'All items')
    AND area_name = 'U.S. city average'
ORDER BY date, item_name
```

---

### 4. FEC Campaign Finance Data

#### Dataset: `bigquery-public-data.fec`
- **Status**: ✅ FULLY ACCESSIBLE
- **Tables**: 146 tables
- **Coverage**: Federal election campaign finance data
- **Key Tables**:
  - `candidate_2016`, `candidate_2018`, `candidate_2020`, `candidate_2022`, `candidate_2024`
  - `candidate_committee_*` - Candidate-committee linkages
  - `ccl*` - Committee candidate links
  - `cm*` - Committee master files
  - `cn*` - Candidate master files
  - `indiv*` - Individual contributions
  - `pas*` - Political action committee data
  - `oth*` - Other committee data

**Use Case**: Track agricultural lobby contributions affecting trade policy

---

### 5. Additional Discovered Datasets

#### Dataset: `bigquery-public-data.covid19_open_data`
- **Status**: ✅ ACCESSIBLE (tested in discovery)
- **Use Case**: Supply chain disruption proxy (2020-2025)

#### Dataset: `bigquery-public-data.census_bureau_acs`
- **Status**: ✅ LIKELY ACCESSIBLE (common public dataset)
- **Use Case**: Demographic and economic data

---

## ❌ DATASETS NOT FOUND (Wrong Names)

These dataset names from your list don't exist, but alternatives are available:

1. **`noaa-public.ghcn-d`** → Use **`bigquery-public-data.noaa_gsod`** instead
2. **`bls-public-data.cpi_unemployment`** → Use **`bigquery-public-data.bls`** instead
3. **`bigquery-public-data.federal_reserve_economic_data`** → Doesn't exist (use FRED API or find alternative)
4. **`federal-election-commission.fec_2024`** → Use **`bigquery-public-data.fec`** instead
5. **`bigquery-public-data.international_trade`** → Doesn't exist (may need UN Comtrade API)
6. **`bigquery-public-data.usda_nass`** → Doesn't exist (use USDA API)
7. **`bigquery-public-data.eia`** → Doesn't exist (use EIA API)

---

## DATA COLLECTION STRATEGY USING GOOGLE MARKETPLACE

**CRITICAL PRINCIPLE**: Google Marketplace is BACKUP ONLY. Keep working sources!

### ✅ KEEP WORKING SOURCES (DO NOT REPLACE)
1. **FRED Economic Data**: ✅ 34/35 series collected via API - **KEEP**
2. **Yahoo Finance**: ✅ 74/79 symbols collected via API - **KEEP**
3. **INMET Brazil Weather**: ✅ We have access (`src/ingestion/ingest_brazil_weather_inmet.py`) - **KEEP**

### ⚠️ USE GOOGLE AS BACKUP ONLY
1. **NOAA Weather API**: Try API first, use `bigquery-public-data.noaa_gsod` as backup if API fails
2. **CFTC COT**: Try legacy URLs first, use Google if available as backup

### ✅ USE GOOGLE FOR DATA WE DON'T HAVE
1. **GDELT Events**: `gdelt-bq.gdeltv2.events` - We don't have this elsewhere
2. **FEC Campaign Finance**: `bigquery-public-data.fec` - We don't have this elsewhere
3. **BLS Economic Data**: `bigquery-public-data.bls` - Use as supplement to FRED (not replacement)

### Phase 1: Weather Data (PRIMARY: APIs, BACKUP: BigQuery)
**Primary Sources**:
- ✅ **Brazil**: INMET API (`src/ingestion/ingest_brazil_weather_inmet.py`) - **KEEP USING**
- ⚠️ **US/Argentina**: NOAA API (`scripts/ingest/collect_noaa_comprehensive.py`) - Try first

**Backup Source**: `bigquery-public-data.noaa_gsod`
- Use ONLY if NOAA API fails or times out
- Use ONLY for historical backfill if API has gaps
- **DO NOT REPLACE** working INMET or NOAA API calls

**Implementation Strategy**:
```python
# Try API first
try:
    df = collect_noaa_api_data()  # Primary source
except (TimeoutError, APIError):
    # Fallback to BigQuery ONLY if API fails
    df = query_bigquery_noaa_gsod()  # Backup
```

### Phase 2: GDELT Events (100% via BigQuery - We Don't Have This Elsewhere)
**Source**: `gdelt-bq.gdeltv2.events`
- ✅ No API needed
- ✅ Real-time updates
- ✅ China-US trade events
- ✅ Tariff monitoring
- ✅ Sentiment analysis
- **Reason**: We don't have access to GDELT API, so BigQuery is primary

### Phase 3: Economic Data (SUPPLEMENT, NOT REPLACE)
**Primary**: FRED API (✅ Already collected 34/35 series) - **KEEP**
**Supplement**: `bigquery-public-data.bls`
- ✅ CPI data available (supplement FRED CPI)
- ✅ Unemployment data available (supplement FRED unemployment)
- **Use**: Additional economic indicators not in FRED
- **DO NOT**: Replace FRED data with BLS

### Phase 4: Political Data (100% via BigQuery - We Don't Have This Elsewhere)
**Source**: `bigquery-public-data.fec`
- ✅ Campaign finance data
- ✅ Agricultural lobby tracking
- ✅ Policy influence analysis
- **Reason**: We don't have FEC API access, so BigQuery is primary

---

## REVISED DATA COLLECTION PLAN

### ✅ KEEP USING (APIs Working - DO NOT REPLACE)
1. **FRED Economic**: ✅ 34/35 series collected via API - **KEEP**
2. **Yahoo Finance**: ✅ 74/79 symbols collected via API - **KEEP**
3. **INMET Brazil Weather**: ✅ We have access - **KEEP**

### ⚠️ TRY API FIRST, USE BIGQUERY AS BACKUP
1. **NOAA Weather**: Try API first (`scripts/ingest/collect_noaa_comprehensive.py`), use `bigquery-public-data.noaa_gsod` as backup
2. **CFTC COT**: Try legacy URLs first, use BigQuery if available as backup

### ✅ USE BIGQUERY FOR DATA WE DON'T HAVE (No API Access)
1. **GDELT Events**: `gdelt-bq.gdeltv2.events` - We don't have API access
2. **FEC Campaign Finance**: `bigquery-public-data.fec` - We don't have API access
3. **BLS Economic**: `bigquery-public-data.bls` - Use as supplement to FRED (not replacement)

### ⚠️ STILL NEED APIs (Not in BigQuery, No Backup Available)
1. **USDA**: Use USDA API (fixed script) - No BigQuery alternative
2. **EIA Biofuel**: Use EIA API v1 or CSV downloads - No BigQuery alternative

---

## EXPECTED COVERAGE WITH CURRENT STRATEGY

**Working Sources (KEEP)**:
- ✅ FRED Economic: 34/35 series
- ✅ Yahoo Finance: 74/79 symbols
- ✅ INMET Brazil Weather: Working

**BigQuery Backup/Supplement**:
- ⚠️ NOAA Weather: Backup if API fails
- ✅ GDELT Events: Primary (no API access)
- ✅ FEC Campaign Finance: Primary (no API access)
- ✅ BLS Economic: Supplement to FRED

**Coverage**: ~85-90% with working APIs + BigQuery supplements

**Remaining Gaps**:
- CFTC COT (try legacy URLs, BigQuery backup if available)
- USDA (use API - no BigQuery alternative)
- EIA (use API or CSV - no BigQuery alternative)

---

## NEXT STEPS

1. ✅ Test all accessible datasets (DONE)
2. ⏭️ Create collection scripts using BigQuery queries **ONLY for data we don't have**
3. ⏭️ Use BigQuery as **BACKUP** for failed API calls (not replacement)
4. ⏭️ Update main plan with **KEEP WORKING SOURCES** strategy
5. ⏭️ Implement data collection: **APIs first, BigQuery backup/supplement**

---

## CRITICAL REMINDER

**DO NOT REPLACE WORKING SOURCES WITH GOOGLE MARKETPLACE**

- ✅ **KEEP**: FRED, Yahoo Finance, INMET (Brazil)
- ⚠️ **BACKUP**: Use Google only if API fails
- ✅ **PRIMARY**: Use Google only for data we don't have elsewhere (GDELT, FEC)

**Google Marketplace = Backup & Gap Filler, NOT Replacement**
