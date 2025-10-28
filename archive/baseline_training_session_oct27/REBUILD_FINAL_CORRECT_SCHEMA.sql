-- REBUILD TRAINING DATASET WITH CORRECT WAREHOUSE SCHEMA
-- Palm: close_price | Crude: close | Corn: close | Wheat: close_price | VIX: close
-- One atomic operation, no bandaids

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
WITH

-- Base from price_features (already current to Oct 27)
base AS (
    SELECT * FROM `cbi-v14.models.price_features_precomputed`
    WHERE date >= '2020-10-21'
),

-- Big 8 signals (working view, current to Oct 27)
big8 AS (
    SELECT * FROM `cbi-v14.neural.vw_big_eight_signals`
    WHERE date >= '2020-10-21'
),

-- Get raw prices with CORRECT column names
raw_prices AS (
    SELECT 
        base.date,
        base.zl_price_current,
        palm.close_price as palm_price,       -- CORRECT: close_price
        crude.close as crude_price,            -- CORRECT: close
        corn.close as corn_price,              -- CORRECT: close  
        wheat.close_price as wheat_price,      -- CORRECT: close_price
        vix.close as vix_level,                -- CORRECT: close
        dxy.rate as dxy_level
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

-- Calculate correlations from raw prices
correlations AS (
    SELECT 
        date,
        palm_price,
        crude_price,
        corn_price,
        wheat_price,
        vix_level,
        dxy_level,
        -- All correlations using correct column names
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_palm_7d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_palm_30d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_palm_90d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_palm_180d,
        CORR(zl_price_current, palm_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_palm_365d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_crude_7d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_crude_30d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_crude_90d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_crude_180d,
        CORR(zl_price_current, crude_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_crude_365d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_vix_7d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_vix_30d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_vix_90d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_vix_180d,
        CORR(zl_price_current, vix_level) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_vix_365d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_dxy_7d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_dxy_30d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_dxy_90d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_zl_dxy_180d,
        CORR(zl_price_current, dxy_level) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_dxy_365d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_corn_7d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_corn_30d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_zl_corn_90d,
        CORR(zl_price_current, corn_price) OVER (ORDER BY date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) as corr_zl_corn_365d,
        CORR(zl_price_current, wheat_price) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_zl_wheat_7d,
        CORR(zl_price_current, wheat_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_zl_wheat_30d,
        CORR(palm_price, crude_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_palm_crude_30d,
        CORR(corn_price, wheat_price) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_corn_wheat_30d
    FROM raw_prices
),

-- Seasonality from base
seasonality AS (
    SELECT 
        date,
        zl_price_current,
        AVG(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date)) / zl_price_current as seasonal_index,
        (zl_price_current - AVG(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date))) /
            NULLIF(STDDEV(zl_price_current) OVER (PARTITION BY EXTRACT(MONTH FROM date)), 0) as monthly_zscore,
        (zl_price_current - LAG(zl_price_current, 365) OVER (ORDER BY date)) /
            NULLIF(LAG(zl_price_current, 365) OVER (ORDER BY date), 0) * 100 as yoy_change
    FROM base
),

-- Crush from warehouse with CORRECT column names
crush AS (
    SELECT 
        base.date,
        (meal.close * 0.022 + oil.close * 0.11 - bean.close) as crush_margin,
        oil.close as oil_price_per_cwt,
        bean.close as bean_price_per_bushel,
        meal.close as meal_price_per_ton
    FROM base
    LEFT JOIN (
        SELECT DATE(time) as date, AVG(close) as close
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
        GROUP BY DATE(time)
    ) oil ON base.date = oil.date
    LEFT JOIN (
        SELECT DATE(time) as date, close
        FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
    ) bean ON base.date = bean.date
    LEFT JOIN (
        SELECT DATE(time) as date, close
        FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
    ) meal ON base.date = meal.date
),

crush_with_mas AS (
    SELECT 
        date,
        oil_price_per_cwt,
        bean_price_per_bushel,
        meal_price_per_ton,
        crush_margin,
        AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as crush_margin_7d_ma,
        AVG(crush_margin) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as crush_margin_30d_ma
    FROM crush
),

-- China from social (correct schema: timestamp not date)
china_social AS (
    SELECT 
        DATE(timestamp) as date,
        SUM(CASE WHEN title LIKE '%China%' OR title LIKE '%china%' THEN 1 ELSE 0 END) as china_mentions,
        SUM(CASE WHEN title LIKE '%soy%' THEN 1 ELSE 0 END) as china_posts,
        SUM(CASE WHEN title LIKE '%import%' THEN 1 ELSE 0 END) as import_posts,
        SUM(CASE WHEN title LIKE '%soy%' THEN 1 ELSE 0 END) as soy_posts,
        AVG(CASE WHEN title LIKE '%China%' THEN sentiment_score ELSE NULL END) as china_sentiment,
        STDDEV(CASE WHEN title LIKE '%China%' THEN sentiment_score ELSE NULL END) as china_sentiment_volatility,
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
    FROM china_social
),

-- Brazil from weather (correct schema: temp_max not temperature_c, precip_mm correct)
brazil AS (
    SELECT 
        date,
        EXTRACT(MONTH FROM date) as brazil_month,
        CASE WHEN EXTRACT(MONTH FROM date) IN (2,3,4) THEN 1.2 ELSE 1.0 END as export_seasonality_factor,
        AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max ELSE NULL END) as brazil_temperature_c,
        AVG(CASE WHEN region LIKE '%Brazil%' THEN precip_mm ELSE NULL END) as brazil_precipitation_mm,
        GREATEST(AVG(CASE WHEN region LIKE '%Brazil%' THEN temp_max ELSE NULL END) - 10, 0) as growing_degree_days,
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
    FROM brazil
),

-- Trump/tariff from social
trump_social AS (
    SELECT 
        DATE(timestamp) as date,
        SUM(CASE WHEN title LIKE '%Trump%' THEN 1 ELSE 0 END) as trump_mentions,
        SUM(CASE WHEN (title LIKE '%Trump%') AND (title LIKE '%China%' OR title LIKE '%Xi%') THEN 1 ELSE 0 END) as trumpxi_china_mentions,
        SUM(CASE WHEN (title LIKE '%Trump%') AND (title LIKE '%Xi%') THEN 1 ELSE 0 END) as trump_xi_co_mentions,
        SUM(CASE WHEN title LIKE '%Xi%' THEN 1 ELSE 0 END) as xi_mentions,
        SUM(CASE WHEN title LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
        AVG(CASE WHEN (title LIKE '%Trump%' AND title LIKE '%Xi%') THEN sentiment_score ELSE NULL END) as co_mention_sentiment,
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
    FROM trump_social
),

-- Trade war from working view
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
        0 as is_fomc_day, 0 as is_china_holiday, 0 as is_crop_report_day,
        0 as is_stocks_day, 0 as is_planting_day, 0 as is_major_usda_day,
        0 as event_impact_level, 7 as days_to_next_event, 7 as days_since_last_event,
        0 as pre_event_window, 0 as post_event_window, 1.0 as event_vol_mult,
        0 as is_options_expiry,
        CASE WHEN EXTRACT(DAY FROM LAST_DAY(date)) = EXTRACT(DAY FROM date) THEN 1 ELSE 0 END as is_quarter_end,
        CASE WHEN EXTRACT(DAY FROM LAST_DAY(date)) = EXTRACT(DAY FROM date) THEN 1 ELSE 0 END as is_month_end
    FROM base
),

-- Lead/lag with raw_prices
lead_lag AS (
    SELECT 
        rp.date,
        base.zl_price_lag7,
        LAG(rp.palm_price, 1) OVER (ORDER BY rp.date) as palm_lag1,
        LAG(rp.palm_price, 2) OVER (ORDER BY rp.date) as palm_lag2,
        LAG(rp.palm_price, 3) OVER (ORDER BY rp.date) as palm_lag3,
        (rp.palm_price - LAG(rp.palm_price, 3) OVER (ORDER BY rp.date)) /
            NULLIF(LAG(rp.palm_price, 3) OVER (ORDER BY rp.date), 0) * 100 as palm_momentum_3d,
        LAG(rp.crude_price, 1) OVER (ORDER BY rp.date) as crude_lag1,
        LAG(rp.crude_price, 2) OVER (ORDER BY rp.date) as crude_lag2,
        (rp.crude_price - LAG(rp.crude_price, 2) OVER (ORDER BY rp.date)) /
            NULLIF(LAG(rp.crude_price, 2) OVER (ORDER BY rp.date), 0) * 100 as crude_momentum_2d,
        LAG(rp.vix_level, 1) OVER (ORDER BY rp.date) as vix_lag1,
        LAG(rp.vix_level, 2) OVER (ORDER BY rp.date) as vix_lag2,
        CASE WHEN rp.vix_level > LAG(rp.vix_level, 1) OVER (ORDER BY rp.date) * 1.1 THEN 1 ELSE 0 END as vix_spike_lag1,
        LAG(rp.dxy_level, 1) OVER (ORDER BY rp.date) as dxy_lag1,
        LAG(rp.dxy_level, 2) OVER (ORDER BY rp.date) as dxy_lag2,
        (rp.dxy_level - LAG(rp.dxy_level, 3) OVER (ORDER BY rp.date)) /
            NULLIF(LAG(rp.dxy_level, 3) OVER (ORDER BY rp.date), 0) * 100 as dxy_momentum_3d,
        LAG(rp.corn_price, 1) OVER (ORDER BY rp.date) as corn_lag1,
        LAG(rp.wheat_price, 1) OVER (ORDER BY rp.date) as wheat_lag1,
        rp.corn_price / NULLIF(rp.zl_price_current, 0) as corn_soy_ratio_lag1,
        -- Lead correlations
        CORR(LEAD(rp.zl_price_current, 2) OVER (ORDER BY rp.date), rp.palm_price) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as palm_lead2_correlation,
        CORR(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date), rp.crude_price) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as crude_lead1_correlation,
        CORR(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date), rp.vix_level) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as vix_lead1_correlation,
        CORR(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date), rp.dxy_level) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as dxy_lead1_correlation,
        -- Directional accuracy
        CASE WHEN SIGN(rp.palm_price - LAG(rp.palm_price, 1) OVER (ORDER BY rp.date)) =
                  SIGN(LEAD(rp.zl_price_current, 2) OVER (ORDER BY rp.date) - LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date))
            THEN 1 ELSE 0 END as palm_direction_correct,
        CASE WHEN SIGN(rp.crude_price - LAG(rp.crude_price, 1) OVER (ORDER BY rp.date)) =
                  SIGN(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date) - rp.zl_price_current)
            THEN 1 ELSE 0 END as crude_direction_correct,
        CASE WHEN SIGN(LAG(rp.vix_level, 1) OVER (ORDER BY rp.date) - rp.vix_level) =
                  SIGN(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date) - rp.zl_price_current)
            THEN 1 ELSE 0 END as vix_inverse_correct,
        0.5 as lead_signal_confidence,
        CASE WHEN (rp.palm_price - LAG(rp.palm_price, 3) OVER (ORDER BY rp.date)) > LAG(rp.palm_price, 3) OVER (ORDER BY rp.date) * 0.02
                  AND (rp.zl_price_current - base.zl_price_lag7) < -base.zl_price_lag7 * 0.02
            THEN 1 ELSE 0 END as momentum_divergence,
        AVG(CASE WHEN SIGN(rp.palm_price - LAG(rp.palm_price, 1) OVER (ORDER BY rp.date)) =
                      SIGN(LEAD(rp.zl_price_current, 2) OVER (ORDER BY rp.date) - LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date))
                THEN 1.0 ELSE 0.0 END) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as palm_accuracy_30d,
        AVG(CASE WHEN SIGN(rp.crude_price - LAG(rp.crude_price, 1) OVER (ORDER BY rp.date)) =
                      SIGN(LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date) - rp.zl_price_current)
                THEN 1.0 ELSE 0.0 END) OVER (
            ORDER BY rp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as crude_accuracy_30d,
        LEAD(rp.zl_price_current, 1) OVER (ORDER BY rp.date) as leadlag_zl_price
    FROM raw_prices rp
    LEFT JOIN base ON rp.date = base.date
),

