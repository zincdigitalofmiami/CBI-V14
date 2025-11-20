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
-- Legacy tables referenced: models_v4.vertex_ai_training_{horizon}_base
--
-- =======================================================================================
-- CREATE_12M_TRAINING_TABLE.sql
-- Description: This script creates the 12-month horizon training table by generating
--              the `target_12m` column.
-- Author: Your Name
-- Date: 2025-11-07
-- =======================================================================================

-- ⚠️ LEGACY: This table is not used in current architecture
-- Current architecture uses: training.zl_training_prod_allhistory_12m
-- CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base` AS
CREATE OR REPLACE TABLE `cbi-v14.training.zl_training_prod_allhistory_12m` AS
SELECT
  *,
  -- ==========================================================================
  -- 12-MONTH TARGET: Future 12-month average price vs. current price
  -- ==========================================================================
  (
    (
      LEAD(zl_price_current, 252) OVER (ORDER BY date) +
      LEAD(zl_price_current, 253) OVER (ORDER BY date) +
      LEAD(zl_price_current, 254) OVER (ORDER BY date) +
      LEAD(zl_price_current, 255) OVER (ORDER BY date) +
      LEAD(zl_price_current, 256) OVER (ORDER BY date)
    ) / 5.0
  ) / zl_price_current - 1.0 AS target_12m
FROM
  `cbi-v14.training.zl_training_prod_allhistory_6m`  -- Current: training.zl_training_prod_allhistory_6m
;
