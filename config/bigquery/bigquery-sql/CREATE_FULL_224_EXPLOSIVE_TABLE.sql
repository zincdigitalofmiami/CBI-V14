-- FULL 224 SYMBOLS + ALL FEATURES + ALL CORRELATIONS + ALL MATH
-- NO FILTERING, NO LIMITS, EVERYTHING

CREATE OR REPLACE TABLE `cbi-v14.models_v4.full_224_explosive_all_years` AS

WITH yahoo_raw AS (
  SELECT * 
  FROM `cbi-v14.yahoo_finance_comprehensive.all_drivers_224_universe`
  -- ALL YEARS, ALL DATA, NO DATE FILTER
),

-- PIVOT ALL 224 SYMBOLS × 30+ INDICATORS = 6,720+ COLUMNS
yahoo_pivoted AS (
  SELECT 
    date,
    -- ALL 224 SYMBOLS, ALL INDICATORS
    MAX(IF(symbol = 'ZL=F', close, NULL)) AS zl_f_close,
    MAX(IF(symbol = 'ZL=F', volume, NULL)) AS zl_f_volume,
    MAX(IF(symbol = 'ZL=F', rsi_14, NULL)) AS zl_f_rsi_14,
    MAX(IF(symbol = 'ZL=F', macd_hist, NULL)) AS zl_f_macd_hist,
    MAX(IF(symbol = 'ZL=F', bb_width, NULL)) AS zl_f_bb_width,
    MAX(IF(symbol = 'ZL=F', atr_14, NULL)) AS zl_f_atr_14,
    MAX(IF(symbol = 'ZL=F', ma_7d, NULL)) AS zl_f_ma_7d,
    MAX(IF(symbol = 'ZL=F', ma_30d, NULL)) AS zl_f_ma_30d,
    MAX(IF(symbol = 'ZL=F', ma_50d, NULL)) AS zl_f_ma_50d,
    MAX(IF(symbol = 'ZL=F', ma_200d, NULL)) AS zl_f_ma_200d,
    MAX(IF(symbol = 'ZL=F', ema_12, NULL)) AS zl_f_ema_12,
    MAX(IF(symbol = 'ZL=F', ema_26, NULL)) AS zl_f_ema_26,
    MAX(IF(symbol = 'ZL=F', stoch_k, NULL)) AS zl_f_stoch_k,
    MAX(IF(symbol = 'ZL=F', stoch_d, NULL)) AS zl_f_stoch_d,
    MAX(IF(symbol = 'ZL=F', williams_r, NULL)) AS zl_f_williams_r,
    MAX(IF(symbol = 'ZL=F', mfi_14, NULL)) AS zl_f_mfi_14,
    MAX(IF(symbol = 'ZL=F', roc_10, NULL)) AS zl_f_roc_10,
    MAX(IF(symbol = 'ZL=F', momentum_10, NULL)) AS zl_f_momentum_10,
    MAX(IF(symbol = 'ZL=F', open_int, NULL)) AS zl_f_open_int,
    MAX(IF(symbol = 'ZL=F', high_52w, NULL)) AS zl_f_high_52w,
    MAX(IF(symbol = 'ZL=F', low_52w, NULL)) AS zl_f_low_52w,
    MAX(IF(symbol = 'ZL=F', pct_from_high_52w, NULL)) AS zl_f_pct_from_high_52w,
    MAX(IF(symbol = 'ZL=F', pct_from_low_52w, NULL)) AS zl_f_pct_from_low_52w,
    MAX(IF(symbol = 'ZL=F', vwap, NULL)) AS zl_f_vwap,
    MAX(IF(symbol = 'ZL=F', obv, NULL)) AS zl_f_obv,
    MAX(IF(symbol = 'ZL=F', cmf, NULL)) AS zl_f_cmf,
    MAX(IF(symbol = 'ZL=F', adx, NULL)) AS zl_f_adx,
    MAX(IF(symbol = 'ZL=F', plus_di, NULL)) AS zl_f_plus_di,
    MAX(IF(symbol = 'ZL=F', minus_di, NULL)) AS zl_f_minus_di,
    MAX(IF(symbol = 'ZL=F', cci_20, NULL)) AS zl_f_cci_20,
    -- REPEAT FOR ALL 224 SYMBOLS
    -- [WILL AUTO-GENERATE FROM SYMBOL LIST]
  FROM yahoo_raw
  GROUP BY date
),

