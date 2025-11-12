-- schema_contract.sql
-- Creates schema contract table to enforce consistent schema across all training tables
-- This prevents Vertex AI training failures due to schema mismatches

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_schema_contract` AS
SELECT 
    column_name,
    data_type,
    is_nullable,
    'vertex_ai_training_1m_base' as source_table  -- Or 'production_training_data_1m' if migrating
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'vertex_ai_training_1m_base'  -- Or 'production_training_data_1m' if migrating
  AND column_name NOT IN ('date', 'target_1m', 'target_3m', 'target_6m', 'target_1w')
ORDER BY column_name;

-- Validate schema consistency
SELECT 
    column_name,
    COUNT(DISTINCT data_type) as distinct_types,
    STRING_AGG(DISTINCT data_type, ', ') as types_found
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('vertex_ai_training_1m_base', 'vertex_ai_training_3m_base', 
                     'vertex_ai_training_6m_base', 'vertex_ai_training_1w_base')  -- Or production_training_data_* if migrating
  AND column_name IN (SELECT column_name FROM `cbi-v14.models_v4.training_schema_contract`)
GROUP BY column_name
HAVING COUNT(DISTINCT data_type) > 1;

-- If above query returns rows, schema mismatch exists - fix before training

