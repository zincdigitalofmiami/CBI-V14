# Master Execution Plan - BigQuery Warehouse Rebuild

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document provides the complete phase-by-phase execution plan for rebuilding the CBI-V14 BigQuery warehouse. The plan ensures zero downtime, data integrity, and seamless transition to the new structure.

## Prerequisites

### Before Starting

1. **Review All Documentation**
   - [ ] Read `NAMING_CONVENTION_SPEC.md`
   - [ ] Read `DATASET_STRUCTURE_DESIGN.md`
   - [ ] Read `DATA_LINEAGE_MAP.md`
   - [ ] Read `DEDUPLICATION_RULES.md`
   - [ ] Read `ROLLBACK_PROCEDURE.md`
   - [ ] Read `VALIDATION_CHECKLIST.md`

2. **Verify Inventory**
   - [ ] Confirm all 340 objects are documented in `GPT_Data/inventory_340_objects.csv`
   - [ ] Review `GPT_Data/empty_minimal_tables.csv` for empty tables
   - [ ] Review `GPT_Data/duplicate_table_names.csv` for duplicates
   - [ ] Review `GPT_Data/schema_all_columns.csv` for schema information

3. **Freeze Schema Changes**
   - [ ] Notify all team members to freeze schema changes
   - [ ] Document any pending schema changes
   - [ ] Pause all non-critical ingestion jobs

4. **Backup Current State**
   - [ ] Run backup script: `python scripts/backup_all_tables.py`
   - [ ] Verify backup manifest created
   - [ ] Store backup configuration: `config/backup/pipeline_config_nov12_2025.json`

## Phase 1: Inventory & Planning

**Duration**: 1-2 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Generate Complete Manifest**
   ```bash
   python scripts/run_bq_inventory_export.py
   ```
   - [ ] Verify all 340 objects are captured
   - [ ] Review manifest: `GPT_Data/raw_exports/COMPLETE_MANIFEST.md`

2. **Identify Duplicates and Empty Tables**
   - [ ] Review `GPT_Data/duplicate_table_names.csv`
   - [ ] Review `GPT_Data/empty_minimal_tables.csv`
   - [ ] Create migration plan for each duplicate/empty table

3. **Create Table Mapping**
   - [ ] Map each of 340 objects to new structure
   - [ ] Document mappings in `docs/plans/TABLE_MAPPING_MATRIX.md`
   - [ ] Review mappings with team

4. **Create Standard Schemas**
   - [ ] Define schemas for top 50 critical tables
   - [ ] Document in `config/bigquery/migration/schemas/`
   - [ ] Review schemas for consistency

### Deliverables

- [ ] Complete inventory manifest
- [ ] Table mapping matrix
- [ ] Standard schema definitions
- [ ] Migration plan document

## Phase 2: Create New Datasets

**Duration**: 1 hour  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Create Datasets**
   ```bash
   # Run SQL script
   bq query --use_legacy_sql=false < config/bigquery/migration/01_create_datasets.sql
   ```
   - [ ] Verify all 6 datasets created
   - [ ] Verify archive sub-dataset created

2. **Set IAM Roles**
   - [ ] Configure service account permissions
   - [ ] Test write access for each dataset
   - [ ] Document IAM configuration

### Deliverables

- [ ] All 6 datasets created
- [ ] IAM roles configured
- [ ] Access verified

## Phase 3: Migrate Raw Intelligence

**Duration**: 2-3 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Migrate Raw Tables**
   ```bash
   python scripts/migrate_warehouse_rebuild.py --phase migrate_raw_intelligence
   ```
   - [ ] Migrate price tables (soybean_oil, corn, palm, etc.)
   - [ ] Migrate weather tables
   - [ ] Migrate policy intelligence tables
   - [ ] Migrate news intelligence tables
   - [ ] Migrate sentiment tables
   - [ ] Migrate FX and rates tables

2. **Apply Deduplication Rules**
   - [ ] Apply source precedence rules
   - [ ] Resolve conflicts per `DEDUPLICATION_RULES.md`
   - [ ] Log conflicts to `monitoring.dedup_conflicts`

3. **Verify Data Integrity**
   - [ ] Compare row counts (old vs new)
   - [ ] Verify date ranges preserved
   - [ ] Random sample validation

### Deliverables

- [ ] All raw intelligence tables migrated
- [ ] Deduplication conflicts resolved
- [ ] Data integrity verified

## Phase 4: Build Feature Tables

