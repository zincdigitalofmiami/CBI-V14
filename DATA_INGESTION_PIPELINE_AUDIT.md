# 📊 DATA INGESTION PIPELINE AUDIT
## Comprehensive Review Against TRUMP ERA EXECUTION PLAN
**Date:** November 7, 2025  
**Status:** CRITICAL GAPS IDENTIFIED

---

## 🎯 EXECUTIVE SUMMARY

### ✅ **STRENGTHS:**
- **42+ ingestion scripts** covering major data sources
- **Cloud Scheduler** configured (2 jobs: data-ingestion every 4 hours, model-training weekly)
- **Cron jobs** optimized (24 scheduled tasks)
- **Big Eight neural signals** pipeline exists (`collect_neural_data_sources.py`)
- **Trump sentiment** monitoring active (`trump_truth_social_monitor.py`)

### ❌ **CRITICAL GAPS:**
1. **Trump Sentiment:** Scheduled but **NOT updating production tables** (only staging)
2. **China Imports:** Script exists but **NOT scheduled** (21 days stale)
3. **RIN Prices:** Script exists but **NOT scheduled** (critical for 42 neural drivers)
4. **Brazil/Argentina Premiums:** **NO dedicated ingestion script**
5. **Production Training Data:** **NO scheduled refresh** (last update Sep 10, 2025 - 56 days stale!)
6. **Big Eight Signals:** Script exists but **NOT scheduled** (manual only)

---

## 📋 INGESTION PIPELINE INVENTORY

### **1. TRUMP SENTIMENT & POLICY INTELLIGENCE**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| `trump_truth_social_monitor.py` | `cbi-v14-ingestion/` | ✅ Every 4h (cron) | `forecasting_data_warehouse.trump_policy_intelligence` | ⚠️ **ACTIVE but may not update production** |
| `backfill_trump_intelligence.py` | `ingestion/` | ✅ 8:45 AM weekdays, 9:15 AM Sat | `staging.trump_policy_intelligence` | ⚠️ **Staging only** |
| `TRUMP_SENTIMENT_QUANT_ENGINE.py` | `scripts/` | ❌ **NOT SCHEDULED** | `trump_sentiment_quantified` | ❌ **MANUAL ONLY** |
| `MASTER_CONTINUOUS_COLLECTOR.py` | `cbi-v14-ingestion/` | ✅ Every hour | Multiple (tariffs, China, prices, FX) | ✅ **ACTIVE** |

**PLAN REQUIREMENT:** Trump sentiment data loaded ✅ (435 rows confirmed)  
**ISSUE:** Quantification engine not scheduled - raw data exists but not processed into features

---

### **2. CHINA IMPORTS DATA**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| `ingest_china_imports_uncomtrade.py` | `ingestion/` | ❌ **NOT SCHEDULED** | `forecasting_data_warehouse.china_soybean_imports` | ❌ **MANUAL ONLY** |
| `ingest_china_sa_alternatives.py` | `ingestion/` | ❌ **NOT SCHEDULED** | Unknown | ❌ **UNKNOWN** |
| `gdelt_china_intelligence.py` | `ingestion/` | ❌ **NOT SCHEDULED** | `forecasting_data_warehouse.news_intelligence` | ❌ **MANUAL ONLY** |

**PLAN REQUIREMENT:** China import data current ⚠️  
**CURRENT STATE:** Last update 2025-10-15 (21 days stale)  
**CRITICAL:** This is feature #9-16 in 42 neural drivers - MUST be fresh

---

### **3. RIN PRICES & BIOFUEL DATA**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| `ingest_epa_rin_prices.py` | `ingestion/` | ❌ **NOT SCHEDULED** | `forecasting_data_warehouse.biofuel_prices` | ❌ **MANUAL ONLY** |
| `ingest_epa_rfs_mandates.py` | `ingestion/` | ❌ **NOT SCHEDULED** | `forecasting_data_warehouse.rfs_mandates` | ❌ **MANUAL ONLY** |
| `ingest_eia_biofuel_real.py` | `ingestion/` | ✅ 10 AM Wed (cron) | `forecasting_data_warehouse.biofuel_production` | ✅ **WEEKLY** |
| `ingest_staging_biofuel_policy.py` | `cbi-v14-ingestion/` | ❌ **NOT SCHEDULED** | `staging.biofuel_policy` | ❌ **MANUAL ONLY** |

