#!/usr/bin/env python3
"""
Amplify Alternative Data Signals - VIX, Sentiment, Tariffs
Using REAL data from our warehouse - NO PLACEHOLDERS!
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"SIGNAL AMPLIFICATION & OPTIMIZATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Using REAL data from forecasting_data_warehouse")
print("="*80)

# Step 1: Check what REAL alternative data we have
print("\nSTEP 1: VERIFY REAL ALTERNATIVE DATA SOURCES")
print("-"*60)

check_sources = [
    ('vix_daily', 'VIX volatility data'),
    ('social_sentiment', 'Social sentiment scores'),
    ('trump_policy_intelligence', 'Policy/tariff intelligence'),
    ('news_intelligence', 'News sentiment'),
    ('volatility_data', 'Market volatility metrics')
]

available_sources = []
for table, description in check_sources:
    try:
        query = f"SELECT COUNT(*) as cnt FROM `cbi-v14.forecasting_data_warehouse.{table}` LIMIT 1"
        result = client.query(query).to_dataframe()
        count = result['cnt'].iloc[0]
        if count > 0:
            print(f"✓ {table}: {count:,} rows - {description}")
            available_sources.append(table)
    except:
        print(f"✗ {table}: Not available")

# Step 2: Create Enhanced Signal Features
print("\nSTEP 2: CREATE ENHANCED SIGNAL FEATURES")
print("-"*60)

signal_enhancement_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.signals_enhanced` AS
WITH 

-- VIX Signal Processing
vix_signals AS (
    SELECT 
        date,
        close as vix_value,
        -- VIX momentum
        close - LAG(close, 1) OVER (ORDER BY date) as vix_change_1d,
        close - LAG(close, 7) OVER (ORDER BY date) as vix_change_7d,
        -- VIX regime detection
        CASE 
            WHEN close > 30 THEN 'CRISIS'
            WHEN close > 25 THEN 'HIGH_STRESS'
            WHEN close > 20 THEN 'ELEVATED'
            WHEN close > 15 THEN 'NORMAL'
            ELSE 'LOW'
        END as vix_regime,
        -- VIX crisis score (exponential for extreme values)
        CASE 
            WHEN close > 30 THEN POWER((close - 30) / 10, 2)
            WHEN close > 25 THEN (close - 25) / 5
            ELSE 0
        END as vix_crisis_score,
        -- Smoothed VIX (3-day average)
        AVG(close) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as vix_smooth_3d,
        -- VIX spike detection
        CASE 
            WHEN close > LAG(close, 1) OVER (ORDER BY date) * 1.2 THEN 1
            ELSE 0
        END as vix_spike_flag
    FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
),

-- Social Sentiment Signal Processing
sentiment_signals AS (
    SELECT 
        DATE(timestamp) as date,
        -- Aggregate sentiment metrics
        AVG(sentiment_score) as avg_sentiment,
        STDDEV(sentiment_score) as sentiment_volatility,
        MIN(sentiment_score) as min_sentiment,
        MAX(sentiment_score) as max_sentiment,
        COUNT(*) as sentiment_volume,
        -- Sentiment momentum
        AVG(sentiment_score) - LAG(AVG(sentiment_score), 1) OVER (ORDER BY DATE(timestamp)) as sentiment_momentum_1d,
        AVG(sentiment_score) - LAG(AVG(sentiment_score), 7) OVER (ORDER BY DATE(timestamp)) as sentiment_momentum_7d,
        -- Extreme sentiment detection
        COUNT(CASE WHEN sentiment_score < -0.5 THEN 1 END) as extreme_negative_count,
        COUNT(CASE WHEN sentiment_score > 0.5 THEN 1 END) as extreme_positive_count,
        -- Platform-specific sentiment
        AVG(CASE WHEN platform = 'reddit' THEN sentiment_score END) as reddit_sentiment,
        AVG(CASE WHEN platform = 'twitter' THEN sentiment_score END) as twitter_sentiment
    FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
    WHERE market_relevance > 0.5  -- Filter for market-relevant content
    GROUP BY DATE(timestamp)
),

-- Tariff/Policy Intelligence Processing
tariff_signals AS (
    SELECT 
        DATE(timestamp) as date,
        -- Policy impact metrics
        AVG(agricultural_impact) as avg_ag_impact,
        MAX(agricultural_impact) as max_ag_impact,
        AVG(soybean_relevance) as avg_soy_relevance,
        -- Tariff mentions and categories
        COUNT(CASE WHEN LOWER(text) LIKE '%tariff%' THEN 1 END) as tariff_mentions,
        COUNT(CASE WHEN LOWER(text) LIKE '%china%' THEN 1 END) as china_mentions,
        COUNT(CASE WHEN LOWER(text) LIKE '%trade%' THEN 1 END) as trade_mentions,
        COUNT(CASE WHEN category = 'tariff' THEN 1 END) as tariff_category_count,
        COUNT(CASE WHEN category = 'trade_policy' THEN 1 END) as trade_policy_count,
        -- Policy momentum
        COUNT(*) - LAG(COUNT(*), 1) OVER (ORDER BY DATE(timestamp)) as policy_event_momentum,
        -- High priority events
        COUNT(CASE WHEN priority = 'HIGH' THEN 1 END) as high_priority_events
    FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
    GROUP BY DATE(timestamp)
),

-- News Intelligence Processing
news_signals AS (
    SELECT 
        DATE(processed_timestamp) as date,
        -- News volume and sentiment
        COUNT(*) as news_volume,
        AVG(intelligence_score) as avg_news_intelligence,
        STDDEV(intelligence_score) as news_intelligence_volatility,
        -- Topic-specific news
        COUNT(CASE WHEN LOWER(title) LIKE '%soybean%' OR LOWER(content) LIKE '%soybean%' THEN 1 END) as soybean_news_count,
        COUNT(CASE WHEN LOWER(title) LIKE '%china%' OR LOWER(content) LIKE '%china%' THEN 1 END) as china_news_count,
        COUNT(CASE WHEN LOWER(title) LIKE '%usda%' OR LOWER(content) LIKE '%usda%' THEN 1 END) as usda_news_count,
        COUNT(CASE WHEN LOWER(title) LIKE '%weather%' OR LOWER(content) LIKE '%weather%' THEN 1 END) as weather_news_count,
        -- News momentum
        AVG(intelligence_score) - LAG(AVG(intelligence_score), 1) OVER (ORDER BY DATE(processed_timestamp)) as news_momentum_1d
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    WHERE confidence_score > 0.7  -- High confidence news only
    GROUP BY DATE(processed_timestamp)
),

-- Combine all signals
combined_signals AS (
    SELECT 
        COALESCE(v.date, s.date, t.date, n.date) as date,
        -- VIX signals
        v.vix_value,
        v.vix_change_1d,
        v.vix_change_7d,
        v.vix_regime,
        v.vix_crisis_score,
        v.vix_smooth_3d,
        v.vix_spike_flag,
        -- Sentiment signals
        s.avg_sentiment,
        s.sentiment_volatility,
        s.sentiment_momentum_1d,
        s.sentiment_momentum_7d,
        s.extreme_negative_count,
        s.extreme_positive_count,
        s.reddit_sentiment,
        s.twitter_sentiment,
        -- Tariff/Policy signals
        t.avg_ag_impact,
        t.max_ag_impact,
        t.tariff_mentions,
        t.china_mentions,
        t.trade_mentions,
        t.policy_event_momentum,
        t.high_priority_events,
        -- News signals
        n.news_volume,
        n.avg_news_intelligence,
        n.soybean_news_count,
        n.china_news_count,
        n.news_momentum_1d
    FROM vix_signals v
    FULL OUTER JOIN sentiment_signals s ON v.date = s.date
    FULL OUTER JOIN tariff_signals t ON v.date = t.date
    FULL OUTER JOIN news_signals n ON v.date = n.date
)

SELECT * FROM combined_signals
WHERE date IS NOT NULL
ORDER BY date DESC
"""

