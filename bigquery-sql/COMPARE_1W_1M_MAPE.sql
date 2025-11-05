-- ============================================
-- COMPARE MAPE FOR 1W AND 1M MODELS
-- ============================================

SELECT 
  '1W Model' as model_name,
  COUNT(*) as prediction_count,
  ROUND(AVG(ABS(predicted_target_1w - target_1w) / ABS(target_1w)) * 100, 2) as mape_percent,
  ROUND(AVG(ABS(predicted_target_1w - target_1w)), 4) as mae,
  ROUND(SQRT(AVG(POW(predicted_target_1w - target_1w, 2))), 4) as rmse
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL)
)
UNION ALL
SELECT 
  '1M Model' as model_name,
  COUNT(*) as prediction_count,
  ROUND(AVG(ABS(predicted_target_1m - target_1m) / ABS(target_1m)) * 100, 2) as mape_percent,
  ROUND(AVG(ABS(predicted_target_1m - target_1m)), 4) as mae,
  ROUND(SQRT(AVG(POW(predicted_target_1m - target_1m, 2))), 4) as rmse
FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
  (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL)
)
ORDER BY model_name;