-- CFTC
cftc AS (
    SELECT 
        date,
        commercial_long as cftc_commercial_long,
        commercial_short as cftc_commercial_short,
        commercial_net as cftc_commercial_net,
        managed_money_long as cftc_managed_long,
        managed_money_short as cftc_managed_short,
        managed_money_net as cftc_managed_net,
        open_interest as cftc_open_interest
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    WHERE date >= '2020-01-01'
),

-- Econ
econ AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN indicator = 'gdp_growth' THEN value ELSE NULL END) as econ_gdp_growth,
        MAX(CASE WHEN indicator = 'inflation_rate' OR indicator = 'cpi_inflation' THEN value ELSE NULL END) as econ_inflation_rate,
        MAX(CASE WHEN indicator = 'unemployment_rate' THEN value ELSE NULL END) as econ_unemployment_rate
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE DATE(time) >= '2020-01-01'
    GROUP BY DATE(time)
),

-- News
news AS (
    SELECT 
        DATE(published) as date,
        COUNT(*) as news_article_count,
        AVG(intelligence_score) as news_avg_score
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    WHERE DATE(published) >= '2020-01-01'
    GROUP BY DATE(published)
),

-- Technical
technical AS (
    SELECT 
        date,
        (zl_price_current - LAG(zl_price_current, 14) OVER (ORDER BY date)) /
            NULLIF(LAG(zl_price_current, 14) OVER (ORDER BY date), 0) * 50 + 50 as rsi_proxy,
        volatility_30d / NULLIF(ma_30d, 0) as bb_width,
        zl_price_current / NULLIF(ma_30d, 0) as price_ma_ratio,
        (zl_price_current - LAG(zl_price_current, 30) OVER (ORDER BY date)) /
            NULLIF(LAG(zl_price_current, 30) OVER (ORDER BY date), 0) * 100 as momentum_30d,
        AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) -
        AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) as macd_proxy
    FROM base
),

