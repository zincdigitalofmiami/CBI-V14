#!/usr/bin/env python3
"""
ENHANCE TRAINING DATASET WITH ALL MISSING FEATURES
Add CFTC, Treasury, Economic indicators, EVERYTHING!
This will REPLACE the existing training_dataset with a complete version
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"ENHANCING TRAINING DATASET WITH ALL FEATURES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Adding CFTC, Treasury, Economic, Currency - EVERYTHING!")
print("="*80)

# Create enhanced dataset with ALL features
query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset` AS
WITH 

-- Get everything from existing training dataset
existing_features AS (
    SELECT * FROM `cbi-v14.models.training_dataset`
),

-- Add CFTC positioning data (CRITICAL for turning points!)
cftc_features AS (
    SELECT 
        DATE(report_date) as date,
        commercial_long as cftc_commercial_long,
        commercial_short as cftc_commercial_short,
        commercial_net_position as cftc_commercial_net,
        managed_money_long as cftc_managed_long,
        managed_money_short as cftc_managed_short,
        managed_money_net_position as cftc_managed_net,
        open_interest as cftc_open_interest,
        -- Calculate positioning extremes
        (managed_money_long - managed_money_short) / NULLIF(open_interest, 0) * 100 as cftc_spec_net_pct,
        (commercial_long - commercial_short) / NULLIF(open_interest, 0) * 100 as cftc_comm_net_pct,
        -- Positioning ratios
        managed_money_long / NULLIF(managed_money_long + managed_money_short, 0) as cftc_spec_long_ratio,
        commercial_long / NULLIF(commercial_long + commercial_short, 0) as cftc_comm_long_ratio
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
),

-- Add Treasury yields (interest rate environment)
treasury_features AS (
    SELECT 
        DATE(time) as date,
        close as treasury_10y_yield,
        -- Yield changes
        close - LAG(close, 1) OVER (ORDER BY time) as treasury_yield_change_1d,
        close - LAG(close, 7) OVER (ORDER BY time) as treasury_yield_change_7d,
        close - LAG(close, 30) OVER (ORDER BY time) as treasury_yield_change_30d,
        -- Yield curve indicators
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as treasury_yield_ma30,
        STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as treasury_yield_vol30
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
),

-- Add Economic indicators (GDP, inflation, unemployment, fed rates)
economic_features AS (
    SELECT 
        date,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%gdp%' THEN value END) as econ_gdp_growth,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%cpi%' OR LOWER(indicator_name) LIKE '%inflation%' 
            THEN value END) as econ_inflation_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%unemployment%' THEN value END) as econ_unemployment_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%fed%' OR LOWER(indicator_name) LIKE '%interest%' 
            OR LOWER(indicator_name) LIKE '%funds%' THEN value END) as econ_fed_funds_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%retail%' THEN value END) as econ_retail_sales,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%pmi%' OR LOWER(indicator_name) LIKE '%manufacturing%' 
            THEN value END) as econ_pmi_index,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%consumer%' AND LOWER(indicator_name) LIKE '%confidence%' 
            THEN value END) as econ_consumer_confidence,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%housing%' OR LOWER(indicator_name) LIKE '%home%' 
            THEN value END) as econ_housing_starts,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%industrial%' THEN value END) as econ_industrial_production,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%durable%' THEN value END) as econ_durable_goods
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY date
),

-- Add more currency details
currency_features AS (
    SELECT 
        date,
        MAX(CASE WHEN currency_pair = 'EUR/USD' THEN exchange_rate END) as fx_eur_usd,
        MAX(CASE WHEN currency_pair = 'USD/JPY' THEN exchange_rate END) as fx_usd_jpy,
        MAX(CASE WHEN currency_pair = 'GBP/USD' THEN exchange_rate END) as fx_gbp_usd,
        MAX(CASE WHEN currency_pair = 'USD/CAD' THEN exchange_rate END) as fx_usd_cad,
        MAX(CASE WHEN currency_pair = 'USD/BRL' THEN exchange_rate END) as fx_usd_brl,
        MAX(CASE WHEN currency_pair = 'USD/CNY' THEN exchange_rate END) as fx_usd_cny,
        MAX(CASE WHEN currency_pair = 'USD/INR' THEN exchange_rate END) as fx_usd_inr,
        MAX(CASE WHEN currency_pair = 'USD/ARS' THEN exchange_rate END) as fx_usd_ars
    FROM `cbi-v14.forecasting_data_warehouse.currency_data`
    GROUP BY date
),

-- Add news intelligence
news_features AS (
    SELECT 
        DATE(published_at) as date,
        COUNT(*) as news_article_count,
        AVG(relevance_score) as news_avg_relevance,
        MAX(relevance_score) as news_max_relevance,
        SUM(CASE WHEN LOWER(headline) LIKE '%china%' THEN 1 ELSE 0 END) as news_china_mentions,
        SUM(CASE WHEN LOWER(headline) LIKE '%tariff%' THEN 1 ELSE 0 END) as news_tariff_mentions,
        SUM(CASE WHEN LOWER(headline) LIKE '%usda%' THEN 1 ELSE 0 END) as news_usda_mentions,
        SUM(CASE WHEN LOWER(headline) LIKE '%drought%' OR LOWER(headline) LIKE '%flood%' 
            THEN 1 ELSE 0 END) as news_weather_mentions
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    GROUP BY date
),

-- Add USDA export sales
export_features AS (
    SELECT 
        DATE(week_ending) as date,
        weekly_exports as usda_weekly_exports,
        accumulated_exports as usda_accumulated_exports,
        outstanding_sales as usda_outstanding_sales,
        next_year_outstanding_sales as usda_next_year_sales
    FROM `cbi-v14.forecasting_data_warehouse.usda_export_sales`
),

-- Add harvest progress
harvest_features AS (
    SELECT 
        date,
        MAX(CASE WHEN LOWER(commodity) LIKE '%soybean%' AND LOWER(activity) LIKE '%harvest%' 
            THEN progress_percent END) as harvest_soybean_pct,
        MAX(CASE WHEN LOWER(commodity) LIKE '%corn%' AND LOWER(activity) LIKE '%harvest%' 
            THEN progress_percent END) as harvest_corn_pct,
        MAX(CASE WHEN LOWER(commodity) LIKE '%soybean%' AND LOWER(activity) LIKE '%plant%' 
            THEN progress_percent END) as planting_soybean_pct,
        MAX(CASE WHEN LOWER(commodity) LIKE '%corn%' AND LOWER(activity) LIKE '%plant%' 
            THEN progress_percent END) as planting_corn_pct
    FROM `cbi-v14.forecasting_data_warehouse.usda_harvest_progress`
    GROUP BY date
),

-- Add biofuel data
biofuel_features AS (
    SELECT 
        DATE(time) as date,
        close as biofuel_ethanol_price,
        volume as biofuel_ethanol_volume
    FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
),

-- Add more detailed VIX features
vix_advanced AS (
    SELECT 
        date,
        close as vix_close,
        high as vix_high,
        low as vix_low,
        -- VIX term structure
        close - LAG(close, 1) OVER (ORDER BY date) as vix_change_1d,
        (high - low) as vix_daily_range,
        -- Percentile ranks
        PERCENT_RANK() OVER (ORDER BY close) as vix_percentile_rank,
        -- Rolling metrics
        MAX(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_high,
        MIN(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_low
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Add all other commodity prices we haven't included
additional_commodities AS (
    SELECT 
        DATE(time) as date,
        close as canola_oil_price
    FROM `cbi-v14.forecasting_data_warehouse.canola_oil_prices`
),

-- Add volatility data
volatility_features AS (
    SELECT 
        date,
        realized_volatility,
        implied_volatility,
        volatility_spread,
        volatility_regime
    FROM `cbi-v14.forecasting_data_warehouse.volatility_data`
)

-- FINAL JOIN - Add ALL new features to existing
SELECT 
    ef.*,
    -- CFTC features
    cf.cftc_commercial_long,
    cf.cftc_commercial_short,
    cf.cftc_commercial_net,
    cf.cftc_managed_long,
    cf.cftc_managed_short,
    cf.cftc_managed_net,
    cf.cftc_open_interest,
    cf.cftc_spec_net_pct,
    cf.cftc_comm_net_pct,
    cf.cftc_spec_long_ratio,
    cf.cftc_comm_long_ratio,
    -- Treasury features
    tf.treasury_10y_yield,
    tf.treasury_yield_change_1d,
    tf.treasury_yield_change_7d,
    tf.treasury_yield_change_30d,
    tf.treasury_yield_ma30,
    tf.treasury_yield_vol30,
    -- Economic features
    ecf.econ_gdp_growth,
    ecf.econ_inflation_rate,
    ecf.econ_unemployment_rate,
    ecf.econ_fed_funds_rate,
    ecf.econ_retail_sales,
    ecf.econ_pmi_index,
    ecf.econ_consumer_confidence,
    ecf.econ_housing_starts,
    ecf.econ_industrial_production,
    ecf.econ_durable_goods,
    -- Currency features
    crf.fx_eur_usd,
    crf.fx_usd_jpy,
    crf.fx_gbp_usd,
    crf.fx_usd_cad,
    crf.fx_usd_brl,
    crf.fx_usd_cny,
    crf.fx_usd_inr,
    crf.fx_usd_ars,
    -- News features
    nf.news_article_count,
    nf.news_avg_relevance,
    nf.news_max_relevance,
    nf.news_china_mentions,
    nf.news_tariff_mentions,
    nf.news_usda_mentions,
    nf.news_weather_mentions,
    -- Export features
    exf.usda_weekly_exports,
    exf.usda_accumulated_exports,
    exf.usda_outstanding_sales,
    exf.usda_next_year_sales,
    -- Harvest features
    hf.harvest_soybean_pct,
    hf.harvest_corn_pct,
    hf.planting_soybean_pct,
    hf.planting_corn_pct,
    -- Biofuel features
    bf.biofuel_ethanol_price,
    bf.biofuel_ethanol_volume,
    -- Advanced VIX features
    vxf.vix_close,
    vxf.vix_high,
    vxf.vix_low,
    vxf.vix_change_1d,
    vxf.vix_daily_range,
    vxf.vix_percentile_rank,
    vxf.vix_52w_high,
    vxf.vix_52w_low,
    -- Additional commodities
    ac.canola_oil_price,
    -- Volatility features
    vf.realized_volatility,
    vf.implied_volatility,
    vf.volatility_spread,
    vf.volatility_regime
FROM existing_features ef
LEFT JOIN cftc_features cf ON ef.date = cf.date
LEFT JOIN treasury_features tf ON ef.date = tf.date
LEFT JOIN economic_features ecf ON ef.date = ecf.date
LEFT JOIN currency_features crf ON ef.date = crf.date
LEFT JOIN news_features nf ON ef.date = nf.date
LEFT JOIN export_features exf ON ef.date = exf.date
LEFT JOIN harvest_features hf ON ef.date = hf.date
LEFT JOIN biofuel_features bf ON ef.date = bf.date
LEFT JOIN vix_advanced vxf ON ef.date = vxf.date
LEFT JOIN additional_commodities ac ON ef.date = ac.date
LEFT JOIN volatility_features vf ON ef.date = vf.date
"""

