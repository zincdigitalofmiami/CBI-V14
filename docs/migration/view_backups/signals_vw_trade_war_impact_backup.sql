-- Backup of signals.vw_trade_war_impact
-- Created: 2025-11-17 17:57:50

WITH trade_dynamics AS (
        SELECT 
            date,
            -- China tariff escalation
            CASE 
                WHEN date >= '2024-01-01' THEN 1.25  -- 125% tariff active
                WHEN date >= '2023-01-01' THEN 0.25  -- Previous 25% tariff
                ELSE 0
            END as china_tariff_rate,
            
            -- Brazil market share dominance
            CASE 
                WHEN date >= '2025-01-01' THEN 0.70  -- 70% of China imports
                WHEN date >= '2024-01-01' THEN 0.60  -- Growing share
                WHEN date >= '2023-01-01' THEN 0.50  -- Historical share
                ELSE 0.40
            END as brazil_market_share,
            
            -- U.S. export destruction
            CASE 
                WHEN date >= '2024-01-01' THEN -0.60  -- 60% reduction
                WHEN date >= '2023-01-01' THEN -0.30  -- Initial impact
                ELSE 0
            END as us_export_impact,
            
            -- Trump-Xi meeting volatility multiplier
            CASE 
                WHEN date BETWEEN '2025-10-25' AND '2025-11-05' THEN 2.5  -- Meeting window
                WHEN date BETWEEN '2025-10-20' AND '2025-10-25' THEN 1.5  -- Pre-meeting
                ELSE 1.0
            END as event_volatility_multiplier,
            
            -- Trade war intensity score (0-1)
            CASE 
                WHEN date >= '2024-01-01' THEN 0.9  -- Maximum intensity
                WHEN date >= '2023-01-01' THEN 0.5  -- Moderate
                ELSE 0.2
            END as trade_war_intensity
            
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            WHERE DATE(time) >= '2020-01-01'
        )
    )
    SELECT 
        date,
        china_tariff_rate,
        brazil_market_share,
        us_export_impact,
        event_volatility_multiplier,
        trade_war_intensity,
        -- Composite trade war impact score
        (china_tariff_rate * 0.3 + 
         brazil_market_share * 0.3 + 
         ABS(us_export_impact) * 0.2 + 
         trade_war_intensity * 0.2) as trade_war_impact_score
    FROM trade_dynamics
    ORDER BY date DESC