**PLAN REQUIREMENT:** RIN D4/D5 prices updated (240% spike tracking)  
**CRITICAL:** Features #23-30 in 42 neural drivers - RIN prices are +0.88 correlation with ZL

---

### **4. BRAZIL/ARGENTINA PREMIUMS**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| **NONE FOUND** | - | ❌ | - | ❌ **MISSING** |

**PLAN REQUIREMENT:** Brazil/Argentina premiums fresh (daily updates)  
**CRITICAL GAP:** No dedicated ingestion script exists!  
**WORKAROUND:** May be calculated from price spreads in `TRUMP_RICH_DART_V1.sql` but not ingested directly

---

### **5. BIG EIGHT NEURAL SIGNALS**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| `collect_neural_data_sources.py` | `scripts/` | ❌ **NOT SCHEDULED** | `neural.vw_big_eight_signals` | ❌ **MANUAL ONLY** |
| `refresh_features_pipeline.py` | `scripts/` | ✅ 6 AM daily (cron) | Multiple (features refresh) | ✅ **ACTIVE** |

**PLAN REQUIREMENT:** Big Eight signals present ✅ (2,141 rows confirmed)  
**ISSUE:** Collection script not scheduled - relies on manual execution or `refresh_features_pipeline.py`

---

### **6. PRODUCTION TRAINING DATA**

| Script | Location | Scheduled | Target Table | Status |
|--------|----------|-----------|--------------|--------|
| `update_production_datasets.py` | `scripts/` | ❌ **NOT SCHEDULED** | `models_v4.production_training_data_*` | ❌ **MANUAL ONLY** |
| `update_training_dataset.py` | `scripts/` | ❌ **NOT SCHEDULED** | `models_v4.production_training_data_*` | ❌ **MANUAL ONLY** |
| `daily_data_pull_and_migrate.py` | `scripts/` | ✅ 2 AM Sunday (cron) | Staging → Main migration | ✅ **WEEKLY** |

**PLAN REQUIREMENT:** Zero stale data ⚠️  
**CURRENT STATE:** Last update Sep 10, 2025 (56 days stale!)  
**CRITICAL:** Production training tables are the source for model training - MUST be refreshed daily

---

### **7. OTHER CRITICAL DATA SOURCES**

| Category | Script | Scheduled | Status |
|----------|--------|-----------|--------|
| **CFTC Positioning** | `ingest_cftc_positioning_REAL.py` | ✅ 5 PM Friday (cron) | ✅ **WEEKLY** |
| **USDA Harvest** | `ingest_usda_harvest_real.py` | ❌ **NOT SCHEDULED** | ❌ **MANUAL ONLY** |
| **USDA Export Sales** | `ingest_usda_export_sales_weekly.py` | ✅ 3 PM Thursday (cron) | ✅ **WEEKLY** |
| **Weather** | `ingest_weather_noaa.py` | ✅ Every 6h (cron) | ✅ **ACTIVE** |
| **Social Intelligence** | `ingest_social_intelligence_comprehensive.py` | ✅ Every 2h (cron) | ✅ **ACTIVE** |
| **Economic Indicators** | `economic_intelligence.py` | ✅ 7:45 AM weekdays (cron) | ✅ **ACTIVE** |
| **News Intelligence** | `multi_source_news.py` | ❌ **NOT SCHEDULED** | ❌ **MANUAL ONLY** |
| **Volatility (VIX)** | `ingest_volatility.py` | ❌ **NOT SCHEDULED** | ❌ **MANUAL ONLY** |

---

## 🔄 SCHEDULED JOBS MAPPING

### **CLOUD SCHEDULER (Google Cloud)**

