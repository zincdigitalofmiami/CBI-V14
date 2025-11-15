-- =====================================================
-- BIG 8 SIGNAL VIEWS FOR CBI-V14
-- Implements exact formulas from Signal Scoring Manual
-- Updated with commodity-appropriate VIX thresholds
-- =====================================================

-- 1. VIX STRESS (Market Volatility) - UPDATED FOR COMMODITY CONTEXT
-- Formula: Uses actual VIX levels appropriate for soybean futures
-- Based on historical analysis: Avg=21.12, Q75=24.33, P95=33.57
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_vix_stress_big8` AS
SELECT
    date,
    close as vix_current,
    -- Commodity-appropriate thresholds (not VIX/20 stress score)
    CASE
        WHEN close > 35 THEN 'CRISIS_VOLATILITY'      -- > P95, extreme events
        WHEN close > 25 THEN 'HIGH_VOLATILITY'        -- > Q75, significant stress
        WHEN close > 18 THEN 'ELEVATED_VOLATILITY'    -- > Q25, above normal
        ELSE 'NORMAL_VOLATILITY'                      -- Normal commodity VIX levels
    END as volatility_regime,
    -- Crisis flag based on commodity context
    close > 35 as crisis_flag,
    -- Stress score normalized for commodities (0-1 scale)
    LEAST(close / 40.0, 1.0) as vix_stress_score,
    CURRENT_TIMESTAMP() as updated_at
FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY date DESC;

-- 2. HARVEST PACE (Supply Fundamentals)
-- Formula: brazil_production_vs_trend * 0.7 + argentina_production_vs_trend * 0.3 (floored at 0.5)
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_harvest_pace_big8` AS
WITH brazil_conditions AS (
    SELECT 
        DATE(date) as date,
        AVG(CASE
            WHEN precip_mm < 50 THEN 0.6   -- Drought
            WHEN precip_mm > 200 THEN 0.9  -- Good
            ELSE 0.75  -- Normal
        END) as brazil_score
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE region LIKE '%Brazil%'
      AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    GROUP BY DATE(date)
),
argentina_conditions AS (
    SELECT
        DATE(date) as date,
        AVG(CASE
            WHEN precip_mm < 40 THEN 0.65   -- Drought
            WHEN precip_mm > 150 THEN 0.85  -- Good
            ELSE 0.75  -- Normal
        END) as argentina_score
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE region LIKE '%Argentina%'
      AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    GROUP BY DATE(date)
)
SELECT 
    COALESCE(b.date, a.date) as date,
    COALESCE(b.brazil_score, 0.75) as brazil_production_vs_trend,
    COALESCE(a.argentina_score, 0.75) as argentina_production_vs_trend,
    GREATEST(
        COALESCE(b.brazil_score, 0.75) * 0.7 + 
        COALESCE(a.argentina_score, 0.75) * 0.3,
        0.5  -- Floor at 0.5
    ) as harvest_pace_score,
    CASE
        WHEN COALESCE(b.brazil_score, 0.75) * 0.7 + COALESCE(a.argentina_score, 0.75) * 0.3 < 0.6 
        THEN 'SEVERE_PRODUCTION_ISSUES'
        WHEN COALESCE(b.brazil_score, 0.75) * 0.7 + COALESCE(a.argentina_score, 0.75) * 0.3 < 0.8 
        THEN 'BELOW_AVERAGE_HARVEST'
        WHEN COALESCE(b.brazil_score, 0.75) * 0.7 + COALESCE(a.argentina_score, 0.75) * 0.3 < 1.0 
        THEN 'NORMAL_PRODUCTION'
        ELSE 'BUMPER_CROP'
    END as harvest_regime,
    COALESCE(b.brazil_score, 0.75) * 0.7 + COALESCE(a.argentina_score, 0.75) * 0.3 < 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM brazil_conditions b
FULL OUTER JOIN argentina_conditions a ON b.date = a.date
ORDER BY date DESC;

