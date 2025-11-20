---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Scrape Creator Data Flow - Reverse Engineering Audit
**Date:** November 5, 2025  
**Purpose:** Understand existing Scrape Creator integration before making changes

---

## 🔍 Data Flow Architecture

### Source Tables (Scrape Creator → BigQuery)
1. **`forecasting_data_warehouse.trump_policy_intelligence`**
   - Current: 380 rows, 49 distinct dates
   - Date range: Apr 3, 2025 → Nov 5, 2025
   - Sources: 10 distinct sources
   - Schema: `source`, `category`, `text`, `agricultural_impact`, `soybean_relevance`, `timestamp`, `priority`, `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`

2. **`forecasting_data_warehouse.social_sentiment`**
   - Schema: `platform`, `subreddit`, `title`, `score`, `comments`, `sentiment_score`, `timestamp`, `market_relevance`, `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`

3. **`forecasting_data_warehouse.news_intelligence`**
   - Schema: `published` (TIMESTAMP), `title`, `content`, `intelligence_score`, etc.

### Intermediate Processing Tables
1. **`models_v4.trump_policy_daily`** - Daily aggregations from `trump_policy_intelligence`
2. **`models_v4.social_sentiment_daily`** - Daily aggregations from `social_sentiment`
3. **`models_v4.news_intelligence_daily`** - Daily aggregations from `news_intelligence`

### Final Destination (Production Training Tables)
**`models_v4.production_training_data_1w/1m/3m/6m`** (290 features each)

**Scrape Creator-related columns in production tables:**
- `trump_policy_events` (INT64)
- `trump_policy_impact_avg` (FLOAT64)
- `trump_policy_impact_max` (FLOAT64)
- `trump_policy_7d` (FLOAT64)
- `trump_events_7d` (INT64)
- `trump_soybean_sentiment_7d` (FLOAT64)
- `trump_agricultural_impact_30d` (FLOAT64)
- `trump_soybean_relevance_30d` (FLOAT64)
- `days_since_trump_policy` (INT64)
- `trump_policy_intensity_14d` (FLOAT64)
- `social_sentiment_avg` (FLOAT64)
- `social_sentiment_volatility` (FLOAT64)
- `social_post_count` (INT64)
- `social_sentiment_7d` (FLOAT64)
- `social_volume_7d` (INT64)
- `social_sentiment_momentum_7d` (FLOAT64)
- `news_article_count` (INT64)
- `news_avg_score` (FLOAT64)
- `news_sentiment_avg` (FLOAT64)
- `news_intelligence_7d` (FLOAT64)
- `news_volume_7d` (INT64)
- `china_news_count` (INT64)
- `biofuel_news_count` (INT64)
- `tariff_news_count` (INT64)
- `weather_news_count` (INT64)
- Plus 20+ more sentiment/policy columns

---

## 📊 Existing Scrape Creator Scripts

### 1. `ingestion/ingest_scrapecreators_institutional.py`
- **Purpose:** Institutional intelligence (lobbying, congressional, analysts, China state media)
- **Targets:** Twitter handles for Cargill, ADM, Bunge, ASA, Congress, Goldman Sachs, JPMorgan, Xinhua, etc.
- **Output:** `staging.institutional_*` tables (NOT connected to production yet!)
- **Capability:** Custom Twitter/LinkedIn/Facebook scrapes via Scrape Creator API