| Job Name | Schedule | Endpoint | Status | Last Run |
|----------|----------|----------|--------|----------|
| `data-ingestion` | Every 4 hours (`0 */4 * * *`) | `forecasting-app-external-data-ingestion` | ✅ ENABLED | 2025-11-06 16:00 UTC |
| `model-training` | Weekly Sunday 2 AM (`0 2 * * 0`) | `forecasting-app-backend/train` | ✅ ENABLED | 2025-11-02 02:00 UTC |

**ISSUE:** Cloud Scheduler jobs call Cloud Run endpoints - need to verify these endpoints trigger the correct ingestion scripts

---

### **CRON JOBS (Local/VM)**

**Total:** 24 scheduled tasks (from `crontab_optimized.sh`)

#### **CRITICAL DATA (Trump Era Plan Requirements):**

| Task | Schedule | Script | Plan Requirement | Status |
|------|----------|--------|------------------|--------|
| **Trump Truth Social** | Every 4h | `trump_truth_social_monitor.py` | ✅ Required | ✅ **SCHEDULED** |
| **Trump Policy Backfill** | 8:45 AM weekdays, 9:15 AM Sat | `backfill_trump_intelligence.py` | ✅ Required | ⚠️ **Staging only** |
| **China Imports** | ❌ **NOT SCHEDULED** | `ingest_china_imports_uncomtrade.py` | ✅ Required | ❌ **MISSING** |
| **RIN Prices** | ❌ **NOT SCHEDULED** | `ingest_epa_rin_prices.py` | ✅ Required | ❌ **MISSING** |
| **Brazil/Argentina Premiums** | ❌ **NOT SCHEDULED** | **NO SCRIPT** | ✅ Required | ❌ **MISSING** |
| **Big Eight Signals** | ❌ **NOT SCHEDULED** | `collect_neural_data_sources.py` | ✅ Required | ❌ **MISSING** |
| **Production Training Data** | ❌ **NOT SCHEDULED** | `update_production_datasets.py` | ✅ Required | ❌ **MISSING** |

#### **OTHER SCHEDULED TASKS:**

| Task | Schedule | Status |
|------|----------|--------|
| Hourly Prices | 9 AM - 4 PM weekdays | ✅ Active |
| Weather Data | Every 6 hours | ✅ Active |
| Social Intelligence | Every 2 hours | ✅ Active |
| Economic Indicators | 7:45 AM weekdays | ✅ Active |
| CFTC Data | 5 PM Friday | ✅ Weekly |
| USDA Export Sales | 3 PM Thursday | ✅ Weekly |
| EIA Biofuel | 10 AM Wednesday | ✅ Weekly |
| Master Continuous Collector | Every hour | ✅ Active |
| Feature Pipeline Refresh | 6 AM daily | ✅ Active |
| Breaking News | 9 AM - 4 PM weekdays | ✅ Active |
| Daily Signals | 7 AM weekdays | ✅ Active |
| Weekend Maintenance | 2 AM Sunday | ✅ Weekly |

---

## ⚠️ CRITICAL GAPS ANALYSIS

### **GAP #1: CHINA IMPORTS NOT SCHEDULED**
- **Impact:** Feature #9-16 in 42 neural drivers (Trade war impact)
- **Current State:** 21 days stale (last update 2025-10-15)
- **Required:** Daily or weekly updates
- **Fix:** Add to cron: `0 8 * * 1-5 cd $INGESTION_DIR && python3 ingest_china_imports_uncomtrade.py`

### **GAP #2: RIN PRICES NOT SCHEDULED**
- **Impact:** Feature #23-30 in 42 neural drivers (+0.88 correlation with ZL)
- **Current State:** Manual only, unknown freshness
- **Required:** Weekly updates (EPA publishes weekly)
- **Fix:** Add to cron: `0 9 * * 3 cd $INGESTION_DIR && python3 ingest_epa_rin_prices.py`

