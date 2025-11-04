# FRED & Yahoo Finance Null Fill Analysis

## Summary

This document identifies which columns with nulls can be filled using FRED API or Yahoo Finance data.

**Total Columns Analyzed:** 209  
**Can be filled by FRED:** ~15 columns  
**Can be filled by Yahoo Finance:** ~50+ columns (direct + calculated)  
**Cannot be filled by either:** ~140+ columns (require custom logic, derived features, or other sources)

---

## ✅ COLUMNS FILLABLE BY FRED API

### Economic Indicators (FRED Series IDs)
| Column Name | FRED Series ID | Type | Null % | Notes |
|------------|----------------|------|-------|-------|
| `treasury_10y_yield` | `DGS10` | Daily | 28.7% | 10-Year Treasury Constant Maturity Rate |
| `econ_gdp_growth` | `GDPC1` | Quarterly | 99.46% | Calculate growth from Real GDP |
| `gdp_growth` | `GDPC1` | Quarterly | 99.46% | Calculate growth from Real GDP |
| `econ_inflation_rate` | `CPIAUCSL` | Monthly | 99.12% | Calculate YoY from CPI |
| `cpi_yoy` | `CPIAUCSL` | Monthly | 99.46% | Year-over-year CPI change |
| `econ_unemployment_rate` | `UNRATE` | Monthly | 96.48% | Unemployment Rate |
| `unemployment_rate` | `UNRATE` | Monthly | 99.46% | Unemployment Rate (forward fill to daily) |
| `usd_cny_rate` | `DEXCHUS` | Daily | 38.83% | China/U.S. Foreign Exchange Rate |
| `usd_brl_rate` | `DEXBZUS` | Daily | 38.83% | Brazilian Real/U.S. Dollar Exchange Rate |
| `dollar_index` | `DTWEXBGS` | Daily | 38.83% | Trade Weighted U.S. Dollar Index |
| `usd_index` | `DTWEXBGS` | Daily | 28.56% | Trade Weighted U.S. Dollar Index |
| `fed_funds_rate` | `FEDFUNDS` | Daily | 38.83% | Federal Funds Effective Rate |
| `vix_index_new` | `VIXCLS` | Daily | 38.83% | VIX Volatility Index (Yahoo is better) |
| `vix_level` | `VIXCLS` | Daily | 38.53% | VIX Volatility Index (Yahoo is better) |

### Calculated from FRED Data
| Column Name | Calculation | Null % | Notes |
|------------|-------------|--------|-------|
| `yield_curve` | DGS10 - FEDFUNDS | 38.83% | Spread between 10Y and Fed Funds |
| `real_yield` | DGS10 - CPIAUCSL YoY | 38.83% | Nominal yield minus inflation |
| `usd_cny_7d_change` | 7-day change of DEXCHUS | 38.83% | Weekly change in USD/CNY |
| `usd_brl_7d_change` | 7-day change of DEXBZUS | 38.83% | Weekly change in USD/BRL |
| `dollar_index_7d_change` | 7-day change of DTWEXBGS | 38.83% | Weekly change in DXY |

**FRED Total:** ~15 direct columns + 5 calculated = **~20 columns fillable**

---

## ✅ COLUMNS FILLABLE BY YAHOO FINANCE

