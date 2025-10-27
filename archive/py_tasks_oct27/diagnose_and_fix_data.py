#!/usr/bin/env python3
"""
DIAGNOSE AND FIX DATA LINKAGE ISSUES
Find why CFTC, Treasury, and Economic data aren't linking properly
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

print("="*80)
print("DIAGNOSING DATA LINKAGE ISSUES")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# 1. CHECK CFTC DATA
print("\n1. DIAGNOSING CFTC DATA")
print("-"*40)

cftc_check = """
SELECT 
    commodity,
    COUNT(*) as rows,
    MIN(report_date) as min_date,
    MAX(report_date) as max_date,
    SUM(CASE WHEN managed_money_net != 0 AND managed_money_net IS NOT NULL THEN 1 ELSE 0 END) as managed_filled,
    SUM(CASE WHEN commercial_net != 0 AND commercial_net IS NOT NULL THEN 1 ELSE 0 END) as commercial_filled
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
GROUP BY commodity
ORDER BY rows DESC
"""

print("CFTC commodities available:")
cftc_df = client.query(cftc_check).to_dataframe()
print(cftc_df.to_string())

# 2. CHECK TREASURY DATA
print("\n2. DIAGNOSING TREASURY DATA")
print("-"*40)

treasury_check = """
SELECT 
    symbol,
    COUNT(*) as rows,
    MIN(DATE(date)) as min_date,
    MAX(DATE(date)) as max_date,
    AVG(close) as avg_yield
FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
GROUP BY symbol
ORDER BY rows DESC
"""

print("Treasury symbols available:")
treasury_df = client.query(treasury_check).to_dataframe()
print(treasury_df.head(10).to_string())

# 3. CHECK ECONOMIC DATA
print("\n3. DIAGNOSING ECONOMIC DATA")
print("-"*40)

econ_check = """
SELECT 
    indicator,
    COUNT(*) as rows,
    MIN(DATE(time)) as min_date,
    MAX(DATE(time)) as max_date,
    AVG(value) as avg_value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
