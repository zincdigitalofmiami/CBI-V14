-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CALCULATE MAPE FOR CURRENT AND COMPARE WITH FIRST TRAINING
-- ============================================

-- Current Model MAPE Calculation
WITH current_predictions AS (
  SELECT 
    target_1w,
    predicted_target_1w
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
    (
      SELECT 
        target_1w,
        * EXCEPT(
          target_1w, 
          target_1m, 
          target_3m, 
          target_6m, 
          date,
          volatility_regime,
          social_sentiment_volatility,
          bullish_ratio,
          bearish_ratio,
          social_sentiment_7d,
          social_volume_7d,
          trump_policy_7d,
          trump_events_7d,
          news_intelligence_7d,
          news_volume_7d
        )
      FROM `cbi-v14.models_v4.training_dataset_super_enriched`
      WHERE target_1w IS NOT NULL
    )
  )
),
current_metrics AS (
  SELECT 
    'CURRENT TRAINING (276 features)' as model_name,
    COUNT(*) as prediction_count,
    ROUND(AVG(ABS((target_1w - predicted_target_1w) / NULLIF(ABS(target_1w), 0)) * 100), 2) as mape_percent,
    ROUND(AVG(ABS(target_1w - predicted_target_1w)), 4) as mae,
    ROUND(SQRT(AVG(POW(target_1w - predicted_target_1w, 2))), 4) as rmse,
    ROUND(
      1 - SUM(POW(target_1w - predicted_target_1w, 2)) / 
      NULLIF(SUM(POW(target_1w - (SELECT AVG(target_1w) FROM current_predictions), 2)), 0),
      4
    ) as r2_score
  FROM current_predictions
  WHERE ABS(target_1w) > 0.01
)

SELECT * FROM current_metrics

UNION ALL

SELECT 
  'FIRST TRAINING (Vertex AI 1W)' as model_name,
  0 as prediction_count,
  2.02 as mape_percent,
  1.008 as mae,
  NULL as rmse,
  0.9836 as r2_score;



