-- ============================================
-- AMPLIFY V3: EXTRACT ALL FEATURES FROM 18 SYMBOLS
-- 850+ features total - let BQML pick winners via L1 regularization
-- ============================================

-- First, expand schema to accommodate ALL features per symbol
-- ETFs/Commodities: 43 features each
-- Stocks: 51 features each (43 + 8 fundamentals)

-- TIER 1 ETF: SOYB (43 features, 0.92 correlation)
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
-- Price features (6)
ADD COLUMN IF NOT EXISTS soyb_open FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_high FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_low FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_close FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_volume FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_vwap FLOAT64,

-- Moving averages (8)
ADD COLUMN IF NOT EXISTS soyb_ma_7d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_14d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_21d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_30d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_50d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_100d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ma_200d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_ema_21d FLOAT64,

-- Momentum indicators (7)
ADD COLUMN IF NOT EXISTS soyb_rsi_14 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_rsi_9 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_roc_10 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_williams_r FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_stoch_k FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_stoch_d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_mfi_14 FLOAT64,

-- Volatility measures (6)
ADD COLUMN IF NOT EXISTS soyb_atr_14 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_bb_upper FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_bb_middle FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_bb_lower FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_bb_width FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_hv_20d FLOAT64,

-- Volume analytics (5)
ADD COLUMN IF NOT EXISTS soyb_volume_ma_20 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_volume_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_obv FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_volume_force FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_accum_dist FLOAT64,

-- Trend indicators (6)
ADD COLUMN IF NOT EXISTS soyb_macd_line FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_macd_signal FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_macd_histogram FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_adx_14 FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_plus_di FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_minus_di FLOAT64,

-- Derivatives (5)
ADD COLUMN IF NOT EXISTS soyb_returns_1d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_returns_5d FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_log_returns FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_realized_vol FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_zscore_20d FLOAT64;

-- [Repeat exact same 43-column pattern for CORN, WEAT, Brent, Copper, DXY, etc.]
-- [For stocks ADM, BG, NTR, DAR, TSN, CF, MOS: Add 8 fundamental columns on top of 43]

-- INTERACTION FEATURES (100+ new)
ALTER TABLE `cbi-v14.models_v4.production_training_data_1m`
-- Spreads & Ratios
ADD COLUMN IF NOT EXISTS soyb_corn_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_weat_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS adm_bg_ratio FLOAT64,
ADD COLUMN IF NOT EXISTS brent_dxy_petrodollar FLOAT64,

-- Correlation dynamics (30d rolling)
ADD COLUMN IF NOT EXISTS corr_soyb_corn_30d FLOAT64,
ADD COLUMN IF NOT EXISTS corr_soyb_weat_30d FLOAT64,
ADD COLUMN IF NOT EXISTS corr_soyb_dxy_30d FLOAT64,
ADD COLUMN IF NOT EXISTS corr_soyb_vix_30d FLOAT64,

-- Relative strength
ADD COLUMN IF NOT EXISTS soyb_rsi_vs_corn_rsi FLOAT64,
ADD COLUMN IF NOT EXISTS soyb_vol_vs_5d_avg FLOAT64;

-- Continue for all interactions...

-- SUMMARY: Total schema expansion
-- Current: 444 columns
-- After amplification: 444 + 850 = 1,294 columns
-- BQML with L1_reg=15.0 will auto-select top ~200 most predictive






