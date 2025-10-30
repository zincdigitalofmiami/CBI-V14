#!/usr/bin/env python3
"""
CREATE COMPLETE TRAINING DATASET V2 - WITH ALL FEATURES
NO SIMPLIFIED VERSION - FULL INSTITUTIONAL GRADE
All schemas are now fixed so this WILL work
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"CREATING COMPLETE TRAINING DATASET V2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("NO SIMPLIFIED VERSION - FULL FEATURE SET")
print("="*80)

# Now that schemas are fixed, this query will work
query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_complete_v2` AS
WITH 

-- Base prices and targets
base_prices AS (
    SELECT 
        DATE(time) as date,
        close as zl_price_current,
        open as zl_open,
        high as zl_high,
        low as zl_low,
        volume as zl_volume,
        -- Momentum
        close - LAG(close, 1) OVER (ORDER BY time) as zl_return_1d,
        close - LAG(close, 7) OVER (ORDER BY time) as zl_return_7d,
        -- Moving averages
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as zl_ma7,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_ma30,
        -- Volatility
        STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_vol30,
        -- Targets
        LEAD(close, 7) OVER (ORDER BY time) as target_1w,
        LEAD(close, 30) OVER (ORDER BY time) as target_1m,
        LEAD(close, 90) OVER (ORDER BY time) as target_3m,
        LEAD(close, 180) OVER (ORDER BY time) as target_6m
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
),

-- All commodity prices (FIXED SCHEMAS)
commodities AS (
    SELECT 
        DATE(time) as date,
        MAX(CASE WHEN source = 'soybeans' THEN close END) as soybeans_price,
        MAX(CASE WHEN source = 'soybean_meal' THEN close END) as soymeal_price,
        MAX(CASE WHEN source = 'palm_oil' THEN close END) as palm_oil_price,
        MAX(CASE WHEN source = 'corn' THEN close END) as corn_price,
        MAX(CASE WHEN source = 'wheat' THEN close END) as wheat_price,
        MAX(CASE WHEN source = 'crude_oil' THEN close END) as crude_oil_price,
        MAX(CASE WHEN source = 'natural_gas' THEN close END) as natural_gas_price,
        MAX(CASE WHEN source = 'gold' THEN close END) as gold_price,
        MAX(CASE WHEN source = 'sp500' THEN close END) as sp500_price,
        MAX(CASE WHEN source = 'treasury' THEN close END) as treasury_yield,
        MAX(CASE WHEN source = 'usd_index' THEN close END) as usd_index
    FROM (
        SELECT DATE(time) as time, 'soybeans' as source, close 
        FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
        UNION ALL
        SELECT DATE(time), 'soybean_meal', close 
        FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
        UNION ALL
        SELECT DATE(time), 'palm_oil', close 
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
        UNION ALL
        SELECT DATE(time), 'corn', close 
        FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
        UNION ALL
        SELECT DATE(time), 'wheat', close 
        FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
        UNION ALL
        SELECT DATE(time), 'crude_oil', close
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        UNION ALL
        SELECT DATE(time), 'natural_gas', close
        FROM `cbi-v14.forecasting_data_warehouse.natural_gas_prices`
        UNION ALL
        SELECT DATE(time), 'gold', close
        FROM `cbi-v14.forecasting_data_warehouse.gold_prices`
        UNION ALL
        SELECT DATE(time), 'sp500', close
        FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`
        UNION ALL
        SELECT DATE(time), 'treasury', close
        FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
        UNION ALL
        SELECT DATE(time), 'usd_index', close
        FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
    )
    GROUP BY date
),

-- VIX and volatility regimes
vix_data AS (
    SELECT 
        date,
        close as vix_level,
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as vix_ma7,
        STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_std30,
        CASE 
            WHEN close > 40 THEN 4
            WHEN close > 30 THEN 3
            WHEN close > 20 THEN 2
            ELSE 1
        END as vix_regime
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Sentiment features
sentiment AS (
    SELECT 
        DATE(timestamp) as date,
        AVG(sentiment_score) as sentiment_avg,
        STDDEV(sentiment_score) as sentiment_std,
        COUNT(*) as sentiment_volume,
        SUM(CASE WHEN LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as china_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%trump%' THEN 1 ELSE 0 END) as trump_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
        AVG(CASE WHEN LOWER(content) LIKE '%china%' THEN sentiment_score END) as china_sentiment,
        AVG(CASE WHEN LOWER(content) LIKE '%trump%' THEN sentiment_score END) as trump_sentiment
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    GROUP BY date
),

-- CFTC positioning (CRITICAL!)
cftc AS (
    SELECT 
        DATE(report_date) as date,
        commercial_long,
        commercial_short,
        commercial_net_position,
        managed_money_long,
        managed_money_short,
        managed_money_net_position,
        open_interest,
        (managed_money_long - managed_money_short) / NULLIF(open_interest, 0) * 100 as spec_net_pct
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
),

-- Economic indicators
economic AS (
    SELECT 
        date,
        MAX(CASE WHEN indicator_name LIKE '%GDP%' THEN value END) as gdp_growth,
        MAX(CASE WHEN indicator_name LIKE '%CPI%' OR indicator_name LIKE '%Inflation%' THEN value END) as inflation_rate,
        MAX(CASE WHEN indicator_name LIKE '%Unemployment%' THEN value END) as unemployment_rate,
        MAX(CASE WHEN indicator_name LIKE '%Fed%' OR indicator_name LIKE '%Interest%' THEN value END) as fed_rate
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY date
),

-- Weather by region
weather AS (
    SELECT 
        date,
        AVG(CASE WHEN LOWER(region) LIKE '%brazil%' THEN temp_max_c END) as brazil_temp,
        SUM(CASE WHEN LOWER(region) LIKE '%brazil%' THEN precipitation_mm END) as brazil_precip,
        AVG(CASE WHEN LOWER(region) LIKE '%argentina%' THEN temp_max_c END) as argentina_temp,
        SUM(CASE WHEN LOWER(region) LIKE '%argentina%' THEN precipitation_mm END) as argentina_precip,
        AVG(CASE WHEN LOWER(region) LIKE '%us%' OR LOWER(region) LIKE '%midwest%' THEN temp_max_c END) as us_temp,
        SUM(CASE WHEN LOWER(region) LIKE '%us%' OR LOWER(region) LIKE '%midwest%' THEN precipitation_mm END) as us_precip
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    GROUP BY date
),

-- Trump policy intelligence
policy AS (
    SELECT 
        DATE(created_at) as date,
        AVG(impact_score) as avg_policy_impact,
        MAX(impact_score) as max_policy_impact,
        COUNT(*) as policy_events
    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
    GROUP BY date
),

-- All shock signals
signals AS (
    SELECT 
        date,
        vix_stress_signal,
        harvest_pace_signal,
        china_relations_signal,
        tariff_threat_signal,
        geopolitical_volatility_signal,
        biofuel_cascade_signal,
        hidden_correlation_signal,
        trade_war_impact_score,
        supply_glut_signal,
        bear_market_signal,
        biofuel_policy_intensity
    FROM `cbi-v14.signals.vw_vix_stress_signal`
    FULL OUTER JOIN `cbi-v14.signals.vw_harvest_pace_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_china_relations_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_tariff_threat_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_geopolitical_volatility_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_cascade_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_hidden_correlation_signal` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_trade_war_impact` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_supply_glut_indicator` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_bear_market_regime` USING(date)
    FULL OUTER JOIN `cbi-v14.signals.vw_biofuel_policy_intensity` USING(date)
),

-- Correlations (30-day rolling)
correlations AS (
    SELECT 
        bp.date,
        CORR(bp.zl_price_current, c.palm_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_palm_corr30,
        CORR(bp.zl_price_current, c.crude_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_crude_corr30,
        CORR(bp.zl_price_current, c.corn_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_corn_corr30,
        CORR(bp.zl_price_current, c.usd_index) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_dxy_corr30
    FROM base_prices bp
    LEFT JOIN commodities c ON bp.date = c.date
),

-- Seasonality
seasonality AS (
    SELECT 
        date,
        EXTRACT(MONTH FROM date) as month,
        EXTRACT(QUARTER FROM date) as quarter,
        EXTRACT(DAYOFWEEK FROM date) as day_of_week,
        CASE WHEN EXTRACT(MONTH FROM date) IN (9,10,11) THEN 1 ELSE 0 END as us_harvest,
        CASE WHEN EXTRACT(MONTH FROM date) IN (2,3,4) THEN 1 ELSE 0 END as brazil_harvest
    FROM base_prices
)

-- FINAL JOIN - ALL FEATURES
SELECT 
    bp.*,
    c.* EXCEPT(date),
    v.* EXCEPT(date),
    s.* EXCEPT(date),
    cf.* EXCEPT(date),
    e.* EXCEPT(date),
    w.* EXCEPT(date),
    p.* EXCEPT(date),
    sg.* EXCEPT(date),
    cr.* EXCEPT(date),
    sn.* EXCEPT(date)
FROM base_prices bp
LEFT JOIN commodities c ON bp.date = c.date
LEFT JOIN vix_data v ON bp.date = v.date
LEFT JOIN sentiment s ON bp.date = s.date
LEFT JOIN cftc cf ON bp.date = cf.date
LEFT JOIN economic e ON bp.date = e.date
LEFT JOIN weather w ON bp.date = w.date
LEFT JOIN policy p ON bp.date = p.date
LEFT JOIN signals sg ON bp.date = sg.date
LEFT JOIN correlations cr ON bp.date = cr.date
LEFT JOIN seasonality sn ON bp.date = sn.date
WHERE bp.date >= '2020-01-01'
AND bp.target_6m IS NOT NULL
"""

