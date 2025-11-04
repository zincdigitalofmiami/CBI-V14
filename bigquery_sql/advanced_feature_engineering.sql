-- ============================================
-- ADVANCED FEATURE ENGINEERING
-- Create comprehensive technical, correlation, and derived features
-- ============================================

-- Step 1: Add schema for new advanced features
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS rsi_14 FLOAT64,
ADD COLUMN IF NOT EXISTS macd_line FLOAT64,
ADD COLUMN IF NOT EXISTS macd_signal FLOAT64,
ADD COLUMN IF NOT EXISTS macd_histogram FLOAT64,
ADD COLUMN IF NOT EXISTS bb_upper FLOAT64,
ADD COLUMN IF NOT EXISTS bb_lower FLOAT64,
ADD COLUMN IF NOT EXISTS bb_percent FLOAT64,
ADD COLUMN IF NOT EXISTS atr_14 FLOAT64,
ADD COLUMN IF NOT EXISTS historical_volatility_30d FLOAT64,
ADD COLUMN IF NOT EXISTS corn_zl_correlation_30d FLOAT64,
ADD COLUMN IF NOT EXISTS wheat_zl_correlation_30d FLOAT64,
ADD COLUMN IF NOT EXISTS crude_zl_correlation_30d FLOAT64,
ADD COLUMN IF NOT EXISTS usd_zl_correlation_30d FLOAT64,
ADD COLUMN IF NOT EXISTS seasonal_month_factor FLOAT64,
ADD COLUMN IF NOT EXISTS price_momentum_1w FLOAT64,
ADD COLUMN IF NOT EXISTS price_momentum_1m FLOAT64,
ADD COLUMN IF NOT EXISTS volume_sma_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS economic_stress_index FLOAT64;

-- Step 2: Create technical indicators from price data
-- RSI, MACD, Bollinger Bands, ATR, Historical Volatility
CREATE OR REPLACE TABLE `cbi-v14.models_v4.technical_indicators` AS
WITH price_data AS (
  SELECT
    date,
    zl_price_current as close,
    zl_price_current - zl_price_lag1 as price_change,
    zl_volume,
    ROW_NUMBER() OVER (ORDER BY date) as row_num
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
  ORDER BY date
),

-- Calculate RSI (14-day)
rsi_calc AS (
  SELECT
    date,
    close,
    CASE
      WHEN AVG(CASE WHEN price_change > 0 THEN price_change ELSE 0 END) OVER w14 +
           AVG(CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END) OVER w14 = 0
      THEN 50
      ELSE 100 - (100 / (1 + (
        AVG(CASE WHEN price_change > 0 THEN price_change ELSE 0 END) OVER w14 /
        NULLIF(AVG(CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END) OVER w14, 0)
      )))
    END as rsi_14
  FROM price_data
  WINDOW w14 AS (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
),

-- Calculate Bollinger Bands (20-day, 2 SD)
bb_calc AS (
  SELECT
    date,
    close,
    AVG(close) OVER w20 as sma_20,
    STDDEV(close) OVER w20 as std_20,
    (AVG(close) OVER w20) + (2 * STDDEV(close) OVER w20) as bb_upper,
    (AVG(close) OVER w20) - (2 * STDDEV(close) OVER w20) as bb_lower,
    SAFE_DIVIDE(
      (close - ((AVG(close) OVER w20) - (2 * STDDEV(close) OVER w20))),
      ((AVG(close) OVER w20) + (2 * STDDEV(close) OVER w20)) - ((AVG(close) OVER w20) - (2 * STDDEV(close) OVER w20))
    ) as bb_percent
  FROM price_data
  WINDOW w20 AS (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
),

-- Calculate MACD (12-26-9)
macd_calc AS (
  SELECT
    date,
    close,
    -- EMA 12
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) as ema_12,
    -- EMA 26
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) as ema_26
  FROM price_data
),

macd_signal AS (
  SELECT
    date,
    ema_12 - ema_26 as macd_line,
    -- Signal line (9-day EMA of MACD)
    AVG(ema_12 - ema_26) OVER (ORDER BY date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) as macd_signal
  FROM macd_calc
),

