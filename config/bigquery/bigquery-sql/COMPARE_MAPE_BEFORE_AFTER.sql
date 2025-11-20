-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- MAPE COMPARISON: BEFORE vs AFTER TRAINING
-- Compares old models (50 iterations) vs new models (100 iterations)
-- ============================================

WITH before_1w AS (
  SELECT 
    target_1w as actual,
    predicted_target_1w as predicted,
    ABS(target_1w - predicted_target_1w) / ABS(target_1w) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL)
  )
),
before_1m AS (
  SELECT 
    target_1m as actual,
    predicted_target_1m as predicted,
    ABS(target_1m - predicted_target_1m) / ABS(target_1m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL)
  )
),
before_3m AS (
  SELECT 
    target_3m as actual,
    predicted_target_3m as predicted,
    ABS(target_3m - predicted_target_3m) / ABS(target_3m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL)
  )
),
before_6m AS (
  SELECT 
    target_6m as actual,
    predicted_target_6m as predicted,
    ABS(target_6m - predicted_target_6m) / ABS(target_6m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m_all_features`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL)
  )
),
after_1w AS (
  SELECT 
    target_1w as actual,
    predicted_target_1w as predicted,
    ABS(target_1w - predicted_target_1w) / ABS(target_1w) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1w`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1w IS NOT NULL)
  )
),
after_1m AS (
  SELECT 
    target_1m as actual,
    predicted_target_1m as predicted,
    ABS(target_1m - predicted_target_1m) / ABS(target_1m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_1m`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_1m IS NOT NULL)
  )
),
after_3m AS (
  SELECT 
    target_3m as actual,
    predicted_target_3m as predicted,
    ABS(target_3m - predicted_target_3m) / ABS(target_3m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_3m`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_3m IS NOT NULL)
  )
),
after_6m AS (
  SELECT 
    target_6m as actual,
    predicted_target_6m as predicted,
    ABS(target_6m - predicted_target_6m) / ABS(target_6m) * 100 as ape
  FROM ML.PREDICT(MODEL `cbi-v14.models_v4.bqml_6m`,
    (SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE target_6m IS NOT NULL)
  )
),
before_metrics AS (
  SELECT '1W' as horizon, ROUND(AVG(ape), 2) as mape, COUNT(*) as n_samples, AVG(ABS(actual - predicted)) as mae FROM before_1w
  UNION ALL
  SELECT '1M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM before_1m
  UNION ALL
  SELECT '3M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM before_3m
  UNION ALL
  SELECT '6M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM before_6m
),
after_metrics AS (
  SELECT '1W' as horizon, ROUND(AVG(ape), 2) as mape, COUNT(*) as n_samples, AVG(ABS(actual - predicted)) as mae FROM after_1w
  UNION ALL
  SELECT '1M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM after_1m
  UNION ALL
  SELECT '3M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM after_3m
  UNION ALL
  SELECT '6M', ROUND(AVG(ape), 2), COUNT(*), AVG(ABS(actual - predicted)) FROM after_6m
)
SELECT 
  b.horizon,
  b.mape as mape_before,
  a.mape as mape_after,
  ROUND(a.mape - b.mape, 2) as mape_change,
  CASE 
    WHEN a.mape < b.mape THEN '✅ IMPROVED'
    WHEN a.mape > b.mape THEN '⚠️ DEGRADED'
    ELSE '➡️ SAME'
  END as status,
  b.mae as mae_before,
  a.mae as mae_after,
  ROUND((a.mae - b.mae) / b.mae * 100, 2) as mae_change_pct,
  b.n_samples as samples_before,
  a.n_samples as samples_after
FROM before_metrics b
JOIN after_metrics a ON b.horizon = a.horizon
ORDER BY b.horizon;
