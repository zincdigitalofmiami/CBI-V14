-- Updated signals.vw_supply_glut_indicator
-- Updated: 2025-11-17 17:57:50

WITH supply_dynamics AS (
        SELECT 
            date,
            -- Global production surge
            CASE 
                WHEN date >= '2025-09-01' THEN 341  -- Current record production
                WHEN date >= '2024-09-01' THEN 320  -- Previous year
                WHEN date >= '2023-09-01' THEN 310  -- 2 years ago
                ELSE 300
            END as global_production_mmt,
            
            -- Brazil production record
            CASE 
                WHEN date >= '2025-09-01' THEN 169  -- RECORD!
                WHEN date >= '2024-09-01' THEN 155
                ELSE 150
            END as brazil_production_mmt,
            
            -- U.S. production growth
            CASE 
                WHEN date >= '2025-09-01' THEN 121  -- +7% YoY
                WHEN date >= '2024-09-01' THEN 113
                ELSE 110
            END as us_production_mmt,
            
            -- Argentina recovery
            CASE 
                WHEN date >= '2025-09-01' THEN 51  -- Highest since 2018/19
                WHEN date >= '2024-09-01' THEN 40
                ELSE 45
            END as argentina_production_mmt,
            
            -- Stocks-to-use ratio (higher = more bearish)
            CASE 
                WHEN date >= '2025-09-01' THEN 0.31  -- Highest in years
                WHEN date >= '2024-09-01' THEN 0.28
                ELSE 0.25
            END as stocks_to_use_ratio
            
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
            WHERE DATE(time) >= '2020-01-01'
        )
    )
    SELECT 
        date,
        global_production_mmt,
        brazil_production_mmt,
        us_production_mmt,
        argentina_production_mmt,
        stocks_to_use_ratio,
        -- Supply pressure score (higher = more bearish)
        (global_production_mmt / 300 - 1) * 0.4 +  -- Production vs baseline
        stocks_to_use_ratio * 2 * 0.3 +  -- Stocks pressure
        (brazil_production_mmt / 150 - 1) * 0.3 as supply_glut_score
    FROM supply_dynamics
    ORDER BY date DESC