-- ============================================
-- ADD ARGENTINA CRISIS SCORE
-- Enhanced crisis score: (ARSUSD_vol_30d + (debt_gdp / 100)) / 2 [0,1]
-- Date: November 2025
-- ============================================

-- Add arg_crisis_score to production training tables
-- This will be calculated from:
-- 1. ARS/USD 30-day volatility
-- 2. Argentina debt-to-GDP ratio
-- 3. Normalized to [0,1] range

-- For now, create a view that calculates it on-the-fly
-- Later, we can materialize it in the production tables

CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_arg_crisis_score` AS
WITH ars_volatility AS (
  SELECT 
    date,
    STDDEV(usd_ars_rate) OVER (
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ars_vol_30d
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE usd_ars_rate IS NOT NULL
),
debt_gdp AS (
  -- Argentina debt-to-GDP (approximate from economic indicators)
  -- If not available, use default of 0.8 (80% debt-to-GDP)
  -- Note: Using simplified calculation - actual debt/GDP may need external data source
  SELECT 
    date,
    0.8 as debt_gdp_ratio  -- Default: 80% debt-to-GDP (can be updated with actual data)
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
),
crisis_calc AS (
  SELECT 
    av.date,
    av.ars_vol_30d,
    dg.debt_gdp_ratio,
    -- Normalize volatility to [0,1] (assuming max vol ~0.5)
    LEAST(av.ars_vol_30d / 0.5, 1.0) as vol_normalized,
    -- Normalize debt/GDP to [0,1] (assuming max ~2.0 or 200%)
    LEAST(dg.debt_gdp_ratio / 2.0, 1.0) as debt_normalized
  FROM ars_volatility av
  JOIN debt_gdp dg ON av.date = dg.date
)
SELECT 
  date,
  (vol_normalized + debt_normalized) / 2.0 as arg_crisis_score
FROM crisis_calc;

-- Add column to production tables (if not exists)
-- Note: This will need to be run as ALTER TABLE statements
-- For now, we'll use the view in training queries

SELECT 
  'ARGENTINA CRISIS SCORE VIEW CREATED' as status,
  'Use vw_arg_crisis_score in training queries' as note;

