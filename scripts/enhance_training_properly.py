#!/usr/bin/env python3
"""
PROPERLY enhance training dataset handling EACH table's specific schema
Because every fucking table uses different column names!
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"PROPERLY ENHANCING TRAINING DATASET - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Handling each table's ACTUAL column names")
print("="*80)

# The CORRECT query with proper column names for each table
query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset` AS
WITH 

-- Get existing features
existing_features AS (
    SELECT * FROM `cbi-v14.models.training_dataset`
),

-- CFTC features (uses report_date)
cftc_features AS (
    SELECT 
        DATE(report_date) as date,  -- report_date not date!
        commercial_long as cftc_commercial_long,
        commercial_short as cftc_commercial_short,
        commercial_net as cftc_commercial_net,
        managed_money_long as cftc_managed_long,
        managed_money_short as cftc_managed_short,
        managed_money_net as cftc_managed_net,
        open_interest as cftc_open_interest,
        (managed_money_long - managed_money_short) / NULLIF(open_interest, 0) * 100 as cftc_spec_net_pct,
        (commercial_long - commercial_short) / NULLIF(open_interest, 0) * 100 as cftc_comm_net_pct
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    WHERE commodity = 'SOYBEAN OIL' OR commodity IS NULL  -- Filter for soybean oil if needed
),

-- Treasury features (uses time not date!)
treasury_features AS (
    SELECT 
        DATE(time) as date,  -- time not date!
        close as treasury_10y_yield,
        close - LAG(close, 1) OVER (ORDER BY time) as treasury_yield_change_1d,
        close - LAG(close, 7) OVER (ORDER BY time) as treasury_yield_change_7d,
        close - LAG(close, 30) OVER (ORDER BY time) as treasury_yield_change_30d,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as treasury_yield_ma30
    FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
),

-- Economic features (uses time and indicator, not indicator_name!)
economic_features AS (
    SELECT 
        DATE(time) as date,  -- time not date!
        MAX(CASE WHEN LOWER(indicator) LIKE '%gdp%' THEN value END) as econ_gdp_growth,
        MAX(CASE WHEN LOWER(indicator) LIKE '%cpi%' OR LOWER(indicator) LIKE '%inflation%' THEN value END) as econ_inflation_rate,
        MAX(CASE WHEN LOWER(indicator) LIKE '%unemployment%' THEN value END) as econ_unemployment_rate,
        MAX(CASE WHEN LOWER(indicator) LIKE '%fed%' OR LOWER(indicator) LIKE '%interest%' THEN value END) as econ_fed_funds_rate,
        MAX(CASE WHEN LOWER(indicator) LIKE '%retail%' THEN value END) as econ_retail_sales,
        MAX(CASE WHEN LOWER(indicator) LIKE '%pmi%' OR LOWER(indicator) LIKE '%manufacturing%' THEN value END) as econ_pmi_index
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY DATE(time)
),

-- News features (uses processed_timestamp!)
news_features AS (
    SELECT 
        DATE(processed_timestamp) as date,  -- processed_timestamp not published_at!
        COUNT(*) as news_article_count,
        AVG(intelligence_score) as news_avg_intelligence_score,  -- intelligence_score not relevance_score!
        MAX(intelligence_score) as news_max_intelligence_score,
        SUM(CASE WHEN LOWER(title) LIKE '%china%' OR LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as news_china_mentions,
        SUM(CASE WHEN LOWER(title) LIKE '%tariff%' OR LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as news_tariff_mentions,
        SUM(CASE WHEN LOWER(title) LIKE '%usda%' OR LOWER(content) LIKE '%usda%' THEN 1 ELSE 0 END) as news_usda_mentions
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    GROUP BY DATE(processed_timestamp)
),

-- VIX features (uses date correctly)
vix_advanced AS (
    SELECT 
        date,  -- This one actually uses date!
        close as vix_close,
        high as vix_high,
        low as vix_low,
        open as vix_open,
        volume as vix_volume,
        close - LAG(close, 1) OVER (ORDER BY date) as vix_change_1d,
        (high - low) as vix_daily_range,
        MAX(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_high,
        MIN(close) OVER (ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) as vix_52w_low
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Currency features (uses date and rate, not exchange_rate!)
currency_features AS (
    SELECT 
        date,
        MAX(CASE WHEN from_currency = 'EUR' AND to_currency = 'USD' THEN rate END) as fx_eur_usd,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'JPY' THEN rate END) as fx_usd_jpy,
        MAX(CASE WHEN from_currency = 'GBP' AND to_currency = 'USD' THEN rate END) as fx_gbp_usd,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'BRL' THEN rate END) as fx_usd_brl,
        MAX(CASE WHEN from_currency = 'USD' AND to_currency = 'CNY' THEN rate END) as fx_usd_cny
    FROM `cbi-v14.forecasting_data_warehouse.currency_data`
    GROUP BY date
),

-- USDA export features (uses report_date!)
export_features AS (
    SELECT 
        DATE(report_date) as date,  -- report_date not date!
        SUM(net_sales_mt) as usda_net_sales,
        SUM(cumulative_exports_mt) as usda_cumulative_exports
    FROM `cbi-v14.forecasting_data_warehouse.usda_export_sales`
    WHERE LOWER(commodity) LIKE '%soy%'
    GROUP BY DATE(report_date)
),

-- Harvest progress (uses harvest_date!)
harvest_features AS (
    SELECT 
        DATE(harvest_date) as date,  -- harvest_date not date!
        AVG(harvest_percentage) as harvest_progress_pct
    FROM `cbi-v14.forecasting_data_warehouse.usda_harvest_progress`
    GROUP BY DATE(harvest_date)
),

-- Biofuel features (uses date correctly)
biofuel_features AS (
    SELECT 
        DATE(date) as date,
        close as biofuel_ethanol_price,
        volume as biofuel_ethanol_volume
    FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
),

-- Trump policy features (uses timestamp!)
policy_features AS (
    SELECT 
        DATE(timestamp) as date,  -- timestamp not created_at!
        AVG(agricultural_impact) as policy_ag_impact_avg,
        MAX(agricultural_impact) as policy_ag_impact_max,
        AVG(soybean_relevance) as policy_soy_relevance_avg,
        COUNT(*) as policy_event_count
    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
    GROUP BY DATE(timestamp)
),

-- Volatility features (uses data_date and last_price!)
volatility_features AS (
    SELECT 
        DATE(data_date) as date,  -- data_date not date!
        AVG(last_price) as volatility_last_price,  -- last_price not close!
        AVG(implied_vol) as implied_volatility,
        AVG(iv_hv_ratio) as iv_hv_ratio
    FROM `cbi-v14.forecasting_data_warehouse.volatility_data`
    GROUP BY DATE(data_date)
)

-- FINAL JOIN with ALL features
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
    -- Treasury features
    tf.treasury_10y_yield,
    tf.treasury_yield_change_1d,
    tf.treasury_yield_change_7d,
    tf.treasury_yield_change_30d,
    tf.treasury_yield_ma30,
    -- Economic features
    ecf.econ_gdp_growth,
    ecf.econ_inflation_rate,
    ecf.econ_unemployment_rate,
    ecf.econ_fed_funds_rate,
    ecf.econ_retail_sales,
    ecf.econ_pmi_index,
    -- News features
    nf.news_article_count,
    nf.news_avg_intelligence_score,
    nf.news_max_intelligence_score,
    nf.news_china_mentions,
    nf.news_tariff_mentions,
    nf.news_usda_mentions,
    -- VIX features
    vxf.vix_close,
    vxf.vix_high,
    vxf.vix_low,
    vxf.vix_open,
    vxf.vix_volume,
    vxf.vix_change_1d,
    vxf.vix_daily_range,
    vxf.vix_52w_high,
    vxf.vix_52w_low,
    -- Currency features
    crf.fx_eur_usd,
    crf.fx_usd_jpy,
    crf.fx_gbp_usd,
    crf.fx_usd_brl,
    crf.fx_usd_cny,
    -- USDA export features
    exf.usda_net_sales,
    exf.usda_cumulative_exports,
    -- Harvest features
    hf.harvest_progress_pct,
    -- Biofuel features
    bf.biofuel_ethanol_price,
    bf.biofuel_ethanol_volume,
    -- Policy features
    pf.policy_ag_impact_avg,
    pf.policy_ag_impact_max,
    pf.policy_soy_relevance_avg,
    pf.policy_event_count,
    -- Volatility features
    vf.volatility_last_price,
    vf.implied_volatility,
    vf.iv_hv_ratio
FROM existing_features ef
LEFT JOIN cftc_features cf ON ef.date = cf.date
LEFT JOIN treasury_features tf ON ef.date = tf.date
LEFT JOIN economic_features ecf ON ef.date = ecf.date
LEFT JOIN news_features nf ON ef.date = nf.date
LEFT JOIN vix_advanced vxf ON ef.date = vxf.date
LEFT JOIN currency_features crf ON ef.date = crf.date
LEFT JOIN export_features exf ON ef.date = exf.date
LEFT JOIN harvest_features hf ON ef.date = hf.date
LEFT JOIN biofuel_features bf ON ef.date = bf.date
LEFT JOIN policy_features pf ON ef.date = pf.date
LEFT JOIN volatility_features vf ON ef.date = vf.date
"""

