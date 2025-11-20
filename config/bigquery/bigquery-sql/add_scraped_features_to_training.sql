-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- PHASE 0.2: ENHANCE TRAINING DATASET WITH SCRAPED FEATURES
-- ============================================
-- Add 9 new features from web scraping to training_dataset_super_enriched

-- Step 1: Add new columns to training dataset
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS forward_curve_carry_1m_3m FLOAT64,
ADD COLUMN IF NOT EXISTS curve_shape STRING,
ADD COLUMN IF NOT EXISTS policy_support_score_7d FLOAT64,
ADD COLUMN IF NOT EXISTS trader_sentiment_score FLOAT64,
ADD COLUMN IF NOT EXISTS trader_sentiment_label STRING,
ADD COLUMN IF NOT EXISTS news_sentiment_7d FLOAT64,
ADD COLUMN IF NOT EXISTS news_sentiment_volatility_7d FLOAT64,
ADD COLUMN IF NOT EXISTS news_volume_7d INT64,
ADD COLUMN IF NOT EXISTS enso_risk_score FLOAT64,
ADD COLUMN IF NOT EXISTS enso_phase STRING,
ADD COLUMN IF NOT EXISTS china_mentions_7d INT64,
ADD COLUMN IF NOT EXISTS brazil_mentions_7d INT64,
ADD COLUMN IF NOT EXISTS argentina_mentions_7d INT64,
ADD COLUMN IF NOT EXISTS market_breadth_score FLOAT64,
ADD COLUMN IF NOT EXISTS rsi_signal STRING,
ADD COLUMN IF NOT EXISTS institutional_pressure_signal STRING;

-- Step 2: Populate features with latest scraped data
-- NOTE: This populates with CURRENT values - for historical backfill, need time-series joins

UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET 
  -- Forward curve carry
  t.forward_curve_carry_1m_3m = (
    SELECT carry_1m_3m 
    FROM `cbi-v14.forecasting_data_warehouse.feature_forward_curve_carry`
    LIMIT 1
  ),
  t.curve_shape = (
    SELECT curve_shape
    FROM `cbi-v14.forecasting_data_warehouse.feature_forward_curve_carry`
    LIMIT 1
  ),
  
  -- Policy support
  t.policy_support_score_7d = (
    SELECT SUM(policy_support_score)
    FROM `cbi-v14.forecasting_data_warehouse.feature_policy_support_7d`
  ),
  
  -- Trader sentiment
  t.trader_sentiment_score = (
    SELECT sentiment_score
    FROM `cbi-v14.forecasting_data_warehouse.feature_trader_sentiment`
    LIMIT 1
  ),
  t.trader_sentiment_label = (
    SELECT sentiment_label
    FROM `cbi-v14.forecasting_data_warehouse.feature_trader_sentiment`
    LIMIT 1
  ),
  
  -- News sentiment
  t.news_sentiment_7d = (
    SELECT avg_sentiment_7d
    FROM `cbi-v14.forecasting_data_warehouse.feature_news_sentiment_7d`
    LIMIT 1
  ),
  t.news_sentiment_volatility_7d = (
    SELECT sentiment_volatility_7d
    FROM `cbi-v14.forecasting_data_warehouse.feature_news_sentiment_7d`
    LIMIT 1
  ),
  t.news_volume_7d = (
    SELECT CAST(news_volume_7d AS INT64)
    FROM `cbi-v14.forecasting_data_warehouse.feature_news_sentiment_7d`
    LIMIT 1
  ),
  
  -- ENSO risk
  t.enso_risk_score = (
    SELECT enso_risk_score
    FROM `cbi-v14.forecasting_data_warehouse.feature_enso_risk`
    LIMIT 1
  ),
  t.enso_phase = (
    SELECT enso_phase
    FROM `cbi-v14.forecasting_data_warehouse.feature_enso_risk`
    LIMIT 1
  ),
  
  -- Entity mentions
  t.china_mentions_7d = (
    SELECT CAST(china_mentions AS INT64)
    FROM `cbi-v14.forecasting_data_warehouse.feature_entity_mentions_7d`
    LIMIT 1
  ),
  t.brazil_mentions_7d = (
    SELECT CAST(brazil_mentions AS INT64)
    FROM `cbi-v14.forecasting_data_warehouse.feature_entity_mentions_7d`
    LIMIT 1
  ),
  t.argentina_mentions_7d = (
    SELECT CAST(argentina_mentions AS INT64)
    FROM `cbi-v14.forecasting_data_warehouse.feature_entity_mentions_7d`
    LIMIT 1
  ),
  
  -- Market breadth
  t.market_breadth_score = (
    SELECT market_breadth_score
    FROM `cbi-v14.forecasting_data_warehouse.feature_market_breadth`
    LIMIT 1
  ),
  t.rsi_signal = (
    SELECT rsi_signal
    FROM `cbi-v14.forecasting_data_warehouse.feature_market_breadth`
    LIMIT 1
  ),
  
  -- Institutional pressure
  t.institutional_pressure_signal = (
    SELECT institutional_signal
    FROM `cbi-v14.forecasting_data_warehouse.feature_institutional_pressure`
    LIMIT 1
  )

