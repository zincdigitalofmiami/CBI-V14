-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- BIGQUERY INVENTORY GENERATION FOR GPT-5 SURGICAL REBUILD
-- Run this locally on Mac to generate 340-object manifest
-- ============================================================================
-- Date: November 13, 2025
-- Purpose: Generate complete inventory for architectural redesign
-- Output: Save each query result to CSV for GPT-5
-- ============================================================================

-- ============================================================================
-- QUERY 1: COMPLETE TABLE INVENTORY (340 objects)
-- Save as: inventory_340_objects.csv
-- ============================================================================

SELECT 
  table_catalog as project,
  table_schema as dataset,
  table_name,
  table_type,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) as age_days,
  creation_time,
  CASE 
    WHEN ddl LIKE '%PARTITION BY%' THEN 'PARTITIONED'
    WHEN ddl LIKE '%CLUSTER BY%' THEN 'CLUSTERED'
    ELSE 'STANDARD'
  END as table_structure,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
  row_count,
  CASE 
    WHEN row_count = 0 THEN 'EMPTY'
    WHEN row_count < 100 THEN 'MINIMAL'
    WHEN row_count < 1000 THEN 'SMALL'
    WHEN row_count < 10000 THEN 'MEDIUM'
    ELSE 'LARGE'
  END as data_volume
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
ORDER BY table_schema, table_name;


-- ============================================================================
-- QUERY 2: SCHEMA DETAILS (All columns)
-- Save as: schema_all_columns.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  table_name,
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  is_partitioning_column,
  clustering_ordinal_position
FROM `cbi-v14.INFORMATION_SCHEMA.COLUMNS`
WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
ORDER BY table_schema, table_name, ordinal_position;


-- ============================================================================
-- QUERY 3: PRODUCTION TABLES DETAIL (Critical Assets)
-- Save as: production_tables_detail.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  table_name,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
  creation_time,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) as age_days,
  ddl
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%production_training_data%'
   OR table_name LIKE '%bqml%'
   OR table_name LIKE '%trump%'
   OR table_name LIKE '%vertex%'
ORDER BY table_schema, table_name;


-- ============================================================================
-- QUERY 4: DATASET SUMMARY (24 datasets)
-- Save as: dataset_summary.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  COUNT(*) as object_count,
  SUM(CASE WHEN table_type = 'BASE TABLE' THEN 1 ELSE 0 END) as tables,
  SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) as views,
  SUM(CASE WHEN table_type = 'MATERIALIZED VIEW' THEN 1 ELSE 0 END) as materialized_views,
  SUM(row_count) as total_rows,
  ROUND(SUM(size_bytes) / 1024 / 1024 / 1024, 2) as total_size_gb,
  MIN(creation_time) as oldest_object,
  MAX(creation_time) as newest_object
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
GROUP BY table_schema
ORDER BY object_count DESC;


-- ============================================================================
-- QUERY 5: EMPTY & MINIMAL TABLES (Candidates for deletion)
-- Save as: empty_minimal_tables.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  table_name,
  table_type,
  row_count,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) as age_days,
  creation_time
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE row_count <= 10
  AND table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
ORDER BY row_count, table_schema, table_name;


-- ============================================================================
-- QUERY 6: DUPLICATE TABLE NAMES (Same name, different datasets)
-- Save as: duplicate_table_names.csv
-- ============================================================================

SELECT 
  table_name,
  COUNT(*) as dataset_count,
  STRING_AGG(table_schema, ', ' ORDER BY table_schema) as datasets,
  STRING_AGG(CAST(row_count AS STRING), ', ' ORDER BY table_schema) as row_counts
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
GROUP BY table_name
HAVING COUNT(*) > 1
ORDER BY dataset_count DESC, table_name;


-- ============================================================================
-- QUERY 7: COLUMN NAME FREQUENCY (Find common patterns)
-- Save as: column_name_frequency.csv
-- ============================================================================