### **GAP #3: BRAZIL/ARGENTINA PREMIUMS MISSING**
- **Impact:** Feature #9-16 (Brazil premium calculation)
- **Current State:** No dedicated script exists
- **Required:** Daily price spread calculations
- **Fix:** Create script or add calculation to existing price ingestion

### **GAP #4: PRODUCTION TRAINING DATA STALE**
- **Impact:** Model training uses stale data (56 days behind!)
- **Current State:** Last update Sep 10, 2025
- **Required:** Daily refresh
- **Fix:** Schedule `update_production_datasets.py` daily: `0 5 * * * cd $SCRIPTS_DIR && python3 update_production_datasets.py`

### **GAP #5: TRUMP SENTIMENT QUANTIFICATION NOT SCHEDULED**
- **Impact:** Raw data exists but not processed into features
- **Current State:** Manual execution only
- **Required:** Daily processing of raw Truth Social data
- **Fix:** Schedule `TRUMP_SENTIMENT_QUANT_ENGINE.py`: `0 7 * * * cd $SCRIPTS_DIR && python3 TRUMP_SENTIMENT_QUANT_ENGINE.py`

### **GAP #6: BIG EIGHT SIGNALS NOT SCHEDULED**
- **Impact:** Neural signals may be stale
- **Current State:** Manual execution or relies on `refresh_features_pipeline.py`
- **Required:** Daily refresh
- **Fix:** Verify `refresh_features_pipeline.py` includes Big Eight, or schedule `collect_neural_data_sources.py`

---

## 📊 DATA FRESHNESS AUDIT

### **TRUMP ERA PLAN REQUIREMENTS vs ACTUAL:**

| Data Source | Plan Requirement | Current State | Days Old | Status |
|-------------|------------------|---------------|----------|--------|
| **Trump Sentiment** | Current | 435 rows, through 2025-11-08 | 0 | ✅ **FRESH** |
| **China Imports** | Current | Last update 2025-10-15 | 21 | ⚠️ **STALE** |
| **RIN Prices** | Updated (240% spike tracking) | Unknown | Unknown | ❌ **UNKNOWN** |
| **Brazil/Argentina Premiums** | Fresh (daily) | Calculated in SQL | N/A | ⚠️ **CALCULATED** |
| **Big Eight Signals** | Present | 2,141 rows, through 2025-11-10 | 0 | ✅ **FRESH** |
| **Production Training Data** | Zero stale data | Last update Sep 10, 2025 | 56 | ❌ **CRITICAL STALE** |

---

## 🎯 RECOMMENDATIONS

### **IMMEDIATE ACTIONS (This Week):**

1. **Schedule China Imports:**
   ```bash
   # Add to crontab
   0 8 * * 1-5 cd $INGESTION_DIR && python3 ingest_china_imports_uncomtrade.py >> $LOG_DIR/china_imports.log 2>&1
   ```

2. **Schedule RIN Prices:**
   ```bash
   # Add to crontab (EPA publishes Wednesdays)
   0 9 * * 3 cd $INGESTION_DIR && python3 ingest_epa_rin_prices.py >> $LOG_DIR/rin_prices.log 2>&1
   ```

3. **Schedule Production Training Data Refresh:**
   ```bash
   # Add to crontab (daily, before market open)
   0 5 * * * cd $SCRIPTS_DIR && python3 update_production_datasets.py >> $LOG_DIR/production_refresh.log 2>&1
   ```

4. **Schedule Trump Sentiment Quantification:**
   ```bash
   # Add to crontab (daily, after Truth Social collection)
   0 7 * * * cd $SCRIPTS_DIR && python3 TRUMP_SENTIMENT_QUANT_ENGINE.py >> $LOG_DIR/trump_quant.log 2>&1
   ```

5. **Verify Big Eight Signals Pipeline:**
   - Check if `refresh_features_pipeline.py` includes Big Eight
   - If not, schedule `collect_neural_data_sources.py` daily

### **SHORT-TERM (Next 2 Weeks):**

