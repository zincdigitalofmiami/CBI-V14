-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Phase 2: Create New Datasets
-- Creates all required datasets for the new naming architecture
-- Run this before migrating tables

-- Create archive dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.archive`
OPTIONS(
  description='Time-stamped snapshots of legacy tables and historical regimes',
  location='us-central1'
);

-- Create raw_intelligence dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.raw_intelligence`
OPTIONS(
  description='Landing zone for ingestion scripts - raw unprocessed data',
  location='us-central1'
);

-- Create features dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.features`
OPTIONS(
  description='Engineered feature datasets for model training',
  location='us-central1'
);

-- Create training dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.training`
OPTIONS(
  description='Finalized training tables for each horizon and regime',
  location='us-central1'
);

-- Create predictions dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.predictions`
OPTIONS(
  description='Model outputs and forecasts for production',
  location='us-central1'
);

-- Create monitoring dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.monitoring`
OPTIONS(
  description='Metrics, logs, and health checks for data and models',
  location='us-central1'
);

-- Create vegas_intelligence dataset (if not exists)
CREATE SCHEMA IF NOT EXISTS `cbi-v14.vegas_intelligence`
OPTIONS(
  description='Data for the Vegas Intel sales dashboard',
  location='us-central1'
);

-- Note: yahoo_finance_comprehensive stays unchanged







