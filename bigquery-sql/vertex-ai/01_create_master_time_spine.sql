-- 01_create_master_time_spine.sql
-- Creates the master time series spine from 1900-2025
-- This is the backbone for all feature joins

CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_master_time_spine` AS
WITH date_spine AS (
  -- Use fundamentals_derived_features as it has the complete 1900-2025 range
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.fundamentals_derived_features`
  WHERE date >= '1900-01-01'
    AND date <= CURRENT_DATE()
  ORDER BY date
)
SELECT 
  date,
  -- Date components
  EXTRACT(YEAR FROM date) as year,
  EXTRACT(MONTH FROM date) as month,
  EXTRACT(DAY FROM date) as day,
  EXTRACT(DAYOFWEEK FROM date) as day_of_week,
  EXTRACT(DAYOFYEAR FROM date) as day_of_year,
  EXTRACT(QUARTER FROM date) as quarter,
  
  -- Regime flags
  CASE 
    WHEN date >= '2023-01-01' THEN TRUE
    ELSE FALSE
  END as is_trump_2_era,
  
  CASE 
    WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN TRUE
    ELSE FALSE
  END as is_trade_war_era,
  
  CASE 
    WHEN date >= '2020-01-01' AND date < '2021-01-01' THEN TRUE
    ELSE FALSE
  END as is_covid_era,
  
  CASE 
    WHEN date >= '2008-01-01' AND date < '2010-01-01' THEN TRUE
    ELSE FALSE
  END as is_financial_crisis,
  
  -- Training weight based on regime
  CASE 
    -- Trump 2.0 Era (2023-2025) - MAXIMUM WEIGHT
    WHEN date >= '2023-01-01' THEN 5000
    
    -- Trade War Era (2017-2019) - HIGH WEIGHT (most similar to current)
    WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN 1500
    
    -- Inflation Era (2021-2023) - VERY HIGH WEIGHT
    WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 1200
    
    -- COVID Crisis (2020-2021) - HIGH WEIGHT
    WHEN date >= '2020-01-01' AND date < '2021-01-01' THEN 800
    
    -- Financial Crisis (2008-2009) - MODERATE-HIGH WEIGHT
    WHEN date >= '2008-01-01' AND date < '2010-01-01' THEN 500
    
    -- Commodity Crash (2014-2016) - MODERATE WEIGHT
    WHEN date >= '2014-01-01' AND date < '2017-01-01' THEN 400
    
    -- QE/China Supercycle (2010-2014) - MODERATE WEIGHT
    WHEN date >= '2010-01-01' AND date < '2014-01-01' THEN 300
    
    -- Pre-Crisis (2000-2007) - BASELINE
    WHEN date >= '2000-01-01' AND date < '2008-01-01' THEN 100
    
    -- Historical (pre-2000) - LOW WEIGHT (for pattern learning only)
    ELSE 50
    
  END AS training_weight,
  
  -- Regime label (for analysis and debugging)
  CASE 
    WHEN date >= '2023-01-01' THEN 'Trump_2.0'
    WHEN date >= '2021-01-01' THEN 'Inflation_Era'
    WHEN date >= '2020-01-01' THEN 'COVID_Crisis'
    WHEN date >= '2017-01-01' THEN 'Trade_War'
    WHEN date >= '2014-01-01' THEN 'Commodity_Crash'
    WHEN date >= '2010-01-01' THEN 'QE_Supercycle'
    WHEN date >= '2008-01-01' THEN 'Financial_Crisis'
    WHEN date >= '2000-01-01' THEN 'Pre_Crisis'
    ELSE 'Historical'
  END AS market_regime

FROM date_spine;

-- Verify results
SELECT 
  market_regime,
  COUNT(*) as row_count,
  MIN(date) as min_date,
  MAX(date) as max_date,
  AVG(training_weight) as avg_weight,
  SUM(training_weight) as total_weight
FROM `cbi-v14.models_v4.vertex_master_time_spine`
GROUP BY market_regime
ORDER BY min_date DESC;

