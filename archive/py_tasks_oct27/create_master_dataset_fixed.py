#!/usr/bin/env python3
"""
CREATE MASTER TRAINING DATASET - FIXED VERSION
Properly integrate all data sources without nested analytics functions
"""

from google.cloud import bigquery
from datetime import datetime

print("="*80)
print("CREATING MASTER TRAINING DATASET - FIXED")
print(f"Timestamp: {datetime.now().strftime('%Y-%m%d_%H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# Create the master dataset in steps to avoid nested analytics
print("\n1. CREATING INTERMEDIATE TABLES")
print("-"*40)

# Step 1: Create CFTC features with proper managed money data
print("Creating CFTC features...")
cftc_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.temp_cftc_features` AS
SELECT 
    report_date as date,
    
    -- Commercial positions (hedgers)
    commercial_long as cftc_commercial_long,
    commercial_short as cftc_commercial_short,
    commercial_net as cftc_commercial_net,
    
    -- Managed money positions (specs)
    managed_money_long as cftc_managed_long,
    managed_money_short as cftc_managed_short,
    managed_money_net as cftc_managed_net,
    
    -- Open interest
    open_interest as cftc_open_interest,
    
    -- Calculate positioning metrics
    SAFE_DIVIDE(managed_money_net, open_interest) * 100 as cftc_spec_net_pct,
    SAFE_DIVIDE(commercial_net, open_interest) * 100 as cftc_comm_net_pct
    
FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
WHERE commodity = 'SOYBEAN OIL' OR commodity IS NULL
"""

try:
    client.query(cftc_query).result()
    print("✓ CFTC features created")
except Exception as e:
    print(f"⚠ CFTC error: {str(e)[:100]}")

# Step 2: Create economic features
print("\nCreating economic features...")
econ_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.temp_economic_features` AS
SELECT 
    DATE(time) as date,
    indicator,
    value
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator IN ('GDP', 'CPI', 'UNEMPLOYMENT', 'FED_FUNDS', 'RETAIL_SALES', 'PMI')
"""

try:
    client.query(econ_query).result()
    print("✓ Economic features created")
except Exception as e:
    print(f"⚠ Economic error: {str(e)[:100]}")

# Step 3: Now create the final master dataset
print("\n2. CREATING FINAL MASTER DATASET")
print("-"*40)

master_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_master` AS
WITH 

-- Base price data
base_prices AS (
    SELECT 
        DATE(time) as date,
        close as zl_price_current,
        LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
        LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
        LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
        
        -- Returns
        (close / NULLIF(LAG(close, 1) OVER (ORDER BY time), 0) - 1) as return_1d,
        (close / NULLIF(LAG(close, 7) OVER (ORDER BY time), 0) - 1) as return_7d,
        
        -- Moving averages
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
        
        -- Volume
        volume as zl_volume,
        
        -- Targets
        LEAD(close, 5) OVER (ORDER BY time) as target_1w,
        LEAD(close, 21) OVER (ORDER BY time) as target_1m,
        LEAD(close, 63) OVER (ORDER BY time) as target_3m,
        LEAD(close, 126) OVER (ORDER BY time) as target_6m
        
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE time >= '2020-01-01'
),

-- Treasury yields
treasury_data AS (
    SELECT 
        DATE(date) as date,
        close as treasury_10y_yield,
        close - LAG(close, 1) OVER (ORDER BY date) as treasury_yield_change_1d
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
    WHERE symbol = 'US10Y' OR symbol IS NULL
),

-- Other commodities
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

wheat_prices AS (
    SELECT 
        DATE(time) as date,
        close as wheat_price
    FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
),

-- VIX
vix_data AS (
    SELECT 
        DATE(date) as date,
        close as vix_level
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- DXY
dxy_data AS (
    SELECT 
        DATE(time) as date,
        close as dxy_level
    FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
),

-- Weather aggregated
weather_data AS (
    SELECT 
        date,
        AVG(CASE WHEN region = 'US_MIDWEST' THEN temp_max END) as weather_us_temp,
        SUM(CASE WHEN region = 'US_MIDWEST' THEN precip_mm END) as weather_us_precip,
        AVG(CASE WHEN region = 'BRAZIL' THEN temp_max END) as weather_brazil_temp,
        SUM(CASE WHEN region = 'BRAZIL' THEN precip_mm END) as weather_brazil_precip,
        AVG(CASE WHEN region = 'ARGENTINA' THEN temp_max END) as weather_argentina_temp,
        SUM(CASE WHEN region = 'ARGENTINA' THEN precip_mm END) as weather_argentina_precip
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    GROUP BY date
),

-- Economic pivoted
economic_pivot AS (
    SELECT 
        date,
        MAX(CASE WHEN indicator = 'GDP' THEN value END) as econ_gdp_growth,
        MAX(CASE WHEN indicator = 'CPI' THEN value END) as econ_inflation_rate,
        MAX(CASE WHEN indicator = 'UNEMPLOYMENT' THEN value END) as econ_unemployment_rate,
        MAX(CASE WHEN indicator = 'FED_FUNDS' THEN value END) as econ_fed_funds_rate,
        MAX(CASE WHEN indicator = 'PMI' THEN value END) as econ_pmi_index
    FROM `cbi-v14.models.temp_economic_features`
    GROUP BY date
)

-- MAIN QUERY: Join everything
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
    COALESCE(wh.wheat_price, 0) as wheat_price,
    
    -- Market indicators
    COALESCE(vx.vix_level, 0) as vix_level,
    COALESCE(dx.dxy_level, 0) as dxy_level,
    
    -- Weather
    COALESCE(w.weather_us_temp, 0) as weather_us_temp,
    COALESCE(w.weather_us_precip, 0) as weather_us_precip,
    COALESCE(w.weather_brazil_temp, 0) as weather_brazil_temp,
    COALESCE(w.weather_brazil_precip, 0) as weather_brazil_precip,
    COALESCE(w.weather_argentina_temp, 0) as weather_argentina_temp,
    COALESCE(w.weather_argentina_precip, 0) as weather_argentina_precip,
    
    CURRENT_TIMESTAMP() as created_at
    
FROM base_prices bp
LEFT JOIN `cbi-v14.models.temp_cftc_features` cftc ON bp.date = cftc.date
LEFT JOIN treasury_data tr ON bp.date = tr.date
LEFT JOIN economic_pivot ec ON bp.date = ec.date
LEFT JOIN commodity_prices cr ON bp.date = cr.date
LEFT JOIN palm_prices pm ON bp.date = pm.date
LEFT JOIN corn_prices cn ON bp.date = cn.date
LEFT JOIN wheat_prices wh ON bp.date = wh.date
LEFT JOIN vix_data vx ON bp.date = vx.date
LEFT JOIN dxy_data dx ON bp.date = dx.date
LEFT JOIN weather_data w ON bp.date = w.date

WHERE bp.date >= '2020-01-01'
ORDER BY bp.date
"""

print("Creating final master dataset...")
try:
    job = client.query(master_query)
    result = job.result()
    
    # Check results
    check_query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as min_date,
        MAX(date) as max_date,
        
        -- Check data coverage
        SUM(CASE WHEN cftc_managed_net != 0 THEN 1 ELSE 0 END) as cftc_managed_filled,
        SUM(CASE WHEN treasury_10y_yield != 0 THEN 1 ELSE 0 END) as treasury_filled,
        SUM(CASE WHEN econ_gdp_growth != 0 THEN 1 ELSE 0 END) as gdp_filled,
        SUM(CASE WHEN weather_brazil_temp != 0 THEN 1 ELSE 0 END) as weather_filled,
        SUM(CASE WHEN crude_price != 0 THEN 1 ELSE 0 END) as crude_filled,
        SUM(CASE WHEN vix_level != 0 THEN 1 ELSE 0 END) as vix_filled
        
    FROM `cbi-v14.models.training_dataset_master`
    """
    
    stats = client.query(check_query).to_dataframe()
    
    print("\n✓ MASTER DATASET CREATED SUCCESSFULLY!")
    print(f"\nDataset Statistics:")
    print(f"  Total rows: {stats['total_rows'].iloc[0]:,}")
    print(f"  Date range: {stats['min_date'].iloc[0]} to {stats['max_date'].iloc[0]}")
    print(f"\nData Coverage:")
    print(f"  CFTC managed money: {stats['cftc_managed_filled'].iloc[0]:,} days")
    print(f"  Treasury yields: {stats['treasury_filled'].iloc[0]:,} days")
    print(f"  Economic data (GDP): {stats['gdp_filled'].iloc[0]:,} days")
    print(f"  Weather data: {stats['weather_filled'].iloc[0]:,} days")
    print(f"  Crude oil prices: {stats['crude_filled'].iloc[0]:,} days")
    print(f"  VIX levels: {stats['vix_filled'].iloc[0]:,} days")
    
    # Clean up temp tables
    print("\n3. CLEANING UP TEMP TABLES")
    print("-"*40)
    
    cleanup_queries = [
        "DROP TABLE IF EXISTS `cbi-v14.models.temp_cftc_features`",
        "DROP TABLE IF EXISTS `cbi-v14.models.temp_economic_features`"
    ]
    
    for query in cleanup_queries:
        try:
            client.query(query).result()
            print(f"✓ Cleaned: {query.split('.')[-1].replace('`', '')}")
        except:
            pass
    
except Exception as e:
    print(f"Error: {str(e)[:500]}")

print("\n" + "="*80)
print("MASTER DATASET CREATION COMPLETE")
print("Table: cbi-v14.models.training_dataset_master")
print("="*80)
