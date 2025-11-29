---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Comprehensive Cron Scheduling Audit Report
**Generated:** 2025-11-05  
**Purpose:** Optimize performance, reduce costs, ensure critical data sources stay current

---

## Executive Summary

**Current State:**
- **Local Crontab Jobs:** 14 active jobs
- **Cloud Scheduler Jobs:** 2 active jobs
- **Total Scheduled Executions:** ~2,200+ runs/month
- **Critical Issues:** 3 high-cost jobs identified, 2 schedule conflicts, 1 over-frequency job

**Estimated Monthly Costs:**
- BigQuery Load Operations: ~$15-25/month
- BigQuery Query Operations: ~$50-100/month (high variance)
- API Calls: ~$5-10/month
- Cloud Run Invocations: ~$10-15/month
- **Total Estimated:** ~$80-150/month

**Potential Savings:** $40-60/month (33-40% reduction) with optimizations

---

## 1. Complete Job Inventory

### 1.1 Local Crontab Jobs

| Job | Schedule | Frequency | Script | Cost Impact |
|-----|----------|-----------|--------|-------------|
| **CRITICAL: Hourly Prices** | `*/15 9-16 * * 1-5` | Every 15 min (9 AM-4 PM weekdays) | `hourly_prices.py` | **HIGH** - 28 runs/day = 600/month |
| **Weather Data** | `0 */6 * * *` | Every 6 hours (24/7) | `daily_weather.py` | Medium - 4 runs/day = 120/month |
| **Social Intelligence** | `0 */2 * * *` | Every 2 hours (24/7) | `ingest_social_intelligence_comprehensive.py` | Medium - 12 runs/day = 360/month |
| **Policy Data** | `0 9 * * 1-5` | Daily 9 AM (weekdays) | `backfill_trump_intelligence.py` | Low - 5 runs/week = 22/month |
| **Economic Indicators** | `0 8 * * 1-5` | Daily 8 AM (weekdays) | `ingest_market_prices.py` | Low - 5 runs/week = 22/month |
| **CFTC Data** | `0 17 * * 5` | Weekly Friday 5 PM | `ingest_cftc_positioning_REAL.py` | Low - 4 runs/month |
| **Export Sales** | `0 15 * * 4` | Weekly Thursday 3 PM | `ingest_usda_harvest_api.py` | Low - 4 runs/month |
| **Biofuel Production** | `0 10 * * 3` | Weekly Wednesday 10 AM | `ingest_eia_biofuel_real.py` | Low - 4 runs/month |
| **Web Scraper (Morning)** | `0 9 * * 1-5` | Daily 9 AM (weekdays) | `production_web_scraper.py` | Medium - 5 runs/week = 22/month |
| **Web Scraper (Afternoon)** | `0 16 * * 1-5` | Daily 4 PM (weekdays) | `production_web_scraper.py` | Medium - 5 runs/week = 22/month |
| **Satellite Data** | `0 7 * * *` | Daily 7 AM (24/7) | `ingest_scrapecreators_institutional.py` | Medium - 30 runs/month |
| **Quality Monitor** | `0 * * * *` | Every hour (24/7) | `enhanced_data_quality_monitor.py` | **HIGH** - 24 runs/day = 720/month |
| **Weekend Maintenance** | `0 2 * * 0` | Weekly Sunday 2 AM | `daily_data_pull_and_migrate.py` | Low - 4 runs/month |
| **Trump Social Monitor** | `0 */4 * * *` | Every 4 hours (24/7) | `trump_truth_social_monitor.py` | Medium - 6 runs/day = 180/month |
| **⚠️ MASTER COLLECTOR** | `*/15 * * * *` | **Every 15 min (24/7)** | `MASTER_CONTINUOUS_COLLECTOR.py` | **CRITICAL** - 96 runs/day = **2,880/month** |

### 1.2 Cloud Scheduler Jobs

| Job Name | Schedule | Target | Frequency | Cost Impact |
|----------|----------|--------|-----------|-------------|
| **data-ingestion** | `0 */4 * * *` | Cloud Run: `forecasting-app-external-data-ingestion` | Every 4 hours (24/7) | Medium - 6 runs/day = 180/month |
| **model-training** | `0 2 * * 0` | Cloud Run: `forecasting-app-backend` | Weekly Sunday 2 AM | Low - 4 runs/month |

