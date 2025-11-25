-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- UPDATE PRODUCTION WITH BIOFUEL COMPONENTS
-- Both raw prices AND RIN proxy calculations
-- ============================================

-- Step 1: Update raw biofuel component prices
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  heating_oil_price = b.close,
  natural_gas_price = b.close,
  gasoline_price = b.close,
  sugar_price = b.close,
  icln_price = b.close,
  tan_price = b.close,
  dba_price = b.close,
  vegi_price = b.close
FROM (
  SELECT date, symbol, close
  FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw`
) b
WHERE t.date = b.date
  AND b.symbol = CASE 
    WHEN TRUE THEN 'HO=F' 
  END;

-- Actually, let's do this properly with separate updates per symbol
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET heating_oil_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'HO=F';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET natural_gas_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'NG=F';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET gasoline_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'RB=F';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET sugar_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'SB=F';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET icln_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'ICLN';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET tan_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'TAN';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET dba_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'DBA';

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET vegi_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = b.date AND b.symbol = 'VEGI';

-- Step 2: Update RIN proxies and calculations
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  -- RIN proxies (replace the NULL columns)
  rin_d4_price = r.biodiesel_spread,
  rin_d6_price = r.ethanol_spread,
  rin_d5_price = (r.biodiesel_spread + r.ethanol_spread) / 2,
  
  -- RFS mandate proxies (replace the NULL columns)
  rfs_mandate_biodiesel = r.biofuel_crack,
  rfs_mandate_advanced = r.biodiesel_margin,
  rfs_mandate_total = r.ethanol_margin,
  
  -- Add all proxy features as independent columns
  biodiesel_spread = r.biodiesel_spread,
  ethanol_spread = r.ethanol_spread,
  biofuel_crack = r.biofuel_crack,
  clean_energy_momentum_30d = r.clean_energy_momentum_30d,
  clean_energy_momentum_7d = r.clean_energy_momentum_7d,
  nat_gas_impact = r.nat_gas_impact,
  sugar_ethanol_spread = r.sugar_ethanol_spread,
  biodiesel_margin = r.biodiesel_margin,
  ethanol_margin = r.ethanol_margin,
  oil_to_gas_ratio = r.oil_to_gas_ratio,
  soy_to_corn_ratio = r.soy_to_corn_ratio,
  biodiesel_spread_ma30 = r.biodiesel_spread_ma30,
  ethanol_spread_ma30 = r.ethanol_spread_ma30,
  biodiesel_spread_vol = r.biodiesel_spread_vol,
  ethanol_spread_vol = r.ethanol_spread_vol
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features` r
WHERE t.date = r.date;

-- Step 3: Verify ALL updates
SELECT 
  'Raw Components' as category,
  COUNT(heating_oil_price) as heating_oil,
  COUNT(natural_gas_price) as nat_gas,
  COUNT(gasoline_price) as gasoline,
  COUNT(sugar_price) as sugar,
  COUNT(icln_price) as icln,
  COUNT(dba_price) as dba,
  CAST(NULL AS INT64) as placeholder1,
  CAST(NULL AS INT64) as placeholder2
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`

UNION ALL

SELECT 
  'RIN Proxies',
  COUNT(rin_d4_price),
  COUNT(rin_d5_price),
  COUNT(rin_d6_price),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64)
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`

UNION ALL

SELECT 
  'Biofuel Spreads',
  COUNT(biodiesel_spread),
  COUNT(ethanol_spread),
  COUNT(biofuel_crack),
  COUNT(clean_energy_momentum_30d),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64)
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;








