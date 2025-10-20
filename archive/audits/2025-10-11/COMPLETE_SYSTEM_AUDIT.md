# CBI-V14 Complete System Audit
**Date:** 2025-10-11  
**Status:** READ-ONLY FORENSIC REVIEW

---

## Executive Summary

**CRITICAL FINDINGS:**
1. **NO PRODUCTION SCRAPERS EXIST** - Despite claims, there are zero Yahoo/TradingEconomics/news scrapers deployed
2. **CRON JOBS ARE RUNNING** but collecting limited data (Yahoo prices, FRED, GDELT only)
3. **SOCIAL INTELLIGENCE BROKEN** - Facebook/LinkedIn scraper collecting 0 records
4. **RAW & STAGING DATASETS EMPTY** - No news/article ingestion infrastructure in place
5. **NAMING VIOLATIONS PERSIST** - Legacy views still exist in `forecasting_data_warehouse`
6. **MISSING CRITICAL DATA** - No CME, EIA, CONAB, USDA exports, EPA, or palm oil MPOB data

---

## 1. BigQuery Datasets & Tables

### 1.1 Dataset Inventory
```
✅ bkp                          (3 backup tables from 2025-10-10)
✅ curated                      (5 facade views)
✅ deprecated                   (1 legacy view)
✅ forecasting_data_warehouse   (24 tables, 12 views - LEGACY)
✅ models                        (EMPTY)
✅ raw                           (EMPTY - NO INGESTION)
✅ staging                       (1 table: market_prices only)
```

### 1.2 Tables in `forecasting_data_warehouse` (Main Warehouse)

| Table | Rows | Size (MB) | Last Modified | Status |
|-------|------|-----------|---------------|--------|
| weather_data | 9,505 | 1.15 | 2025-10-04 | ✅ Active (NOAA/INMET) |
| economic_indicators | 6,534 | 0.62 | 2025-10-02 | ⚠️ Needs rebuild (FRED only) |
| news_intelligence | 333 | 0.17 | 2025-10-04 | ⚠️ GDELT only, missing metadata |
| volatility_data | 780 | 0.10 | 2025-10-04 | ❌ Placeholder data, needs replacement |
| soybean_oil_prices | 525 | 0.06 | 2025-10-06 | ❌ Yahoo source, unreliable |
| soybean_prices | 524 | 0.06 | 2025-10-06 | ❌ Yahoo source |
| soybean_meal_prices | 524 | 0.06 | 2025-10-06 | ❌ Yahoo source |
| corn_prices | 524 | 0.06 | 2025-10-06 | ❌ Yahoo source |
| cotton_prices | 524 | 0.06 | 2025-10-06 | ❌ Yahoo source |
| cocoa_prices | 446 | 0.06 | 2025-10-06 | ❌ Yahoo source |
| palm_oil_prices | 421 | 0.02 | 2025-10-07 | ❌ Yahoo source |
| ice_trump_intelligence | 182 | 0.05 | 2025-10-04 | ✅ Active (ScrapeCreators) |
| treasury_prices | 136 | 0.02 | 2025-10-06 | ⚠️ Needs validation |
| social_sentiment | 0 | 0 | 2025-10-04 | ❌ BROKEN - collecting 0 records |

### 1.3 Views in `forecasting_data_warehouse` (LEGACY - VIOLATE NAMING)

**These should NOT exist in the legacy dataset:**
- `vw_brazil_precip_daily`
- `vw_brazil_weather_summary`
- `vw_dashboard_brazil_weather`
- `vw_dashboard_trump_intel`
- `vw_fed_rates_realtime`
- `vw_ice_trump_daily`
- `vw_multi_source_intelligence_summary`
- `vw_news_intel_daily`
- `vw_treasury_daily`
- `vw_trump_effect_breakdown`
- `vw_trump_effect_categories`
- `vw_trump_intelligence_dashboard`
- `soy_oil_features` (not even prefixed with vw_!)

