-- ============================================
-- GET REAL MAPE FOR ALL MODELS
-- Using ML.EVALUATE (official BQML method)
-- ============================================

SELECT 
  '1W Model' as model_name,
  ROUND(mean_absolute_percentage_error * 100, 2) as mape_percent,
  mean_absolute_error as mae,
  root_mean_squared_error as rmse,
  r2_score
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL),
  STRUCT('target_1w' AS input_label_cols[SAFE_OFFSET(0)])
)
UNION ALL
SELECT 
  '1M Model',
  ROUND(mean_absolute_percentage_error * 100, 2),
  mean_absolute_error,
  root_mean_squared_error,
  r2_score
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL),
  STRUCT('target_1m' AS input_label_cols[SAFE_OFFSET(0)])
)
UNION ALL
SELECT 
  '3M Model',
  ROUND(mean_absolute_percentage_error * 100, 2),
  mean_absolute_error,
  root_mean_squared_error,
  r2_score
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_3m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL),
  STRUCT('target_3m' AS input_label_cols[SAFE_OFFSET(0)])
)
UNION ALL
SELECT 
  '6M Model',
  ROUND(mean_absolute_percentage_error * 100, 2),
  mean_absolute_error,
  root_mean_squared_error,
  r2_score
FROM ML.EVALUATE(MODEL `cbi-v14.models_v4.bqml_6m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL),
  STRUCT('target_6m' AS input_label_cols[SAFE_OFFSET(0)])
)
ORDER BY model_name;


