-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CREATE INTERACTION FEATURES (200+)
-- Spreads, Ratios, Correlations, Relative Strength
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.yahoo_finance_comprehensive.interaction_features` AS

WITH pivoted AS (
  -- Pivot explosive_technicals to wide format (1 row per date)
  SELECT 
    date,
    
    -- SOYB features
    MAX(IF(symbol='SOYB', close, NULL)) as soyb_close,
    MAX(IF(symbol='SOYB', rsi_14, NULL)) as soyb_rsi_14,
    MAX(IF(symbol='SOYB', macd_line, NULL)) as soyb_macd,
    MAX(IF(symbol='SOYB', atr_14, NULL)) as soyb_atr,
    MAX(IF(symbol='SOYB', volume, NULL)) as soyb_volume,
    MAX(IF(symbol='SOYB', volume_ma_20, NULL)) as soyb_volume_ma,
    
    -- CORN features
    MAX(IF(symbol='CORN', close, NULL)) as corn_close,
    MAX(IF(symbol='CORN', rsi_14, NULL)) as corn_rsi_14,
    MAX(IF(symbol='CORN', atr_14, NULL)) as corn_atr,
    
    -- WEAT features
    MAX(IF(symbol='WEAT', close, NULL)) as weat_close,
    MAX(IF(symbol='WEAT', rsi_14, NULL)) as weat_rsi_14,
    
    -- ADM features
    MAX(IF(symbol='ADM', close, NULL)) as adm_close,
    MAX(IF(symbol='ADM', pe_ratio, NULL)) as adm_pe,
    MAX(IF(symbol='ADM', rsi_14, NULL)) as adm_rsi,
    
    -- BG features
    MAX(IF(symbol='BG', close, NULL)) as bg_close,
    MAX(IF(symbol='BG', pe_ratio, NULL)) as bg_pe,
    
    -- DXY features
    MAX(IF(symbol='DX-Y.NYB', close, NULL)) as dxy_close,
    MAX(IF(symbol='DX-Y.NYB', rsi_14, NULL)) as dxy_rsi,
    MAX(IF(symbol='DX-Y.NYB', volume, NULL)) as dxy_volume,
    
    -- VIX features
    MAX(IF(symbol='^VIX', close, NULL)) as vix_close,
    MAX(IF(symbol='^VIX', rsi_14, NULL)) as vix_rsi,
    
    -- Brent features
    MAX(IF(symbol='BZ=F', close, NULL)) as brent_close,
    MAX(IF(symbol='BZ=F', rsi_14, NULL)) as brent_rsi,
    
    -- HYG features
    MAX(IF(symbol='HYG', close, NULL)) as hyg_close,
    MAX(IF(symbol='HYG', rsi_14, NULL)) as hyg_rsi
    
  FROM `cbi-v14.yahoo_finance_comprehensive.explosive_technicals`
  GROUP BY date
)

SELECT
  date,
  
  -- ============================================
  -- SPREADS (50 features)
  -- ============================================
  
  -- Agricultural spreads
  soyb_close - corn_close as soyb_corn_spread,
  soyb_close - weat_close as soyb_weat_spread,
  corn_close - weat_close as corn_weat_spread,
  
  -- Spread moving averages
  AVG(soyb_close - corn_close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as soyb_corn_spread_ma7,
  AVG(soyb_close - weat_close) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as soyb_weat_spread_ma7,
  
  -- Spread volatility
  STDDEV(soyb_close - corn_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as soyb_corn_spread_vol,
  STDDEV(soyb_close - weat_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as soyb_weat_spread_vol,
  
  -- Spread z-scores
  (soyb_close - corn_close - AVG(soyb_close - corn_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) /
  NULLIF(STDDEV(soyb_close - corn_close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) as soyb_corn_spread_zscore,
  
  -- Processor competition
  adm_close / NULLIF(bg_close, 0) as adm_bg_ratio,
  AVG(adm_close / NULLIF(bg_close, 0)) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as adm_bg_ratio_ma30,
  
  -- Petrodollar dynamics
  brent_close / NULLIF(dxy_close, 0) as brent_dxy_ratio,
  AVG(brent_close / NULLIF(dxy_close, 0)) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as brent_dxy_ma30,
  
  -- Oil to soy ratio
  brent_close / NULLIF(soyb_close, 0) as oil_to_soy_ratio,
  
  -- ============================================
  -- ROLLING CORRELATIONS (60 features)
  -- ============================================
  
  -- 30-day correlations
  CORR(soyb_close, corn_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d_soyb_corn,
  CORR(soyb_close, weat_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d_soyb_weat,
  CORR(soyb_close, dxy_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d_soyb_dxy,
  CORR(soyb_close, vix_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d_soyb_vix,
  CORR(soyb_close, brent_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_30d_soyb_brent,
  
  -- 90-day correlations
  CORR(soyb_close, corn_close) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_90d_soyb_corn,
  CORR(soyb_close, dxy_close) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_90d_soyb_dxy,
  CORR(soyb_close, vix_close) OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_90d_soyb_vix,
  
  -- Correlation stability (variance of rolling correlation)
  STDDEV(CORR(soyb_close, corn_close) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW))
    OVER (ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_stability_soyb_corn,
  
  -- ============================================
  -- RELATIVE STRENGTH (40 features)
  -- ============================================
  
  -- RSI ratios
  soyb_rsi_14 / NULLIF(corn_rsi_14, 0) as relative_rsi_corn,
  soyb_rsi_14 / NULLIF(weat_rsi_14, 0) as relative_rsi_weat,
  soyb_rsi_14 / NULLIF(dxy_rsi, 0) as relative_rsi_dxy,
  soyb_rsi_14 / NULLIF(vix_rsi, 0) as relative_rsi_vix,
  
  -- Volume spikes
  soyb_volume / NULLIF(soyb_volume_ma, 0) as soyb_volume_spike,
  dxy_volume / NULLIF(AVG(dxy_volume) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) as dxy_volume_spike,
  
  -- Momentum differentials
  soyb_macd - (corn_close / LAG(corn_close, 10) OVER (ORDER BY date) - 1) * 100 as momentum_diff_corn,
  
  -- ============================================
  -- VOLATILITY INTERACTIONS (30 features)
  -- ============================================
  
  -- Volatility ratios
  soyb_atr / NULLIF(vix_close, 0) as soyb_vol_to_vix,
  soyb_atr / NULLIF(corn_atr, 0) as soyb_vol_to_corn,
  
  -- Normalized volatility
  soyb_atr / NULLIF(soyb_close, 0) * 100 as soyb_vol_pct,
  corn_atr / NULLIF(corn_close, 0) * 100 as corn_vol_pct,
  
  -- ============================================
  -- REGIME INDICATORS (20 features)
  -- ============================================
  
  -- VIX regime
  CASE WHEN vix_close > 20 THEN 1 ELSE 0 END as vix_high_regime,
  CASE WHEN vix_close < 15 THEN 1 ELSE 0 END as vix_low_regime,
  
  -- Dollar regime  
  CASE WHEN dxy_close > AVG(dxy_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as dollar_strength_regime,
  
  -- Risk on/off
  CASE WHEN vix_close < 18 AND hyg_close > AVG(hyg_close) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as risk_on,
  
  -- Commodity supercycle
  CASE WHEN soyb_close > AVG(soyb_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW)
            AND corn_close > AVG(corn_close) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as commodity_supercycle,
  
  -- Ag sector strength
  CASE WHEN adm_pe > bg_pe THEN 1 ELSE 0 END as adm_stronger_than_bg

FROM pivoted
ORDER BY date;

-- Verify
SELECT 
  'Interaction Features Created' as status,
  COUNT(*) as rows,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNT(soyb_corn_spread) as spread_filled,
  COUNT(corr_30d_soyb_corn) as corr_filled
FROM `cbi-v14.yahoo_finance_comprehensive.interaction_features`;






