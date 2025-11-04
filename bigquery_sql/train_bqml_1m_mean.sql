-- ============================================
-- 1-MONTH MODEL TRAINING
-- ============================================
-- First drop if exists to avoid concurrent update errors
DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1m_mean`;

CREATE MODEL `cbi-v14.models_v4.bqml_1m_mean`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  
  -- HYPERPARAMETER TUNING (Optimized)
  num_trials=30,                           -- Number of hyperparameter combinations to test
  MAX_PARALLEL_TRIALS=5,                   -- ⚡ Run 5 trials in parallel (max allowed: 5)
  -- OPTIMIZATION_STRATEGY removed - not supported for BOOSTED_TREE_REGRESSOR
  
  -- HYPERPARAMETER RANGES (Optimized for small dataset)
  learn_rate=HPARAM_RANGE(0.01, 0.2),
  max_tree_depth=HPARAM_CANDIDATES([3, 5, 7]), -- ⚠️ Reduced to prevent overfitting on small dataset
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 5),               -- ⚠️ Increased upper bound to encourage feature sparsity
  l2_reg=HPARAM_RANGE(0, 1),
  num_parallel_tree=HPARAM_CANDIDATES([10, 15, 20]),
  
  -- TRAINING SETTINGS
  max_iterations=200,                      -- Maximum iterations per trial
  early_stop=TRUE,                         -- Stop if validation performance doesn't improve
  MIN_REL_PROGRESS=0.001,                  -- ⚡ Stop if improvement < 0.1% (prevents wasted computation)
  
  -- OPTIMIZATION_OBJECTIVE removed - not supported for BOOSTED_TREE_REGRESSOR (always minimizes RMSE)
  
  -- ANALYSIS
  enable_global_explain=TRUE,              -- Feature importance for analysis
  
  -- DATA SPLIT
  data_split_method='CUSTOM',             -- Manual train/val split
  data_split_col='data_split'             -- Split column: 'TRAIN' or 'EVAL' (STRING required)
) AS
SELECT 
  * EXCEPT(
    date, 
    treasury_10y_yield, 
    econ_unemployment_rate, 
    news_article_count, 
    news_avg_score,
    -- ALL-NULL COLUMNS (excluded to prevent training errors)
    -- TODO: Backfill these columns with proper data sources
    cpi_yoy,                                -- All NULL - economic data missing
    econ_gdp_growth,                        -- All NULL - economic data missing
    gdp_growth,                             -- All NULL - economic data missing (duplicate)
    soybean_meal_price,                     -- All NULL - market data missing
    unemployment_rate,                      -- All NULL - economic data missing
    us_midwest_conditions_score,            -- All NULL - weather data missing
    us_midwest_drought_days,                -- All NULL - weather data missing
    us_midwest_flood_days,                  -- All NULL - weather data missing
    us_midwest_heat_stress_days,            -- All NULL - weather data missing
    us_midwest_precip_mm,                   -- All NULL - weather data missing
    us_midwest_temp_c,                      -- All NULL - weather data missing
    -- TEMPORAL LEAKAGE FEATURES (exclude from training - not available at prediction time)
    crude_lead1_correlation,
    dxy_lead1_correlation,
    vix_lead1_correlation,
    palm_lead2_correlation,
    leadlag_zl_price,
    lead_signal_confidence,
    days_to_next_event,
    post_event_window,
    event_impact_level,
    event_vol_mult,
    tradewar_event_vol_mult
  ),
  -- ⚠️ OPTIMIZED: Changed to 2024-12-01 for better eval set (17% instead of 2.4%)
  -- Train on past, evaluate on future (correct time-series validation)
  IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split
FROM `cbi-v14.models_v4.train_1m`  -- USE EXISTING VIEW - already excludes other targets
WHERE target_1m IS NOT NULL;