**ACTION:** All views should be in `curated` dataset with proper `vw_` naming.

### 1.4 Curated Facade Views (CORRECT LOCATION)

✅ `vw_economic_daily` → queries `forecasting_data_warehouse.economic_indicators`  
✅ `vw_social_intelligence` → queries `forecasting_data_warehouse.social_sentiment`  
✅ `vw_volatility_daily` → queries `forecasting_data_warehouse.volatility_data`  
✅ `vw_weather_daily` → queries `forecasting_data_warehouse.weather_data`  
✅ `vw_zl_features_daily` → queries `forecasting_data_warehouse.soybean_oil_prices`

### 1.5 Staging Tables

**Only 1 table exists:**
- `staging.market_prices` (empty, created for TradingEconomics ingestion that never ran)

**MISSING:**
- `staging.news_articles_raw`
- `staging.news_articles_normalized`
- `staging.social_intel_events`
- `staging.cache_ingestion_ledger`
- `staging.commodity_forecasts`
- `staging.usda_exports`
- `staging.conab_crops`
- `staging.epa_biofuels`

### 1.6 Raw Dataset

**COMPLETELY EMPTY** - No ingestion infrastructure deployed.

---

## 2. Ingestion Code Review

### 2.1 Existing Python Scripts (31 files)

| Script | Purpose | Status |
|--------|---------|--------|
| `multi_source_collector.py` | Yahoo prices + FRED + GDELT | ✅ WORKING (cron: 9,11,13,15 weekdays) |
| `gdelt_china_intelligence.py` | GDELT China news | ✅ WORKING (cron: every 6hr) |
| `social_intelligence.py` | Facebook/LinkedIn scraping | ❌ BROKEN (0 records collected) |
| `trump_truth_social_monitor.py` | Trump posts | ✅ WORKING (cron: every 4hr) |
| `ingest_weather_noaa.py` | US weather | ✅ WORKING (cron: 6am daily) |
| `ingest_brazil_weather_inmet.py` | Brazil weather | ✅ WORKING (cron: 7am daily) |
| `ingest_market_prices.py` | TradingEconomics/Polygon | ❌ NEVER RAN (TE requires paid plan) |
| `ingest_zl_futures.py` | Polygon ZL | ❌ NOT SCHEDULED |
| `ingest_volatility.py` | VIX data | ❌ NOT SCHEDULED |
| `economic_intelligence.py` | FRED collector | ⚠️ Partial (used by multi_source) |
| `ice_trump_intelligence.py` | ICE + Trump correlation | ⚠️ Unknown schedule |

### 2.2 Missing Scrapers (NOT BUILT)

**These do NOT exist:**
1. **Yahoo Finance news scraper** (tariffs, economic news, crude, inflation, calendar)
2. **TradingEconomics news scraper** (markets, economy, inflation, commodities)
3. **Reddit search scraper** (tariffs/ICE/soybeans/trade)
4. **CME FTP settlements loader**
5. **EIA API loader** (crude, biod iesel)
6. **USDA export sales loader** (China purchases)
7. **CONAB Brazil crops loader**
8. **EPA RFS biofuels loader**
9. **MPOB palm oil loader**
10. **Baltic Dry Index loader**
11. **Wheat futures loader**
12. **CVOL soybean volatility loader**

---

## 3. Active Cron Jobs

```cron
# Working collectors (running on schedule)
0 9,11,13,15 * * 1-5  multi_source_collector.py      # Yahoo + FRED + GDELT
0 */6 * * *           gdelt_china_intelligence.py    # China news
0 10,16 * * *         social_intelligence.py         # BROKEN (0 records)
0 */4 * * *           trump_truth_social_monitor.py  # Trump posts
0 6 * * *             ingest_weather_noaa.py         # US weather
0 7 * * *             ingest_brazil_weather_inmet.py # Brazil weather
```

**Logs directory:** `/Users/zincdigital/CBI-V14/logs/`

### 3.1 Recent Log Summary

