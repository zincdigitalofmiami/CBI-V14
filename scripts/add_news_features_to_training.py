#!/usr/bin/env python3
"""
ADD SEGMENTED NEWS FEATURES TO TRAINING DATASET
Surgical update: Add all news intelligence without breaking existing models
"""

from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🚀 ADDING SEGMENTED NEWS FEATURES TO TRAINING DATASET")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("✅ Strategy: Create NEW enriched view, test it, then replace training_dataset")
print()

# Step 1: Create daily news aggregates
print("Step 1: Creating daily news aggregates from news_advanced...")

news_aggregates_query = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_daily_news_features` AS
WITH daily_news AS (
  SELECT 
    DATE(published_date) as date,
    COUNT(*) as news_total_articles,
    COUNT(DISTINCT source) as news_unique_sources,
    
    -- Segmented mention counts
    SUM(soybean_oil_mentions) as news_soy_oil_mentions,
    SUM(tariffs_mentions) as news_tariff_mentions,
    SUM(china_mentions) as news_china_mentions,
    SUM(brazil_mentions) as news_brazil_mentions,
    SUM(legislation_mentions) as news_legislation_mentions,
    SUM(lobbying_mentions) as news_lobbying_mentions,
    SUM(weather_mentions) as news_weather_mentions,
    SUM(biofuel_mentions) as news_biofuel_mentions,
    
    -- Relevance scores
    AVG(total_score) as news_avg_relevance_score,
    MAX(total_score) as news_max_relevance_score,
    
    -- High relevance article count
    SUM(CASE WHEN relevance = 'HIGH' THEN 1 ELSE 0 END) as news_high_relevance_count,
    SUM(CASE WHEN relevance = 'MEDIUM' THEN 1 ELSE 0 END) as news_medium_relevance_count,
    
    -- Content metrics
    AVG(content_length) as news_avg_content_length,
    SUM(content_length) as news_total_content_length
    
  FROM `cbi-v14.forecasting_data_warehouse.news_advanced`
  WHERE published_date IS NOT NULL
  GROUP BY DATE(published_date)
),
-- Add 7-day rolling averages for trend detection
rolling_averages AS (
  SELECT 
    * EXCEPT(date),
    date,
    AVG(news_total_articles) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_7d_avg_articles,
    AVG(news_tariff_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_7d_avg_tariff_mentions,
    AVG(news_china_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_7d_avg_china_mentions,
    AVG(news_biofuel_mentions) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_7d_avg_biofuel_mentions
  FROM daily_news
)
SELECT * FROM rolling_averages;
"""

try:
    job = client.query(news_aggregates_query)
    job.result()
    print("✅ Created vw_daily_news_features")
    
    # Check row count
    check_query = "SELECT COUNT(*) as cnt FROM `cbi-v14.models.vw_daily_news_features`"
    result = client.query(check_query).to_dataframe()
    print(f"   News features: {result['cnt'].iloc[0]} days")
    print()
except Exception as e:
    print(f"❌ Error creating news features: {str(e)}")
    exit(1)

# Step 2: Create social sentiment aggregates
print("Step 2: Creating daily social sentiment features...")

social_aggregates_query = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_daily_social_features` AS
WITH daily_social AS (
  SELECT 
    DATE(timestamp) as date,
    COUNT(*) as social_post_count,
    AVG(sentiment_score) as social_avg_sentiment,
    STDDEV(sentiment_score) as social_sentiment_volatility,
    
    -- Sentiment distribution
    SUM(CASE WHEN sentiment_score > 0.5 THEN 1 ELSE 0 END) as social_bullish_posts,
    SUM(CASE WHEN sentiment_score < -0.5 THEN 1 ELSE 0 END) as social_bearish_posts,
    SUM(CASE WHEN sentiment_score BETWEEN -0.5 AND 0.5 THEN 1 ELSE 0 END) as social_neutral_posts,
    
    -- Extreme sentiment detection
    MAX(sentiment_score) as social_max_sentiment,
    MIN(sentiment_score) as social_min_sentiment
    
  FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
  WHERE timestamp IS NOT NULL
  GROUP BY DATE(timestamp)
),
-- Add momentum indicators
sentiment_momentum AS (
  SELECT 
    * EXCEPT(date),
    date,
    AVG(social_avg_sentiment) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as social_7d_avg_sentiment,
    AVG(social_sentiment_volatility) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as social_7d_avg_volatility
  FROM daily_social
)
SELECT * FROM sentiment_momentum;
"""

try:
    job = client.query(social_aggregates_query)
    job.result()
    print("✅ Created vw_daily_social_features")
    
    check_query = "SELECT COUNT(*) as cnt FROM `cbi-v14.models.vw_daily_social_features`"
    result = client.query(check_query).to_dataframe()
    print(f"   Social features: {result['cnt'].iloc[0]} days")
    print()
except Exception as e:
    print(f"❌ Error creating social features: {str(e)}")
    exit(1)

# Step 3: Create ENRICHED training dataset (TEST VERSION)
print("Step 3: Creating ENRICHED training dataset (test version)...")

enriched_dataset_query = """
CREATE OR REPLACE VIEW `cbi-v14.models.training_dataset_enriched` AS
SELECT 
  t.*,
  -- News features (COALESCE to 0 if no news that day)
  COALESCE(n.news_total_articles, 0) as news_total_articles,
  COALESCE(n.news_unique_sources, 0) as news_unique_sources,
  COALESCE(n.news_soy_oil_mentions, 0) as news_soy_oil_mentions,
  COALESCE(n.news_tariff_mentions, 0) as news_tariff_mentions,
  COALESCE(n.news_china_mentions, 0) as news_china_mentions,
  COALESCE(n.news_brazil_mentions, 0) as news_brazil_mentions,
  COALESCE(n.news_legislation_mentions, 0) as news_legislation_mentions,
  COALESCE(n.news_lobbying_mentions, 0) as news_lobbying_mentions,
  COALESCE(n.news_weather_mentions, 0) as news_weather_mentions,
  COALESCE(n.news_biofuel_mentions, 0) as news_biofuel_mentions,
  COALESCE(n.news_avg_relevance_score, 0) as news_avg_relevance_score,
  COALESCE(n.news_max_relevance_score, 0) as news_max_relevance_score,
  COALESCE(n.news_high_relevance_count, 0) as news_high_relevance_count,
  COALESCE(n.news_medium_relevance_count, 0) as news_medium_relevance_count,
  COALESCE(n.news_avg_content_length, 0) as news_avg_content_length,
  COALESCE(n.news_7d_avg_articles, 0) as news_7d_avg_articles,
  COALESCE(n.news_7d_avg_tariff_mentions, 0) as news_7d_avg_tariff_mentions,
  COALESCE(n.news_7d_avg_china_mentions, 0) as news_7d_avg_china_mentions,
  COALESCE(n.news_7d_avg_biofuel_mentions, 0) as news_7d_avg_biofuel_mentions,
  
  -- Social sentiment features (COALESCE to 0 if no social data that day)
  COALESCE(s.social_post_count, 0) as social_post_count,
  COALESCE(s.social_avg_sentiment, 0) as social_avg_sentiment,
  COALESCE(s.social_sentiment_volatility, 0) as social_sentiment_volatility,
  COALESCE(s.social_bullish_posts, 0) as social_bullish_posts,
  COALESCE(s.social_bearish_posts, 0) as social_bearish_posts,
  COALESCE(s.social_neutral_posts, 0) as social_neutral_posts,
  COALESCE(s.social_max_sentiment, 0) as social_max_sentiment,
  COALESCE(s.social_min_sentiment, 0) as social_min_sentiment,
  COALESCE(s.social_7d_avg_sentiment, 0) as social_7d_avg_sentiment,
  COALESCE(s.social_7d_avg_volatility, 0) as social_7d_avg_volatility

