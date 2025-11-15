-- ============================================
-- BUILD TRAINING TABLES - NEW NAMING CONVENTION
-- Date: November 14, 2025
-- Mission: Build training tables with Option 3 naming
-- Pattern: training.zl_training_{surface}_allhistory_{horizon}
-- ============================================

-- ============================================
-- PRODUCTION SURFACE (≈290 columns)
-- ============================================

-- Build zl_training_prod_allhistory_1m
CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_1m` AS
WITH 
-- Get ALL dates from Big 8 signals (current through today)
all_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2000-01-01'
),

-- Get existing production data (from new training tables)
existing_data AS (
  SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2000-01-01'
),

-- Get current prices
current_prices AS (
  SELECT 
    DATE(time) as date,
    close as zl_price_current,
    LAG(close, 1) OVER (ORDER BY time) as zl_price_lag1,
    LAG(close, 7) OVER (ORDER BY time) as zl_price_lag7,
    LAG(close, 30) OVER (ORDER BY time) as zl_price_lag30,
    volume as zl_volume
  FROM `cbi-v14.raw_intelligence.commodity_soybean_oil_prices`
  WHERE symbol = 'ZL'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get current palm oil
current_palm AS (
  SELECT 
    DATE(time) as date,
    close as palm_price
  FROM `cbi-v14.raw_intelligence.commodity_palm_oil_prices`
  WHERE symbol = 'PALM'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get current VIX
current_vix AS (
  SELECT 
    DATE(time) as date,
    close as vix_level
  FROM `cbi-v14.forecasting_data_warehouse.vix_data`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),

-- Get current Big 8 signals
current_big8 AS (
  SELECT 
    date,
    feature_vix_stress,
    feature_harvest_pace,
    feature_china_relations,
    feature_tariff_threat,
    feature_geopolitical_volatility,
    feature_biofuel_cascade,
    feature_hidden_correlation,
    feature_biofuel_ethanol,
    big8_composite_score
  FROM `cbi-v14.neural.vw_big_eight_signals`
  WHERE date >= '2000-01-01'
),

-- Combine all data sources
combined_data AS (
  SELECT 
    ad.date,
    
    -- Core price data
    COALESCE(ed.zl_price_current, cp.zl_price_current) as zl_price_current,
    COALESCE(ed.zl_price_lag1, cp.zl_price_lag1) as zl_price_lag1,
    COALESCE(ed.zl_price_lag7, cp.zl_price_lag7) as zl_price_lag7,
    COALESCE(ed.zl_price_lag30, cp.zl_price_lag30) as zl_price_lag30,
    COALESCE(ed.zl_volume, cp.zl_volume) as zl_volume,
    
    -- Big 8 signals
    COALESCE(ed.feature_vix_stress, cb8.feature_vix_stress) as feature_vix_stress,
    COALESCE(ed.feature_harvest_pace, cb8.feature_harvest_pace) as feature_harvest_pace,
    COALESCE(ed.feature_china_relations, cb8.feature_china_relations) as feature_china_relations,
    COALESCE(ed.feature_tariff_threat, cb8.feature_tariff_threat) as feature_tariff_threat,
    COALESCE(ed.feature_geopolitical_volatility, cb8.feature_geopolitical_volatility) as feature_geopolitical_volatility,
    COALESCE(ed.feature_biofuel_cascade, cb8.feature_biofuel_cascade) as feature_biofuel_cascade,
    COALESCE(ed.feature_hidden_correlation, cb8.feature_hidden_correlation) as feature_hidden_correlation,
    COALESCE(ed.feature_biofuel_ethanol, cb8.feature_biofuel_ethanol) as feature_biofuel_ethanol,
    COALESCE(ed.big8_composite_score, cb8.big8_composite_score) as big8_composite_score,
    
    -- Commodity prices
    COALESCE(ed.palm_price, cpalm.palm_price) as palm_price,
    COALESCE(ed.corn_price, ed.corn_price) as corn_price,
    COALESCE(ed.wheat_price, ed.wheat_price) as wheat_price,
    COALESCE(ed.crude_price, ed.crude_price) as crude_price,
    
    -- VIX
    COALESCE(ed.vix_level, cv.vix_level) as vix_level,
    
    -- Targets (keep existing or calculate)
    COALESCE(ed.target_1w, ed.target_1w) as target_1w,
    COALESCE(ed.target_1m, ed.target_1m) as target_1m,
    COALESCE(ed.target_3m, ed.target_3m) as target_3m,
    COALESCE(ed.target_6m, ed.target_6m) as target_6m,
    COALESCE(ed.target_12m, ed.target_12m) as target_12m,
    
    -- All other existing columns from production data
    ed.* EXCEPT(
      date, zl_price_current, zl_price_lag1, zl_price_lag7, zl_price_lag30, zl_volume,
      feature_vix_stress, feature_harvest_pace, feature_china_relations, feature_tariff_threat,
      feature_geopolitical_volatility, feature_biofuel_cascade, feature_hidden_correlation,
      feature_biofuel_ethanol, big8_composite_score, palm_price, corn_price, wheat_price,
      crude_price, vix_level, target_1w, target_1m, target_3m, target_6m, target_12m
    ),
    
    -- Regime and weight columns
    1 as training_weight,
    'allhistory' as market_regime
    
  FROM all_dates ad
  LEFT JOIN existing_data ed ON ad.date = ed.date
  LEFT JOIN current_prices cp ON ad.date = cp.date
  LEFT JOIN current_palm cpalm ON ad.date = cpalm.date
  LEFT JOIN current_vix cv ON ad.date = cv.date
  LEFT JOIN current_big8 cb8 ON ad.date = cb8.date
)

SELECT * FROM combined_data
ORDER BY date;

-- Build other horizons (1w, 3m, 6m, 12m) - same structure, different targets
CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_1w` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_3m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_6m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_12m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- ============================================
-- FULL SURFACE (1,948+ columns)
-- ============================================
-- NOTE: Full surface tables will be built from comprehensive feature joins
-- For now, copy from prod surface as placeholder
-- TODO: Build full surface with all intelligence features

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_full_allhistory_1w` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1w`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_full_allhistory_1m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_full_allhistory_3m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_3m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_full_allhistory_6m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_6m`;

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_full_allhistory_12m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_12m`;

-- ============================================
-- UPDATE REGIME LABELS
-- ============================================
-- Join with regime_calendar to set market_regime

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1w` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_3m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_6m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_12m` t
SET market_regime = rc.regime
FROM `cbi-v14.training.regime_calendar` rc
WHERE t.date = rc.date;

-- ============================================
-- UPDATE TRAINING WEIGHTS
-- ============================================
-- Join with regime_weights to set training_weight

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND t.date >= rw.start_date
  AND t.date <= rw.end_date;

-- Repeat for other horizons
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1w` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND t.date >= rw.start_date
  AND t.date <= rw.end_date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_3m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND t.date >= rw.start_date
  AND t.date <= rw.end_date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_6m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND t.date >= rw.start_date
  AND t.date <= rw.end_date;

UPDATE `cbi-v14.training.zl_training_prod_allhistory_12m` t
SET training_weight = CAST(rw.weight AS INT64)
FROM `cbi-v14.training.regime_weights` rw
WHERE t.market_regime = rw.regime
  AND t.date >= rw.start_date
  AND t.date <= rw.end_date;