-- Calculate ATR (14-day Average True Range) - simplified version
atr_calc AS (
  SELECT
    date,
    zl_price_current as close,
    -- Simplified ATR using just price range (since we don't have H/L data)
    ABS(zl_price_current - LAG(zl_price_current) OVER (ORDER BY date)) as true_range
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
),

atr_final AS (
  SELECT
    date,
    AVG(true_range) OVER (ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as atr_14
  FROM atr_calc
),

-- Calculate Historical Volatility (30-day)
volatility_calc AS (
  SELECT
    date,
    STDDEV(price_change) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) *
    SQRT(252) as historical_volatility_30d  -- Annualized
  FROM price_data
)

SELECT
  r.date,
  r.rsi_14,
  m.macd_line,
  m.macd_signal,
  m.macd_line - m.macd_signal as macd_histogram,
  b.bb_upper,
  b.bb_lower,
  b.bb_percent,
  a.atr_14,
  v.historical_volatility_30d
FROM rsi_calc r
LEFT JOIN macd_signal m ON r.date = m.date
LEFT JOIN bb_calc b ON r.date = b.date
LEFT JOIN atr_final a ON r.date = a.date
LEFT JOIN volatility_calc v ON r.date = v.date
ORDER BY r.date;

-- Step 3: Create cross-asset correlation features
CREATE OR REPLACE TABLE `cbi-v14.models_v4.cross_asset_correlations` AS
WITH asset_prices AS (
  SELECT
    date,
    zl_price_current,
    corn_price,
    wheat_price,
    palm_price,
    crude_price,
    usd_index
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE zl_price_current IS NOT NULL
),

-- Rolling 30-day correlations
correlations AS (
  SELECT
    date,
    -- Corn vs Soybean Oil
    CORR(corn_price, zl_price_current) OVER w30 as corn_zl_correlation_30d,
    -- Wheat vs Soybean Oil
    CORR(wheat_price, zl_price_current) OVER w30 as wheat_zl_correlation_30d,
    -- Palm Oil vs Soybean Oil
    CORR(palm_price, zl_price_current) OVER w30 as palm_zl_correlation_30d,
    -- Crude vs Soybean Oil
    CORR(crude_price, zl_price_current) OVER w30 as crude_zl_correlation_30d,
    -- USD Index vs Soybean Oil (inverse relationship)
    CORR(usd_index, zl_price_current) OVER w30 as usd_zl_correlation_30d
  FROM asset_prices
  WINDOW w30 AS (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
)

SELECT * FROM correlations WHERE date IS NOT NULL ORDER BY date;

-- Step 4: Create seasonal and momentum features
CREATE OR REPLACE TABLE `cbi-v14.models_v4.seasonal_features` AS
SELECT
  date,
  zl_price_current,

  -- Seasonal month factor (soybean harvest cycle)
  CASE EXTRACT(MONTH FROM date)
    WHEN 9 THEN 0.9  -- September harvest start
    WHEN 10 THEN 1.0 -- October peak harvest
    WHEN 11 THEN 0.8 -- November harvest end
    WHEN 12 THEN 0.6 -- December planting
    WHEN 1 THEN 0.5  -- January winter
    WHEN 2 THEN 0.4  -- February pre-planting
    WHEN 3 THEN 0.6  -- March planting
    WHEN 4 THEN 0.7  -- April growth
    WHEN 5 THEN 0.8  -- May development
    WHEN 6 THEN 0.9  -- June flowering
    WHEN 7 THEN 1.0  -- July pod fill
    WHEN 8 THEN 0.9  -- August maturation
    ELSE 0.5
  END as seasonal_month_factor,

  -- Price momentum (1-week and 1-month returns)
  SAFE_DIVIDE(zl_price_current - LAG(zl_price_current, 5) OVER (ORDER BY date),
               LAG(zl_price_current, 5) OVER (ORDER BY date)) as price_momentum_1w,

  SAFE_DIVIDE(zl_price_current - LAG(zl_price_current, 22) OVER (ORDER BY date),
               LAG(zl_price_current, 22) OVER (ORDER BY date)) as price_momentum_1m,

  -- Volume analysis
  SAFE_DIVIDE(zl_volume,
               AVG(zl_volume) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) as volume_sma_ratio

FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE zl_price_current IS NOT NULL
ORDER BY date;

-- Step 5: Create economic stress composite
CREATE OR REPLACE TABLE `cbi-v14.models_v4.economic_stress_features` AS
SELECT
  date,

  -- Economic stress index (higher = more stress)
  CASE
    WHEN fed_funds_rate > 4.0 THEN 0.9  -- High rates
    WHEN fed_funds_rate > 2.0 THEN 0.6  -- Elevated rates
    WHEN gdp_growth < 1.0 THEN 0.8     -- Slow growth
    WHEN unemployment_rate > 6.0 THEN 0.7 -- High unemployment
    WHEN cpi_yoy > 4.0 THEN 0.8        -- High inflation
    WHEN cpi_yoy < 1.0 THEN 0.5        -- Deflation risk
    ELSE 0.3                           -- Normal conditions
  END as economic_stress_index

FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE fed_funds_rate IS NOT NULL OR gdp_growth IS NOT NULL OR
      unemployment_rate IS NOT NULL OR cpi_yoy IS NOT NULL
ORDER BY date;

-- Step 6: Update training dataset with new features (separate updates to avoid conflicts)

-- Technical indicators
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET
  rsi_14 = ti.rsi_14,
  macd_line = ti.macd_line,
  macd_signal = ti.macd_signal,
  macd_histogram = ti.macd_histogram,
  bb_upper = ti.bb_upper,
  bb_lower = ti.bb_lower,
  bb_percent = ti.bb_percent,
  atr_14 = ti.atr_14,
  historical_volatility_30d = ti.historical_volatility_30d
FROM `cbi-v14.models_v4.technical_indicators` ti
WHERE t.date = ti.date;

-- Cross-asset correlations
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET
  corn_zl_correlation_30d = corr.corn_zl_correlation_30d,
  wheat_zl_correlation_30d = corr.wheat_zl_correlation_30d,
  crude_zl_correlation_30d = corr.crude_zl_correlation_30d,
  usd_zl_correlation_30d = corr.usd_zl_correlation_30d
FROM `cbi-v14.models_v4.cross_asset_correlations` corr
WHERE t.date = corr.date;

-- Seasonal and momentum features
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET
  seasonal_month_factor = seas.seasonal_month_factor,
  price_momentum_1w = seas.price_momentum_1w,
  price_momentum_1m = seas.price_momentum_1m,
  volume_sma_ratio = seas.volume_sma_ratio
FROM `cbi-v14.models_v4.seasonal_features` seas
WHERE t.date = seas.date;

-- Economic stress index
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` t
SET economic_stress_index = econ.economic_stress_index
FROM `cbi-v14.models_v4.economic_stress_features` econ
WHERE t.date = econ.date;

-- Step 7: Clean up temporary tables
DROP TABLE IF EXISTS `cbi-v14.models_v4.technical_indicators`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.cross_asset_correlations`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.seasonal_features`;
DROP TABLE IF EXISTS `cbi-v14.models_v4.economic_stress_features`;

-- Step 8: Update feature metadata for new features
INSERT INTO `cbi-v14.forecasting_data_warehouse.feature_metadata`
  (feature_name, feature_type, asset_class, economic_meaning, directional_impact,
   typical_lag_days, source_table, source_column, related_features, chat_aliases,
   source_reliability_score, affected_commodities)

VALUES
  ('rsi_14', 'technical', 'momentum', 'Relative Strength Index - overbought/oversold momentum', 'neutral',
   1, 'calculated', 'RSI calculation', ['zl_price_current', 'macd_line'], ['rsi', 'relative strength'],
   0.95, ['soybean_oil']),

  ('macd_line', 'technical', 'momentum', 'MACD line - trend following momentum', 'neutral',
   1, 'calculated', 'MACD calculation', ['macd_signal', 'macd_histogram'], ['macd'],
   0.95, ['soybean_oil']),

  ('bb_percent', 'technical', 'volatility', 'Bollinger Band %B - position within bands', 'neutral',
   1, 'calculated', 'Bollinger Band calculation', ['bb_upper', 'bb_lower'], ['bollinger', 'bb percent'],
   0.95, ['soybean_oil']),

  ('atr_14', 'technical', 'volatility', 'Average True Range - volatility measure', 'positive',
   1, 'calculated', 'ATR calculation', ['historical_volatility_30d'], ['atr', 'volatility'],
   0.95, ['soybean_oil']),

  ('corn_zl_correlation_30d', 'correlation', 'intermarket', '30-day rolling correlation between corn and soybean oil', 'neutral',
   30, 'calculated', 'correlation calculation', ['wheat_zl_correlation_30d', 'crude_zl_correlation_30d'], ['corn correlation'],
   0.90, ['soybean_oil', 'corn']),

  ('usd_zl_correlation_30d', 'correlation', 'macro', '30-day rolling correlation between USD index and soybean oil', 'negative',
   30, 'calculated', 'correlation calculation', ['zl_price_current'], ['usd correlation', 'dollar correlation'],
   0.93, ['soybean_oil']),

  ('seasonal_month_factor', 'seasonal', 'cyclical', 'Monthly seasonal factor based on soybean production cycle', 'neutral',
   30, 'calculated', 'seasonal calculation', ['zl_price_current'], ['seasonal', 'month factor'],
   0.85, ['soybean_oil']),

  ('economic_stress_index', 'economic', 'macro', 'Composite index of economic stress conditions', 'negative',
   30, 'calculated', 'economic indicators composite', ['fed_funds_rate', 'gdp_growth'], ['economic stress', 'stress index'],
   0.91, ['soybean_oil', 'all_commodities']);

-- Step 9: Verify feature engineering results
SELECT
  'Advanced Feature Engineering Results' as check_type,
  COUNTIF(rsi_14 IS NOT NULL) as technical_features,
  COUNTIF(corn_zl_correlation_30d IS NOT NULL) as correlation_features,
  COUNTIF(seasonal_month_factor IS NOT NULL) as seasonal_features,
  COUNTIF(economic_stress_index IS NOT NULL) as economic_features,
  COUNT(*) as total_rows
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;
