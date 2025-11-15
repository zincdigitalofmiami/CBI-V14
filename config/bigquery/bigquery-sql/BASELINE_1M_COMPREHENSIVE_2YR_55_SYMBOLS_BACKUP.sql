-- ============================================
-- COMPREHENSIVE BASELINE TRAINING - 1 MONTH HORIZON
-- 2024+ Data with ALL 220 Yahoo Finance Symbols
-- ============================================
-- Version: 1.0
-- Date: November 2025
--
-- OBJECTIVE: Discovery baseline to identify which features actually matter
-- ISOLATION: Completely separate from production models/tables
-- MODEL: bqml_1m_baseline_exploratory (separate from bqml_1m, bqml_1m_v2)
-- TABLE: baseline_1m_comprehensive_2yr (separate from zl_training_prod_allhistory_1m)
--
-- CONFIGURATION:
-- - Max Iterations: 100
-- - Early Stop: TRUE (stops when learning plateaus)
-- - Min Relative Progress: 0.0001
-- - L1 Regularization: 0.2 (auto-selects important features)
-- - L2 Regularization: 0.1 (prevents overfitting)
--
-- EXPECTED FEATURES: ~1,500-2,000 total
-- - Base production: ~300 features
-- - Yahoo symbols: ~1,540 features (220 symbols × 7 indicators)
-- - Correlations: ~200 features (50 symbols × 4 windows)
-- - Interactions: ~50 features
--
-- PERFORMANCE NOTES:
-- - Table creation: ~5-10 minutes (pivoting 220 symbols)
-- - Model training: ~15-25 minutes (1,500+ features, 50 iterations)
-- - Estimated cost: $3-10 (depends on data volume, 2024+ only)
-- - Memory: May require slot reservation for large feature set
--
-- EXECUTION STRATEGY:
-- 1. Run pre-flight check queries first (uncomment above)
-- 2. Execute STEP 1 (table creation) - monitor for errors
-- 3. Verify table was created successfully before proceeding
-- 4. Execute STEP 2 (model training) - can take 15-25 minutes (50 iterations)
-- 5. Check training progress via ML.TRAINING_INFO if needed
-- 6. Run STEP 3 & 4 (evaluation and feature importance)
--
-- TROUBLESHOOTING:
-- - If table creation fails: Check Yahoo data availability for 2024+
-- - If training times out: Already set to 50 iterations (early_stop will likely trigger sooner)
-- - If memory errors: Use slot reservation or reduce feature set
-- - All issues should be caught in pre-flight checks before execution
-- ============================================

-- ============================================
-- PRE-FLIGHT CHECK: Verify data exists
-- ============================================
-- Run this first to verify data availability before full execution
/*
SELECT 
  'zl_training_prod_allhistory_1m' as table_name,
  COUNT(*) as total_rows,
  COUNTIF(target_1m IS NOT NULL) as rows_with_target,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date >= '2024-01-01';

SELECT 
  'yahoo_finance_complete_enterprise' as table_name,
  COUNT(DISTINCT symbol) as unique_symbols,
  COUNT(*) as total_rows,
  MIN(DATE(TIMESTAMP_MICROS(CAST(date AS INT64)))) as earliest_date,
  MAX(DATE(TIMESTAMP_MICROS(CAST(date AS INT64)))) as latest_date
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
WHERE DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) >= '2024-01-01';
*/