**multi_source.log (last run: 2025-10-10 15:06):**
- ✅ Collected 24 records (6 FRED + 6 Yahoo prices + 1 VIX + 11 GDELT)
- ✅ 9/9 sources successful
- ✅ All free sources, $0 cost

**social.log (last run: 2025-10-10 16:00):**
- ❌ Facebook scraper collected **0 records**
- ⚠️ No data saved to BigQuery

**trump_social.log (last run: 2025-10-10 20:00):**
- ✅ Collected 1 Trump post
- ✅ 5,049 ScrapeCreators credits remaining
- ✅ Saved to `ice_trump_intelligence` table

---

## 4. Data Lineage & Dependencies

### 4.1 Curated Views → Source Tables

```
curated.vw_economic_daily
  └─ forecasting_data_warehouse.economic_indicators (6,534 rows, FRED only)

curated.vw_social_intelligence
  └─ forecasting_data_warehouse.social_sentiment (0 rows, BROKEN)

curated.vw_volatility_daily
  └─ forecasting_data_warehouse.volatility_data (780 rows, placeholder data)

curated.vw_weather_daily
  └─ forecasting_data_warehouse.weather_data (9,505 rows, ACTIVE)

curated.vw_zl_features_daily
  └─ forecasting_data_warehouse.soybean_oil_prices (525 rows, Yahoo source)
```

### 4.2 Legacy Views (in wrong dataset)

All 12 `vw_*` views in `forecasting_data_warehouse` query the same tables as curated views → **REDUNDANT**

### 4.3 Orphaned Objects

- `deprecated.fct_zl_price_volatility_daily_legacy_20251009T114922` (safe to drop)
- `forecasting_data_warehouse.soy_oil_features` (misnamed view, should be `vw_soy_oil_features_daily`)

---

## 5. Cloud Resources

### 5.1 Compute Instances
```
workstations-1ee5d88b-d9b7-47ad-af54-f46e2535f426
  Type: e2-medium
  Zone: us-central1-a
  Status: RUNNING
  External IP: 104.198.144.75
```

**ACTION:** Verify if this is actively used or can be stopped.

### 5.2 Cloud Storage Buckets
```
gs://cbi-v14_cloudbuild/              (Cloud Build artifacts)
gs://forecasting-app-raw-data-bucket/ (unknown contents)
```

**ACTION:** Audit bucket contents and retention policies.

### 5.3 Cloud Scheduler
**NONE** - All scheduling is via local cron.

---

## 6. Gap Analysis

### 6.1 Critical Missing Data Sources

| Priority | Data Source | Purpose | Status |
|----------|-------------|---------|--------|
| HIGH | USDA Export Sales | China purchases tracking | ❌ Missing |
| HIGH | CONAB Brazil | Harvest forecasts | ❌ Missing |
| HIGH | EPA RFS/EIA Biodiesel | Biofuel demand | ❌ Missing |
| HIGH | CME Settlements | Authoritative futures prices | ❌ Missing |
| HIGH | MPOB Malaysia | Palm oil supply | ❌ Missing |
| MEDIUM | Yahoo/TE News | Market intelligence | ❌ Missing |
| MEDIUM | Baltic Dry Index | Shipping costs | ❌ Missing |
| MEDIUM | CME CVOL | Soybean volatility index | ❌ Missing |
| MEDIUM | Wheat futures | Alt commodity tracking | ❌ Missing |
| LOW | Reddit search | Social sentiment | ❌ Missing |

### 6.2 Broken/Placeholder Data

| Table | Issue | Action Required |
|-------|-------|-----------------|
| `volatility_data` | Placeholder/suspect data | Backup, purge, reload from CBOE/FRED |
| `soybean_oil_prices` | Yahoo source (unreliable) | Replace with CME/EIA/Polygon |
| `social_sentiment` | 0 rows collected | Fix Facebook/LinkedIn scraper |
| `news_intelligence` | Only GDELT, missing metadata | Add Yahoo/TE scrapers |
| `economic_indicators` | FRED only | Add EIA, Treasury, USDA data |

