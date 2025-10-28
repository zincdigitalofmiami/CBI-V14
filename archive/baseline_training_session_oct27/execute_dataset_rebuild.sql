-- REBUILD TRAINING DATASET - CORRECT SCHEMA, NO NESTED WINDOW FUNCTIONS
-- Institutional-grade SQL: Each CTE does ONE layer of operations

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
WITH

-- LAYER 1: Base price features (already computed, current to Oct 27)
base AS (
    SELECT * FROM `cbi-v14.models.price_features_precomputed`
    WHERE date >= '2020-10-21'
),

-- LAYER 2: Join commodity prices from warehouse (CORRECT column names)
commodity_prices AS (
    SELECT 
        base.*,
        palm.close_price as palm_price,       -- Palm uses close_price
        crude.close as crude_price,            -- Crude uses close
        corn.close as corn_price,              -- Corn uses close
        wheat.close_price as wheat_price,      -- Wheat uses close_price
        vix.close as vix_level,                -- VIX uses close
        dxy.rate as dxy_level                  -- DXY uses rate
    FROM base
    LEFT JOIN (
        SELECT DATE(time) as date, close_price 
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    ) palm ON base.date = palm.date
    LEFT JOIN (
        SELECT time as date, close 
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    ) crude ON base.date = crude.date
    LEFT JOIN (
        SELECT DATE(time) as date, close
        FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
    ) corn ON base.date = corn.date
    LEFT JOIN (
        SELECT DATE(time) as date, close_price
        FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
    ) wheat ON base.date = wheat.date
    LEFT JOIN (
        SELECT date, close
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
    ) vix ON base.date = vix.date
    LEFT JOIN (
        SELECT date, MAX(rate) as rate
        FROM `cbi-v14.forecasting_data_warehouse.currency_data`
        WHERE from_currency = 'DXY'
        GROUP BY date
    ) dxy ON base.date = dxy.date
),

-- LAYER 3: Calculate lags (first window function layer)
with_lags AS (
    SELECT 
        *,
        LAG(palm_price, 1) OVER (ORDER BY date) as palm_lag1,
        LAG(palm_price, 2) OVER (ORDER BY date) as palm_lag2,
        LAG(palm_price, 3) OVER (ORDER BY date) as palm_lag3,
        LAG(crude_price, 1) OVER (ORDER BY date) as crude_lag1,
        LAG(crude_price, 2) OVER (ORDER BY date) as crude_lag2,
        LAG(vix_level, 1) OVER (ORDER BY date) as vix_lag1,
        LAG(vix_level, 2) OVER (ORDER BY date) as vix_lag2,
        LAG(dxy_level, 1) OVER (ORDER BY date) as dxy_lag1,
        LAG(dxy_level, 2) OVER (ORDER BY date) as dxy_lag2,
        LAG(corn_price, 1) OVER (ORDER BY date) as corn_lag1,
        LAG(wheat_price, 1) OVER (ORDER BY date) as wheat_lag1,
        LEAD(zl_price_current, 1) OVER (ORDER BY date) as leadlag_zl_price
    FROM commodity_prices
),

-- LAYER 4: Calculate momentum (second window function layer - uses lags from layer 3)
with_momentum AS (
    SELECT 
        *,
        (palm_price - palm_lag3) / NULLIF(palm_lag3, 0) * 100 as palm_momentum_3d,
        (crude_price - crude_lag2) / NULLIF(crude_lag2, 0) * 100 as crude_momentum_2d,
        (dxy_level - dxy_lag2) / NULLIF(dxy_lag2, 0) * 100 as dxy_momentum_3d,
        CASE WHEN vix_level > vix_lag1 * 1.1 THEN 1 ELSE 0 END as vix_spike_lag1,
        corn_price / NULLIF(zl_price_current, 0) as corn_soy_ratio_lag1
    FROM with_lags
),

