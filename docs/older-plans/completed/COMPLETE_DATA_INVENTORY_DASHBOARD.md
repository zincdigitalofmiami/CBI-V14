# CBI-V14 Dashboard Blueprint - Complete Data Inventory & Features

**Date:** November 4, 2025  
**Status:** Complete Inventory of All Available Data  
**Purpose:** Dashboard development reference

---

## PART 1: CHRIS STACY'S PRIORITY REQUIREMENTS

**Client:** US Oil Solutions (Chris Stacy)

**Three Critical Dashboard Priority Areas:**

### 1. China Purchases/Cancellations (Medium-term price driver)
- China import data tracking
- Purchase cancellations monitoring
- Trade relationship indicators
- Import diversification signals

### 2. Harvest Updates from Brazil/Argentina/US (Short-term volatility driver)
- Real-time harvest progress
- Weather impact on yields
- Production vs trend analysis
- Supply-side fundamentals

### 3. Biofuel Markets (EPA RFS, Biodiesel Mandates) (Long-term trend driver)
- RFS volume announcements
- Biodiesel blend mandates
- Renewable diesel margins
- Policy impact on demand

---

## PART 2: KEVIN'S VEGAS INTEL PAGE INTEGRATION

**Vegas Intel Page Purpose:**
- Real-time market intelligence dashboard
- Live forecast updates
- Signal strength indicators
- Market regime classifications
- Crisis intensity scores
- Breaking news overlays

**Forecast Integration Points:**
- Forecast Confidence Scores (45-75% based on crisis intensity)
- Regime-Based Forecasts (different forecasts for different market regimes)
- Signal-Driven Adjustments (forecast adjustments based on Big 8 signal strength)
- Crisis Overrides (when crisis flags trigger, show adjusted forecasts)
- Historical Accuracy (MAPE metrics by regime type)

**Data Flow:**
- `cbi-v14.predictions_uc1.production_forecasts`
- `cbi-v14.api.vw_big8_composite_signal`
- Market regime classification
- Crisis intensity scores
- Forecast confidence percentages

---

## PART 3: COMPLETE DATA INVENTORY

### 3.1 Core Price & Market Data Tables

**Primary Sources:**
- `soybean_oil_prices` - Main ZL futures prices (timestamp, close, volume, open_interest)
- `palm_oil_prices` - Palm oil futures (substitution indicator)
- `crude_oil_prices` - Crude oil correlation data
- `corn_prices` - Corn correlation (soybean relationship)
- `wheat_prices` - Wheat correlation
- `soybean_prices` - Bean prices (crush margin calculation)
- `soybean_meal_prices` - Meal prices (crush margin)
- `canola_oil_prices` - Canola substitution
- `rapeseed_oil_prices` - Rapeseed substitution
- `cocoa_prices` - Soft commodity correlation
- `cotton_prices` - Agricultural correlation
- `gold_prices` - Macro correlation
- `natural_gas_prices` - Energy correlation
- `sp500_prices` - Equity correlation
- `treasury_prices` - Fixed income correlation
- `usd_index_prices` - Dollar strength (DXY)
- `vix_daily` - Volatility index (VIX stress signal)

**Futures Market Data:**
- `futures_prices_barchart` - Barchart forward curve data
- `futures_prices_marketwatch` - MarketWatch futures data
- `futures_prices_investing` - Investing.com futures data
- `futures_prices_cme_public` - CME public settlement prices
- `futures_sentiment_tradingview` - Trader sentiment (bullish/bearish %)

**Realtime Data:**
- `realtime_prices` - Live price feeds
- `volatility_data` - Volatility metrics

### 3.2 Fundamental & Trade Data

**China Trade Intelligence:**
- `china_soybean_imports` - Monthly import data (MT)
- `argentina_china_sales_mt` - Argentina-China trade
- `usda_export_sales` - USDA export sales reports
- `china_imports_from_us_mt` - US-China trade specific

