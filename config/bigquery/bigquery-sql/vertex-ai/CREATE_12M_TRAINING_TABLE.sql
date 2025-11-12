-- =======================================================================================
-- CREATE_12M_TRAINING_TABLE.sql
-- Description: This script creates the 12-month horizon training table by generating
--              the `target_12m` column.
-- Author: Your Name
-- Date: 2025-11-07
-- =======================================================================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base` AS
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
  `cbi-v14.models_v4.vertex_ai_training_6m_base`  -- Start from 6m base table (or production_training_data_6m if migrating)
;
