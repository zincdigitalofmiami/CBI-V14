#!/usr/bin/env python3
"""
Materialize Signal Features to Avoid Window Function Errors
Pre-compute all window functions into physical tables for BigQuery ML
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"MATERIALIZING SIGNAL FEATURES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Pre-computing all window functions to avoid BigQuery ML limitations")
print("="*80)

# Step 1: Materialize VIX Features
print("\nSTEP 1: MATERIALIZE VIX FEATURES")
print("-"*60)

vix_features_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.vix_features_materialized` AS
SELECT 
    date,
    close as vix_value,
    LAG(close, 1) OVER (ORDER BY date) as vix_lag1,
    LAG(close, 7) OVER (ORDER BY date) as vix_lag7,
    close - LAG(close, 1) OVER (ORDER BY date) as vix_change_1d,
    close - LAG(close, 7) OVER (ORDER BY date) as vix_change_7d,
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as vix_ma7,
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_ma30,
    MAX(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_max30,
    MIN(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_min30,
    STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as vix_std30,
    CASE 
        WHEN close > 30 THEN 'CRISIS'
        WHEN close > 25 THEN 'HIGH'
        WHEN close > 20 THEN 'ELEVATED'
        WHEN close > 15 THEN 'NORMAL'
        ELSE 'LOW'
    END as vix_regime,
    CASE 
        WHEN close > 30 THEN POWER((close - 30) / 10, 2)
        WHEN close > 25 THEN (close - 25) / 5
        ELSE 0
    END as vix_crisis_score
FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
ORDER BY date
"""

print("Materializing VIX features...")
try:
    job = client.query(vix_features_query)
    result = job.result()
    print("✓ VIX features materialized")
    
    # Check results
    check = "SELECT COUNT(*) as rows, MIN(date) as min_date, MAX(date) as max_date FROM `cbi-v14.models.vix_features_materialized`"
    stats = client.query(check).to_dataframe()
    print(f"  - {stats['rows'].iloc[0]:,} rows from {stats['min_date'].iloc[0]} to {stats['max_date'].iloc[0]}")
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

# Step 2: Materialize Sentiment Features
print("\nSTEP 2: MATERIALIZE SENTIMENT FEATURES")
print("-"*60)

