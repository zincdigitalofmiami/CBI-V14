
-- Update zl_training_prod_allhistory_1m with RIN proxy features
-- These replace the NULL RIN columns with calculated proxies

UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  -- Use biodiesel spread as D4 RIN proxy
  rin_d4_price = COALESCE(r.biodiesel_spread, 0),
  
  -- Use ethanol spread as D6 RIN proxy  
  rin_d6_price = COALESCE(r.ethanol_spread, 0),
  
  -- Use average of spreads as D5 RIN proxy (advanced biofuel)
  rin_d5_price = COALESCE((r.biodiesel_spread + r.ethanol_spread) / 2, 0),
  
  -- Use biofuel crack for RFS mandate proxies
  rfs_mandate_biodiesel = COALESCE(r.biofuel_crack, 0),
  rfs_mandate_advanced = COALESCE(r.biodiesel_margin, 0),
  rfs_mandate_total = COALESCE(r.ethanol_margin, 0)
  
FROM `cbi-v14.yahoo_finance_comprehensive.rin_proxy_features` r
WHERE t.date = r.date;

-- Verify the update
SELECT 
  COUNT(*) as total_rows,
  COUNT(rin_d4_price) as d4_filled,
  COUNT(rin_d6_price) as d6_filled,
  AVG(rin_d4_price) as avg_d4_proxy,
  AVG(rin_d6_price) as avg_d6_proxy
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date >= '2020-01-01';
