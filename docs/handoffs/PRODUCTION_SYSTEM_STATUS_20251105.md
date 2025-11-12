# PRODUCTION SYSTEM STATUS - November 5, 2025
**Time**: 11:00 AM ET  
**Status**: ✅ DATASETS RESTORED, MODELS IDENTIFIED

---

## ✅ PRODUCTION BQML MODELS (USE THESE - CANNOT RENAME)

**Note**: BigQuery does NOT allow copying/renaming BQML models. We use original names:

```
cbi-v14.models_v4.bqml_1w  (Trained Nov 4, 274 features, MAE 0.393)
cbi-v14.models_v4.bqml_1m  (Trained Nov 4, 274 features, MAE 0.297, R² 0.987)
cbi-v14.models_v4.bqml_3m  (Trained Nov 4, 268 features, MAE 0.409)
cbi-v14.models_v4.bqml_6m  (Trained Nov 4, 258 features, MAE 0.401)
```

**Archived**: `bqml_1m_archive_nov4` (backup created)

---

## ✅ PRODUCTION TRAINING DATASETS (MAIN DATASETS)

```
cbi-v14.models_v4.production_training_data_1w  (290 cols, 1,448 rows, latest: Oct 13)
cbi-v14.models_v4.production_training_data_1m  (290 cols, 1,347 rows, latest: Sept 10)
cbi-v14.models_v4.production_training_data_3m  (290 cols, 1,329 rows, latest: June 13)
cbi-v14.models_v4.production_training_data_6m  (290 cols, 1,198 rows, latest: Feb 4)
```

**Source**: `training_dataset_pre_integration_backup` (Nov 3, 2,043 rows, 290 features)

---

## 🎯 CRITICAL FEATURES (274 in bqml_1m)

### Price & Market (10)
- zl_price_current, zl_volume
- corn_price, wheat_price, corn_lag1, wheat_lag1
- bean_price_per_bushel, crush_margin
- oil_price_per_cwt, soybean_meal_price

### Big 8 Signals (9)
- feature_vix_stress
- feature_harvest_pace
- feature_china_relations
- feature_tariff_threat
- feature_geopolitical_volatility
- feature_biofuel_cascade
- feature_hidden_correlation
- feature_biofuel_ethanol
- big8_composite_score

### Correlations (30+)
- corr_zl_palm_7d/30d/90d/180d/365d
- corr_zl_crude_7d/30d/90d/180d/365d
- corr_zl_vix_7d/30d/90d/180d/365d
- corr_zl_dxy_7d/30d/90d/180d/365d
- corr_zl_corn_7d/30d/90d/365d
- corr_zl_wheat_7d/30d
- corr_palm_crude_30d, corr_corn_wheat_30d

### Weather (30+)
- **Brazil**: temp_c, precip_mm, conditions_score, heat_stress_days, drought_days, flood_days, precip_30d_ma, temp_7d_ma
- **Argentina**: temp_c, precip_mm, conditions_score, heat_stress_days, drought_days, flood_days
- **US Midwest**: temp_c, precip_mm, conditions_score, heat_stress_days, drought_days, flood_days

### Economic (15+)
- cpi_yoy, gdp_growth, unemployment_rate
- treasury_10y_yield, fed_funds_rate, real_yield, yield_curve
- usd_cny_rate, usd_brl_rate, usd_ars_rate, usd_myr_rate
- dollar_index, dxy_level
- usd_cny_7d_change, usd_brl_7d_change, dollar_index_7d_change

### China Data (15+)
- china_soybean_sales, cn_imports, cn_imports_fixed
- china_sentiment, china_sentiment_30d_ma, china_sentiment_volatility
- china_mentions, china_posts, china_posts_7d_ma
- china_policy_events, china_policy_impact
- china_tariff_rate, china_news_count

### Argentina Data (10+)
- argentina_export_tax ✅
- argentina_china_sales_mt ✅
- argentina_competitive_threat
- argentina_conditions_score
- argentina_temp_c, argentina_precip_mm
- argentina_heat_stress_days, argentina_drought_days, argentina_flood_days

### CFTC Data (10)
- cftc_commercial_long, cftc_commercial_short, cftc_commercial_net
- cftc_managed_long, cftc_managed_short, cftc_managed_net
- cftc_open_interest
- cftc_commercial_extreme, cftc_spec_extreme

### Technical Indicators (20+)
- rsi_14, rsi_proxy
- bb_upper, bb_middle, bb_lower, bb_percent, bb_width
- macd_line, macd_signal, macd_histogram, macd_proxy
- ma_7d, ma_30d, ma_90d
- atr_14, volatility_30d
- seasonal_index, seasonal_sin, seasonal_cos
- monthly_zscore, yoy_change

### News & Social (20+)
- news_article_count, news_avg_score, news_sentiment_avg
- china_news_count, biofuel_news_count, tariff_news_count, weather_news_count
- social_sentiment_avg, social_sentiment_volatility
- avg_sentiment, sentiment_volume
- trump_soybean_sentiment_7d, trump_agricultural_impact_30d
- trump_policy_events, trump_policy_impact_avg, trump_policy_impact_max
- trade_policy_events, china_policy_events, ag_policy_events

### Substitution & Correlation Dynamics (20+)
- palm_price, palm_lag1/2/3, palm_momentum_3d
- crude_price, crude_lag1/2, crude_momentum_2d
- palm_accuracy_30d, crude_accuracy_30d
- palm_direction_correct, crude_direction_correct
- palm_lead2_correlation, crude_lead1_correlation
- vix_lead1_correlation, dxy_lead1_correlation
- lead_signal_confidence, momentum_divergence

### Seasonal & Calendar (15+)
- is_wasde_day, is_fomc_day, is_china_holiday
- is_crop_report_day, is_stocks_day, is_planting_day, is_major_usda_day
- is_options_expiry, is_quarter_end, is_month_end
- day_of_week, day_of_week_num, day_of_month
- month, month_num, quarter

### Trade & Export (10+)
- brazil_market_share, export_capacity_index, export_seasonality_factor
- us_export_impact, harvest_pressure
- soybean_weekly_sales, soybean_oil_weekly_sales, soybean_meal_weekly_sales

### Volatility & Risk (10+)
- vix_level, vix_lag1/2, vix_spike_lag1, vix_index_new
- volatility_regime, volatility_multiplier
- event_impact_level, event_vol_mult
- global_weather_risk_score
- economic_stress_index

---

## 🚨 DATA FRESHNESS ISSUE

**Current State**:
- 1W: Oct 13 (23 days stale)
- 1M: Sept 10 (56 days stale)
- 3M/6M: Much older

**Root Cause**: Datasets restored from Nov 3 backup, but still missing Oct 14 - Nov 5 data

---

## 🔧 NEXT STEPS

### Step 1: Update Datasets with Latest Data
Run `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql` to add Nov 4-5 data

### Step 2: Connect Ingestion Scripts
Modify ALL ingestion scripts to UPDATE production_training_data_*

### Step 3: Daily Automation
Schedule daily refresh to keep datasets current

---

**OFFICIAL PRODUCTION SYSTEM - ALL NEW DATA GOES HERE**







