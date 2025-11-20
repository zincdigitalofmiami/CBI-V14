-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CREATE EXPLOSIVE PRODUCTION TABLE (FAST APPROACH)
-- Join existing production table with pivoted Yahoo features
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_1m_explosive` AS

WITH 
-- Start with current production (444 columns including 110 v3 features)
base_production AS (
  SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
),

-- Pivot Yahoo data for remaining symbols we need
yahoo_pivoted AS (
  SELECT
    date,
    
    -- Additional technical indicators per symbol (beyond what's in production)
    -- SOYB additional features
    MAX(IF(symbol='SOYB', ma_90d, NULL)) as soyb_ma_90d,
    MAX(IF(symbol='SOYB', ma_100d, NULL)) as soyb_ma_100d,
    MAX(IF(symbol='SOYB', macd_signal, NULL)) as soyb_macd_signal,
    MAX(IF(symbol='SOYB', macd_histogram, NULL)) as soyb_macd_histogram,
    MAX(IF(symbol='SOYB', bb_middle, NULL)) as soyb_bb_middle,
    MAX(IF(symbol='SOYB', bb_lower, NULL)) as soyb_bb_lower,
    
    -- CORN additional features
    MAX(IF(symbol='CORN', ma_90d, NULL)) as corn_ma_90d,
    MAX(IF(symbol='CORN', ma_100d, NULL)) as corn_ma_100d,
    MAX(IF(symbol='CORN', macd_signal, NULL)) as corn_macd_signal,
    MAX(IF(symbol='CORN', macd_histogram, NULL)) as corn_macd_histogram,
    MAX(IF(symbol='CORN', bb_middle, NULL)) as corn_bb_middle,
    MAX(IF(symbol='CORN', bb_lower, NULL)) as corn_bb_lower,
    
    -- WEAT additional features
    MAX(IF(symbol='WEAT', ma_90d, NULL)) as weat_ma_90d,
    MAX(IF(symbol='WEAT', ma_100d, NULL)) as weat_ma_100d,
    MAX(IF(symbol='WEAT', macd_signal, NULL)) as weat_macd_signal,
    MAX(IF(symbol='WEAT', bb_middle, NULL)) as weat_bb_middle,
    
    -- Additional stocks (NTR, DAR, TSN already have basics, add MACD/BB)
    MAX(IF(symbol='NTR', macd_line, NULL)) as ntr_macd,
    MAX(IF(symbol='DAR', macd_line, NULL)) as dar_macd,
    MAX(IF(symbol='TSN', macd_line, NULL)) as tsn_macd,
    MAX(IF(symbol='CF', macd_line, NULL)) as cf_macd,
    MAX(IF(symbol='MOS', macd_line, NULL)) as mos_macd,
    
    -- Energy/FX additional features
    MAX(IF(symbol='BZ=F', macd_signal, NULL)) as brent_macd_signal,
    MAX(IF(symbol='HG=F', macd_signal, NULL)) as copper_macd_signal,
    MAX(IF(symbol='NG=F', macd_signal, NULL)) as natgas_macd_signal,
    MAX(IF(symbol='DX-Y.NYB', macd_signal, NULL)) as dxy_macd_signal,
    MAX(IF(symbol='^VIX', macd_signal, NULL)) as vix_macd_signal
    
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol IN ('SOYB', 'CORN', 'WEAT', 'NTR', 'DAR', 'TSN', 'CF', 'MOS',
                   'BZ=F', 'HG=F', 'NG=F', 'DX-Y.NYB', '^VIX')
    AND date >= '2020-01-01'
  GROUP BY date
),

-- Calculate key interaction features
interactions AS (
  SELECT
    date,
    
    -- Spreads
    soyb_close - corn_etf_close as soyb_corn_spread,
    soyb_close - weat_close as soyb_weat_spread,
    adm_close / NULLIF(bg_close, 0) as adm_bg_processor_ratio,
    brent_close / NULLIF(dxy_yahoo_close, 0) as brent_dxy_petrodollar,
    
    -- Relative strength
    soyb_rsi_14 / NULLIF(corn_etf_rsi_14, 0) as relative_rsi_corn,
    soyb_volume / NULLIF(AVG(soyb_volume) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) as soyb_volume_spike,
    
    -- Volatility ratios
    soyb_atr_14 / NULLIF(vix_yahoo_close, 0) as soyb_vol_to_vix,
    
    -- Regime indicators
    CASE WHEN vix_yahoo_close > 20 THEN 1 ELSE 0 END as vix_high_regime,
    CASE WHEN dxy_yahoo_close > AVG(dxy_yahoo_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as dollar_strength_regime
    
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2020-01-01'
)

-- Join everything together
SELECT
  p.*,
  y.* EXCEPT(date),
  i.* EXCEPT(date)
  
FROM base_production p
LEFT JOIN yahoo_pivoted y ON p.date = y.date
LEFT JOIN interactions i ON p.date = i.date;

-- Verify
SELECT 
  'Explosive Production Table Created' as status,
  COUNT(*) as rows,
  (SELECT COUNT(*) FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS` 
   WHERE table_name = 'zl_training_prod_allhistory_1m_explosive') as columns,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.training.zl_training_prod_allhistory_1m_explosive`;