-- Temporal
temporal AS (
    SELECT 
        rp.date,
        EXTRACT(DAYOFWEEK FROM rp.date) as day_of_week_num,
        EXTRACT(DAY FROM rp.date) as day_of_month,
        EXTRACT(MONTH FROM rp.date) as month_num,
        SIN(2 * 3.14159 * EXTRACT(DAYOFYEAR FROM rp.date) / 365) as seasonal_sin,
        COS(2 * 3.14159 * EXTRACT(DAYOFYEAR FROM rp.date) / 365) as seasonal_cos,
        CASE 
            WHEN rp.vix_level < 15 THEN 'LOW'
            WHEN rp.vix_level BETWEEN 15 AND 25 THEN 'NORMAL'
            ELSE 'HIGH'
        END as volatility_regime,
        EXP(-0.001 * DATE_DIFF(CURRENT_DATE(), rp.date, DAY)) as time_weight
    FROM raw_prices rp
),

-- Currencies
currencies AS (
    SELECT 
        date,
        MAX(CASE WHEN to_currency = 'CNY' THEN rate ELSE NULL END) as usd_cny_rate,
        MAX(CASE WHEN to_currency = 'BRL' THEN rate ELSE NULL END) as usd_brl_rate,
        MAX(CASE WHEN from_currency = 'DXY' THEN rate ELSE NULL END) as dollar_index,
        MAX(CASE WHEN to_currency = 'ARS' THEN rate ELSE NULL END) as usd_ars_rate,
        MAX(CASE WHEN to_currency = 'EUR' THEN rate ELSE NULL END) as usd_eur_rate
    FROM `cbi-v14.forecasting_data_warehouse.currency_data`
    WHERE date >= '2020-01-01'
    GROUP BY date
),