### 6.3 Naming Violations

**12 views in wrong dataset:**
- Move all `forecasting_data_warehouse.vw_*` to `curated` or drop if redundant
- Rename `soy_oil_features` to `vw_soybean_oil_features_daily` (add missing "bean" to match table name)

---

## 7. Documentation Review

### 7.1 Current Documentation

✅ `docs/governance/warehouse_governance.md` - Medallion architecture, naming rules  
✅ `docs/plans/production_architecture_plan.md` - 9-phase execution plan  
⚠️ `docs/operations/FORENSIC_AUDIT_V14_FINAL.md` - Outdated (pre-October audit)  
⚠️ `docs/plans/PROJECT_STATUS.md` - May be stale  

### 7.2 Documentation Gaps

- No ingestion runbook for new scrapers
- No data lineage diagram
- No SLO/freshness dashboard spec
- No cost monitoring playbook
- No scraper development template

---

## 8. Cleanup Plan (NOT EXECUTED - FOR REVIEW ONLY)

### 8.1 Immediate Actions (No Data Loss)

```sql
-- 1. Archive legacy views from forecasting_data_warehouse
CREATE OR REPLACE VIEW deprecated.vw_brazil_precip_daily_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_brazil_precip_daily;

-- Repeat for all 12 legacy views, then DROP from forecasting_data_warehouse

-- 2. Drop orphaned deprecated view
DROP VIEW deprecated.fct_zl_price_volatility_daily_legacy_20251009T114922;

-- 3. Rename misnamed view (add missing "bean" to match soybean_oil_prices table)
CREATE OR REPLACE VIEW curated.vw_soybean_oil_features_daily AS
SELECT * FROM forecasting_data_warehouse.soy_oil_features;

DROP VIEW forecasting_data_warehouse.soy_oil_features;
```

### 8.2 Data Replacement (Requires Backups First)

```sql
-- 1. Backup current price tables
CREATE TABLE bkp.soybean_oil_prices_20251011 AS SELECT * FROM forecasting_data_warehouse.soybean_oil_prices;
CREATE TABLE bkp.volatility_data_20251011 AS SELECT * FROM forecasting_data_warehouse.volatility_data;

-- 2. Purge placeholder/Yahoo data (DO NOT RUN UNTIL NEW DATA READY)
-- TRUNCATE TABLE forecasting_data_warehouse.soybean_oil_prices;
-- TRUNCATE TABLE forecasting_data_warehouse.volatility_data;

-- 3. Load from CME/EIA/CBOE (new scrapers required)
```

### 8.3 Missing Table Creation

```sql
-- Create staging tables for new scrapers
CREATE TABLE staging.news_articles_raw (
  url STRING NOT NULL,
  source STRING NOT NULL,
  title STRING,
  full_text STRING,
  published_date TIMESTAMP,
  fetched_at TIMESTAMP NOT NULL,
  content_hash STRING NOT NULL,
  provenance_uuid STRING NOT NULL
)
PARTITION BY DATE(fetched_at)
CLUSTER BY source, url;

CREATE TABLE staging.cache_ingestion_ledger (
  content_hash STRING NOT NULL,
  url STRING NOT NULL,
  source STRING NOT NULL,
  first_seen TIMESTAMP NOT NULL,
  last_checked TIMESTAMP NOT NULL
)
PARTITION BY DATE(first_seen)
CLUSTER BY content_hash;

-- Repeat for usda_exports, conab_crops, epa_biofuels, etc.
```

---

## 9. Build Plan (New Scrapers Required)

### 9.1 Priority 1: Market Data (CME/EIA/FRED)

**Goal:** Replace Yahoo-sourced prices with authoritative data