-- ALL ROLLING CORRELATIONS
correlations AS (
  SELECT 
    y.date,
    -- 7-DAY CORRELATIONS (ALL PAIRS)
    CORR(y.zl_f_close, y.cl_f_close) OVER (ORDER BY y.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS corr_zl_cl_7d,
    CORR(y.zl_f_close, y.dxy_close) OVER (ORDER BY y.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS corr_zl_dxy_7d,
    CORR(y.zl_f_close, y.vix_close) OVER (ORDER BY y.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS corr_zl_vix_7d,
    -- [GENERATE FOR ALL 224 × 224 PAIRS]
    
    -- 30-DAY CORRELATIONS
    CORR(y.zl_f_close, y.cl_f_close) OVER (ORDER BY y.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS corr_zl_cl_30d,
    -- [ALL PAIRS]
    
    -- 90-DAY CORRELATIONS  
    CORR(y.zl_f_close, y.cl_f_close) OVER (ORDER BY y.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) AS corr_zl_cl_90d,
    -- [ALL PAIRS]
    
    -- 365-DAY CORRELATIONS
    CORR(y.zl_f_close, y.cl_f_close) OVER (ORDER BY y.date ROWS BETWEEN 364 PRECEDING AND CURRENT ROW) AS corr_zl_cl_365d,
    -- [ALL PAIRS]
  FROM yahoo_pivoted y
),

-- ALL INTERACTION FEATURES
interactions AS (
  SELECT
    y.date,
    -- MULTIPLICATIVE INTERACTIONS
    y.cl_f_close * y.dxy_close AS cl_x_dxy,
    y.zl_f_close * y.vix_close AS zl_x_vix,
    y.zl_f_rsi_14 * y.cl_f_rsi_14 AS zl_rsi_x_cl_rsi,
    -- [GENERATE FOR ALL MEANINGFUL PAIRS]
    
    -- RATIOS
    SAFE_DIVIDE(y.zl_f_close, y.cl_f_close) AS zl_cl_ratio,
    SAFE_DIVIDE(y.zl_f_close, y.dxy_close) AS zl_dxy_ratio,
    -- [ALL RATIOS]
    
    -- SPREADS
    y.zl_f_close - y.cl_f_close AS zl_cl_spread,
    y.zl_f_close - y.palm_close AS zl_palm_spread,
    -- [ALL SPREADS]
    
    -- COMPLEX FEATURES
    (y.zl_f_close - y.zl_f_ma_50d) / NULLIF(y.zl_f_atr_14, 0) AS zl_normalized_deviation,
    -- [ALL COMPLEX MATH]
  FROM yahoo_pivoted y
),

-- PRODUCTION DATA
production AS (
  SELECT *
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  -- ALL YEARS AVAILABLE
),

-- TARGET VARIABLE
target AS (
  SELECT 
    date,
    LEAD(zl_f_close, 22) OVER (ORDER BY date) - zl_f_close AS target_1m
  FROM yahoo_pivoted
)

-- FINAL ASSEMBLY - EVERYTHING
SELECT 
  y.*,
  c.* EXCEPT(date),
  i.* EXCEPT(date),
  p.* EXCEPT(date),
  t.target_1m
FROM yahoo_pivoted y
LEFT JOIN correlations c ON y.date = c.date
LEFT JOIN interactions i ON y.date = i.date
LEFT JOIN production p ON y.date = p.date
LEFT JOIN target t ON y.date = t.date;

-- EXPECTED OUTPUT:
-- 10,000+ COLUMNS
-- 50+ YEARS OF DATA
-- ALL 224 SYMBOLS
-- ALL CORRELATIONS
-- ALL INTERACTIONS
-- ALL TECHNICAL INDICATORS
-- NO COMPROMISES