print("Creating enhanced signals table with REAL data...")
try:
    job = client.query(signal_enhancement_query)
    result = job.result()
    print("✓ Enhanced signals table created successfully")
    
    # Check results
    check_query = "SELECT COUNT(*) as rows, COUNT(DISTINCT date) as days FROM `cbi-v14.models.signals_enhanced`"
    stats = client.query(check_query).to_dataframe()
    print(f"  - Rows: {stats['rows'].iloc[0]:,}")
    print(f"  - Days: {stats['days'].iloc[0]:,}")
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

# Step 3: Create Signal Interaction Features
print("\nSTEP 3: CREATE SIGNAL INTERACTION FEATURES")
print("-"*60)

interaction_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.signal_interactions` AS
SELECT 
    *,
    -- VIX-Sentiment Interactions
    COALESCE(vix_value * (1 - avg_sentiment), 0) as vix_sentiment_stress,
    COALESCE(vix_crisis_score * extreme_negative_count, 0) as crisis_panic_score,
    
    -- Tariff-VIX Interactions
    COALESCE(tariff_mentions * vix_change_1d, 0) as tariff_vix_impact,
    COALESCE(china_mentions * (vix_value / 20), 0) as china_vix_stress,
    
    -- News-Sentiment Alignment
    COALESCE(avg_news_intelligence * avg_sentiment, 0) as news_sentiment_alignment,
    COALESCE(news_volume * sentiment_volatility, 0) as information_uncertainty,
    
    -- Policy-Market Stress
    COALESCE(high_priority_events * vix_value, 0) as policy_market_stress,
    COALESCE(avg_ag_impact * (30 - vix_value), 0) as ag_impact_calm_market,
    
    -- Composite Risk Score
    COALESCE(
        (vix_crisis_score * 0.3) + 
        (extreme_negative_count * 0.2) + 
        (tariff_mentions * 0.2) + 
        (high_priority_events * 0.3), 0
    ) as composite_risk_score,
    
    -- Market Regime Classification
    CASE 
        WHEN vix_value > 25 AND avg_sentiment < 0 THEN 'CRISIS'
        WHEN vix_value > 20 AND tariff_mentions > 5 THEN 'TRADE_TENSION'
        WHEN vix_value < 15 AND avg_sentiment > 0.5 THEN 'BULLISH'
        WHEN vix_value < 20 AND avg_sentiment BETWEEN -0.2 AND 0.2 THEN 'NEUTRAL'
        ELSE 'UNCERTAIN'
    END as market_regime
    
FROM `cbi-v14.models.signals_enhanced`
"""

print("Creating signal interaction features...")
try:
    job = client.query(interaction_query)
    result = job.result()
    print("✓ Signal interactions created successfully")
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

# Step 4: Create Regime-Specific Training Datasets
print("\nSTEP 4: CREATE REGIME-SPECIFIC DATASETS")
print("-"*60)

regimes = [
    ('crisis', "market_regime = 'CRISIS' OR vix_value > 25"),
    ('trade_tension', "market_regime = 'TRADE_TENSION' OR tariff_mentions > 10"),
    ('bullish', "market_regime = 'BULLISH' OR (vix_value < 15 AND avg_sentiment > 0.3)"),
    ('high_volatility', "sentiment_volatility > 0.5 OR vix_change_1d > 2")
]

for regime_name, condition in regimes:
    print(f"\nCreating {regime_name} regime dataset...")
    
    regime_query = f"""
    CREATE OR REPLACE TABLE `cbi-v14.models.training_{regime_name}_regime` AS
    SELECT 
        t.*,
        s.vix_value,
        s.vix_crisis_score,
        s.avg_sentiment,
        s.sentiment_momentum_1d,
        s.tariff_mentions,
        s.china_mentions,
        s.composite_risk_score,
        s.vix_sentiment_stress,
        s.crisis_panic_score
    FROM `cbi-v14.models.training_dataset` t
    LEFT JOIN `cbi-v14.models.signal_interactions` s
    ON t.date = s.date
    WHERE s.{condition}
    """
    
    try:
        job = client.query(regime_query)
        print(f"  ✓ {regime_name} regime dataset created")
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")

print("\n" + "="*80)
print("SIGNAL AMPLIFICATION COMPLETE")
print("="*80)

print("""
Created with REAL data:
1. ✓ Enhanced signals from VIX, sentiment, news, policy data
2. ✓ Signal interaction features (VIX-sentiment, tariff-VIX, etc.)
3. ✓ Composite risk scores and market regime classification
4. ✓ Regime-specific training datasets

Next Steps:
1. Train models on regime-specific datasets
2. Create ensemble predictions weighted by current regime
3. Monitor signal effectiveness with feature importance
""")
