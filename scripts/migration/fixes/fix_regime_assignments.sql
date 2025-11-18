-- Fix Regime Assignments in Training Tables
-- Date: November 17, 2025
-- Purpose: Fix 'allhistory' placeholders and properly assign regimes with weights
-- Issue: zl_training_prod_allhistory_1m has ALL rows with regime='allhistory' and weight=1

-- ============================================================
-- CRITICAL FIX: Update regime assignments from regime_calendar
-- ============================================================

-- Fix zl_training_prod_allhistory_1m (MOST CRITICAL - 100% placeholders)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Fix zl_training_prod_allhistory_1w
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1w` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Fix zl_training_prod_allhistory_3m
UPDATE `cbi-v14.training.zl_training_prod_allhistory_3m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Fix zl_training_prod_allhistory_6m
UPDATE `cbi-v14.training.zl_training_prod_allhistory_6m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Fix zl_training_prod_allhistory_12m
UPDATE `cbi-v14.training.zl_training_prod_allhistory_12m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- Fix FULL surface tables
UPDATE `cbi-v14.training.zl_training_full_allhistory_1m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_full_allhistory_1w` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_full_allhistory_3m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_full_allhistory_6m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_full_allhistory_12m` t
SET 
  market_regime = COALESCE(rc.regime, 'unknown'),
  training_weight = CAST(COALESCE(rw.weight, 100) AS INT64)
FROM `cbi-v14.training.regime_calendar` rc
LEFT JOIN `cbi-v14.training.regime_weights` rw
  ON rc.regime = rw.regime
WHERE t.date = rc.date;

-- ============================================================
-- VERIFICATION: Check regime distribution after updates
-- ============================================================

-- Verify prod_allhistory_1m (was 100% 'allhistory')
SELECT 
  market_regime,
  COUNT(*) as row_count,
  MIN(training_weight) as min_weight,
  MAX(training_weight) as max_weight,
  AVG(training_weight) as avg_weight
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
GROUP BY market_regime
ORDER BY row_count DESC;

-- Verify all prod tables
WITH regime_summary AS (
  SELECT 
    'prod_1w' as table_name,
    market_regime,
    COUNT(*) as row_count,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
  GROUP BY market_regime
  
  UNION ALL
  
  SELECT 
    'prod_1m' as table_name,
    market_regime,
    COUNT(*) as row_count,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  GROUP BY market_regime
  
  UNION ALL
  
  SELECT 
    'prod_3m' as table_name,
    market_regime,
    COUNT(*) as row_count,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_3m`
  GROUP BY market_regime
  
  UNION ALL
  
  SELECT 
    'prod_6m' as table_name,
    market_regime,
    COUNT(*) as row_count,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_6m`
  GROUP BY market_regime
  
  UNION ALL
  
  SELECT 
    'prod_12m' as table_name,
    market_regime,
    COUNT(*) as row_count,
    MIN(training_weight) as min_weight,
    MAX(training_weight) as max_weight
  FROM `cbi-v14.training.zl_training_prod_allhistory_12m`
  GROUP BY market_regime
)
SELECT 
  table_name,
  COUNT(DISTINCT market_regime) as unique_regimes,
  SUM(row_count) as total_rows,
  STRING_AGG(
    CONCAT(market_regime, '(', CAST(row_count AS STRING), ')'), 
    ', ' 
    ORDER BY row_count DESC
  ) as regime_distribution
FROM regime_summary
GROUP BY table_name
ORDER BY table_name;

-- ============================================================
-- Expected Results After Fix:
-- - 7-11 unique regimes per table
-- - Weight range: 50-5000 (not all 1)
-- - No 'allhistory' placeholder regimes
-- - Proper distribution across regimes
-- ============================================================


