WITH price_data_raw AS (
    SELECT 
        DATE(time) as date,
        close as price,
        EXTRACT(YEAR FROM time) as year,
        EXTRACT(MONTH FROM time) as month,
        EXTRACT(QUARTER FROM time) as quarter,
        EXTRACT(WEEK FROM time) as week_of_year,
        EXTRACT(DAYOFWEEK FROM time) as day_of_week
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
),
-- AGGREGATE TO ONE ROW PER DATE FIRST
price_data AS (
    SELECT 
        date,
        AVG(price) as price,
        MAX(year) as year,
        MAX(month) as month,
        MAX(quarter) as quarter,
        MAX(week_of_year) as week_of_year,
        MAX(day_of_week) as day_of_week
    FROM price_data_raw
    GROUP BY date
),
seasonal_averages AS (
    SELECT 
        month,
        AVG(price) as avg_price_for_month
    FROM price_data
    GROUP BY month
),
overall_avg AS (
    SELECT AVG(price) as overall_avg_price
    FROM price_data
),
yoy_changes AS (
    SELECT 
        date,
        price,
        LAG(price, 365) OVER (ORDER BY date) as price_1y_ago,
        (price - LAG(price, 365) OVER (ORDER BY date)) / NULLIF(LAG(price, 365) OVER (ORDER BY date), 0) as yoy_change
    FROM price_data
),
agricultural_phases AS (
    SELECT 
        date,
        CASE
            WHEN month IN (4, 5) THEN 'US_PLANTING'
            WHEN month IN (6, 7, 8) THEN 'US_GROWING'
            WHEN month IN (9, 10, 11) THEN 'US_HARVEST_BRAZIL_PLANTING'
            WHEN month IN (2, 3) THEN 'BRAZIL_HARVEST'
            WHEN month IN (12, 1) THEN 'OFF_SEASON'
            ELSE 'MIXED'
        END as agricultural_phase
    FROM price_data
)
-- FINAL SELECT - ONE ROW PER DATE GUARANTEED
SELECT 
    p.date,
    sa.avg_price_for_month / NULLIF(oa.overall_avg_price, 0) as seasonal_index,
    (p.price - sa.avg_price_for_month) / NULLIF(
        (SELECT STDDEV(price) FROM price_data WHERE month = p.month), 0
    ) as monthly_zscore,
    yoy.yoy_change,
    ap.agricultural_phase
FROM price_data p
LEFT JOIN seasonal_averages sa ON p.month = sa.month
CROSS JOIN overall_avg oa
LEFT JOIN yoy_changes yoy ON p.date = yoy.date
LEFT JOIN agricultural_phases ap ON p.date = ap.date
ORDER BY p.date DESC