### Direct Price & Volume Data
| Column Name | Yahoo Ticker | Type | Null % | Notes |
|------------|--------------|------|--------|-------|
| `zl_price_current` | `ZL=F` | Daily | 28.17% | Soybean Oil Futures (Continuous) |
| `zl_volume` | `ZL=F` | Daily | 28.51% | Volume for ZL futures |
| `target_1w` | `ZL=F` | Daily | 29.19% | Future price 7 days ahead |
| `target_1m` | `ZL=F` | Daily | 34.13% | Future price 30 days ahead |
| `target_3m` | `ZL=F` | Daily | 35.01% | Future price 90 days ahead |
| `target_6m` | `ZL=F` | Daily | 41.42% | Future price 180 days ahead |
| `corn_price` | `ZC=F` | Daily | 38.83% | Corn Futures |
| `wheat_price` | `ZW=F` | Daily | 38.83% | Wheat Futures |
| `crude_oil_wti_new` | `CL=F` | Daily | 38.83% | Crude Oil WTI Futures |
| `crude_price` | `CL=F` | Daily | 38.53% | Crude Oil WTI Futures |
| `palm_price` | `FCPO=F` | Daily | 38.39% | Palm Oil Futures (Malaysia) |
| `soybean_meal_price` | `ZM=F` | Daily | 28.17% | Soybean Meal Futures |
| `vix_level` | `^VIX` | Daily | 38.53% | VIX Volatility Index |
| `vix_index_new` | `^VIX` | Daily | 38.83% | VIX Volatility Index |
| `dxy_level` | `DX-Y.NYB` | Daily | 38.83% | Dollar Index |
| `usd_cny_rate` | `CNY=X` | Daily | 38.83% | USD/CNY Exchange Rate |
| `usd_brl_rate` | `BRL=X` | Daily | 38.83% | USD/BRL Exchange Rate |
| `dollar_index` | `DX-Y.NYB` | Daily | 38.83% | Dollar Index |

### Technical Indicators (Calculated from Price Data)
Once base prices are available, these can be calculated:

