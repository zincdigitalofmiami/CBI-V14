# Rollback Procedure

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document provides step-by-step procedures for rolling back the BigQuery warehouse rebuild if critical issues are discovered during or after migration. The rollback plan ensures zero data loss and minimal downtime.

## Pre-Migration Backups

### Phase 1: Export All Current Tables

Before making any changes, export all current tables to the archive dataset.

```bash
# Run backup script
python scripts/backup_all_tables.py \
  --project cbi-v14 \
  --source-datasets forecasting_data_warehouse,models_v4,api,curated,dashboard \
  --target-dataset archive.legacy_nov12_2025 \
  --format parquet \
  --location us-central1
```

**Backup Checklist**:
- [ ] All 340 objects exported to `archive.legacy_nov12_2025`
- [ ] Row counts verified for all tables
- [ ] Checksums calculated and stored
- [ ] Backup manifest created (`archive.legacy_nov12_2025.BACKUP_MANIFEST`)

### Phase 2: Create Backup Manifest

```sql
-- Create backup manifest
CREATE OR REPLACE TABLE `cbi-v14.archive.legacy_nov12_2025.BACKUP_MANIFEST` AS
SELECT 
  dataset_name,
  table_name,
  row_count,
  size_bytes,
  TIMESTAMP('2025-11-12 00:00:00') as backup_timestamp,
  FORMAT('%s.%s', dataset_name, table_name) as original_location
FROM `cbi-v14.archive.legacy_nov12_2025.__TABLES__`
ORDER BY dataset_name, table_name;
```

### Phase 3: Record Current Configuration

Document current pipeline configuration:

```bash
# Export current configuration
python scripts/export_pipeline_config.py \
  --output config/backup/pipeline_config_nov12_2025.json
```

**Configuration to Backup**:
- Training table names and locations
- Feature table names and locations
- Prediction table names and locations
- Dashboard API endpoints
- Mac M4 training script paths
- BQML model names and locations

## Parallel Operation Strategy

### During Migration

**Critical Rule**: Do NOT modify existing tables during migration.

1. **Create New Tables**: All new tables are created in new datasets (`raw_intelligence`, `features`, `training`, `predictions`, `monitoring`)
2. **Shadow Mode**: Run pipeline in shadow mode reading from new tables
3. **Compare Outputs**: Daily comparison of old vs new table outputs
4. **Keep Old Tables**: Original tables remain untouched until cutover

### Shadow Mode Configuration

```python
# Example shadow mode configuration
SHADOW_MODE = {
    'enabled': True,
    'old_tables': {
        'training': 'models_v4.production_training_data_1m',
        'features': 'models_v4.vertex_core_features',
        'predictions': 'predictions.monthly_vertex_predictions'
    },
    'new_tables': {
        'training': 'training.horizon_1m_production',
        'features': 'features.general_master_daily',
        'predictions': 'predictions.horizon_1m_production'
    },
    'comparison_enabled': True,
    'alert_on_diff': True
}
```

## Cutover Criteria

Only switch the live pipeline to new tables when ALL criteria are met:

### 1. Row Counts Match or Exceed

```sql
-- Verify row counts
SELECT 
  'old' as source,
  COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`
UNION ALL
SELECT 
  'new' as source,
  COUNT(*) as row_count
FROM `cbi-v14.training.horizon_1m_production`;
```

**Requirement**: New table row count ≥ old table row count

### 2. Model Performance Matches Baseline

```sql
-- Compare model performance
SELECT 
  'old' as source,
  AVG(mape) as avg_mape,
  AVG(mae) as avg_mae,
  AVG(r2) as avg_r2
FROM `cbi-v14.monitoring.model_performance_daily`
WHERE table_source = 'models_v4.production_training_data_1m'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
UNION ALL
SELECT 
  'new' as source,
  AVG(mape) as avg_mape,
  AVG(mae) as avg_mae,
  AVG(r2) as avg_r2
FROM `cbi-v14.monitoring.model_performance_daily`
WHERE table_source = 'training.horizon_1m_production'
  AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
```

**Requirements**:
- ΔMAPE ≤ 0.1%
- ΔR² ≤ 0.01
- ΔMAE ≤ 0.1%

### 3. Dashboard Endpoints Tested

```bash
# Test dashboard API endpoints
curl -X GET "https://api.cbi-v14.com/api/v4/procurement-timing?horizon=1m" \
  -H "X-Test-Mode: shadow" \
  -H "X-Table-Source: new"
```

**Requirements**:
- All API endpoints return identical data
- Response times within 10% of baseline
- No errors or warnings

### 4. Data Quality Checks Pass

```sql
-- Verify data quality
SELECT 
  table_name,
  freshness_days,
  null_rate,
  duplicate_count
FROM `cbi-v14.monitoring.data_quality_daily`
WHERE date = CURRENT_DATE()
  AND (freshness_days > 2 OR null_rate > 0.05 OR duplicate_count > 0);
```

**Requirements**:
- No tables older than 2 days
- No critical features with >5% nulls
- No duplicate dates after deduplication

## Rollback Triggers

Immediately trigger rollback if:

1. **Critical Errors**: Any production pipeline failures
2. **Data Loss**: Row count decreases by >1%
3. **Model Degradation**: MAPE increases by >0.5%
4. **Data Quality Issues**: Freshness >7 days or null rate >10%
5. **Dashboard Failures**: API endpoints return errors
6. **User Complaints**: Multiple user reports of incorrect data

## Rollback Procedures

### Immediate Rollback (Within 1 Hour)

If critical issues are detected immediately after cutover:

#### Step 1: Revert Pipeline Configuration

```bash
# Restore old configuration
python scripts/restore_pipeline_config.py \
  --backup config/backup/pipeline_config_nov12_2025.json \
  --restore-mode immediate