**Scrapers to build:**
1. `ingest_cme_settlements.py` - FTP scraper for ZL/ZS/ZM/ZC/ZW daily settlements
2. `ingest_eia_energy.py` - EIA API for WTI/Brent/biofuels
3. `ingest_fred_macro.py` - FRED API for FX (USD/BRL, USD/CNY), rates, CPI

**Targets:**
- `staging.cme_settlements` → facade to `curated.vw_prices_daily`
- `staging.eia_energy` → facade to `curated.vw_energy_daily`
- `staging.fred_macro` → merge into `curated.vw_economic_daily`

### 9.2 Priority 2: News & Intelligence (Yahoo/TE/Reddit)

**Goal:** Full-text article ingestion with deduplication

**Scrapers to build:**
1. `scrape_yahoo_news.py` - 7 Yahoo Finance topics (tariffs, econ, crude, etc.)
2. `scrape_tradingeconomics_news.py` - 7 TE commodity/stream pages
3. `scrape_reddit_search.py` - Reddit API for keywords (tariffs, ICE, soybeans, etc.)

**Features:**
- Hash-based deduplication (SHA-256 of URL + content)
- Full article text extraction (not just headlines)
- `staging.cache_ingestion_ledger` to prevent re-fetch
- Hourly cadence for 14 days, then 4-hour steady state

**Targets:**
- `raw.news_*` → `staging.news_articles_normalized` → `curated.vw_news_market_articles`

### 9.3 Priority 3: Fundamentals (USDA/CONAB/EPA)

**Goal:** Client-priority data for dashboard

**Scrapers to build:**
1. `ingest_usda_exports.py` - Weekly export sales (China purchases)
2. `ingest_conab_brazil.py` - Monthly crop reports
3. `ingest_epa_rfs.py` - Biofuel mandates/production

**Targets:**
- `staging.usda_exports` → `curated.vw_china_demand_daily`
- `staging.conab_crops` → `curated.vw_brazil_harvest_monthly`
- `staging.epa_biofuels` → `curated.vw_biofuel_demand_monthly`

### 9.4 Priority 4: Volatility Suite Rebuild

**Goal:** Distinct, clearly named volatility metrics

**Scrapers to build:**
1. `ingest_cboe_vix.py` - CBOE VIX index (FRED fallback)
2. `ingest_cme_cvol.py` - CME soybean CVOL index
3. `calc_realized_volatility.py` - Price-derived ZL volatility

**Targets:**
- 3 separate views: `vw_vix_daily`, `vw_cvol_soybean_daily`, `vw_zl_realized_volatility_daily`
- Merge into `curated.vw_volatility_suite_daily` for dashboard

### 9.5 Priority 5: Social Intelligence Fix

**Goal:** Get Facebook/LinkedIn scraper working

**Actions:**
1. Debug `social_intelligence.py` - why 0 records?
2. Verify ScrapeCreators API endpoints
3. Add neural scoring before BigQuery load
4. Backfill 100 posts per source (Facebook + LinkedIn)

---

## 10. Cost & Monitoring

### 10.1 Current Spend

- BigQuery storage: ~3 MB total (negligible)
- BigQuery queries: ~$0 (free tier)
- ScrapeCreators: 5,049 credits remaining
- Compute (e2-medium): ~$30/month if running 24/7

### 10.2 Projected Spend (New Scrapers)

**Scenario: Hourly news scraping for 14 days**
- Yahoo/TE/Reddit: ~500 articles/day × 14 days = 7,000 articles
- Storage: ~100 MB raw text
- BigQuery cost: < $1
- ScrapeCreators: ~1,000 credits (~$10)
- Total: ~$11 for 14-day sprint

**Steady-state (4-hour cadence):**
- ~125 articles/day
- ~$3/month additional

### 10.3 Monitoring Gaps

- No freshness dashboard
- No ingestion failure alerts
- No cost anomaly detection
- No placeholder data scanner

---

## 11. Action Items (Prioritized)

### Immediate (Do Now)
1. ✅ **Complete this audit** and review with user
2. ❌ **Stop claiming scrapers are running** when they don't exist
3. ❌ **Get explicit approval** before building any new code

