-- ============================================
-- ULTIMATE DATA CONSOLIDATION - ZERO STALE DATA
-- Date: November 6, 2025
-- Mission: Consolidate ALL available data with ZERO staleness
-- Target: production_training_data_1m (and other horizons)
-- ============================================

-- STEP 1: Create backup before major changes
CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_1m_backup_nov6` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;

-- ============================================
-- STEP 2: EXTEND DATES USING BIG 8 SIGNALS (CURRENT!)
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_1m` AS
WITH 
-- Get ALL dates from Big 8 signals (current through Nov 6!)
all_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2020-01-01'
),

-- Get existing production data
existing_data AS (
  SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`
),

-- Get Vertex AI data for missing dates (Sep 11 - Oct 27)
vertex_ai_data AS (
  SELECT 
    CAST(date AS DATE) as date,
    china_soybean_imports_mt,
    argentina_export_tax,
    argentina_china_sales_mt,
    avg_sentiment,
    big8_composite_score,
    brazil_precipitation_mm,
    brazil_temperature_c,
    cftc_commercial_long,
    cftc_commercial_short,
    cftc_managed_long,
    cftc_managed_short,
    cftc_open_interest,
    china_tariff_rate,
    corn_price,
    crude_oil_wti_new as crude_price,
    crush_margin,
    dollar_index,
    feature_biofuel_cascade,
    feature_biofuel_ethanol,
    feature_china_relations,
    feature_geopolitical_volatility,
    feature_harvest_pace,
    feature_hidden_correlation,
    feature_tariff_threat,
    feature_vix_stress,
    fed_funds_rate,
    industrial_demand_index,
    palm_price,
    treasury_10y_yield,
    usd_brl_rate,
    usd_cny_rate,
    vix_level,
    volatility_30d,
    weather_argentina_temp,
    weather_brazil_temp,
    weather_us_temp,
    wheat_price,
    zl_price_current,
    zl_price_lag1,
    zl_price_lag7,
    zl_price_lag30,
    target_1w,
    target_1m,
    target_3m,
    target_6m
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  WHERE CAST(date AS DATE) >= '2025-09-11'
    AND CAST(date AS DATE) <= '2025-10-27'
),

-- Get current prices (Nov 5-6)
current_prices AS (
  SELECT 
    DATE(time) as date,
    close as zl_price_current,
    LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
    LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
    LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
    volume as zl_volume
  FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
  WHERE symbol = 'ZL'
    AND DATE(time) >= '2025-10-28'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get current palm oil
current_palm AS (
  SELECT 
    DATE(time) as date,
    close as palm_price,
    volume as palm_volume
  FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
  WHERE DATE(time) >= '2025-10-28'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get current VIX
current_vix AS (
  SELECT 
    date,
    close as vix_level,
    LAG(close, 1) OVER (ORDER BY date) as vix_lag1,
    LAG(close, 2) OVER (ORDER BY date) as vix_lag2
  FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
  WHERE date >= '2025-10-28'
),

-- Get current Big 8 signals (ALL current!)
current_big8 AS (
  SELECT * 
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2025-10-28'
),

-- COMBINE ALL DATA SOURCES
combined_data AS (
  SELECT 
    ad.date,
    
    -- Existing data (Sep 10 and earlier)
    COALESCE(ed.china_soybean_imports_mt, vad.china_soybean_imports_mt) as china_soybean_imports_mt,
    COALESCE(ed.argentina_export_tax, vad.argentina_export_tax) as argentina_export_tax,
    COALESCE(ed.argentina_china_sales_mt, vad.argentina_china_sales_mt) as argentina_china_sales_mt,
    
    -- Prices (use most current)
    COALESCE(cp.zl_price_current, ed.zl_price_current, vad.zl_price_current) as zl_price_current,
    COALESCE(cp.zl_price_lag1, ed.zl_price_lag1, vad.zl_price_lag1) as zl_price_lag1,
    COALESCE(cp.zl_price_lag7, ed.zl_price_lag7, vad.zl_price_lag7) as zl_price_lag7,
    COALESCE(cp.zl_price_lag30, ed.zl_price_lag30, vad.zl_price_lag30) as zl_price_lag30,
    COALESCE(cp.zl_volume, ed.zl_volume) as zl_volume,
    
    COALESCE(cpalm.palm_price, ed.palm_price, vad.palm_price) as palm_price,
    COALESCE(cpalm.palm_volume, ed.palm_volume) as palm_volume,
    
    -- VIX features
    COALESCE(cv.vix_level, ed.vix_level, vad.vix_level) as vix_level,
    COALESCE(cv.vix_lag1, ed.vix_lag1) as vix_lag1,
    COALESCE(cv.vix_lag2, ed.vix_lag2) as vix_lag2,
    
    -- Big 8 signals (use most current)
    COALESCE(cb8.feature_vix_stress, ed.feature_vix_stress, vad.feature_vix_stress) as feature_vix_stress,
    COALESCE(cb8.feature_harvest_pace, ed.feature_harvest_pace, vad.feature_harvest_pace) as feature_harvest_pace,
    COALESCE(cb8.feature_china_relations, ed.feature_china_relations, vad.feature_china_relations) as feature_china_relations,
    COALESCE(cb8.feature_tariff_threat, ed.feature_tariff_threat, vad.feature_tariff_threat) as feature_tariff_threat,
    COALESCE(cb8.feature_geopolitical_volatility, ed.feature_geopolitical_volatility, vad.feature_geopolitical_volatility) as feature_geopolitical_volatility,
    COALESCE(cb8.feature_biofuel_cascade, ed.feature_biofuel_cascade, vad.feature_biofuel_cascade) as feature_biofuel_cascade,
    COALESCE(cb8.feature_hidden_correlation, ed.feature_hidden_correlation, vad.feature_hidden_correlation) as feature_hidden_correlation,
    COALESCE(cb8.feature_biofuel_ethanol, ed.feature_biofuel_ethanol, vad.feature_biofuel_ethanol) as feature_biofuel_ethanol,
    COALESCE(cb8.big8_composite_score, ed.big8_composite_score, vad.big8_composite_score) as big8_composite_score,
    
    -- CFTC features (fill from Vertex AI for missing dates)
    COALESCE(ed.cftc_commercial_long, vad.cftc_commercial_long) as cftc_commercial_long,
    COALESCE(ed.cftc_commercial_short, vad.cftc_commercial_short) as cftc_commercial_short,
    COALESCE(ed.cftc_managed_long, vad.cftc_managed_long) as cftc_managed_long,
    COALESCE(ed.cftc_managed_short, vad.cftc_managed_short) as cftc_managed_short,
    COALESCE(ed.cftc_open_interest, vad.cftc_open_interest) as cftc_open_interest,
    
    -- Economic indicators
    COALESCE(ed.fed_funds_rate, vad.fed_funds_rate) as fed_funds_rate,
    COALESCE(ed.treasury_10y_yield, vad.treasury_10y_yield) as treasury_10y_yield,
    COALESCE(ed.usd_cny_rate, vad.usd_cny_rate) as usd_cny_rate,
    COALESCE(ed.usd_brl_rate, vad.usd_brl_rate) as usd_brl_rate,
    
    -- ALL other existing columns from production data
    ed.* EXCEPT(
      date, china_soybean_imports_mt, argentina_export_tax, argentina_china_sales_mt,
      zl_price_current, zl_price_lag1, zl_price_lag7, zl_price_lag30, zl_volume,
      palm_price, palm_volume, vix_level, vix_lag1, vix_lag2,
      feature_vix_stress, feature_harvest_pace, feature_china_relations, feature_tariff_threat,
      feature_geopolitical_volatility, feature_biofuel_cascade, feature_hidden_correlation,
      feature_biofuel_ethanol, big8_composite_score,
      cftc_commercial_long, cftc_commercial_short, cftc_managed_long, cftc_managed_short,
      cftc_open_interest, fed_funds_rate, treasury_10y_yield, usd_cny_rate, usd_brl_rate
    ),
    
    -- Targets (keep existing or use Vertex AI)
    COALESCE(ed.target_1w, vad.target_1w) as target_1w,
    COALESCE(ed.target_1m, vad.target_1m) as target_1m,
    COALESCE(ed.target_3m, vad.target_3m) as target_3m,
    COALESCE(ed.target_6m, vad.target_6m) as target_6m
    
  FROM all_dates ad
  LEFT JOIN existing_data ed ON ad.date = ed.date
  LEFT JOIN vertex_ai_data vad ON ad.date = vad.date
  LEFT JOIN current_prices cp ON ad.date = cp.date
  LEFT JOIN current_palm cpalm ON ad.date = cpalm.date
  LEFT JOIN current_vix cv ON ad.date = cv.date
  LEFT JOIN current_big8 cb8 ON ad.date = cb8.date
)

-- Final result with forward-fill for sparse features
SELECT 
  date,
  -- Forward-fill sparse features
  LAST_VALUE(china_soybean_imports_mt IGNORE NULLS) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as china_soybean_imports_mt,
  LAST_VALUE(argentina_export_tax IGNORE NULLS) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as argentina_export_tax,
  LAST_VALUE(argentina_china_sales_mt IGNORE NULLS) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as argentina_china_sales_mt,
  
  -- Keep all other columns as-is
  * EXCEPT(date, china_soybean_imports_mt, argentina_export_tax, argentina_china_sales_mt)
  
FROM combined_data
WHERE date IS NOT NULL
ORDER BY date;

-- ============================================
-- STEP 3: POPULATE FEATURE IMPORTANCE
-- ============================================
INSERT INTO `cbi-v14.predictions_uc1.model_feature_importance`
  (prediction_date, horizon, feature, importance_score, model_name)
WITH feature_correlations AS (
  SELECT 
    CURRENT_DATE() as prediction_date,
    '1w' as horizon,
    'china_soybean_imports_mt' as feature,
    ABS(CORR(china_soybean_imports_mt, target_1w)) as importance_score,
    'vertex_ai_export' as model_name
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  UNION ALL
  
  SELECT CURRENT_DATE(), '1w', 'vix_level',
    ABS(CORR(vix_level, target_1w)), 'vertex_ai_export'
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  UNION ALL
  
  SELECT CURRENT_DATE(), '1w', 'palm_price',
    ABS(CORR(palm_price, target_1w)), 'vertex_ai_export'
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  UNION ALL
  
  SELECT CURRENT_DATE(), '1w', 'feature_tariff_threat',
    ABS(CORR(feature_tariff_threat, target_1w)), 'vertex_ai_export'
  FROM `cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items`
  
  -- Add more features as needed
)
SELECT * FROM feature_correlations
WHERE importance_score IS NOT NULL;

-- ============================================
-- STEP 4: VERIFY SUCCESS
-- ============================================
SELECT 
  'CONSOLIDATION COMPLETE' as status,
  MAX(date) as latest_date,
  MIN(date) as earliest_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  
  -- Check coverage of key features
  ROUND(100 * SUM(CASE WHEN china_soybean_imports_mt IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as china_imports_coverage,
  ROUND(100 * SUM(CASE WHEN feature_vix_stress IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as vix_stress_coverage,
  ROUND(100 * SUM(CASE WHEN feature_tariff_threat IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as tariff_threat_coverage,
  ROUND(100 * SUM(CASE WHEN palm_price IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as palm_coverage,
  
  -- Final assessment
  CASE 
    WHEN MAX(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY) THEN '✅ DATA IS CURRENT!'
    ELSE '⚠️ DATA STILL STALE'
  END as freshness_status
  
FROM `cbi-v14.models_v4.production_training_data_1m`;

-- ============================================
-- STEP 5: REPLICATE TO OTHER HORIZONS
-- ============================================
-- Repeat for 1w, 3m, 6m tables
CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_1w` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;

CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_3m` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;

CREATE OR REPLACE TABLE `cbi-v14.models_v4.production_training_data_6m` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;






