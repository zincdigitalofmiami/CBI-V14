-- Updated signals.vw_hidden_correlation_signal
-- Updated: 2025-11-17 17:57:50

WITH price_data AS (
    SELECT 
        s.date,
        s.yahoo_close_price as soy_price,
        c.yahoo_close_price as crude_price,
        
        -- Calculate returns
        (s.yahoo_close_price - LAG(s.yahoo_close_price) OVER (ORDER BY s.date)) / 
            NULLIF(LAG(s.yahoo_close_price) OVER (ORDER BY s.date), 0) as soy_return,
        (c.yahoo_close_price - LAG(c.yahoo_close_price) OVER (ORDER BY c.date)) / 
            NULLIF(LAG(c.yahoo_close_price) OVER (ORDER BY c.date), 0) as crude_return
        
    FROM (
        SELECT DATE(time) as date, AVG(close) as close_price
        FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
        WHERE symbol = 'ZL'
        GROUP BY DATE(time)
    ) s
    LEFT JOIN (
        SELECT time as date, AVG(close) as close_price
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        GROUP BY time
    ) c
    ON s.date = c.date
),
correlations AS (
    SELECT 
        date,
        soy_price,
        crude_price,
        soy_return,
        crude_return,
        
        -- Rolling correlations
        CORR(soy_return, crude_return) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d,
        CORR(soy_return, crude_return) OVER (ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) as corr_60d,
        CORR(soy_return, crude_return) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_90d
        
    FROM price_data
    WHERE soy_return IS NOT NULL AND crude_return IS NOT NULL
)
SELECT 
    date,
    
    -- Hidden correlation score (deviation from normal correlation)
    ABS(COALESCE(corr_30d, 0) - COALESCE(corr_90d, 0)) as hidden_correlation_score,
    
    -- Correlation strength
    COALESCE(corr_30d, 0) as correlation_30d,
    COALESCE(corr_60d, 0) as correlation_60d,
    COALESCE(corr_90d, 0) as correlation_90d,
    
    -- Regime
    CASE 
        WHEN ABS(corr_30d) > 0.7 THEN 'HIGH_CORRELATION'
        WHEN ABS(corr_30d) > 0.4 THEN 'MODERATE_CORRELATION'
        WHEN ABS(corr_30d) < 0.2 THEN 'DECORRELATED'
        ELSE 'NORMAL'
    END as correlation_regime
    
FROM correlations
WHERE date >= '2020-01-01'
ORDER BY date DESC