#!/usr/bin/env python3
"""
CREATE MASTER TRAINING DATASET WITH ALL AVAILABLE DATA
Properly integrate all data sources with correct schema, calculations, and optimizations
"""

from google.cloud import bigquery
from datetime import datetime

print("="*80)
print("CREATING MASTER TRAINING DATASET")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

client = bigquery.Client(project='cbi-v14')

# First, create a backup of current training dataset
print("\n1. BACKING UP CURRENT DATASET")
print("-"*40)

backup_query = f"""
CREATE OR REPLACE TABLE `cbi-v14.bkp.training_dataset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}` AS
SELECT * FROM `cbi-v14.models.training_complete_enhanced`
"""

try:
    client.query(backup_query).result()
    print("✓ Backup created successfully")
except Exception as e:
    print(f"⚠ Backup warning: {str(e)[:100]}")

# Now create the master dataset with ALL data properly integrated
print("\n2. CREATING MASTER TRAINING DATASET")
print("-"*40)

master_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_master` AS
WITH 

-- Base price data with proper date alignment
base_prices AS (
    SELECT 
        DATE(time) as date,
        close as zl_price_current,
        LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
        LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
        LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
        
        -- Calculate returns
        (close / LAG(close, 1) OVER (ORDER BY time) - 1) as return_1d,
        (close / LAG(close, 7) OVER (ORDER BY time) - 1) as return_7d,
        
        -- Moving averages
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7d,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as ma_30d,
        
        -- Volatility
        STDDEV(close / LAG(close, 1) OVER (ORDER BY time) - 1) 
            OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as volatility_30d,
        
        -- Volume
        volume as zl_volume,
        
        -- Future targets
        LEAD(close, 5) OVER (ORDER BY time) as target_1w,
        LEAD(close, 21) OVER (ORDER BY time) as target_1m,
        LEAD(close, 63) OVER (ORDER BY time) as target_3m,
        LEAD(close, 126) OVER (ORDER BY time) as target_6m
        
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE time >= '2020-01-01'
),

-- CFTC Data with PROPER managed money data
cftc_enhanced AS (
    SELECT 
        report_date as date,
        
        -- Commercial positions (hedgers)
        commercial_long as cftc_commercial_long,
        commercial_short as cftc_commercial_short,
        commercial_net as cftc_commercial_net,
        
        -- Managed money positions (specs) - THESE EXIST IN THE TABLE
        managed_money_long as cftc_managed_long,
        managed_money_short as cftc_managed_short,
        managed_money_net as cftc_managed_net,
        
        -- Open interest
        open_interest as cftc_open_interest,
        
        -- Calculate positioning metrics
        SAFE_DIVIDE(managed_money_net, open_interest) * 100 as cftc_spec_net_pct,
        SAFE_DIVIDE(commercial_net, open_interest) * 100 as cftc_comm_net_pct,
        
        -- Positioning extremes
        PERCENTILE_CONT(managed_money_net, 0.9) 
            OVER (ORDER BY report_date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as cftc_spec_90th_percentile,
        PERCENTILE_CONT(managed_money_net, 0.1) 
            OVER (ORDER BY report_date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as cftc_spec_10th_percentile
            
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    WHERE commodity = 'SOYBEAN OIL'
),

-- Treasury yields with proper calculations
treasury_data AS (
    SELECT 
        DATE(date) as date,
        close as treasury_10y_yield,
        
        -- Yield changes
        close - LAG(close, 1) OVER (ORDER BY date) as treasury_yield_change_1d,
        close - LAG(close, 7) OVER (ORDER BY date) as treasury_yield_change_7d,
        close - LAG(close, 30) OVER (ORDER BY date) as treasury_yield_change_30d,
        
        -- Yield curve shape indicators
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as treasury_yield_ma30,
        
        -- Rate volatility
        STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as treasury_yield_vol30
        
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
    WHERE symbol = 'US10Y'
),

-- Economic indicators properly pivoted
economic_data AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN indicator = 'GDP' THEN value END) as econ_gdp_growth,
        MAX(CASE WHEN indicator = 'CPI' THEN value END) as econ_inflation_rate,
        MAX(CASE WHEN indicator = 'UNEMPLOYMENT' THEN value END) as econ_unemployment_rate,
        MAX(CASE WHEN indicator = 'FED_FUNDS' THEN value END) as econ_fed_funds_rate,
        MAX(CASE WHEN indicator = 'RETAIL_SALES' THEN value END) as econ_retail_sales,
        MAX(CASE WHEN indicator = 'PMI' THEN value END) as econ_pmi_index,
        MAX(CASE WHEN indicator = 'CONSUMER_CONFIDENCE' THEN value END) as econ_consumer_confidence,
        MAX(CASE WHEN indicator = 'HOUSING_STARTS' THEN value END) as econ_housing_starts,
        MAX(CASE WHEN indicator = 'INDUSTRIAL_PRODUCTION' THEN value END) as econ_industrial_production,
        MAX(CASE WHEN indicator = 'DURABLE_GOODS' THEN value END) as econ_durable_goods
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY date
),

-- Currency data with key pairs
currency_data AS (
    SELECT 
        date,
        MAX(CASE WHEN from_currency = 'EUR' AND to_currency = 'USD' THEN rate END) as fx_eur_usd,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'JPY' THEN rate END) as fx_usd_jpy,
        MAX(CASE WHEN from_currency = 'GBP' AND to_currency = 'USD' THEN rate END) as fx_gbp_usd,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'BRL' THEN rate END) as fx_usd_brl,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'CNY' THEN rate END) as fx_usd_cny,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'ARS' THEN rate END) as fx_usd_ars
    FROM `cbi-v14.forecasting_data_warehouse.currency_data`
    GROUP BY date
),

-- Weather data aggregated by region
weather_aggregated AS (
    SELECT 
        date,
        
        -- US Midwest weather
        AVG(CASE WHEN region = 'US_MIDWEST' THEN temp_max END) as weather_us_temp,
        SUM(CASE WHEN region = 'US_MIDWEST' THEN precip_mm END) as weather_us_precip,
        
        -- Brazil weather
        AVG(CASE WHEN region = 'BRAZIL' THEN temp_max END) as weather_brazil_temp,
        SUM(CASE WHEN region = 'BRAZIL' THEN precip_mm END) as weather_brazil_precip,
        
        -- Argentina weather
        AVG(CASE WHEN region = 'ARGENTINA' THEN temp_max END) as weather_argentina_temp,
        SUM(CASE WHEN region = 'ARGENTINA' THEN precip_mm END) as weather_argentina_precip,
        
        -- Weather stress indicators
        CASE WHEN AVG(CASE WHEN region = 'US_MIDWEST' THEN temp_max END) > 35 THEN 1 ELSE 0 END as us_heat_stress,
        CASE WHEN SUM(CASE WHEN region = 'BRAZIL' THEN precip_mm END) < 50 THEN 1 ELSE 0 END as brazil_drought_signal
        
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    GROUP BY date
),

-- Other commodity prices for correlations
commodity_prices AS (
    SELECT 
        DATE(cp.time) as date,
        cp.close as crude_price,
        pp.close as palm_price,
        cn.close as corn_price,
        wh.close as wheat_price,
        sm.close as meal_price,
        sb.close as bean_price
    FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices` cp
    FULL OUTER JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`) pp USING(date)
    FULL OUTER JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.corn_prices`) cn USING(date)
    FULL OUTER JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`) wh USING(date)
    FULL OUTER JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`) sm USING(date)
    FULL OUTER JOIN (SELECT DATE(time) as date, close FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`) sb USING(date)
),

-- VIX and market indicators
market_indicators AS (
    SELECT 
        DATE(date) as date,
        close as vix_level,
        -- VIX regimes
        CASE 
            WHEN close < 15 THEN 'low_vol'
            WHEN close < 25 THEN 'normal'
            WHEN close < 35 THEN 'elevated'
            ELSE 'crisis'
        END as vix_regime
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- DXY dollar index
dollar_index AS (
    SELECT 
        DATE(time) as date,
        close as dxy_level
    FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
),

-- News and sentiment features (keep existing)
news_features AS (
    SELECT 
        date,
        COUNT(*) as news_article_count,
        AVG(sentiment_score) as news_avg_score,
        COUNT(DISTINCT source) as news_source_count,
        SUM(CASE WHEN relevance_score > 0.7 THEN 1 ELSE 0 END) as news_high_relevance_count
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    GROUP BY date
)

-- MAIN QUERY: Join everything together
SELECT 
    bp.*,
    
    -- CFTC features (with proper managed money data)
    COALESCE(cftc.cftc_commercial_long, 0) as cftc_commercial_long,
    COALESCE(cftc.cftc_commercial_short, 0) as cftc_commercial_short,
    COALESCE(cftc.cftc_commercial_net, 0) as cftc_commercial_net,
    COALESCE(cftc.cftc_managed_long, 0) as cftc_managed_long,
    COALESCE(cftc.cftc_managed_short, 0) as cftc_managed_short,
    COALESCE(cftc.cftc_managed_net, 0) as cftc_managed_net,
    COALESCE(cftc.cftc_open_interest, 0) as cftc_open_interest,
    COALESCE(cftc.cftc_spec_net_pct, 0) as cftc_spec_net_pct,
    COALESCE(cftc.cftc_comm_net_pct, 0) as cftc_comm_net_pct,
    
    -- Treasury features
    COALESCE(tr.treasury_10y_yield, 0) as treasury_10y_yield,
    COALESCE(tr.treasury_yield_change_1d, 0) as treasury_yield_change_1d,
    COALESCE(tr.treasury_yield_change_7d, 0) as treasury_yield_change_7d,
    COALESCE(tr.treasury_yield_ma30, 0) as treasury_yield_ma30,
    
    -- Economic features
    COALESCE(ec.econ_gdp_growth, 0) as econ_gdp_growth,
    COALESCE(ec.econ_inflation_rate, 0) as econ_inflation_rate,
    COALESCE(ec.econ_unemployment_rate, 0) as econ_unemployment_rate,
    COALESCE(ec.econ_fed_funds_rate, 0) as econ_fed_funds_rate,
    COALESCE(ec.econ_pmi_index, 0) as econ_pmi_index,
    
    -- Currency features
    COALESCE(fx.fx_usd_brl, 0) as fx_usd_brl,
    COALESCE(fx.fx_usd_cny, 0) as fx_usd_cny,
    COALESCE(fx.fx_usd_ars, 0) as fx_usd_ars,
    
    -- Weather features
    COALESCE(w.weather_us_temp, 0) as weather_us_temp,
    COALESCE(w.weather_us_precip, 0) as weather_us_precip,
    COALESCE(w.weather_brazil_temp, 0) as weather_brazil_temp,
    COALESCE(w.weather_brazil_precip, 0) as weather_brazil_precip,
    COALESCE(w.weather_argentina_temp, 0) as weather_argentina_temp,
    COALESCE(w.us_heat_stress, 0) as us_heat_stress,
    COALESCE(w.brazil_drought_signal, 0) as brazil_drought_signal,
    
    -- Commodity prices
    COALESCE(cp.crude_price, 0) as crude_price,
    COALESCE(cp.palm_price, 0) as palm_price,
    COALESCE(cp.corn_price, 0) as corn_price,
    COALESCE(cp.wheat_price, 0) as wheat_price,
    COALESCE(cp.meal_price, 0) as meal_price,
    COALESCE(cp.bean_price, 0) as bean_price,
    
    -- Market indicators
    COALESCE(mi.vix_level, 0) as vix_level,
    COALESCE(mi.vix_regime, 'normal') as vix_regime,
    COALESCE(di.dxy_level, 0) as dxy_level,
    
    -- News features
    COALESCE(nf.news_article_count, 0) as news_article_count,
    COALESCE(nf.news_avg_score, 0) as news_avg_score,
    COALESCE(nf.news_source_count, 0) as news_source_count,
    
    -- Timestamp for tracking
    CURRENT_TIMESTAMP() as created_at
    
FROM base_prices bp
LEFT JOIN cftc_enhanced cftc ON bp.date = cftc.date
LEFT JOIN treasury_data tr ON bp.date = tr.date
LEFT JOIN economic_data ec ON bp.date = ec.date
LEFT JOIN currency_data fx ON bp.date = fx.date
LEFT JOIN weather_aggregated w ON bp.date = w.date
LEFT JOIN commodity_prices cp ON bp.date = cp.date
LEFT JOIN market_indicators mi ON bp.date = mi.date
LEFT JOIN dollar_index di ON bp.date = di.date
LEFT JOIN news_features nf ON bp.date = nf.date

WHERE bp.date >= '2020-01-01'
ORDER BY bp.date
"""

print("Creating master training dataset...")
print("This integrates:")
print("  • Soybean oil prices with proper calculations")
print("  • CFTC data INCLUDING managed money positions")
print("  • Treasury yields from treasury_prices table")
print("  • Economic indicators (GDP, CPI, unemployment, etc.)")
print("  • Currency data (BRL, CNY, ARS)")
print("  • Weather data (US, Brazil, Argentina)")
print("  • Commodity prices (crude, palm, corn, wheat)")
print("  • VIX and DXY indices")
print("  • News features")

try:
    job = client.query(master_query)
    result = job.result()
    
    # Check the results
    check_query = """
    SELECT 
        COUNT(*) as total_rows,
        MIN(date) as min_date,
        MAX(date) as max_date,
        
        -- Check CFTC managed money
        SUM(CASE WHEN cftc_managed_net != 0 THEN 1 ELSE 0 END) as cftc_managed_filled,
        
        -- Check Treasury
        SUM(CASE WHEN treasury_10y_yield != 0 THEN 1 ELSE 0 END) as treasury_filled,
        
        -- Check Economic
        SUM(CASE WHEN econ_gdp_growth != 0 THEN 1 ELSE 0 END) as gdp_filled,
        
        -- Check Weather
        SUM(CASE WHEN weather_brazil_temp != 0 THEN 1 ELSE 0 END) as weather_filled
        
    FROM `cbi-v14.models.training_dataset_master`
    """
    
    stats = client.query(check_query).to_dataframe()
    
    print("\n✓ Master dataset created successfully!")
    print(f"\nDataset Statistics:")
    print(f"  Total rows: {stats['total_rows'].iloc[0]:,}")
    print(f"  Date range: {stats['min_date'].iloc[0]} to {stats['max_date'].iloc[0]}")
    print(f"\nData Coverage:")
    print(f"  CFTC managed money: {stats['cftc_managed_filled'].iloc[0]:,} days")
    print(f"  Treasury yields: {stats['treasury_filled'].iloc[0]:,} days")
    print(f"  Economic data: {stats['gdp_filled'].iloc[0]:,} days")
    print(f"  Weather data: {stats['weather_filled'].iloc[0]:,} days")
    
except Exception as e:
    print(f"Error creating master dataset: {str(e)[:500]}")

print("\n" + "="*80)
print("MASTER DATASET CREATION COMPLETE")
print("="*80)