### 1.3 Jobs Not Currently Scheduled (from setup scripts)

These jobs are defined in setup scripts but **not active** in current crontab:
- `refresh_features_pipeline.py` (should run 2x/day per `enhanced_cron_setup.sh`)
- `hourly_news.py` (should run hourly per `crontab_setup.sh`)
- `daily_signals.py` (should run daily per `crontab_setup.sh`)

---

## 2. Cost Analysis

### 2.1 BigQuery Load Operations

**High-frequency load jobs:**
1. **MASTER_CONTINUOUS_COLLECTOR** (2,880 runs/month)
   - Loads to multiple tables: `trump_policy_intelligence`, `social_sentiment`, `news_intelligence`
   - Estimated: 10-50 rows per run = 28,800-144,000 rows/month
   - **Cost: ~$1-7/month** (load operations)

2. **hourly_prices.py** (600 runs/month)
   - Loads ~8-10 price records per run = 4,800-6,000 rows/month
   - **Cost: ~$0.25/month** (load operations)

3. **daily_weather.py** (120 runs/month)
   - Loads ~19 weather station records per run = 2,280 rows/month
   - **Cost: ~$0.10/month** (load operations)

4. **ingest_social_intelligence_comprehensive.py** (360 runs/month)
   - Variable rows per run (10-100) = 3,600-36,000 rows/month
   - **Cost: ~$0.20-2/month** (load operations)

**Total Load Costs: ~$2-10/month**

### 2.2 BigQuery Query Operations

**High-cost query jobs:**
1. **enhanced_data_quality_monitor.py** (720 runs/month)
   - Runs multiple validation queries per execution:
     - Cross-source FX validation (queries currency_data table)
     - Missing data detection (scans multiple tables)
     - Anomaly detection (statistical queries)
   - Estimated: 5-10 queries per run = 3,600-7,200 queries/month
   - **Cost: ~$10-50/month** (depends on table sizes)

2. **refresh_features_pipeline.py** (if scheduled: 60 runs/month)
   - **CRITICAL:** Materializes `training_dataset_super_enriched` from view `neural.vw_big_eight_signals`
   - This view likely scans 100+ GB of data across multiple tables
   - `CREATE OR REPLACE TABLE` scans all underlying data
   - **Cost: ~$50-100/month** (if run 2x/day as intended)

3. **daily_signals.py** (if scheduled: 22 runs/month)
   - Queries `vix_daily`, `training_dataset` tables
   - **Cost: ~$1-5/month**

**Total Query Costs: ~$61-155/month** (high variance)

### 2.3 API Costs

- **Scrape Creators API** (used by MASTER_CONTINUOUS_COLLECTOR, trump_truth_social_monitor)
  - MASTER_COLLECTOR: 2,880 calls/month = potentially expensive
  - Trump monitor: 180 calls/month
  - **Estimated: $5-10/month** (if paid tier)

- **Yahoo Finance** (free, but rate-limited)
- **Alpha Vantage** (free tier: 500 calls/day = 15,000/month)
  - VIX data: 600 calls/month from hourly_prices.py = safe

### 2.4 Cloud Run Costs

- **data-ingestion**: 180 invocations/month × ~30s execution = ~90 minutes compute
  - **Cost: ~$2-5/month**

- **model-training**: 4 invocations/month × ~10-30 min execution = ~40-120 minutes compute
  - **Cost: ~$5-15/month**

**Total Cloud Run: ~$7-20/month**

### 2.5 Total Monthly Cost Estimate

| Category | Low Estimate | High Estimate |
|----------|--------------|----------------|
| BigQuery Loads | $2 | $10 |
| BigQuery Queries | $61 | $155 |
| API Calls | $5 | $10 |
| Cloud Run | $7 | $20 |
| **TOTAL** | **$75** | **$195** |

---

## 3. Performance & Overlap Analysis

### 3.1 Schedule Conflicts

**Peak Load Times:**

1. **9:00 AM (Weekdays)** - **3 jobs competing:**
   - `production_web_scraper.py` (morning)
   - `backfill_trump_intelligence.py` (policy data)
   - `ingest_market_prices.py` (economic indicators)
   - **Risk:** Network bandwidth, API rate limits, BigQuery concurrency