FROM `cbi-v14.models.training_dataset` t
LEFT JOIN `cbi-v14.models.vw_daily_news_features` n 
  ON t.date = CAST(n.date AS STRING)
LEFT JOIN `cbi-v14.models.vw_daily_social_features` s 
  ON t.date = CAST(s.date AS STRING);
"""

try:
    job = client.query(enriched_dataset_query)
    job.result()
    print("✅ Created training_dataset_enriched (TEST VERSION)")
    print()
except Exception as e:
    print(f"❌ Error creating enriched dataset: {str(e)}")
    exit(1)

# Step 4: Validate enriched dataset
print("Step 4: Validating enriched dataset...")

validation_query = """
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  SUM(CASE WHEN news_total_articles > 0 THEN 1 ELSE 0 END) as days_with_news,
  SUM(CASE WHEN social_post_count > 0 THEN 1 ELSE 0 END) as days_with_social,
  AVG(news_tariff_mentions) as avg_tariff_mentions,
  AVG(news_china_mentions) as avg_china_mentions,
  AVG(social_avg_sentiment) as avg_sentiment_score
FROM `cbi-v14.models.training_dataset_enriched`;
"""

try:
    validation_df = client.query(validation_query).to_dataframe()
    print("📊 ENRICHED DATASET VALIDATION:")
    print(f"   Total rows: {validation_df['total_rows'].iloc[0]}")
    print(f"   Unique dates: {validation_df['unique_dates'].iloc[0]}")
    print(f"   Days with news: {validation_df['days_with_news'].iloc[0]}")
    print(f"   Days with social data: {validation_df['days_with_social'].iloc[0]}")
    print(f"   Avg tariff mentions/day: {validation_df['avg_tariff_mentions'].iloc[0]:.2f}")
    print(f"   Avg China mentions/day: {validation_df['avg_china_mentions'].iloc[0]:.2f}")
    print(f"   Avg sentiment score: {validation_df['avg_sentiment_score'].iloc[0]:.3f}")
    print()
except Exception as e:
    print(f"❌ Error validating dataset: {str(e)}")
    exit(1)

# Step 5: Check for any NULL columns (data quality)
print("Step 5: Checking for NULL values...")

null_check_query = """
SELECT 
  SUM(CASE WHEN zl_price_current IS NULL THEN 1 ELSE 0 END) as null_price,
  SUM(CASE WHEN target_1w IS NULL THEN 1 ELSE 0 END) as null_target_1w,
  SUM(CASE WHEN target_1m IS NULL THEN 1 ELSE 0 END) as null_target_1m,
  SUM(CASE WHEN target_3m IS NULL THEN 1 ELSE 0 END) as null_target_3m,
  SUM(CASE WHEN target_6m IS NULL THEN 1 ELSE 0 END) as null_target_6m
