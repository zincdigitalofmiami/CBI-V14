-- ============================================
-- UPDATE VIX STRESS TO ACTUAL VIX PRICE
-- Change feature_vix_stress from VIX/20 stress score to actual VIX price
-- ============================================

-- Update existing feature_vix_stress values to use actual VIX price
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET feature_vix_stress = v.close
FROM `cbi-v14.forecasting_data_warehouse.vix_daily` v
WHERE t.date = v.date
  AND t.feature_vix_stress IS NOT NULL;  -- Only update existing populated values

-- Verify the update
SELECT
  'VIX Update Results' as check_type,
  COUNTIF(feature_vix_stress IS NOT NULL) as populated_count,
  ROUND(AVG(feature_vix_stress), 2) as avg_vix,
  MIN(feature_vix_stress) as min_vix,
  MAX(feature_vix_stress) as max_vix
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE feature_vix_stress IS NOT NULL;