**Supply Fundamentals:**
- `usda_harvest_progress` - Harvest progress by region
- `usda_wasde_soy` - WASDE report data
- `ers_oilcrops_monthly` - ERS monthly oilcrops reports
- `argentina_crisis_tracker` - Argentina crisis indicators

**Weather Data:**
- `weather_data` - Raw weather observations
- `weather_brazil_daily` - Brazil daily weather
- `weather_argentina_daily` - Argentina daily weather
- `weather_us_midwest_daily` - US Midwest daily weather
- `weather_brazil_clean` - Cleaned Brazil weather
- `weather_us_midwest_clean` - Cleaned US Midwest weather
- `enso_climate_status` - ENSO phase indicators

### 3.3 Policy & Intelligence Data

**Policy Intelligence:**
- `trump_policy_intelligence` - Trump policy signals (215 records)
- `biofuel_policy` - Biofuel policy tracking
- `policy_rfs_volumes` - RFS volume announcements
- `policy_events_federalregister` - Federal Register policy events
- `legislative_bills` - Congressional bills tracking

**Social & Sentiment:**
- `social_sentiment` - Social media sentiment
- `social_intelligence_unified` - Unified social intelligence
- `news_intelligence` - News intelligence (2,705 records)
- `news_advanced` - Advanced news analysis
- `news_industry_brownfield` - Industry news (Brownfield)
- `news_market_farmprogress` - Market news (Farm Progress)
- `news_reuters` - Reuters news
- `news_ultra_aggressive` - Aggressive news scraping
- `breaking_news_hourly` - Breaking news hourly updates

### 3.4 Economic & Macro Data

**Economic Indicators:**
- `economic_indicators` - FRED economic data
- `industrial_demand_indicators` - Industrial demand metrics
- `currency_data` - FX rates (USD/CNY, USD/BRL, etc.)
- `cftc_cot` - CFTC Commitments of Traders

**Market Structure:**
- `market_analysis_correlations` - Cross-asset correlations
- `shap_drivers` - SHAP feature importance

### 3.5 Signals & Composite Views

**Big 8 Signal Views (from `cbi-v14.signals` dataset):**
- `vw_vix_stress_big8` - VIX stress signal
- `vw_harvest_pace_big8` - Harvest pace signal
- `vw_china_relations_big8` - China relations signal
- `vw_tariff_threat_big8` - Tariff threat signal
- `vw_geopolitical_volatility_big8` - GVI signal
- `vw_biofuel_cascade_big8` - Biofuel cascade signal
- `vw_hidden_correlation_big8` - Hidden correlation signal

**Composite Views:**
- `cbi-v14.api.vw_big8_composite_signal` - Master composite signal
- `cbi-v14.forecasting_data_warehouse.signals_1w` - 1-week signals table

**Training Dataset Features:**
- `cbi-v14.models_v4.training_dataset_super_enriched` - 284 features including:
  - Price features (`zl_price_current`, `oil_price_per_cwt`, etc.)
  - Big 8 signal features (`feature_vix_stress`, `feature_harvest_pace`, etc.)
  - China features (`china_mentions`, `china_posts`, `china_sentiment`, etc.)
  - Trump features (`trump_mentions`, `trumpxi_china_mentions`, etc.)
  - Weather features (`brazil_temperature_c`, `brazil_precipitation_mm`, etc.)
  - Correlation features (`palm_spread`, `crush_margin`, etc.)
  - Event features (`is_wasde_day`, `is_fomc_day`, etc.)
  - Lag features (`palm_lag1`, `crude_lag1`, `vix_lag1`, etc.)

### 3.6 Forecast & Prediction Data

**Production Forecasts:**
- `cbi-v14.predictions_uc1.production_forecasts` - Daily forecasts (4 horizons)
  - Columns: `forecast_id`, `horizon`, `forecast_date`, `target_date`, `predicted_value`, `lower_bound_80`, `upper_bound_80`, `palm_sub_risk`, `model_name`, `confidence`, `created_at`

