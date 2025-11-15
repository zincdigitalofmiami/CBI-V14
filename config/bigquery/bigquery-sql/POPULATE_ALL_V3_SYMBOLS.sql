-- ============================================
-- POPULATE ALL 18 SYMBOLS FOR V3 AMPLIFIED
-- ============================================

-- 1. CORN ETF (0.88 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  corn_etf_close = y.close,
  corn_etf_ma_7d = y.ma_7d,
  corn_etf_ma_30d = y.ma_30d,
  corn_etf_ma_200d = y.ma_200d,
  corn_etf_rsi_14 = y.rsi_14,
  corn_etf_macd_line = y.macd_line,
  corn_etf_bb_upper = y.bb_upper,
  corn_etf_bb_width = y.bb_width,
  corn_etf_atr_14 = y.atr_14,
  corn_etf_momentum_10 = y.momentum_10
FROM (
  SELECT date, close, ma_7d, ma_30d, ma_200d, rsi_14, macd_line,
         bb_upper, bb_width, atr_14, momentum_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'CORN'
) y
WHERE t.date = y.date;

-- 2. WEAT ETF (0.82 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  weat_close = y.close,
  weat_ma_7d = y.ma_7d,
  weat_ma_30d = y.ma_30d,
  weat_ma_200d = y.ma_200d,
  weat_rsi_14 = y.rsi_14,
  weat_macd_line = y.macd_line,
  weat_bb_upper = y.bb_upper,
  weat_bb_width = y.bb_width,
  weat_atr_14 = y.atr_14,
  weat_momentum_10 = y.momentum_10
FROM (
  SELECT date, close, ma_7d, ma_30d, ma_200d, rsi_14, macd_line,
         bb_upper, bb_width, atr_14, momentum_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'WEAT'
) y
WHERE t.date = y.date;

-- 3. ADM (0.78 correlation) - includes fundamentals
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  adm_close = y.close,
  adm_pe_ratio = y.pe_ratio,
  adm_beta = y.beta,
  adm_analyst_target = y.analyst_target_price,
  adm_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'ADM'
) y
WHERE t.date = y.date;

-- 4. BG Bunge (0.76 correlation) - includes fundamentals
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  bg_close = y.close,
  bg_pe_ratio = y.pe_ratio,
  bg_beta = y.beta,
  bg_analyst_target = y.analyst_target_price,
  bg_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'BG'
) y
WHERE t.date = y.date;

-- 5. NTR Nutrien (0.72 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  ntr_close = y.close,
  ntr_pe_ratio = y.pe_ratio,
  ntr_beta = y.beta,
  ntr_analyst_target = y.analyst_target_price,
  ntr_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'NTR'
) y
WHERE t.date = y.date;

-- 6. DAR Darling (0.72 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  dar_close = y.close,
  dar_pe_ratio = y.pe_ratio,
  dar_beta = y.beta,
  dar_analyst_target = y.analyst_target_price,
  dar_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'DAR'
) y
WHERE t.date = y.date;

-- 7. TSN Tyson (0.68 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  tsn_close = y.close,
  tsn_pe_ratio = y.pe_ratio,
  tsn_beta = y.beta,
  tsn_analyst_target = y.analyst_target_price,
  tsn_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'TSN'
) y
WHERE t.date = y.date;

