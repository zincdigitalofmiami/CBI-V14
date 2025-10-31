#!/usr/bin/env python3
"""
CREATE COMPLETE TRAINING DATASET - FINAL VERSION
Working around broken views, using direct tables
INCLUDING ALL FEATURES - NO SHORTCUTS
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"CREATING COMPLETE TRAINING DATASET FINAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("FULL INSTITUTIONAL GRADE - ALL FEATURES INCLUDED")
print("="*80)

# Final working query with all features
query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_complete_final` AS
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
        -- Price changes
        close - LAG(close, 1) OVER (ORDER BY time) as zl_return_1d,
        close - LAG(close, 7) OVER (ORDER BY time) as zl_return_7d,
        close - LAG(close, 30) OVER (ORDER BY time) as zl_return_30d,
        -- Moving averages
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as zl_ma7,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_ma30,
        AVG(close) OVER (ORDER BY time ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as zl_ma90,
        -- Volatility
        STDDEV(close) OVER (ORDER BY time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_vol30,
        -- RSI components
        AVG(GREATEST(close - LAG(close) OVER (ORDER BY time), 0)) 
            OVER (ORDER BY time ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_gain_14,
        AVG(GREATEST(LAG(close) OVER (ORDER BY time) - close, 0)) 
            OVER (ORDER BY time ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_loss_14,
        -- Targets
        LEAD(close, 7) OVER (ORDER BY time) as target_1w,
        LEAD(close, 30) OVER (ORDER BY time) as target_1m,
        LEAD(close, 90) OVER (ORDER BY time) as target_3m,
        LEAD(close, 180) OVER (ORDER BY time) as target_6m
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
),

-- All commodities with fixed schemas
all_commodities AS (
    SELECT 
        date,
        MAX(soybeans_close) as soybeans_price,
        MAX(soymeal_close) as soymeal_price,
        MAX(palm_close) as palm_oil_price,
        MAX(corn_close) as corn_price,
        MAX(wheat_close) as wheat_price,
        MAX(crude_close) as crude_oil_price,
        MAX(natgas_close) as natural_gas_price,
        MAX(gold_close) as gold_price,
        MAX(sp500_close) as sp500_price,
        MAX(treasury_close) as treasury_yield,
        MAX(usd_close) as usd_index,
        -- Crush spread
        MAX(soymeal_close * 0.022 + soybeans_close * 0.11 - soybeans_close) as crush_margin
    FROM (
        SELECT DATE(time) as date, close as soybeans_close, NULL as soymeal_close, NULL as palm_close,
               NULL as corn_close, NULL as wheat_close, NULL as crude_close, NULL as natgas_close,
               NULL as gold_close, NULL as sp500_close, NULL as treasury_close, NULL as usd_close
        FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
        UNION ALL
        SELECT DATE(time), NULL, close, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.soybean_meal_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, close, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, close, NULL, NULL, NULL, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, close, NULL, NULL, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.wheat_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, close, NULL, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, NULL, close, NULL, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.natural_gas_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, NULL, NULL, close, NULL, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.gold_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, close, NULL, NULL
        FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, close, NULL
        FROM `cbi-v14.forecasting_data_warehouse.treasury_prices`
        UNION ALL
        SELECT DATE(time), NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, close
        FROM `cbi-v14.forecasting_data_warehouse.usd_index_prices`
    )
    GROUP BY date
),

-- VIX regimes (CRITICAL for volatility)
vix_features AS (
    SELECT 
        date,
        close as vix_level,
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as vix_ma7,
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_ma30,
        STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_std30,
        MAX(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_max30,
        CASE 
            WHEN close > 40 THEN 4  -- Panic
            WHEN close > 30 THEN 3  -- High stress
            WHEN close > 20 THEN 2  -- Elevated
            ELSE 1  -- Normal
        END as vix_regime,
        CASE WHEN close > LAG(close) OVER (ORDER BY date) * 1.2 THEN 1 ELSE 0 END as vix_spike
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Sentiment (LEADING INDICATOR)
sentiment_features AS (
    SELECT 
        DATE(timestamp) as date,
        AVG(sentiment_score) as sentiment_avg,
        STDDEV(sentiment_score) as sentiment_std,
        MIN(sentiment_score) as sentiment_min,
        MAX(sentiment_score) as sentiment_max,
        COUNT(*) as sentiment_posts,
        -- Topic analysis
        SUM(CASE WHEN LOWER(content) LIKE '%china%' THEN 1 ELSE 0 END) as china_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%trump%' THEN 1 ELSE 0 END) as trump_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%harvest%' THEN 1 ELSE 0 END) as harvest_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%drought%' THEN 1 ELSE 0 END) as drought_mentions,
        SUM(CASE WHEN LOWER(content) LIKE '%biofuel%' THEN 1 ELSE 0 END) as biofuel_mentions,
        -- Sentiment by topic
        AVG(CASE WHEN LOWER(content) LIKE '%china%' THEN sentiment_score END) as china_sentiment,
        AVG(CASE WHEN LOWER(content) LIKE '%trump%' THEN sentiment_score END) as trump_sentiment,
        AVG(CASE WHEN LOWER(content) LIKE '%weather%' OR LOWER(content) LIKE '%drought%' 
            THEN sentiment_score END) as weather_sentiment
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    GROUP BY date
),

-- CFTC Positioning (TURNING POINTS)
cftc_features AS (
    SELECT 
        DATE(report_date) as date,
        commercial_long,
        commercial_short,
        commercial_net_position,
        managed_money_long,
        managed_money_short,
        managed_money_net_position,
        open_interest,
        -- Positioning metrics
        (managed_money_long - managed_money_short) / NULLIF(open_interest, 0) * 100 as spec_net_pct,
        (commercial_long - commercial_short) / NULLIF(open_interest, 0) * 100 as comm_net_pct,
        managed_money_long / NULLIF(managed_money_long + managed_money_short, 0) as spec_long_ratio
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
),

-- Economic indicators
economic_features AS (
    SELECT 
        date,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%gdp%' THEN value END) as gdp_growth,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%cpi%' OR LOWER(indicator_name) LIKE '%inflation%' 
            THEN value END) as inflation_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%unemployment%' THEN value END) as unemployment_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%fed%' OR LOWER(indicator_name) LIKE '%interest%' 
            THEN value END) as fed_funds_rate,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%retail%' THEN value END) as retail_sales,
        MAX(CASE WHEN LOWER(indicator_name) LIKE '%pmi%' OR LOWER(indicator_name) LIKE '%manufacturing%' 
            THEN value END) as pmi_index
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    GROUP BY date
),

-- Weather by region (PRODUCTION IMPACT)
weather_features AS (
    SELECT 
        date,
        -- Brazil (largest exporter)
        AVG(CASE WHEN LOWER(region) LIKE '%brazil%' THEN temp_max_c END) as brazil_temp_max,
        AVG(CASE WHEN LOWER(region) LIKE '%brazil%' THEN temp_min_c END) as brazil_temp_min,
        SUM(CASE WHEN LOWER(region) LIKE '%brazil%' THEN precipitation_mm END) as brazil_precip,
        AVG(CASE WHEN LOWER(region) LIKE '%brazil%' THEN gdd END) as brazil_gdd,
        -- Argentina
        AVG(CASE WHEN LOWER(region) LIKE '%argentina%' THEN temp_max_c END) as argentina_temp_max,
        SUM(CASE WHEN LOWER(region) LIKE '%argentina%' THEN precipitation_mm END) as argentina_precip,
        -- US Midwest
        AVG(CASE WHEN LOWER(region) LIKE '%us%' OR LOWER(region) LIKE '%midwest%' 
            THEN temp_max_c END) as us_temp_max,
        SUM(CASE WHEN LOWER(region) LIKE '%us%' OR LOWER(region) LIKE '%midwest%' 
            THEN precipitation_mm END) as us_precip,
        AVG(CASE WHEN LOWER(region) LIKE '%us%' OR LOWER(region) LIKE '%midwest%' 
            THEN gdd END) as us_gdd
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    GROUP BY date
),

-- Trump/Policy intelligence
policy_features AS (
    SELECT 
        DATE(created_at) as date,
        AVG(impact_score) as policy_impact_avg,
        MAX(impact_score) as policy_impact_max,
        STDDEV(impact_score) as policy_impact_std,
        COUNT(*) as policy_event_count,
        SUM(CASE WHEN LOWER(policy_type) LIKE '%tariff%' THEN 1 ELSE 0 END) as tariff_policy_count,
        SUM(CASE WHEN LOWER(policy_type) LIKE '%trade%' THEN 1 ELSE 0 END) as trade_policy_count,
        MAX(CASE WHEN LOWER(policy_type) LIKE '%tariff%' THEN impact_score ELSE 0 END) as max_tariff_impact
    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
    GROUP BY date
),

-- Cross-asset correlations (SUBSTITUTION EFFECTS)
correlation_features AS (
    SELECT 
        bp.date,
        -- 30-day correlations
        CORR(bp.zl_price_current, ac.palm_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_palm_corr_30d,
        CORR(bp.zl_price_current, ac.crude_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_crude_corr_30d,
        CORR(bp.zl_price_current, ac.corn_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_corn_corr_30d,
        CORR(bp.zl_price_current, ac.wheat_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_wheat_corr_30d,
        CORR(bp.zl_price_current, ac.usd_index) OVER (
            ORDER BY bp.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as soy_dxy_corr_30d,
        -- 90-day correlations
        CORR(bp.zl_price_current, ac.palm_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as soy_palm_corr_90d,
        CORR(bp.zl_price_current, ac.crude_oil_price) OVER (
            ORDER BY bp.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) as soy_crude_corr_90d
    FROM base_prices bp
    LEFT JOIN all_commodities ac ON bp.date = ac.date
),

-- Seasonality patterns
seasonality_features AS (
    SELECT 
        date,
        EXTRACT(MONTH FROM date) as month,
        EXTRACT(QUARTER FROM date) as quarter,
        EXTRACT(DAYOFWEEK FROM date) as day_of_week,
        EXTRACT(WEEK FROM date) as week_of_year,
        EXTRACT(DAYOFYEAR FROM date) as day_of_year,
        -- Seasonal flags
        CASE WHEN EXTRACT(MONTH FROM date) IN (9,10,11) THEN 1 ELSE 0 END as us_harvest_season,
        CASE WHEN EXTRACT(MONTH FROM date) IN (2,3,4) THEN 1 ELSE 0 END as brazil_harvest_season,
        CASE WHEN EXTRACT(MONTH FROM date) IN (4,5,6) THEN 1 ELSE 0 END as argentina_harvest_season,
        CASE WHEN EXTRACT(MONTH FROM date) IN (4,5,6,7,8,9) THEN 1 ELSE 0 END as planting_season,
        -- Trading patterns
        CASE WHEN EXTRACT(DAYOFWEEK FROM date) = 2 THEN 1 ELSE 0 END as monday,
        CASE WHEN EXTRACT(DAYOFWEEK FROM date) = 6 THEN 1 ELSE 0 END as friday,
        CASE WHEN EXTRACT(DAY FROM date) <= 7 THEN 1 ELSE 0 END as month_start,
        CASE WHEN EXTRACT(DAY FROM date) >= 24 THEN 1 ELSE 0 END as month_end
    FROM base_prices
)

-- FINAL COMPREHENSIVE JOIN
SELECT 
    bp.*,
    ac.* EXCEPT(date),
    vf.* EXCEPT(date),
    sf.* EXCEPT(date),
    cf.* EXCEPT(date),
    ef.* EXCEPT(date),
    wf.* EXCEPT(date),
    pf.* EXCEPT(date),
    crf.* EXCEPT(date),
    snf.* EXCEPT(date)
FROM base_prices bp
LEFT JOIN all_commodities ac ON bp.date = ac.date
LEFT JOIN vix_features vf ON bp.date = vf.date
LEFT JOIN sentiment_features sf ON bp.date = sf.date
LEFT JOIN cftc_features cf ON bp.date = cf.date
LEFT JOIN economic_features ef ON bp.date = ef.date
LEFT JOIN weather_features wf ON bp.date = wf.date
LEFT JOIN policy_features pf ON bp.date = pf.date
LEFT JOIN correlation_features crf ON bp.date = crf.date
LEFT JOIN seasonality_features snf ON bp.date = snf.date
WHERE bp.date >= '2020-01-01'
AND bp.target_6m IS NOT NULL
"""

