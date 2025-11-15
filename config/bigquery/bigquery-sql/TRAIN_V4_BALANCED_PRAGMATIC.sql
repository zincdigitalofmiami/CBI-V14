-- ============================================
-- TRAIN V4 with BALANCED CONFIG on 444 Features
-- Pragmatic approach: Use what we have, optimize hyperparameters
-- ============================================

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v4`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  
  -- ============================================
  -- STANDARD BOOSTER (not DART for stability)
  -- ============================================
  booster_type='GBTREE',
  tree_method='HIST',
  
  -- ============================================
  -- BALANCED REGULARIZATION (not extreme)
  -- ============================================
  l1_reg=1.0,                       -- Moderate feature selection
  l2_reg=0.5,                       -- Balanced Ridge
  min_split_loss=0.01,              -- Minimum gain to split
  
  -- ============================================
  -- TRAINING WITH EARLY STOPPING
  -- ============================================
  max_iterations=200,
  learn_rate=0.08,
  early_stop=TRUE,
  min_rel_progress=0.0005,          -- Stop if improvement < 0.05%
  
  -- ============================================
  -- SAMPLING FOR 444 FEATURES
  -- ============================================
  subsample=0.8,                    -- 80% of rows per tree
  colsample_bytree=0.7,             -- 70% of features (not 60%)
  num_parallel_tree=3,              -- Ensemble boost
  
  -- ============================================
  -- TREE STRUCTURE
  -- ============================================
  max_tree_depth=8,                 -- Deep enough for interactions
  min_tree_child_weight=5,          -- Leaf regularization
  
  -- ============================================
  -- FEATURE IMPORTANCE & VALIDATION
  -- ============================================
  enable_global_explain=TRUE,       -- Get feature importance
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2      -- 20% holdout
) AS

SELECT 
  target_1m,
  * EXCEPT(
    -- Labels
    date, target_1m, target_1w, target_3m, target_6m,
    
    -- 100% NULL columns (from v3 scan)
    adm_analyst_target,
    argentina_port_throughput_teu,
    argentina_vessel_queue_count,
    baltic_dry_index,
    bg_analyst_target,
    bg_beta,
    biofuel_news_count,
    cf_analyst_target,
    china_news_count,
    china_weekly_cancellations_mt,
    dar_analyst_target,
    mos_analyst_target,
    ntr_analyst_target,
    tariff_news_count,
    tsn_analyst_target,
    weather_news_count
  )
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE target_1m IS NOT NULL
  AND date >= '2020-01-01';






