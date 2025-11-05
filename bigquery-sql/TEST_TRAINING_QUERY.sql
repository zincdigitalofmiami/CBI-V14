-- ============================================
-- TEST EXACT TRAINING QUERY - NO ERRORS
-- ============================================

-- Test that the exact query we'll use for training works
SELECT 
  target_1w,
  * EXCEPT(target_1w, target_1m, target_3m, target_6m, date)
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
LIMIT 10;



