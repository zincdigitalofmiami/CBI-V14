-- ============================================
-- GET REAL MAPE FOR ALL MODELS
-- Manual calculation to verify
-- ============================================

WITH predictions_1w AS (
  SELECT 
    target_1w as actual_target,
    predicted_target_1w as predicted_target,
    ABS(target_1w - predicted_target_1w) / ABS(target_1w) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL)
  )
),
predictions_1m AS (
  SELECT 
    target_1m as actual_target,
    predicted_target_1m as predicted_target,
    ABS(target_1m - predicted_target_1m) / ABS(target_1m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL)
  )
),
predictions_3m AS (
  SELECT 
    target_3m as actual_target,
    predicted_target_3m as predicted_target,
    ABS(target_3m - predicted_target_3m) / ABS(target_3m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL)
  )
),
predictions_6m AS (
  SELECT 
    target_6m as actual_target,
    predicted_target_6m as predicted_target,
    ABS(target_6m - predicted_target_6m) / ABS(target_6m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL)
  )
)
SELECT 
  '1W Model' as model_name,
  ROUND(AVG(ape), 2) as true_mape_percent,
  COUNT(*) as prediction_count
FROM predictions_1w
UNION ALL
SELECT 
  '1M Model',
  ROUND(AVG(ape), 2),
  COUNT(*)
FROM predictions_1m
UNION ALL
SELECT 
  '3M Model',
  ROUND(AVG(ape), 2),
  COUNT(*)
FROM predictions_3m
UNION ALL
SELECT 
  '6M Model',
  ROUND(AVG(ape), 2),
  COUNT(*)
FROM predictions_6m
ORDER BY model_name;