FROM `cbi-v14.models.training_dataset_enriched`;
"""

try:
    null_df = client.query(null_check_query).to_dataframe()
    print("🔍 NULL CHECK:")
    print(f"   NULL current prices: {null_df['null_price'].iloc[0]}")
    print(f"   NULL 1w targets: {null_df['null_target_1w'].iloc[0]}")
    print(f"   NULL 1m targets: {null_df['null_target_1m'].iloc[0]}")
    print(f"   NULL 3m targets: {null_df['null_target_3m'].iloc[0]}")
    print(f"   NULL 6m targets: {null_df['null_target_6m'].iloc[0]}")
    print()
    
    if null_df['null_price'].iloc[0] > 0:
        print("⚠️  WARNING: Some rows have NULL prices - will exclude from training")
    
except Exception as e:
    print(f"❌ Error checking NULLs: {str(e)}")
    exit(1)

# Step 6: Compare feature counts
print("Step 6: Comparing OLD vs NEW dataset...")

compare_query = """
WITH old_cols AS (
  SELECT COUNT(*) as col_count
  FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset'
),
new_cols AS (
  SELECT COUNT(*) as col_count
  FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_enriched'
)
SELECT 
  o.col_count as old_column_count,
  n.col_count as new_column_count,
  n.col_count - o.col_count as added_columns
FROM old_cols o, new_cols n;
"""

try:
    compare_df = client.query(compare_query).to_dataframe()
    print("📊 DATASET COMPARISON:")
    print(f"   OLD training_dataset: {compare_df['old_column_count'].iloc[0]} columns")
    print(f"   NEW training_dataset_enriched: {compare_df['new_column_count'].iloc[0]} columns")
    print(f"   ADDED: {compare_df['added_columns'].iloc[0]} news/social features")
    print()
except Exception as e:
    print(f"❌ Error comparing datasets: {str(e)}")
    exit(1)

print("=" * 80)
print("✅ NEWS FEATURES SUCCESSFULLY ADDED TO TRAINING DATASET")
print("=" * 80)
print()

print("🎯 NEXT STEPS:")
print("1. Test model training with `training_dataset_enriched`")
print("2. If performance improves, replace `training_dataset` with enriched version")
print("3. Retrain ALL models with new features")
print()

print("🧪 TO TEST A MODEL:")
print("   python3 scripts/test_enriched_model.py")
print()

print("🚀 TO PROMOTE ENRICHED DATASET TO PRODUCTION:")
print("   # Backup old dataset")
print("   bq cp cbi-v14:models.training_dataset cbi-v14:models.training_dataset_backup")
print()
print("   # Replace with enriched version")
print("   bq rm -f cbi-v14:models.training_dataset")
print("   bq cp cbi-v14:models.training_dataset_enriched cbi-v14:models.training_dataset")
print()

print("=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

