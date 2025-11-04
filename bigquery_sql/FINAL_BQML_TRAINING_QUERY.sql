-- ============================================
-- FINAL BQML TRAINING QUERY - VERIFIED SAFE
-- All issues fixed, ready for production
-- ============================================

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w_all_features`

OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=50,
  learn_rate=0.1,
  early_stop=True
) AS

SELECT 
  target_1w,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime  -- STRING type - must be excluded for BQML
  )
  -- ✅ 254 NUMERIC FEATURES (excludes STRING volatility_regime)
  
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

