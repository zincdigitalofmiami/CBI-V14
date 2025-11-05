-- ============================================
-- CALCULATE MAPE FOR 6M MODEL
-- ============================================

SELECT 
  '6M Model' as model_name,
  COUNT(*) as prediction_count,
  ROUND(AVG(ABS(predicted_target_6m - target_6m) / ABS(target_6m)) * 100, 2) as mape_percent,
  ROUND(AVG(ABS(predicted_target_6m - target_6m)), 4) as mae,
  ROUND(SQRT(AVG(POW(predicted_target_6m - target_6m, 2))), 4) as rmse,
  ROUND(1 - SUM(POW(predicted_target_6m - target_6m, 2)) / SUM(POW(target_6m - (SELECT AVG(target_6m) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL), 2)), 4) as r2_score
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL)
);



