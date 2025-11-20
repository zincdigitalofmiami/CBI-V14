---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🎯 OFFICIAL PRODUCTION SYSTEM - CBI-V14
**Last Updated**: November 5, 2025, 11:15 AM ET  
**Status**: ✅ PRODUCTION READY

---

## WRITE THIS DOWN - OFFICIAL NAMES

### PRODUCTION BQML MODELS (CANNOT BE RENAMED)
```
cbi-v14.models_v4.bqml_1w
cbi-v14.models_v4.bqml_1m
cbi-v14.models_v4.bqml_3m
cbi-v14.models_v4.bqml_6m
```

**Created**: November 4, 2025, 11:25-11:41 AM  
**Features**: 258-274 features each  
**Performance**: MAE 0.30-0.41, R² 0.987, MAPE <1%

---

### PRODUCTION TRAINING DATASETS (MAIN DATASETS - ALL INGESTION GOES HERE)
```
cbi-v14.models_v4.production_training_data_1w
cbi-v14.models_v4.production_training_data_1m
cbi-v14.models_v4.production_training_data_3m
cbi-v14.models_v4.production_training_data_6m
```

**Features**: 290 columns each  
**Source**: training_dataset_pre_integration_backup (Nov 3, 2025)  
**Rows**: 1,198 - 1,448 depending on horizon  

---

### DEPRECATED (DO NOT USE - EVER)
```
training_dataset_super_enriched (11 columns - BROKEN)
All _ARCHIVED_* tables
All *_backup tables (except for restore purposes)
```

---

## DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────┐
│   INGESTION SCRIPTS (Hourly/Daily)      │
│                                         │
│  • hourly_prices.py                     │
│  • daily_weather.py                     │
│  • ingest_social_intelligence.py        │
│  • ingest_market_prices.py              │
│  • ingest_cftc_positioning_REAL.py      │
│  • ingest_usda_harvest_api.py           │
│  • ingest_eia_biofuel_real.py           │
│  • backfill_trump_intelligence.py       │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  PRODUCTION TRAINING DATASETS (290 cols)│
│                                         │
│  • production_training_data_1w          │
│  • production_training_data_1m          │
│  • production_training_data_3m          │
│  • production_training_data_6m          │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│     BQML PRODUCTION MODELS (274 feat)   │
│                                         │
│  • bqml_1w (1 week predictions)         │
│  • bqml_1m (1 month predictions)        │
│  • bqml_3m (3 month predictions)        │
│  • bqml_6m (6 month predictions)        │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│   ML.PREDICT() QUERIES                  │
│                                         │
│  GENERATE_PREDICTIONS_PRODUCTION.sql    │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│      PREDICTION OUTPUT                  │
│                                         │
│  predictions_uc1.production_forecasts   │
│  or predictions.daily_forecasts         │
└─────────────────────────────────────────┘
```

---

## 📊 COMPLETE FEATURE LIST (290 columns)

### 1. TARGET COLUMNS (4)
- target_1w, target_1m, target_3m, target_6m

### 2. DATE COLUMN (1)
- date

### 3. PRICE DATA (10)
- zl_price_current, zl_volume
- zl_price_lag1, zl_price_lag7, zl_price_lag30
- corn_price, wheat_price
- bean_price_per_bushel, oil_price_per_cwt
- soybean_meal_price

### 4. BIG 8 SIGNALS (9)
- feature_vix_stress
- feature_harvest_pace
- feature_china_relations
- feature_tariff_threat
- feature_geopolitical_volatility
- feature_biofuel_cascade
- feature_hidden_correlation
- feature_biofuel_ethanol
- big8_composite_score

### 5. CORRELATIONS (30)
**ZL-Palm**: corr_zl_palm_7d, corr_zl_palm_30d, corr_zl_palm_90d, corr_zl_palm_180d, corr_zl_palm_365d  
**ZL-Crude**: corr_zl_crude_7d, corr_zl_crude_30d, corr_zl_crude_90d, corr_zl_crude_180d, corr_zl_crude_365d  
**ZL-VIX**: corr_zl_vix_7d, corr_zl_vix_30d, corr_zl_vix_90d, corr_zl_vix_180d, corr_zl_vix_365d  
**ZL-DXY**: corr_zl_dxy_7d, corr_zl_dxy_30d, corr_zl_dxy_90d, corr_zl_dxy_180d, corr_zl_dxy_365d  
**ZL-Corn**: corr_zl_corn_7d, corr_zl_corn_30d, corr_zl_corn_90d, corr_zl_corn_365d  
**ZL-Wheat**: corr_zl_wheat_7d, corr_zl_wheat_30d  
**Cross-Asset**: corr_palm_crude_30d, corr_corn_wheat_30d, corn_zl_correlation_30d, wheat_zl_correlation_30d, crude_zl_correlation_30d

### 6. WEATHER DATA (30+)
**Brazil**: brazil_temp_c, brazil_temperature_c, brazil_precip_mm, brazil_precipitation_mm, brazil_conditions_score, brazil_heat_stress_days, brazil_drought_days, brazil_flood_days, brazil_precip_30d_ma, brazil_temp_7d_ma, brazil_month  
**Argentina**: argentina_temp_c, argentina_precip_mm, argentina_conditions_score, argentina_heat_stress_days, argentina_drought_days, argentina_flood_days  
**US Midwest**: us_midwest_temp_c, us_midwest_precip_mm, us_midwest_conditions_score, us_midwest_heat_stress_days, us_midwest_drought_days, us_midwest_flood_days  
**Derived**: growing_degree_days, global_weather_risk_score

### 7. ECONOMIC INDICATORS (20+)
**Macro**: cpi_yoy, gdp_growth, econ_gdp_growth, econ_inflation_rate, econ_unemployment_rate, unemployment_rate  
**Rates**: treasury_10y_yield, fed_funds_rate, real_yield, yield_curve  
**FX**: usd_cny_rate, usd_brl_rate, usd_ars_rate, usd_myr_rate, fx_usd_ars_30d_z, fx_usd_myr_30d_z  
**Dollar Index**: dollar_index, dxy_level, usd_cny_7d_change, usd_brl_7d_change, dollar_index_7d_change

### 8. CHINA DATA (20+)
**Imports**: china_soybean_sales, cn_imports, cn_imports_fixed, import_posts, import_demand_index  
**Sentiment**: china_sentiment, china_sentiment_30d_ma, china_sentiment_volatility  
**Social**: china_mentions, china_posts, china_posts_7d_ma  
**Policy**: china_policy_events, china_policy_impact, china_tariff_rate, china_news_count  
**Correlations**: (see correlations section)

### 9. ARGENTINA DATA (15+)
**Critical**: argentina_export_tax ✅, argentina_china_sales_mt ✅  
**Competitive**: argentina_competitive_threat, brazil_market_share  
**Weather**: argentina_temp_c, argentina_precip_mm, argentina_conditions_score  
**Conditions**: argentina_heat_stress_days, argentina_drought_days, argentina_flood_days

### 10. BRAZIL DATA (15+)
**Market**: brazil_market_share, br_yield, export_seasonality_factor, export_capacity_index  
**Weather**: (see weather section)  
**Competitive**: harvest_pressure

### 11. CFTC POSITIONING (10)
- cftc_commercial_long, cftc_commercial_short, cftc_commercial_net
- cftc_managed_long, cftc_managed_short, cftc_managed_net
- cftc_open_interest
- cftc_commercial_extreme, cftc_spec_extreme

### 12. TECHNICAL INDICATORS (25+)
**Moving Averages**: ma_7d, ma_30d, ma_90d  
**Bollinger Bands**: bb_upper, bb_middle, bb_lower, bb_percent, bb_width  
**RSI**: rsi_14, rsi_proxy  
**MACD**: macd_line, macd_signal, macd_histogram, macd_proxy  
**Volatility**: atr_14, volatility_30d, historical_volatility_30d  
**Returns**: return_1d, return_7d  
**Price Patterns**: price_ma_ratio, price_momentum_1w, price_momentum_1m  
**Seasonal**: seasonal_index, seasonal_sin, seasonal_cos, monthly_zscore, yoy_change

### 13. PALM OIL & CRUDE (15+)
**Palm**: palm_price, palm_lag1, palm_lag2, palm_lag3, palm_momentum_3d, palm_accuracy_30d, palm_direction_correct  
**Crude**: crude_price, crude_oil_wti_new, crude_lag1, crude_lag2, crude_momentum_2d, crude_accuracy_30d, crude_direction_correct, wti_7d_change  
**Lead Signals**: palm_lead2_correlation, crude_lead1_correlation, vix_lead1_correlation, dxy_lead1_correlation, lead_signal_confidence, momentum_divergence

### 14. VIX & VOLATILITY (10+)
- vix_level, vix_index_new
- vix_lag1, vix_lag2, vix_spike_lag1
- volatility_regime, volatility_multiplier
- is_low_vol, is_normal_vol, is_high_vol

### 15. NEWS & SOCIAL SENTIMENT (20+)
**News**: news_article_count, news_avg_score, news_sentiment_avg, news_intelligence_7d, news_volume_7d  
**By Topic**: china_news_count, biofuel_news_count, tariff_news_count, weather_news_count  
**Social**: social_sentiment_avg, social_sentiment_volatility, social_sentiment_7d, social_volume_7d, social_post_count  
**Social Dynamics**: avg_sentiment, sentiment_volume, sentiment_volatility, bullish_ratio, bearish_ratio  
**Trump-China**: trumpxi_china_mentions, trump_xi_co_mentions, co_mention_sentiment, trumpxi_sentiment_volatility, co_mentions_7d_ma, trumpxi_volatility_30d_ma

### 16. TRUMP POLICY INTELLIGENCE (15+)
**Sentiment**: trump_soybean_sentiment_7d, trump_agricultural_impact_30d, trump_soybean_relevance_30d  
**Events**: trump_policy_events, trump_events_7d, trump_policy_7d  
**Impact**: trump_policy_impact_avg, trump_policy_impact_max, trump_policy_intensity_14d, days_since_trump_policy  
**Categories**: trade_policy_events, china_policy_events, ag_policy_events  
**Activity**: trump_mentions, xi_mentions, tariff_mentions

### 17. USDA & EXPORT DATA (10+)
**Weekly Sales**: soybean_weekly_sales, soybean_oil_weekly_sales, soybean_meal_weekly_sales  
**Export**: us_export_impact, export_capacity_index, export_seasonality_factor

### 18. CALENDAR & SEASONAL (20+)
**Calendar Events**: is_wasde_day, is_fomc_day, is_china_holiday, is_crop_report_day, is_stocks_day, is_planting_day, is_major_usda_day, is_options_expiry, is_quarter_end, is_month_end  
**Event Timing**: days_to_next_event, days_since_last_event, pre_event_window, post_event_window, event_impact_level, event_vol_mult  
**Temporal**: day_of_week, day_of_week_num, day_of_month, month, month_num, quarter

### 19. TRADE & GEOPOLITICS (10+)
- trade_war_intensity, trade_war_impact_score, tradewar_event_vol_mult
- tension_index, volatility_multiplier
- leadlag_zl_price
- time_weight

### 20. CRUSH & PROCESSING (5+)
- crush_margin, crush_margin_7d_ma, crush_margin_30d_ma
- meal_price_per_ton

### 21. CORN & WHEAT SPECIFICS (5+)
- corn_lag1, wheat_lag1
- corn_soy_ratio_lag1

### 22. OTHER DERIVED (10+)
- seasonal_month_factor
- volume_sma_ratio
- economic_stress_index
- social_sentiment_momentum_7d
- momentum_30d
- rn (row number)

---

## 🔄 DATA UPDATE PROCESS

### Step 1: Run Comprehensive Integration
```bash
bq query --use_legacy_sql=false < bigquery-sql/COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql
```

### Step 2: Connect Ingestion Scripts
Each script must UPDATE production_training_data_* tables

### Step 3: Daily Refresh
Cron at 6:00 AM runs comprehensive integration

---

## 📝 QUICK REFERENCE

**Project**: cbi-v14  
**Main Dataset**: forecasting_data_warehouse  
**Models Dataset**: models_v4  
**Predictions**: predictions_uc1.production_forecasts

**Production Models**: bqml_1w, bqml_1m, bqml_3m, bqml_6m  
**Production Data**: production_training_data_1w/1m/3m/6m  

**Features**: 290 total, 258-274 used per model  
**Performance**: MAE 0.30, R² 0.987, MAPE <1%

---

**PRINT THIS AND KEEP IT - THIS IS THE OFFICIAL SYSTEM**