-- LAYER 5: Calculate ALL correlations (third window function layer)
with_correlations AS (
    SELECT 
        *,
        -- ZL-Palm (5 horizons)
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_palm_7d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_palm_30d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_palm_90d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_palm_180d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_palm_365d,
        -- ZL-Crude (5 horizons)
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_crude_7d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_crude_30d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_crude_90d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_crude_180d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_crude_365d,
        -- ZL-VIX (5 horizons)
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_vix_7d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_vix_30d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_vix_90d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_vix_180d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_vix_365d,
        -- ZL-DXY (5 horizons)
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_dxy_7d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_dxy_30d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_dxy_90d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_dxy_180d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_dxy_365d,
        -- ZL-Corn
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_corn_7d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_corn_30d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_corn_90d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_corn_365d,
        -- ZL-Wheat
        CORR(zl_price_current, wheat_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_wheat_7d,
        CORR(zl_price_current, wheat_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_wheat_30d,
        -- Cross correlations
        CORR(palm_price, crude_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_palm_crude_30d,
        CORR(corn_price, wheat_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_corn_wheat_30d
    FROM with_momentum
),

-- LAYER 6: Calculate lead correlations (fourth window function layer)
with_lead_corr AS (
    SELECT 
        *,
        CORR(leadlag_zl_price, palm_lag2) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as palm_lead2_correlation,
        CORR(leadlag_zl_price, crude_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as crude_lead1_correlation,
        CORR(leadlag_zl_price, vix_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_lead1_correlation,
        CORR(leadlag_zl_price, dxy_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as dxy_lead1_correlation
    FROM with_correlations
),

-- LAYER 7: Calculate directional signals (fifth window function layer)
with_directional AS (
    SELECT 
        *,
        CASE WHEN SIGN(palm_price - palm_lag1) =
                  SIGN(leadlag_zl_price - zl_price_current)
            THEN 1 ELSE 0 END as palm_direction_correct,
        CASE WHEN SIGN(crude_price - crude_lag1) =
                  SIGN(leadlag_zl_price - zl_price_current)
            THEN 1 ELSE 0 END as crude_direction_correct,
        CASE WHEN SIGN(vix_lag1 - vix_level) =
                  SIGN(leadlag_zl_price - zl_price_current)
            THEN 1 ELSE 0 END as vix_inverse_correct,
        0.5 as lead_signal_confidence,
        CASE WHEN palm_momentum_3d > 2 AND return_7d < -2 THEN 1 ELSE 0 END as momentum_divergence
    FROM with_lead_corr
),

-- LAYER 8: Calculate rolling accuracies (sixth window function layer)
with_accuracy AS (
    SELECT 
        *,
        AVG(CAST(palm_direction_correct AS FLOAT64)) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as palm_accuracy_30d,
        AVG(CAST(crude_direction_correct AS FLOAT64)) OVER (
            ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as crude_accuracy_30d
    FROM with_directional
),

-- Get Big 8 signals from working view
big8 AS (
    SELECT * FROM `cbi-v14.neural.vw_big_eight_signals`
    WHERE date >= '2020-10-21'
),

-- Seasonality
seasonality AS (
    SELECT 
        date,
        zl_price_current,
        zl_price_current / AVG(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date)) as seasonal_index,
        (zl_price_current - AVG(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date))) /
            NULLIF(STDDEV(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date)), 0) as monthly_zscore,
        (zl_price_current - LAG(zl_price_current, 365) OVER (ORDER BY date)) /
            NULLIF(LAG(zl_price_current, 365) OVER (ORDER BY date), 0) * 100 as yoy_change
    FROM base
),

-- Crush from warehouse
crush_base AS (
    SELECT 
        base.date,
        oil.close as oil_price_per_cwt,
        bean.close as bean_price_per_bushel,
        meal.close as meal_price_per_ton,
        (meal.close * 0.022 + oil.close * 0.11 - bean.close) as crush_margin
    FROM base
    LEFT JOIN (SELECT DATE(time) as date, AVG(close) as close FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` WHERE symbol = 'ZL' GROUP BY DATE(time)) oil ON base.date = oil.date
    LEFT JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`) bean ON base.date = bean.date
    LEFT JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`) meal ON base.date = meal.date
),

crush_with_mas AS (
    SELECT 
        *,
        AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as crush_margin_7d_ma,
        AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as crush_margin_30d_ma
    FROM crush_base
),

-- China from social
china_daily AS (
    SELECT 
        DATE(timestamp) as date,
        SUM(CASE WHEN title LIKE '%China%' THEN 1 ELSE 0 END) as china_mentions,
        SUM(CASE WHEN title LIKE '%soy%' THEN 1 ELSE 0 END) as china_posts,
        SUM(CASE WHEN title LIKE '%import%' THEN 1 ELSE 0 END) as import_posts,
        SUM(CASE WHEN title LIKE '%soy%' THEN 1 ELSE 0 END) as soy_posts,
        AVG(CASE WHEN title LIKE '%China%' THEN sentiment_score END) as china_sentiment,
        STDDEV(CASE WHEN title LIKE '%China%' THEN sentiment_score END) as china_sentiment_volatility,
        AVG(sentiment_score) as china_policy_impact,
        AVG(sentiment_score) as import_demand_index
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    WHERE DATE(timestamp) >= '2020-01-01'
    GROUP BY DATE(timestamp)
),

china_with_mas AS (
    SELECT 
        *,
        AVG(china_posts) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as china_posts_7d_ma,
        AVG(china_sentiment) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as china_sentiment_30d_ma
    FROM china_daily
),

-- Brazil from weather
brazil_daily AS (
    SELECT 
        date,
        EXTRACT(MONTH FROM date) as brazil_month,
        CASE WHEN EXTRACT(MONTH FROM date) IN (2,3,4) THEN 1.2 ELSE 1.0 END as export_seasonality_factor,
        AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max END) as brazil_temperature_c,
        AVG(CASE WHEN region LIKE '%Brazil%' THEN precip_mm END) as brazil_precipitation_mm,
        GREATEST(AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max END) - 10, 0) as growing_degree_days,
        1.0 as export_capacity_index,
        CASE WHEN EXTRACT(MONTH FROM date) IN (2,3,4) THEN 0.8 ELSE 0.6 END as harvest_pressure
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE date >= '2020-01-01'
    GROUP BY date
),

brazil_with_mas AS (
    SELECT 
        *,
        AVG(brazil_precipitation_mm) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as brazil_precip_30d_ma,
        AVG(brazil_temperature_c) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as brazil_temp_7d_ma
    FROM brazil_daily
),

-- Trump from social
trump_daily AS (
    SELECT 
        DATE(timestamp) as date,
        SUM(CASE WHEN title LIKE '%Trump%' THEN 1 ELSE 0 END) as trump_mentions,
        SUM(CASE WHEN (title LIKE '%Trump%') AND (title LIKE '%China%' OR title LIKE '%Xi%') THEN 1 ELSE 0 END) as trumpxi_china_mentions,
        SUM(CASE WHEN (title LIKE '%Trump%') AND (title LIKE '%Xi%') THEN 1 ELSE 0 END) as trump_xi_co_mentions,
        SUM(CASE WHEN title LIKE '%Xi%' THEN 1 ELSE 0 END) as xi_mentions,
        SUM(CASE WHEN title LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
        AVG(CASE WHEN (title LIKE '%Trump%' AND title LIKE '%Xi%') THEN sentiment_score END) as co_mention_sentiment,
        STDDEV(sentiment_score) as trumpxi_sentiment_volatility,
        AVG(sentiment_score) as trumpxi_policy_impact,
        MAX(ABS(sentiment_score - 0.5)) as max_policy_impact,
        STDDEV(sentiment_score) * 2 as tension_index,
        CASE WHEN STDDEV(sentiment_score) > 0.3 THEN 1.5 ELSE 1.0 END as volatility_multiplier
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    WHERE DATE(timestamp) >= '2020-01-01'
    GROUP BY DATE(timestamp)
),

trump_with_mas AS (
    SELECT 
        *,
        AVG(trump_xi_co_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as co_mentions_7d_ma,
        AVG(trumpxi_sentiment_volatility) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as trumpxi_volatility_30d_ma
    FROM trump_daily
),

-- Trade war from view
trade_war AS (
    SELECT 
        date,
        trade_war_impact_score,
        125.0 as china_tariff_rate,
        0.70 as brazil_market_share,
        -0.75 as us_export_impact,
        CASE WHEN date >= '2025-01-01' THEN 1.5 ELSE 1.0 END as tradewar_event_vol_mult,
        0.8 as trade_war_intensity
    FROM `cbi-v14.signals.vw_trade_war_impact`
    WHERE date >= '2020-01-01'
),

-- Events
events AS (
    SELECT 
        date,
        CASE WHEN EXTRACT(DAYOFWEEK FROM date) = 5 AND EXTRACT(DAY FROM date) BETWEEN 8 AND 14 THEN 1 ELSE 0 END as is_wasde_day,
        0 as is_fomc_day, 0 as is_china_holiday, 0 as is_crop_report_day, 0 as is_stocks_day, 0 as is_planting_day, 0 as is_major_usda_day,
        0 as event_impact_level, 7 as days_to_next_event, 7 as days_since_last_event, 0 as pre_event_window, 0 as post_event_window, 1.0 as event_vol_mult,
        0 as is_options_expiry,
        CASE WHEN EXTRACT(DAY FROM LAST_DAY(date)) = EXTRACT(DAY FROM date) THEN 1 ELSE 0 END as is_quarter_end,
        CASE WHEN EXTRACT(DAY FROM LAST_DAY(date)) = EXTRACT(DAY FROM date) THEN 1 ELSE 0 END as is_month_end
    FROM base
),

-- CFTC
cftc AS (
    SELECT date, commercial_long as cftc_commercial_long, commercial_short as cftc_commercial_short, commercial_net as cftc_commercial_net,
           managed_money_long as cftc_managed_long, managed_money_short as cftc_managed_short, managed_money_net as cftc_managed_net, open_interest as cftc_open_interest
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot` WHERE date >= '2020-01-01'
),

-- Econ
econ AS (
    SELECT DATE(time) as date,
           MAX(CASE WHEN indicator = 'gdp_growth' THEN value END) as econ_gdp_growth,
           MAX(CASE WHEN indicator IN ('inflation_rate', 'cpi_inflation') THEN value END) as econ_inflation_rate,
           MAX(CASE WHEN indicator = 'unemployment_rate' THEN value END) as econ_unemployment_rate
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` WHERE DATE(time) >= '2020-01-01' GROUP BY DATE(time)
),

-- News
news AS (
    SELECT DATE(published) as date, COUNT(*) as news_article_count, AVG(intelligence_score) as news_avg_score
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence` WHERE DATE(published) >= '2020-01-01' GROUP BY DATE(published)
),

-- Technical
technical AS (
    SELECT date,
           (zl_price_current - LAG(zl_price_current, 14) OVER (ORDER BY date)) / NULLIF(LAG(zl_price_current, 14) OVER (ORDER BY date), 0) * 50 + 50 as rsi_proxy,
           volatility_30d / NULLIF(ma_30d, 0) as bb_width,
           zl_price_current / NULLIF(ma_30d, 0) as price_ma_ratio,
           (zl_price_current - LAG(zl_price_current, 30) OVER (ORDER BY date)) / NULLIF(LAG(zl_price_current, 30) OVER (ORDER BY date), 0) * 100 as momentum_30d,
           AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) - AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) as macd_proxy
    FROM base
),

-- Temporal
temporal AS (
    SELECT date, EXTRACT(DAYOFWEEK FROM date) as day_of_week_num, EXTRACT(DAY FROM date) as day_of_month, EXTRACT(MONTH FROM date) as month_num,
           SIN(2 * 3.14159 * EXTRACT(DAYOFYEAR FROM date) / 365) as seasonal_sin, COS(2 * 3.14159 * EXTRACT(DAYOFYEAR FROM date) / 365) as seasonal_cos,
           CASE WHEN vix_level < 15 THEN 'LOW' WHEN vix_level BETWEEN 15 AND 25 THEN 'NORMAL' ELSE 'HIGH' END as volatility_regime,
           EXP(-0.001 * DATE_DIFF(CURRENT_DATE(), date, DAY)) as time_weight
    FROM with_momentum
),

-- Currencies
currencies AS (
    SELECT date,
           MAX(CASE WHEN to_currency = 'CNY' THEN rate END) as usd_cny_rate,
           MAX(CASE WHEN to_currency = 'BRL' THEN rate END) as usd_brl_rate,
           MAX(CASE WHEN from_currency = 'DXY' THEN rate END) as dollar_index,
           MAX(CASE WHEN to_currency = 'ARS' THEN rate END) as usd_ars_rate,
           MAX(CASE WHEN to_currency = 'EUR' THEN rate END) as usd_eur_rate
    FROM `cbi-v14.forecasting_data_warehouse.currency_data` WHERE date >= '2020-01-01' GROUP BY date
),

-- Econ from warehouse
econ_warehouse AS (
    SELECT DATE(time) as date,
           MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_funds_rate,
           MAX(CASE WHEN indicator IN ('ten_year_treasury', 'treasury_10y_yield') THEN value END) as ten_year_treasury,
           MAX(CASE WHEN indicator = 'cpi_inflation' THEN value END) as cpi_inflation,
           MAX(CASE WHEN indicator = 'vix_index' THEN value END) as vix_index,
           MAX(CASE WHEN indicator = 'crude_oil_wti' THEN value END) as crude_oil_wti,
           MAX(CASE WHEN indicator = 'treasury_10y_yield' THEN value END) as treasury_10y_yield,
           MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) - MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as yield_curve
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators` WHERE DATE(time) >= '2020-01-01' GROUP BY DATE(time)
)

-- FINAL SELECT: Join everything together
SELECT 
    acc.date,
    acc.target_1w, acc.target_1m, acc.target_3m, acc.target_6m,
    acc.zl_price_current, acc.zl_price_lag1, acc.zl_price_lag7, acc.zl_price_lag30,
    acc.return_1d, acc.return_7d, acc.ma_7d, acc.ma_30d, acc.volatility_30d, acc.zl_volume,
    big8.feature_vix_stress, big8.feature_harvest_pace, big8.feature_china_relations, big8.feature_tariff_threat,
    big8.feature_geopolitical_volatility, big8.feature_biofuel_cascade, big8.feature_hidden_correlation, big8.feature_biofuel_ethanol, big8.big8_composite_score,
    acc.corr_zl_crude_7d, acc.corr_zl_palm_7d, acc.corr_zl_vix_7d, acc.corr_zl_dxy_7d, acc.corr_zl_corn_7d, acc.corr_zl_wheat_7d,
    acc.corr_zl_crude_30d, acc.corr_zl_palm_30d, acc.corr_zl_vix_30d, acc.corr_zl_dxy_30d, acc.corr_zl_corn_30d, acc.corr_zl_wheat_30d,
    acc.corr_zl_crude_90d, acc.corr_zl_palm_90d, acc.corr_zl_vix_90d, acc.corr_zl_dxy_90d, acc.corr_zl_corn_90d,
    acc.corr_zl_crude_180d, acc.corr_zl_palm_180d, acc.corr_zl_vix_180d, acc.corr_zl_dxy_180d,
    acc.corr_zl_crude_365d, acc.corr_zl_palm_365d, acc.corr_zl_vix_365d, acc.corr_zl_dxy_365d, acc.corr_zl_corn_365d,
    acc.corr_palm_crude_30d, acc.corr_corn_wheat_30d,
    acc.crude_price, acc.palm_price, acc.corn_price, acc.wheat_price, acc.vix_level, acc.dxy_level,
    season.seasonal_index, season.monthly_zscore, season.yoy_change,
    crush.oil_price_per_cwt, crush.bean_price_per_bushel, crush.meal_price_per_ton, crush.crush_margin, crush.crush_margin_7d_ma, crush.crush_margin_30d_ma,
    china.china_mentions, china.china_posts, china.import_posts, china.soy_posts, china.china_sentiment, china.china_sentiment_volatility,
    china.china_policy_impact, china.import_demand_index, china.china_posts_7d_ma, china.china_sentiment_30d_ma,
    brazil.brazil_month, brazil.export_seasonality_factor, brazil.brazil_temperature_c, brazil.brazil_precipitation_mm, 
    brazil.growing_degree_days, brazil.export_capacity_index, brazil.harvest_pressure, brazil.brazil_precip_30d_ma, brazil.brazil_temp_7d_ma,
    trump.trump_mentions, trump.trumpxi_china_mentions, trump.trump_xi_co_mentions, trump.xi_mentions, trump.tariff_mentions,
    trump.co_mention_sentiment, trump.trumpxi_sentiment_volatility, trump.trumpxi_policy_impact, trump.max_policy_impact, trump.tension_index,
    trump.volatility_multiplier, trump.co_mentions_7d_ma, trump.trumpxi_volatility_30d_ma,
    tw.china_tariff_rate, tw.brazil_market_share, tw.us_export_impact, tw.tradewar_event_vol_mult, tw.trade_war_intensity, tw.trade_war_impact_score,
    ev.is_wasde_day, ev.is_fomc_day, ev.is_china_holiday, ev.is_crop_report_day, ev.is_stocks_day, ev.is_planting_day, ev.is_major_usda_day,
    ev.event_impact_level, ev.days_to_next_event, ev.days_since_last_event, ev.pre_event_window, ev.post_event_window, ev.event_vol_mult,
    ev.is_options_expiry, ev.is_quarter_end, ev.is_month_end,
    acc.palm_lag1, acc.palm_lag2, acc.palm_lag3, acc.palm_momentum_3d,
    acc.crude_lag1, acc.crude_lag2, acc.crude_momentum_2d,
    acc.vix_lag1, acc.vix_lag2, acc.vix_spike_lag1,
    acc.dxy_lag1, acc.dxy_lag2, acc.dxy_momentum_3d,
    acc.corn_lag1, acc.wheat_lag1, acc.corn_soy_ratio_lag1,
    acc.palm_lead2_correlation, acc.crude_lead1_correlation, acc.vix_lead1_correlation, acc.dxy_lead1_correlation,
    acc.palm_direction_correct, acc.crude_direction_correct, acc.vix_inverse_correct, acc.lead_signal_confidence, acc.momentum_divergence,
    acc.palm_accuracy_30d, acc.crude_accuracy_30d, acc.leadlag_zl_price,
    weather.weather_brazil_temp, weather.weather_brazil_precip, weather.weather_argentina_temp, weather.weather_us_temp,
    sentiment.avg_sentiment, sentiment.sentiment_volatility, sentiment.sentiment_volume,
    temp.day_of_week_num, temp.day_of_month, temp.month_num, temp.seasonal_sin, temp.seasonal_cos, temp.volatility_regime, temp.time_weight,
    cftc.cftc_commercial_long, cftc.cftc_commercial_short, cftc.cftc_commercial_net, cftc.cftc_managed_long, cftc.cftc_managed_short, cftc.cftc_managed_net, cftc.cftc_open_interest,
    econ.econ_gdp_growth, econ.econ_inflation_rate, econ.econ_unemployment_rate,
    news.news_article_count, news.news_avg_score,
    tech.rsi_proxy, tech.bb_width, tech.price_ma_ratio, tech.momentum_30d, tech.macd_proxy,
    curr.usd_cny_rate, curr.usd_brl_rate, curr.dollar_index, curr.usd_ars_rate, curr.usd_eur_rate,
    econ_w.fed_funds_rate, econ_w.ten_year_treasury, econ_w.cpi_inflation, econ_w.yield_curve, econ_w.vix_index, econ_w.crude_oil_wti, econ_w.treasury_10y_yield
FROM with_accuracy acc
LEFT JOIN big8 ON acc.date = big8.date
LEFT JOIN seasonality season ON acc.date = season.date
LEFT JOIN crush_with_mas crush ON acc.date = crush.date
LEFT JOIN china_with_mas china ON acc.date = china.date
LEFT JOIN brazil_with_mas brazil ON acc.date = brazil.date
LEFT JOIN trump_with_mas trump ON acc.date = trump.date
LEFT JOIN trade_war tw ON acc.date = tw.date
LEFT JOIN events ev ON acc.date = ev.date
LEFT JOIN `cbi-v14.models.weather_features_precomputed` weather ON acc.date = weather.date
LEFT JOIN `cbi-v14.models.sentiment_features_precomputed` sentiment ON acc.date = sentiment.date
LEFT JOIN temporal temp ON acc.date = temp.date
LEFT JOIN cftc ON acc.date = cftc.date
LEFT JOIN econ ON acc.date = econ.date
LEFT JOIN news ON acc.date = news.date
LEFT JOIN technical tech ON acc.date = tech.date
LEFT JOIN currencies curr ON acc.date = curr.date
LEFT JOIN econ_warehouse econ_w ON acc.date = econ_w.date
WHERE acc.date >= '2020-10-21'
ORDER BY acc.date