print("Creating COMPLETE training dataset with ALL features...")
print("\nIncludes:")
print("  ✓ All commodity prices (soybeans, oil, meal, palm, crude, gas, gold, SP500)")
print("  ✓ VIX and volatility regimes")
print("  ✓ Sentiment analysis (China, Trump, tariff mentions)")
print("  ✓ CFTC positioning data")
print("  ✓ Treasury yields")
print("  ✓ USD index")
print("  ✓ Economic indicators (GDP, inflation, unemployment)")
print("  ✓ Regional weather (Brazil, Argentina, US)")
print("  ✓ Trump policy intelligence")
print("  ✓ All 11 shock signals")
print("  ✓ Cross-asset correlations")
print("  ✓ Seasonality patterns")

try:
    job = client.query(query)
    print(f"\nJob ID: {job.job_id}")
    print("Status: Running...")
    
    result = job.result()
    
    print("\n✓ SUCCESS! Training dataset created!")
    
    # Check results
    check_query = """
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT date) as days,
        MIN(date) as min_date,
        MAX(date) as max_date
    FROM `cbi-v14.models.training_dataset_complete_v2`
    """
    
    stats = client.query(check_query).to_dataframe()
    print(f"\nDataset Statistics:")
    print(f"  Rows: {stats['rows'].iloc[0]:,}")
    print(f"  Days: {stats['days'].iloc[0]:,}")
    print(f"  Date range: {stats['min_date'].iloc[0]} to {stats['max_date'].iloc[0]}")
    
    # Count columns
    col_query = "SELECT * FROM `cbi-v14.models.training_dataset_complete_v2` LIMIT 1"
    cols = client.query(col_query).to_dataframe()
    print(f"  Total features: {len(cols.columns)}")
    
    # List some key features
    key_features = [c for c in cols.columns if any(k in c.lower() for k in 
                    ['cftc', 'vix', 'sentiment', 'trump', 'treasury', 'gdp', 'inflation'])]
    
    print(f"\nKey features included:")
    for feat in key_features[:10]:
        print(f"    ✓ {feat}")
    
    print("\n" + "="*80)
    print("COMPLETE TRAINING DATASET READY!")
    print("="*80)
    print("\nNOW we can train models with ALL the intelligence data!")
    print("No simplified version, no shortcuts, EVERYTHING is included!")
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nDebugging...")
    
    # Check which table is causing issues
    tables_to_check = [
        'soybean_oil_prices', 'crude_oil_prices', 'natural_gas_prices',
        'gold_prices', 'usd_index_prices', 'vix_daily', 'cftc_cot'
    ]
    
    for table in tables_to_check:
        try:
            test_query = f"SELECT * FROM `cbi-v14.forecasting_data_warehouse.{table}` LIMIT 1"
            test_df = client.query(test_query).to_dataframe()
            print(f"  ✓ {table}: {len(test_df.columns)} columns")
        except Exception as e:
            print(f"  ✗ {table}: ERROR - {str(e)[:50]}")
