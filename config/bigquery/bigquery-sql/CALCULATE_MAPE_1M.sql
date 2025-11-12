-- ============================================
-- CALCULATE MAPE FOR 1M MODEL
-- ============================================

SELECT 
  '1M Model' as model_name,
  COUNT(*) as prediction_count,
  ROUND(AVG(ABS(predicted_target_1m - target_1m) / ABS(target_1m)) * 100, 2) as mape_percent,
  ROUND(AVG(ABS(predicted_target_1m - target_1m)), 4) as mae,
  ROUND(SQRT(AVG(POW(predicted_target_1m - target_1m, 2))), 4) as rmse,
  ROUND(1 - SUM(POW(predicted_target_1m - target_1m, 2)) / SUM(POW(target_1m - (SELECT AVG(target_1m) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL), 2)), 4) as r2_score
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL)
);



