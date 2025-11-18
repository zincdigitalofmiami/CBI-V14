-- Updated signals.vw_hidden_correlation_signal
-- Updated: 2025-11-17 18:42:00

WITH price_data AS (
    SELECT 
        s.date,
        s.close_price as soy_price,
        c.close_price as crude_price,
        
        -- Calculate returns
        (s.close_price - LAG(s.close_price) OVER (ORDER BY s.date)) / 
            NULLIF(LAG(s.close_price) OVER (ORDER BY s.date), 0) as soy_return,
        (c.close_price - LAG(c.close_price) OVER (ORDER BY c.date)) / 
            NULLIF(LAG(c.close_price) OVER (ORDER BY c.date), 0) as crude_return
        
    FROM (
        SELECT date, AVG(yahoo_close) as close_price
        FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
        WHERE symbol = 'ZL=F'
        GROUP BY date
    ) s
    LEFT JOIN (
        SELECT date, AVG(yahoo_close) as close_price
        FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
        WHERE symbol = 'CL'
        GROUP BY date
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
    
    -- Correlation signals
    corr_30d as correlation_30d,
    corr_60d as correlation_60d,
    corr_90d as correlation_90d,
    
    -- Interpretation
    CASE 
        WHEN ABS(COALESCE(corr_30d, 0) - COALESCE(corr_90d, 0)) > 0.3 THEN 'HIGH'
        WHEN ABS(COALESCE(corr_30d, 0) - COALESCE(corr_90d, 0)) > 0.2 THEN 'MEDIUM'
        ELSE 'LOW'
    END as correlation_regime
    
FROM correlations
ORDER BY date DESC