| Column Name | Calculation | Null % | Notes |
|------------|-------------|--------|-------|
| `zl_price_lag1` | `zl_price_current` lagged 1 day | 38.19% | Requires ZL price |
| `zl_price_lag7` | `zl_price_current` lagged 7 days | 38.34% | Requires ZL price |
| `zl_price_lag30` | `zl_price_current` lagged 30 days | 39.12% | Requires ZL price |
| `return_1d` | Daily return from ZL price | 51.59% | Requires ZL price |
| `return_7d` | 7-day return from ZL price | 40.59% | Requires ZL price |
| `ma_7d` | 7-day moving average of ZL | 10.02% | Requires ZL price |
| `ma_30d` | 30-day moving average of ZL | 10.02% | Requires ZL price |
| `ma_90d` | 90-day moving average of ZL | 38.19% | Requires ZL price |
| `volatility_30d` | 30-day rolling volatility | 10.07% | Requires ZL price |
| `historical_volatility_30d` | 30-day historical volatility | 38.09% | Requires ZL price |
| `rsi_14` | 14-period RSI | 28.31% | Requires ZL price |
| `rsi_proxy` | RSI proxy calculation | 39.17% | Requires ZL price |
| `macd_line` | MACD line | 28.07% | Requires ZL price |
| `macd_signal` | MACD signal line | 28.07% | Requires ZL price |
| `macd_histogram` | MACD histogram | 28.07% | Requires ZL price |
| `macd_proxy` | MACD proxy | 38.83% | Requires ZL price |
| `bb_upper` | Bollinger Band upper | 28.12% | Requires ZL price |
| `bb_middle` | Bollinger Band middle | 38.19% | Requires ZL price |
| `bb_lower` | Bollinger Band lower | 28.12% | Requires ZL price |
| `bb_width` | Bollinger Band width | 38.88% | Requires ZL price |
| `bb_percent` | Bollinger Band %B | 28.12% | Requires ZL price |
| `atr_14` | 14-period ATR | 28.12% | Requires ZL price |
| `price_ma_ratio` | Price / MA ratio | 38.83% | Requires ZL price |
| `momentum_30d` | 30-day momentum | 40.29% | Requires ZL price |
| `price_momentum_1w` | 1-week momentum | 28.31% | Requires ZL price |
| `price_momentum_1m` | 1-month momentum | 29.14% | Requires ZL price |
| `volume_sma_ratio` | Volume / SMA ratio | 28.41% | Requires ZL volume |
| `corn_lag1` | Corn price lagged 1 day | 38.83% | Requires corn price |
| `wheat_lag1` | Wheat price lagged 1 day | 38.83% | Requires wheat price |
| `crude_lag1` | Crude price lagged 1 day | 38.83% | Requires crude price |
| `crude_lag2` | Crude price lagged 2 days | 38.83% | Requires crude price |
| `crude_momentum_2d` | 2-day crude momentum | 38.83% | Requires crude price |
| `palm_lag1` | Palm price lagged 1 day | 38.83% | Requires palm price |
| `palm_lag2` | Palm price lagged 2 days | 38.83% | Requires palm price |
| `palm_lag3` | Palm price lagged 3 days | 38.83% | Requires palm price |
| `palm_momentum_3d` | 3-day palm momentum | 38.83% | Requires palm price |
| `vix_lag1` | VIX lagged 1 day | 38.83% | Requires VIX |
| `vix_lag2` | VIX lagged 2 days | 38.83% | Requires VIX |
| `dxy_lag1` | DXY lagged 1 day | 38.83% | Requires DXY |
| `dxy_lag2` | DXY lagged 2 days | 38.83% | Requires DXY |
| `dxy_momentum_3d` | 3-day DXY momentum | 38.83% | Requires DXY |
| `wti_7d_change` | 7-day WTI change | 38.83% | Requires crude price |
| `corr_zl_palm_7d` | 7-day ZL-Palm correlation | 10.32% | Requires both prices |
| `corr_zl_palm_30d` | 30-day ZL-Palm correlation | 10.07% | Requires both prices |
| `corr_zl_palm_90d` | 90-day correlation | 10.07% | Requires both prices |
| `corr_zl_palm_180d` | 180-day correlation | 10.07% | Requires both prices |
| `corr_zl_palm_365d` | 365-day correlation | 10.07% | Requires both prices |
| `corr_zl_crude_7d` | 7-day ZL-Crude correlation | 10.46% | Requires both prices |
| `corr_zl_crude_30d` | 30-day correlation | 10.07% | Requires both prices |
| `corr_zl_crude_90d` | 90-day correlation | 10.07% | Requires both prices |
| `corr_zl_crude_180d` | 180-day correlation | 10.07% | Requires both prices |
| `corr_zl_crude_365d` | 365-day correlation | 10.07% | Requires both prices |
| `corr_zl_vix_7d` | 7-day ZL-VIX correlation | 10.46% | Requires both series |
| `corr_zl_vix_30d` | 30-day correlation | 10.07% | Requires both series |
| `corr_zl_vix_90d` | 90-day correlation | 10.07% | Requires both series |
| `corr_zl_vix_180d` | 180-day correlation | 10.07% | Requires both series |
| `corr_zl_vix_365d` | 365-day correlation | 10.07% | Requires both series |
| `corr_zl_dxy_7d` | 7-day ZL-DXY correlation | 10.95% | Requires both series |
| `corr_zl_dxy_30d` | 30-day correlation | 10.07% | Requires both series |
| `corr_zl_dxy_90d` | 90-day correlation | 10.07% | Requires both series |
| `corr_zl_dxy_180d` | 180-day correlation | 10.07% | Requires both series |
| `corr_zl_dxy_365d` | 365-day correlation | 10.07% | Requires both series |
| `corr_zl_corn_7d` | 7-day ZL-Corn correlation | 10.95% | Requires both prices |
| `corr_zl_corn_30d` | 30-day correlation | 10.07% | Requires both prices |
| `corr_zl_corn_90d` | 90-day correlation | 10.07% | Requires both prices |
| `corr_zl_corn_365d` | 365-day correlation | 10.07% | Requires both prices |
| `corr_zl_wheat_7d` | 7-day ZL-Wheat correlation | 10.95% | Requires both prices |
| `corr_zl_wheat_30d` | 30-day correlation | 10.07% | Requires both prices |
| `corr_palm_crude_30d` | 30-day Palm-Crude correlation | 10.07% | Requires both prices |
| `corr_corn_wheat_30d` | 30-day Corn-Wheat correlation | 10.07% | Requires both prices |
| `corn_soy_ratio_lag1` | Corn/Soy ratio lagged | 38.83% | Requires corn & bean prices |
| `usd_zl_correlation_30d` | 30-day USD-ZL correlation | 28.12% | Requires both series |