### 2. `ingestion/backfill_trump_intelligence.py`
- **Purpose:** Historical Trump policy backfill
- **API:** Scrape Creators Truth Social API
- **Current:** Tries to fetch 2018-2020 (returns 404 - Truth Social didn't exist then)
- **Fix needed:** Change date range to 2022-2025 (Truth Social launch)

### 3. `ingestion/trump_truth_social_monitor.py`
- **Purpose:** Real-time Trump Truth Social monitoring
- **API:** Scrape Creators Truth Social API

### 4. `ingestion/ingest_social_intelligence_comprehensive.py`
- **Purpose:** Process scraped social media data
- **Output:** `staging.comprehensive_social_intelligence`
- **Capability:** Multi-platform (Twitter, Facebook, LinkedIn, YouTube, Reddit, TikTok)

---

## 🔗 Data Integration Flow (from SQL)

### Step 1: Source → Daily Aggregations
```sql
-- From COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql
CREATE TABLE models_v4.trump_policy_daily AS
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as trump_policy_events,
  AVG(agricultural_impact) as trump_policy_impact_avg,
  MAX(agricultural_impact) as trump_policy_impact_max,
  ...
FROM forecasting_data_warehouse.trump_policy_intelligence
GROUP BY DATE(timestamp)
```

### Step 2: Daily Aggregations → Production Training Tables
```sql
-- MERGE into production_training_data_* tables
MERGE INTO models_v4.training_dataset_super_enriched target
USING (
  SELECT * FROM models_v4.trump_policy_daily
  UNION ALL
  SELECT * FROM models_v4.social_sentiment_daily
  UNION ALL
  SELECT * FROM models_v4.news_intelligence_daily
) source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET ...
```

---

## 🎯 What Can Be Done Without Schema Changes

### ✅ Historical Backfill via Scrape Creator API

**Available via Scrape Creator API (key: <SCRAPECREATORS_API_KEY>):**

1. **Twitter Profiles** (via `ingest_scrapecreators_institutional.py`)
   - Any Twitter handle (companies, individuals, organizations)
   - Historical posts (if API supports)
   - Example: Cargill, ADM, Bunge, Goldman Sachs, JPMorgan, Xinhua News

2. **LinkedIn Profiles** (can be added to existing script)
   - Company pages
   - Individual profiles
   - Historical posts (if API supports)

3. **Facebook Pages** (can be added to existing script)
   - Company pages
   - Public profiles
   - Historical posts (if API supports)

4. **Truth Social** (via `backfill_trump_intelligence.py`)
   - Trump's Truth Social posts
   - Date range: 2022-2025 (Truth Social launch to present)
   - **FIX:** Change backfill script from 2018-2020 to 2022-2025

### ✅ Profile/Company Targets for Historical Backfill

**High-Value Targets:**
- **Agricultural Companies:** Cargill, ADM, Bunge, Louis Dreyfus, COFCO, Sinograin
- **Government Agencies:** USDA, EPA, USTR, ICE, GACC (China)
- **Financial Institutions:** Goldman Sachs, JPMorgan, Citi, Morgan Stanley
- **China State Media:** Xinhua News, People's Daily, Global Times
- **Policy Makers:** Trump, Biden, key Senators/Congress members
- **Trade Organizations:** ASA, NOPA, USSEC

---

## ⚠️ Critical Constraints

1. **DO NOT CHANGE SCHEMAS** - Production tables have fixed 290-column schema
2. **DO NOT CREATE NEW TABLES** - Use existing source tables
3. **DO NOT MODIFY PRODUCTION TABLES** - Only append to source tables
4. **USE EXISTING SCRAPERS** - Modify existing scripts, don't create new ones

---

## 📋 Action Plan (No Schema Changes)

### Step 1: Fix Trump Backfill Script
- Change date range from 2018-2020 to 2022-2025
- Run `backfill_trump_intelligence.py`
- Data flows automatically to `trump_policy_intelligence` → `trump_policy_daily` → production tables

### Step 2: Extend Institutional Intelligence
- Use `ingest_scrapecreators_institutional.py`
- Add more Twitter/LinkedIn/Facebook profiles
- Historical backfill if API supports
- Data flows to `staging.institutional_*` (need to check if connected to production)

### Step 3: Verify Data Flow
- Check if `staging.institutional_*` tables connect to production
- If not, check if `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql` needs update
- Run integration SQL to update production tables

---

## 🚨 Next Steps

1. ✅ **Audit complete** - Data flow understood
2. ⏳ **Fix Trump backfill date range** (2022-2025 instead of 2018-2020)
3. ⏳ **Check institutional intelligence connection** to production
4. ⏳ **Add more profiles** to institutional scraper (if needed)
5. ⏳ **Run backfills** and verify data flows to production

**Status:** Ready to proceed with historical backfill using existing scrapers






