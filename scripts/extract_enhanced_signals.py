#!/usr/bin/env python3
"""
EXTRACT ENHANCED SIGNALS FROM EXISTING DATA
Mining social sentiment data for policy, tariff, labor, and market signals
Working around government shutdown constraints
"""

from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print(f"ENHANCED SIGNAL EXTRACTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print("Extracting maximum value from existing social sentiment data")
print("="*80)

# STEP 1: Enhanced Policy Features from Social Data
print("\nSTEP 1: EXTRACT POLICY SIGNALS FROM SOCIAL DATA")
print("-"*60)

enhanced_policy_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.enhanced_policy_features` AS
SELECT
  DATE(timestamp) AS date,
  
  -- Tariff and Trade War Signals
  COUNT(CASE WHEN LOWER(title) LIKE '%tariff%' OR LOWER(content) LIKE '%tariff%' 
             OR LOWER(title) LIKE '%trade war%' OR LOWER(content) LIKE '%trade war%' THEN 1 END) AS tariff_mentions,
  
  -- ICE and Immigration Enforcement
  COUNT(CASE WHEN (LOWER(title) LIKE '%ice%' OR LOWER(content) LIKE '%ice%') 
             AND (LOWER(title) LIKE '%enforcement%' OR LOWER(content) LIKE '%enforcement%'
                  OR LOWER(title) LIKE '%immigration%' OR LOWER(content) LIKE '%immigration%') THEN 1 END) AS ice_mentions,
  
  -- Labor and Farming Workers
  COUNT(CASE WHEN LOWER(title) LIKE '%labor%' OR LOWER(content) LIKE '%labor%'
             OR LOWER(title) LIKE '%worker%' OR LOWER(content) LIKE '%worker%'
             OR LOWER(title) LIKE '%farm labor%' OR LOWER(content) LIKE '%farm labor%'
             OR LOWER(title) LIKE '%harvest crew%' OR LOWER(content) LIKE '%harvest crew%' THEN 1 END) AS labor_mentions,
  
  -- Trump Orders and Executive Actions
  COUNT(CASE WHEN (LOWER(title) LIKE '%trump%' OR LOWER(content) LIKE '%trump%')
             AND (LOWER(title) LIKE '%order%' OR LOWER(content) LIKE '%order%'
                  OR LOWER(title) LIKE '%executive%' OR LOWER(content) LIKE '%executive%'
                  OR LOWER(title) LIKE '%announce%' OR LOWER(content) LIKE '%announce%') THEN 1 END) AS trump_order_mentions,
  
  -- China-specific mentions
  COUNT(CASE WHEN LOWER(title) LIKE '%china%' OR LOWER(content) LIKE '%china%'
             OR LOWER(title) LIKE '%chinese%' OR LOWER(content) LIKE '%chinese%'
             OR LOWER(title) LIKE '%beijing%' OR LOWER(content) LIKE '%beijing%' THEN 1 END) AS china_mentions,
  
  -- Sentiment Analysis per Category
  AVG(CASE WHEN LOWER(title) LIKE '%tariff%' OR LOWER(content) LIKE '%tariff%' 
           THEN sentiment_score END) AS tariff_sentiment,
  AVG(CASE WHEN LOWER(title) LIKE '%trump%' OR LOWER(content) LIKE '%trump%' 
           THEN sentiment_score END) AS trump_sentiment,
  AVG(CASE WHEN LOWER(title) LIKE '%china%' OR LOWER(content) LIKE '%china%' 
           THEN sentiment_score END) AS china_sentiment,
  AVG(CASE WHEN LOWER(title) LIKE '%labor%' OR LOWER(content) LIKE '%labor%' 
           THEN sentiment_score END) AS labor_sentiment,
  
  -- Volume and Engagement Metrics
  SUM(score) AS total_engagement_score,
  SUM(comments) AS total_comments,
  COUNT(*) AS total_posts,
  AVG(sentiment_score) AS avg_daily_sentiment
  
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
GROUP BY date
ORDER BY date
"""

print("Creating enhanced policy features table...")
try:
    job = client.query(enhanced_policy_query)
    result = job.result()
    print("✓ Enhanced policy features created")
    
    # Check results
    check = """
    SELECT 
        COUNT(*) as days,
        SUM(tariff_mentions) as total_tariff,
        SUM(ice_mentions) as total_ice,
        SUM(labor_mentions) as total_labor,
        SUM(trump_order_mentions) as total_trump,
        SUM(china_mentions) as total_china
    FROM `cbi-v14.models.enhanced_policy_features`
    """
    stats = client.query(check).to_dataframe()
    print(f"  Days: {stats['days'].iloc[0]:,}")
    print(f"  Tariff mentions: {stats['total_tariff'].iloc[0]:,.0f}")
    print(f"  ICE mentions: {stats['total_ice'].iloc[0]:,.0f}")
    print(f"  Labor mentions: {stats['total_labor'].iloc[0]:,.0f}")
    print(f"  Trump mentions: {stats['total_trump'].iloc[0]:,.0f}")
    print(f"  China mentions: {stats['total_china'].iloc[0]:,.0f}")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

# STEP 2: Enhanced News Categories from Social Data
print("\nSTEP 2: CREATE NEWS PROXY FROM SOCIAL DATA")
print("-"*60)

news_proxy_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.enhanced_news_proxy` AS
WITH social_news AS (
  SELECT
    DATE(timestamp) AS date,
    title,
    COALESCE(title, '') || ' ' || COALESCE(subreddit, '') AS content,
    sentiment_score,
    score,
    comments,
    CASE
      WHEN LOWER(title) LIKE '%soybean%' OR LOWER(title) LIKE '%soy bean%' 
           OR LOWER(title) LIKE '%soy oil%' THEN 'SOYBEAN'
      WHEN LOWER(title) LIKE '%oil price%' OR LOWER(title) LIKE '%crude%' 
           OR LOWER(title) LIKE '%petroleum%' THEN 'OIL'
      WHEN LOWER(title) LIKE '%tariff%' OR LOWER(title) LIKE '%trade war%' 
           OR LOWER(title) LIKE '%trade deal%' THEN 'TRADE'
      WHEN LOWER(title) LIKE '%weather%' OR LOWER(title) LIKE '%drought%' 
           OR LOWER(title) LIKE '%rain%' OR LOWER(title) LIKE '%flood%' THEN 'WEATHER'
      WHEN LOWER(title) LIKE '%harvest%' OR LOWER(title) LIKE '%crop%' 
           OR LOWER(title) LIKE '%yield%' OR LOWER(title) LIKE '%planting%' THEN 'HARVEST'
      WHEN LOWER(title) LIKE '%usda%' OR LOWER(title) LIKE '%wasde%' 
           OR LOWER(title) LIKE '%report%' THEN 'USDA'
      WHEN LOWER(title) LIKE '%export%' OR LOWER(title) LIKE '%import%' 
           OR LOWER(title) LIKE '%shipment%' THEN 'EXPORT'
      ELSE 'OTHER'
    END AS news_category,
    market_relevance
  FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
)
SELECT
  date,
  -- Total counts
  COUNT(*) AS total_news_proxy,
  
  -- Category-specific counts
  COUNT(CASE WHEN news_category = 'SOYBEAN' THEN 1 END) AS soybean_news,
  COUNT(CASE WHEN news_category = 'OIL' THEN 1 END) AS oil_news,
  COUNT(CASE WHEN news_category = 'TRADE' THEN 1 END) AS trade_news,
  COUNT(CASE WHEN news_category = 'WEATHER' THEN 1 END) AS weather_news,
  COUNT(CASE WHEN news_category = 'HARVEST' THEN 1 END) AS harvest_news,
  COUNT(CASE WHEN news_category = 'USDA' THEN 1 END) AS usda_news,
  COUNT(CASE WHEN news_category = 'EXPORT' THEN 1 END) AS export_news,
  
  -- Category-specific sentiment
  AVG(sentiment_score) AS avg_news_sentiment,
  AVG(CASE WHEN news_category = 'SOYBEAN' THEN sentiment_score END) AS soybean_sentiment,
  AVG(CASE WHEN news_category = 'TRADE' THEN sentiment_score END) AS trade_sentiment,
  AVG(CASE WHEN news_category = 'WEATHER' THEN sentiment_score END) AS weather_sentiment,
  
  -- Engagement metrics as proxy for importance
  SUM(score + comments) AS total_engagement,
  MAX(score) AS max_post_score,
  
  -- Market relevance
  COUNT(CASE WHEN market_relevance = 'high' THEN 1 END) AS high_relevance_count
  
FROM social_news
GROUP BY date
ORDER BY date
"""

print("Creating enhanced news proxy from social data...")
try:
    job = client.query(news_proxy_query)
    result = job.result()
    print("✓ News proxy features created")
    
    # Check coverage
    check = """
    SELECT 
        COUNT(*) as days,
        AVG(total_news_proxy) as avg_posts_per_day,
        SUM(soybean_news) as total_soybean,
        SUM(trade_news) as total_trade,
        SUM(weather_news) as total_weather
    FROM `cbi-v14.models.enhanced_news_proxy`
    """
    stats = client.query(check).to_dataframe()
    print(f"  Days with data: {stats['days'].iloc[0]:,}")
    print(f"  Avg posts/day: {stats['avg_posts_per_day'].iloc[0]:.1f}")
    print(f"  Soybean news: {stats['total_soybean'].iloc[0]:,.0f}")
    print(f"  Trade news: {stats['total_trade'].iloc[0]:,.0f}")
    print(f"  Weather news: {stats['total_weather'].iloc[0]:,.0f}")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

# STEP 3: Enhanced Market Regimes
print("\nSTEP 3: CREATE DETAILED MARKET REGIMES")
print("-"*60)

market_regime_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.enhanced_market_regimes` AS
WITH price_metrics AS (
  SELECT
    date,
    zl_price_current,
    (zl_price_current - zl_price_lag30) / NULLIF(zl_price_lag30, 0) AS return_30d,
    volatility_30d
  FROM `cbi-v14.models.training_dataset`
)
SELECT
  s.date,
  
  -- Define detailed market regime
  CASE
    WHEN s.vix_value > 30 THEN 'CRISIS'
    WHEN s.vix_value > 25 THEN 'HIGH_VOLATILITY'
    WHEN p.return_30d > 0.10 THEN 'BULLISH_TREND'
    WHEN p.return_30d < -0.10 THEN 'BEARISH_TREND'
    WHEN s.tariff_mentions > 10 THEN 'TRADE_TENSION'
    WHEN s.extreme_negative > 10 THEN 'NEGATIVE_SENTIMENT'
    WHEN s.extreme_positive > 10 THEN 'POSITIVE_SENTIMENT'
    WHEN p.volatility_30d > 2 THEN 'VOLATILE_NEUTRAL'
    ELSE 'NEUTRAL'
  END AS detailed_regime,
  
  -- Regime confidence score
  CASE
    WHEN s.vix_value > 30 THEN 1.0
    WHEN s.vix_value > 25 THEN 0.9
    WHEN ABS(p.return_30d) > 0.10 THEN 0.8
    WHEN s.tariff_mentions > 10 THEN 0.7
    ELSE 0.5
  END AS regime_confidence,
  
  -- Risk level
  CASE
    WHEN s.vix_value > 30 OR p.return_30d < -0.15 THEN 'EXTREME'
    WHEN s.vix_value > 25 OR p.return_30d < -0.10 THEN 'HIGH'
    WHEN s.vix_value > 20 OR ABS(p.return_30d) > 0.08 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  
  -- Trading environment
  CASE
    WHEN p.volatility_30d > 2 AND s.vix_value > 20 THEN 'AVOID'
    WHEN p.return_30d > 0.05 AND s.vix_value < 20 THEN 'FAVORABLE'
    WHEN s.tariff_mentions > 5 THEN 'UNCERTAIN'
    ELSE 'NORMAL'
  END AS trading_environment
  
FROM `cbi-v14.models.signals_master` s
LEFT JOIN price_metrics p ON s.date = p.date
WHERE s.date IS NOT NULL
ORDER BY s.date
"""

print("Creating enhanced market regimes...")
try:
    job = client.query(market_regime_query)
    result = job.result()
    print("✓ Enhanced market regimes created")
    
    # Check regime distribution
    check = """
    SELECT 
        detailed_regime,
        COUNT(*) as days,
        AVG(regime_confidence) as avg_confidence
    FROM `cbi-v14.models.enhanced_market_regimes`
    GROUP BY detailed_regime
    ORDER BY days DESC
    """
    regimes = client.query(check).to_dataframe()
    print("\nRegime Distribution:")
    for _, row in regimes.head(5).iterrows():
        print(f"  {row['detailed_regime']}: {row['days']:,} days ({row['avg_confidence']:.2f} confidence)")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

# STEP 4: Combine All Enhanced Features
print("\nSTEP 4: CREATE MASTER ENHANCED DATASET")
print("-"*60)

master_enhanced_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_enhanced_final` AS
SELECT 
  t.*,
  
  -- Policy features
  COALESCE(p.tariff_mentions, 0) AS policy_tariff_mentions,
  COALESCE(p.ice_mentions, 0) AS policy_ice_mentions,
  COALESCE(p.labor_mentions, 0) AS policy_labor_mentions,
  COALESCE(p.trump_order_mentions, 0) AS policy_trump_mentions,
  COALESCE(p.china_mentions, 0) AS policy_china_mentions,
  COALESCE(p.tariff_sentiment, 0) AS policy_tariff_sentiment,
  COALESCE(p.trump_sentiment, 0) AS policy_trump_sentiment,
  
  -- News proxy features
  COALESCE(n.soybean_news, 0) AS news_soybean_count,
  COALESCE(n.trade_news, 0) AS news_trade_count,
  COALESCE(n.weather_news, 0) AS news_weather_count,
  COALESCE(n.soybean_sentiment, 0) AS news_soybean_sentiment,
  COALESCE(n.trade_sentiment, 0) AS news_trade_sentiment,
  COALESCE(n.total_engagement, 0) AS social_engagement,
  
  -- Market regime features
  COALESCE(r.detailed_regime, 'NEUTRAL') AS market_regime_detailed,
  COALESCE(r.regime_confidence, 0.5) AS regime_confidence,
  COALESCE(r.risk_level, 'LOW') AS risk_level,
  COALESCE(r.trading_environment, 'NORMAL') AS trading_environment
  
FROM `cbi-v14.models.training_dataset` t
LEFT JOIN `cbi-v14.models.enhanced_policy_features` p ON t.date = p.date
LEFT JOIN `cbi-v14.models.enhanced_news_proxy` n ON t.date = n.date
LEFT JOIN `cbi-v14.models.enhanced_market_regimes` r ON t.date = r.date
ORDER BY t.date
"""

print("Creating master enhanced dataset...")
try:
    job = client.query(master_enhanced_query)
    result = job.result()
    print("✓ Master enhanced dataset created")
    
    # Final statistics
    check = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(CASE WHEN policy_tariff_mentions > 0 THEN 1 END) as rows_with_tariff,
        COUNT(CASE WHEN news_soybean_count > 0 THEN 1 END) as rows_with_soybean_news,
        COUNT(DISTINCT market_regime_detailed) as unique_regimes
    FROM `cbi-v14.models.training_enhanced_final`
    """
    stats = client.query(check).to_dataframe()
    print(f"\nFinal Dataset Statistics:")
    print(f"  Total rows: {stats['total_rows'].iloc[0]:,}")
    print(f"  Rows with tariff mentions: {stats['rows_with_tariff'].iloc[0]:,}")
    print(f"  Rows with soybean news: {stats['rows_with_soybean_news'].iloc[0]:,}")
    print(f"  Unique market regimes: {stats['unique_regimes'].iloc[0]}")
    
except Exception as e:
    print(f"✗ Error: {str(e)[:200]}")

print("\n" + "="*80)
print("ENHANCED SIGNAL EXTRACTION COMPLETE")
print("="*80)

print("""
✅ CREATED ENHANCED FEATURES:

1. POLICY FEATURES (from social data):
   - Tariff, ICE, Labor, Trump order mentions
   - Category-specific sentiment analysis
   - China-specific tracking

2. NEWS PROXY (from social posts):
   - Soybean, Oil, Trade, Weather, Harvest news
   - Category-specific sentiment
   - Engagement metrics as importance proxy

3. MARKET REGIMES (9 detailed types):
   - Crisis, High Volatility, Bullish/Bearish Trends
   - Trade Tension, Sentiment Extremes
   - Confidence scores and risk levels

4. MASTER DATASET:
   - All original features
   - Enhanced policy signals
   - News proxy features
   - Detailed market regimes

NEXT STEP: Train regime-specific models:

CREATE OR REPLACE MODEL `cbi-v14.models.zl_boosted_enhanced_v6`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w']
) AS
SELECT * EXCEPT(date, target_1m, target_3m, target_6m, market_regime_detailed, risk_level, trading_environment)
FROM `cbi-v14.models.training_enhanced_final`
WHERE target_1w IS NOT NULL
""")