**Duration**: 3-5 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Build Master Feature Table**
   ```sql
   -- Transform raw intelligence into features
   -- See config/bigquery/migration/03_build_features.sql
   ```
   - [ ] Combine price features
   - [ ] Calculate correlation features
   - [ ] Compute volatility features
   - [ ] Aggregate macro features
   - [ ] Engineer weather features
   - [ ] Process policy features
   - [ ] Aggregate sentiment features
   - [ ] Calculate Big-8 signals

2. **Build Specialized Feature Tables**
   - [ ] Build `features.biofuel_rin_proxy_daily`
   - [ ] Build `features.commodities_agriculture_cftc_filled_daily`
   - [ ] Build other specialized feature tables

3. **Consolidate Duplicate Columns**
   - [ ] Consolidate 97 sentiment columns into canonical set
   - [ ] Consolidate price columns
   - [ ] Consolidate weather columns
   - [ ] Document consolidation in `DATA_LINEAGE_MAP.md`

### Deliverables

- [ ] Master feature table built (290+ features)
- [ ] Specialized feature tables built
- [ ] Duplicate columns consolidated
- [ ] Feature lineage documented

## Phase 5: Build Training Tables

**Duration**: 2-3 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Build Horizon Training Tables**
   ```bash
   python scripts/migrate_warehouse_rebuild.py --phase build_training
   ```
   - [ ] Build `training.horizon_1w_production`
   - [ ] Build `training.horizon_1m_production`
   - [ ] Build `training.horizon_3m_production`
   - [ ] Build `training.horizon_6m_production`
   - [ ] Build `training.horizon_12m_production`

2. **Build Regime Training Tables**
   - [ ] Build `training.regime_trump_2023_2025_production`
   - [ ] Build `training.regime_pre_crisis_2000_2007_archive`
   - [ ] Build `training.regime_recovery_2010_2016_archive`
   - [ ] Build `training.regime_trade_war_2017_2019_archive`
   - [ ] Build `training.regime_crisis_2008_archive`

3. **Ensure Schema Consistency**
   - [ ] Verify all training tables have identical schemas
   - [ ] Verify column order matches across horizons
   - [ ] Verify data types match

4. **Add Training Metadata**
   - [ ] Calculate `training_weight` for each row
   - [ ] Assign `market_regime` based on date ranges
   - [ ] Verify target columns (target_1w, target_1m, etc.)

### Deliverables

- [ ] All horizon training tables built
- [ ] All regime training tables built
- [ ] Schema consistency verified
- [ ] Training metadata added

## Phase 6: Shadow Run & Validation

**Duration**: 5-7 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Configure Shadow Mode**
   - [ ] Update pipeline configuration for shadow mode
   - [ ] Point training scripts to new tables
   - [ ] Keep old tables accessible

2. **Run Parallel Pipelines**
   - [ ] Run Mac M4 training on new tables
   - [ ] Run BQML models on new tables
   - [ ] Run prediction serving on new tables
   - [ ] Compare outputs daily

3. **Validate Performance**
   - [ ] Compare model performance (MAPE, MAE, R²)
   - [ ] Verify predictions match baseline
   - [ ] Test dashboard API endpoints
   - [ ] Verify data quality metrics

4. **Run Validation Checklist**
   ```bash
   # Run validation script
   python scripts/validate_migration.py --check-all
   ```
   - [ ] Complete all 18 validation checks
   - [ ] Document any issues
   - [ ] Fix blocking issues

### Deliverables

- [ ] Shadow mode running successfully
- [ ] Model performance validated
- [ ] All validation checks passed
- [ ] Validation report generated

## Phase 7: Cutover & Backfill

**Duration**: 1 day  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Final Pre-Cutover Checks**
   - [ ] All validation checks passed
   - [ ] Team sign-off received
   - [ ] Rollback plan ready
   - [ ] On-call engineer notified

2. **Update Pipeline Configuration**
   ```bash
   # Update training table references
   python scripts/update_pipeline_config.py --cutover
   ```
   - [ ] Update training scripts
   - [ ] Update feature engineering scripts
   - [ ] Update prediction serving scripts
   - [ ] Update dashboard API endpoints

3. **Cutover Execution**
   - [ ] Switch training pipeline to new tables
   - [ ] Switch prediction pipeline to new tables
   - [ ] Switch dashboard API to new tables
   - [ ] Monitor for errors

4. **Backfill Missing Data**
   - [ ] Identify any missing historical data
   - [ ] Backfill from archive if needed
   - [ ] Verify backfill completeness

### Deliverables

- [ ] Pipeline cutover complete
- [ ] All systems using new tables
- [ ] Missing data backfilled
- [ ] Cutover report generated

## Phase 8: Cleanup & Archive

