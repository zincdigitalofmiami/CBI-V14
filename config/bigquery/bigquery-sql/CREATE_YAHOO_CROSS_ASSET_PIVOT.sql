-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- PIVOT YAHOO 314K ROWS TO WIDE FORMAT
-- Create 1 row per date with all symbols as columns
-- ============================================
-- This creates cross-asset features for production table integration

CREATE OR REPLACE TABLE `cbi-v14.yahoo_finance_comprehensive.yahoo_cross_asset_daily` 
PARTITION BY date
CLUSTER BY date AS

WITH yahoo_data AS (
  SELECT 
    DATE(TIMESTAMP_MICROS(CAST(date AS INT64))) as date,
    symbol,
    close,
    ma_7d,
    ma_30d,
    ma_50d,
    ma_90d,
    ma_100d,
    ma_200d,
    rsi_14,
    macd_line,
    macd_signal,
    bb_upper,
    bb_middle,
    bb_lower,
    atr_14,
    volume,
    momentum_10,
    rate_of_change_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_finance_complete_enterprise`
)
SELECT
  date,
  
  -- ============================================
  -- FX PAIRS (9 symbols × 10 features = 90)
  -- ============================================
  MAX(IF(symbol='DX-Y.NYB', close, NULL)) as dxy_close,
  MAX(IF(symbol='DX-Y.NYB', rsi_14, NULL)) as dxy_rsi_14,
  MAX(IF(symbol='DX-Y.NYB', ma_30d, NULL)) as dxy_ma_30d,
  MAX(IF(symbol='DX-Y.NYB', ma_200d, NULL)) as dxy_ma_200d,
  
  MAX(IF(symbol='EURUSD=X', close, NULL)) as eurusd_close,
  MAX(IF(symbol='EURUSD=X', rsi_14, NULL)) as eurusd_rsi_14,
  MAX(IF(symbol='EURUSD=X', ma_30d, NULL)) as eurusd_ma_30d,
  
  MAX(IF(symbol='JPYUSD=X', close, NULL)) as jpyusd_close,
  MAX(IF(symbol='JPYUSD=X', rsi_14, NULL)) as jpyusd_rsi_14,
  
  MAX(IF(symbol='GBPUSD=X', close, NULL)) as gbpusd_close,
  MAX(IF(symbol='CNYUSD=X', close, NULL)) as cnyusd_close,
  MAX(IF(symbol='BRLUSD=X', close, NULL)) as brlusd_close,
  MAX(IF(symbol='MXNUSD=X', close, NULL)) as mxnusd_close,
  MAX(IF(symbol='AUDUSD=X', close, NULL)) as audusd_close,
  MAX(IF(symbol='CADUSD=X', close, NULL)) as cadusd_close,
  
  -- ============================================
  -- ENERGY (5 symbols × 10 features = 50)
  -- ============================================
  MAX(IF(symbol='CL=F', close, NULL)) as crude_wti_close,
  MAX(IF(symbol='CL=F', rsi_14, NULL)) as crude_wti_rsi_14,
  MAX(IF(symbol='CL=F', macd_line, NULL)) as crude_wti_macd,
  MAX(IF(symbol='CL=F', ma_30d, NULL)) as crude_wti_ma_30d,
  MAX(IF(symbol='CL=F', ma_200d, NULL)) as crude_wti_ma_200d,
  
  MAX(IF(symbol='BZ=F', close, NULL)) as brent_close,
  MAX(IF(symbol='BZ=F', rsi_14, NULL)) as brent_rsi_14,
  
  MAX(IF(symbol='HO=F', close, NULL)) as heating_oil_close,
  MAX(IF(symbol='RB=F', close, NULL)) as gasoline_close,
  MAX(IF(symbol='NG=F', close, NULL)) as natgas_close,
  MAX(IF(symbol='NG=F', rsi_14, NULL)) as natgas_rsi_14,
  
  -- ============================================
  -- INDICES & VOLATILITY (5 symbols × 10 features = 50)
  -- ============================================
  MAX(IF(symbol='^VIX', close, NULL)) as vix_close,
  MAX(IF(symbol='^VIX', rsi_14, NULL)) as vix_rsi_14,
  MAX(IF(symbol='^VIX', ma_30d, NULL)) as vix_ma_30d,
  MAX(IF(symbol='^VIX', ma_200d, NULL)) as vix_ma_200d,
  
  MAX(IF(symbol='^GSPC', close, NULL)) as spx_close,
  MAX(IF(symbol='^GSPC', rsi_14, NULL)) as spx_rsi_14,
  MAX(IF(symbol='^GSPC', ma_30d, NULL)) as spx_ma_30d,
  MAX(IF(symbol='^GSPC', ma_200d, NULL)) as spx_ma_200d,
  
  MAX(IF(symbol='^DJI', close, NULL)) as dji_close,
  MAX(IF(symbol='^IXIC', close, NULL)) as nasdaq_close,
  
  -- ============================================
  -- RATES (5 symbols × 5 features = 25)
  -- ============================================
  MAX(IF(symbol='^TNX', close, NULL)) as treasury_10y_close,
  MAX(IF(symbol='^TYX', close, NULL)) as treasury_30y_close,
  MAX(IF(symbol='^FVX', close, NULL)) as treasury_5y_close,
  MAX(IF(symbol='^IRX', close, NULL)) as treasury_13w_close,
  MAX(IF(symbol='TLT', close, NULL)) as tlt_close,
  
  -- ============================================
  -- AG STOCKS (9 symbols × 5 features = 45)
  -- ============================================
  MAX(IF(symbol='ADM', close, NULL)) as adm_close,
  MAX(IF(symbol='ADM', rsi_14, NULL)) as adm_rsi_14,
  MAX(IF(symbol='ADM', pe_ratio, NULL)) as adm_pe,
  MAX(IF(symbol='ADM', beta, NULL)) as adm_beta,
  MAX(IF(symbol='ADM', analyst_target_price, NULL)) as adm_target,
  
  MAX(IF(symbol='BG', close, NULL)) as bg_close,
  MAX(IF(symbol='BG', pe_ratio, NULL)) as bg_pe,
  
  MAX(IF(symbol='DAR', close, NULL)) as dar_close,
  MAX(IF(symbol='TSN', close, NULL)) as tsn_close,
  MAX(IF(symbol='DE', close, NULL)) as de_close,
  MAX(IF(symbol='AGCO', close, NULL)) as agco_close,
  MAX(IF(symbol='CF', close, NULL)) as cf_close,
  MAX(IF(symbol='MOS', close, NULL)) as mos_close,
  MAX(IF(symbol='NTR', close, NULL)) as ntr_close,
  
  -- ============================================
  -- SOFT COMMODITIES (4 symbols × 5 features = 20)
  -- ============================================
  MAX(IF(symbol='SB=F', close, NULL)) as sugar_close,
  MAX(IF(symbol='CT=F', close, NULL)) as cotton_close,
  MAX(IF(symbol='KC=F', close, NULL)) as coffee_close,
  MAX(IF(symbol='CC=F', close, NULL)) as cocoa_close,
  
  -- ============================================
  -- METALS (4 symbols × 5 features = 20)
  -- ============================================
  MAX(IF(symbol='GC=F', close, NULL)) as gold_close,
  MAX(IF(symbol='GC=F', rsi_14, NULL)) as gold_rsi_14,
  MAX(IF(symbol='GC=F', ma_200d, NULL)) as gold_ma_200d,
  
  MAX(IF(symbol='SI=F', close, NULL)) as silver_close,
  MAX(IF(symbol='HG=F', close, NULL)) as copper_close,
  MAX(IF(symbol='PL=F', close, NULL)) as platinum_close,
  
  -- ============================================
  -- CREDIT (2 symbols × 5 features = 10)
  -- ============================================
  MAX(IF(symbol='HYG', close, NULL)) as hyg_close,
  MAX(IF(symbol='LQD', close, NULL)) as lqd_close,
  
  -- ============================================
  -- ETFs (4 symbols × 5 features = 20)
  -- ============================================
  MAX(IF(symbol='DBA', close, NULL)) as dba_close,
  MAX(IF(symbol='CORN', close, NULL)) as corn_etf_close,
  MAX(IF(symbol='SOYB', close, NULL)) as soyb_etf_close,
  MAX(IF(symbol='WEAT', close, NULL)) as weat_etf_close,
  
  MAX(IF(symbol='ICLN', close, NULL)) as icln_close,
  MAX(IF(symbol='TAN', close, NULL)) as tan_close,
  MAX(IF(symbol='VEGI', close, NULL)) as vegi_close
  
FROM yahoo_data
GROUP BY date
ORDER BY date;

-- Verify the pivot
SELECT 
  COUNT(*) as total_dates,
  MIN(date) as earliest,
  MAX(date) as latest,
  COUNT(dxy_close) as dxy_filled,
  COUNT(vix_close) as vix_filled,
  COUNT(crude_wti_close) as crude_filled,
  COUNT(adm_close) as adm_filled
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_cross_asset_daily`;






