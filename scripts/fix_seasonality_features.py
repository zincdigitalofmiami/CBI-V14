#!/usr/bin/env python3
"""
Fix Seasonality Features - Remove Correlated Subqueries
"""
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("FIXING SEASONALITY FEATURES")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}\n")

# Create fixed materialized table (no correlated subqueries)
query = """
CREATE OR REPLACE TABLE `cbi-v14.staging_ml.seasonality_features_v1`
PARTITION BY DATE_TRUNC(date, MONTH)
CLUSTER BY date
OPTIONS(
    description="Seasonality features - Fixed to remove correlated subqueries - Version 1",
    labels=[("feature_type", "seasonality"), ("version", "v1"), ("environment", "staging")]
)
AS
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
-- Aggregate to one row per date
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
-- Pre-calculate monthly averages
seasonal_averages AS (
    SELECT 
        month,
        AVG(price) as avg_price_for_month
    FROM price_data
    GROUP BY month
),
-- Pre-calculate monthly standard deviations (FIX for correlated subquery)
monthly_stddev AS (
    SELECT 
        month,
        STDDEV(price) as stddev_price_for_month
    FROM price_data
    GROUP BY month
),
-- Overall average
overall_avg AS (
    SELECT AVG(price) as overall_avg_price
    FROM price_data
),
-- Year-over-year changes
yoy_changes AS (
    SELECT 
        date,
        price,
        LAG(price, 365) OVER (ORDER BY date) as price_1y_ago,
        (price - LAG(price, 365) OVER (ORDER BY date)) / 
            NULLIF(LAG(price, 365) OVER (ORDER BY date), 0) as yoy_change
    FROM price_data
)
-- Final select with NO correlated subqueries
SELECT 
    p.date,
    sa.avg_price_for_month / NULLIF(oa.overall_avg_price, 0) as seasonal_index,
    (p.price - sa.avg_price_for_month) / NULLIF(mstd.stddev_price_for_month, 0) as monthly_zscore,
    yoy.yoy_change
FROM price_data p
LEFT JOIN seasonal_averages sa ON p.month = sa.month
LEFT JOIN monthly_stddev mstd ON p.month = mstd.month  -- FIX: Pre-calculated stddev
CROSS JOIN overall_avg oa
LEFT JOIN yoy_changes yoy ON p.date = yoy.date
"""

print("Creating fixed seasonality_features_v1...")
try:
    job = client.query(query)
    result = job.result()
    print("✅ Table created successfully!")
    
    # Validate
    val_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        COUNTIF(seasonal_index IS NULL) as null_seasonal,
        COUNTIF(monthly_zscore IS NULL) as null_zscore,
        COUNTIF(yoy_change IS NULL) as null_yoy,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.staging_ml.seasonality_features_v1`
    """
    val_result = list(client.query(val_query).result())[0]
    
    print(f"\n✅ Validation:")
    print(f"   Total rows: {val_result.total_rows}")
    print(f"   Unique dates: {val_result.unique_dates}")
    print(f"   NULL seasonal_index: {val_result.null_seasonal}")
    print(f"   NULL monthly_zscore: {val_result.null_zscore}")
    print(f"   NULL yoy_change: {val_result.null_yoy}")
    print(f"   Date range: {val_result.min_date} to {val_result.max_date}")
    
    # Promote to production
    print("\nPromoting to production...")
    promote_query = """
    CREATE OR REPLACE TABLE `cbi-v14.models.seasonality_features_production_v1`
    CLONE `cbi-v14.staging_ml.seasonality_features_v1`
    """
    client.query(promote_query).result()
    print("✅ Promoted to production: models.seasonality_features_production_v1")
    
    print("\n" + "="*80)
    print("✅ SEASONALITY FEATURES FIXED")
    print("="*80)
    print("\nNext step: Rebuild training table with seasonality features")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    raise