2. **4:00 PM (Weekdays)** - **2-3 jobs competing:**
   - `production_web_scraper.py` (afternoon)
   - Cloud Scheduler: palm daily scraper (if configured)
   - Cloud Scheduler: `scrape-comprehensive-afternoon` (if configured)
   - **Risk:** BigQuery write contention

3. **Every 15 minutes (9 AM-4 PM weekdays)** - **Continuous load:**
   - `hourly_prices.py` + `MASTER_CONTINUOUS_COLLECTOR.py` = **2 jobs every 15 min**
   - **Risk:** Constant BigQuery load operations, API rate limits

### 3.2 Resource Contention

**BigQuery Concurrent Operations:**
- Multiple jobs writing simultaneously (9 AM, 4 PM peaks)
- `MASTER_CONTINUOUS_COLLECTOR` runs every 15 min = constant background load
- `enhanced_data_quality_monitor` runs hourly = frequent query load

**Network Bandwidth:**
- Multiple scrapers at 9 AM and 4 PM hitting external APIs
- Potential rate limiting from Yahoo Finance, Alpha Vantage, Scrape Creators

### 3.3 Frequency Optimization Opportunities

**Over-frequent:**
1. **MASTER_CONTINUOUS_COLLECTOR** - Every 15 min (24/7) = **2,880 runs/month**
   - **Recommendation:** Reduce to hourly (24 runs/day = 720/month) = **75% reduction**
   - **Savings:** ~$30-40/month in API + BigQuery costs

2. **hourly_prices.py** - Every 15 min during market hours (28 runs/day)
   - **Recommendation:** Reduce to every hour (7 runs/day) = **75% reduction**
   - **Savings:** ~$5-10/month in BigQuery costs
   - **Note:** Markets don't update every 15 minutes; hourly is sufficient

3. **enhanced_data_quality_monitor** - Every hour (24 runs/day)
   - **Recommendation:** Reduce to every 4 hours (6 runs/day) = **75% reduction**
   - **Savings:** ~$10-30/month in BigQuery query costs
   - **Note:** Data quality checks don't need hourly frequency

**Under-frequent:**
- No critical sources are under-frequented (all critical Big 8 signals are covered)

**Missing:**
- `refresh_features_pipeline.py` is **not scheduled** but should run 1-2x/day
- `hourly_news.py` is **not scheduled** but should run hourly for breaking news
- `daily_signals.py` is **not scheduled** but should run daily for signal calculations

---

## 4. Critical Data Source Coverage

### 4.1 Current Coverage Assessment

**✅ Critical Sources Covered:**
- China imports: Covered by various scrapers and ingestion scripts
- Argentina crisis: Covered by `MASTER_CONTINUOUS_COLLECTOR` and weather scrapers
- Industrial demand: Covered by economic indicators and market prices
- Big 8 signals: Data collected (though `refresh_features_pipeline.py` not scheduled)

**⚠️ Missing Sources (from audit):**
- Baltic Dry Index (daily freight rates)
- Port congestion data (daily shipping delays)
- Fertilizer prices (monthly cost pressures)
- ENSO climate data (monthly weather forecasts)
- Satellite crop health (weekly vegetation indices)

**Note:** These missing sources are not critical for current model training but should be added for comprehensive coverage.

### 4.2 Data Freshness

**Hourly/Frequent Updates:**
- ✅ Prices: Every 15 min (over-frequent, but ensures freshness)
- ✅ Weather: Every 6 hours (good for crop monitoring)
- ✅ Social intelligence: Every 2 hours (good for breaking news)
- ✅ Quality monitoring: Every hour (over-frequent)

**Daily Updates:**
- ✅ Policy data: Daily at 9 AM (weekdays only - missing weekends)
- ✅ Economic indicators: Daily at 8 AM (weekdays only)
- ✅ Web scraping: 2x/day (9 AM, 4 PM weekdays)

**Weekly Updates:**
- ✅ CFTC: Weekly Friday (appropriate)
- ✅ Export sales: Weekly Thursday (appropriate)
- ✅ Biofuel: Weekly Wednesday (appropriate)

