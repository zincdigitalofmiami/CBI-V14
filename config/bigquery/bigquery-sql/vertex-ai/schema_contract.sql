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
-- schema_contract.sql
-- Creates schema contract table to enforce consistent schema across all training tables
-- This prevents Vertex AI training failures due to schema mismatches
-- =======================================================================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_schema_contract` AS
SELECT 
    column_name,
    data_type,
    is_nullable,
    'zl_training_prod_allhistory_1m' as source_table  -- Current: training.zl_training_prod_allhistory_1m
FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'zl_training_prod_allhistory_1m'  -- Current: training.zl_training_prod_allhistory_1m
  AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w')
ORDER BY column_name;

-- Validate schema consistency
SELECT 
    column_name,
    COUNT(DISTINCT data_type) as distinct_types,
    STRING_AGG(DISTINCT data_type, ', ') as types_found
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('zl_training_prod_allhistory_1m', 'zl_training_prod_allhistory_3m', 
                     'zl_training_prod_allhistory_6m', 'zl_training_prod_allhistory_1w')  -- Current: training.zl_training_prod_allhistory_{horizon}
  AND column_name IN (SELECT column_name FROM `cbi-v14.models_v4.training_schema_contract`)
GROUP BY column_name
HAVING COUNT(DISTINCT data_type) > 1;

-- If above query returns rows, schema mismatch exists - fix before training

