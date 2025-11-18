-- Updated signals.vw_harvest_pace_signal
-- Updated: 2025-11-17 17:57:49

WITH harvest_seasons AS (
        SELECT 
            date,
            -- US harvest: September-November
            CASE 
                WHEN EXTRACT(MONTH FROM date) IN (9, 10, 11) THEN 0.8
                WHEN EXTRACT(MONTH FROM date) IN (8, 12) THEN 0.5
                ELSE 0.2
            END as us_harvest_intensity,
            
            -- Brazil harvest: February-April
            CASE 
                WHEN EXTRACT(MONTH FROM date) IN (2, 3, 4) THEN 0.8
                WHEN EXTRACT(MONTH FROM date) IN (1, 5) THEN 0.5
                ELSE 0.2
            END as brazil_harvest_intensity,
            
            -- Argentina harvest: March-May
            CASE 
                WHEN EXTRACT(MONTH FROM date) IN (3, 4, 5) THEN 0.8
                WHEN EXTRACT(MONTH FROM date) IN (2, 6) THEN 0.5
                ELSE 0.2
            END as argentina_harvest_intensity
        FROM (
            SELECT DISTINCT DATE(time) as date
            FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
            WHERE DATE(time) >= '2020-01-01'
        )
    ),
    weather_impact AS (
        SELECT 
            date,
            AVG(CASE 
                WHEN region LIKE '%Brazil%' AND precip_mm > 200 THEN -0.3  -- Too wet
                WHEN region LIKE '%Brazil%' AND precip_mm < 50 THEN -0.2   -- Too dry
                ELSE 0
            END) as brazil_weather_impact,
            AVG(CASE 
                WHEN region LIKE '%US%' AND precip_mm > 150 THEN -0.2
                WHEN region LIKE '%US%' AND precip_mm < 25 THEN -0.1
                ELSE 0
            END) as us_weather_impact
        FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        GROUP BY date
    )
    SELECT 
        h.date,
        h.date as signal_date,  -- Some views expect this
        
        -- Weighted harvest pace (0-1 scale)
        GREATEST(0, LEAST(1,
            h.us_harvest_intensity * 0.4 + 
            h.brazil_harvest_intensity * 0.35 + 
            h.argentina_harvest_intensity * 0.25 +
            COALESCE(w.brazil_weather_impact, 0) +
            COALESCE(w.us_weather_impact, 0)
        )) as harvest_pace,
        
        -- Individual components for transparency
        h.us_harvest_intensity as us_harvest,
        h.brazil_harvest_intensity as brazil_harvest,
        h.argentina_harvest_intensity as argentina_harvest,
        
        -- Harvest pressure (inverse of pace - yahoo_high pressure = yahoo_low prices)
        1 - GREATEST(0, LEAST(1,
            h.us_harvest_intensity * 0.4 + 
            h.brazil_harvest_intensity * 0.35 + 
            h.argentina_harvest_intensity * 0.25
        )) as harvest_pressure
        
    FROM harvest_seasons h
    LEFT JOIN weather_impact w ON h.date = w.date
    ORDER BY h.date