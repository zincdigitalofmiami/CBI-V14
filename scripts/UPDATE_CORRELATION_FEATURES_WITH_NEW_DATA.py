#!/usr/bin/env python3
"""
UPDATE CORRELATION FEATURES WITH THE NEW DATA YOU LOADED
NO MORE NaNs - We have the data now!
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("UPDATING CORRELATION FEATURES WITH YOUR NEW DATA")
print("=" * 80)

# Update the correlation features view to handle the data properly
update_query = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_correlation_features` AS
WITH aligned_prices AS (
    -- Align all prices by date
    SELECT 
        COALESCE(s.date, c.date, p.date) as date,
        s.close as zl_close,
        c.close_price as crude_close,
        p.close as palm_close
    FROM (
        SELECT DATE(time) as date, close, symbol
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE symbol = 'ZL'
    ) s
    FULL OUTER JOIN (
        SELECT date, close_price
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
    ) c ON s.date = c.date
    FULL OUTER JOIN (
        SELECT DATE(time) as date, close
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
    ) p ON s.date = p.date
),
vix_data AS (
    SELECT date, close as vix_close
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
)
SELECT 
    date,
    -- 7-day correlations (use IFNULL to handle edge cases)
    IFNULL(CORR(zl_close, crude_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_crude_7d,
    
    IFNULL(CORR(zl_close, palm_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_palm_7d,
    
    IFNULL(CORR(zl_close, v.vix_close) OVER (
        ORDER BY ap.date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_vix_7d,
    
    -- 30-day correlations
    IFNULL(CORR(zl_close, crude_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_crude_30d,
    
    IFNULL(CORR(zl_close, palm_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_palm_30d,
    
    IFNULL(CORR(zl_close, v.vix_close) OVER (
        ORDER BY ap.date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_vix_30d,
    
    -- 90-day correlations
    IFNULL(CORR(zl_close, crude_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_crude_90d,
    
    IFNULL(CORR(zl_close, palm_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_palm_90d,
    
    -- 180-day correlation
    IFNULL(CORR(zl_close, crude_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 179 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_crude_180d,
    
    -- 365-day correlation
    IFNULL(CORR(zl_close, crude_close) OVER (
        ORDER BY date 
        ROWS BETWEEN 364 PRECEDING AND CURRENT ROW
    ), 0) as corr_zl_crude_365d,
    
    -- Correlation breakdown flag
    CASE 
        WHEN ABS(CORR(zl_close, crude_close) OVER (
            ORDER BY date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        )) < 0.2 THEN 1
        ELSE 0
    END as correlation_breakdown_flag

FROM aligned_prices ap
LEFT JOIN vix_data v ON ap.date = v.date
WHERE ap.date >= '2023-01-01'  -- Focus on recent data with all commodities
AND zl_close IS NOT NULL  -- Must have soybean oil data
"""

try:
    client.query(update_query).result()
    print("✅ Updated correlation features view successfully!")
except Exception as e:
    logger.error(f"Error updating correlation features: {e}")

# Verify the update worked
print("\n" + "=" * 80)
print("VERIFYING NO MORE NaNs:")
print("=" * 80)

verify_query = """
SELECT 
    COUNT(*) as total_rows,
    COUNTIF(IS_NAN(corr_zl_crude_7d)) as crude_7d_nans,
    COUNTIF(IS_NAN(corr_zl_palm_7d)) as palm_7d_nans,
    COUNTIF(IS_NAN(corr_zl_crude_30d)) as crude_30d_nans,
    COUNTIF(corr_zl_crude_7d IS NULL) as crude_7d_nulls,
    COUNTIF(corr_zl_palm_7d IS NULL) as palm_7d_nulls
FROM `cbi-v14.models.vw_correlation_features`
"""

for row in client.query(verify_query):
    print(f"Total rows: {row.total_rows}")
    print(f"Crude 7d NaNs: {row.crude_7d_nans} (should be 0)")
    print(f"Palm 7d NaNs: {row.palm_7d_nans} (should be 0)")
    print(f"Crude 30d NaNs: {row.crude_30d_nans} (should be 0)")
    print(f"Crude 7d NULLs: {row.crude_7d_nulls}")
    print(f"Palm 7d NULLs: {row.palm_7d_nulls}")

print("\n" + "=" * 80)
print("NEXT: Delete duplicate training view and train models")
print("=" * 80)
