-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- POPULATE MOVING AVERAGES
-- Calculate ma_7d and ma_30d for new dates
-- Date: November 6, 2025
-- ============================================

-- This script calculates moving averages for ALL dates (to ensure consistency)
-- Then updates zl_training_prod_allhistory_1m with the calculated values

-- Update ma_7d and ma_30d for zl_training_prod_allhistory_1m
UPDATE `cbi-v14.training.zl_training_prod_allhistory_1m` t
SET 
  ma_7d = ma_calc.ma_7d,
  ma_30d = ma_calc.ma_30d,
  ma_90d = ma_calc.ma_90d
FROM (
  SELECT 
    date,
    AVG(zl_price_current) OVER (
      ORDER BY date 
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma_7d,
    AVG(zl_price_current) OVER (
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ma_30d,
    AVG(zl_price_current) OVER (
      ORDER BY date 
      ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as ma_90d
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE zl_price_current IS NOT NULL
) ma_calc
WHERE t.date = ma_calc.date
  AND t.date > '2025-09-10';

-- Verification
SELECT 
  'Moving Averages Updated' as status,
  COUNT(*) as rows_updated,
  COUNT(CASE WHEN ma_7d IS NOT NULL THEN 1 END) as has_ma_7d,
  COUNT(CASE WHEN ma_30d IS NOT NULL THEN 1 END) as has_ma_30d,
  MIN(date) as earliest,
  MAX(date) as latest
FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
WHERE date > '2025-09-10';








