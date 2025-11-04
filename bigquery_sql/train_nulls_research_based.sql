-- ============================================
-- TRAINING WITH NULL HANDLING - RESEARCH-BASED APPROACH
-- Use CTE to preprocess NULLs with sentinel values
-- Tree models treat sentinel values as distinct categories
-- ============================================

DROP MODEL IF EXISTS `cbi-v14.models_v4.bqml_1w_nulls_research`;

CREATE MODEL `cbi-v14.models_v4.bqml_1w_nulls_research`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w'],
  num_trials=25,
  MAX_PARALLEL_TRIALS=5,
  learn_rate=HPARAM_RANGE(0.01, 0.3),
  max_tree_depth=HPARAM_CANDIDATES([4, 5, 6, 8]),
  subsample=HPARAM_RANGE(0.7, 1.0),
  l1_reg=HPARAM_RANGE(0, 10),
  l2_reg=HPARAM_RANGE(0, 5),
  num_parallel_tree=HPARAM_CANDIDATES([15, 20, 25]),
  max_iterations=120,
  early_stop=TRUE,
  MIN_REL_PROGRESS=0.005,
  enable_global_explain=TRUE,
  data_split_method='CUSTOM',
  data_split_col='data_split'
) AS
WITH null_handled_data AS (
  SELECT
    -- Handle entirely NULL columns with sentinel values
    -- These preserve "data not available" information
    CASE WHEN treasury_10y_yield IS NULL THEN -9999.0 ELSE treasury_10y_yield END as treasury_10y_yield,
    CASE WHEN econ_gdp_growth IS NULL THEN -9999.0 ELSE econ_gdp_growth END as econ_gdp_growth,
    CASE WHEN econ_unemployment_rate IS NULL THEN -9999.0 ELSE econ_unemployment_rate END as econ_unemployment_rate,
    CASE WHEN news_article_count IS NULL THEN -1.0 ELSE news_article_count END as news_article_count,
    CASE WHEN news_avg_score IS NULL THEN -1.0 ELSE news_avg_score END as news_avg_score,
    CASE WHEN us_midwest_temp_c IS NULL THEN -9999.0 ELSE us_midwest_temp_c END as us_midwest_temp_c,
    CASE WHEN brazil_temp_c IS NULL THEN -9999.0 ELSE brazil_temp_c END as brazil_temp_c,
    CASE WHEN argentina_temp_c IS NULL THEN -9999.0 ELSE argentina_temp_c END as argentina_temp_c,

    -- Keep all other features unchanged
    * EXCEPT(
      date, target_1w,
      treasury_10y_yield, econ_gdp_growth, econ_unemployment_rate,
      news_article_count, news_avg_score,
      us_midwest_temp_c, brazil_temp_c, argentina_temp_c
    ),

    -- Target and data split
    target_1w,
    IF(date < '2024-12-01', 'TRAIN', 'EVAL') AS data_split

  FROM `cbi-v14.models_v4.train_1w`
  WHERE target_1w IS NOT NULL
)
SELECT * FROM null_handled_data;

SELECT 'Training completed with research-based NULL handling!' as status;