**Issues:**
- Policy and economic data only run weekdays - missing weekend updates
- No scheduled `refresh_features_pipeline.py` - Big 8 signals may be stale

---

## 5. Error Handling & Monitoring

### 5.1 Current Monitoring

**Logging:**
- ✅ All jobs log to `/Users/zincdigital/CBI-V14/logs/`
- ✅ Individual log files per job (e.g., `prices.log`, `weather.log`)
- ✅ Log rotation exists (daily at midnight, deletes logs >30 days)

**Error Handling:**
- ✅ `@intelligence_collector` decorator provides retry logic (3 retries, exponential backoff)
- ✅ `enhanced_data_quality_monitor.py` has error handling
- ⚠️ Some scripts (e.g., `hourly_prices.py`) have basic error handling but may not retry on transient failures

### 5.2 Gaps Identified

**Missing:**
- ❌ No centralized failure alerting (Cloud Monitoring, email, Slack)
- ❌ No cost monitoring alerts (BigQuery budget alerts)
- ❌ No data freshness monitoring (alert if data is stale)
- ❌ No job execution tracking (which jobs succeeded/failed)
- ❌ No automated health checks (proactive monitoring)

**Current Log Audit:**
- Recent logs show active execution:
  - `MASTER_CONTINUOUS.log` (Nov 5, 8:30 AM) - active
  - `COMPREHENSIVE_POLICY.log` (Nov 5, 7:08 AM) - active
  - `WEB_SCRAPER_FULL.log` (Nov 5, 7:09 AM) - active
- No obvious errors in recent logs

---

## 6. Optimization Recommendations

### 6.1 Immediate Cost Optimizations (High Impact)

#### 6.1.1 Reduce MASTER_CONTINUOUS_COLLECTOR Frequency
**Current:** Every 15 minutes (24/7) = 2,880 runs/month  
**Recommended:** Every hour (24/7) = 720 runs/month  
**Savings:** ~$30-40/month (75% reduction)

**Impact:** Minimal - hourly updates are sufficient for policy/social intelligence data.  
**Action:** Update crontab: `*/15` → `0 * * * *`

#### 6.1.2 Reduce hourly_prices.py Frequency
**Current:** Every 15 minutes (9 AM-4 PM weekdays) = 28 runs/day = 600/month  
**Recommended:** Every hour (9 AM-4 PM weekdays) = 7 runs/day = 150/month  
**Savings:** ~$5-10/month (75% reduction)

**Impact:** Minimal - markets don't update every 15 minutes; hourly is sufficient.  
**Action:** Update crontab: `*/15 9-16 * * 1-5` → `0 9-16 * * 1-5`

#### 6.1.3 Reduce enhanced_data_quality_monitor Frequency
**Current:** Every hour (24/7) = 24 runs/day = 720/month  
**Recommended:** Every 4 hours (24/7) = 6 runs/day = 180/month  
**Savings:** ~$10-30/month (75% reduction)

**Impact:** Minimal - data quality checks don't need hourly frequency.  
**Action:** Update crontab: `0 * * * *` → `0 */4 * * *`

#### 6.1.4 Optimize refresh_features_pipeline.py (if scheduled)
**Current:** Should run 2x/day (per `enhanced_cron_setup.sh`) but not currently scheduled  
**Recommended:** Run 1x/day at 6 AM, OR implement incremental materialization  
**Savings:** ~$25-50/month (if reduced from 2x to 1x/day)

**Impact:** Medium - if Big 8 signals need same-day updates, keep 2x/day. Otherwise, 1x/day is sufficient.  
**Action:** 
- Schedule 1x/day at 6 AM
- OR implement incremental materialization (only update changed rows)

**Total Immediate Savings: ~$70-130/month**

### 6.2 Performance Optimizations

#### 6.2.1 Stagger Peak Times
**Current:** 3 jobs at 9 AM, 2 jobs at 4 PM  
**Recommended:** Spread jobs across 15-minute intervals:
- 8:45 AM: `ingest_market_prices.py` (economic indicators)
- 9:00 AM: `production_web_scraper.py` (morning)
- 9:15 AM: `backfill_trump_intelligence.py` (policy data)
- 4:00 PM: `production_web_scraper.py` (afternoon)
- 4:15 PM: Cloud Scheduler jobs (if configured)

