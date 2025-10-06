# CBI-V14 Complete Data Pipeline Scaffold Plan

**Last Updated:** 2025-10-06  
**Status:** PRE-TRAINING - All pipelines must be operational before model training

---

## 🎯 Core Principle
**No model training until all data sources are properly piped, tested, and validated.**

---

## 📊 Current State Audit

### ✅ Working Pipelines (Data Exists)

| Source | Table | Rows | Coverage | Script | Status |
|--------|-------|------|----------|--------|--------|
| **ZL Prices** | `soybean_oil_prices` | 519 | 100% (Sep 2023 - Oct 2025) | `ingest_zl_futures.py` | ✅ OPERATIONAL |
| **Weather US** | `weather_data` (region=US) | 2,672 | 89% | `ingest_weather_noaa.py` | ✅ OPERATIONAL |
| **Weather Argentina** | `weather_data` (region=Argentina) | 1,342 | 39% | `ingest_weather_noaa.py` | ⚠️ NEEDS BACKFILL |
| **Economic Indicators** | `economic_indicators` | 3,220 | Unknown | `economic_intelligence.py` | ✅ HAS DATA |
| **Treasury Prices** | `treasury_prices` | 136 | 26% | `load_barchart.py` | ⚠️ SPARSE |
| **Volatility Data** | `volatility_data` | 2 | 0.2% | `ingest_volatility.py` | ❌ NEARLY EMPTY |
| **News Intelligence** | `news_intelligence` | 10 | Test data only | `multi_source_news.py` | ⚠️ NOT RUN AT SCALE |

### ❌ Empty Pipelines (No Data Yet)

| Source | Table | Rows | Script | Status |
|--------|-------|------|--------|--------|
| **Weather Brazil** | `weather_data` (region=Brazil) | 0 | `ingest_weather_noaa.py` | ❌ MISSING |
| **Social Sentiment** | `social_sentiment` | 0 | `social_intelligence.py` | ❌ NOT RUN |
| **Shipping Alerts** | `shipping_alerts` | 0 | `shipping_intelligence.py` | ❌ NOT RUN |
| **ICE/Trump Intel** | `ice_trump_intelligence` | 0 | `ice_trump_intelligence.py` | ❌ NOT RUN |
| **Currency Data** | `currency_data` | 0 | `economic_intelligence.py` | ❌ NOT RUN |

---

## 🗺️ Complete Data Architecture Map

### Layer 1: Core Price Data (Foundation)
```
[Barchart CSV] → soybean_oil_prices (ZL futures) ✅ DONE
[Barchart CSV] → treasury_prices (ZN 10Y) ⚠️ SPARSE
[Barchart CSV] → volatility_data (VIX/VXSLV) ❌ NEEDS FIX
```

### Layer 2: Weather & Climate (Critical Predictors)
```
[NOAA API] → weather_data
  ├── US (Iowa, Illinois) ✅ 2,672 rows
  ├── Argentina (Buenos Aires, Rosario) ⚠️ 1,342 rows (needs backfill)
  └── Brazil (Mato Grosso, MS) ❌ 0 rows (BLOCKED - needs fix)
```

### Layer 3: Economic Intelligence (Macro Factors)
```
[FRED API] → economic_indicators ✅ 3,220 rows
  ├── 10Y Treasury Yield
  ├── USD Index
  ├── Fed Funds Rate
  ├── Crude Oil WTI
  ├── USD/CNY (China demand)
  ├── USD/BRL (Brazil export)
  ├── USD/ARS (Argentina export)
  └── CPI Inflation

[Yahoo Finance / FRED] → currency_data ❌ 0 rows
  ├── USD/BRL (Brazil competitiveness)
  ├── USD/ARS (Argentina competitiveness)
  ├── USD/CNY (China buying power)
  └── DXY (Dollar strength)
```

