-- Backup of models_v4.vw_arg_crisis_score
-- Created: 2025-11-17 17:57:49

WITH ars_volatility AS (
  SELECT 
    date,
    STDDEV(usd_ars_rate) OVER (
      ORDER BY date 
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as ars_vol_30d
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE usd_ars_rate IS NOT NULL
),
debt_gdp AS (
  -- Argentina debt-to-GDP (approximate from economic indicators)
  -- If not available, use default of 0.8 (80% debt-to-GDP)
  -- Note: Using simplified calculation - actual debt/GDP may need external data source
  SELECT 
    date,
    0.8 as debt_gdp_ratio  -- Default: 80% debt-to-GDP (can be updated with actual data)
  FROM `cbi-v14.models_v4.production_training_data_1m`
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
FROM crisis_calc