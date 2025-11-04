# NULL AUDIT & ELIMINATION STRATEGY

**Date:** November 3, 2025  
**Audit Scope:** training_dataset_super_enriched (2,045 rows, 2020-2025)  
**Total Columns with NULLs:** 259  
**HIGH-NULL Columns (>50%):** 30

---

## AUDIT RESULTS

### 🔴 ELIMINATED (by copying from existing columns):
- ✅ `brazil_temp_c` (was 50.66% NULL → now 23% NULL) - copied from `brazil_temperature_c`
- ✅ `argentina_temp_c` (was 86.60% NULL → now 34% NULL) - copied from `weather_argentina_temp`
- ✅ `brazil_precip_mm` (partially filled)
- ✅ `brazil/argentina heat_stress/drought/flood_days` (calculated from temp/precip)

**Affected rows:** 1,571 rows updated

---

## 🔴 REMAINING 30 HIGH-NULL COLUMNS

### Category 1: CFTC Data (7 columns, 97% NULL)
- `cftc_commercial_long/short/net`
- `cftc_managed_long/short/net`
- `cftc_open_interest`

**Source:** ✅ `cbi-v14-ingestion/ingest_cftc_positioning.py` EXISTS  
**Status:** ✅ WORKING (just ran - loaded 3 records)  
**Issue:** Only has 60 weeks of data, need 2020-2025 (260+ weeks)  
**Solution:** Run historical backfill, then weekly cron  
**Cron:** Already exists in `enhanced_cron_setup.sh` (Fridays 5pm)

### Category 2: Economic Data (6 columns, 96-99% NULL)
- `econ_gdp_growth` (99.46% NULL)
- `econ_inflation_rate` (99.12% NULL)
- `econ_unemployment_rate` (96.48% NULL)
- `gdp_growth` (99.46% NULL - duplicate)
- `unemployment_rate` (99.46% NULL - duplicate)
- `cpi_yoy` (99.46% NULL)

**Source:** ✅ `scripts/fetch_fred_economic_data.py` EXISTS  
**Status:** ❌ FRED API key missing/invalid  
**Alternative:** yfinance for ^GSPC, calculate proxies from market data  
**Solution:** 
  - Option A: Get proper FRED API key
  - Option B: Use yfinance economic indicators
  - Option C: Keep in EXCEPT (accept we can't use these features)

### Category 3: US Midwest Weather (6 columns, 99% NULL)
- `us_midwest_temp_c/precip_mm`
- `us_midwest_conditions_score`
- `us_midwest_heat_stress/drought/flood_days`

**Source:** ✅ `cbi-v14-ingestion/ingest_midwest_weather_openmeteo.py` EXISTS  
**Status:** ✅ WORKING (just ran - loaded 495 records)  
**Issue:** Data goes to `staging.weather_midwest_openmeteo`, not training table  
**Solution:** Create ETL to aggregate staging → training_dataset_super_enriched

### Category 4: News Data (2 columns, 99% NULL)
- `news_article_count`
- `news_avg_score`

**Source:** ✅ Existing news tables (news_reuters, news_farmprogress, news_brownfield)  
**Status:** ✅ Tables exist with data  
**Solution:** Aggregate by date and UPDATE training table

### Category 5: Trump Intelligence (5 columns, 98-99% NULL)
- `trump_soybean_sentiment_7d`
- `trump_agricultural_impact_30d`
- `trump_soybean_relevance_30d`
- `days_since_trump_policy`
- `trump_policy_intensity_14d`

**Source:** ✅ `cbi-v14-ingestion/backfill_trump_intelligence.py` EXISTS  
**Status:** ⚠️ Uses wrong ScrapeCreators endpoint (/twitter/user/posts vs /twitter/user-tweets)  
**Solution:** Fix endpoint, run historical backfill

### Category 6: Social Sentiment (1 column, 99% NULL)
- `social_sentiment_momentum_7d`

**Source:** ✅ Existing `social_sentiment` table (653 records)  
**Solution:** Calculate 7-day momentum from social_sentiment table

### Category 7: Argentina Precipitation (1 column, 85% NULL)
- `argentina_precip_mm`

**Source:** Check if data exists in weather tables  
**Solution:** Query weather_argentina_precip or calculate/estimate

### Category 8: Return Data (1 column, 51% NULL)
- `return_1d`

**Source:** Calculate from `zl_price_current`  
**Solution:** Create temp table with LAG calculation, then MERGE

### Category 9: Global Weather Risk (1 column, 50% NULL)
- `global_weather_risk_score`

**Source:** Calculate from brazil + argentina + us_midwest weather  
**Solution:** Composite calculation

---

## EXECUTION PLAN

### ✅ STEP 1: COMPLETED
- Copied from existing columns (brazil/argentina weather)
- Calculated derived features
- **Result:** Reduced high-NULL from 41 → 30 columns

### 🔄 STEP 2: RUN EXISTING INGEST SCRIPTS
```bash
# CFTC (historical backfill needed)
python3 cbi-v14-ingestion/ingest_cftc_positioning.py --historical --start-date 2020-01-01

# US Midwest weather (already ran - 495 records)
# Need ETL to move from staging → training

# News aggregation (calculate from existing tables)
# Run SQL to aggregate news_* tables by date

# Trump intelligence (fix endpoint first)
# Fix backfill_trump_intelligence.py endpoint
# Then run historical

# Social sentiment momentum (calculate from existing)
# Query social_sentiment table, calculate rolling 7d
```

### ⏳ STEP 3: SETUP CRONS (using existing cron file)
**File:** `scripts/enhanced_cron_setup.sh`

**Add:**
- Midwest weather: Daily 6am
- News aggregation: Daily 8am  
- Trump intelligence: Daily 7am (with ScrapeCreators)
- CFTC: Weekly Friday 5pm (already exists)

### ⏳ STEP 4: DEEP TRAINING AUDIT
- Verify all NULLs handled
- Check temporal leakage
- Check label leakage
- Validate SQL syntax

### ⏳ STEP 5: TRAIN
- Run `execute_phase_1.py`

---

**CURRENT STATUS: 30 high-NULL columns remain, most have existing data sources/scripts**

**Next action: Fix existing scripts and run them, or keep columns in EXCEPT and train now?**


