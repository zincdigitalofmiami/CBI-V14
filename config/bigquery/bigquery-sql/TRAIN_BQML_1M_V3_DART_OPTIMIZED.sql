-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- TRAIN bqml_1m_v3 with DART + Extreme L1
-- 444 features → Let BQML select top 200-300
-- ============================================

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_v3`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  
  -- ============================================
  -- DART CONFIGURATION (per your recommendation)
  -- ============================================
  booster_type='DART',              -- Dropout Additive Regression Trees
  tree_method='HIST',               -- Histogram-based for 400+ features
  
  -- ============================================
  -- TRAINING ITERATIONS
  -- ============================================
  max_iterations=150,               -- More trees for complex patterns
  learn_rate=0.05,                  -- Slower learning = better convergence
  early_stop=FALSE,                 -- Run full iterations
  
  -- ============================================
  -- EXTREME REGULARIZATION (as requested)
  -- ============================================
  l1_reg=15.0,                      -- EXTREME Lasso (was 0.1 in v2)
  l2_reg=0.15,                      -- Modest Ridge
  min_split_loss=0.02,              -- Prevent tiny splits
  
  -- ============================================
  -- TREE STRUCTURE
  -- ============================================
  max_tree_depth=10,                -- Deep trees for interactions
  min_tree_child_weight=5,          -- Leaf regularization
  
  -- ============================================
  -- SAMPLING (per your 0.6 suggestion)
  -- ============================================
  subsample=0.8,                    -- 80% of rows per tree
  colsample_bytree=0.6,             -- 60% of features (your suggestion)
  num_parallel_tree=3,              -- Ensemble within ensemble
  
  -- ============================================
  -- VALIDATION
  -- ============================================
  data_split_method='RANDOM',
  data_split_eval_fraction=0.2      -- 20% holdout
) AS

-- ============================================
-- SELECT with 444 columns minus 16 NULLs = 428 features
-- ============================================
SELECT 
  target_1m,
  * EXCEPT(
    -- Label and metadata
    date, target_1m, target_1w, target_3m, target_6m,
    
    -- 100% NULL columns from scan
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
  
-- Expected: 
-- Features: 444 - 16 NULL - 6 metadata = 422 features
-- With L1=15.0, BQML will select ~200-300 most important