### Layer 4: News & Policy Intelligence (Event Signals)
```
[Multi-Source Scraping] → news_intelligence ⚠️ 10 rows (test only)
  ├── China demand (COFCO, Sinograin, imports)
  ├── Brazil policy (CONAB, export taxes, Ferrogrão)
  ├── Argentina policy (sojadólar, retenciones, strikes)
  ├── US policy (USDA, Farm Bill, RFS)
  ├── Biofuel policy (B40, RenovaBio, EPA RVO)
  ├── Palm oil competition (Malaysia, Indonesia)
  ├── Weather events (drought, La Niña)
  └── Trade wars (tariffs, WTO)

[ICE.gov / DHS] → ice_trump_intelligence ❌ 0 rows
  ├── Immigration enforcement (farm labor)
  ├── H-2A visa restrictions
  └── Agricultural worker availability

[Social APIs] → social_sentiment ❌ 0 rows
  ├── Reddit r/agriculture
  ├── Twitter agricultural hashtags
  └── Farmer sentiment indicators
```

### Layer 5: Logistics & Trade Flow (Supply Chain)
```
[Shipping APIs / Scraping] → shipping_alerts ❌ 0 rows
  ├── Panama Canal (water levels, transit times)
  ├── Brazilian ports (Santos, Paranaguá congestion)
  ├── Argentine ports (Rosario strikes)
  ├── US Gulf ports (New Orleans, Houston)
  └── Freight rates (Baltic Exchange)
```

### Layer 6: Aggregation Views (Feature Engineering)
```
Raw Tables → Daily Aggregation Views
  ├── vw_weather_daily (US + AR + BR precip/temp) ⚠️ BR=0
  ├── vw_economic_daily (yields, FX, inflation) ✅
  ├── vw_treasury_daily (10Y yields) ✅
  ├── vw_volatility_daily (implied vol) ⚠️ Nearly empty
  ├── vw_news_intel_daily (sentiment scores) ⚠️ No data
  ├── vw_social_daily (social sentiment) ❌ Empty
  ├── vw_ice_trump_daily (enforcement events) ❌ Empty
  └── vw_shipping_daily (disruption alerts) ❌ Empty

Aggregation Views → Master Features
  └── vw_zl_features_daily (519 rows, combines all) ⚠️ INCOMPLETE
```

---

## 🔧 Execution Plan (Sequential Phases)

### Phase 1: Fix Critical Gaps (Week 1)
**Goal:** Get all foundational data flowing

#### 1.1 Fix Brazil Weather (High Priority)
- **Issue:** NOAA API has BR stations but 0 rows loaded
- **Script:** `ingest_weather_noaa.py`
- **Action:**
  ```bash
  # Debug why Brazil stations return 0 rows
  python3 cbi-v14-ingestion/ingest_weather_noaa.py --backfill --years 2
  # May need to add more BR station IDs or use alternative source
  ```
- **Success Criteria:** ≥1,000 Brazil weather rows

#### 1.2 Backfill Argentina Weather
- **Issue:** Only 39% coverage (1,342 rows vs 2,672 US)
- **Action:**
  ```bash
  python3 cbi-v14-ingestion/ingest_weather_noaa.py --backfill --years 2
  ```
- **Success Criteria:** ≥2,000 Argentina rows (match US coverage)

#### 1.3 Fix Volatility Data
- **Issue:** Only 2 rows (0.2% coverage)
- **Script:** `ingest_volatility.py`
- **Action:** Debug why volatility ingestion is nearly empty
- **Success Criteria:** ≥400 volatility rows (daily data)

#### 1.4 Expand Treasury Data
- **Issue:** Only 26% coverage (136 rows)
- **Script:** `load_barchart.py`
- **Action:** Backfill treasury prices to match ZL date range
- **Success Criteria:** ≥450 treasury rows (match ZL coverage)

**Phase 1 Validation:**
```sql
-- All core regressors should have ≥80% coverage
SELECT 
  COUNT(*) total,
  COUNTIF(y_close IS NOT NULL) / COUNT(*) * 100 as zl_pct,
  COUNTIF(yield_10y IS NOT NULL) / COUNT(*) * 100 as treasury_pct,
  COUNTIF(implied_vol IS NOT NULL) / COUNT(*) * 100 as vol_pct,
  COUNTIF(us_precip_mm IS NOT NULL) / COUNT(*) * 100 as us_weather_pct,
  COUNTIF(ar_precip_mm IS NOT NULL) / COUNT(*) * 100 as ar_weather_pct
FROM `cbi-v14.forecasting_data_warehouse.vw_zl_features_daily`;
-- TARGET: All ≥80%
```

