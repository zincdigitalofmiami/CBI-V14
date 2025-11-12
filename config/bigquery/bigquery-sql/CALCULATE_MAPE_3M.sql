-- ============================================
-- CALCULATE MAPE FOR 3M MODEL
-- ============================================

SELECT 
  '3M Model' as model_name,
  COUNT(*) as prediction_count,
  ROUND(AVG(ABS(predicted_target_3m - target_3m) / ABS(target_3m)) * 100, 2) as mape_percent,
  ROUND(AVG(ABS(predicted_target_3m - target_3m)), 4) as mae,
  ROUND(SQRT(AVG(POW(predicted_target_3m - target_3m, 2))), 4) as rmse,
  ROUND(1 - SUM(POW(predicted_target_3m - target_3m, 2)) / SUM(POW(target_3m - (SELECT AVG(target_3m) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL), 2)), 4) as r2_score
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL)
);