SELECT 
  column_name,
  COUNT(DISTINCT CONCAT(table_schema, '.', table_name)) as table_count,
  STRING_AGG(DISTINCT data_type, ', ' ORDER BY data_type) as data_types_used,
  STRING_AGG(DISTINCT table_schema, ', ' ORDER BY table_schema LIMIT 5) as sample_datasets
FROM `cbi-v14.INFORMATION_SCHEMA.COLUMNS`
WHERE table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
GROUP BY column_name
HAVING COUNT(DISTINCT CONCAT(table_schema, '.', table_name)) > 5
ORDER BY table_count DESC
LIMIT 100;


-- ============================================================================
-- QUERY 8: FEATURE COLUMNS (290 production features)
-- Save as: production_features_290.csv
-- ============================================================================

SELECT 
  column_name,
  data_type,
  is_nullable,
  COUNT(*) as appears_in_tables,
  STRING_AGG(DISTINCT table_name, ', ' ORDER BY table_name) as table_names
FROM `cbi-v14.INFORMATION_SCHEMA.COLUMNS`
WHERE table_schema = 'models_v4'
  AND table_name LIKE 'production_training_data%'
  AND column_name NOT IN ('date', 'row_number', 'rn')
GROUP BY column_name, data_type, is_nullable
ORDER BY column_name;


-- ============================================================================
-- QUERY 9: HISTORICAL DATA SOURCES (25-year coverage)
-- Save as: historical_data_sources.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  table_name,
  row_count,
  creation_time,
  CASE 
    WHEN table_name LIKE '%yahoo%' THEN 'Yahoo Finance'
    WHEN table_name LIKE '%soybean%' THEN 'Soybean Prices'
    WHEN table_name LIKE '%economic%' THEN 'Economic Indicators'
    WHEN table_name LIKE '%biofuel%' THEN 'Biofuel Data'
    WHEN table_name LIKE '%china%' THEN 'China Trade'
    ELSE 'Other'
  END as data_category
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE (table_name LIKE '%yahoo%' 
   OR table_name LIKE '%soybean_oil%'
   OR table_name LIKE '%economic_indicators%'
   OR table_name LIKE '%biofuel%'
   OR table_name LIKE '%historical%')
  AND table_schema NOT IN ('INFORMATION_SCHEMA', '_SESSION')
ORDER BY data_category, table_schema, table_name;


-- ============================================================================
-- QUERY 10: MODELS & TRAINING TABLES
-- Save as: models_training_inventory.csv
-- ============================================================================

SELECT 
  table_schema as dataset,
  table_name,
  table_type,
  row_count,
  ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
  creation_time,
  CASE 
    WHEN table_name LIKE 'bqml%' THEN 'BQML Model'
    WHEN table_name LIKE '%training_data%' THEN 'Training Dataset'
    WHEN table_name LIKE '%features%' THEN 'Feature Table'
    WHEN table_name LIKE '%vertex%' THEN 'Vertex AI'
    ELSE 'Other'
  END as model_category
FROM `cbi-v14.INFORMATION_SCHEMA.TABLES`
WHERE table_schema IN ('models_v4', 'models', 'models_v5', 'neural')
ORDER BY model_category, table_name;


-- ============================================================================
-- END OF INVENTORY QUERIES
-- ============================================================================
-- 
-- EXECUTION INSTRUCTIONS:
-- 
-- 1. Run each query in BigQuery console
-- 2. Download results as CSV
-- 3. Save with the filename indicated in comments
-- 4. Share CSVs with GPT-5 for architectural design
-- 
-- Expected outputs:
--   - inventory_340_objects.csv (~340 rows)
--   - schema_all_columns.csv (~3,000+ rows)
--   - production_tables_detail.csv (~20 rows)
--   - dataset_summary.csv (~24 rows)
--   - empty_minimal_tables.csv (~50+ rows)
--   - duplicate_table_names.csv (~20+ rows)
--   - column_name_frequency.csv (~100 rows)
--   - production_features_290.csv (~290 rows)
--   - historical_data_sources.csv (~30 rows)
--   - models_training_inventory.csv (~50 rows)
-- 
-- ============================================================================