**Yahoo Finance Total:** ~18 direct + ~50 calculated = **~68 columns fillable**

---

## ❌ COLUMNS NOT FILLABLE BY FRED OR YAHOO

These columns require custom logic, derived features, or other data sources:

### Target Variables (Forward-Looking)
- Cannot be "filled" - these are future values that don't exist yet for recent dates

### Feature Engineering (Calculated from Multiple Sources)
- `feature_vix_stress` - Custom feature calculation
- `feature_harvest_pace` - Agricultural timing logic
- `feature_china_relations` - Custom sentiment/policy scoring
- `feature_tariff_threat` - Policy analysis
- `feature_geopolitical_volatility` - Composite measure
- `feature_biofuel_cascade` - Biofuel market analysis
- `feature_hidden_correlation` - Statistical discovery
- `feature_biofuel_ethanol` - Biofuel-specific analysis
- `big8_composite_score` - Composite of 8 signals
- `seasonal_index` - Seasonal pattern analysis
- `monthly_zscore` - Statistical normalization
- `yoy_change` - Year-over-year calculation (needs historical data)
- `oil_price_per_cwt` - Unit conversion (cwt = hundredweight)
- `bean_price_per_bushel` - Unit conversion
- `meal_price_per_ton` - Unit conversion
- `crush_margin` - Calculated from multiple prices
- `crush_margin_7d_ma` - Moving average of crush margin
- `crush_margin_30d_ma` - Moving average of crush margin

### Social Media / Sentiment Data
- `china_mentions` - Social media scraping/API
- `china_posts` - Social media scraping/API
- `import_posts` - Social media scraping/API
- `soy_posts` - Social media scraping/API
- `china_sentiment` - Sentiment analysis
- `china_sentiment_volatility` - Sentiment volatility
- `china_policy_impact` - Policy analysis
- `import_demand_index` - Custom index
- `china_posts_7d_ma` - Moving average of posts
- `china_sentiment_30d_ma` - Moving average of sentiment
- `trump_mentions` - Social media/Twitter/Truth Social
- `trumpxi_china_mentions` - Social media co-mentions
- `trump_xi_co_mentions` - Social media co-mentions
- `xi_mentions` - Social media
- `tariff_mentions` - News/social media
- `co_mention_sentiment` - Sentiment analysis
- `trumpxi_sentiment_volatility` - Sentiment volatility
- `trumpxi_policy_impact` - Policy analysis
- `max_policy_impact` - Policy analysis
- `tension_index` - Custom index
- `volatility_multiplier` - Custom calculation
- `co_mentions_7d_ma` - Moving average
- `trumpxi_volatility_30d_ma` - Moving average
- `trump_soybean_sentiment_7d` - Custom sentiment
- `trump_agricultural_impact_30d` - Custom impact measure
- `trump_soybean_relevance_30d` - Custom relevance score
- `days_since_trump_policy` - Event tracking
- `trump_policy_intensity_14d` - Policy intensity
- `social_sentiment_momentum_7d` - Sentiment momentum
- `avg_sentiment` - Average sentiment
- `sentiment_volatility` - Sentiment volatility
- `sentiment_volume` - Sentiment volume