-- Econ from warehouse
econ_warehouse AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value ELSE NULL END) as fed_funds_rate,
        MAX(CASE WHEN indicator = 'ten_year_treasury' OR indicator = 'treasury_10y_yield' THEN value ELSE NULL END) as ten_year_treasury,
        MAX(CASE WHEN indicator = 'cpi_inflation' THEN value ELSE NULL END) as cpi_inflation,
        MAX(CASE WHEN indicator = 'vix_index' THEN value ELSE NULL END) as vix_index,
        MAX(CASE WHEN indicator = 'crude_oil_wti' THEN value ELSE NULL END) as crude_oil_wti,
        MAX(CASE WHEN indicator = 'treasury_10y_yield' THEN value ELSE NULL END) as treasury_10y_yield,
        MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value ELSE NULL END) - 
        MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value ELSE NULL END) as yield_curve
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE DATE(time) >= '2020-01-01'
    GROUP BY DATE(time)
)

-- FINAL SELECT - All features from template
SELECT 
    base.date,
    base.target_1w,
    base.target_1m,
    base.target_3m,
    base.target_6m,
    base.zl_price_current,
    base.zl_price_lag1,
    base.zl_price_lag7,
    base.zl_price_lag30,
    base.return_1d,
    base.return_7d,
    base.ma_7d,
    base.ma_30d,
    base.volatility_30d,
    base.zl_volume,
    big8.feature_vix_stress,
    big8.feature_harvest_pace,
    big8.feature_china_relations,
    big8.feature_tariff_threat,
    big8.feature_geopolitical_volatility,
    big8.feature_biofuel_cascade,
    big8.feature_hidden_correlation,
    big8.feature_biofuel_ethanol,
    big8.big8_composite_score,
    corr.corr_zl_crude_7d,
    corr.corr_zl_palm_7d,
    corr.corr_zl_vix_7d,
    corr.corr_zl_dxy_7d,
    corr.corr_zl_corn_7d,
    corr.corr_zl_wheat_7d,
    corr.corr_zl_crude_30d,
    corr.corr_zl_palm_30d,
    corr.corr_zl_vix_30d,
    corr.corr_zl_dxy_30d,
    corr.corr_zl_corn_30d,
    corr.corr_zl_wheat_30d,
    corr.corr_zl_crude_90d,
    corr.corr_zl_palm_90d,
    corr.corr_zl_vix_90d,
    corr.corr_zl_dxy_90d,
    corr.corr_zl_corn_90d,
    corr.corr_zl_crude_180d,
    corr.corr_zl_palm_180d,
    corr.corr_zl_vix_180d,
    corr.corr_zl_dxy_180d,
    corr.corr_zl_crude_365d,
    corr.corr_zl_palm_365d,
    corr.corr_zl_vix_365d,
    corr.corr_zl_dxy_365d,
    corr.corr_zl_corn_365d,
    corr.corr_palm_crude_30d,
    corr.corr_corn_wheat_30d,
    corr.crude_price,
    corr.palm_price,
    corr.corn_price,
    corr.wheat_price,
    corr.vix_level,
    corr.dxy_level,
    season.seasonal_index,
    season.monthly_zscore,
    season.yoy_change,
    crush.oil_price_per_cwt,
    crush.bean_price_per_bushel,
    crush.meal_price_per_ton,
    crush.crush_margin,
    crush.crush_margin_7d_ma,
    crush.crush_margin_30d_ma,
    china.china_mentions,
    china.china_posts,
    china.import_posts,
    china.soy_posts,
    china.china_sentiment,
    china.china_sentiment_volatility,
    china.china_policy_impact,
    china.import_demand_index,
    china.china_posts_7d_ma,
    china.china_sentiment_30d_ma,
    brazil.brazil_month,
    brazil.export_seasonality_factor,
    brazil.brazil_temperature_c,
    brazil.brazil_precipitation_mm,
    brazil.growing_degree_days,
    brazil.export_capacity_index,
    brazil.harvest_pressure,
    brazil.brazil_precip_30d_ma,
    brazil.brazil_temp_7d_ma,
    trump.trump_mentions,
    trump.trumpxi_china_mentions,
    trump.trump_xi_co_mentions,
    trump.xi_mentions,
    trump.tariff_mentions,
    trump.co_mention_sentiment,
    trump.trumpxi_sentiment_volatility,
    trump.trumpxi_policy_impact,
    trump.max_policy_impact,
    trump.tension_index,
    trump.volatility_multiplier,
    trump.co_mentions_7d_ma,
    trump.trumpxi_volatility_30d_ma,
    tw.china_tariff_rate,
    tw.brazil_market_share,
    tw.us_export_impact,
    tw.tradewar_event_vol_mult,
    tw.trade_war_intensity,
    tw.trade_war_impact_score,
    ev.is_wasde_day,
    ev.is_fomc_day,
    ev.is_china_holiday,
    ev.is_crop_report_day,
    ev.is_stocks_day,
    ev.is_planting_day,
    ev.is_major_usda_day,
    ev.event_impact_level,
    ev.days_to_next_event,
    ev.days_since_last_event,
    ev.pre_event_window,
    ev.post_event_window,
    ev.event_vol_mult,
    ev.is_options_expiry,
    ev.is_quarter_end,
    ev.is_month_end,
    ll.palm_lag1,
    ll.palm_lag2,
    ll.palm_lag3,
    ll.palm_momentum_3d,
    ll.crude_lag1,
    ll.crude_lag2,
    ll.crude_momentum_2d,
    ll.vix_lag1,
    ll.vix_lag2,
    ll.vix_spike_lag1,
    ll.dxy_lag1,
    ll.dxy_lag2,
    ll.dxy_momentum_3d,
    ll.corn_lag1,
    ll.wheat_lag1,
    ll.corn_soy_ratio_lag1,
    ll.palm_lead2_correlation,
    ll.crude_lead1_correlation,
    ll.vix_lead1_correlation,
    ll.dxy_lead1_correlation,
    ll.palm_direction_correct,
    ll.crude_direction_correct,
    ll.vix_inverse_correct,
    ll.lead_signal_confidence,
    ll.momentum_divergence,
    ll.palm_accuracy_30d,
    ll.crude_accuracy_30d,
    ll.leadlag_zl_price,
    weather.weather_brazil_temp,
    weather.weather_brazil_precip,
    weather.weather_argentina_temp,
    weather.weather_us_temp,
    sentiment.avg_sentiment,
    sentiment.sentiment_volatility,
    sentiment.sentiment_volume,
    temp.day_of_week_num,
    temp.day_of_month,
    temp.month_num,
    temp.seasonal_sin,
    temp.seasonal_cos,
    temp.volatility_regime,
    temp.time_weight,
    cftc.cftc_commercial_long,
    cftc.cftc_commercial_short,
    cftc.cftc_commercial_net,
    cftc.cftc_managed_long,
    cftc.cftc_managed_short,
    cftc.cftc_managed_net,
    cftc.cftc_open_interest,
    econ.econ_gdp_growth,
    econ.econ_inflation_rate,
    econ.econ_unemployment_rate,
    news.news_article_count,
    news.news_avg_score,
    tech.rsi_proxy,
    tech.bb_width,
    tech.price_ma_ratio,
    tech.momentum_30d,
    tech.macd_proxy,
    curr.usd_cny_rate,
    curr.usd_brl_rate,
    curr.dollar_index,
    curr.usd_ars_rate,
    curr.usd_eur_rate,
    econ_w.fed_funds_rate,
    econ_w.ten_year_treasury,
    econ_w.cpi_inflation,
    econ_w.yield_curve,
    econ_w.vix_index,
    econ_w.crude_oil_wti,
    econ_w.treasury_10y_yield