print("Creating FINAL COMPLETE training dataset...")
print("\nThis includes EVERYTHING:")
print("  ✓ Soybean oil prices with technical indicators")
print("  ✓ ALL commodities (beans, meal, palm, crude, gas, gold, etc.)")
print("  ✓ VIX levels and volatility regimes")
print("  ✓ Sentiment analysis with topic breakdown")
print("  ✓ CFTC positioning data (specs vs commercials)")
print("  ✓ Economic indicators (GDP, inflation, unemployment, fed rates)")
print("  ✓ Regional weather (Brazil, Argentina, US)")
print("  ✓ Trump policy intelligence and impacts")
print("  ✓ Cross-asset correlations (30 and 90 day)")
print("  ✓ Seasonality and trading patterns")
print("  ✓ Crush margins")

try:
    job = client.query(query)
    print(f"\nJob ID: {job.job_id}")
    print("Running...")
    
    result = job.result()
    
    print("\n" + "="*80)
    print("✓ SUCCESS! COMPLETE TRAINING DATASET CREATED!")
    print("="*80)
    
    # Verify results
    verify_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_days,
        MIN(date) as start_date,
        MAX(date) as end_date
    FROM `cbi-v14.models.training_dataset_complete_final`
    """
    
    stats = client.query(verify_query).to_dataframe()
    print(f"\nDataset Statistics:")
    print(f"  Total rows: {stats['total_rows'].iloc[0]:,}")
    print(f"  Unique days: {stats['unique_days'].iloc[0]:,}")
    print(f"  Date range: {stats['start_date'].iloc[0]} to {stats['end_date'].iloc[0]}")
    
    # Count features
    feature_query = "SELECT * FROM `cbi-v14.models.training_dataset_complete_final` LIMIT 1"
    features = client.query(feature_query).to_dataframe()
    
    print(f"  Total features: {len(features.columns)}")
    
    # Show key features
    print(f"\nKey feature categories included:")
    
    price_features = [c for c in features.columns if 'price' in c.lower() or 'close' in c.lower()]
    print(f"  Price features: {len(price_features)}")
    
    sentiment_features = [c for c in features.columns if 'sentiment' in c.lower() or 'mentions' in c.lower()]
    print(f"  Sentiment features: {len(sentiment_features)}")
    
    cftc_features = [c for c in features.columns if 'commercial' in c.lower() or 'managed' in c.lower() or 'spec' in c.lower()]
    print(f"  CFTC features: {len(cftc_features)}")
    
    weather_features = [c for c in features.columns if 'temp' in c.lower() or 'precip' in c.lower() or 'gdd' in c.lower()]
    print(f"  Weather features: {len(weather_features)}")
    
    vix_features = [c for c in features.columns if 'vix' in c.lower()]
    print(f"  VIX features: {len(vix_features)}")
    
    corr_features = [c for c in features.columns if 'corr' in c.lower()]
    print(f"  Correlation features: {len(corr_features)}")
    
    economic_features = [c for c in features.columns if any(e in c.lower() for e in ['gdp', 'inflation', 'unemployment', 'fed', 'pmi'])]
    print(f"  Economic features: {len(economic_features)}")
    
    policy_features = [c for c in features.columns if 'policy' in c.lower() or 'tariff' in c.lower()]
    print(f"  Policy features: {len(policy_features)}")
    
    print("\n" + "="*80)
    print("TRAINING DATASET IS NOW COMPLETE WITH ALL FEATURES!")
    print("="*80)
    print("\nThis is the FULL institutional-grade dataset with:")
    print("- ALL commodity prices")
    print("- ALL market intelligence")
    print("- ALL positioning data")
    print("- ALL weather regions")
    print("- ALL policy impacts")
    print("- ALL correlations calculated")
    print("\nNO SIMPLIFIED VERSION - THIS IS THE REAL DEAL!")
    
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nThis shouldn't happen after fixing schemas...")
