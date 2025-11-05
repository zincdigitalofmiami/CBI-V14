-- ============================================
-- VERIFY ALL MODELS USE IDENTICAL FEATURES
-- ============================================

WITH 
-- Get all numeric columns from training dataset
all_numeric_columns AS (
  SELECT column_name
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
    AND data_type IN ('FLOAT64', 'INT64')
    AND column_name NOT IN ('target_1w', 'target_1m', 'target_3m', 'target_6m')
),

-- Columns that should be excluded (same for all models)
excluded_columns AS (
  SELECT column_name FROM UNNEST([
    'date',
    'volatility_regime',
    'social_sentiment_volatility',
    'news_article_count',
    'news_avg_score',
    'news_sentiment_avg',
    'china_news_count',
    'biofuel_news_count',
    'tariff_news_count',
    'weather_news_count',
    'news_intelligence_7d',
    'news_volume_7d'
  ]) AS column_name
),

-- Calculate included features
included_features AS (
  SELECT 
    anc.column_name,
    CASE 
      WHEN ec.column_name IS NULL THEN 'INCLUDED'
      ELSE 'EXCLUDED'
    END as status
  FROM all_numeric_columns anc
  LEFT JOIN excluded_columns ec ON anc.column_name = ec.column_name
)

SELECT 
  COUNTIF(status = 'INCLUDED') as total_included_features,
  COUNTIF(status = 'EXCLUDED') as total_excluded_features,
  COUNT(*) as total_numeric_features,
  CASE 
    WHEN COUNTIF(status = 'INCLUDED') = 274 THEN '✅ CORRECT - 274 FEATURES'
    ELSE '❌ ERROR - WRONG FEATURE COUNT'
  END as verification_status
FROM included_features;