print("Running query with CORRECT column names for each table...")
print("\nThis handles:")
print("  - cftc_cot: report_date")
print("  - treasury_prices: time")
print("  - economic_indicators: time, indicator, value")
print("  - news_intelligence: processed_timestamp, intelligence_score")
print("  - vix_daily: date (correct!)")
print("  - currency_data: date, rate")
print("  - usda_export_sales: report_date")
print("  - usda_harvest_progress: harvest_date")
print("  - biofuel_prices: date")
print("  - trump_policy_intelligence: timestamp")
print("  - volatility_data: data_date, last_price")

try:
    job = client.query(query)
    print(f"\nJob ID: {job.job_id}")
    print("Running...")
    
    result = job.result()
    
    print("\n" + "="*80)
    print("✓ SUCCESS! TRAINING DATASET ENHANCED WITH ALL FEATURES!")
    print("="*80)
    
    # Check results
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
    
    print(f"\nTotal features: {len(cols.columns)}")
    
    # Check which new features were added
    new_features = [c for c in cols.columns if any(prefix in c for prefix in 
                    ['cftc_', 'treasury_', 'econ_', 'fx_', 'news_', 'usda_', 
                     'harvest_', 'biofuel_', 'vix_', 'policy_', 'volatility_', 'implied_'])]
    
    print(f"\nNew features added: {len(new_features)}")
    print("\nSample of new features:")
    for feat in new_features[:20]:
        print(f"  ✓ {feat}")
    if len(new_features) > 20:
        print(f"  ... and {len(new_features)-20} more")
    
    print("\n" + "="*80)
    print("ALL FEATURES NOW INCLUDED!")
    print("="*80)
    print("\nDespite the schema mess, we now have:")
    print("- CFTC positioning data")
    print("- Treasury yields")
    print("- Economic indicators")
    print("- News intelligence")
    print("- Currency data")
    print("- USDA exports")
    print("- Harvest progress")
    print("- Biofuel prices")
    print("- Policy impacts")
    print("- Volatility metrics")
    print("\nALL IN THE TRAINING DATASET!")
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nLet me check which specific table is causing issues...")