**Impact:** Reduces network bandwidth contention and BigQuery write conflicts.  
**Savings:** Reduces failed operations and retries.

#### 6.2.2 Add Delays Between Concurrent BigQuery Operations
**Current:** Multiple jobs may write simultaneously  
**Recommended:** Add 5-10 second delays between jobs that write to BigQuery  
**Impact:** Reduces BigQuery write contention and improves reliability.

### 6.3 Reliability Improvements

#### 6.3.1 Add refresh_features_pipeline.py to Schedule
**Current:** Not scheduled (defined in `enhanced_cron_setup.sh` but not active)  
**Recommended:** Schedule 1x/day at 6 AM  
**Action:** Add to crontab: `0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_features_pipeline.py >> /Users/zincdigital/CBI-V14/logs/feature_refresh.log 2>&1`

#### 6.3.2 Add hourly_news.py for Breaking News
**Current:** Not scheduled (defined in `crontab_setup.sh` but not active)  
**Recommended:** Schedule hourly during market hours (9 AM-4 PM weekdays)  
**Action:** Add to crontab: `0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_news.py >> /Users/zincdigital/CBI-V14/logs/breaking_news.log 2>&1`

#### 6.3.3 Add daily_signals.py for Signal Calculations
**Current:** Not scheduled (defined in `crontab_setup.sh` but not active)  
**Recommended:** Schedule daily at 7 AM (weekdays)  
**Action:** Add to crontab: `0 7 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_signals.py >> /Users/zincdigital/CBI-V14/logs/signals.log 2>&1`

#### 6.3.4 Add Weekend Coverage for Critical Sources
**Current:** Policy and economic data only run weekdays  
**Recommended:** Add weekend runs for critical sources:
- Policy data: Add Saturday 9 AM run
- Economic indicators: Add Saturday 8 AM run

**Action:** Update crontab schedules to include weekends for critical sources.

### 6.4 Monitoring & Alerting

#### 6.4.1 Set Up Cloud Monitoring Alerts
**Recommended:**
- Alert on cron job failures (if Cloud Functions are used)
- Alert on BigQuery job failures
- Alert on data freshness (if data older than expected threshold)

#### 6.4.2 Set Up BigQuery Cost Budget Alerts
**Recommended:**
- Budget: $100/month for BigQuery
- Alert at 80% ($80) and 100% ($100)

#### 6.4.3 Add Centralized Job Execution Tracking
**Recommended:**
- Create a simple table in BigQuery to track job execution:
  - `job_name`, `execution_time`, `status`, `rows_processed`, `duration_seconds`
- Update all scripts to log execution to this table

---

## 7. Optimized Cron Configuration

### 7.1 Recommended Optimized Crontab

