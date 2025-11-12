-- ============================================
-- GENERATE NULL AUDIT FOR ALL COLUMNS
-- This will show EVERY column and its NULL percentage
-- ============================================

-- Get all numeric columns
WITH all_columns AS (
  SELECT column_name
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
    AND column_name NOT IN ('date', 'symbol')
    AND data_type IN ('FLOAT64', 'INT64')
),

-- Generate dynamic SQL for each column
column_queries AS (
  SELECT 
    column_name,
    CONCAT(
      'SELECT ''', column_name, ''' as column_name, ',
      'COUNT(*) as total_rows, ',
      'COUNTIF(', column_name, ' IS NULL) as null_count, ',
      'ROUND(COUNTIF(', column_name, ' IS NULL) / COUNT(*) * 100, 1) as null_pct ',
      'FROM `cbi-v14.models_v4.training_dataset_super_enriched` ',
      'WHERE target_1w IS NOT NULL'
    ) as query_text
  FROM all_columns
)

SELECT query_text
FROM column_queries
ORDER BY column_name;