**Dashboard Aggregation Views:**
- `cbi-v14.forecasting_data_warehouse.agg_1m_latest` - Latest forecast aggregation

**Model Metadata:**
- `cbi-v14.models_v4.residual_quantiles` - Residual quantiles for confidence bands
- `cbi-v14.models_v4.prediction_residuals` - Historical residuals

### 3.7 Metadata & System Tables

- `data_catalog` - Data source catalog
- `feature_metadata` - Feature descriptions
- `enhanced_feature_metadata` - Enhanced feature metadata
- `model_interpretability_metadata` - Model explainability
- `ai_metadata_summary` - AI system metadata
- `data_integration_status` - Integration status tracking
- `metadata_completeness_check` - Completeness audits

### 3.8 ScrapeCreator Proxy Views

- `vw_scrapecreator_economic_proxy` - Economic proxy data
- `vw_scrapecreator_policy_signals` - Policy signal proxies
- `vw_scrapecreator_price_proxy` - Price proxy data
- `vw_scrapecreator_weather_proxy` - Weather proxy data

---

## PART 4: AVAILABLE FEATURES FOR CHARTING

### 4.1 Price & Correlation Features (50+ features)

**Direct Price Features:**
- `zl_price_current`, `zl_volume`
- `oil_price_per_cwt`, `bean_price_per_bushel`, `meal_price_per_ton`
- `crush_margin`, `crush_margin_7d_ma`, `crush_margin_30d_ma`
- `palm_spread` (palm oil substitution indicator)
- `seasonal_index`, `monthly_zscore`, `yoy_change`

**Correlation Features:**
- `palm_lag1`, `palm_lag2`, `palm_lag3`, `palm_momentum_3d`
- `crude_lag1`, `crude_lag2`, `crude_momentum_2d`
- `vix_lag1`, `vix_lag2`, `vix_spike_lag1`
- `dxy_lag1`, `dxy_lag2`, `dxy_momentum_3d`
- `corn_lag1`, `wheat_lag1`, `corn_soy_ratio_lag1`
- `palm_lead2_correlation`, `crude_lead1_correlation`, `vix_lead1_correlation`

**Cross-Asset Prices:**
- `corn_price`, `wheat_price`
- `palm_oil_prices` (full table)
- `crude_oil_prices` (full table)
- `vix_current` (from `volatility_data`)

### 4.2 Big 8 Signal Features (7 primary signals)

**From `training_dataset_super_enriched`:**
- `feature_vix_stress`
- `feature_harvest_pace`
- `feature_china_relations`
- `feature_tariff_threat`
- `feature_geopolitical_volatility`
- `feature_biofuel_cascade`
- `feature_hidden_correlation`

**Composite Score:**
- `big8_composite_score`

**From signals views:**
- `vix_stress_score`, `vix_stress_regime`, `vix_crisis_flag`
- `harvest_pace_score`, `harvest_regime`, `harvest_crisis_flag`
- `china_relations_score`, `china_regime`, `china_crisis_flag`
- `tariff_threat_score`, `tariff_regime`, `tariff_crisis_flag`
- `gvi_score`, `gvi_regime`, `gvi_crisis_flag`
- `bsc_score`, `bsc_regime`, `bsc_crisis_flag`
- `hci_score`, `hci_regime`, `hci_crisis_flag`

**Composite Metrics:**
- `composite_signal_score` (0-1 scale)
- `crisis_intensity_score` (0-100)
- `market_regime` (FUNDAMENTALS_REGIME, VIX_CRISIS_REGIME, etc.)
- `forecast_confidence_pct` (45-75%)
- `primary_signal_driver`

### 4.3 China Intelligence Features (20+ features)

**China Trade:**
- `china_imports_from_us_mt`
- `china_soybean_imports_mt` (monthly)
- `argentina_china_sales_mt`
- `china_cancellation_signals`

**China Sentiment:**
- `china_mentions`, `china_posts`, `import_posts`, `soy_posts`
- `china_sentiment`, `china_sentiment_volatility`
- `china_policy_impact`
- `import_demand_index`
- `china_posts_7d_ma`, `china_sentiment_30d_ma`

