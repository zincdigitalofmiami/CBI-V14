-- ============================================
-- EVALUATE AND COMPARE V2 vs V3 MODELS
-- ============================================

-- 1. Create evaluation dataset (2024-2025 holdout)
CREATE OR REPLACE TABLE `cbi-v14.models_v4.eval_holdout_2024` AS
SELECT 
  date,
  target_1m as actual_price,
  * EXCEPT(
    date, target_1m, target_1w, target_3m, target_6m,
    -- NULL columns
    adm_analyst_target, argentina_port_throughput_teu, argentina_vessel_queue_count,
    baltic_dry_index, bg_analyst_target, bg_beta, biofuel_news_count,
    cf_analyst_target, china_news_count, china_weekly_cancellations_mt,
    dar_analyst_target, mos_analyst_target, ntr_analyst_target,
    tariff_news_count, tsn_analyst_target, weather_news_count
  )
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date >= '2024-01-01'
  AND target_1m IS NOT NULL;

-- 2. Generate predictions from both models
CREATE OR REPLACE TABLE `cbi-v14.models_v4.predictions_comparison` AS
WITH 
v2_predictions AS (
  SELECT 
    date,
    actual_price,
    predicted_target_1m as v2_prediction
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_v2`,
    TABLE `cbi-v14.models_v4.eval_holdout_2024`
  )
),
v3_predictions AS (
  SELECT 
    date,
    actual_price,
    predicted_target_1m as v3_prediction
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1m_v3`,
    TABLE `cbi-v14.models_v4.eval_holdout_2024`
  )
)
SELECT 
  COALESCE(v2.date, v3.date) as date,
  COALESCE(v2.actual_price, v3.actual_price) as actual_price,
  v2.v2_prediction,
  v3.v3_prediction,
  ABS(v2.actual_price - v2.v2_prediction) as v2_error,
  ABS(v3.actual_price - v3.v3_prediction) as v3_error,
  -- Improvement calculation
  CASE 
    WHEN ABS(v2.actual_price - v2.v2_prediction) > 0 THEN
      ROUND(100.0 * (ABS(v2.actual_price - v2.v2_prediction) - ABS(v3.actual_price - v3.v3_prediction)) / 
            ABS(v2.actual_price - v2.v2_prediction), 2)
    ELSE NULL
  END as v3_improvement_pct
FROM v2_predictions v2
FULL OUTER JOIN v3_predictions v3
  ON v2.date = v3.date;

-- 3. Calculate comprehensive metrics
WITH metrics AS (
  SELECT 
    'v2' as model,
    COUNT(*) as predictions,
    ROUND(AVG(v2_error), 4) as mae,
    ROUND(SQRT(AVG(POWER(v2_error, 2))), 4) as rmse,
    ROUND(STDDEV(v2_error), 4) as error_std,
    ROUND(MIN(v2_error), 4) as min_error,
    ROUND(MAX(v2_error), 4) as max_error,
    ROUND(APPROX_QUANTILES(v2_error, 100)[OFFSET(50)], 4) as median_error,
    ROUND(CORR(actual_price, v2_prediction), 6) as correlation
  FROM `cbi-v14.models_v4.predictions_comparison`
  
  UNION ALL
  
  SELECT 
    'v3' as model,
    COUNT(*) as predictions,
    ROUND(AVG(v3_error), 4) as mae,
    ROUND(SQRT(AVG(POWER(v3_error, 2))), 4) as rmse,
    ROUND(STDDEV(v3_error), 4) as error_std,
    ROUND(MIN(v3_error), 4) as min_error,
    ROUND(MAX(v3_error), 4) as max_error,
    ROUND(APPROX_QUANTILES(v3_error, 100)[OFFSET(50)], 4) as median_error,
    ROUND(CORR(actual_price, v3_prediction), 6) as correlation
  FROM `cbi-v14.models_v4.predictions_comparison`
)
SELECT 
  *,
  -- Calculate improvement
  CASE 
    WHEN model = 'v3' THEN 
      ROUND(100.0 * (
        (SELECT mae FROM metrics WHERE model = 'v2') - mae
      ) / (SELECT mae FROM metrics WHERE model = 'v2'), 2)
    ELSE NULL
  END as improvement_pct
FROM metrics
ORDER BY model;

-- 4. Feature importance from v3 (if DART included it)
SELECT 
  'Top 20 Features in V3' as analysis,
  feature,
  importance_weight,
  importance_gain,
  importance_cover
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.bqml_1m_v3`)
ORDER BY importance_gain DESC
LIMIT 20;





