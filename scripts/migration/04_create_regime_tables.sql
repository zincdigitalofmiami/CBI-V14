-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Phase 3: Create Regime Calendar and Weights Tables
-- These tables support regime-based training and weighting

-- Regime Calendar: Maps dates to market regimes
CREATE OR REPLACE TABLE `cbi-v14.training.regime_calendar` AS
SELECT 
  date,
  CASE 
    WHEN date < '2000-01-01' THEN 'historical_pre2000'
    WHEN date >= '2000-01-01' AND date < '2008-01-01' THEN 'precrisis_2000_2007'
    WHEN date >= '2008-01-01' AND date < '2010-01-01' THEN 'financial_crisis_2008_2009'
    WHEN date >= '2010-01-01' AND date < '2014-01-01' THEN 'qe_supercycle_2010_2014'
    WHEN date >= '2014-01-01' AND date < '2017-01-01' THEN 'commodity_crash_2014_2016'
    WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN 'tradewar_2017_2019'
    WHEN date >= '2020-01-01' AND date < '2021-01-01' THEN 'covid_2020_2021'
    WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 'inflation_2021_2023'
    WHEN date >= '2023-01-01' THEN 'trump_2023_2025'
    ELSE 'allhistory'
  END AS regime
FROM UNNEST(GENERATE_DATE_ARRAY('1990-01-01', CURRENT_DATE(), INTERVAL 1 DAY)) AS date
ORDER BY date;

-- Regime Weights: Maps regimes to training weights
-- Research-based weighting: recency bias + importance weighting + sample compensation
-- Scale: 50-5000 provides strong differentiation in gradient-based training
-- Trump era: 100x weight of historical (recency bias)
-- Crisis/Trade War: High weights for learning volatility patterns
-- Overlaps resolved by MAX(weight) per date
CREATE OR REPLACE TABLE `cbi-v14.training.regime_weights` AS
SELECT 
  regime,
  weight,
  start_date,
  end_date,
  description
FROM UNNEST([
  STRUCT('historical_pre2000' AS regime, 50 AS weight, DATE('1990-01-01') AS start_date, DATE('1999-12-31') AS end_date, 'Pre-2000 historical data - pattern learning only' AS description),
  STRUCT('precrisis_2000_2007' AS regime, 100 AS weight, DATE('2000-01-01') AS start_date, DATE('2007-12-31') AS end_date, 'Pre-crisis baseline patterns' AS description),
  STRUCT('financial_crisis_2008_2009' AS regime, 500 AS weight, DATE('2008-01-01') AS start_date, DATE('2009-12-31') AS end_date, 'Financial crisis - volatility spike learning' AS description),
  STRUCT('qe_supercycle_2010_2014' AS regime, 300 AS weight, DATE('2010-01-01') AS start_date, DATE('2014-12-31') AS end_date, 'QE supercycle - commodity boom patterns' AS description),
  STRUCT('commodity_crash_2014_2016' AS regime, 400 AS weight, DATE('2014-01-01') AS start_date, DATE('2016-12-31') AS end_date, 'Commodity crash dynamics' AS description),
  STRUCT('tradewar_2017_2019' AS regime, 1500 AS weight, DATE('2017-01-01') AS start_date, DATE('2019-12-31') AS end_date, 'Trade war era - high relevance to current policy environment' AS description),
  STRUCT('covid_2020_2021' AS regime, 800 AS weight, DATE('2020-01-01') AS start_date, DATE('2021-12-31') AS end_date, 'COVID pandemic - supply chain disruption learning' AS description),
  STRUCT('inflation_2021_2023' AS regime, 1200 AS weight, DATE('2021-01-01') AS start_date, DATE('2022-12-31') AS end_date, 'Inflation surge - current macro dynamics' AS description),
  STRUCT('trump_2023_2025' AS regime, 5000 AS weight, DATE('2023-01-01') AS start_date, DATE('2025-12-31') AS end_date, 'Trump 2.0 era - MAXIMUM recency bias, current policy regime' AS description),
  STRUCT('structural_events' AS regime, 2000 AS weight, DATE('1990-01-01') AS start_date, DATE('2025-12-31') AS end_date, 'Structural market events - extreme event learning' AS description),
  STRUCT('allhistory' AS regime, 1000 AS weight, DATE('1990-01-01') AS start_date, DATE('2025-12-31') AS end_date, 'All historical data - baseline reference' AS description)
]);

-- Partition and cluster regime_calendar
ALTER TABLE `cbi-v14.training.regime_calendar`
SET OPTIONS(
  description='Maps dates to market regimes for regime-based training'
);

-- Add partitioning (if supported)
-- Note: Partitioning must be set at table creation, so this will be done in a recreate step