---

### Phase 2: Intelligence Collection (Week 2)
**Goal:** Add event-driven signals

#### 2.1 News Intelligence (16 Categories)
- **Script:** `multi_source_news.py`
- **Sources:** 50+ monitored (Reuters, USDA, CONAB, ABIOVE, etc.)
- **Action:**
  ```bash
  # Run initial collection
  python3 cbi-v14-ingestion/multi_source_news.py
  
  # Set up daily cron (15-minute intervals)
  # Monitors: China demand, Brazil/Argentina policy, biofuel, weather, trade
  ```
- **Success Criteria:** ≥1,000 news articles collected, ≥14 categories covered

#### 2.2 Social Sentiment
- **Script:** `social_intelligence.py`
- **Sources:** Reddit r/agriculture, Twitter agricultural hashtags
- **Action:**
  ```bash
  python3 cbi-v14-ingestion/social_intelligence.py
  ```
- **Success Criteria:** ≥500 social signals collected

#### 2.3 ICE/Trump Enforcement
- **Script:** `ice_trump_intelligence.py`
- **Sources:** ICE.gov, DHS press releases, farm labor news
- **Action:**
  ```bash
  python3 cbi-v14-ingestion/ice_trump_intelligence.py
  ```
- **Success Criteria:** ≥50 enforcement events cataloged

#### 2.4 Shipping & Logistics
- **Script:** `shipping_intelligence.py`
- **Sources:** Panama Canal, port congestion, freight rates
- **Action:**
  ```bash
  python3 cbi-v14-ingestion/shipping_intelligence.py
  ```
- **Success Criteria:** ≥100 shipping alerts collected

**Phase 2 Validation:**
```sql
-- Verify intelligence tables populated
SELECT 
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`) as news,
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`) as social,
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.ice_trump_intelligence`) as ice,
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.shipping_alerts`) as shipping;
-- TARGET: All ≥50 rows
```

---

### Phase 3: Features View Rebuild (Week 2-3)
**Goal:** Combine all sources into training-ready view

#### 3.1 Rebuild vw_zl_features_daily_all
- Add all intelligence sources to features view
- Use explicit ON joins (no USING ambiguity)
- COALESCE event counts to 0 for missing data

```sql
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_zl_features_daily_all` AS
WITH base AS (
  SELECT DATE(time) AS date, 'ZL' AS symbol, close AS y_close
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol='ZL'
)
SELECT
  b.date, b.symbol, b.y_close,
  
  -- Economic factors
  e.yield_10y, e.dollar_index, e.fed_funds_rate, e.crude_oil_wti,
  e.usd_cny_rate, e.usd_brl_rate, e.usd_ars_rate, e.cpi_inflation,
  
  -- Market factors
  v.implied_vol,
  
  -- Weather (3 regions)
  w_us.precip_mm_avg AS us_precip_mm,
  w_ar.precip_mm_avg AS ar_precip_mm,
  w_br.precip_mm_avg AS br_precip_mm,
  
  -- Intelligence signals (event counts + scores)
  COALESCE(n.news_count, 0) AS news_count,
  n.news_score, n.news_brazil_score, n.news_china_score,
  
  COALESCE(s.social_count, 0) AS social_count,
  s.social_score,
  
  COALESCE(it.ice_trump_events, 0) AS ice_trump_events,
  COALESCE(it.ice_enforcement_events, 0) AS ice_enforcement_events,
  
  COALESCE(sh.shipping_alerts, 0) AS shipping_alerts,
  COALESCE(sh.shipping_congestion, 0) AS shipping_congestion

