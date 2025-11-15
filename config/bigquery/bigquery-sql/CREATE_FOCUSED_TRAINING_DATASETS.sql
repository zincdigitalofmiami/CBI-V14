-- ============================================
-- CREATE FOCUSED TRAINING DATASETS (50-100 Features)
-- Optimized training sets for faster iteration
-- Date: November 2025
-- ============================================

-- STEP 1: Create focused training dataset for 1W
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_training_data_1w` AS
WITH feature_list AS (
  SELECT feature 
  FROM `cbi-v14.models_v4.rich_focused_feature_list_final`
  WHERE available_1w = TRUE
),
feature_array AS (
  SELECT ARRAY_AGG(feature ORDER BY feature) as features
  FROM feature_list
)
SELECT 
  date,
  target_1w,
  -- Dynamically select only focused features
  -- For now, we'll use a static list - will be generated dynamically in Python
  zl_price_current,
  zl_price_lag1,
  zl_price_lag7,
  return_1d,
  return_7d,
  ma_7d,
  ma_30d,
  crush_margin,
  china_soybean_imports_mt,
  dollar_index,
  fed_funds_rate,
  crude_price,
  palm_price,
  vix_level,
  feature_vix_stress,
  feature_tariff_threat,
  feature_biofuel_cascade,
  feature_china_relations,
  -- Add top 50 from importance ranking
  -- (This will be expanded based on focused_feature_list_final)
  COALESCE(crush_margin_30d_ma, 0) as crush_margin_30d_ma,
  COALESCE(crush_margin_7d_ma, 0) as crush_margin_7d_ma,
  COALESCE(china_imports_from_us_mt, 0) as china_imports_from_us_mt,
  COALESCE(china_weekly_cancellations_mt, 0) as china_weekly_cancellations_mt,
  COALESCE(usd_cny_rate, 0) as usd_cny_rate,
  COALESCE(usd_brl_rate, 0) as usd_brl_rate,
  COALESCE(dollar_index_7d_change, 0) as dollar_index_7d_change,
  COALESCE(real_yield, 0) as real_yield,
  COALESCE(treasury_10y_yield, 0) as treasury_10y_yield,
  COALESCE(yield_curve, 0) as yield_curve,
  COALESCE(trade_war_intensity, 0) as trade_war_intensity,
  COALESCE(china_tariff_rate, 0) as china_tariff_rate,
  COALESCE(trump_policy_events, 0) as trump_policy_events,
  COALESCE(feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
  COALESCE(wti_7d_change, 0) as wti_7d_change,
  COALESCE(palm_spread, 0) as palm_spread,
  COALESCE(vix_lag1, 0) as vix_lag1,
  COALESCE(vix_lag2, 0) as vix_lag2,
  COALESCE(volatility_30d, 0) as volatility_30d,
  COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
  COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
  COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
  COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
  COALESCE(feature_harvest_pace, 0) as feature_harvest_pace,
  COALESCE(feature_geopolitical_volatility, 0) as feature_geopolitical_volatility,
  COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
  COALESCE(big8_composite_score, 0) as big8_composite_score,
  COALESCE(volatility_regime, 'normal') as volatility_regime
FROM `cbi-v14.training.zl_training_prod_allhistory_1w`
WHERE target_1w IS NOT NULL
  AND date >= '2023-01-01'
  AND zl_price_current > 0;

-- STEP 2: Create focused training dataset for 1M
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_training_data_1m` AS
SELECT 
  date,
  target_1m,
  -- Same feature set as 1W
  zl_price_current,
  zl_price_lag1,
  zl_price_lag7,
  return_1d,
  return_7d,
  ma_7d,
  ma_30d,
  crush_margin,
  china_soybean_imports_mt,
  dollar_index,
  fed_funds_rate,
  crude_price,
  palm_price,
  vix_level,
  feature_vix_stress,
  feature_tariff_threat,
  feature_biofuel_cascade,
  feature_china_relations,
  COALESCE(crush_margin_30d_ma, 0) as crush_margin_30d_ma,
  COALESCE(crush_margin_7d_ma, 0) as crush_margin_7d_ma,
  COALESCE(china_imports_from_us_mt, 0) as china_imports_from_us_mt,
  COALESCE(china_weekly_cancellations_mt, 0) as china_weekly_cancellations_mt,
  COALESCE(usd_cny_rate, 0) as usd_cny_rate,
  COALESCE(usd_brl_rate, 0) as usd_brl_rate,
  COALESCE(dollar_index_7d_change, 0) as dollar_index_7d_change,
  COALESCE(real_yield, 0) as real_yield,
  COALESCE(treasury_10y_yield, 0) as treasury_10y_yield,
  COALESCE(yield_curve, 0) as yield_curve,
  COALESCE(trade_war_intensity, 0) as trade_war_intensity,
  COALESCE(china_tariff_rate, 0) as china_tariff_rate,
  COALESCE(trump_policy_events, 0) as trump_policy_events,
  COALESCE(feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
  COALESCE(wti_7d_change, 0) as wti_7d_change,
  COALESCE(palm_spread, 0) as palm_spread,
  COALESCE(vix_lag1, 0) as vix_lag1,
  COALESCE(vix_lag2, 0) as vix_lag2,
  COALESCE(volatility_30d, 0) as volatility_30d,
  COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
  COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
  COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
  COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
  COALESCE(feature_harvest_pace, 0) as feature_harvest_pace,
  COALESCE(feature_geopolitical_volatility, 0) as feature_geopolitical_volatility,
  COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
  COALESCE(big8_composite_score, 0) as big8_composite_score,
  COALESCE(volatility_regime, 'normal') as volatility_regime
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE target_1m IS NOT NULL
  AND date >= '2023-01-01'
  AND zl_price_current > 0;

-- STEP 3: Create focused training dataset for 3M
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_training_data_3m` AS
SELECT 
  date,
  target_3m,
  -- Same feature set
  zl_price_current,
  zl_price_lag1,
  zl_price_lag7,
  return_1d,
  return_7d,
  ma_7d,
  ma_30d,
  crush_margin,
  china_soybean_imports_mt,
  dollar_index,
  fed_funds_rate,
  crude_price,
  palm_price,
  vix_level,
  feature_vix_stress,
  feature_tariff_threat,
  feature_biofuel_cascade,
  feature_china_relations,
  COALESCE(crush_margin_30d_ma, 0) as crush_margin_30d_ma,
  COALESCE(crush_margin_7d_ma, 0) as crush_margin_7d_ma,
  COALESCE(china_imports_from_us_mt, 0) as china_imports_from_us_mt,
  COALESCE(china_weekly_cancellations_mt, 0) as china_weekly_cancellations_mt,
  COALESCE(usd_cny_rate, 0) as usd_cny_rate,
  COALESCE(usd_brl_rate, 0) as usd_brl_rate,
  COALESCE(dollar_index_7d_change, 0) as dollar_index_7d_change,
  COALESCE(real_yield, 0) as real_yield,
  COALESCE(treasury_10y_yield, 0) as treasury_10y_yield,
  COALESCE(yield_curve, 0) as yield_curve,
  COALESCE(trade_war_intensity, 0) as trade_war_intensity,
  COALESCE(china_tariff_rate, 0) as china_tariff_rate,
  COALESCE(trump_policy_events, 0) as trump_policy_events,
  COALESCE(feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
  COALESCE(wti_7d_change, 0) as wti_7d_change,
  COALESCE(palm_spread, 0) as palm_spread,
  COALESCE(vix_lag1, 0) as vix_lag1,
  COALESCE(vix_lag2, 0) as vix_lag2,
  COALESCE(volatility_30d, 0) as volatility_30d,
  COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
  COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
  COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
  COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
  COALESCE(feature_harvest_pace, 0) as feature_harvest_pace,
  COALESCE(feature_geopolitical_volatility, 0) as feature_geopolitical_volatility,
  COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
  COALESCE(big8_composite_score, 0) as big8_composite_score,
  COALESCE(volatility_regime, 'normal') as volatility_regime
FROM `cbi-v14.training.zl_training_prod_allhistory_3m`
WHERE target_3m IS NOT NULL
  AND date >= '2023-01-01'
  AND zl_price_current > 0;

-- STEP 4: Create focused training dataset for 6M
CREATE OR REPLACE TABLE `cbi-v14.models_v4.focused_training_data_6m` AS
SELECT 
  date,
  target_6m,
  -- Same feature set
  zl_price_current,
  zl_price_lag1,
  zl_price_lag7,
  return_1d,
  return_7d,
  ma_7d,
  ma_30d,
  crush_margin,
  china_soybean_imports_mt,
  dollar_index,
  fed_funds_rate,
  crude_price,
  palm_price,
  vix_level,
  feature_vix_stress,
  feature_tariff_threat,
  feature_biofuel_cascade,
  feature_china_relations,
  COALESCE(crush_margin_30d_ma, 0) as crush_margin_30d_ma,
  COALESCE(crush_margin_7d_ma, 0) as crush_margin_7d_ma,
  COALESCE(china_imports_from_us_mt, 0) as china_imports_from_us_mt,
  COALESCE(china_weekly_cancellations_mt, 0) as china_weekly_cancellations_mt,
  COALESCE(usd_cny_rate, 0) as usd_cny_rate,
  COALESCE(usd_brl_rate, 0) as usd_brl_rate,
  COALESCE(dollar_index_7d_change, 0) as dollar_index_7d_change,
  COALESCE(real_yield, 0) as real_yield,
  COALESCE(treasury_10y_yield, 0) as treasury_10y_yield,
  COALESCE(yield_curve, 0) as yield_curve,
  COALESCE(trade_war_intensity, 0) as trade_war_intensity,
  COALESCE(china_tariff_rate, 0) as china_tariff_rate,
  COALESCE(trump_policy_events, 0) as trump_policy_events,
  COALESCE(feature_biofuel_ethanol, 0) as feature_biofuel_ethanol,
  COALESCE(wti_7d_change, 0) as wti_7d_change,
  COALESCE(palm_spread, 0) as palm_spread,
  COALESCE(vix_lag1, 0) as vix_lag1,
  COALESCE(vix_lag2, 0) as vix_lag2,
  COALESCE(volatility_30d, 0) as volatility_30d,
  COALESCE(corr_zl_vix_7d, 0) as corr_zl_vix_7d,
  COALESCE(corr_zl_vix_30d, 0) as corr_zl_vix_30d,
  COALESCE(corr_zl_palm_7d, 0) as corr_zl_palm_7d,
  COALESCE(corr_zl_crude_7d, 0) as corr_zl_crude_7d,
  COALESCE(feature_harvest_pace, 0) as feature_harvest_pace,
  COALESCE(feature_geopolitical_volatility, 0) as feature_geopolitical_volatility,
  COALESCE(feature_hidden_correlation, 0) as feature_hidden_correlation,
  COALESCE(big8_composite_score, 0) as big8_composite_score,
  COALESCE(volatility_regime, 'normal') as volatility_regime
FROM `cbi-v14.training.zl_training_prod_allhistory_6m`
WHERE target_6m IS NOT NULL
  AND date >= '2023-01-01'
  AND zl_price_current > 0;

-- STEP 5: Summary
SELECT 
  'FOCUSED TRAINING DATASETS CREATED' as status,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.focused_training_data_1w`) as rows_1w,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.focused_training_data_1m`) as rows_1m,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.focused_training_data_3m`) as rows_3m,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.focused_training_data_6m`) as rows_6m,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS` 
   WHERE table_name = 'focused_training_data_1w') as features_count;

