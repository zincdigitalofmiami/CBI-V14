#!/usr/bin/env python3
"""
INTEGRATE NEWS DATA INTO TRAINING DATASET
Create comprehensive news features from staging tables and merge into training dataset
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

client = bigquery.Client(project='cbi-v14')

print("="*80)
print("INTEGRATING NEWS DATA INTO TRAINING DATASET")
print("="*80)

# Step 1: Create consolidated news features table
print("\n1. CREATING CONSOLIDATED NEWS FEATURES")
print("-"*60)

consolidate_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.news_features_daily`
OPTIONS(
  expiration_timestamp=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 55 DAY)
) AS
WITH all_news AS (
  -- News from advanced scraper
  SELECT
    DATE(published_date) AS date,
    source,
    source_type,
    title,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    lobbying_mentions,
    weather_mentions,
    biofuel_mentions,
    content_length,
    sentiment
  FROM `cbi-v14.forecasting_data_warehouse.news_advanced`
  WHERE published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  
  UNION ALL
  
  -- News from ultra-aggressive scraper
  SELECT
    DATE(published_date) AS date,
    source,
    'scraped' AS source_type,
    title,
    relevance,
    total_score,
    soybean_oil_mentions,
    tariffs_mentions,
    china_mentions,
    brazil_mentions,
    legislation_mentions,
    0 AS lobbying_mentions,
    0 AS weather_mentions,
    0 AS biofuel_mentions,
    content_length,
    0.0 AS sentiment
  FROM `cbi-v14.forecasting_data_warehouse.news_ultra_aggressive`
  WHERE published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  
  UNION ALL
  
  -- Original news intelligence
  SELECT
    DATE(timestamp) AS date,
    source,
    'api' AS source_type,
    title,
    CASE 
      WHEN news_sentiment_score > 0.5 THEN 'high'
      WHEN news_sentiment_score < -0.5 THEN 'high'
      ELSE 'medium'
    END AS relevance,
    ABS(news_sentiment_score) * 10 AS total_score,
    0 AS soybean_oil_mentions,
    0 AS tariffs_mentions,
    0 AS china_mentions,
    0 AS brazil_mentions,
    0 AS legislation_mentions,
    0 AS lobbying_mentions,
    0 AS weather_mentions,
    0 AS biofuel_mentions,
    LENGTH(content) AS content_length,
    news_sentiment_score AS sentiment
  FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
  WHERE timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    AND content IS NOT NULL
)

SELECT
  date,
  -- News volume metrics
  COUNT(*) AS news_total_count,
  COUNT(DISTINCT source) AS news_source_count,
  COUNT(CASE WHEN relevance IN ('critical', 'high') THEN 1 END) AS news_high_relevance_count,
  
  -- Soybean oil specific news
  SUM(soybean_oil_mentions) AS news_soybean_oil_mentions,
  COUNT(CASE WHEN soybean_oil_mentions > 0 THEN 1 END) AS news_soybean_oil_articles,
  
  -- Tariff news
  SUM(tariffs_mentions) AS news_tariff_mentions,
  COUNT(CASE WHEN tariffs_mentions > 0 THEN 1 END) AS news_tariff_articles,
  AVG(CASE WHEN tariffs_mentions > 0 THEN total_score END) AS news_tariff_avg_score,
  
  -- China trade news
  SUM(china_mentions) AS news_china_mentions,
  COUNT(CASE WHEN china_mentions > 0 THEN 1 END) AS news_china_articles,
  AVG(CASE WHEN china_mentions > 0 THEN sentiment END) AS news_china_sentiment,
  
  -- Brazil trade news
  SUM(brazil_mentions) AS news_brazil_mentions,
  COUNT(CASE WHEN brazil_mentions > 0 THEN 1 END) AS news_brazil_articles,
  
  -- Policy/Legislation news
  SUM(legislation_mentions) AS news_legislation_mentions,
  COUNT(CASE WHEN legislation_mentions > 0 THEN 1 END) AS news_legislation_articles,
  
  -- Lobbying news
  SUM(lobbying_mentions) AS news_lobbying_mentions,
  COUNT(CASE WHEN lobbying_mentions > 0 THEN 1 END) AS news_lobbying_articles,
  
  -- Weather impacts news
  SUM(weather_mentions) AS news_weather_mentions,
  COUNT(CASE WHEN weather_mentions > 0 THEN 1 END) AS news_weather_articles,
  
  -- Biofuel news
  SUM(biofuel_mentions) AS news_biofuel_mentions,
  COUNT(CASE WHEN biofuel_mentions > 0 THEN 1 END) AS news_biofuel_articles,
  
  -- Overall sentiment and quality
  AVG(sentiment) AS news_avg_sentiment,
  STDDEV(sentiment) AS news_sentiment_volatility,
  AVG(total_score) AS news_avg_relevance_score,
  AVG(content_length) AS news_avg_content_length,
  
  -- Trend indicators (7-day average)
  AVG(COUNT(*)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS news_7d_avg_count,
  AVG(SUM(soybean_oil_mentions)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS news_7d_avg_soybean_mentions,
  AVG(SUM(tariffs_mentions)) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS news_7d_avg_tariff_mentions,
  
  -- Peak activity detection
  CASE 
    WHEN COUNT(*) > PERCENTILE_CONT(COUNT(*), 0.9) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) THEN 1
    ELSE 0
  END AS news_spike_detected
  
FROM all_news
GROUP BY date
ORDER BY date DESC
"""

print("Creating consolidated news features table...")
job = client.query(consolidate_query)
job.result()
print("✓ Created news_features_daily table")