GROUP BY indicator
ORDER BY rows DESC
LIMIT 20
"""

print("Economic indicators available:")
econ_df = client.query(econ_check).to_dataframe()
print(econ_df.to_string())

# 4. FIX THE MASTER DATASET WITH CORRECT FILTERS
print("\n4. CREATING FIXED MASTER DATASET WITH PROPER FILTERS")
print("-"*40)

# First, let's find the right commodity name for soybean oil in CFTC
cftc_soy_check = """
SELECT DISTINCT commodity 
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
WHERE LOWER(commodity) LIKE '%soy%' OR LOWER(commodity) LIKE '%oil%'
"""

print("Checking for soybean oil in CFTC data:")
soy_commodities = client.query(cftc_soy_check).to_dataframe()
print(soy_commodities.to_string())

# Now create the properly filtered dataset
fixed_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_master_v2` AS
WITH 

-- Base prices
base_prices AS (
    SELECT 
        DATE(time) as date,
        close as zl_price_current,
        LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
        LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
        LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
        (close / NULLIF(LAG(close, 1) OVER (ORDER BY time), 0) - 1) as return_1d,
        (close / NULLIF(LAG(close, 7) OVER (ORDER BY time), 0) - 1) as return_7d,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
        volume as zl_volume,
        LEAD(close, 5) OVER (ORDER BY time) as target_1w,
        LEAD(close, 21) OVER (ORDER BY time) as target_1m,
        LEAD(close, 63) OVER (ORDER BY time) as target_3m,
        LEAD(close, 126) OVER (ORDER BY time) as target_6m
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE time >= '2020-01-01'
),

-- CFTC with ALL commodities (we'll filter for soybean oil if available)
cftc_data AS (
    SELECT 
        report_date as date,
        commercial_long as cftc_commercial_long,
        commercial_short as cftc_commercial_short,
        commercial_net as cftc_commercial_net,
        managed_money_long as cftc_managed_long,
        managed_money_short as cftc_managed_short,
        managed_money_net as cftc_managed_net,
        open_interest as cftc_open_interest
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    -- Try multiple possible names for soybean oil
    WHERE LOWER(commodity) IN ('soybean oil', 'soybean_oil', 'soy oil', 'zl', 'soyoil')
       OR commodity IS NULL  -- Include nulls in case commodity not specified
),

-- Treasury with proper symbol
treasury_data AS (
    SELECT 
        DATE(date) as date,
        close as treasury_10y_yield,
        close - LAG(close, 1) OVER (ORDER BY date) as treasury_yield_change_1d
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
    WHERE symbol = 'TNX' OR symbol = 'US10Y' OR symbol = '^TNX' OR symbol = 'DGS10'
),

-- Economic with actual indicator names from the data
economic_data AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN indicator IN ('US GDP Growth Rate QoQ', 'GDP', 'gdp_growth') THEN value END) as econ_gdp_growth,
        MAX(CASE WHEN indicator IN ('US Inflation Rate', 'CPI', 'inflation', 'cpi_yoy') THEN value END) as econ_inflation_rate,
        MAX(CASE WHEN indicator IN ('US Unemployment Rate', 'UNEMPLOYMENT', 'unemployment') THEN value END) as econ_unemployment_rate,
        MAX(CASE WHEN indicator IN ('US Fed Funds Rate', 'FED_FUNDS', 'fed_funds', 'interest_rate') THEN value END) as econ_fed_funds_rate,
        MAX(CASE WHEN indicator IN ('US ISM Manufacturing PMI', 'PMI', 'pmi', 'manufacturing_pmi') THEN value END) as econ_pmi_index
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY date
),

-- Other commodity prices
commodity_prices AS (
    SELECT 
        DATE(time) as date,
        close as crude_price
    FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
),

palm_prices AS (
    SELECT 
        DATE(time) as date,
        close as palm_price
    FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
),

corn_prices AS (
    SELECT 
        DATE(time) as date,
        close as corn_price
    FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
),

-- VIX
vix_data AS (
    SELECT 
        DATE(date) as date,
        close as vix_level
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Weather
weather_data AS (
    SELECT 
        date,
        AVG(CASE WHEN UPPER(region) IN ('US_MIDWEST', 'US', 'MIDWEST', 'IOWA', 'ILLINOIS') THEN temp_max END) as weather_us_temp,
        SUM(CASE WHEN UPPER(region) IN ('US_MIDWEST', 'US', 'MIDWEST', 'IOWA', 'ILLINOIS') THEN precip_mm END) as weather_us_precip,
        AVG(CASE WHEN UPPER(region) IN ('BRAZIL', 'BR', 'MATO_GROSSO') THEN temp_max END) as weather_brazil_temp,
        SUM(CASE WHEN UPPER(region) IN ('BRAZIL', 'BR', 'MATO_GROSSO') THEN precip_mm END) as weather_brazil_precip
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    GROUP BY date
)

-- MAIN QUERY
SELECT 
    bp.date,
    bp.zl_price_current,
    bp.zl_price_lag1,
    bp.zl_price_lag7,
    bp.zl_price_lag30,
    bp.return_1d,
    bp.return_7d,
    bp.ma_7d,
    bp.ma_30d,
    bp.zl_volume,
    bp.target_1w,
    bp.target_1m,
    bp.target_3m,
    bp.target_6m,
    
    -- CFTC
    COALESCE(cftc.cftc_commercial_long, 0) as cftc_commercial_long,
    COALESCE(cftc.cftc_commercial_short, 0) as cftc_commercial_short,
    COALESCE(cftc.cftc_commercial_net, 0) as cftc_commercial_net,
    COALESCE(cftc.cftc_managed_long, 0) as cftc_managed_long,
    COALESCE(cftc.cftc_managed_short, 0) as cftc_managed_short,
    COALESCE(cftc.cftc_managed_net, 0) as cftc_managed_net,
    COALESCE(cftc.cftc_open_interest, 0) as cftc_open_interest,
    
    -- Treasury
    COALESCE(tr.treasury_10y_yield, 0) as treasury_10y_yield,
    COALESCE(tr.treasury_yield_change_1d, 0) as treasury_yield_change_1d,
    
    -- Economic
    COALESCE(ec.econ_gdp_growth, 0) as econ_gdp_growth,
    COALESCE(ec.econ_inflation_rate, 0) as econ_inflation_rate,
    COALESCE(ec.econ_unemployment_rate, 0) as econ_unemployment_rate,
    COALESCE(ec.econ_fed_funds_rate, 0) as econ_fed_funds_rate,
    COALESCE(ec.econ_pmi_index, 0) as econ_pmi_index,
    
    -- Commodities
    COALESCE(cr.crude_price, 0) as crude_price,
    COALESCE(pm.palm_price, 0) as palm_price,
    COALESCE(cn.corn_price, 0) as corn_price,
    
    -- Market indicators
    COALESCE(vx.vix_level, 0) as vix_level,
    
    -- Weather
    COALESCE(w.weather_us_temp, 0) as weather_us_temp,
    COALESCE(w.weather_us_precip, 0) as weather_us_precip,
    COALESCE(w.weather_brazil_temp, 0) as weather_brazil_temp,
    COALESCE(w.weather_brazil_precip, 0) as weather_brazil_precip,
    
    CURRENT_TIMESTAMP() as created_at
    
FROM base_prices bp
LEFT JOIN cftc_data cftc ON bp.date = cftc.date
LEFT JOIN treasury_data tr ON bp.date = tr.date
LEFT JOIN economic_data ec ON bp.date = ec.date
LEFT JOIN commodity_prices cr ON bp.date = cr.date
LEFT JOIN palm_prices pm ON bp.date = pm.date
LEFT JOIN corn_prices cn ON bp.date = cn.date
LEFT JOIN vix_data vx ON bp.date = vx.date
LEFT JOIN weather_data w ON bp.date = w.date

WHERE bp.date >= '2020-01-01'
ORDER BY bp.date
"""

