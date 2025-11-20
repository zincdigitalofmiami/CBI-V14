-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- =======================================================================================
-- ⚠️ LEGACY SCRIPT - REFERENCE ONLY ⚠️
-- 
-- This script is NOT used in the current architecture (100% local M4 training).
-- Kept for reference only.
--
-- Current architecture: 100% local training, no Vertex AI deployment.
-- Current table naming: training.zl_training_prod_allhistory_{horizon}
-- Regime weights are already in training.regime_weights table
--
-- =======================================================================================
-- 03_add_regime_weights_to_production.sql
-- Add regime weights to existing vertex_ai_training_1m_base table
-- This preserves all features and adds training weights
-- Creates final vertex_ai_training_1m table (WITH weights, feeds Vertex AI)
-- =======================================================================================

-- ⚠️ LEGACY: This table is not used in current architecture
-- Current architecture uses: training.zl_training_prod_allhistory_1m (already has regime weights)
-- CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_1m` AS
CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_1m_with_weights` AS
SELECT 
  *,
  -- Training weight based on regime
  CASE 
    WHEN date >= '2023-01-01' THEN 5000  -- Trump 2.0
    WHEN date >= '2021-01-01' THEN 1200  -- Inflation Era
    WHEN date >= '2020-01-01' THEN 800   -- COVID
    ELSE 100  -- Baseline (2020 pre-COVID)
  END AS training_weight,
  
  -- Regime label
  CASE 
    WHEN date >= '2023-01-01' THEN 'Trump_2.0'
    WHEN date >= '2021-01-01' THEN 'Inflation_Era'
    WHEN date >= '2020-01-01' THEN 'COVID_Crisis'
    ELSE 'Pre_COVID'
  END AS market_regime

FROM `cbi-v14.training.zl_training_prod_allhistory_1m`  -- Current: training.zl_training_prod_allhistory_1m
WHERE target_1m IS NOT NULL;  -- Only rows with valid targets

-- Verify
SELECT 
  market_regime,
  COUNT(*) as row_count,
  SUM(training_weight) as total_weight,
  ROUND(100.0 * SUM(training_weight) / (SELECT SUM(training_weight) FROM `cbi-v14.models_v4.vertex_ai_training_1m`), 2) as weight_pct,
  MIN(date) as min_date,
  MAX(date) as max_date
FROM `cbi-v14.models_v4.vertex_ai_training_1m`
GROUP BY market_regime
ORDER BY total_weight DESC;