# Step 2: Enhance training dataset with news features
print("\n2. ENHANCING TRAINING DATASET WITH NEWS FEATURES")
print("-"*60)

enhance_query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_dataset`
PARTITION BY date
CLUSTER BY date
AS
SELECT
  -- All existing features
  t.*,
  
  -- News features (fill nulls with 0)
  COALESCE(n.news_total_count, 0) AS news_total_count,
  COALESCE(n.news_source_count, 0) AS news_source_count,
  COALESCE(n.news_high_relevance_count, 0) AS news_high_relevance_count,
  
  -- Soybean oil news
  COALESCE(n.news_soybean_oil_mentions, 0) AS news_soybean_oil_mentions,
  COALESCE(n.news_soybean_oil_articles, 0) AS news_soybean_oil_articles,
  
  -- Tariff news
  COALESCE(n.news_tariff_mentions, 0) AS news_tariff_mentions,
  COALESCE(n.news_tariff_articles, 0) AS news_tariff_articles,
  COALESCE(n.news_tariff_avg_score, 0) AS news_tariff_avg_score,
  
  -- China trade news
  COALESCE(n.news_china_mentions, 0) AS news_china_mentions,
  COALESCE(n.news_china_articles, 0) AS news_china_articles,
  COALESCE(n.news_china_sentiment, 0) AS news_china_sentiment,
  
  -- Brazil trade news
  COALESCE(n.news_brazil_mentions, 0) AS news_brazil_mentions,
  COALESCE(n.news_brazil_articles, 0) AS news_brazil_articles,
  
  -- Policy/Legislation news
  COALESCE(n.news_legislation_mentions, 0) AS news_legislation_mentions,
  COALESCE(n.news_legislation_articles, 0) AS news_legislation_articles,
  
  -- Lobbying news
  COALESCE(n.news_lobbying_mentions, 0) AS news_lobbying_mentions,
  COALESCE(n.news_lobbying_articles, 0) AS news_lobbying_articles,
  
  -- Weather news
  COALESCE(n.news_weather_mentions, 0) AS news_weather_mentions,
  COALESCE(n.news_weather_articles, 0) AS news_weather_articles,
  
  -- Biofuel news
  COALESCE(n.news_biofuel_mentions, 0) AS news_biofuel_mentions,
  COALESCE(n.news_biofuel_articles, 0) AS news_biofuel_articles,
  
  -- Sentiment metrics
  COALESCE(n.news_avg_sentiment, 0) AS news_avg_sentiment,
  COALESCE(n.news_sentiment_volatility, 0) AS news_sentiment_volatility,
  COALESCE(n.news_avg_relevance_score, 0) AS news_avg_relevance_score,
  COALESCE(n.news_avg_content_length, 0) AS news_avg_content_length,
  
  -- Trend indicators
  COALESCE(n.news_7d_avg_count, 0) AS news_7d_avg_count,
  COALESCE(n.news_7d_avg_soybean_mentions, 0) AS news_7d_avg_soybean_mentions,
  COALESCE(n.news_7d_avg_tariff_mentions, 0) AS news_7d_avg_tariff_mentions,
  
  -- Peak detection
  COALESCE(n.news_spike_detected, 0) AS news_spike_detected

FROM `cbi-v14.models.training_dataset` t
LEFT JOIN `cbi-v14.models.news_features_daily` n ON t.date = n.date
"""

print("Enhancing training dataset...")
job = client.query(enhance_query)
job.result()
print("✓ Enhanced training dataset")

# Step 3: Verify the integration
print("\n3. VERIFYING INTEGRATION")
print("-"*60)

verify_query = """
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT date) AS unique_dates,
  COUNT(*) - COUNT(news_total_count) AS missing_news_data,
  AVG(news_total_count) AS avg_daily_news_count,
  AVG(news_tariff_mentions) AS avg_tariff_mentions,
  AVG(news_china_mentions) AS avg_china_mentions,
  AVG(news_brazil_mentions) AS avg_brazil_mentions,
  AVG(news_soybean_oil_mentions) AS avg_soybean_oil_mentions
FROM `cbi-v14.models.training_dataset`
"""

stats = client.query(verify_query).to_dataframe()
print("\nTraining Dataset Stats:")
print(stats.to_string(index=False))

# Step 4: Show feature counts
print("\n4. FEATURE INVENTORY")
print("-"*60)

feature_query = """
SELECT 
  COUNT(*) AS total_features,
  COUNT(CASE WHEN column_name LIKE 'news_%' THEN 1 END) AS news_features,
  COUNT(CASE WHEN column_name LIKE 'corr_%' THEN 1 END) AS correlation_features,
  COUNT(CASE WHEN column_name LIKE 'feature_%' THEN 1 END) AS engineered_features,
  COUNT(CASE WHEN column_name LIKE 'china_%' THEN 1 END) AS china_features,
  COUNT(CASE WHEN column_name LIKE 'brazil_%' THEN 1 END) AS brazil_features,
  COUNT(CASE WHEN column_name LIKE 'tariff%' THEN 1 END) AS tariff_features
FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset'
"""

features = client.query(feature_query).to_dataframe()
print("\nFeature Breakdown:")
print(features.to_string(index=False))

print("\n" + "="*80)
print("INTEGRATION COMPLETE")
print("="*80)
print(f"""
NEWS FEATURES ADDED:
- {int(features['news_features'].iloc[0])} news-related features
- Covering: tariffs, China, Brazil, legislation, lobbying, weather, biofuel
- Integration method: LEFT JOIN with null handling
- All existing features preserved

NEXT STEPS:
1. Retrain models with enhanced dataset
2. Monitor model performance improvements
3. Add more news sources as they become available
""")
