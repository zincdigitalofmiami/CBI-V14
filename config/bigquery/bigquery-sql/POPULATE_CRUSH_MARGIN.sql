-- ============================================
-- POPULATE CRUSH MARGIN
-- Calculate crush_margin and moving averages
-- Date: November 6, 2025
-- ============================================

-- Crush margin formula (soybean crush economics):
-- crush_margin = (oil_price_per_cwt * 11) + (meal_price_per_ton * 0.022) - bean_price_per_bushel
-- 
-- Explanation:
-- - 1 bushel of soybeans (60 lbs) yields ~11 lbs of oil and ~44 lbs of meal
-- - Oil: 11 lbs @ oil_price_per_cwt (price per 100 lbs) = oil_price_per_cwt * 0.11
-- - Meal: 44 lbs @ meal_price_per_ton (price per 2000 lbs) = meal_price_per_ton * 0.022
-- - Cost: bean_price_per_bushel

-- Step 1: Calculate crush_margin for ALL dates (for consistency)
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  crush_margin = crush_calc.crush_margin
FROM (
  SELECT 
    date,
    -- Crush margin calculation
    (oil_price_per_cwt * 0.11) + (meal_price_per_ton * 0.022) - bean_price_per_bushel as crush_margin
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE bean_price_per_bushel IS NOT NULL
    AND oil_price_per_cwt IS NOT NULL
    AND meal_price_per_ton IS NOT NULL
) crush_calc
WHERE t.date = crush_calc.date
  AND t.date > '2025-09-10';

-- Step 2: Calculate crush margin moving averages
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  crush_margin_7d_ma = crush_ma.crush_margin_7d_ma,
  crush_margin_30d_ma = crush_ma.crush_margin_30d_ma
FROM (
  SELECT 
    date,
    AVG(crush_margin) OVER (
      ORDER BY date 
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as crush_margin_7d_ma,
    AVG(crush_margin) OVER (
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as crush_margin_30d_ma
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE crush_margin IS NOT NULL
) crush_ma
WHERE t.date = crush_ma.date
  AND t.date > '2025-09-10';

-- Verification
SELECT 
  'Crush Margin Updated' as status,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN crush_margin IS NOT NULL THEN 1 END) as has_crush_margin,
  COUNT(CASE WHEN crush_margin_7d_ma IS NOT NULL THEN 1 END) as has_crush_7d_ma,
  COUNT(CASE WHEN crush_margin_30d_ma IS NOT NULL THEN 1 END) as has_crush_30d_ma,
  AVG(crush_margin) as avg_crush_margin,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date > '2025-09-10';







