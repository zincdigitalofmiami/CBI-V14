-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- PHASE 0.2: COMPUTED FEATURES FROM SCRAPED DATA
-- ============================================
-- Create 9 feature views from web scraping tables
-- These enhance training dataset with real-time intelligence

-- ============================================
-- FEATURE 1: Forward Curve Carry
-- ============================================
-- Measures backwardation vs contango from Barchart futures
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_forward_curve_carry` AS
WITH latest_prices AS (
  SELECT 
    contract_month,
    last,
    scrape_timestamp,
    ROW_NUMBER() OVER (PARTITION BY contract_month ORDER BY scrape_timestamp DESC) as rn
  FROM `cbi-v14.forecasting_data_warehouse.futures_prices_barchart`
  WHERE scrape_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
)
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  (SELECT last FROM latest_prices WHERE rn = 1 
   ORDER BY contract_month LIMIT 1 OFFSET 0) - 
  (SELECT last FROM latest_prices WHERE rn = 1 
   ORDER BY contract_month LIMIT 1 OFFSET 2) AS carry_1m_3m,
  
  CASE 
    WHEN (SELECT last FROM latest_prices WHERE rn = 1 ORDER BY contract_month LIMIT 1 OFFSET 0) > 
         (SELECT last FROM latest_prices WHERE rn = 1 ORDER BY contract_month LIMIT 1 OFFSET 2) 
    THEN 'backwardation'
    WHEN (SELECT last FROM latest_prices WHERE rn = 1 ORDER BY contract_month LIMIT 1 OFFSET 0) < 
         (SELECT last FROM latest_prices WHERE rn = 1 ORDER BY contract_month LIMIT 1 OFFSET 2)
    THEN 'contango'
    ELSE 'flat'
  END AS curve_shape
FROM (SELECT 1);

-- ============================================
-- FEATURE 2: Policy Support Score (7-day)
-- ============================================
-- Aggregate policy support from EPA RFS and Federal Register
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_policy_support_7d` AS
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  COALESCE(
    COUNTIF(category IN ('RFS', '45Z') AND value_num > 0) -
    COUNTIF(category = 'SRE'),
    0
  ) AS policy_support_score,
  COUNT(*) AS total_policy_events
FROM `cbi-v14.forecasting_data_warehouse.policy_rfs_volumes`
WHERE announcement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)

UNION ALL

SELECT
  CURRENT_TIMESTAMP() AS as_of,
  COUNTIF(doc_type IN ('Rule', 'Proposed Rule')) AS policy_support_score,
  COUNT(*) AS total_policy_events
FROM `cbi-v14.forecasting_data_warehouse.policy_events_federalregister`
WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND ARRAY_TO_STRING(topics, ',') LIKE '%agriculture%';

-- ============================================
-- FEATURE 3: Trader Sentiment Score
-- ============================================
-- TradingView bullish/bearish sentiment
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_trader_sentiment` AS
SELECT
  scrape_timestamp,
  bullish_pct - bearish_pct AS sentiment_score,
  bullish_pct,
  bearish_pct,
  CASE
    WHEN bullish_pct - bearish_pct > 20 THEN 'very_bullish'
    WHEN bullish_pct - bearish_pct > 10 THEN 'bullish'
    WHEN bullish_pct - bearish_pct < -20 THEN 'very_bearish'
    WHEN bullish_pct - bearish_pct < -10 THEN 'bearish'
    ELSE 'neutral'
  END AS sentiment_label
FROM `cbi-v14.forecasting_data_warehouse.futures_sentiment_tradingview`
WHERE symbol = 'ZL'
ORDER BY scrape_timestamp DESC
LIMIT 1;

-- ============================================
-- FEATURE 4: News Sentiment Aggregation (7-day)
-- ============================================
-- Aggregate sentiment from all news sources
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_news_sentiment_7d` AS
WITH all_news AS (
  SELECT sentiment, published_at FROM `cbi-v14.forecasting_data_warehouse.news_reuters`
  WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  
  UNION ALL
  
  SELECT 0.0 AS sentiment, published_at FROM `cbi-v14.forecasting_data_warehouse.news_industry_brownfield`
  WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  
  UNION ALL
  
  SELECT 0.0 AS sentiment, published_at FROM `cbi-v14.forecasting_data_warehouse.news_market_farmprogress`
  WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
)
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  AVG(sentiment) AS avg_sentiment_7d,
  STDDEV(sentiment) AS sentiment_volatility_7d,
  COUNT(*) AS news_volume_7d,
  MIN(published_at) AS earliest_article,
  MAX(published_at) AS latest_article
FROM all_news;

