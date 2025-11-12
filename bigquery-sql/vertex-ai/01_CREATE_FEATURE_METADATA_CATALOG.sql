-- =======================================================================================
-- 01_CREATE_FEATURE_METADATA_CATALOG.sql
-- Description: Creates a rich metadata catalog for all features. This table serves as
--              the single source of truth for feature definitions, types, sources,
--              and other critical metadata needed for advanced modeling and governance.
--              It is initialized from the vertex_ai_training_1m_base schema (or production_training_data_1m if migrating).
-- v2 Update: Added `factor_group` to align with GS Quant / JPM DNA methodology.
-- Author: Your Name
-- Date: 2025-11-07
-- =======================================================================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.feature_metadata_catalog` AS
SELECT
  column_name,
  ordinal_position,
  data_type,
  is_nullable,
  
  -- ==========================================================================
  -- RICH METADATA COLUMNS (To be populated manually or by other scripts)
  -- ==========================================================================
  
  -- Factor Group (GS Quant / JPM DNA Style): (e.g., 'GROWTH', 'INFLATION', 'MONETARY_POLICY', 'VOLATILITY', 'POSITIONING', 'WEATHER')
  CAST(NULL AS STRING) AS factor_group,
  
  -- Feature Type: (e.g., 'PRICE', 'VOLUME', 'TECHNICAL_INDICATOR', 'FUNDAMENTAL', 'NEURAL_SCORE', 'TARGET')
  CAST(NULL AS STRING) AS feature_type,
  
  -- Source System: (e.g., 'yahoo_finance', 'fred', 'usda', 'cftc', 'internal_calculation')
  CAST(NULL AS STRING) AS source_system,
  
  -- Unit of Measurement: (e.g., 'USD', 'TONNE', '%', 'INDEX', 'DAYS', 'RATIO')
  CAST(NULL AS STRING) AS unit_of_measurement,
  
  -- Lag Information: (e.g., 7 for a 7-day lagged feature)
  CAST(NULL AS INT64) AS lag_days,
  
  -- Normalization Method: (e.g., 'MIN_MAX', 'Z_SCORE', 'NONE')
  CAST(NULL AS STRING) AS normalization_method,
  
  -- Description: A clear, human-readable description of the feature.
  CAST(NULL AS STRING) AS description

FROM
  `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE
  table_name = 'vertex_ai_training_1m_base'  -- Or 'production_training_data_1m' if migrating
ORDER BY
  ordinal_position;

-- Verification Step:
-- This query should return 444.
-- SELECT COUNT(*) FROM `cbi-v14.models_v4.feature_metadata_catalog`;

-- Example Population (for key columns):
/*
UPDATE `cbi-v14.models_v4.feature_metadata_catalog`
SET 
  factor_group = 'PRICE',
  feature_type = 'PRICE',
  source_system = 'yahoo_finance',
  unit_of_measurement = 'USD',
  description = 'The daily closing price for Soybean Oil Futures (ZL=F).'
WHERE column_name = 'zl_price_current';

UPDATE `cbi-v14.models_v4.feature_metadata_catalog`
SET 
  factor_group = 'TARGET',
  feature_type = 'TARGET',
  source_system = 'internal_calculation',
  unit_of_measurement = '%_CHANGE',
  description = 'The 1-month forward return target variable.'
WHERE column_name = 'target_1m';
*/
