-- ============================================
-- POPULATE NULL RAW BIOFUEL COMPONENT PRICES
-- Load from biofuel_components_raw into production
-- ============================================

-- Update heating oil price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET heating_oil_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'HO=F';

-- Update natural gas price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET natural_gas_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'NG=F';

-- Update gasoline price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET gasoline_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'RB=F';

-- Update sugar price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET sugar_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'SB=F';

-- Update ICLN ETF price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET icln_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'ICLN';

-- Update TAN ETF price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET tan_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'TAN';

-- Update DBA ETF price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET dba_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'DBA';

-- Update VEGI ETF price
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET vegi_price = b.close
FROM `cbi-v14.yahoo_finance_comprehensive.biofuel_components_raw` b
WHERE t.date = CAST(b.date AS DATE)
  AND b.symbol = 'VEGI';

-- Verify updates
SELECT 
  'Raw Biofuel Prices Updated' as status,
  COUNT(heating_oil_price) as heating_oil_filled,
  COUNT(natural_gas_price) as natgas_filled,
  COUNT(gasoline_price) as gasoline_filled,
  COUNT(sugar_price) as sugar_filled,
  COUNT(icln_price) as icln_filled,
  COUNT(tan_price) as tan_filled,
  COUNT(dba_price) as dba_filled,
  COUNT(vegi_price) as vegi_filled
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;







