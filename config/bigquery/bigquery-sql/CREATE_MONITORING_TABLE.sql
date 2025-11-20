-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- CREATE MONITORING TABLE
-- ============================================
-- Purpose: Track daily monitoring checks for prediction quality
-- Dataset: cbi-v14.predictions_uc1
-- Table: monitoring_checks
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.predictions_uc1.monitoring_checks` (
  check_id STRING NOT NULL,
  check_date DATE NOT NULL,
  check_type STRING NOT NULL,  -- 'staleness', 'quality', 'completeness', 'accuracy'
  status STRING NOT NULL,  -- 'PASS', 'WARN', 'FAIL'
  message STRING,
  details JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY check_date
CLUSTER BY check_type, status
OPTIONS(
  description="Daily monitoring checks for prediction quality, staleness, completeness, and accuracy"
);

-- ============================================
-- VERIFICATION
-- ============================================
-- Check table was created
/*
SELECT 
  table_name,
  row_count,
  size_bytes,
  created
FROM `cbi-v14.predictions_uc1.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'monitoring_checks';
*/

