-- ============================================
-- ENTERPRISE RIN PROXY CALCULATION ENGINE
-- Industry-standard biofuel economics features
-- ============================================
-- Version: 1.0
-- Author: CBI-V14 Data Engineering
-- Date: November 6, 2025
--
-- PURPOSE: Calculate RIN (Renewable Identification Number) proxy features
-- from raw commodity prices using industry-standard formulas and proper
-- unit conversions.
--
-- ASSUMPTIONS:
-- - All input prices are in their native units ($/cwt, $/gal, cents/bushel)
-- - Output features are in USD with consistent scaling
-- - NULL values are preserved (no artificial fill)
--
-- METHODOLOGY:
-- 1. Biodiesel economics (D4 RIN proxy)
-- 2. Ethanol economics (D6 RIN proxy)
-- 3. Advanced biofuel economics (D5 RIN proxy)
-- 4. Cross-commodity ratios for regime detection
-- ============================================

-- STEP 1: CREATE CANONICAL BIOFUEL COMPONENTS TABLE
-- Pivot raw commodity data into single-row-per-date format
CREATE OR REPLACE TABLE `cbi-v14.yahoo_finance_comprehensive.biofuel_components_canonical` AS
WITH raw_data AS (
  -- Pull commodities from primary source (ag commodities)
  SELECT
    date,
    symbol,
    close as price
  FROM `cbi-v14.yahoo_finance_comprehensive.all_symbols_20yr`
  WHERE symbol IN (
    'ZL=F',  -- Soybean Oil ($/cwt)
    'ZS=F',  -- Soybeans (cents/bushel)
    'ZM=F',  -- Soybean Meal ($/ton)
    'ZC=F',  -- Corn (cents/bushel)
    'CL=F'   -- Crude Oil ($/barrel) - energy baseline
  )
  
  UNION ALL
  
  -- Pull energy commodities from biofuel components source
  SELECT
    CAST(date AS DATE) as date,
    symbol,
    close as price
  FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw`
  WHERE symbol IN (
    'HO=F',  -- Heating Oil ($/gallon) - diesel proxy
    'RB=F',  -- RBOB Gasoline ($/gallon)
    'NG=F',  -- Natural Gas ($/MMBtu) - ethanol production cost
    'SB=F'   -- Sugar #11 (cents/pound) - Brazil ethanol feedstock
  )
),
pivoted AS (
  SELECT
    date,
    MAX(IF(symbol='ZL=F', price, NULL)) as soybean_oil_price_cwt,
    MAX(IF(symbol='ZS=F', price, NULL)) as soybean_price_cents_bu,
    MAX(IF(symbol='ZM=F', price, NULL)) as soybean_meal_price_ton,
    MAX(IF(symbol='ZC=F', price, NULL)) as corn_price_cents_bu,
    MAX(IF(symbol='HO=F', price, NULL)) as heating_oil_price_gal,
    MAX(IF(symbol='RB=F', price, NULL)) as gasoline_price_gal,
    MAX(IF(symbol='NG=F', price, NULL)) as natural_gas_price_mmbtu,
    MAX(IF(symbol='SB=F', price, NULL)) as sugar_price_cents_lb,
    MAX(IF(symbol='CL=F', price, NULL)) as crude_oil_price_bbl
  FROM raw_data
  GROUP BY date
)
SELECT
  date,
  -- Raw prices (native units, validated)
  soybean_oil_price_cwt,
  soybean_price_cents_bu,
  soybean_meal_price_ton,
  corn_price_cents_bu,
  heating_oil_price_gal,
  gasoline_price_gal,
  natural_gas_price_mmbtu,
  sugar_price_cents_lb,
  crude_oil_price_bbl,
  
  -- UNIT CONVERSIONS (for cross-commodity comparison)
  -- Convert all to $/metric ton for standardization
  soybean_oil_price_cwt * 22.0462 as soybean_oil_usd_mt,  -- 1 MT = 22.0462 cwt
  (soybean_price_cents_bu / 100) * 36.7437 as soybean_usd_mt,  -- 1 MT = 36.7437 bu
  soybean_meal_price_ton * 1.10231 as soybean_meal_usd_mt,  -- 1 MT = 1.10231 short tons
  (corn_price_cents_bu / 100) * 39.3683 as corn_usd_mt,  -- 1 MT = 39.3683 bu
  heating_oil_price_gal * 317.975 as heating_oil_usd_mt,  -- 1 MT = 317.975 gal (density 0.85)
  gasoline_price_gal * 353.677 as gasoline_usd_mt,  -- 1 MT = 353.677 gal (density 0.75)
  natural_gas_price_mmbtu as natural_gas_usd_mmbtu,  -- Already in $/MMBtu
  (sugar_price_cents_lb / 100) * 2204.62 as sugar_usd_mt,  -- 1 MT = 2204.62 lb
  crude_oil_price_bbl * 7.33 as crude_oil_usd_mt  -- 1 MT = ~7.33 barrels (density 0.85)
  
FROM pivoted
WHERE date IS NOT NULL;

-- STEP 2: CALCULATE RIN PROXY FEATURES
-- Industry-standard biofuel economics calculations
CREATE OR REPLACE TABLE `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final` AS
WITH base AS (
  SELECT * FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_canonical`
),
calculations AS (
  SELECT
    date,
    
    -- ============================================
    -- BIODIESEL ECONOMICS (D4 RIN PROXY)
    -- ============================================
    -- Biodiesel Spread: Output value minus input cost
    -- Formula: Soybean oil revenue - Heating oil (diesel) market price
    -- Units: $/cwt for direct comparison
    -- Interpretation: Positive = profitable to produce biodiesel vs petroleum diesel
    soybean_oil_price_cwt - (heating_oil_price_gal * 12) as biodiesel_spread_cwt,
    
    -- Biodiesel Margin: Profitability as % of feedstock cost
    -- Formula: (Output - Input) / Input * 100
    -- Interpretation: Higher = more attractive for biodiesel producers
    SAFE_DIVIDE(
      soybean_oil_price_cwt - (heating_oil_price_gal * 12),
      soybean_oil_price_cwt
    ) * 100 as biodiesel_margin_pct,
    
    -- Biodiesel Crack Spread: Simplified crush margin for biodiesel
    -- Formula: (Oil yield * Oil price) + (Meal yield * Meal price) - Bean cost
    -- Standard yields: 11 lbs oil/bushel (0.11 cwt), 44 lbs meal/bushel (0.022 ton)
    -- Units: $/bushel
    (soybean_oil_price_cwt * 0.11) + 
    (soybean_meal_price_ton * 0.022) - 
    (soybean_price_cents_bu / 100) as biodiesel_crack_spread_bu,
    
    -- ============================================
    -- ETHANOL ECONOMICS (D6 RIN PROXY)
    -- ============================================
    -- Ethanol Spread: Gasoline value minus corn feedstock cost
    -- Formula: (Gasoline price * barrel) - (Corn cost * bushels per barrel)
    -- Ethanol yield: 2.8 gallons per bushel of corn
    -- Energy equivalent: 1.5 gallons of ethanol = 1 gallon of gasoline (E85)
    -- Units: $/barrel equivalent
    (gasoline_price_gal * 42) - 
    ((corn_price_cents_bu / 100) * 2.8) as ethanol_spread_bbl,
    
    -- Ethanol Margin: Profitability as % of gasoline price
    SAFE_DIVIDE(
      (gasoline_price_gal * 42) - ((corn_price_cents_bu / 100) * 2.8),
      gasoline_price_gal * 42
    ) * 100 as ethanol_margin_pct,
    
    -- Ethanol Production Cost Index: Natural gas is primary energy input
    -- Natural gas represents ~30% of ethanol production cost
    natural_gas_price_mmbtu as ethanol_production_cost_proxy,
    
    -- ============================================
    -- ADVANCED BIOFUEL (D5 RIN PROXY)
    -- ============================================
    -- D5 RINs are for advanced biofuels (non-corn ethanol)
    -- Proxy: Average of biodiesel (D4) and ethanol (D6) economics
    (
      (soybean_oil_price_cwt - (heating_oil_price_gal * 12)) +
      ((gasoline_price_gal * 42) - ((corn_price_cents_bu / 100) * 2.8))
    ) / 2 as advanced_biofuel_spread,
    
    -- ============================================
    -- CROSS-COMMODITY RATIOS (REGIME DETECTION)
    -- ============================================
    -- Soy-to-Corn Ratio: Feedstock substitution signal
    -- High ratio = soybeans expensive relative to corn → ethanol more attractive
    SAFE_DIVIDE(soybean_price_cents_bu, corn_price_cents_bu) as soy_corn_ratio,
    
    -- Oil-to-Gas Ratio: Energy market dynamics
    -- High ratio = crude expensive relative to gasoline → biofuels more competitive
    SAFE_DIVIDE(crude_oil_price_bbl, gasoline_price_gal) as oil_gas_ratio,
    
    -- Sugar-Ethanol Arbitrage: Brazil flex-fuel dynamics
    -- Brazil produces ethanol from both corn and sugar cane
    -- Formula: Sugar price - (Corn price * conversion factor)
    (sugar_price_cents_lb * 2000) - (corn_price_cents_bu * 0.5) as sugar_ethanol_spread,
    
    -- ============================================
    -- RFS MANDATE PROXIES
    -- ============================================
    -- RFS mandates create demand floors for biofuels
    -- When spreads are negative, RINs become valuable to comply with mandates
    
    -- Biodiesel Mandate Fill Rate: Proxy from crack spread
    -- Positive crack = easy to fill mandate, cheap RINs
    -- Negative crack = expensive to produce, expensive RINs
    (soybean_oil_price_cwt * 0.11) + 
    (soybean_meal_price_ton * 0.022) - 
    (soybean_price_cents_bu / 100) as rfs_biodiesel_fill_proxy,
    
    -- Advanced Biofuel Mandate: Proxy from margin
    SAFE_DIVIDE(
      soybean_oil_price_cwt - (heating_oil_price_gal * 12),
      soybean_oil_price_cwt
    ) * 100 as rfs_advanced_fill_proxy,
    
    -- Total Renewable Fuel Mandate: Proxy from ethanol margin
    SAFE_DIVIDE(
      (gasoline_price_gal * 42) - ((corn_price_cents_bu / 100) * 2.8),
      gasoline_price_gal * 42
    ) * 100 as rfs_total_fill_proxy
    
  FROM base
)
SELECT * FROM calculations
WHERE date IS NOT NULL
ORDER BY date DESC;