-- 8. Brent Crude BZ=F (0.75 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  brent_close = y.close,
  brent_rsi_14 = y.rsi_14,
  brent_macd_line = y.macd_line,
  brent_ma_30d = y.ma_30d,
  brent_ma_200d = y.ma_200d
FROM (
  SELECT date, close, rsi_14, macd_line, ma_30d, ma_200d
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'BZ=F'
) y
WHERE t.date = y.date;

-- 9. Copper HG=F (0.65 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  copper_close = y.close,
  copper_rsi_14 = y.rsi_14,
  copper_macd_line = y.macd_line,
  copper_ma_30d = y.ma_30d,
  copper_ma_200d = y.ma_200d
FROM (
  SELECT date, close, rsi_14, macd_line, ma_30d, ma_200d
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'HG=F'
) y
WHERE t.date = y.date;

-- 10. Natural Gas NG=F
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  natgas_yahoo_close = y.close,
  natgas_yahoo_rsi_14 = y.rsi_14,
  natgas_yahoo_ma_30d = y.ma_30d,
  natgas_yahoo_momentum_10 = y.momentum_10,
  natgas_yahoo_roc_10 = y.rate_of_change_10
FROM (
  SELECT date, close, rsi_14, ma_30d, momentum_10, rate_of_change_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'NG=F'
) y
WHERE t.date = y.date;

-- 11. CF Industries (0.68 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  cf_close = y.close,
  cf_pe_ratio = y.pe_ratio,
  cf_beta = y.beta,
  cf_analyst_target = y.analyst_target_price,
  cf_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'CF'
) y
WHERE t.date = y.date;

-- 12. MOS Mosaic (0.70 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  mos_close = y.close,
  mos_pe_ratio = y.pe_ratio,
  mos_beta = y.beta,
  mos_analyst_target = y.analyst_target_price,
  mos_market_cap = y.market_cap
FROM (
  SELECT date, close, pe_ratio, beta, analyst_target_price, market_cap
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'MOS'
) y
WHERE t.date = y.date;

-- 13. DXY Dollar Index (-0.658 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  dxy_yahoo_close = y.close,
  dxy_yahoo_rsi_14 = y.rsi_14,
  dxy_yahoo_macd_line = y.macd_line,
  dxy_yahoo_ma_30d = y.ma_30d,
  dxy_yahoo_ma_200d = y.ma_200d
FROM (
  SELECT date, close, rsi_14, macd_line, ma_30d, ma_200d
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'DX-Y.NYB'
) y
WHERE t.date = y.date;

-- 14. BRL/USD (-0.60 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  brlusd_close = y.close,
  brlusd_rsi_14 = y.rsi_14,
  brlusd_ma_30d = y.ma_30d,
  brlusd_momentum_10 = y.momentum_10,
  brlusd_roc_10 = y.rate_of_change_10
FROM (
  SELECT date, close, rsi_14, ma_30d, momentum_10, rate_of_change_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'BRLUSD=X'
) y
WHERE t.date = y.date;

-- 15. CNY/USD (-0.50 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  cnyusd_close = y.close,
  cnyusd_rsi_14 = y.rsi_14,
  cnyusd_ma_30d = y.ma_30d,
  cnyusd_momentum_10 = y.momentum_10,
  cnyusd_roc_10 = y.rate_of_change_10
FROM (
  SELECT date, close, rsi_14, ma_30d, momentum_10, rate_of_change_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'CNYUSD=X'
) y
WHERE t.date = y.date;

-- 16. MXN/USD
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  mxnusd_close = y.close,
  mxnusd_rsi_14 = y.rsi_14,
  mxnusd_ma_30d = y.ma_30d,
  mxnusd_momentum_10 = y.momentum_10,
  mxnusd_roc_10 = y.rate_of_change_10
FROM (
  SELECT date, close, rsi_14, ma_30d, momentum_10, rate_of_change_10
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'MXNUSD=X'
) y
WHERE t.date = y.date;

-- 17. VIX (0.398 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  vix_yahoo_close = y.close,
  vix_yahoo_rsi_14 = y.rsi_14,
  vix_yahoo_ma_30d = y.ma_30d,
  vix_yahoo_macd_line = y.macd_line,
  vix_yahoo_bb_upper = y.bb_upper
FROM (
  SELECT date, close, rsi_14, ma_30d, macd_line, bb_upper
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = '^VIX'
) y
WHERE t.date = y.date;

-- 18. HYG High Yield Credit (-0.58 correlation)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  hyg_close = y.close,
  hyg_rsi_14 = y.rsi_14,
  hyg_ma_30d = y.ma_30d,
  hyg_macd_line = y.macd_line,
  hyg_bb_width = y.bb_width
FROM (
  SELECT date, close, rsi_14, ma_30d, macd_line, bb_width
  FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
  WHERE symbol = 'HYG'
) y
WHERE t.date = y.date;

-- FINAL VERIFICATION
SELECT 
  'V3 Population Complete' as status,
  COUNT(*) as total_rows,
  -- ETFs
  COUNT(soyb_close) as soyb_filled,
  COUNT(corn_etf_close) as corn_filled,
  COUNT(weat_close) as weat_filled,
  -- Ag Stocks
  COUNT(adm_close) as adm_filled,
  COUNT(bg_close) as bg_filled,
  COUNT(ntr_close) as ntr_filled,
  -- Energy/FX
  COUNT(brent_close) as brent_filled,
  COUNT(dxy_yahoo_close) as dxy_filled,
  COUNT(vix_yahoo_close) as vix_filled
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;





