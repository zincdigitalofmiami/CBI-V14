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
  `cbi-v14.models_v4.vertex_ai_training_3m_base` AS t3  -- Or production_training_data_3m if migrating
LEFT JOIN
  `cbi-v14.models_v4.vertex_ai_training_1m_base` AS t1  -- Or production_training_data_1m if migrating
ON
  t3.date = t1.date;

-- Step 2: Standardize the 6m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized` AS
SELECT
  t6.*,
  t1.* EXCEPT (date, target_1w, target_1m, target_3m, target_6m, target_12m) -- Exclude all common/target columns
FROM
  `cbi-v14.models_v4.vertex_ai_training_6m_base` AS t6  -- Or production_training_data_6m if migrating
LEFT JOIN
  `cbi-v14.models_v4.vertex_ai_training_1m_base` AS t1  -- Or production_training_data_1m if migrating
ON
  t6.date = t1.date;

-- Step 3: Standardize the 12m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized` AS
SELECT
  t12.*,
  t1.* EXCEPT (date, target_1w, target_1m, target_3m, target_6m, target_12m) -- Exclude all common/target columns
FROM
  `cbi-v14.models_v4.vertex_ai_training_12m_base` AS t12  -- Or production_training_data_12m if migrating
LEFT JOIN
  `cbi-v14.models_v4.vertex_ai_training_1m_base` AS t1  -- Or production_training_data_1m if migrating
ON
  t12.date = t1.date;

-- =======================================================================================
-- Final Step: Overwrite original tables with standardized and deduplicated versions
-- =======================================================================================

-- Overwrite 3m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_3m_base` AS
SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_3m_base_standardized`;

-- Overwrite 6m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base` AS
SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized`;

-- Overwrite 12m table
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base` AS
SELECT * FROM `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized`;

-- Drop the intermediate standardized tables
DROP TABLE `cbi-v14.models_v4.vertex_ai_training_3m_base_standardized`;
DROP TABLE `cbi-v14.models_v4.vertex_ai_training_6m_base_standardized`;
DROP TABLE `cbi-v14.models_v4.vertex_ai_training_12m_base_standardized`;