print("Enhancing training dataset with ALL features...")
print("\nAdding:")
print("  ✓ CFTC positioning (commercial vs specs)")
print("  ✓ Treasury yields and changes")
print("  ✓ Economic indicators (GDP, inflation, unemployment, fed rates, PMI, etc.)")
print("  ✓ Currency pairs (EUR, JPY, BRL, CNY, etc.)")
print("  ✓ News intelligence")
print("  ✓ USDA export sales")
print("  ✓ Harvest progress")
print("  ✓ Biofuel prices")
print("  ✓ Advanced VIX features")
print("  ✓ Additional commodities")
print("  ✓ Volatility metrics")

try:
    job = client.query(query)
    print(f"\nJob ID: {job.job_id}")
    print("Running...")
    
    result = job.result()
    
    print("\n" + "="*80)
    print("✓ SUCCESS! TRAINING DATASET ENHANCED WITH ALL FEATURES!")
    print("="*80)
    
    # Check the results
    check_query = """
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT date) as days
    FROM `cbi-v14.models.training_dataset`
    """
    
    stats = client.query(check_query).to_dataframe()
    print(f"\nDataset statistics:")
    print(f"  Rows: {stats['rows'].iloc[0]:,}")
    print(f"  Days: {stats['days'].iloc[0]:,}")
    
    # Count columns
    col_query = "SELECT * FROM `cbi-v14.models.training_dataset` LIMIT 1"
    cols = client.query(col_query).to_dataframe()
    
    original_features = 159
    new_features = len(cols.columns)
    added_features = new_features - original_features
    
    print(f"\nFeature count:")
    print(f"  Original features: {original_features}")
    print(f"  New total features: {new_features}")
    print(f"  Features added: {added_features}")
    
    # List some of the new features
    new_feature_names = [c for c in cols.columns if any(prefix in c for prefix in 
                         ['cftc_', 'treasury_', 'econ_', 'fx_', 'news_', 'usda_', 'harvest_', 'biofuel_', 'vix_'])]
    
    print(f"\nNew features added include:")
    for feat in new_feature_names[:20]:
        print(f"  ✓ {feat}")
    if len(new_feature_names) > 20:
        print(f"  ... and {len(new_feature_names)-20} more")
    
    print("\n" + "="*80)
    print("TRAINING DATASET NOW HAS EVERYTHING!")
    print("="*80)
    print("\nReady to retrain models with COMPLETE feature set!")
    print("This includes ALL intelligence data:")
    print("- CFTC positioning")
    print("- Treasury yields")
    print("- Economic indicators")
    print("- Currency data")
    print("- News intelligence")
    print("- USDA data")
    print("- Everything!")
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nThis might be a join issue. Let me check the tables...")
