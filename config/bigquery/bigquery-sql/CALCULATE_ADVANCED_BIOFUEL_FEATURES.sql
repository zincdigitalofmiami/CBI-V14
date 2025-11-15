-- ============================================
-- CALCULATE ADVANCED BIOFUEL FEATURES
-- Moving averages, volatility, derived ratios
-- ============================================

-- Calculate biodiesel spread 30-day MA
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET biodiesel_spread_ma30 = ma_calc.ma30
FROM (
  SELECT 
    date,
    AVG(biodiesel_spread) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ma30
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE biodiesel_spread IS NOT NULL
) ma_calc
WHERE t.date = ma_calc.date;

-- Calculate ethanol spread 30-day MA
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET ethanol_spread_ma30 = ma_calc.ma30
FROM (
  SELECT 
    date,
    AVG(ethanol_spread) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ma30
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE ethanol_spread IS NOT NULL
) ma_calc
WHERE t.date = ma_calc.date;

-- Calculate biodiesel spread volatility (20-day rolling stddev)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET biodiesel_spread_vol = vol_calc.vol
FROM (
  SELECT 
    date,
    STDDEV(biodiesel_spread) OVER (
      ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as vol
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE biodiesel_spread IS NOT NULL
) vol_calc
WHERE t.date = vol_calc.date;

-- Calculate ethanol spread volatility (20-day rolling stddev)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET ethanol_spread_vol = vol_calc.vol
FROM (
  SELECT 
    date,
    STDDEV(ethanol_spread) OVER (
      ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as vol
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE ethanol_spread IS NOT NULL
) vol_calc
WHERE t.date = vol_calc.date;

-- Update nat_gas_impact (same as natural_gas_price)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET nat_gas_impact = natural_gas_price
WHERE natural_gas_price IS NOT NULL;

-- Update oil_to_gas_ratio (from canonical table)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET oil_to_gas_ratio = c.oil_gas_ratio
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final` c
WHERE t.date = c.date;

-- Update sugar_ethanol_spread (from canonical table)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET sugar_ethanol_spread = c.sugar_ethanol_spread
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features_final` c
WHERE t.date = c.date;

-- Verify all updates
SELECT 
  'Advanced Biofuel Features Updated' as status,
  COUNT(biodiesel_spread_ma30) as bio_ma30_filled,
  COUNT(ethanol_spread_ma30) as eth_ma30_filled,
  COUNT(biodiesel_spread_vol) as bio_vol_filled,
  COUNT(ethanol_spread_vol) as eth_vol_filled,
  COUNT(nat_gas_impact) as natgas_filled,
  COUNT(oil_to_gas_ratio) as oil_gas_filled,
  COUNT(sugar_ethanol_spread) as sugar_eth_filled
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;