-- 3. CHINA RELATIONS (Trade Dynamics)
-- Formula: china_trade_tension_index * 0.6 + (1 - china_us_import_share) * 0.4 (capped at 1.0)
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_china_relations_big8` AS
WITH daily_sentiment AS (
    SELECT
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at)) as date,
        -- Trade tension index from sentiment
        AVG(CASE 
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%tariff%' THEN 0.9
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%retaliat%' THEN 0.85
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%trade war%' THEN 0.8
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%tension%' THEN 0.7
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%cooperat%' THEN 0.3
            WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%deal%' THEN 0.4
            ELSE 0.5
        END) as trade_tension_index,
        
        -- Estimate US import share from diversification mentions
        COUNT(CASE WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%brazil%' THEN 1 END) as brazil_mentions,
        COUNT(CASE WHEN LOWER(content) LIKE '%china%' AND LOWER(content) LIKE '%argentina%' THEN 1 END) as argentina_mentions,
        COUNT(*) as total_mentions
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) IS NOT NULL
      AND SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      AND LOWER(content) LIKE '%china%'
    GROUP BY DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at))
)
SELECT 
    date,
    trade_tension_index,
    -- Estimate US share: lower when more Brazil/Argentina mentions
    GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2) as china_us_import_share,
    LEAST(
        trade_tension_index * 0.6 + 
        (1 - GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2)) * 0.4,
        1.0
    ) as china_relations_score,
    CASE
        WHEN trade_tension_index * 0.6 + (1 - GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2)) * 0.4 > 0.8
        THEN 'TRADE_CRISIS'
        WHEN trade_tension_index * 0.6 + (1 - GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2)) * 0.4 > 0.6
        THEN 'ELEVATED_TENSIONS'
        WHEN trade_tension_index * 0.6 + (1 - GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2)) * 0.4 > 0.3
        THEN 'NORMAL_RELATIONS'
        ELSE 'STRONG_RELATIONS'
    END as china_regime,
    trade_tension_index * 0.6 + (1 - GREATEST(0.15, 1.0 - (brazil_mentions + argentina_mentions) / NULLIF(total_mentions, 0) * 2)) * 0.4 > 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM daily_sentiment
ORDER BY date DESC;

-- 4. TARIFF THREAT (Policy Risk)
-- Formula: (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 (capped at 1.0)
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_tariff_threat_big8` AS
WITH daily_tariffs AS (
    SELECT
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at)) as date,
        COUNT(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 END) as tariff_mentions_daily,
        AVG(CASE
            WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%china%' THEN 0.9
            WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%trade%' THEN 0.8
            WHEN LOWER(content) LIKE '%tariff%' AND LOWER(content) LIKE '%agriculture%' THEN 0.85
            WHEN LOWER(content) LIKE '%tariff%' THEN 0.7
            ELSE 0.3
        END) as china_trade_tension
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) IS NOT NULL
      AND SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at))
),
tariff_data AS (
    SELECT
        date,
        SUM(tariff_mentions_daily) OVER (
            ORDER BY date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as tariff_mentions_7d,
        china_trade_tension
    FROM daily_tariffs
)
SELECT 
    date,
    tariff_mentions_7d,
    china_trade_tension,
    LEAST(
        (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3,
        1.0
    ) as tariff_threat_score,
    CASE
        WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.8 THEN 'IMMINENT_TARIFF_ACTION'
        WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.6 THEN 'ELEVATED_TARIFF_RISK'
        WHEN (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.3 THEN 'BACKGROUND_RISK'
        ELSE 'LOW_TARIFF_PROBABILITY'
    END as tariff_regime,
    (tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension * 0.3 > 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM tariff_data
ORDER BY date DESC;

-- 5. GEOPOLITICAL VOLATILITY INDEX (GVI)
-- Formula: Updated for commodity VIX context - using actual levels not VIX/20
-- Crisis VIX (>35) gets 0.8 weight, High VIX (25-35) gets 0.6, etc.
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_geopolitical_volatility_big8` AS
WITH vix_component AS (
    SELECT
        date,
        CASE
            WHEN close > 35 THEN 0.8  -- Crisis levels
            WHEN close > 25 THEN 0.6  -- High volatility
            WHEN close > 18 THEN 0.4  -- Elevated
            ELSE 0.2  -- Normal
        END * 0.4 as vix_contribution
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
    WHERE date = (SELECT MAX(date) FROM `cbi-v14.forecasting_data_warehouse.vix_daily`)
),
social_components AS (
    SELECT 
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at)) as date,
        -- Trump tweet market correlation (simplified)
        ABS(CORR(
            CASE WHEN LOWER(content) LIKE '%market%' OR LOWER(content) LIKE '%trade%' THEN 1 ELSE 0 END,
            CASE WHEN LOWER(content) LIKE '%tariff%' OR LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END
        ) OVER (ORDER BY DATE(created_at) ROWS BETWEEN 30 PRECEDING AND CURRENT ROW)) * 0.3 as trump_contribution,
        
        -- Panama Canal delays (from mentions)
        LEAST(
            COUNT(CASE WHEN LOWER(content) LIKE '%panama%canal%' OR LOWER(content) LIKE '%suez%' THEN 1 END) / 15.0,
            1.0
        ) * 0.2 as panama_contribution,
        
        -- Emerging market stress
        AVG(CASE 
            WHEN LOWER(content) LIKE '%emerging%market%' AND LOWER(content) LIKE '%crisis%' THEN 0.9
            WHEN LOWER(content) LIKE '%currency%' AND LOWER(content) LIKE '%devaluat%' THEN 0.8
            WHEN LOWER(content) LIKE '%debt%' AND LOWER(content) LIKE '%default%' THEN 0.85
            ELSE 0.3
        END) * 0.1 as em_contribution
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) IS NOT NULL
      AND SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at))
)
SELECT 
    COALESCE(v.date, s.date) as date,
    COALESCE(v.vix_contribution, 0.4) as vix_component,
    COALESCE(s.trump_contribution, 0.09) as trump_component,
    COALESCE(s.panama_contribution, 0) as panama_component,
    COALESCE(s.em_contribution, 0.03) as em_component,
    LEAST(
        COALESCE(v.vix_contribution, 0.4) + 
        COALESCE(s.trump_contribution, 0.09) + 
        COALESCE(s.panama_contribution, 0) + 
        COALESCE(s.em_contribution, 0.03),
        1.0
    ) as gvi_score,
    CASE
        WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
             COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.8 
        THEN 'GEOPOLITICAL_CRISIS'
        WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
             COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.6 
        THEN 'ELEVATED_RISK'
        WHEN COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
             COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.3 
        THEN 'NORMAL_TENSION'
        ELSE 'STABLE_ENVIRONMENT'
    END as gvi_regime,
    COALESCE(v.vix_contribution, 0.4) + COALESCE(s.trump_contribution, 0.09) + 
    COALESCE(s.panama_contribution, 0) + COALESCE(s.em_contribution, 0.03) > 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM vix_component v
FULL OUTER JOIN (
    SELECT * FROM social_components 
    WHERE date = (SELECT MAX(date) FROM social_components)
) s ON v.date = s.date;

-- 6. BIOFUEL SUBSTITUTION CASCADE (BSC)
-- Formula: rfs * 0.3 + indonesia/3M * 0.3 + rd_margin/150 * 0.2 + eu_red * 0.2
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_biofuel_cascade_big8` AS
WITH biofuel_signals AS (
    SELECT 
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at)) as date,
        -- US RFS mandate signals
        LEAST(COUNT(CASE WHEN LOWER(content) LIKE '%rfs%' OR LOWER(content) LIKE '%renewable%fuel%' THEN 1 END) / 100.0, 1.0) * 0.3 as rfs_component,
        
        -- Indonesia B40 signals (2.4M MT impact)
        LEAST(COUNT(CASE WHEN LOWER(content) LIKE '%indonesia%' AND LOWER(content) LIKE '%b40%' THEN 1 END) * 2.4 / 10.0, 1.0) * 0.3 as indonesia_component,
        
        -- Renewable diesel margin signals ($120 estimate)
        LEAST(AVG(CASE 
            WHEN LOWER(content) LIKE '%renewable%diesel%' THEN 1.0
            WHEN LOWER(content) LIKE '%biodiesel%' THEN 0.8
            WHEN LOWER(content) LIKE '%biofuel%' THEN 0.6
            ELSE 0.3
        END) * 120 / 150, 1.0) * 0.2 as rd_component,
        
        -- EU RED II signals
        LEAST(COUNT(CASE WHEN LOWER(content) LIKE '%eu%' AND LOWER(content) LIKE '%palm%' THEN 1 END) / 50.0, 1.0) * 0.2 as eu_component
        
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) IS NOT NULL
      AND SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S +0000 %Y', created_at))
)
SELECT 
    date,
    rfs_component,
    indonesia_component,
    rd_component,
    eu_component,
    LEAST(
        rfs_component + indonesia_component + rd_component + eu_component,
        1.0
    ) as bsc_score,
    CASE
        WHEN rfs_component + indonesia_component + rd_component + eu_component > 0.8 THEN 'MAJOR_BIOFUEL_SURGE'
        WHEN rfs_component + indonesia_component + rd_component + eu_component > 0.6 THEN 'BULLISH_BIOFUEL_IMPACT'
        WHEN rfs_component + indonesia_component + rd_component + eu_component > 0.3 THEN 'NEUTRAL_BIOFUEL'
        ELSE 'BEARISH_BIOFUEL'
    END as bsc_regime,
    rfs_component + indonesia_component + rd_component + eu_component > 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM biofuel_signals
ORDER BY date DESC;

-- 7. HIDDEN CORRELATION INDEX (HCI)
-- Formula: zl_crude * 0.25 + zl_dxy * -0.25 + soy_palm * 0.25 + vix_trump * 0.25
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_hidden_correlation_big8` AS
WITH price_correlations AS (
    -- Calculate REAL 30-day rolling correlations
    SELECT 
        DATE(s.time) as date,
        -- ZL-Crude REAL correlation (soybean.close vs crude.close_price)
        CORR(s.close, c.close_price) OVER (
            ORDER BY DATE(s.time) 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as zl_crude_correlation,
        
        -- ZL-DXY REAL correlation (soybean.close vs usd.close_price)
        CORR(s.close, d.close_price) OVER (
            ORDER BY DATE(s.time) 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as zl_dxy_correlation,
        
        -- Soy-Palm REAL correlation (soybean.close vs palm.close_price)
        CORR(s.close, p.close_price) OVER (
            ORDER BY DATE(s.time) 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_palm_correlation
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` s
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.crude_oil_prices` c
      ON DATE(s.time) = c.date  -- soybean uses time (TIMESTAMP), crude uses date (DATE)
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.usd_index_prices` d
      ON DATE(s.time) = d.date AND (d.symbol = 'DX' OR d.symbol = 'DXY')  -- usd uses date (DATE)
    LEFT JOIN `cbi-v14.forecasting_data_warehouse.palm_oil_prices` p
      ON s.time = p.time  -- both use time (TIMESTAMP)
    WHERE DATE(s.time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
),
trump_correlation AS (
    SELECT 
        -- VIX-Trump tweet correlation
        CORR(
            CASE WHEN LOWER(content) LIKE '%volatil%' THEN 1 ELSE 0 END,
            CASE WHEN LOWER(content) LIKE '%trump%' OR LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END
        ) as vix_trump_correlation
    FROM `cbi-v14.staging.comprehensive_social_intelligence`
    WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
)
SELECT 
    p.date,
    p.zl_crude_correlation,
    p.zl_dxy_correlation,
    p.soy_palm_correlation,
    COALESCE(t.vix_trump_correlation, 0) as vix_trump_correlation,
    -- Calculate HCI score (range -1 to 1)
    p.zl_crude_correlation * 0.25 + 
    p.zl_dxy_correlation * -0.25 +  -- Inverted
    COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
    COALESCE(t.vix_trump_correlation, 0) * 0.25 as hci_score,
    CASE
        WHEN ABS(p.zl_crude_correlation * 0.25 + p.zl_dxy_correlation * -0.25 + 
                 COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                 COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.8 
        THEN 'EXTREME_CORRELATION_SHIFT'
        WHEN ABS(p.zl_crude_correlation * 0.25 + p.zl_dxy_correlation * -0.25 + 
                 COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                 COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.6 
        THEN 'STRONG_CORRELATIONS'
        WHEN ABS(p.zl_crude_correlation * 0.25 + p.zl_dxy_correlation * -0.25 + 
                 COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
                 COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.2 
        THEN 'MODERATE_CORRELATIONS'
        ELSE 'NEUTRAL_PATTERNS'
    END as hci_regime,
    ABS(p.zl_crude_correlation * 0.25 + p.zl_dxy_correlation * -0.25 + 
        COALESCE(p.soy_palm_correlation, 0.5) * 0.25 + 
        COALESCE(t.vix_trump_correlation, 0) * 0.25) > 0.8 as crisis_flag,
    CURRENT_TIMESTAMP() as updated_at
FROM price_correlations p
CROSS JOIN trump_correlation t
WHERE p.date = (SELECT MAX(date) FROM price_correlations);

-- MASTER BIG 8 COMPOSITE VIEW
CREATE OR REPLACE VIEW `cbi-v14.api.vw_big8_composite_signal` AS
WITH latest_signals AS (
    SELECT 
        CURRENT_DATE() as date,
        
        -- VIX Stress
        (SELECT vix_stress_score FROM `cbi-v14.signals.vw_vix_stress_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_vix_stress_big8`)) as vix_stress,

        -- Harvest Pace
        (SELECT harvest_pace_score FROM `cbi-v14.signals.vw_harvest_pace_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_harvest_pace_big8`)) as harvest_pace,

        -- China Relations
        (SELECT china_relations_score FROM `cbi-v14.signals.vw_china_relations_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_china_relations_big8`)) as china_relations,

        -- Tariff Threat
        (SELECT tariff_threat_score FROM `cbi-v14.signals.vw_tariff_threat_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_tariff_threat_big8`)) as tariff_threat,

        -- GVI
        (SELECT gvi_score FROM `cbi-v14.signals.vw_geopolitical_volatility_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_geopolitical_volatility_big8`)) as geopolitical_volatility,

        -- BSC
        (SELECT bsc_score FROM `cbi-v14.signals.vw_biofuel_cascade_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_biofuel_cascade_big8`)) as biofuel_cascade,

        -- HCI
        (SELECT hci_score FROM `cbi-v14.signals.vw_hidden_correlation_big8`
         WHERE date = (SELECT MAX(date) FROM `cbi-v14.signals.vw_hidden_correlation_big8`)) as hidden_correlation
),
crisis_calc AS (
    SELECT 
        *,
        -- Calculate crisis intensity (0-100)
        LEAST(
            CASE WHEN vix_stress > 1.5 THEN 17 ELSE 0 END +
            CASE WHEN harvest_pace < 0.8 THEN 17 ELSE 0 END +
            CASE WHEN china_relations > 0.8 THEN 17 ELSE 0 END +
            CASE WHEN tariff_threat > 0.8 THEN 17 ELSE 0 END +
            CASE WHEN geopolitical_volatility > 0.8 THEN 12 ELSE 0 END +
            CASE WHEN biofuel_cascade > 0.8 THEN 12 ELSE 0 END +
            CASE WHEN ABS(hidden_correlation) > 0.8 THEN 8 ELSE 0 END,
            100
        ) as crisis_intensity_score
    FROM latest_signals
),
regime_calc AS (
    SELECT 
        *,
        -- Determine market regime
        CASE
            -- Single factor crisis regimes
            WHEN vix_stress > 1.5 THEN 'VIX_CRISIS_REGIME'
            WHEN harvest_pace < 0.8 THEN 'SUPPLY_CRISIS_REGIME'
            WHEN china_relations > 0.8 THEN 'CHINA_CRISIS_REGIME'
            WHEN tariff_threat > 0.8 THEN 'TARIFF_CRISIS_REGIME'
            WHEN geopolitical_volatility > 0.8 THEN 'GEOPOLITICAL_CRISIS_REGIME'
            WHEN biofuel_cascade > 0.8 THEN 'BIOFUEL_IMPACT_REGIME'
            WHEN ABS(hidden_correlation) > 0.8 THEN 'CORRELATION_SHIFT_REGIME'
            
            -- Multi-factor stress regimes
            WHEN vix_stress > 1.25 AND china_relations > 0.6 THEN 'GEOPOLITICAL_STRESS_REGIME'
            WHEN harvest_pace < 0.9 AND china_relations > 0.6 THEN 'SUPPLY_GEOPOLITICAL_REGIME'
            WHEN vix_stress > 1.25 AND tariff_threat > 0.6 THEN 'TRUMP_VOLATILITY_REGIME'
            WHEN biofuel_cascade > 0.6 AND hidden_correlation > 0.6 THEN 'BIOFUEL_CORRELATION_REGIME'
            
            -- Normal regime
            WHEN vix_stress < 1.0 AND harvest_pace > 0.95 AND china_relations < 0.4 AND tariff_threat < 0.3 
            THEN 'FUNDAMENTALS_REGIME'
            
            -- Default
            ELSE 'MIXED_SIGNALS_REGIME'
        END as market_regime
    FROM crisis_calc
)
SELECT 
    date,
    
    -- Big 7 Signals
    ROUND(vix_stress, 3) as vix_stress_score,
    ROUND(harvest_pace, 3) as harvest_pace_score,
    ROUND(china_relations, 3) as china_relations_score,
    ROUND(tariff_threat, 3) as tariff_threat_score,
    ROUND(geopolitical_volatility, 3) as gvi_score,
    ROUND(biofuel_cascade, 3) as bsc_score,
    ROUND(hidden_correlation, 3) as hci_score,
    
    -- Composite with neural weights
    ROUND(
        (vix_stress * 2.5 + harvest_pace * 2.5 + china_relations * 2.5 + tariff_threat * 2.5 +
         geopolitical_volatility * 1.5 + biofuel_cascade * 1.5 + 
         ((hidden_correlation + 1) / 2) * 1.0) / 14.0,  -- Total weight = 14
        3
    ) as composite_signal_score,
    
    -- Crisis and regime
    crisis_intensity_score,
    market_regime,
    
    -- Confidence based on crisis intensity
    CASE
        WHEN crisis_intensity_score < 25 THEN 75
        WHEN crisis_intensity_score < 50 THEN 65
        WHEN crisis_intensity_score < 75 THEN 55
        ELSE 45
    END as forecast_confidence_pct,
    
    -- Primary driver
    CASE
        WHEN vix_stress > 1.5 THEN 'VIX_STRESS'
        WHEN harvest_pace < 0.8 THEN 'HARVEST_PACE'
        WHEN china_relations > 0.8 THEN 'CHINA_RELATIONS'
        WHEN tariff_threat > 0.8 THEN 'TARIFF_THREAT'
        WHEN geopolitical_volatility > 0.8 THEN 'GEOPOLITICAL_VOLATILITY'
        WHEN biofuel_cascade > 0.8 THEN 'BIOFUEL_CASCADE'
        WHEN ABS(hidden_correlation) > 0.8 THEN 'HIDDEN_CORRELATIONS'
        ELSE 'BALANCED_FUNDAMENTALS'
    END as primary_signal_driver,
    
    CURRENT_TIMESTAMP() as updated_at
