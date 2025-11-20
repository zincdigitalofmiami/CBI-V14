-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- 02_join_derived_features.sql
-- Joins pre-computed derived features tables to the master spine
-- These tables are ALREADY feature-engineered and daily

CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_core_features` AS
SELECT 
  -- Master spine columns
  s.date,
  s.year,
  s.month,
  s.day,
  s.day_of_week,
  s.day_of_year,
  s.quarter,
  s.training_weight,
  s.market_regime,
  s.is_trump_2_era,
  s.is_trade_war_era,
  s.is_covid_era,
  s.is_financial_crisis,
  
  -- Fundamentals derived features (all columns)
  f.* EXCEPT(date),
  
  -- FX derived features (all columns)
  fx.* EXCEPT(date),
  
  -- Monetary derived features (all columns)
  m.* EXCEPT(date),
  
  -- Volatility derived features (all columns)
  v.* EXCEPT(date)

FROM `cbi-v14.models_v4.vertex_master_time_spine` s

LEFT JOIN `cbi-v14.models_v4.fundamentals_derived_features` f 
  ON s.date = f.date

LEFT JOIN `cbi-v14.models_v4.fx_derived_features` fx 
  ON s.date = fx.date

LEFT JOIN `cbi-v14.models_v4.monetary_derived_features` m 
  ON s.date = m.date

LEFT JOIN `cbi-v14.models_v4.volatility_derived_features` v 
  ON s.date = v.date;

-- Verify results
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as distinct_dates,
  MIN(date) as min_date,
  MAX(date) as max_date
FROM `cbi-v14.models_v4.vertex_core_features`;

-- Check regime distribution
SELECT 
  market_regime,
  COUNT(*) as row_count,
  SUM(training_weight) as total_weight,
  ROUND(100.0 * SUM(training_weight) / (SELECT SUM(training_weight) FROM `cbi-v14.models_v4.vertex_core_features`), 2) as weight_pct
FROM `cbi-v14.models_v4.vertex_core_features`
GROUP BY market_regime
ORDER BY total_weight DESC;