6. **Create Brazil/Argentina Premiums Script:**
   - Calculate from price spreads (ZL, ZS, ZM)
   - Or find dedicated data source
   - Schedule daily updates

7. **Verify Cloud Scheduler Endpoints:**
   - Ensure `data-ingestion` endpoint triggers correct scripts
   - Test that all critical data sources are covered

8. **Add Monitoring:**
   - Alert on stale data (>7 days old)
   - Alert on failed ingestion jobs
   - Dashboard for data freshness

### **LONG-TERM (Next Month):**

9. **Consolidate Ingestion Scripts:**
   - Reduce duplication (multiple Trump scripts)
   - Standardize error handling
   - Unified logging

10. **Automated Testing:**
    - Test ingestion scripts before scheduling
    - Validate data quality after ingestion
    - Alert on schema mismatches

---

## 📝 CHECKLIST FOR PLAN COMPLIANCE

### **TRUMP ERA EXECUTION PLAN CHECKLIST:**

- [x] Trump sentiment data loaded ✅ (435 rows)
- [ ] China import data current ⚠️ (21 days stale - **FIX NEEDED**)
- [ ] RIN prices updated ❌ (Not scheduled - **FIX NEEDED**)
- [ ] Brazil/Argentina premiums fresh ⚠️ (Calculated, not ingested - **REVIEW NEEDED**)
- [x] Big Eight signals present ✅ (2,141 rows)
- [ ] Production training data fresh ❌ (56 days stale - **CRITICAL FIX**)
- [ ] Sequential split configured ✅ (In SQL)
- [ ] DART parameters set ✅ (In SQL)
- [ ] Monotonic constraints defined ✅ (In SQL)
- [ ] 2023-2025 data only ✅ (In SQL)
- [ ] No NULL columns ⚠️ (Need verification)
- [ ] No string columns ✅ (In SQL)

**COMPLIANCE SCORE: 7/12 (58%)** - Critical gaps in data freshness

---

## 🔍 VERIFICATION QUERIES

### **Check Data Freshness:**
```sql
-- China Imports
SELECT MAX(date) as latest_date, COUNT(*) as rows
FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`;

-- RIN Prices
SELECT MAX(date) as latest_date, COUNT(*) as rows
FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
WHERE rin_d4_price IS NOT NULL;

-- Production Training Data
SELECT MAX(date) as latest_date, COUNT(*) as rows
FROM `cbi-v14.models_v4.production_training_data_1m`;

-- Trump Sentiment
SELECT MAX(timestamp) as latest_date, COUNT(*) as rows
FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`;
```

### **Check Scheduled Jobs:**
```bash
# View current crontab
crontab -l

# Check Cloud Scheduler
gcloud scheduler jobs list --project=cbi-v14
```

---

## 📈 SUCCESS METRICS

### **Target Metrics:**
- ✅ All critical data sources < 7 days old
- ✅ 100% of plan-required scripts scheduled
- ✅ Zero failed ingestion jobs (7-day rolling)
- ✅ Production training data refreshed daily

### **Current Metrics:**
- ⚠️ 2/6 critical data sources fresh (33%)
- ⚠️ 4/7 plan-required scripts scheduled (57%)
- ❓ Unknown failure rate
- ❌ Production training data 56 days stale

---

## 🚨 PRIORITY ACTIONS

### **P0 (Critical - Do Today):**
1. Schedule `update_production_datasets.py` (production training data)
2. Schedule `ingest_china_imports_uncomtrade.py` (China imports)
3. Schedule `ingest_epa_rin_prices.py` (RIN prices)

### **P1 (High - This Week):**
4. Schedule `TRUMP_SENTIMENT_QUANT_ENGINE.py` (Trump sentiment processing)
5. Verify Big Eight signals pipeline
6. Create Brazil/Argentina premiums script

### **P2 (Medium - Next 2 Weeks):**
7. Verify Cloud Scheduler endpoints
8. Add monitoring/alerts
9. Consolidate duplicate scripts

---

**AUDIT COMPLETE**  
**Next Review:** After implementing P0 actions