-- STEP 3: DATA QUALITY VALIDATION
-- Verify calculation outputs before production update
SELECT
  'Data Quality Check' as check_type,
  COUNT(*) as total_rows,
  COUNT(biodiesel_spread_cwt) as biodiesel_spread_filled,
  COUNT(ethanol_spread_bbl) as ethanol_spread_filled,
  COUNT(biodiesel_crack_spread_bu) as crack_spread_filled,
  ROUND(AVG(biodiesel_spread_cwt), 2) as avg_biodiesel_spread,
  ROUND(AVG(ethanol_spread_bbl), 2) as avg_ethanol_spread,
  ROUND(AVG(soy_corn_ratio), 2) as avg_soy_corn_ratio,
  ROUND(STDDEV(biodiesel_spread_cwt), 2) as stddev_biodiesel_spread,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final`;

-- STEP 4: SAMPLE OUTPUT FOR VERIFICATION
SELECT
  date,
  ROUND(biodiesel_spread_cwt, 2) as biodiesel_spread,
  ROUND(ethanol_spread_bbl, 2) as ethanol_spread,
  ROUND(biodiesel_crack_spread_bu, 2) as crack_spread,
  ROUND(soy_corn_ratio, 2) as soy_corn_ratio,
  ROUND(oil_gas_ratio, 2) as oil_gas_ratio
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final`
WHERE date >= '2025-10-01'
ORDER BY date DESC
LIMIT 10;

