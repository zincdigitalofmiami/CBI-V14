-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- A/B TEST: 40 Iterations vs 100 Iterations
-- ============================================
-- This script creates a test model with 40 iterations and compares
-- predictions side-by-side with the existing 100-iteration model

-- Step 1: Create test model with 40 iterations
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1w_test_40iter`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  max_iterations=40,
  early_stop=TRUE,
  min_rel_progress=0.005,
  learn_rate=0.1,
  subsample=0.8,
  max_tree_depth=6
) AS
SELECT 
  target_1w,
  * EXCEPT(
    target_1w, 
    target_1m, 
    target_3m, 
    target_6m, 
    date,
    volatility_regime,
    social_sentiment_volatility,
    bullish_ratio,
    bearish_ratio,
    social_sentiment_7d,
    social_volume_7d,
    trump_policy_7d,
    trump_events_7d,
    news_intelligence_7d,
    news_volume_7d
  )
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- Step 2: Wait for training to complete, then run this comparison query
-- Get latest row for prediction
WITH latest_row AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
),
iter_40_pred AS (
  SELECT predicted_target_1w as pred_40
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1w_test_40iter`,
    (SELECT * FROM latest_row)
  )
),
iter_100_pred AS (
  SELECT predicted_target_1w as pred_100
  FROM ML.PREDICT(
    MODEL `cbi-v14.models_v4.bqml_1w`,
    (SELECT * FROM latest_row)
  )
)
SELECT 
  49.56 as actual_price_nov_5,
  pred_40,
  pred_100,
  ABS(pred_40 - 49.56) / 49.56 * 100 as mape_40_iter,
  ABS(pred_100 - 49.56) / 49.56 * 100 as mape_100_iter,
  ABS(pred_40 - 49.56) as abs_error_40,
  ABS(pred_100 - 49.56) as abs_error_100,
  CASE 
    WHEN ABS(pred_40 - 49.56) < ABS(pred_100 - 49.56) THEN '40 iterations wins'
    WHEN ABS(pred_40 - 49.56) > ABS(pred_100 - 49.56) THEN '100 iterations wins'
    ELSE 'Tie'
  END as winner,
  -- Calculate improvement
  ROUND((ABS(pred_100 - 49.56) - ABS(pred_40 - 49.56)) / ABS(pred_100 - 49.56) * 100, 2) as improvement_pct
FROM iter_40_pred, iter_100_pred;

-- Step 3: Compare training info (overfit ratios)
-- Run this after both models are trained
SELECT 
  '40 iterations' as model_version,
  iteration,
  loss as training_loss,
  eval_loss as evaluation_loss,
  ROUND(eval_loss / NULLIF(loss, 0), 2) as overfit_ratio
FROM ML.TRAINING_INFO(MODEL `cbi-v14.models_v4.bqml_1w_test_40iter`)
WHERE iteration IN (10, 20, 30, 40)
ORDER BY iteration

UNION ALL

SELECT 
  '100 iterations' as model_version,
  iteration,
  loss as training_loss,
  eval_loss as evaluation_loss,
  ROUND(eval_loss / NULLIF(loss, 0), 2) as overfit_ratio
FROM ML.TRAINING_INFO(MODEL `cbi-v14.models_v4.bqml_1w`)
WHERE iteration IN (10, 20, 30, 40)
ORDER BY iteration;

-- Step 4: Evaluate both models on validation set (last 30 days)
-- Note: This requires train_1w view to be fixed
SELECT 
  '40 iterations' as model_version,
  *
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1w_test_40iter`,
  (SELECT * FROM `cbi-v14.models_v4.train_1w` 
   WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
     AND target_1w IS NOT NULL)
)

UNION ALL

SELECT 
  '100 iterations' as model_version,
  *
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1w`,
  (SELECT * FROM `cbi-v14.models_v4.train_1w` 
   WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
     AND target_1w IS NOT NULL)
);