FROM regime_calc;

-- ============================================================================
-- PRIORITY REGIME DETECTOR (Big 4 + Labor)
-- ============================================================================
CREATE OR REPLACE VIEW `cbi-v14.neural.vw_chris_priority_regime_detector` AS
WITH base_signals AS (
  SELECT
    signal_date,
    COALESCE(feature_vix_stress, 0.0) AS feature_vix_stress,
    COALESCE(feature_harvest_pace, 0.0) AS feature_harvest_pace,
    COALESCE(feature_china_relations, 0.0) AS feature_china_relations,
    COALESCE(feature_tariff_probability, 0.0) AS feature_tariff_probability,
    COALESCE(ice_labor_shortage_risk_score, 0.0) AS feature_labor_stress,
    COALESCE(feature_geopolitical_volatility, 0.0) AS feature_geopolitical_volatility,
    COALESCE(feature_biofuel_cascade, 0.0) AS feature_biofuel_cascade,
    COALESCE(feature_hidden_correlation, 0.0) AS feature_hidden_correlation,
    master_regime_classification,
    crisis_intensity_score
  FROM `cbi-v14.signals.vw_comprehensive_signal_universe`
)
SELECT
  signal_date,
  feature_vix_stress,
  feature_harvest_pace,
  feature_china_relations,
  feature_tariff_probability,
  feature_labor_stress,
  -- Override flags for attribution and Sharpe slices
  (feature_vix_stress > 1.5) AS vix_override_flag,
  (feature_harvest_pace < 0.8) AS harvest_override_flag,
  (feature_china_relations > 0.8) AS china_override_flag,
  (feature_tariff_probability > 0.8) AS tariff_override_flag,
  (feature_labor_stress > 0.7) AS labor_override_flag,
  -- Primary driver preference order (labor elevated ahead of seasonal drivers)
  CASE
    WHEN feature_labor_stress > 0.7 THEN 'LABOR'
    WHEN feature_vix_stress > 1.5 THEN 'VIX'
    WHEN feature_harvest_pace < 0.8 THEN 'HARVEST'
    WHEN feature_china_relations > 0.8 THEN 'CHINA'
    WHEN feature_tariff_probability > 0.8 THEN 'TARIFF'
    WHEN feature_geopolitical_volatility > 0.8 THEN 'GEOPOLITICAL'
    WHEN feature_biofuel_cascade > 0.8 THEN 'BIOFUEL'
    WHEN ABS(feature_hidden_correlation) > 0.8 THEN 'HIDDEN_CORRELATION'
    ELSE 'BALANCED'
  END AS primary_signal_driver,
  CASE
    WHEN feature_labor_stress > 0.7 THEN 'LABOR_STRESS_REGIME'
    ELSE master_regime_classification
  END AS master_regime_classification,
  crisis_intensity_score
FROM base_signals
WHERE signal_date IS NOT NULL;