WHERE TRUE;

-- Step 3: Verification
-- Check new columns were added and populated
SELECT 
  'New Scraped Features' AS audit_type,
  COUNT(*) AS total_rows,
  
  -- Check feature coverage
  COUNTIF(forward_curve_carry_1m_3m IS NOT NULL) AS has_forward_curve,
  COUNTIF(policy_support_score_7d IS NOT NULL) AS has_policy_score,
  COUNTIF(trader_sentiment_score IS NOT NULL) AS has_trader_sentiment,
  COUNTIF(news_sentiment_7d IS NOT NULL) AS has_news_sentiment,
  COUNTIF(enso_risk_score IS NOT NULL) AS has_enso_risk,
  COUNTIF(china_mentions_7d IS NOT NULL) AS has_china_mentions,
  COUNTIF(market_breadth_score IS NOT NULL) AS has_market_breadth,
  COUNTIF(institutional_pressure_signal IS NOT NULL) AS has_institutional_pressure,
  
  -- Coverage percentages
  ROUND(COUNTIF(forward_curve_carry_1m_3m IS NOT NULL) * 100.0 / COUNT(*), 2) AS forward_curve_pct,
  ROUND(COUNTIF(policy_support_score_7d IS NOT NULL) * 100.0 / COUNT(*), 2) AS policy_score_pct,
  ROUND(COUNTIF(trader_sentiment_score IS NOT NULL) * 100.0 / COUNT(*), 2) AS trader_sentiment_pct

FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- Step 4: Feature statistics
SELECT
  'forward_curve_carry_1m_3m' AS feature_name,
  COUNT(*) AS non_null_count,
  AVG(forward_curve_carry_1m_3m) AS mean_value,
  STDDEV(forward_curve_carry_1m_3m) AS stddev,
  MIN(forward_curve_carry_1m_3m) AS min_value,
  MAX(forward_curve_carry_1m_3m) AS max_value
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE forward_curve_carry_1m_3m IS NOT NULL

UNION ALL

SELECT
  'policy_support_score_7d',
  COUNT(*),
  AVG(policy_support_score_7d),
  STDDEV(policy_support_score_7d),
  MIN(policy_support_score_7d),
  MAX(policy_support_score_7d)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE policy_support_score_7d IS NOT NULL

UNION ALL

SELECT
  'trader_sentiment_score',
  COUNT(*),
  AVG(trader_sentiment_score),
  STDDEV(trader_sentiment_score),
  MIN(trader_sentiment_score),
  MAX(trader_sentiment_score)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE trader_sentiment_score IS NOT NULL

UNION ALL

SELECT
  'news_sentiment_7d',
  COUNT(*),
  AVG(news_sentiment_7d),
  STDDEV(news_sentiment_7d),
  MIN(news_sentiment_7d),
  MAX(news_sentiment_7d)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE news_sentiment_7d IS NOT NULL

UNION ALL

SELECT
  'enso_risk_score',
  COUNT(*),
  AVG(enso_risk_score),
  STDDEV(enso_risk_score),
  MIN(enso_risk_score),
  MAX(enso_risk_score)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE enso_risk_score IS NOT NULL

UNION ALL

SELECT
  'market_breadth_score',
  COUNT(*),
  AVG(market_breadth_score),
  STDDEV(market_breadth_score),
  MIN(market_breadth_score),
  MAX(market_breadth_score)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE market_breadth_score IS NOT NULL;








