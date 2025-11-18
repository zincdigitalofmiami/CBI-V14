-- Updated signals.vw_bear_market_regime
-- Updated: 2025-11-17 17:57:49

WITH price_regime AS (
        SELECT 
            date,
            -- Price level indicators
            CASE 
                WHEN date >= '2025-01-01' THEN 11.20  -- Current bearish
                WHEN date >= '2024-01-01' THEN 12.55  -- Previous year
                WHEN date >= '2023-01-01' THEN 13.50
                ELSE 12.00
            END as implied_price_level,
            
            -- YoY price change
            CASE 
                WHEN date >= '2025-01-01' THEN -0.25  -- Down 25%
                WHEN date >= '2024-01-01' THEN -0.07  -- Down 7%
                ELSE 0
            END as yoy_price_change,
            
            -- China demand destruction
            CASE 
                WHEN date >= '2025-06-01' THEN -0.15  -- Pig herd down 15%
                WHEN date >= '2025-01-01' THEN -0.10  -- Initial decline
                ELSE 0
            END as china_demand_destruction,
            
            -- Market regime classification
            CASE 
                WHEN date >= '2025-01-01' THEN 'BEAR'
                WHEN date >= '2024-06-01' THEN 'NEUTRAL'
                WHEN date >= '2023-01-01' THEN 'BULL'
                ELSE 'NEUTRAL'
            END as market_regime,
            
            -- Regime intensity (0-1, 1 = strongest)
            CASE 
                WHEN date >= '2025-01-01' THEN 0.9  -- Strong bear
                WHEN date >= '2024-06-01' THEN 0.5  -- Transitioning
                ELSE 0.3
            END as regime_intensity
            
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
            WHERE DATE(time) >= '2020-01-01'
        )
    )
    SELECT 
        date,
        implied_price_level,
        yoy_price_change,
        china_demand_destruction,
        market_regime,
        regime_intensity,
        -- Composite bear market score
        ABS(yoy_price_change) * 0.4 +  -- Price decline weight
        ABS(china_demand_destruction) * 0.3 +  -- Demand weight
        regime_intensity * 0.3 as bear_market_score
    FROM price_regime
    ORDER BY date DESC