### Weather Data
- `brazil_month` - Calendar logic
- `export_seasonality_factor` - Seasonal calculation
- `brazil_temperature_c` - Weather API (NOAA, INMET, etc.)
- `brazil_precipitation_mm` - Weather API
- `growing_degree_days` - Weather calculation
- `export_capacity_index` - Custom index
- `harvest_pressure` - Agricultural logic
- `brazil_precip_30d_ma` - Weather moving average
- `brazil_temp_7d_ma` - Weather moving average
- `brazil_temp_c` - Weather API (different from above?)
- `brazil_precip_mm` - Weather API
- `brazil_conditions_score` - Weather composite
- `brazil_heat_stress_days` - Weather calculation
- `brazil_drought_days` - Weather calculation
- `brazil_flood_days` - Weather calculation
- `argentina_temp_c` - Weather API
- `argentina_precip_mm` - Weather API
- `argentina_conditions_score` - Weather composite
- `argentina_heat_stress_days` - Weather calculation
- `argentina_drought_days` - Weather calculation
- `argentina_flood_days` - Weather calculation
- `us_midwest_temp_c` - Weather API
- `us_midwest_precip_mm` - Weather API
- `us_midwest_conditions_score` - Weather composite
- `us_midwest_heat_stress_days` - Weather calculation
- `us_midwest_drought_days` - Weather calculation
- `us_midwest_flood_days` - Weather calculation
- `global_weather_risk_score` - Weather composite
- `weather_brazil_temp` - Weather API
- `weather_brazil_precip` - Weather API
- `weather_argentina_temp` - Weather API
- `weather_us_temp` - Weather API

### Trade/Policy Data
- `china_tariff_rate` - Policy/regulatory data
- `brazil_market_share` - Trade statistics
- `us_export_impact` - Trade analysis
- `tradewar_event_vol_mult` - Event analysis
- `trade_war_intensity` - Trade war analysis
- `trade_war_impact_score` - Trade war impact
- `argentina_export_tax` - Policy/regulatory data
- `argentina_china_sales_mt` - Trade statistics
- `argentina_competitive_threat` - Trade analysis
- `industrial_demand_index` - Industrial data
- `cn_imports` - China import statistics
- `cn_imports_fixed` - China import statistics (fixed)

### Event Calendar Data
- `is_wasde_day` - USDA calendar
- `is_fomc_day` - Fed calendar
- `is_china_holiday` - Chinese calendar
- `is_crop_report_day` - USDA calendar
- `is_stocks_day` - Trading calendar
- `is_planting_day` - Agricultural calendar
- `is_major_usda_day` - USDA calendar
- `event_impact_level` - Event analysis
- `days_to_next_event` - Event calendar
- `days_since_last_event` - Event calendar
- `pre_event_window` - Event calendar
- `post_event_window` - Event calendar
- `event_vol_mult` - Event analysis
- `is_options_expiry` - Options calendar
- `is_quarter_end` - Calendar
- `is_month_end` - Calendar

### Time/Date Features
- `day_of_week` - Calendar logic (but has 38.83% nulls - strange!)
- `day_of_week_num` - Calendar logic
- `day_of_month` - Calendar logic
- `month` - Calendar logic
- `month_num` - Calendar logic
- `quarter` - Calendar logic
- `seasonal_sin` - Seasonal calculation
- `seasonal_cos` - Seasonal calculation
- `seasonal_month_factor` - Seasonal calculation
- `volatility_regime` - Regime classification
- `time_weight` - Time weighting

### CFTC Data
- `cftc_commercial_long` - CFTC Commitments of Traders (97.07% nulls!)
- `cftc_commercial_short` - CFTC data
- `cftc_commercial_net` - CFTC data
- `cftc_managed_long` - CFTC data
- `cftc_managed_short` - CFTC data
- `cftc_managed_net` - CFTC data
- `cftc_open_interest` - CFTC data

### News Data
- `news_article_count` - News API (99.8% nulls!)
- `news_avg_score` - News sentiment (99.8% nulls!)

### FX Data (Advanced)
- `fx_usd_ars_30d_z` - USD/ARS z-score (needs ARS data)
- `fx_usd_myr_30d_z` - USD/MYR z-score (needs MYR data)

### Lead/Lag Analysis
- `palm_lead2_correlation` - Lead correlation
- `crude_lead1_correlation` - Lead correlation
- `vix_lead1_correlation` - Lead correlation
- `dxy_lead1_correlation` - Lead correlation
- `palm_direction_correct` - Direction accuracy
- `crude_direction_correct` - Direction accuracy
- `vix_inverse_correct` - Inverse accuracy
- `lead_signal_confidence` - Confidence score
- `momentum_divergence` - Divergence detection
- `palm_accuracy_30d` - Accuracy metric
- `crude_accuracy_30d` - Accuracy metric
- `leadlag_zl_price` - Lead-lag price
- `vix_spike_lag1` - VIX spike detection

