# BigQuery Warehouse Rebuild Plan - Summary

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform

## Overview

This document provides a high-level summary of the BigQuery warehouse rebuild plan. The complete plan includes 6 documentation files, migration scripts, and a master execution plan.

## Documentation Files Created

### 1. Naming Convention Specification
**File**: `docs/plans/NAMING_CONVENTION_SPEC.md`

Defines the institutional-style naming pattern:
```
{asset_class}_{subcategory}_{instrument}_{function}_{frequency}_{environment}
```

Includes:
- Component definitions and examples
- Example mappings from old to new names
- Validation rules and migration checklist

### 2. Dataset Structure Design
**File**: `docs/plans/DATASET_STRUCTURE_DESIGN.md`

Defines the 6 purpose-driven datasets:
- `raw_intelligence` – Landing zone for ingestion
- `features` – Engineered feature datasets
- `training` – Finalized training tables
- `predictions` – Model outputs
- `monitoring` – Metrics and logs
- `archive` – Historical snapshots

### 3. Data Lineage Map
**File**: `docs/plans/DATA_LINEAGE_MAP.md`

Documents complete data flow:
- Ingestion → Raw Intelligence
- Raw Intelligence → Features
- Features → Training
- Training → Predictions
- All → Monitoring

Includes upstream sources, transformations, and downstream consumers for each table.

### 4. Deduplication Rules
**File**: `docs/plans/DEDUPLICATION_RULES.md`

Defines:
- Source precedence order for price, sentiment, weather, policy, and CFTC data
- Conflict resolution procedures (2%, 2-10%, >10% thresholds)
- Column consolidation rules (97 sentiment columns → canonical set)
- Audit table schema for tracking conflicts

### 5. Rollback Procedure
**File**: `docs/plans/ROLLBACK_PROCEDURE.md`

Provides:
- Pre-migration backup procedures
- Parallel operation strategy
- Cutover criteria
- Immediate, partial, and full rollback procedures
- Compatibility views for grace period

### 6. Validation Checklist
**File**: `docs/plans/VALIDATION_CHECKLIST.md`

18 validation checks covering:
- Table completeness
- Schema consistency
- Row counts & date ranges
- Model performance
- Downstream integration
- Data quality metrics
- Documentation completeness

## Migration Scripts Created

### 1. SQL Scripts
**Location**: `config/bigquery/migration/`

- `01_create_datasets.sql` – Creates all 6 new datasets
- `02_create_core_tables.sql` – Creates core table schemas

### 2. Python Migration Script
**File**: `scripts/migrate_warehouse_rebuild.py`

Automated migration script with phases:
- `migrate_raw_intelligence` – Migrate raw tables
- `build_features` – Build feature tables
- `build_training` – Build training tables
- `validate` – Validate migration

## Master Execution Plan

**File**: `docs/plans/MASTER_EXECUTION_PLAN.md`

9-phase execution plan:

1. **Inventory & Planning** (1-2 days)
2. **Create New Datasets** (1 hour)
3. **Migrate Raw Intelligence** (2-3 days)
4. **Build Feature Tables** (3-5 days)
5. **Build Training Tables** (2-3 days)
6. **Shadow Run & Validation** (5-7 days)
7. **Cutover & Backfill** (1 day)
8. **Cleanup & Archive** (2-3 days)
9. **Post-Migration Validation** (3-5 days)

**Total Duration**: 19-29 days

## Key Features

### Zero Downtime
- Parallel operation during migration
- Shadow mode validation
- Gradual cutover
- Compatibility views for grace period

### Data Integrity
- Complete backups before migration
- Row count verification at each phase
- Random sampling validation
- Schema consistency checks

### Risk Mitigation
- Comprehensive rollback procedures
- Validation at each phase
- Performance monitoring
- User acceptance testing

## Next Steps

1. **Review Documentation**
   - Read all 6 documentation files
   - Review master execution plan
   - Understand naming conventions

2. **Prepare for Migration**
   - Freeze schema changes
   - Backup current state
   - Verify inventory completeness

3. **Begin Phase 1**
   - Generate complete manifest
   - Create table mapping matrix
   - Define standard schemas

## Success Criteria

Migration is successful when:
- ✅ All 340 objects migrated or archived
- ✅ All validation checks passed
- ✅ Model performance matches baseline (ΔMAPE ≤ 0.1%)
- ✅ Dashboard API endpoints working
- ✅ Mac M4 training pipeline working
- ✅ Data quality metrics acceptable
- ✅ Documentation updated
- ✅ Team sign-off received

## Files Created

### Documentation
- `docs/plans/NAMING_CONVENTION_SPEC.md`
- `docs/plans/DATASET_STRUCTURE_DESIGN.md`
- `docs/plans/DATA_LINEAGE_MAP.md`
- `docs/plans/DEDUPLICATION_RULES.md`
- `docs/plans/ROLLBACK_PROCEDURE.md`
- `docs/plans/VALIDATION_CHECKLIST.md`
- `docs/plans/MASTER_EXECUTION_PLAN.md`
- `docs/plans/REBUILD_PLAN_SUMMARY.md` (this file)

### Migration Scripts
- `config/bigquery/migration/01_create_datasets.sql`
- `config/bigquery/migration/02_create_core_tables.sql`
- `scripts/migrate_warehouse_rebuild.py`

## References

For detailed information, see:
- Naming conventions: `NAMING_CONVENTION_SPEC.md`
- Dataset structure: `DATASET_STRUCTURE_DESIGN.md`
- Data flow: `DATA_LINEAGE_MAP.md`
- Deduplication: `DEDUPLICATION_RULES.md`
- Rollback: `ROLLBACK_PROCEDURE.md`
- Validation: `VALIDATION_CHECKLIST.md`
- Execution: `MASTER_EXECUTION_PLAN.md`

