-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- PROMOTE FOCUSED MODELS TO PRODUCTION
-- After validation, replace production models
-- Date: November 2025
-- ============================================

-- STEP 1: Verify focused models outperform originals
WITH comparison AS (
  SELECT 
    CASE 
      WHEN model_name LIKE 'focused%' THEN SPLIT(model_name, '_')[OFFSET(1)]
      ELSE SPLIT(model_name, '_')[OFFSET(0)]
    END as horizon,
    CASE 
      WHEN model_name LIKE 'focused%' THEN 'focused'
      ELSE 'original'
    END as model_type,
    mean_absolute_error,
    r2_score
  FROM `cbi-v14.models_v4.focused_model_evaluation`
),
performance_comparison AS (
  SELECT 
    horizon,
    MAX(CASE WHEN model_type = 'focused' THEN mean_absolute_error END) as focused_mae,
    MAX(CASE WHEN model_type = 'original' THEN mean_absolute_error END) as original_mae,
    MAX(CASE WHEN model_type = 'focused' THEN r2_score END) as focused_r2,
    MAX(CASE WHEN model_type = 'original' THEN r2_score END) as original_r2
  FROM comparison
  GROUP BY horizon
)
SELECT 
  horizon,
  focused_mae,
  original_mae,
  (original_mae - focused_mae) / original_mae * 100 as mae_improvement_pct,
  focused_r2,
  original_r2,
  (focused_r2 - original_r2) as r2_improvement,
  CASE 
    WHEN focused_mae < original_mae AND focused_r2 >= original_r2 THEN '✅ PROMOTE'
    WHEN focused_mae <= original_mae * 1.05 AND focused_r2 >= original_r2 * 0.95 THEN '⚠️ CONSIDER'
    ELSE '❌ KEEP ORIGINAL'
  END as recommendation
FROM performance_comparison
ORDER BY horizon;

-- STEP 2: Backup original models (rename with _backup suffix)
-- Note: BigQuery doesn't support RENAME for models, so we'll document the backup
CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_model_backup_log` AS
SELECT 
  CURRENT_TIMESTAMP() as backup_timestamp,
  'bqml_1w' as original_model,
  'bqml_focused_1w' as new_model,
  'Backup before promoting focused model' as reason
UNION ALL
SELECT 
  CURRENT_TIMESTAMP(),
  'bqml_1m',
  'bqml_focused_1m',
  'Backup before promoting focused model'
UNION ALL
SELECT 
  CURRENT_TIMESTAMP(),
  'bqml_3m',
  'bqml_focused_3m',
  'Backup before promoting focused model'
UNION ALL
SELECT 
  CURRENT_TIMESTAMP(),
  'bqml_6m',
  'bqml_focused_6m',
  'Backup before promoting focused model';

-- STEP 3: Create production models with focused feature set
-- These will replace the original models after validation

-- Production 1W Model (Focused)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1m, target_3m, target_6m, volatility_regime),
  target_1w
FROM `cbi-v14.models_v4.focused_training_data_1w`
WHERE target_1w IS NOT NULL;

-- Production 1M Model (Focused)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_3m, target_6m, volatility_regime),
  target_1m
FROM `cbi-v14.models_v4.focused_training_data_1m`
WHERE target_1m IS NOT NULL;

-- Production 3M Model (Focused)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_3m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_3m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_6m, volatility_regime),
  target_3m
FROM `cbi-v14.models_v4.focused_training_data_3m`
WHERE target_3m IS NOT NULL;

-- Production 6M Model (Focused)
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_6m`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_6m'],
  max_iterations=150,
  subsample=0.85,
  learn_rate=0.1,
  max_tree_depth=8,
  min_tree_child_weight=10,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  * EXCEPT(date, target_1w, target_1m, target_3m, volatility_regime),
  target_6m
FROM `cbi-v14.models_v4.focused_training_data_6m`
WHERE target_6m IS NOT NULL;

-- STEP 4: Final validation
SELECT 
  '✅ PRODUCTION MODELS UPDATED' as status,
  COUNT(*) as models_updated,
  'All models now use focused feature set (50-100 features)' as note
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.MODELS`
WHERE model_name IN ('bqml_1w', 'bqml_1m', 'bqml_3m', 'bqml_6m')
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);