```bash
# ====================================================================
# CBI-V14 OPTIMIZED DATA COLLECTION SCHEDULE
# Updated: 2025-11-05
# Optimizations: Reduced frequency for cost savings, staggered peak times
# ====================================================================

# ====================================================================
# CRITICAL FINANCIAL DATA (Every hour during market hours)
# ====================================================================
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_prices.py >> /Users/zincdigital/CBI-V14/logs/prices.log 2>&1

# ====================================================================
# WEATHER DATA (Every 6 hours - includes weekends for crop monitoring)
# ====================================================================
0 */6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 daily_weather.py >> /Users/zincdigital/CBI-V14/logs/weather.log 2>&1

# ====================================================================
# NEWS & SOCIAL INTELLIGENCE (Every 2 hours - 24/7 coverage)
# ====================================================================
0 */2 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_social_intelligence_comprehensive.py >> /Users/zincdigital/CBI-V14/logs/social_intel.log 2>&1

# ====================================================================
# POLICY & GOVERNMENT DATA (Staggered to avoid 9 AM peak)
# ====================================================================
45 8 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 backfill_trump_intelligence.py >> /Users/zincdigital/CBI-V14/logs/trump_policy.log 2>&1
15 9 * * 6 cd /Users/zincdigital/CBI-V14/ingestion && python3 backfill_trump_intelligence.py >> /Users/zincdigital/CBI-V14/logs/trump_policy.log 2>&1  # Saturday

# ====================================================================
# ECONOMIC INDICATORS (Staggered to avoid 9 AM peak)
# ====================================================================
45 7 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_market_prices.py >> /Users/zincdigital/CBI-V14/logs/economic_data.log 2>&1
45 7 * * 6 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_market_prices.py >> /Users/zincdigital/CBI-V14/logs/economic_data.log 2>&1  # Saturday

# ====================================================================
# WEEKLY DATA SOURCES
# ====================================================================
0 17 * * 5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_cftc_positioning_REAL.py >> /Users/zincdigital/CBI-V14/logs/cftc_data.log 2>&1
0 15 * * 4 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_usda_harvest_api.py >> /Users/zincdigital/CBI-V14/logs/usda_exports.log 2>&1
0 10 * * 3 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_eia_biofuel_real.py >> /Users/zincdigital/CBI-V14/logs/biofuel_data.log 2>&1

# ====================================================================
# WEB SCRAPING (Staggered to avoid conflicts)
# ====================================================================
0 9 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 production_web_scraper.py >> /Users/zincdigital/CBI-V14/logs/scraper_morning.log 2>&1
0 16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 production_web_scraper.py >> /Users/zincdigital/CBI-V14/logs/scraper_afternoon.log 2>&1

# ====================================================================
# SATELLITE & ALTERNATIVE DATA
# ====================================================================
0 7 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_scrapecreators_institutional.py >> /Users/zincdigital/CBI-V14/logs/satellite_data.log 2>&1

# ====================================================================
# DATA QUALITY MONITORING (Reduced frequency)
# ====================================================================
0 */4 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 enhanced_data_quality_monitor.py >> /Users/zincdigital/CBI-V14/logs/quality_monitor.log 2>&1

# ====================================================================
# MASTER CONTINUOUS COLLECTOR (Reduced frequency - CRITICAL OPTIMIZATION)
# ====================================================================
0 * * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 MASTER_CONTINUOUS_COLLECTOR.py >> /Users/zincdigital/CBI-V14/logs/MASTER_CONTINUOUS.log 2>&1

# ====================================================================
# FEATURE PIPELINE REFRESH (Previously missing - now scheduled)
# ====================================================================
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_features_pipeline.py >> /Users/zincdigital/CBI-V14/logs/feature_refresh.log 2>&1

# ====================================================================
# BREAKING NEWS (Previously missing - now scheduled)
# ====================================================================
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_news.py >> /Users/zincdigital/CBI-V14/logs/breaking_news.log 2>&1

# ====================================================================
# DAILY SIGNAL CALCULATIONS (Previously missing - now scheduled)
# ====================================================================
0 7 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_signals.py >> /Users/zincdigital/CBI-V14/logs/signals.log 2>&1

# ====================================================================
# MAINTENANCE & MONITORING
# ====================================================================
0 2 * * 0 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_data_pull_and_migrate.py >> /Users/zincdigital/CBI-V14/logs/weekend_maintenance.log 2>&1
0 */4 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 trump_truth_social_monitor.py >> /Users/zincdigital/CBI-V14/logs/trump_social.log 2>&1

# ====================================================================
# LOG ROTATION (Daily at midnight)
# ====================================================================
0 0 * * * find /Users/zincdigital/CBI-V14/logs -name "*.log" -mtime +30 -delete

# END OF CBI-V14 SCHEDULE
```

### 7.2 Changes Summary

**Frequency Reductions:**
- `MASTER_CONTINUOUS_COLLECTOR`: 96 runs/day → 24 runs/day (75% reduction)
- `hourly_prices.py`: 28 runs/day → 7 runs/day (75% reduction)
- `enhanced_data_quality_monitor`: 24 runs/day → 6 runs/day (75% reduction)

**New Jobs Added:**
- `refresh_features_pipeline.py`: 1 run/day (previously missing)
- `hourly_news.py`: 7 runs/day (previously missing)
- `daily_signals.py`: 5 runs/week (previously missing)

**Staggered Times:**
- Economic indicators: 8:45 AM (was 8:00 AM)
- Policy data: 8:45 AM weekdays, 9:15 AM Saturday (was 9:00 AM)

**Total Runs After Optimization:**
- Before: ~2,200 runs/month
- After: ~1,100 runs/month
- **Reduction: 50%**

---

## 8. Implementation Plan