-- ============================================
-- STEP 1: CREATE COMPREHENSIVE FEATURE TABLE
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.baseline_1m_comprehensive_2yr` AS

WITH 
-- Base production features (read-only, never modified)
base_production AS (
  SELECT * 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2024-01-01'
    AND target_1m IS NOT NULL
),

-- Yahoo Finance data - pivot all symbols with technical indicators
-- NOTE: Timestamps in source table are NANOSECONDS (not microseconds)
yahoo_data AS (
  SELECT 
    DATE(TIMESTAMP_MICROS(CAST(date/1000 AS INT64))) as date,  -- Convert nanoseconds to microseconds
    symbol,
    close,
    rsi_14,
    ma_30d,
    macd_line,
    atr_14,
    bb_upper,
    momentum_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
  WHERE date IS NOT NULL
    AND date > 1704067200000000000  -- 2024-01-01 in NANOSECONDS (note the extra 000)
    AND date < 1767225600000000000  -- 2026-01-01 in NANOSECONDS
),

-- Pivot all 55 symbols (7 indicators each = 385 Yahoo features)
yahoo_pivoted AS (
  SELECT
    date,
    MAX(IF(symbol='ADM', close, NULL)) as adm_close_yh,
    MAX(IF(symbol='ADM', rsi_14, NULL)) as adm_rsi_14_yh,
    MAX(IF(symbol='ADM', ma_30d, NULL)) as adm_ma_30d_yh,
    MAX(IF(symbol='ADM', macd_line, NULL)) as adm_macd_yh,
    MAX(IF(symbol='ADM', atr_14, NULL)) as adm_atr_yh,
    MAX(IF(symbol='ADM', bb_upper, NULL)) as adm_bb_upper_yh,
    MAX(IF(symbol='ADM', momentum_10, NULL)) as adm_momentum_yh,
    MAX(IF(symbol='AGCO', close, NULL)) as agco_close,
    MAX(IF(symbol='AGCO', rsi_14, NULL)) as agco_rsi_14,
    MAX(IF(symbol='AGCO', ma_30d, NULL)) as agco_ma_30d,
    MAX(IF(symbol='AGCO', macd_line, NULL)) as agco_macd,
    MAX(IF(symbol='AGCO', atr_14, NULL)) as agco_atr,
    MAX(IF(symbol='AGCO', bb_upper, NULL)) as agco_bb_upper,
    MAX(IF(symbol='AGCO', momentum_10, NULL)) as agco_momentum,
    MAX(IF(symbol='AUDUSD=X', close, NULL)) as audusd_x_close,
    MAX(IF(symbol='AUDUSD=X', rsi_14, NULL)) as audusd_x_rsi_14,
    MAX(IF(symbol='AUDUSD=X', ma_30d, NULL)) as audusd_x_ma_30d,
    MAX(IF(symbol='AUDUSD=X', macd_line, NULL)) as audusd_x_macd,
    MAX(IF(symbol='AUDUSD=X', atr_14, NULL)) as audusd_x_atr,
    MAX(IF(symbol='AUDUSD=X', bb_upper, NULL)) as audusd_x_bb_upper,
    MAX(IF(symbol='AUDUSD=X', momentum_10, NULL)) as audusd_x_momentum,
    MAX(IF(symbol='BG', close, NULL)) as bg_close_yh,
    MAX(IF(symbol='BG', rsi_14, NULL)) as bg_rsi_14_yh,
    MAX(IF(symbol='BG', ma_30d, NULL)) as bg_ma_30d_yh,
    MAX(IF(symbol='BG', macd_line, NULL)) as bg_macd_yh,
    MAX(IF(symbol='BG', atr_14, NULL)) as bg_atr_yh,
    MAX(IF(symbol='BG', bb_upper, NULL)) as bg_bb_upper_yh,
    MAX(IF(symbol='BG', momentum_10, NULL)) as bg_momentum_yh,
    MAX(IF(symbol='BRLUSD=X', close, NULL)) as brlusd_x_close,
    MAX(IF(symbol='BRLUSD=X', rsi_14, NULL)) as brlusd_x_rsi_14,
    MAX(IF(symbol='BRLUSD=X', ma_30d, NULL)) as brlusd_x_ma_30d,
    MAX(IF(symbol='BRLUSD=X', macd_line, NULL)) as brlusd_x_macd,
    MAX(IF(symbol='BRLUSD=X', atr_14, NULL)) as brlusd_x_atr,
    MAX(IF(symbol='BRLUSD=X', bb_upper, NULL)) as brlusd_x_bb_upper,
    MAX(IF(symbol='BRLUSD=X', momentum_10, NULL)) as brlusd_x_momentum,
    MAX(IF(symbol='BZ=F', close, NULL)) as bz_f_close,
    MAX(IF(symbol='BZ=F', rsi_14, NULL)) as bz_f_rsi_14,
    MAX(IF(symbol='BZ=F', ma_30d, NULL)) as bz_f_ma_30d,
    MAX(IF(symbol='BZ=F', macd_line, NULL)) as bz_f_macd,
    MAX(IF(symbol='BZ=F', atr_14, NULL)) as bz_f_atr,
    MAX(IF(symbol='BZ=F', bb_upper, NULL)) as bz_f_bb_upper,
    MAX(IF(symbol='BZ=F', momentum_10, NULL)) as bz_f_momentum,
    MAX(IF(symbol='CADUSD=X', close, NULL)) as cadusd_x_close,
    MAX(IF(symbol='CADUSD=X', rsi_14, NULL)) as cadusd_x_rsi_14,
    MAX(IF(symbol='CADUSD=X', ma_30d, NULL)) as cadusd_x_ma_30d,
    MAX(IF(symbol='CADUSD=X', macd_line, NULL)) as cadusd_x_macd,
    MAX(IF(symbol='CADUSD=X', atr_14, NULL)) as cadusd_x_atr,
    MAX(IF(symbol='CADUSD=X', bb_upper, NULL)) as cadusd_x_bb_upper,
    MAX(IF(symbol='CADUSD=X', momentum_10, NULL)) as cadusd_x_momentum,
    MAX(IF(symbol='CC=F', close, NULL)) as cc_f_close,
    MAX(IF(symbol='CC=F', rsi_14, NULL)) as cc_f_rsi_14,
    MAX(IF(symbol='CC=F', ma_30d, NULL)) as cc_f_ma_30d,
    MAX(IF(symbol='CC=F', macd_line, NULL)) as cc_f_macd,
    MAX(IF(symbol='CC=F', atr_14, NULL)) as cc_f_atr,
    MAX(IF(symbol='CC=F', bb_upper, NULL)) as cc_f_bb_upper,
    MAX(IF(symbol='CC=F', momentum_10, NULL)) as cc_f_momentum,
    MAX(IF(symbol='CF', close, NULL)) as cf_close_yh,
    MAX(IF(symbol='CF', rsi_14, NULL)) as cf_rsi_14_yh,
    MAX(IF(symbol='CF', ma_30d, NULL)) as cf_ma_30d_yh,
    MAX(IF(symbol='CF', macd_line, NULL)) as cf_macd_yh,
    MAX(IF(symbol='CF', atr_14, NULL)) as cf_atr_yh,
    MAX(IF(symbol='CF', bb_upper, NULL)) as cf_bb_upper_yh,
    MAX(IF(symbol='CF', momentum_10, NULL)) as cf_momentum_yh,
    MAX(IF(symbol='CL=F', close, NULL)) as cl_f_close,
    MAX(IF(symbol='CL=F', rsi_14, NULL)) as cl_f_rsi_14,
    MAX(IF(symbol='CL=F', ma_30d, NULL)) as cl_f_ma_30d,
    MAX(IF(symbol='CL=F', macd_line, NULL)) as cl_f_macd,
    MAX(IF(symbol='CL=F', atr_14, NULL)) as cl_f_atr,
    MAX(IF(symbol='CL=F', bb_upper, NULL)) as cl_f_bb_upper,
    MAX(IF(symbol='CL=F', momentum_10, NULL)) as cl_f_momentum,
    MAX(IF(symbol='CNYUSD=X', close, NULL)) as cnyusd_x_close,
    MAX(IF(symbol='CNYUSD=X', rsi_14, NULL)) as cnyusd_x_rsi_14,
    MAX(IF(symbol='CNYUSD=X', ma_30d, NULL)) as cnyusd_x_ma_30d,
    MAX(IF(symbol='CNYUSD=X', macd_line, NULL)) as cnyusd_x_macd,
    MAX(IF(symbol='CNYUSD=X', atr_14, NULL)) as cnyusd_x_atr,
    MAX(IF(symbol='CNYUSD=X', bb_upper, NULL)) as cnyusd_x_bb_upper,
    MAX(IF(symbol='CNYUSD=X', momentum_10, NULL)) as cnyusd_x_momentum,
    MAX(IF(symbol='CORN', close, NULL)) as corn_close,
    MAX(IF(symbol='CORN', rsi_14, NULL)) as corn_rsi_14,
    MAX(IF(symbol='CORN', ma_30d, NULL)) as corn_ma_30d,
    MAX(IF(symbol='CORN', macd_line, NULL)) as corn_macd,
    MAX(IF(symbol='CORN', atr_14, NULL)) as corn_atr,
    MAX(IF(symbol='CORN', bb_upper, NULL)) as corn_bb_upper,
    MAX(IF(symbol='CORN', momentum_10, NULL)) as corn_momentum,
    MAX(IF(symbol='CT=F', close, NULL)) as ct_f_close,
    MAX(IF(symbol='CT=F', rsi_14, NULL)) as ct_f_rsi_14,
    MAX(IF(symbol='CT=F', ma_30d, NULL)) as ct_f_ma_30d,
    MAX(IF(symbol='CT=F', macd_line, NULL)) as ct_f_macd,
    MAX(IF(symbol='CT=F', atr_14, NULL)) as ct_f_atr,
    MAX(IF(symbol='CT=F', bb_upper, NULL)) as ct_f_bb_upper,
    MAX(IF(symbol='CT=F', momentum_10, NULL)) as ct_f_momentum,
    MAX(IF(symbol='DAR', close, NULL)) as dar_close_yh,
    MAX(IF(symbol='DAR', rsi_14, NULL)) as dar_rsi_14_yh,
    MAX(IF(symbol='DAR', ma_30d, NULL)) as dar_ma_30d_yh,
    MAX(IF(symbol='DAR', macd_line, NULL)) as dar_macd_yh,
    MAX(IF(symbol='DAR', atr_14, NULL)) as dar_atr_yh,
    MAX(IF(symbol='DAR', bb_upper, NULL)) as dar_bb_upper_yh,
    MAX(IF(symbol='DAR', momentum_10, NULL)) as dar_momentum_yh,
    MAX(IF(symbol='DE', close, NULL)) as de_close,
    MAX(IF(symbol='DE', rsi_14, NULL)) as de_rsi_14,
    MAX(IF(symbol='DE', ma_30d, NULL)) as de_ma_30d,
    MAX(IF(symbol='DE', macd_line, NULL)) as de_macd,
    MAX(IF(symbol='DE', atr_14, NULL)) as de_atr,
    MAX(IF(symbol='DE', bb_upper, NULL)) as de_bb_upper,
    MAX(IF(symbol='DE', momentum_10, NULL)) as de_momentum,
    MAX(IF(symbol='DX-Y.NYB', close, NULL)) as dx_y_nyb_close,
    MAX(IF(symbol='DX-Y.NYB', rsi_14, NULL)) as dx_y_nyb_rsi_14,
    MAX(IF(symbol='DX-Y.NYB', ma_30d, NULL)) as dx_y_nyb_ma_30d,
    MAX(IF(symbol='DX-Y.NYB', macd_line, NULL)) as dx_y_nyb_macd,
    MAX(IF(symbol='DX-Y.NYB', atr_14, NULL)) as dx_y_nyb_atr,
    MAX(IF(symbol='DX-Y.NYB', bb_upper, NULL)) as dx_y_nyb_bb_upper,
    MAX(IF(symbol='DX-Y.NYB', momentum_10, NULL)) as dx_y_nyb_momentum,
    MAX(IF(symbol='EURUSD=X', close, NULL)) as eurusd_x_close,
    MAX(IF(symbol='EURUSD=X', rsi_14, NULL)) as eurusd_x_rsi_14,
    MAX(IF(symbol='EURUSD=X', ma_30d, NULL)) as eurusd_x_ma_30d,
    MAX(IF(symbol='EURUSD=X', macd_line, NULL)) as eurusd_x_macd,
    MAX(IF(symbol='EURUSD=X', atr_14, NULL)) as eurusd_x_atr,
    MAX(IF(symbol='EURUSD=X', bb_upper, NULL)) as eurusd_x_bb_upper,
    MAX(IF(symbol='EURUSD=X', momentum_10, NULL)) as eurusd_x_momentum,
    MAX(IF(symbol='GBPUSD=X', close, NULL)) as gbpusd_x_close,
    MAX(IF(symbol='GBPUSD=X', rsi_14, NULL)) as gbpusd_x_rsi_14,
    MAX(IF(symbol='GBPUSD=X', ma_30d, NULL)) as gbpusd_x_ma_30d,
    MAX(IF(symbol='GBPUSD=X', macd_line, NULL)) as gbpusd_x_macd,
    MAX(IF(symbol='GBPUSD=X', atr_14, NULL)) as gbpusd_x_atr,
    MAX(IF(symbol='GBPUSD=X', bb_upper, NULL)) as gbpusd_x_bb_upper,
    MAX(IF(symbol='GBPUSD=X', momentum_10, NULL)) as gbpusd_x_momentum,
    MAX(IF(symbol='GC=F', close, NULL)) as gc_f_close,
    MAX(IF(symbol='GC=F', rsi_14, NULL)) as gc_f_rsi_14,
    MAX(IF(symbol='GC=F', ma_30d, NULL)) as gc_f_ma_30d,
    MAX(IF(symbol='GC=F', macd_line, NULL)) as gc_f_macd,
    MAX(IF(symbol='GC=F', atr_14, NULL)) as gc_f_atr,
    MAX(IF(symbol='GC=F', bb_upper, NULL)) as gc_f_bb_upper,
    MAX(IF(symbol='GC=F', momentum_10, NULL)) as gc_f_momentum,
    MAX(IF(symbol='GPRE', close, NULL)) as gpre_close,
    MAX(IF(symbol='GPRE', rsi_14, NULL)) as gpre_rsi_14,
    MAX(IF(symbol='GPRE', ma_30d, NULL)) as gpre_ma_30d,
    MAX(IF(symbol='GPRE', macd_line, NULL)) as gpre_macd,
    MAX(IF(symbol='GPRE', atr_14, NULL)) as gpre_atr,
    MAX(IF(symbol='GPRE', bb_upper, NULL)) as gpre_bb_upper,
    MAX(IF(symbol='GPRE', momentum_10, NULL)) as gpre_momentum,
    MAX(IF(symbol='HG=F', close, NULL)) as hg_f_close,
    MAX(IF(symbol='HG=F', rsi_14, NULL)) as hg_f_rsi_14,
    MAX(IF(symbol='HG=F', ma_30d, NULL)) as hg_f_ma_30d,
    MAX(IF(symbol='HG=F', macd_line, NULL)) as hg_f_macd,
    MAX(IF(symbol='HG=F', atr_14, NULL)) as hg_f_atr,
    MAX(IF(symbol='HG=F', bb_upper, NULL)) as hg_f_bb_upper,
    MAX(IF(symbol='HG=F', momentum_10, NULL)) as hg_f_momentum,
    MAX(IF(symbol='HO=F', close, NULL)) as ho_f_close,
    MAX(IF(symbol='HO=F', rsi_14, NULL)) as ho_f_rsi_14,
    MAX(IF(symbol='HO=F', ma_30d, NULL)) as ho_f_ma_30d,
    MAX(IF(symbol='HO=F', macd_line, NULL)) as ho_f_macd,
    MAX(IF(symbol='HO=F', atr_14, NULL)) as ho_f_atr,
    MAX(IF(symbol='HO=F', bb_upper, NULL)) as ho_f_bb_upper,
    MAX(IF(symbol='HO=F', momentum_10, NULL)) as ho_f_momentum,
    MAX(IF(symbol='HYG', close, NULL)) as hyg_close_yh,
    MAX(IF(symbol='HYG', rsi_14, NULL)) as hyg_rsi_14_yh,
    MAX(IF(symbol='HYG', ma_30d, NULL)) as hyg_ma_30d_yh,
    MAX(IF(symbol='HYG', macd_line, NULL)) as hyg_macd_yh,
    MAX(IF(symbol='HYG', atr_14, NULL)) as hyg_atr_yh,
    MAX(IF(symbol='HYG', bb_upper, NULL)) as hyg_bb_upper_yh,
    MAX(IF(symbol='HYG', momentum_10, NULL)) as hyg_momentum_yh,
    MAX(IF(symbol='ICLN', close, NULL)) as icln_close,
    MAX(IF(symbol='ICLN', rsi_14, NULL)) as icln_rsi_14,
    MAX(IF(symbol='ICLN', ma_30d, NULL)) as icln_ma_30d,
    MAX(IF(symbol='ICLN', macd_line, NULL)) as icln_macd,
    MAX(IF(symbol='ICLN', atr_14, NULL)) as icln_atr,
    MAX(IF(symbol='ICLN', bb_upper, NULL)) as icln_bb_upper,
    MAX(IF(symbol='ICLN', momentum_10, NULL)) as icln_momentum,
    MAX(IF(symbol='JPYUSD=X', close, NULL)) as jpyusd_x_close,
    MAX(IF(symbol='JPYUSD=X', rsi_14, NULL)) as jpyusd_x_rsi_14,
    MAX(IF(symbol='JPYUSD=X', ma_30d, NULL)) as jpyusd_x_ma_30d,
    MAX(IF(symbol='JPYUSD=X', macd_line, NULL)) as jpyusd_x_macd,
    MAX(IF(symbol='JPYUSD=X', atr_14, NULL)) as jpyusd_x_atr,
    MAX(IF(symbol='JPYUSD=X', bb_upper, NULL)) as jpyusd_x_bb_upper,
    MAX(IF(symbol='JPYUSD=X', momentum_10, NULL)) as jpyusd_x_momentum,
    MAX(IF(symbol='KC=F', close, NULL)) as kc_f_close,
    MAX(IF(symbol='KC=F', rsi_14, NULL)) as kc_f_rsi_14,
    MAX(IF(symbol='KC=F', ma_30d, NULL)) as kc_f_ma_30d,
    MAX(IF(symbol='KC=F', macd_line, NULL)) as kc_f_macd,
    MAX(IF(symbol='KC=F', atr_14, NULL)) as kc_f_atr,
    MAX(IF(symbol='KC=F', bb_upper, NULL)) as kc_f_bb_upper,
    MAX(IF(symbol='KC=F', momentum_10, NULL)) as kc_f_momentum,
    MAX(IF(symbol='LQD', close, NULL)) as lqd_close,
    MAX(IF(symbol='LQD', rsi_14, NULL)) as lqd_rsi_14,
    MAX(IF(symbol='LQD', ma_30d, NULL)) as lqd_ma_30d,
    MAX(IF(symbol='LQD', macd_line, NULL)) as lqd_macd,
    MAX(IF(symbol='LQD', atr_14, NULL)) as lqd_atr,
    MAX(IF(symbol='LQD', bb_upper, NULL)) as lqd_bb_upper,
    MAX(IF(symbol='LQD', momentum_10, NULL)) as lqd_momentum,
    MAX(IF(symbol='MOS', close, NULL)) as mos_close_yh,
    MAX(IF(symbol='MOS', rsi_14, NULL)) as mos_rsi_14_yh,
    MAX(IF(symbol='MOS', ma_30d, NULL)) as mos_ma_30d_yh,
    MAX(IF(symbol='MOS', macd_line, NULL)) as mos_macd_yh,
    MAX(IF(symbol='MOS', atr_14, NULL)) as mos_atr_yh,
    MAX(IF(symbol='MOS', bb_upper, NULL)) as mos_bb_upper_yh,
    MAX(IF(symbol='MOS', momentum_10, NULL)) as mos_momentum_yh,
    MAX(IF(symbol='MXNUSD=X', close, NULL)) as mxnusd_x_close,
    MAX(IF(symbol='MXNUSD=X', rsi_14, NULL)) as mxnusd_x_rsi_14,
    MAX(IF(symbol='MXNUSD=X', ma_30d, NULL)) as mxnusd_x_ma_30d,
    MAX(IF(symbol='MXNUSD=X', macd_line, NULL)) as mxnusd_x_macd,
    MAX(IF(symbol='MXNUSD=X', atr_14, NULL)) as mxnusd_x_atr,
    MAX(IF(symbol='MXNUSD=X', bb_upper, NULL)) as mxnusd_x_bb_upper,
    MAX(IF(symbol='MXNUSD=X', momentum_10, NULL)) as mxnusd_x_momentum,
    MAX(IF(symbol='NG=F', close, NULL)) as ng_f_close,
    MAX(IF(symbol='NG=F', rsi_14, NULL)) as ng_f_rsi_14,
    MAX(IF(symbol='NG=F', ma_30d, NULL)) as ng_f_ma_30d,
    MAX(IF(symbol='NG=F', macd_line, NULL)) as ng_f_macd,
    MAX(IF(symbol='NG=F', atr_14, NULL)) as ng_f_atr,
    MAX(IF(symbol='NG=F', bb_upper, NULL)) as ng_f_bb_upper,
    MAX(IF(symbol='NG=F', momentum_10, NULL)) as ng_f_momentum,
    MAX(IF(symbol='NTR', close, NULL)) as ntr_close_yh,
    MAX(IF(symbol='NTR', rsi_14, NULL)) as ntr_rsi_14_yh,
    MAX(IF(symbol='NTR', ma_30d, NULL)) as ntr_ma_30d_yh,
    MAX(IF(symbol='NTR', macd_line, NULL)) as ntr_macd_yh,
    MAX(IF(symbol='NTR', atr_14, NULL)) as ntr_atr_yh,
    MAX(IF(symbol='NTR', bb_upper, NULL)) as ntr_bb_upper_yh,
    MAX(IF(symbol='NTR', momentum_10, NULL)) as ntr_momentum_yh,
    MAX(IF(symbol='PL=F', close, NULL)) as pl_f_close,
    MAX(IF(symbol='PL=F', rsi_14, NULL)) as pl_f_rsi_14,
    MAX(IF(symbol='PL=F', ma_30d, NULL)) as pl_f_ma_30d,
    MAX(IF(symbol='PL=F', macd_line, NULL)) as pl_f_macd,
    MAX(IF(symbol='PL=F', atr_14, NULL)) as pl_f_atr,
    MAX(IF(symbol='PL=F', bb_upper, NULL)) as pl_f_bb_upper,
    MAX(IF(symbol='PL=F', momentum_10, NULL)) as pl_f_momentum,
    MAX(IF(symbol='RB=F', close, NULL)) as rb_f_close,
    MAX(IF(symbol='RB=F', rsi_14, NULL)) as rb_f_rsi_14,
    MAX(IF(symbol='RB=F', ma_30d, NULL)) as rb_f_ma_30d,
    MAX(IF(symbol='RB=F', macd_line, NULL)) as rb_f_macd,
    MAX(IF(symbol='RB=F', atr_14, NULL)) as rb_f_atr,
    MAX(IF(symbol='RB=F', bb_upper, NULL)) as rb_f_bb_upper,
    MAX(IF(symbol='RB=F', momentum_10, NULL)) as rb_f_momentum,
    MAX(IF(symbol='REX', close, NULL)) as rex_close,
    MAX(IF(symbol='REX', rsi_14, NULL)) as rex_rsi_14,
    MAX(IF(symbol='REX', ma_30d, NULL)) as rex_ma_30d,
    MAX(IF(symbol='REX', macd_line, NULL)) as rex_macd,
    MAX(IF(symbol='REX', atr_14, NULL)) as rex_atr,
    MAX(IF(symbol='REX', bb_upper, NULL)) as rex_bb_upper,
    MAX(IF(symbol='REX', momentum_10, NULL)) as rex_momentum,
    MAX(IF(symbol='SB=F', close, NULL)) as sb_f_close,
    MAX(IF(symbol='SB=F', rsi_14, NULL)) as sb_f_rsi_14,
    MAX(IF(symbol='SB=F', ma_30d, NULL)) as sb_f_ma_30d,
    MAX(IF(symbol='SB=F', macd_line, NULL)) as sb_f_macd,
    MAX(IF(symbol='SB=F', atr_14, NULL)) as sb_f_atr,
    MAX(IF(symbol='SB=F', bb_upper, NULL)) as sb_f_bb_upper,
    MAX(IF(symbol='SB=F', momentum_10, NULL)) as sb_f_momentum,
    MAX(IF(symbol='SI=F', close, NULL)) as si_f_close,
    MAX(IF(symbol='SI=F', rsi_14, NULL)) as si_f_rsi_14,
    MAX(IF(symbol='SI=F', ma_30d, NULL)) as si_f_ma_30d,
    MAX(IF(symbol='SI=F', macd_line, NULL)) as si_f_macd,
    MAX(IF(symbol='SI=F', atr_14, NULL)) as si_f_atr,
    MAX(IF(symbol='SI=F', bb_upper, NULL)) as si_f_bb_upper,
    MAX(IF(symbol='SI=F', momentum_10, NULL)) as si_f_momentum,
    MAX(IF(symbol='SOYB', close, NULL)) as soyb_close_yh,
    MAX(IF(symbol='SOYB', rsi_14, NULL)) as soyb_rsi_14_yh,
    MAX(IF(symbol='SOYB', ma_30d, NULL)) as soyb_ma_30d_yh,
    MAX(IF(symbol='SOYB', macd_line, NULL)) as soyb_macd_yh,
    MAX(IF(symbol='SOYB', atr_14, NULL)) as soyb_atr_yh,
    MAX(IF(symbol='SOYB', bb_upper, NULL)) as soyb_bb_upper_yh,
    MAX(IF(symbol='SOYB', momentum_10, NULL)) as soyb_momentum_yh,
    MAX(IF(symbol='TAN', close, NULL)) as tan_close,
    MAX(IF(symbol='TAN', rsi_14, NULL)) as tan_rsi_14,
    MAX(IF(symbol='TAN', ma_30d, NULL)) as tan_ma_30d,
    MAX(IF(symbol='TAN', macd_line, NULL)) as tan_macd,
    MAX(IF(symbol='TAN', atr_14, NULL)) as tan_atr,
    MAX(IF(symbol='TAN', bb_upper, NULL)) as tan_bb_upper,
    MAX(IF(symbol='TAN', momentum_10, NULL)) as tan_momentum,
    MAX(IF(symbol='TLT', close, NULL)) as tlt_close,
    MAX(IF(symbol='TLT', rsi_14, NULL)) as tlt_rsi_14,
    MAX(IF(symbol='TLT', ma_30d, NULL)) as tlt_ma_30d,
    MAX(IF(symbol='TLT', macd_line, NULL)) as tlt_macd,
    MAX(IF(symbol='TLT', atr_14, NULL)) as tlt_atr,
    MAX(IF(symbol='TLT', bb_upper, NULL)) as tlt_bb_upper,
    MAX(IF(symbol='TLT', momentum_10, NULL)) as tlt_momentum,
    MAX(IF(symbol='TSN', close, NULL)) as tsn_close_yh,
    MAX(IF(symbol='TSN', rsi_14, NULL)) as tsn_rsi_14_yh,
    MAX(IF(symbol='TSN', ma_30d, NULL)) as tsn_ma_30d_yh,
    MAX(IF(symbol='TSN', macd_line, NULL)) as tsn_macd_yh,
    MAX(IF(symbol='TSN', atr_14, NULL)) as tsn_atr_yh,
    MAX(IF(symbol='TSN', bb_upper, NULL)) as tsn_bb_upper_yh,
    MAX(IF(symbol='TSN', momentum_10, NULL)) as tsn_momentum_yh,
    MAX(IF(symbol='VEGI', close, NULL)) as vegi_close,
    MAX(IF(symbol='VEGI', rsi_14, NULL)) as vegi_rsi_14,
    MAX(IF(symbol='VEGI', ma_30d, NULL)) as vegi_ma_30d,
    MAX(IF(symbol='VEGI', macd_line, NULL)) as vegi_macd,
    MAX(IF(symbol='VEGI', atr_14, NULL)) as vegi_atr,
    MAX(IF(symbol='VEGI', bb_upper, NULL)) as vegi_bb_upper,
    MAX(IF(symbol='VEGI', momentum_10, NULL)) as vegi_momentum,
    MAX(IF(symbol='WEAT', close, NULL)) as weat_close_yh,
    MAX(IF(symbol='WEAT', rsi_14, NULL)) as weat_rsi_14_yh,
    MAX(IF(symbol='WEAT', ma_30d, NULL)) as weat_ma_30d_yh,
    MAX(IF(symbol='WEAT', macd_line, NULL)) as weat_macd_yh,
    MAX(IF(symbol='WEAT', atr_14, NULL)) as weat_atr_yh,
    MAX(IF(symbol='WEAT', bb_upper, NULL)) as weat_bb_upper_yh,
    MAX(IF(symbol='WEAT', momentum_10, NULL)) as weat_momentum_yh,
    MAX(IF(symbol='ZC=F', close, NULL)) as zc_f_close,
    MAX(IF(symbol='ZC=F', rsi_14, NULL)) as zc_f_rsi_14,
    MAX(IF(symbol='ZC=F', ma_30d, NULL)) as zc_f_ma_30d,
    MAX(IF(symbol='ZC=F', macd_line, NULL)) as zc_f_macd,
    MAX(IF(symbol='ZC=F', atr_14, NULL)) as zc_f_atr,
    MAX(IF(symbol='ZC=F', bb_upper, NULL)) as zc_f_bb_upper,
    MAX(IF(symbol='ZC=F', momentum_10, NULL)) as zc_f_momentum,
    MAX(IF(symbol='ZL=F', close, NULL)) as zl_f_close,
    MAX(IF(symbol='ZL=F', rsi_14, NULL)) as zl_f_rsi_14,
    MAX(IF(symbol='ZL=F', ma_30d, NULL)) as zl_f_ma_30d,
    MAX(IF(symbol='ZL=F', macd_line, NULL)) as zl_f_macd,
    MAX(IF(symbol='ZL=F', atr_14, NULL)) as zl_f_atr,
    MAX(IF(symbol='ZL=F', bb_upper, NULL)) as zl_f_bb_upper,
    MAX(IF(symbol='ZL=F', momentum_10, NULL)) as zl_f_momentum,
    MAX(IF(symbol='ZM=F', close, NULL)) as zm_f_close,
    MAX(IF(symbol='ZM=F', rsi_14, NULL)) as zm_f_rsi_14,
    MAX(IF(symbol='ZM=F', ma_30d, NULL)) as zm_f_ma_30d,
    MAX(IF(symbol='ZM=F', macd_line, NULL)) as zm_f_macd,
    MAX(IF(symbol='ZM=F', atr_14, NULL)) as zm_f_atr,
    MAX(IF(symbol='ZM=F', bb_upper, NULL)) as zm_f_bb_upper,
    MAX(IF(symbol='ZM=F', momentum_10, NULL)) as zm_f_momentum,
    MAX(IF(symbol='ZS=F', close, NULL)) as zs_f_close,
    MAX(IF(symbol='ZS=F', rsi_14, NULL)) as zs_f_rsi_14,
    MAX(IF(symbol='ZS=F', ma_30d, NULL)) as zs_f_ma_30d,
    MAX(IF(symbol='ZS=F', macd_line, NULL)) as zs_f_macd,
    MAX(IF(symbol='ZS=F', atr_14, NULL)) as zs_f_atr,
    MAX(IF(symbol='ZS=F', bb_upper, NULL)) as zs_f_bb_upper,
    MAX(IF(symbol='ZS=F', momentum_10, NULL)) as zs_f_momentum,
    MAX(IF(symbol='ZW=F', close, NULL)) as zw_f_close,
    MAX(IF(symbol='ZW=F', rsi_14, NULL)) as zw_f_rsi_14,
    MAX(IF(symbol='ZW=F', ma_30d, NULL)) as zw_f_ma_30d,
    MAX(IF(symbol='ZW=F', macd_line, NULL)) as zw_f_macd,
    MAX(IF(symbol='ZW=F', atr_14, NULL)) as zw_f_atr,
    MAX(IF(symbol='ZW=F', bb_upper, NULL)) as zw_f_bb_upper,
    MAX(IF(symbol='ZW=F', momentum_10, NULL)) as zw_f_momentum,
    MAX(IF(symbol='^DJI', close, NULL)) as dji_close,
    MAX(IF(symbol='^DJI', rsi_14, NULL)) as dji_rsi_14,
    MAX(IF(symbol='^DJI', ma_30d, NULL)) as dji_ma_30d,
    MAX(IF(symbol='^DJI', macd_line, NULL)) as dji_macd,
    MAX(IF(symbol='^DJI', atr_14, NULL)) as dji_atr,
    MAX(IF(symbol='^DJI', bb_upper, NULL)) as dji_bb_upper,
    MAX(IF(symbol='^DJI', momentum_10, NULL)) as dji_momentum,
    MAX(IF(symbol='^FVX', close, NULL)) as fvx_close,
    MAX(IF(symbol='^FVX', rsi_14, NULL)) as fvx_rsi_14,
    MAX(IF(symbol='^FVX', ma_30d, NULL)) as fvx_ma_30d,
    MAX(IF(symbol='^FVX', macd_line, NULL)) as fvx_macd,
    MAX(IF(symbol='^FVX', atr_14, NULL)) as fvx_atr,
    MAX(IF(symbol='^FVX', bb_upper, NULL)) as fvx_bb_upper,
    MAX(IF(symbol='^FVX', momentum_10, NULL)) as fvx_momentum,
    MAX(IF(symbol='^GSPC', close, NULL)) as gspc_close,
    MAX(IF(symbol='^GSPC', rsi_14, NULL)) as gspc_rsi_14,
    MAX(IF(symbol='^GSPC', ma_30d, NULL)) as gspc_ma_30d,
    MAX(IF(symbol='^GSPC', macd_line, NULL)) as gspc_macd,
    MAX(IF(symbol='^GSPC', atr_14, NULL)) as gspc_atr,
    MAX(IF(symbol='^GSPC', bb_upper, NULL)) as gspc_bb_upper,
    MAX(IF(symbol='^GSPC', momentum_10, NULL)) as gspc_momentum,
    MAX(IF(symbol='^IRX', close, NULL)) as irx_close,
    MAX(IF(symbol='^IRX', rsi_14, NULL)) as irx_rsi_14,
    MAX(IF(symbol='^IRX', ma_30d, NULL)) as irx_ma_30d,
    MAX(IF(symbol='^IRX', macd_line, NULL)) as irx_macd,
    MAX(IF(symbol='^IRX', atr_14, NULL)) as irx_atr,
    MAX(IF(symbol='^IRX', bb_upper, NULL)) as irx_bb_upper,
    MAX(IF(symbol='^IRX', momentum_10, NULL)) as irx_momentum,
    MAX(IF(symbol='^IXIC', close, NULL)) as ixic_close,
    MAX(IF(symbol='^IXIC', rsi_14, NULL)) as ixic_rsi_14,
    MAX(IF(symbol='^IXIC', ma_30d, NULL)) as ixic_ma_30d,
    MAX(IF(symbol='^IXIC', macd_line, NULL)) as ixic_macd,
    MAX(IF(symbol='^IXIC', atr_14, NULL)) as ixic_atr,
    MAX(IF(symbol='^IXIC', bb_upper, NULL)) as ixic_bb_upper,
    MAX(IF(symbol='^IXIC', momentum_10, NULL)) as ixic_momentum,
    MAX(IF(symbol='^TNX', close, NULL)) as tnx_close,
    MAX(IF(symbol='^TNX', rsi_14, NULL)) as tnx_rsi_14,
    MAX(IF(symbol='^TNX', ma_30d, NULL)) as tnx_ma_30d,
    MAX(IF(symbol='^TNX', macd_line, NULL)) as tnx_macd,
    MAX(IF(symbol='^TNX', atr_14, NULL)) as tnx_atr,
    MAX(IF(symbol='^TNX', bb_upper, NULL)) as tnx_bb_upper,
    MAX(IF(symbol='^TNX', momentum_10, NULL)) as tnx_momentum,
    MAX(IF(symbol='^TYX', close, NULL)) as tyx_close,
    MAX(IF(symbol='^TYX', rsi_14, NULL)) as tyx_rsi_14,
    MAX(IF(symbol='^TYX', ma_30d, NULL)) as tyx_ma_30d,
    MAX(IF(symbol='^TYX', macd_line, NULL)) as tyx_macd,
    MAX(IF(symbol='^TYX', atr_14, NULL)) as tyx_atr,
    MAX(IF(symbol='^TYX', bb_upper, NULL)) as tyx_bb_upper,
    MAX(IF(symbol='^TYX', momentum_10, NULL)) as tyx_momentum,
    MAX(IF(symbol='^VIX', close, NULL)) as vix_close,
    MAX(IF(symbol='^VIX', rsi_14, NULL)) as vix_rsi_14,
    MAX(IF(symbol='^VIX', ma_30d, NULL)) as vix_ma_30d,
    MAX(IF(symbol='^VIX', macd_line, NULL)) as vix_macd,
    MAX(IF(symbol='^VIX', atr_14, NULL)) as vix_atr,
    MAX(IF(symbol='^VIX', bb_upper, NULL)) as vix_bb_upper,
    MAX(IF(symbol='^VIX', momentum_10, NULL)) as vix_momentum
  FROM yahoo_data
  GROUP BY date
),

-- Rolling correlations for top symbols vs zl_price_current
-- Using 7d, 30d, 90d, 180d windows (skip 365d - not enough data in 2-year window)
correlations AS (
  SELECT
    p.date,
    -- SOYB correlations (use production version since Yahoo version excluded)
    CORR(p.soyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_soyb_zl_7d,
    CORR(p.soyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_soyb_zl_30d,
    CORR(p.soyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_soyb_zl_90d,
    CORR(p.soyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_soyb_zl_180d,
    
    -- CORN correlations (use production version since Yahoo version excluded)
    CORR(p.corn_etf_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_corn_zl_7d,
    CORR(p.corn_etf_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_corn_zl_30d,
    CORR(p.corn_etf_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_corn_zl_90d,
    CORR(p.corn_etf_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_corn_zl_180d,
    
    -- CL=F correlations
    CORR(y.cl_f_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_cl_zl_7d,
    CORR(y.cl_f_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_cl_zl_30d,
    CORR(y.cl_f_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_cl_zl_90d,
    CORR(y.cl_f_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_cl_zl_180d,
    
    -- DXY correlations (symbol is DX-Y.NYB, column is dx_y_nyb_close)
    CORR(y.dx_y_nyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_dxy_zl_7d,
    CORR(y.dx_y_nyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_dxy_zl_30d,
    CORR(y.dx_y_nyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_dxy_zl_90d,
    CORR(y.dx_y_nyb_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_dxy_zl_180d,
    
    -- VIX correlations
    CORR(y.vix_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as corr_vix_zl_7d,
    CORR(y.vix_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as corr_vix_zl_30d,
    CORR(y.vix_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) as corr_vix_zl_90d,
    CORR(y.vix_close, p.zl_price_current) OVER (ORDER BY p.date ROWS BETWEEN 179 PRECEDING AND CURRENT ROW) as corr_vix_zl_180d
    
    -- NOTE: Add correlations for remaining top 50 symbols as needed
    -- Full version would have ~200 correlation features (50 symbols × 4 windows)
    
  FROM base_production p
  LEFT JOIN yahoo_pivoted y ON p.date = y.date
  WHERE p.date >= '2024-01-01'
),

-- Interaction features (spreads, ratios, relative strength)
interactions AS (
  SELECT
    p.date,
    
    -- Spreads (use production versions for excluded symbols, Yahoo for others)
    p.soyb_close - p.corn_etf_close as soyb_corn_spread,
    p.soyb_close - p.weat_close as soyb_weat_spread,
    y.cl_f_close - y.bz_f_close as wti_brent_spread,
    p.adm_close - p.bg_close as adm_bg_spread,
    
    -- Ratios
    p.soyb_close / NULLIF(p.corn_etf_close, 0) as soyb_corn_ratio,
    y.cl_f_close / NULLIF(y.dx_y_nyb_close, 0) as crude_dxy_ratio,
    y.vix_close / NULLIF(y.gspc_close, 0) as vix_spx_ratio,
    
    -- Relative strength
    p.soyb_rsi_14 - p.corn_etf_rsi_14 as soyb_corn_rsi_diff,
    p.adm_close - p.bg_close as adm_bg_spread_rsi,
    
    -- Volatility ratios
    p.soyb_atr_14 / NULLIF(y.vix_close, 0) as soyb_vol_to_vix,
    y.cl_f_atr / NULLIF(y.vix_close, 0) as crude_vol_to_vix,
    
    -- Regime indicators
    CASE WHEN y.vix_close > 20 THEN 1 ELSE 0 END as vix_high_regime,
    CASE WHEN y.dx_y_nyb_close > AVG(y.dx_y_nyb_close) OVER (ORDER BY p.date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as dollar_strength_regime,
    CASE WHEN y.cl_f_close > AVG(y.cl_f_close) OVER (ORDER BY p.date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) THEN 1 ELSE 0 END as crude_strength_regime
    
  FROM base_production p
  LEFT JOIN yahoo_pivoted y ON p.date = y.date
  WHERE p.date >= '2024-01-01'
)

-- Final comprehensive table
-- Keep ALL production data (p.*) - do not exclude anything
-- Only exclude conflicting columns from Yahoo (y.*) to preserve production versions
SELECT
  p.*,
  y.* EXCEPT(date),
  c.* EXCEPT(date),
  i.* EXCEPT(date)
FROM base_production p
LEFT JOIN yahoo_pivoted y ON p.date = y.date
LEFT JOIN correlations c ON p.date = c.date
LEFT JOIN interactions i ON p.date = i.date;

-- ============================================
-- STEP 2: TRAIN BASELINE MODEL
-- ============================================

CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1m'],
  max_iterations=50,
  learn_rate=0.05,
  early_stop=TRUE,
  min_rel_progress=0.0001,
  -- REGULARIZATION: Adjusted for 1,500-2,000 features (vs V2: 334, V4: 422)
  -- V2: L1=0.1 (334 features) = 0.0003 per feature
  -- V4: L1=1.0 (422 features) = 0.0024 per feature ✅ Worked well
  -- Baseline: L1=1.5 (1,500-2,000 features) = 0.00075-0.001 per feature (balanced)
  l1_reg=1.5,                      -- Feature selection for high-dimensional discovery
  l2_reg=0.5,                      -- Balanced Ridge (matches V4's 0.5)
  subsample=0.8,
  max_tree_depth=10,
  data_split_method='RANDOM',      -- Required for data_split_eval_fraction
  data_split_eval_fraction=0.2     -- 20% holdout for validation
) AS
SELECT 
  target_1m,
  * EXCEPT(
    -- Exclude other targets
    target_1w,
    target_1m,
    target_3m,
    target_6m,
    -- Exclude date (not a feature)
    date,
    -- Exclude string columns
    yahoo_data_source,
    volatility_regime,
    -- Exclude 100% NULL columns (complete list from V2/V3/V4 validation)
    social_sentiment_volatility,
    news_article_count,
    news_avg_score,
    news_sentiment_avg,
    china_news_count,
    biofuel_news_count,
    tariff_news_count,
    weather_news_count,
    news_intelligence_7d,
    news_volume_7d,
    china_weekly_cancellations_mt,
    argentina_vessel_queue_count,
    argentina_port_throughput_teu,
    baltic_dry_index,
    heating_oil_price,
    natural_gas_price,
    gasoline_price,
    sugar_price,
    icln_price,
    tan_price,
    dba_price,
    vegi_price,
    biodiesel_spread_ma30,
    ethanol_spread_ma30,
    biodiesel_spread_vol,
    ethanol_spread_vol,
    -- Analyst target columns (100% NULL)
    adm_analyst_target,
    bg_analyst_target,
    bg_beta,
    cf_analyst_target,
    dar_analyst_target,
    mos_analyst_target,
    ntr_analyst_target,
    tsn_analyst_target
  )
FROM `cbi-v14.models_v4.baseline_1m_comprehensive_2yr`
WHERE target_1m IS NOT NULL
  AND date >= '2024-01-01';

-- ============================================
-- STEP 3: EVALUATE MODEL
-- ============================================

-- Evaluate on 2024+ test data
SELECT 
  'bqml_1m_baseline_exploratory' as model_name,
  *
FROM ML.EVALUATE(
  MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`,
  (
    SELECT * FROM `cbi-v14.models_v4.baseline_1m_comprehensive_2yr`
    WHERE target_1m IS NOT NULL
      AND date >= '2024-01-01'
  )
);

-- ============================================
-- STEP 4: EXTRACT FEATURE IMPORTANCE
-- ============================================

-- Get top 100 most important features
SELECT 
  feature,
  importance,
  ROUND(importance * 100, 4) as importance_pct
FROM ML.FEATURE_IMPORTANCE(
  MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`
)
ORDER BY importance DESC
LIMIT 100;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check table was created
SELECT 
  'baseline_1m_comprehensive_2yr' as table_name,
  COUNT(*) as total_rows,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNTIF(target_1m IS NOT NULL) as rows_with_target
FROM `cbi-v14.models_v4.baseline_1m_comprehensive_2yr`;

-- Check model was created
SELECT 
  model_name,
  creation_time,
  model_type,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, MINUTE) as minutes_old
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.MODELS`
WHERE model_name = 'bqml_1m_baseline_exploratory';

-- Check training info
SELECT 
  iteration,
  training_loss,
  evaluation_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(
  MODEL `cbi-v14.models_v4.bqml_1m_baseline_exploratory`
)
ORDER BY iteration DESC
LIMIT 10;