**China Policy:**
- `china_policy_events`
- `china_tariff_rate`
- `china_us_import_share` (from trade data)

### 4.4 Trump Policy Features (15+ features)

**Trump Mentions:**
- `trump_mentions`, `trumpxi_china_mentions`, `trump_xi_co_mentions`
- `xi_mentions`, `tariff_mentions`
- `co_mention_sentiment`, `trumpxi_sentiment_volatility`
- `trumpxi_policy_impact`, `max_policy_impact`
- `tension_index`, `volatility_multiplier`
- `co_mentions_7d_ma`, `trumpxi_volatility_30d_ma`

**Trade War:**
- `china_tariff_rate`
- `brazil_market_share`
- `us_export_impact`
- `tradewar_event_vol_mult`
- `trade_war_intensity`
- `trade_war_impact_score`

### 4.5 Harvest & Weather Features (15+ features)

**Harvest Signals:**
- `brazil_harvest_signals`
- `argentina_harvest_signals`
- `feature_harvest_pace` (composite)

**Brazil Weather:**
- `brazil_month`, `export_seasonality_factor`
- `brazil_temperature_c`, `brazil_precipitation_mm`
- `growing_degree_days`
- `export_capacity_index`
- `harvest_pressure`
- `brazil_precip_30d_ma`, `brazil_temp_7d_ma`

**Argentina Weather:**
- `argentina_temperature_c`, `argentina_precipitation_mm` (from weather tables)

**US Weather:**
- `us_midwest_temperature_f`, `us_midwest_precipitation_inch` (from weather tables)

### 4.6 Biofuel Features (10+ features)

**Biofuel Demand:**
- `biodiesel_demand_signals`
- `feature_biofuel_cascade` (composite)
- `feature_biofuel_ethanol`

**Policy Signals:**
- `rfs_volumes` (from `policy_rfs_volumes` table)
- `indonesia_b40_signals`
- `renewable_diesel_margin`
- `eu_red_ii_signals`

**News:**
- `biofuel_article_count`
- `biofuel_news_count`

### 4.7 Event & Calendar Features (10+ features)

**Major Events:**
- `is_wasde_day`, `is_fomc_day`, `is_china_holiday`
- `is_crop_report_day`, `is_stocks_day`
- `is_planting_day`, `is_major_usda_day`
- `is_options_expiry`, `is_quarter_end`, `is_month_end`

**Event Impact:**
- `event_impact_level`
- `days_to_next_event`, `days_since_last_event`
- `pre_event_window`, `post_event_window`
- `event_vol_mult`

### 4.8 News & Sentiment Features (10+ features)

**News Volume:**
- `news_article_count`, `news_avg_score`
- `news_sentiment_avg`
- `china_news_count`, `biofuel_news_count`
- `tariff_news_count`, `weather_news_count`

**News Intelligence:**
- `news_intelligence_7d`, `news_volume_7d`

**Social Sentiment:**
- `social_sentiment_volatility` (if available)
- `bullish_ratio`, `bearish_ratio` (from `futures_sentiment_tradingview`)

---

## PART 5: DASHBOARD CONSUMPTION VIEWS

### 5.1 Forecast Views (Created)

**From `CREATE_DASHBOARD_VIEWS_STAGE6_WITH_REASONING.sql`:**
- `vw_forecast_with_signals` - Latest forecast + signals + AI reasoning
- `vw_vegas_intel_feed` - Kevin's live page feed
- `vw_china_intel_dashboard` - Chris Priority #1
- `vw_harvest_intel_dashboard` - Chris Priority #2
- `vw_biofuel_intel_dashboard` - Chris Priority #3
- `vw_forecast_timeline` - Historical timeline

### 5.2 Data Views Available

**Forecast Views:**
- `agg_1m_latest` - Latest forecast aggregation

**Signal Views:**
- `vw_big8_composite_signal` - Master composite signal
- `signals_1w` - 1-week signals table