### Phase 1: Cleanup (1 day)
1. Move 12 legacy views from `forecasting_data_warehouse` to `curated` or drop
2. Rename `soy_oil_features` to `vw_soybean_oil_features_daily` (fix missing "bean")
3. Drop deprecated orphan view
4. Document current data lineage

### Phase 2: Market Data (3 days)
1. Build CME FTP scraper for settlements
2. Build EIA API scraper for energy
3. Extend FRED scraper for FX
4. Replace Yahoo price data
5. Validate against Reuters/Bloomberg

### Phase 3: News Ingestion (5 days)
1. Build Yahoo Finance news scraper (7 topics)
2. Build TradingEconomics news scraper (7 streams)
3. Build Reddit search scraper
4. Implement hash-based deduplication cache
5. Deploy hourly schedule for 14 days
6. Monitor costs and cache hit ratio

### Phase 4: Fundamentals (5 days)
1. Build USDA export sales scraper
2. Build CONAB Brazil crops scraper
3. Build EPA RFS biofuels scraper
4. Build MPOB palm oil scraper
5. Build Baltic Dry Index scraper
6. Build wheat futures scraper

### Phase 5: Volatility Suite (2 days)
1. Build CBOE VIX scraper
2. Build CME CVOL scraper
3. Build realized volatility calculator
4. Create separate views for each

### Phase 6: Social Intelligence (2 days)
1. Debug Facebook/LinkedIn scraper
2. Add neural scoring
3. Backfill 100 posts per source
4. Integrate with ScrapeCreators LinkedIn endpoints

### Phase 7: Monitoring (2 days)
1. Build freshness dashboard
2. Add ingestion failure alerts
3. Implement cost anomaly detection
4. Deploy nightly placeholder scanner

---

## 12. Risk Assessment

### High Risk
- **Yahoo-sourced price data** may diverge from CME official settlements
- **Missing canonical metadata** in 43 news_intelligence rows
- **Social intelligence broken** - 0 records for weeks
- **No backup recovery tested** - backups exist but never restored

### Medium Risk
- **Compute instance running 24/7** - unknown purpose, may be wasteful
- **No alerting** - failures go unnoticed for days
- **Cron-based scheduling** - fragile, no retries or dead-letter queue

### Low Risk
- **Small data volumes** - easy to re-ingest if lost
- **Free API tier usage** - no cost overruns
- **Separate datasets** - changes isolated to staging/curated

---

## 13. Recommendations

### Do Immediately
1. **Stop making claims about non-existent infrastructure**
2. **Get user approval for each build phase**
3. **Test every scraper locally before scheduling**
4. **Document what actually exists vs. what's planned**

### Do This Week
1. **Clean up naming violations**
2. **Build CME/EIA/FRED scrapers**
3. **Replace Yahoo price data**
4. **Fix social intelligence collector**

### Do This Month
1. **Build all news scrapers (Yahoo/TE/Reddit)**
2. **Build fundamentals scrapers (USDA/CONAB/EPA)**
3. **Rebuild volatility suite with clear naming**
4. **Implement monitoring and alerting**

### Do This Quarter
1. **Migrate all cron jobs to Cloud Scheduler**
2. **Implement proper CI/CD for scrapers**
3. **Build ML training pipeline**
4. **Complete dashboard integration**

---

## 14. Conclusion

**Reality Check:**
- Only 6 scrapers are actually running
- 0 news article scrapers exist
- Raw dataset completely empty
- Social intelligence broken
- Missing 10+ critical data sources
- Naming violations persist

**The Good News:**
- What is running works reliably
- Data quality is good where it exists
- Medallion architecture is sound
- Documentation exists (if outdated)
- Codebase is organized
- No cost overruns

**Next Step:**
- Get user approval for each phase
- Build scrapers properly with full testing
- Only deploy after user review
- Update docs to match reality

---

**END OF AUDIT REPORT**