FROM base b
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_economic_daily` e 
  ON e.date = b.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_volatility_daily` v 
  ON v.date = b.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_weather_daily` w_us 
  ON w_us.date = b.date AND w_us.region = 'US'
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_weather_daily` w_ar 
  ON w_ar.date = b.date AND w_ar.region = 'Argentina'
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_weather_daily` w_br 
  ON w_br.date = b.date AND w_br.region = 'Brazil'
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_news_intel_daily` n 
  ON n.date = b.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_social_daily` s 
  ON s.date = b.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_ice_trump_daily` it 
  ON it.date = b.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vw_shipping_daily` sh 
  ON sh.date = b.date;
```

#### 3.2 Final Coverage Check
```sql
SELECT
  COUNT(*) as total_rows,
  -- Core features (TARGET: ≥80%)
  COUNTIF(yield_10y IS NOT NULL) / COUNT(*) * 100 as treasury_pct,
  COUNTIF(implied_vol IS NOT NULL) / COUNT(*) * 100 as vol_pct,
  COUNTIF(us_precip_mm IS NOT NULL) / COUNT(*) * 100 as us_weather_pct,
  COUNTIF(ar_precip_mm IS NOT NULL) / COUNT(*) * 100 as ar_weather_pct,
  COUNTIF(br_precip_mm IS NOT NULL) / COUNT(*) * 100 as br_weather_pct,
  -- Intelligence features (TARGET: ≥50%, OK if sparse for events)
  COUNTIF(news_count > 0) / COUNT(*) * 100 as news_coverage_pct,
  COUNTIF(social_count > 0) / COUNT(*) * 100 as social_coverage_pct,
  COUNTIF(ice_trump_events > 0) / COUNT(*) * 100 as ice_coverage_pct,
  COUNTIF(shipping_alerts > 0) / COUNT(*) * 100 as shipping_coverage_pct,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.forecasting_data_warehouse.vw_zl_features_daily_all`;
```

**Phase 3 Success Criteria:**
- Total rows: ≥500 (Sep 2023 - Oct 2025)
- Core features: ≥80% coverage each
- Intelligence features: ≥50% coverage each
- Zero schema errors, all views queryable

---

### Phase 4: Continuous Collection Setup (Week 3)
**Goal:** Automate daily updates

#### 4.1 Cron Jobs (Google Cloud Scheduler)
```bash
# Daily at 6 AM UTC (after market close)
0 6 * * * python3 /path/to/ingest_zl_futures.py
0 6 * * * python3 /path/to/ingest_weather_noaa.py --days 7
0 6 * * * python3 /path/to/economic_intelligence.py

# Every 15 minutes during trading hours (13:30-20:00 UTC)
*/15 13-20 * * * python3 /path/to/multi_source_news.py
*/15 13-20 * * * python3 /path/to/social_intelligence.py

# Hourly for logistics
0 * * * * python3 /path/to/shipping_intelligence.py
0 * * * * python3 /path/to/ice_trump_intelligence.py
```

#### 4.2 Monitoring & Alerts
- Set up email alerts for ingestion failures
- Dashboard for pipeline health
- Daily data quality checks

---

### Phase 5: Model Training (Week 4+)
**⚠️ DO NOT START UNTIL PHASES 1-3 COMPLETE**

Only proceed when:
1. ✅ All core features ≥80% coverage
2. ✅ Brazil weather operational
3. ✅ Intelligence tables populated (≥50 rows each)
4. ✅ Features view rebuilt and validated
5. ✅ Zero schema errors

Then and only then:
```sql
-- Baseline ARIMA (price only)
CREATE OR REPLACE MODEL `cbi-v14.forecasting_data_warehouse.zl_arima_baseline`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='y_close'
) AS
SELECT date, y_close
FROM `cbi-v14.forecasting_data_warehouse.vw_zl_features_daily_all`;

