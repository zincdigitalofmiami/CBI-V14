#!/usr/bin/env python3
"""
STEP 2: CREATE INTERMEDIATE TABLES WITH PRE-COMPUTED WINDOW FUNCTIONS
This eliminates correlated subqueries for BQML compatibility
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("STEP 2: PRE-COMPUTING WINDOW FUNCTIONS IN INTERMEDIATE TABLES")
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 80)

# =============================================================================
# INTERMEDIATE TABLE 1: Price Features with Window Functions
# =============================================================================
print("\n1. Creating price_features_precomputed...")

price_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.price_features_precomputed` AS
WITH daily_prices AS (
    SELECT
        DATE(time) as date,
        AVG(close) as zl_price_current,
        SUM(volume) as zl_volume
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE symbol = 'ZL'
    AND DATE(time) >= '2018-01-01'
    GROUP BY DATE(time)
)
SELECT 
    date,
    zl_price_current,
    zl_volume,
    
    -- TARGETS (using LEAD)
    LEAD(zl_price_current, 7) OVER (ORDER BY date) as target_1w,
    LEAD(zl_price_current, 30) OVER (ORDER BY date) as target_1m,
    LEAD(zl_price_current, 90) OVER (ORDER BY date) as target_3m,
    LEAD(zl_price_current, 180) OVER (ORDER BY date) as target_6m,
    
    -- LAG FEATURES
    LAG(zl_price_current, 1) OVER (ORDER BY date) as zl_price_lag1,
    LAG(zl_price_current, 7) OVER (ORDER BY date) as zl_price_lag7,
    LAG(zl_price_current, 30) OVER (ORDER BY date) as zl_price_lag30,
    
    -- RETURNS
    (zl_price_current - LAG(zl_price_current, 1) OVER (ORDER BY date)) /
        NULLIF(LAG(zl_price_current, 1) OVER (ORDER BY date), 0) as return_1d,
    (zl_price_current - LAG(zl_price_current, 7) OVER (ORDER BY date)) /
        NULLIF(LAG(zl_price_current, 7) OVER (ORDER BY date), 0) as return_7d,
    
    -- MOVING AVERAGES
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
    AVG(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
    
    -- VOLATILITY
    STDDEV(zl_price_current) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d

FROM daily_prices
ORDER BY date
"""

try:
    client.query(price_query).result()
    check = list(client.query("SELECT COUNT(*) as cnt FROM `cbi-v14.models.price_features_precomputed`").result())[0]
    print(f"  ✅ price_features_precomputed: {check.cnt:,} rows")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:150]}")

# =============================================================================
# INTERMEDIATE TABLE 2: Weather Features Aggregated
# =============================================================================
print("\n2. Creating weather_features_precomputed...")

weather_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.weather_features_precomputed` AS
SELECT 
    date,
    AVG(CASE WHEN region = 'Brazil' THEN temperature_c END) as weather_brazil_temp,
    AVG(CASE WHEN region = 'Brazil' THEN precipitation_mm END) as weather_brazil_precip,
    AVG(CASE WHEN region = 'Argentina' THEN temperature_c END) as weather_argentina_temp,
    AVG(CASE WHEN region = 'Argentina' THEN precipitation_mm END) as weather_argentina_precip,
    AVG(CASE WHEN region = 'US' THEN temperature_c END) as weather_us_temp,
    AVG(CASE WHEN region = 'US' THEN precipitation_mm END) as weather_us_precip,
    
    -- Pre-computed moving averages
    AVG(AVG(CASE WHEN region = 'Brazil' THEN precipitation_mm END)) 
        OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as brazil_precip_30d_ma,
    AVG(AVG(CASE WHEN region = 'Brazil' THEN temperature_c END)) 
        OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as brazil_temp_7d_ma
        
FROM `cbi-v14.forecasting_data_warehouse.weather_data`
WHERE date >= '2018-01-01'
GROUP BY date
ORDER BY date
"""

try:
    client.query(weather_query).result()
    check = list(client.query("SELECT COUNT(*) as cnt FROM `cbi-v14.models.weather_features_precomputed`").result())[0]
    print(f"  ✅ weather_features_precomputed: {check.cnt:,} rows")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:150]}")

# =============================================================================
# INTERMEDIATE TABLE 3: Sentiment Features Aggregated
# =============================================================================
print("\n3. Creating sentiment_features_precomputed...")

sentiment_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.sentiment_features_precomputed` AS
SELECT 
    DATE(date) as date,
    AVG(sentiment_score) as avg_sentiment,
    STDDEV(sentiment_score) as sentiment_volatility,
    COUNT(*) as sentiment_volume,
    
    -- Pre-computed moving average
    AVG(AVG(sentiment_score)) OVER (
        ORDER BY DATE(date) 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as avg_sentiment_30d_ma
    
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
WHERE date >= '2018-01-01'
GROUP BY DATE(date)
ORDER BY date
"""

try:
    client.query(sentiment_query).result()
    check = list(client.query("SELECT COUNT(*) as cnt FROM `cbi-v14.models.sentiment_features_precomputed`").result())[0]
    print(f"  ✅ sentiment_features_precomputed: {check.cnt:,} rows")
except Exception as e:
    print(f"  ❌ Error: {str(e)[:150]}")

print("\n" + "=" * 80)
print("INTERMEDIATE TABLES CREATED")
print("=" * 80)
print("\nNext: Create final training table by joining all sources")
print(f"Completed: {datetime.now().strftime('%H:%M:%S')}")