### Supply/Demand
- `supply_demand_ratio` - Supply/demand analysis

### Other
- `rn` - Row number? (38.19% nulls - strange!)
- `is_low_vol` - Volatility classification
- `is_normal_vol` - Volatility classification
- `is_high_vol` - Volatility classification

---

## 📊 PRIORITY RANKING

### High Priority (Easy Wins - Direct Data)
1. **FRED Economic Data** (~15 columns, 28-99% nulls)
   - `treasury_10y_yield` (28.7%)
   - `econ_gdp_growth` (99.46%)
   - `econ_inflation_rate` (99.12%)
   - `econ_unemployment_rate` (96.48%)
   - `unemployment_rate` (99.46%)
   - `gdp_growth` (99.46%)
   - `cpi_yoy` (99.46%)
   - `usd_cny_rate` (38.83%)
   - `usd_brl_rate` (38.83%)
   - `dollar_index` (38.83%)
   - `fed_funds_rate` (38.83%)
   - `yield_curve` (38.83%)

2. **Yahoo Finance Price Data** (~18 columns, 28-41% nulls)
   - `zl_price_current` (28.17%)
   - `zl_volume` (28.51%)
   - `target_1w` (29.19%)
   - `target_1m` (34.13%)
   - `target_3m` (35.01%)
   - `target_6m` (41.42%)
   - `corn_price` (38.83%)
   - `wheat_price` (38.83%)
   - `crude_oil_wti_new` (38.83%)
   - `palm_price` (38.39%)
   - `soybean_meal_price` (28.17%)
   - `vix_level` (38.53%)
   - `dxy_level` (38.83%)

3. **Technical Indicators** (~50 columns, calculated from prices)
   - All RSI, MACD, Bollinger Bands, moving averages, correlations
   - These automatically fill once base prices are available

### Medium Priority (Custom Logic Required)
- Weather data (need NOAA/INMET APIs)
- Social sentiment (need APIs/scraping)
- CFTC data (need CFTC API)
- Event calendar (need calendar logic)

### Low Priority (May Not Be Worth Filling)
- Columns with 97%+ nulls (CFTC, news)
- Highly derived features requiring multiple sources

---

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: FRED Data Integration (High Impact, Low Effort)
1. Expand `scripts/fetch_fred_economic_data.py` to fetch ALL FRED series
2. Add series: DGS10, FEDFUNDS, DEXCHUS, DEXBZUS, DTWEXBGS, VIXCLS
3. Calculate derived columns: yield_curve, real_yield, 7d changes
4. **Expected Impact:** Fill ~20 columns, reduce nulls by 28-99%

### Phase 2: Yahoo Finance Data Integration (High Impact, Medium Effort)
1. Fetch all commodity futures prices (ZL, ZC, ZW, CL, FCPO, ZM)
2. Fetch VIX and DXY
3. Calculate all technical indicators from prices
4. Calculate all correlation features
5. **Expected Impact:** Fill ~68 columns, reduce nulls by 28-51%

### Phase 3: Derived Features (Medium Impact, High Effort)
1. Calculate crush margins from prices
2. Calculate unit conversions (cwt, bushel, ton)
3. Calculate seasonal features
4. **Expected Impact:** Fill ~10-15 additional columns

**Total Potential Fill:** ~88-103 columns out of 209 (42-49% of columns)

---

## 📝 NOTES

- **FRED API Key:** Already tested and working ✅
- **Yahoo Finance:** Need to verify ticker symbols and data availability
- **Date Alignment:** Some FRED data is monthly/quarterly - need forward fill logic
- **Data Quality:** Some columns have strange null patterns (e.g., day_of_week with 38% nulls)
- **Prioritization:** Focus on columns with <50% nulls first (easier wins)