-- Multivariate ARIMA (all features)
CREATE OR REPLACE MODEL `cbi-v14.forecasting_data_warehouse.zl_arima_xreg`
OPTIONS(
  model_type='ARIMA_PLUS_XREG',
  time_series_timestamp_col='date',
  time_series_data_col='y_close'
) AS
SELECT * EXCEPT (symbol)
FROM `cbi-v14.forecasting_data_warehouse.vw_zl_features_daily_all`
WHERE date >= '2023-09-01';  -- Only use data with good coverage
```

---

## 📋 Checklist (Complete Before Training)

### Data Ingestion
- [ ] Brazil weather: ≥1,000 rows
- [ ] Argentina weather: ≥2,000 rows (backfill)
- [ ] Volatility data: ≥400 rows (fix ingestion)
- [ ] Treasury data: ≥450 rows (backfill)
- [ ] Economic indicators: Validated (already 3,220 rows)
- [ ] News intelligence: ≥1,000 articles
- [ ] Social sentiment: ≥500 signals
- [ ] ICE/Trump: ≥50 events
- [ ] Shipping alerts: ≥100 alerts

### Views & Schema
- [ ] vw_economic_daily: Working (already ✅)
- [ ] vw_weather_daily: Add Brazil region
- [ ] vw_news_intel_daily: Create after news collection
- [ ] vw_social_daily: Create after social collection
- [ ] vw_ice_trump_daily: Create after ICE collection
- [ ] vw_shipping_daily: Create after shipping collection
- [ ] vw_zl_features_daily_all: Rebuild with all sources
- [ ] Final coverage check: All ≥80% (core), ≥50% (intelligence)

### Automation
- [ ] Daily ingestion cron jobs set up
- [ ] 15-minute intelligence monitoring
- [ ] Pipeline health dashboard
- [ ] Email alerts for failures

### Documentation
- [ ] Update CURSOR_RULES.md with new schemas
- [ ] Document each intelligence source
- [ ] Create runbook for pipeline failures
- [ ] API key management documented

---

## 🚨 Critical Dependencies

### External APIs Required
- ✅ NOAA (weather): Token in code
- ✅ FRED (economic): Needs API key
- ⚠️ Barchart (prices): Manual CSV for now
- ❌ News sources: Scraping (no API keys needed)
- ❌ Social APIs: Reddit/Twitter need tokens
- ❌ Shipping: Scraping + possible API keys

### BigQuery Costs (Estimate)
- Ingestion: ~$5/day (batch loads)
- Views: ~$1/day (aggregations)
- Training: ~$50/model (one-time)
- Forecasting: ~$0.10/run

**Budget:** $200/month for full operation

---

## 📊 Success Metrics

### Data Quality
- Coverage: ≥80% for core features
- Freshness: Data ≤24 hours old
- Accuracy: Spot checks monthly
- Completeness: All 16 intelligence categories

### Pipeline Reliability
- Uptime: ≥99% (ingestion success rate)
- Latency: Updates within 1 hour of source
- Failures: ≤1% of runs fail

### Model Readiness
- Training data: ≥450 days with full features
- Feature count: ≥20 regressors
- Date range: Sep 2023 - current
- No null-only columns

---

## 🎯 Next Immediate Actions (This Week)

1. **Debug Brazil weather** (2 hours)
   - Check NOAA station IDs for Brazil
   - Test API response
   - Fix ingestion script if needed

2. **Backfill Argentina weather** (1 hour)
   - Run backfill command
   - Verify 2,000+ rows

3. **Fix volatility ingestion** (2 hours)
   - Debug why only 2 rows
   - Check source data
   - Re-run ingestion

4. **Run news collector** (30 minutes)
   - Test multi_source_news.py
   - Verify 1,000+ articles
   - Check 14+ categories

5. **Coverage validation** (15 minutes)
   - Run final coverage check
   - Document gaps
   - Prioritize remaining work

**Total Time Estimate:** 6-8 hours to complete Phase 1

---

## 📝 Notes

- All ingestion scripts use `safe_load_to_bigquery` for batching
- Views are free to query (no scanning cost)
- Archive old tables (milk, commodity_prices) for cleanup
- Master controller can run all intelligence in parallel
- Focus on Brazil: 50% of global soybean production

---

**Status:** Phase 0 (Planning) → Ready to start Phase 1  
**Next Review:** After Phase 1 completion (coverage validation)