**Price Views:**
- All price tables (direct access)

**Correlation Views:**
- `market_analysis_correlations` - Cross-asset correlations

---

## PART 6: GLIDE API DATA (VEGAS INTEL)

**Glide API Integration (READ ONLY):**

1. **Restaurant Groups** (`native-table-w295hHsL0PHvty2sAFwl`)
   - Group-level data and relationships
   - Scheduling availability
   - Delivery window preferences

2. **Restaurants** (`native-table-ojIjQjDcDAEOpdtZG5Ao`)
   - Individual restaurant details
   - Current usage patterns
   - Scheduling constraints
   - Delivery timing requirements
   - Location data (for route optimization)

3. **Fryers** (`native-table-r2BIqSLhezVbOKGeRJj8`)
   - Fryer count per restaurant
   - Fryer capacity and utilization
   - Current weekly/monthly usage
   - Fryer type (cuisine-based consumption patterns)

**API Configuration:**
- Endpoint: `https://api.glideapp.io/api/function/queryTables`
- Bearer Token: `460c9ee4-edcb-43cc-86b5-929e2bb94351` (stored in secrets)
- App ID: `mUOrVLuWpdduTpJev9t1`
- Access Level: Business plan or above required

**Key Data Points:**
- **Scheduling:** When restaurants can receive upsold oil (delivery windows, availability)
- **Current Usage:** How much oil they're currently using (baseline for upsell calculation)
- **Fryer Count:** Number of fryers per restaurant (capacity indicator)
- **Delivery Timing:** When they need the oil delivered (event-driven timing)
- **Past Usage:** Historical consumption patterns (for trend analysis)

---

## PART 7: MODEL DATA

### 7.1 Trained Models

**BOOSTED_TREE Models (Production Ready):**
- `bqml_1w` - 276 features, 100 iterations, MAPE: 1.21%
- `bqml_1m` - 274 features, 100 iterations, MAPE: 1.29%
- `bqml_3m` - 268 features, 100 iterations, MAPE: 0.70% ⭐
- `bqml_6m` - 258 features, 100 iterations, MAPE: 1.21%

**ARIMA Models (Exists, Not Evaluated):**
- `arima_baseline_1w`, `arima_baseline_1m`, `arima_baseline_3m`, `arima_baseline_6m`
- `zl_arima_1w_v4`, `zl_arima_1m_v4`, `zl_arima_3m_v4`, `zl_arima_6m_v4`

### 7.2 Training Data

- `cbi-v14.models_v4.training_dataset_super_enriched`
  - 2,043 rows total
  - 1,448 training rows
  - 284 numeric features
  - Date range: 2020-01-06 to 2025-09-10
  - Feature coverage: 99%+ for critical features

---

## SUMMARY: DATA AVAILABLE FOR DASHBOARD

### Core Data Sources
- ✅ **70+ data tables** (prices, weather, policy, sentiment, etc.)
- ✅ **284 features** in training dataset
- ✅ **7 Big 8 signals** with composite scoring
- ✅ **4 production models** (BOOSTED_TREE, 1W/1M/3M/6M)
- ✅ **Forecast outputs** (production_forecasts table)
- ✅ **Glide API** (Restaurant Groups, Restaurants, Fryers)

### Dashboard Views Available
- ✅ **6 dashboard views** with Tier 1 AI reasoning
- ✅ **Forecast views** (latest, timeline, vs actual)
- ✅ **Signal views** (Big 8 composite, individual signals)
- ✅ **Intel views** (China, Harvest, Biofuel)

### Features Available
- ✅ **50+ price/correlation features**
- ✅ **20+ China intelligence features**
- ✅ **15+ Trump policy features**
- ✅ **15+ harvest/weather features**
- ✅ **10+ biofuel features**
- ✅ **10+ event/calendar features**
- ✅ **10+ news/sentiment features**

**Total: 284 features + 70+ tables + 4 models + 6 views = Complete data ecosystem ready for dashboard**

