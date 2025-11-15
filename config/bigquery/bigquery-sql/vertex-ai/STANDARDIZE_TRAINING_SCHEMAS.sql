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
-- STANDARDIZE_TRAINING_SCHEMAS.sql
-- Description: This script standardizes the schemas of the 3m, 6m, and 12m training
--              tables to match the 1,000-column schema of the 1m table.
--              UPDATED: Uses new naming convention (vertex_ai_training_*_base)
-- Author: Your Name
-- Date: 2025-11-07
-- =======================================================================================

-- Step 1: Standardize the 3m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_3m_base_standardized` AS
SELECT
  t3.*,
  t1.* EXCEPT (date, target_1w, target_1m, target_3m, target_6m, target_12m) -- Exclude all common/target columns
FROM
  `cbi-v14.training.zl_training_prod_allhistory_3m` AS t3  -- Current: training.zl_training_prod_allhistory_3m
LEFT JOIN
  `cbi-v14.training.zl_training_prod_allhistory_1m` AS t1  -- Current: training.zl_training_prod_allhistory_1m
ON
  t3.date = t1.date;

-- Step 2: Standardize the 6m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized` AS
SELECT
  t6.*,
  t1.* EXCEPT (date, target_1w, target_1m, target_3m, target_6m, target_12m) -- Exclude all common/target columns
FROM
  `cbi-v14.training.zl_training_prod_allhistory_6m` AS t6  -- Current: training.zl_training_prod_allhistory_6m
LEFT JOIN
  `cbi-v14.training.zl_training_prod_allhistory_1m` AS t1  -- Current: training.zl_training_prod_allhistory_1m
ON
  t6.date = t1.date;

-- Step 3: Standardize the 12m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized` AS
SELECT
  t12.*,
  t1.* EXCEPT (date, target_1w, target_1m, target_3m, target_6m, target_12m) -- Exclude all common/target columns
FROM
  `cbi-v14.training.zl_training_prod_allhistory_12m` AS t12  -- Current: training.zl_training_prod_allhistory_12m
LEFT JOIN
  `cbi-v14.training.zl_training_prod_allhistory_1m` AS t1  -- Current: training.zl_training_prod_allhistory_1m
ON
  t12.date = t1.date;

-- =======================================================================================
-- Final Step: Overwrite original tables with standardized and deduplicated versions
-- =======================================================================================

-- ⚠️ LEGACY: These tables are not used in current architecture
-- Current architecture uses: training.zl_training_prod_allhistory_{horizon}
-- These CREATE statements are kept for reference only

-- Overwrite 3m table (LEGACY - not used)
-- CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_3m_base` AS
-- SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_3m_base_standardized`;

-- Overwrite 6m table (LEGACY - not used)
-- CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base` AS
-- SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized`;

-- Overwrite 12m table (LEGACY - not used)
-- CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base` AS
-- SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized`;

-- Drop the intermediate standardized tables (LEGACY - not used)
-- DROP TABLE `cbi-v14.models_v4.vertex_ai_training_3m_base_standardized`;
-- DROP TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized`;
-- DROP TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized`;