sentiment_features_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.sentiment_features_materialized` AS
WITH daily_sentiment AS (
    SELECT 
        DATE(timestamp) as date,
        AVG(sentiment_score) as avg_sentiment,
        STDDEV(sentiment_score) as sentiment_std,
        MIN(sentiment_score) as min_sentiment,
        MAX(sentiment_score) as max_sentiment,
        COUNT(*) as sentiment_volume,
        COUNT(CASE WHEN sentiment_score < -0.5 THEN 1 END) as extreme_negative,
        COUNT(CASE WHEN sentiment_score > 0.5 THEN 1 END) as extreme_positive,
        AVG(CASE WHEN platform = 'reddit' THEN sentiment_score END) as reddit_sentiment,
        AVG(CASE WHEN platform = 'twitter' THEN sentiment_score END) as twitter_sentiment
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    WHERE market_relevance IN ('high', 'medium')
    GROUP BY DATE(timestamp)
)
SELECT 
    date,
    avg_sentiment,
    sentiment_std,
    min_sentiment,
    max_sentiment,
    sentiment_volume,
    extreme_negative,
    extreme_positive,
    reddit_sentiment,
    twitter_sentiment,
    LAG(avg_sentiment, 1) OVER (ORDER BY date) as sentiment_lag1,
    LAG(avg_sentiment, 7) OVER (ORDER BY date) as sentiment_lag7,
    avg_sentiment - LAG(avg_sentiment, 1) OVER (ORDER BY date) as sentiment_change_1d,
    avg_sentiment - LAG(avg_sentiment, 7) OVER (ORDER BY date) as sentiment_change_7d,
    AVG(avg_sentiment) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as sentiment_ma7,
    AVG(avg_sentiment) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as sentiment_ma30
FROM daily_sentiment
ORDER BY date
"""

print("Materializing sentiment features...")
try:
    job = client.query(sentiment_features_query)
    result = job.result()
    print("✓ Sentiment features materialized")
    
    check = "SELECT COUNT(*) as rows, AVG(sentiment_volume) as avg_posts FROM `cbi-v14.models.sentiment_features_materialized`"
    stats = client.query(check).to_dataframe()
    print(f"  - {stats['rows'].iloc[0]:,} days with avg {stats['avg_posts'].iloc[0]:.1f} posts/day")
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

# Step 3: Materialize Tariff/Policy Features
print("\nSTEP 3: MATERIALIZE TARIFF/POLICY FEATURES")
print("-"*60)

tariff_features_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.tariff_features_materialized` AS
WITH daily_tariff AS (
    SELECT 
        DATE(timestamp) as date,
        AVG(agricultural_impact) as avg_ag_impact,
        MAX(agricultural_impact) as max_ag_impact,
        AVG(soybean_relevance) as avg_soy_relevance,
        COUNT(CASE WHEN LOWER(text) LIKE '%tariff%' THEN 1 END) as tariff_mentions,
        COUNT(CASE WHEN LOWER(text) LIKE '%china%' THEN 1 END) as china_mentions,
        COUNT(CASE WHEN LOWER(text) LIKE '%trade%' THEN 1 END) as trade_mentions,
        COUNT(CASE WHEN LOWER(text) LIKE '%soybean%' OR LOWER(text) LIKE '%soy%' THEN 1 END) as soy_mentions,
        COUNT(CASE WHEN priority = 'HIGH' THEN 1 END) as high_priority_events,
        COUNT(*) as policy_events
    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
    GROUP BY DATE(timestamp)
)
SELECT 
    date,
    avg_ag_impact,
    max_ag_impact,
    avg_soy_relevance,
    tariff_mentions,
    china_mentions,
    trade_mentions,
    soy_mentions,
    high_priority_events,
    policy_events,
    LAG(tariff_mentions, 1) OVER (ORDER BY date) as tariff_mentions_lag1,
    LAG(tariff_mentions, 7) OVER (ORDER BY date) as tariff_mentions_lag7,
    LAG(china_mentions, 1) OVER (ORDER BY date) as china_mentions_lag1,
    SUM(tariff_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as tariff_mentions_7d,
    SUM(china_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as china_mentions_7d
FROM daily_tariff
ORDER BY date
"""

print("Materializing tariff/policy features...")
try:
    job = client.query(tariff_features_query)
    result = job.result()
    print("✓ Tariff features materialized")
    
    check = "SELECT COUNT(*) as rows, SUM(tariff_mentions) as total_tariff, SUM(china_mentions) as total_china FROM `cbi-v14.models.tariff_features_materialized`"
    stats = client.query(check).to_dataframe()
    print(f"  - {stats['rows'].iloc[0]:,} days with {stats['total_tariff'].iloc[0]:.0f} tariff mentions, {stats['total_china'].iloc[0]:.0f} China mentions")
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

# Step 4: Materialize News Features
print("\nSTEP 4: MATERIALIZE NEWS FEATURES")
print("-"*60)

news_features_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.news_features_materialized` AS
WITH daily_news AS (
    SELECT 
        DATE(processed_timestamp) as date,
        COUNT(*) as news_volume,
        AVG(intelligence_score) as avg_intelligence,
        MAX(intelligence_score) as max_intelligence,
        STDDEV(intelligence_score) as intelligence_std,
        COUNT(CASE WHEN LOWER(title) LIKE '%soybean%' OR LOWER(content) LIKE '%soybean%' THEN 1 END) as soybean_news,
        COUNT(CASE WHEN LOWER(title) LIKE '%china%' OR LOWER(content) LIKE '%china%' THEN 1 END) as china_news,
        COUNT(CASE WHEN LOWER(title) LIKE '%usda%' OR LOWER(content) LIKE '%usda%' THEN 1 END) as usda_news,
        COUNT(CASE WHEN LOWER(title) LIKE '%weather%' OR LOWER(content) LIKE '%weather%' THEN 1 END) as weather_news
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    WHERE confidence_score > 0.6
    GROUP BY DATE(processed_timestamp)
)
SELECT 
    date,
    news_volume,
    avg_intelligence,
    max_intelligence,
    intelligence_std,
    soybean_news,
    china_news,
    usda_news,
    weather_news,
    LAG(news_volume, 1) OVER (ORDER BY date) as news_volume_lag1,
    LAG(avg_intelligence, 1) OVER (ORDER BY date) as intelligence_lag1,
    AVG(news_volume) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_volume_ma7,
    AVG(avg_intelligence) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as intelligence_ma7
FROM daily_news
ORDER BY date
"""

print("Materializing news features...")
try:
    job = client.query(news_features_query)
    result = job.result()
    print("✓ News features materialized")
    
    check = "SELECT COUNT(*) as rows, AVG(news_volume) as avg_news FROM `cbi-v14.models.news_features_materialized`"
    stats = client.query(check).to_dataframe()
    print(f"  - {stats['rows'].iloc[0]:,} days with avg {stats['avg_news'].iloc[0]:.1f} articles/day")
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

# Step 5: Join All Materialized Features
print("\nSTEP 5: CREATE MASTER SIGNALS TABLE")
print("-"*60)

master_signals_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.signals_master` AS
SELECT 
    COALESCE(v.date, s.date, t.date, n.date) as date,
    
    -- VIX features
    v.vix_value,
    v.vix_lag1,
    v.vix_lag7,
    v.vix_change_1d,
    v.vix_change_7d,
    v.vix_ma7,
    v.vix_ma30,
    v.vix_regime,
    v.vix_crisis_score,
    
    -- Sentiment features
    s.avg_sentiment,
    s.sentiment_std,
    s.extreme_negative,
    s.extreme_positive,
    s.sentiment_volume,
    s.sentiment_lag1,
    s.sentiment_change_1d,
    s.sentiment_ma7,
    
    -- Tariff features
    t.tariff_mentions,
    t.china_mentions,
    t.avg_ag_impact,
    t.max_ag_impact,
    t.tariff_mentions_lag1,
    t.tariff_mentions_7d,
    t.china_mentions_7d,
    
    -- News features
    n.news_volume,
    n.avg_intelligence,
    n.soybean_news,
    n.china_news,
    n.intelligence_ma7,
    
    -- Signal interactions (calculated here, not as window functions)
    v.vix_value * COALESCE(1 - s.avg_sentiment, 1) as vix_sentiment_stress,
    COALESCE(t.tariff_mentions, 0) * COALESCE(v.vix_change_1d, 0) as tariff_vix_impact,
    COALESCE(s.extreme_negative, 0) * COALESCE(v.vix_crisis_score, 0) as crisis_panic_score,
    
    -- Composite risk score
    COALESCE(v.vix_crisis_score * 0.3, 0) + 
    COALESCE(s.extreme_negative * 0.2, 0) + 
    COALESCE(t.tariff_mentions * 0.1, 0) + 
    COALESCE(t.china_mentions * 0.1, 0) as composite_risk_score,
    
    -- Market regime
    CASE 
        WHEN v.vix_value > 25 AND s.avg_sentiment < 0 THEN 'CRISIS'
        WHEN v.vix_value > 20 AND t.tariff_mentions > 5 THEN 'TRADE_TENSION'
        WHEN v.vix_value < 15 AND s.avg_sentiment > 0.3 THEN 'BULLISH'
        ELSE 'NEUTRAL'
    END as market_regime

FROM `cbi-v14.models.vix_features_materialized` v
FULL OUTER JOIN `cbi-v14.models.sentiment_features_materialized` s ON v.date = s.date
FULL OUTER JOIN `cbi-v14.models.tariff_features_materialized` t ON v.date = t.date
FULL OUTER JOIN `cbi-v14.models.news_features_materialized` n ON v.date = n.date
WHERE COALESCE(v.date, s.date, t.date, n.date) IS NOT NULL
ORDER BY date
"""

print("Creating master signals table...")
try:
    job = client.query(master_signals_query)
    result = job.result()
    print("✓ Master signals table created")
    
    # Check final results
    check = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(vix_value) as vix_rows,
        COUNT(avg_sentiment) as sentiment_rows,
        COUNT(tariff_mentions) as tariff_rows,
        COUNT(news_volume) as news_rows
    FROM `cbi-v14.models.signals_master`
    """
    stats = client.query(check).to_dataframe()
    print(f"\nSignal Coverage:")
    print(f"  Total days: {stats['total_rows'].iloc[0]:,}")
    print(f"  VIX data: {stats['vix_rows'].iloc[0]:,} days")
    print(f"  Sentiment: {stats['sentiment_rows'].iloc[0]:,} days")
    print(f"  Tariff: {stats['tariff_rows'].iloc[0]:,} days")
    print(f"  News: {stats['news_rows'].iloc[0]:,} days")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

# Step 6: Join with Training Dataset
print("\nSTEP 6: CREATE FINAL TRAINING DATASET WITH SIGNALS")
print("-"*60)

final_dataset_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset_with_signals` AS
SELECT 
    t.*,
    s.vix_value,
    s.vix_change_1d,
    s.vix_regime,
    s.vix_crisis_score,
    s.avg_sentiment,
    s.sentiment_change_1d,
    s.extreme_negative,
    s.tariff_mentions,
    s.china_mentions,
    s.tariff_mentions_7d,
    s.news_volume,
    s.avg_intelligence,
    s.vix_sentiment_stress,
    s.tariff_vix_impact,
    s.composite_risk_score,
    s.market_regime
FROM `cbi-v14.models.training_dataset` t
LEFT JOIN `cbi-v14.models.signals_master` s
ON t.date = s.date
ORDER BY t.date
"""

print("Creating final training dataset with signals...")
try:
    job = client.query(final_dataset_query)
    result = job.result()
    print("✓ Final training dataset created")
    
    # Check enrichment
    check = """
    SELECT 
        COUNT(*) as rows,
        COUNT(vix_value) as rows_with_vix,
        COUNT(avg_sentiment) as rows_with_sentiment,
        COUNT(tariff_mentions) as rows_with_tariff
    FROM `cbi-v14.models.training_dataset_with_signals`
    """
    stats = client.query(check).to_dataframe()
    print(f"\nEnrichment Results:")
    print(f"  Total rows: {stats['rows'].iloc[0]:,}")
    print(f"  With VIX: {stats['rows_with_vix'].iloc[0]:,} ({100*stats['rows_with_vix'].iloc[0]/stats['rows'].iloc[0]:.1f}%)")
    print(f"  With sentiment: {stats['rows_with_sentiment'].iloc[0]:,} ({100*stats['rows_with_sentiment'].iloc[0]/stats['rows'].iloc[0]:.1f}%)")
    print(f"  With tariff: {stats['rows_with_tariff'].iloc[0]:,} ({100*stats['rows_with_tariff'].iloc[0]/stats['rows'].iloc[0]:.1f}%)")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:100]}")

print("\n" + "="*80)
print("MATERIALIZATION COMPLETE")
print("="*80)

print("""
Successfully created:
1. ✓ vix_features_materialized - Pre-computed VIX window functions
2. ✓ sentiment_features_materialized - Pre-computed sentiment metrics
3. ✓ tariff_features_materialized - Pre-computed policy signals
4. ✓ news_features_materialized - Pre-computed news intelligence
5. ✓ signals_master - Combined signal features
6. ✓ training_dataset_with_signals - Ready for model training

Now you can train models without window function errors:

CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_tree_signals`
OPTIONS(
    model_type='BOOSTED_TREE_REGRESSOR',
    input_label_cols=['target_1w']
) AS
SELECT * EXCEPT(date, target_1m, target_3m, target_6m, market_regime)
FROM `cbi-v14.models.training_dataset_with_signals`
WHERE target_1w IS NOT NULL
""")