**Duration**: 2-3 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Create Compatibility Views**
   ```sql
   -- Create views for backward compatibility
   CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_1m` AS
   SELECT * FROM `cbi-v14.training.horizon_1m_production`;
   ```
   - [ ] Create views for all critical tables
   - [ ] Test views work correctly
   - [ ] Document grace period (30 days)

2. **Archive Legacy Tables**
   - [ ] Move unused tables to `archive.legacy_nov12_2025`
   - [ ] Archive empty staging datasets
   - [ ] Document archived tables

3. **Clean Up Staging Datasets**
   - [ ] Drop unused staging datasets (models_v5, performance, raw)
   - [ ] Verify no dependencies before dropping
   - [ ] Document dropped datasets

4. **Update Documentation**
   - [ ] Update all documentation with new table names
   - [ ] Update API documentation
   - [ ] Update training guides
   - [ ] Update data lineage maps

### Deliverables

- [ ] Compatibility views created
- [ ] Legacy tables archived
- [ ] Staging datasets cleaned up
- [ ] Documentation updated

## Phase 9: Post-Migration Validation

**Duration**: 3-5 days  
**Status**: [ ] Not Started [ ] In Progress [ ] Complete

### Tasks

1. **Monitor System Health**
   - [ ] Monitor data quality daily
   - [ ] Monitor model performance daily
   - [ ] Monitor API response times
   - [ ] Monitor error rates

2. **User Acceptance Testing**
   - [ ] Test dashboard functionality
   - [ ] Test API endpoints
   - [ ] Test training pipeline
   - [ ] Collect user feedback

3. **Performance Optimization**
   - [ ] Optimize slow queries
   - [ ] Adjust partitioning/clustering
   - [ ] Optimize feature engineering
   - [ ] Document optimizations

### Deliverables

- [ ] System health monitoring active
- [ ] User acceptance testing complete
- [ ] Performance optimizations applied
- [ ] Post-migration report generated

## Timeline Summary

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|--------|
| Phase 1: Inventory & Planning | 1-2 days | | | [ ] |
| Phase 2: Create New Datasets | 1 hour | | | [ ] |
| Phase 3: Migrate Raw Intelligence | 2-3 days | | | [ ] |
| Phase 4: Build Feature Tables | 3-5 days | | | [ ] |
| Phase 5: Build Training Tables | 2-3 days | | | [ ] |
| Phase 6: Shadow Run & Validation | 5-7 days | | | [ ] |
| Phase 7: Cutover & Backfill | 1 day | | | [ ] |
| Phase 8: Cleanup & Archive | 2-3 days | | | [ ] |
| Phase 9: Post-Migration Validation | 3-5 days | | | [ ] |
| **Total** | **19-29 days** | | | |

## Risk Mitigation

### High-Risk Areas

1. **Data Loss Risk**
   - **Mitigation**: Complete backups before migration, verify row counts at each phase
   - **Rollback**: Immediate rollback if row counts decrease

2. **Model Performance Degradation**
   - **Mitigation**: Shadow run validation, compare performance metrics
   - **Rollback**: Rollback if MAPE increases >0.5%

3. **Pipeline Downtime**
   - **Mitigation**: Parallel operation, shadow mode, gradual cutover
   - **Rollback**: Immediate rollback if pipeline fails

4. **Schema Inconsistencies**
   - **Mitigation**: Schema validation at each phase, automated schema checks
   - **Rollback**: Fix schemas before proceeding

## Success Criteria

The migration is considered successful when:

1. ✅ All 340 objects migrated or archived
2. ✅ All validation checks passed
3. ✅ Model performance matches baseline (ΔMAPE ≤ 0.1%)
4. ✅ Dashboard API endpoints working correctly
5. ✅ Mac M4 training pipeline working with new tables
6. ✅ Data quality metrics within acceptable ranges
7. ✅ All documentation updated
8. ✅ Team sign-off received

## Sign-Off

- **Data Team Lead**: [ ] Approved
- **Platform Engineer**: [ ] Approved
- **Model Team Lead**: [ ] Approved
- **Project Manager**: [ ] Approved
- **Date**: _______________

## References

- `NAMING_CONVENTION_SPEC.md` – Naming rules
- `DATASET_STRUCTURE_DESIGN.md` – Dataset architecture
- `DATA_LINEAGE_MAP.md` – Data flow documentation
- `DEDUPLICATION_RULES.md` – Deduplication procedures
- `ROLLBACK_PROCEDURE.md` – Rollback instructions
- `VALIDATION_CHECKLIST.md` – Validation criteria