```

#### Step 2: Update Training Scripts

```python
# Update training table references
TRAINING_TABLES = {
    '1w': 'models_v4.production_training_data_1w',  # Revert to old
    '1m': 'models_v4.production_training_data_1m',  # Revert to old
    '3m': 'models_v4.production_training_data_3m',  # Revert to old
    '6m': 'models_v4.production_training_data_6m',  # Revert to old
    '12m': 'models_v4.production_training_data_12m'  # Revert to old
}
```

#### Step 3: Update Dashboard API

```typescript
// Revert API endpoints
const TRAINING_TABLE = 'models_v4.production_training_data_1m';  // Old table
const FEATURES_TABLE = 'models_v4.vertex_core_features';  // Old table
const PREDICTIONS_TABLE = 'predictions.monthly_vertex_predictions';  // Old table
```

#### Step 4: Verify Rollback

```bash
# Run validation tests
python scripts/validate_rollback.py \
  --check-row-counts \
  --check-api-endpoints \
  --check-model-performance
```

### Partial Rollback (Within 24 Hours)

If issues are detected in specific components:

#### Rollback Feature Tables Only

```sql
-- Revert feature table references
CREATE OR REPLACE VIEW `cbi-v14.features.general_master_daily` AS
SELECT * FROM `cbi-v14.models_v4.vertex_core_features`;
```

#### Rollback Training Tables Only

```sql
-- Revert training table references
CREATE OR REPLACE VIEW `cbi-v14.training.horizon_1m_production` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;
```

#### Rollback Predictions Only

```sql
-- Revert prediction table references
CREATE OR REPLACE VIEW `cbi-v14.predictions.horizon_1m_production` AS
SELECT * FROM `cbi-v14.predictions.monthly_vertex_predictions`;
```

### Full Rollback (Within 7 Days)

If comprehensive issues are detected:

#### Step 1: Restore from Archive

```bash
# Restore all tables from archive
python scripts/restore_from_archive.py \
  --source-dataset archive.legacy_nov12_2025 \
  --target-datasets forecasting_data_warehouse,models_v4,api,curated,dashboard \
  --verify-checksums
```

#### Step 2: Drop New Datasets

```sql
-- Drop new datasets (after verification)
DROP SCHEMA IF EXISTS `cbi-v14.raw_intelligence` CASCADE;
DROP SCHEMA IF EXISTS `cbi-v14.features` CASCADE;
DROP SCHEMA IF EXISTS `cbi-v14.training` CASCADE;
DROP SCHEMA IF EXISTS `cbi-v14.predictions` CASCADE;
DROP SCHEMA IF EXISTS `cbi-v14.monitoring` CASCADE;
```

#### Step 3: Restore Configuration

```bash
# Restore full configuration
python scripts/restore_pipeline_config.py \
  --backup config/backup/pipeline_config_nov12_2025.json \
  --restore-mode full
```

## Compatibility Views

During the transition period (30 days), maintain compatibility views:

```sql
-- Create compatibility views
CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_1m` AS
SELECT * FROM `cbi-v14.training.horizon_1m_production`;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.vertex_core_features` AS
SELECT * FROM `cbi-v14.features.general_master_daily`;

CREATE OR REPLACE VIEW `cbi-v14.predictions.monthly_vertex_predictions` AS
SELECT * FROM `cbi-v14.predictions.horizon_1m_production`;
```

**Grace Period**: 30 days after cutover

**After Grace Period**: Drop compatibility views and update all references

## Rollback Validation

After rollback, verify:

### 1. Data Integrity

```sql
-- Compare row counts
SELECT 
  'old' as source,
  COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`
UNION ALL
SELECT 
  'restored' as source,
  COUNT(*) as row_count
FROM `cbi-v14.archive.legacy_nov12_2025.production_training_data_1m`;
```

**Requirement**: Row counts match exactly

### 2. Pipeline Functionality

```bash
# Test pipeline end-to-end
python scripts/test_pipeline.py \
  --test-training \
  --test-predictions \
  --test-api
```

**Requirement**: All tests pass

### 3. Model Performance

```sql
-- Verify model performance restored
SELECT 
  AVG(mape) as avg_mape,
  AVG(mae) as avg_mae,
  AVG(r2) as avg_r2
FROM `cbi-v14.monitoring.model_performance_daily`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
```

**Requirement**: Performance matches pre-migration baseline

## Post-Rollback Actions

1. **Root Cause Analysis**: Document why rollback was necessary
2. **Fix Issues**: Address problems in new tables/datasets
3. **Update Plan**: Revise migration plan based on lessons learned
4. **Re-attempt**: Schedule new migration attempt after fixes

## Rollback Decision Matrix

| Issue Type | Severity | Rollback Type | Time Window |
|-----------|----------|---------------|-------------|
| Data loss | Critical | Immediate | < 1 hour |
| Model degradation | High | Immediate | < 1 hour |
| API failures | High | Immediate | < 1 hour |
| Data quality issues | Medium | Partial | < 24 hours |
| Performance degradation | Medium | Partial | < 24 hours |
| Minor schema issues | Low | Full | < 7 days |

## Emergency Contacts

- **Data Team Lead**: [Contact Info]
- **Platform Engineer**: [Contact Info]
- **On-Call Engineer**: [Contact Info]

## References

- See `VALIDATION_CHECKLIST.md` for validation procedures
- See `MASTER_EXECUTION_PLAN.md` for migration steps