FROM base
LEFT JOIN big8 ON base.date = big8.date
LEFT JOIN correlations corr ON base.date = corr.date
LEFT JOIN seasonality season ON base.date = season.date
LEFT JOIN crush_with_mas crush ON base.date = crush.date
LEFT JOIN china_with_mas china ON base.date = china.date
LEFT JOIN brazil_with_mas brazil ON base.date = brazil.date
LEFT JOIN trump_with_mas trump ON base.date = trump.date
LEFT JOIN trade_war tw ON base.date = tw.date
LEFT JOIN events ev ON base.date = ev.date
LEFT JOIN lead_lag ll ON base.date = ll.date
LEFT JOIN `cbi-v14.models.weather_features_precomputed` weather ON base.date = weather.date
LEFT JOIN `cbi-v14.models.sentiment_features_precomputed` sentiment ON base.date = sentiment.date
LEFT JOIN temporal temp ON base.date = temp.date
LEFT JOIN cftc ON base.date = cftc.date
LEFT JOIN econ ON base.date = econ.date
LEFT JOIN news ON base.date = news.date
LEFT JOIN technical tech ON base.date = tech.date
LEFT JOIN currencies curr ON base.date = curr.date
LEFT JOIN econ_warehouse econ_w ON base.date = econ_w.date

WHERE base.date >= '2020-10-21'
ORDER BY base.date