print("Creating fixed master dataset with proper filters...")
try:
    job = client.query(fixed_query)
    result = job.result()
    
    # Check results
    check_query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as min_date,
        MAX(date) as max_date,
        SUM(CASE WHEN cftc_managed_net != 0 THEN 1 ELSE 0 END) as cftc_managed_filled,
        SUM(CASE WHEN cftc_commercial_net != 0 THEN 1 ELSE 0 END) as cftc_commercial_filled,
        SUM(CASE WHEN treasury_10y_yield != 0 THEN 1 ELSE 0 END) as treasury_filled,
        SUM(CASE WHEN econ_inflation_rate != 0 THEN 1 ELSE 0 END) as inflation_filled,
        SUM(CASE WHEN weather_brazil_temp != 0 THEN 1 ELSE 0 END) as weather_filled
    FROM `cbi-v14.models.training_dataset_master_v2`
    """
    
    stats = client.query(check_query).to_dataframe()
    
    print("\n✓ FIXED DATASET CREATED!")
    print(f"\nFinal Statistics:")
    print(f"  Total rows: {stats['total_rows'].iloc[0]:,}")
    print(f"  Date range: {stats['min_date'].iloc[0]} to {stats['max_date'].iloc[0]}")
    print(f"\nData Coverage:")
    print(f"  CFTC commercial: {stats['cftc_commercial_filled'].iloc[0]:,} days")
    print(f"  CFTC managed: {stats['cftc_managed_filled'].iloc[0]:,} days")
    print(f"  Treasury yields: {stats['treasury_filled'].iloc[0]:,} days")
    print(f"  Inflation data: {stats['inflation_filled'].iloc[0]:,} days")
    print(f"  Weather data: {stats['weather_filled'].iloc[0]:,} days")
    
except Exception as e:
    print(f"Error: {str(e)[:500]}")

print("\n" + "="*80)
print("DIAGNOSIS AND FIX COMPLETE")
print("="*80)
