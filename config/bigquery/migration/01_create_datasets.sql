-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================================================
-- BigQuery Warehouse Rebuild - Phase 1: Create New Datasets
-- ============================================================================
-- Date: November 13, 2025
-- Project: CBI-V14 Soybean Oil Forecasting Platform
--
-- This script creates the new purpose-driven datasets for the warehouse rebuild.
-- Run this script FIRST before any table migrations.
-- ============================================================================

-- Set project
SET @@project_id = 'cbi-v14';

-- ============================================================================
-- 1. RAW INTELLIGENCE DATASET
-- Landing zone for all ingestion scripts
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.raw_intelligence`
OPTIONS(
  description='Landing zone for ingestion scripts - raw unprocessed data from external sources',
  location='us-central1'
);

-- ============================================================================
-- 2. FEATURES DATASET
-- Engineered feature datasets for model training
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.features`
OPTIONS(
  description='Engineered feature datasets used for model training and prediction',
  location='us-central1'
);

-- ============================================================================
-- 3. TRAINING DATASET
-- Finalized training tables for each horizon and regime
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.training`
OPTIONS(
  description='Finalized training tables for each horizon and regime with targets',
  location='us-central1'
);

-- ============================================================================
-- 4. PREDICTIONS DATASET
-- Model outputs and forecasts for production
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.predictions`
OPTIONS(
  description='Model outputs and forecasts for production use',
  location='us-central1'
);

-- ============================================================================
-- 5. MONITORING DATASET
-- Metrics, logs, and health checks for data and models
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.monitoring`
OPTIONS(
  description='Metrics, logs, and health checks for data quality and model performance',
  location='us-central1'
);

-- ============================================================================
-- 6. ARCHIVE DATASET
-- Time-stamped snapshots of legacy tables and historical regimes
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS `cbi-v14.archive`
OPTIONS(
  description='Time-stamped snapshots of legacy tables and historical regimes',
  location='us-central1'
);

-- Create legacy archive sub-dataset for pre-migration backup
CREATE SCHEMA IF NOT EXISTS `cbi-v14.archive.legacy_nov12_2025`
OPTIONS(
  description='Pre-migration backup of all 340 original objects (November 12, 2025)',
  location='us-central1'
);

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this to verify all datasets were created successfully:
SELECT 
  schema_name,
  creation_time,
  location
FROM `cbi-v14.INFORMATION_SCHEMA.SCHEMATA`
WHERE schema_name IN (
  'raw_intelligence',
  'features',
  'training',
  'predictions',
  'monitoring',
  'archive'
)
ORDER BY schema_name;

