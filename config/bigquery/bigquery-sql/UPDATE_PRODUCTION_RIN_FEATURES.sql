-- ============================================
-- UPDATE PRODUCTION WITH RIN PROXY FEATURES
-- Enterprise-grade data integration
-- ============================================
-- Version: 1.0
-- Date: November 6, 2025
--
-- PURPOSE: Update zl_training_prod_allhistory_1m with calculated RIN proxy
-- features, filling the 6 NULL RIN/RFS columns and adding new biofuel
-- economics features.
--
-- DEPENDENCIES:
-- - cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final
-- - cbi-v14.models_v4.zl_training_prod_allhistory_1m
--
-- VALIDATION: Performs row count verification before and after update
-- ============================================

-- PRE-UPDATE VALIDATION
SELECT
  '=== PRE-UPDATE STATUS ===' as status,
  COUNT(*) as total_rows,
  COUNT(rin_d4_price) as rin_d4_filled_before,
  COUNT(rin_d6_price) as rin_d6_filled_before,
  COUNT(rin_d5_price) as rin_d5_filled_before,
  COUNT(rfs_mandate_biodiesel) as rfs_biodiesel_filled_before,
  COUNT(rfs_mandate_advanced) as rfs_advanced_filled_before,
  COUNT(rfs_mandate_total) as rfs_total_filled_before
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- MAIN UPDATE: FILL RIN/RFS COLUMNS + NEW BIOFUEL FEATURES
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  -- ============================================
  -- FILL THE 6 NULL RIN/RFS COLUMNS
  -- ============================================
  -- D4 RIN (Biodiesel): Use biodiesel spread as proxy
  -- Negative spread = tight biodiesel economics = high RIN prices
  rin_d4_price = r.biodiesel_spread_cwt,
  
  -- D6 RIN (Corn Ethanol): Use ethanol spread as proxy
  -- Negative spread = tight ethanol economics = high RIN prices
  rin_d6_price = r.ethanol_spread_bbl,
  
  -- D5 RIN (Advanced Biofuel): Average of D4 and D6
  rin_d5_price = r.advanced_biofuel_spread,
  
  -- RFS Mandate Biodiesel: Crack spread indicates mandate fill difficulty
  rfs_mandate_biodiesel = r.rfs_biodiesel_fill_proxy,
  
  -- RFS Mandate Advanced: Margin indicates advanced biofuel economics
  rfs_mandate_advanced = r.rfs_advanced_fill_proxy,
  
  -- RFS Mandate Total: Overall renewable fuel economics
  rfs_mandate_total = r.rfs_total_fill_proxy,
  
  -- ============================================
  -- UPDATE EXISTING BIOFUEL FEATURE COLUMNS
  -- ============================================
  biodiesel_spread = r.biodiesel_spread_cwt,
  ethanol_spread = r.ethanol_spread_bbl,
  biofuel_crack = r.biodiesel_crack_spread_bu,
  
  -- ============================================
  -- FILL ADDITIONAL BIOFUEL ECONOMICS FEATURES
  -- ============================================
  biodiesel_margin = r.biodiesel_margin_pct,
  ethanol_margin = r.ethanol_margin_pct,
  nat_gas_impact = r.ethanol_production_cost_proxy,
  sugar_ethanol_spread = r.sugar_ethanol_spread,
  soy_to_corn_ratio = r.soy_corn_ratio,
  oil_to_gas_ratio = r.oil_gas_ratio
  
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final` r
WHERE t.date = r.date;

-- POST-UPDATE VALIDATION
SELECT
  '=== POST-UPDATE STATUS ===' as status,
  COUNT(*) as total_rows,
  COUNT(rin_d4_price) as rin_d4_filled_after,
  COUNT(rin_d6_price) as rin_d6_filled_after,
  COUNT(rin_d5_price) as rin_d5_filled_after,
  COUNT(rfs_mandate_biodiesel) as rfs_biodiesel_filled_after,
  COUNT(rfs_mandate_advanced) as rfs_advanced_filled_after,
  COUNT(rfs_mandate_total) as rfs_total_filled_after,
  ROUND(AVG(rin_d4_price), 2) as avg_rin_d4,
  ROUND(AVG(rin_d6_price), 2) as avg_rin_d6,
  ROUND(AVG(biodiesel_spread), 2) as avg_biodiesel_spread,
  ROUND(AVG(ethanol_spread), 2) as avg_ethanol_spread
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

-- SAMPLE RECENT DATA FOR VERIFICATION
SELECT
  date,
  ROUND(rin_d4_price, 2) as rin_d4,
  ROUND(rin_d6_price, 2) as rin_d6,
  ROUND(rin_d5_price, 2) as rin_d5,
  ROUND(biodiesel_spread, 2) as bio_spread,
  ROUND(ethanol_spread, 2) as eth_spread,
  ROUND(soy_to_corn_ratio, 2) as soy_corn
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date >= '2025-10-01'
  AND rin_d4_price IS NOT NULL
ORDER BY date DESC
LIMIT 10;

-- DATA QUALITY ASSERTIONS
-- These should all return TRUE
SELECT
  'Quality Checks' as check_type,
  COUNT(rin_d4_price) = COUNT(*) as all_rin_d4_filled,
  COUNT(rin_d6_price) = COUNT(*) as all_rin_d6_filled,
  COUNT(rin_d5_price) = COUNT(*) as all_rin_d5_filled,
  AVG(ABS(rin_d4_price)) < 1000 as rin_d4_in_valid_range,
  AVG(ABS(rin_d6_price)) < 500 as rin_d6_in_valid_range,
  STDDEV(biodiesel_spread) > 0 as biodiesel_spread_has_variance,
  CORR(rin_d4_price, biodiesel_spread) = 1.0 as rin_d4_matches_spread
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date >= '2020-01-01';