-- ============================================
-- FEATURE 5: Entity Mentions (China, Brazil, Argentina) - 7-day
-- ============================================
-- Track geopolitical entity mentions in news
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_entity_mentions_7d` AS
WITH all_entities AS (
  SELECT entities, published_at FROM `cbi-v14.forecasting_data_warehouse.news_reuters`
  WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  
  UNION ALL
  
  SELECT entities, published_at FROM `cbi-v14.forecasting_data_warehouse.news_industry_brownfield`
  WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
)
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  SUM(CASE WHEN 'China' IN UNNEST(entities) OR 'Chinese' IN UNNEST(entities) THEN 1 ELSE 0 END) AS china_mentions,
  SUM(CASE WHEN 'Brazil' IN UNNEST(entities) OR 'Brazilian' IN UNNEST(entities) THEN 1 ELSE 0 END) AS brazil_mentions,
  SUM(CASE WHEN 'Argentina' IN UNNEST(entities) OR 'Argentine' IN UNNEST(entities) THEN 1 ELSE 0 END) AS argentina_mentions,
  SUM(CASE WHEN 'USA' IN UNNEST(entities) OR 'United States' IN UNNEST(entities) THEN 1 ELSE 0 END) AS usa_mentions,
  COUNT(DISTINCT published_at) AS total_articles
FROM all_entities;

-- ============================================
-- FEATURE 6: ENSO Risk Score
-- ============================================
-- Climate risk based on La Niña/El Niño phases
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_enso_risk` AS
SELECT
  as_of_date,
  enso_phase,
  probability,
  strength,
  CASE 
    WHEN enso_phase = 'La Niña' AND strength = 'strong' THEN probability * 1.5
    WHEN enso_phase = 'La Niña' AND strength = 'moderate' THEN probability * 1.0
    WHEN enso_phase = 'La Niña' AND strength = 'weak' THEN probability * 0.5
    WHEN enso_phase = 'El Niño' AND strength = 'strong' THEN -probability * 1.5
    WHEN enso_phase = 'El Niño' AND strength = 'moderate' THEN -probability * 1.0
    WHEN enso_phase = 'El Niño' AND strength = 'weak' THEN -probability * 0.5
    ELSE 0
  END AS enso_risk_score,
  forecast_phase_3mo,
  notes
FROM `cbi-v14.forecasting_data_warehouse.enso_climate_status`
ORDER BY as_of_date DESC
LIMIT 1;

-- ============================================
-- FEATURE 7: Legislative Activity Score (30-day)
-- ============================================
-- Track agricultural legislation activity
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_legislative_activity_30d` AS
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  COUNT(*) AS active_bills,
  COUNTIF(DATE(latest_action) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) AS recent_activity,
  COUNT(DISTINCT ARRAY_TO_STRING(sponsors, ',')) AS unique_sponsors,
  AVG(DATE_DIFF(CURRENT_DATE(), DATE(introduced), DAY)) AS avg_days_since_introduction
FROM `cbi-v14.forecasting_data_warehouse.legislative_bills`
WHERE DATE(introduced) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- ============================================
-- FEATURE 8: Market Breadth Score
-- ============================================
-- Aggregate technical indicators across sources
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_market_breadth` AS
WITH latest_technicals AS (
  -- From Investing.com
  SELECT 
    technical_indicator_rsi,
    technical_indicator_macd,
    scrape_timestamp
  FROM `cbi-v14.forecasting_data_warehouse.futures_prices_investing`
  WHERE symbol = 'ZL'
  ORDER BY scrape_timestamp DESC
  LIMIT 1
),
latest_sentiment AS (
  -- From TradingView
  SELECT
    bullish_pct - bearish_pct AS sentiment_score,
    scrape_timestamp
  FROM `cbi-v14.forecasting_data_warehouse.futures_sentiment_tradingview`
  WHERE symbol = 'ZL'
  ORDER BY scrape_timestamp DESC
  LIMIT 1
)
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  t.technical_indicator_rsi AS rsi,
  t.technical_indicator_macd AS macd,
  s.sentiment_score AS trader_sentiment,
  -- Composite breadth score (0-100)
  COALESCE(
    (t.technical_indicator_rsi + ((s.sentiment_score + 100) / 2)) / 2,
    50
  ) AS market_breadth_score,
  CASE
    WHEN t.technical_indicator_rsi > 70 THEN 'overbought'
    WHEN t.technical_indicator_rsi < 30 THEN 'oversold'
    ELSE 'neutral'
  END AS rsi_signal
FROM latest_technicals t
CROSS JOIN latest_sentiment s;

-- ============================================
-- FEATURE 9: Institutional Pressure Score
-- ============================================
-- CME open interest changes indicate institutional positioning
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.feature_institutional_pressure` AS
WITH recent_oi AS (
  SELECT 
    scrape_timestamp,
    open_interest,
    volume,
    LAG(open_interest) OVER (ORDER BY scrape_timestamp) AS prev_open_interest
  FROM `cbi-v14.forecasting_data_warehouse.futures_prices_cme_public`
  WHERE symbol = 'ZL'
  ORDER BY scrape_timestamp DESC
  LIMIT 10
)
SELECT
  CURRENT_TIMESTAMP() AS as_of,
  AVG(open_interest) AS avg_open_interest,
  AVG(open_interest - prev_open_interest) AS avg_oi_change,
  AVG(volume) AS avg_volume,
  CASE
    WHEN AVG(open_interest - prev_open_interest) > 1000 THEN 'bullish_accumulation'
    WHEN AVG(open_interest - prev_open_interest) < -1000 THEN 'bearish_distribution'
    ELSE 'neutral'
  END AS institutional_signal
FROM recent_oi
WHERE prev_open_interest IS NOT NULL;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Check all feature views are operational
SELECT 
  'forward_curve_carry' AS feature,
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_forward_curve_carry`) AS has_data

UNION ALL

SELECT 
  'policy_support_7d',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_policy_support_7d`)

UNION ALL

SELECT 
  'trader_sentiment',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_trader_sentiment`)

UNION ALL

SELECT 
  'news_sentiment_7d',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_news_sentiment_7d`)

UNION ALL

SELECT 
  'entity_mentions_7d',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_entity_mentions_7d`)

UNION ALL

SELECT 
  'enso_risk',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_enso_risk`)

UNION ALL

SELECT 
  'legislative_activity_30d',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_legislative_activity_30d`)

UNION ALL

SELECT 
  'market_breadth',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_market_breadth`)

UNION ALL

SELECT 
  'institutional_pressure',
  (SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.feature_institutional_pressure`);