### Phase 1: Immediate Cost Optimizations (Week 1)

1. **Update crontab with optimized frequencies:**
   - Reduce `MASTER_CONTINUOUS_COLLECTOR` to hourly
   - Reduce `hourly_prices.py` to hourly during market hours
   - Reduce `enhanced_data_quality_monitor` to every 4 hours

2. **Monitor costs for 1 week:**
   - Track BigQuery costs daily
   - Verify data freshness is maintained
   - Check for any missed data

### Phase 2: Add Missing Jobs (Week 1-2)

1. **Schedule missing critical jobs:**
   - Add `refresh_features_pipeline.py` (daily at 6 AM)
   - Add `hourly_news.py` (hourly during market hours)
   - Add `daily_signals.py` (daily at 7 AM)

2. **Add weekend coverage:**
   - Add Saturday runs for policy and economic data

### Phase 3: Stagger Peak Times (Week 2)

1. **Update schedules to stagger 9 AM jobs:**
   - Economic indicators: 8:45 AM
   - Web scraper: 9:00 AM
   - Policy data: 9:15 AM

### Phase 4: Monitoring & Alerting (Week 2-3)

1. **Set up Cloud Monitoring alerts:**
   - Job failure alerts
   - Data freshness alerts

2. **Set up BigQuery budget alerts:**
   - Budget: $100/month
   - Alert at 80% and 100%

3. **Create job execution tracking table:**
   - Simple BigQuery table to track job runs
   - Update scripts to log execution

### Phase 5: Long-term Optimizations (Month 2+)

1. **Implement incremental materialization for `refresh_features_pipeline.py`:**
   - Only update changed rows instead of full table replace
   - Could reduce costs by 50-70%

2. **Add missing data sources:**
   - Baltic Dry Index
   - Port congestion data
   - Fertilizer prices
   - ENSO climate data
   - Satellite crop health

---

## 9. Risk Assessment

### 9.1 Risks of Optimization

**Low Risk:**
- Reducing `hourly_prices.py` to hourly: Markets don't update every 15 minutes; hourly is sufficient
- Reducing `enhanced_data_quality_monitor` to every 4 hours: Data quality doesn't need hourly checks
- Staggering peak times: Reduces conflicts, improves reliability

**Medium Risk:**
- Reducing `MASTER_CONTINUOUS_COLLECTOR` to hourly: May miss some breaking policy news, but hourly is still frequent enough
- Running `refresh_features_pipeline.py` 1x/day instead of 2x/day: If same-day updates are critical, keep 2x/day

**Mitigation:**
- Monitor data freshness for 1 week after optimization
- Keep 2x/day for `refresh_features_pipeline.py` if needed
- Add alerts for stale data

### 9.2 Rollback Plan

If optimizations cause issues:
1. Revert crontab to previous version (backup before changes)
2. Monitor logs for errors
3. Gradually re-optimize with smaller changes

---

## 10. Conclusion

**Current State:**
- 14 local cron jobs + 2 Cloud Scheduler jobs
- ~2,200 runs/month
- Estimated costs: $75-195/month
- 3 high-cost jobs identified
- 2 schedule conflicts
- 3 missing critical jobs

**After Optimization:**
- ~1,100 runs/month (50% reduction)
- Estimated costs: $40-80/month (40-50% reduction)
- All critical jobs scheduled
- Staggered peak times to reduce conflicts
- Improved monitoring and alerting

**Key Recommendations:**
1. **Immediate:** Reduce `MASTER_CONTINUOUS_COLLECTOR` frequency (saves ~$30-40/month)
2. **Immediate:** Reduce `hourly_prices.py` and `enhanced_data_quality_monitor` frequencies (saves ~$15-40/month)
3. **Short-term:** Add missing jobs (`refresh_features_pipeline.py`, `hourly_news.py`, `daily_signals.py`)
4. **Short-term:** Stagger peak times to reduce conflicts
5. **Medium-term:** Set up monitoring and alerting
6. **Long-term:** Implement incremental materialization for `refresh_features_pipeline.py`

**Total Potential Savings: ~$40-60/month (40-50% reduction)**

---

**Report Generated:** 2025-11-05  
**Next Review:** 2025-12-05 (after 1 month of optimization)







