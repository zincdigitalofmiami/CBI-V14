# Surgical Rebuild Plan - Status Report

**Date**: November 13, 2025  
**Status**: Planning Phase Complete, Execution Phase 0 Ready  
**Next Action**: Create missing deliverables and scripts

---

## Executive Summary

The surgical rebuild plan architecture is **85% complete**. Core design documents exist, BigQuery inventory is complete, and all data has been exported. However, critical execution deliverables are missing and must be created before migration begins.

---

## ✅ What's Complete

### 1. Core Architecture Documents (100% Complete)
- ✅ `docs/plans/DATASET_STRUCTURE_DESIGN.md` - 6-dataset structure fully defined
- ✅ `docs/plans/NAMING_CONVENTION_SPEC.md` - Institutional naming convention with examples
- ✅ `docs/plans/DATA_LINEAGE_MAP.md` - Complete data flow documentation
- ✅ `docs/plans/DEDUPLICATION_RULES.md` - Source precedence rules defined
- ✅ `docs/plans/MASTER_EXECUTION_PLAN.md` - 9-phase execution plan with checklists
- ✅ `docs/plans/ROLLBACK_PROCEDURE.md` - Rollback procedures documented
- ✅ `docs/plans/VALIDATION_CHECKLIST.md` - Validation criteria defined

### 2. BigQuery Inventory (100% Complete)
- ✅ `GPT_Data/inventory_340_objects.csv` - All 341 objects cataloged
- ✅ `GPT_Data/schema_all_columns.csv` - Complete schema inventory
- ✅ `GPT_Data/duplicate_table_names.csv` - Duplicates identified
- ✅ `GPT_Data/empty_minimal_tables.csv` - Empty tables flagged
- ✅ `GPT_Data/production_features_290.csv` - Production feature set documented
- ✅ `GPT_Data/historical_data_sources.csv` - Historical data coverage verified
- ✅ `GPT_Data/raw_exports/COMPLETE_MANIFEST.md` - Complete export manifest

### 3. Data Exports (100% Complete)
- ✅ All 341 BigQuery objects exported to `GPT_Data/raw_exports/` (322 Parquet files)
- ✅ Complete backup to `TrainingData/raw/` (external drive)
- ✅ Comprehensive audit data in `GPT_Data/comprehensive_audit/`

### 4. Migration Script (Partial - 40% Complete)
- ⚠️ `scripts/migrate_warehouse_rebuild.py` - Exists but needs critical updates:
  - Missing Vegas Intel mapping
  - Missing weather multi-location handling
  - Missing full 1,948-column feature preservation
  - Missing archive-first logic (`cbi-v14.archive_legacy_nov12`)

### 5. Plan Validation (100% Complete)
- ✅ `docs/plans/REBUILD_PLAN_VALIDATION.md` - Comprehensive gap analysis complete
- ✅ Identified all missing elements: Vegas Intel, view dependencies, full feature strategy

---

## ❌ What's Missing (Critical Gaps)

### 1. Table Mapping Matrix (NOT CREATED)
**Status**: Referenced in plan but not built  
**Priority**: CRITICAL - Cannot execute migration without this  
**Needed**: `docs/plans/TABLE_MAPPING_MATRIX.md` mapping all 341 objects

**Must Include**:
- Current location → new location for every object
- Vegas Intel tables → `raw_intelligence.intelligence_vegas_*` (sales-only, separate from forecasting)
- Weather tables → preserve multi-location structure (Argentina/Brazil/US/US_Midwest)
- Regime tables → `training.regime_*`
- Archive-only objects → `archive.legacy_nov12_2025_*`

### 2. Schema Normalization Guide (NOT CREATED)
**Status**: Not created  
**Priority**: HIGH - Needed for consistent migration  
**Needed**: `docs/plans/SCHEMA_NORMALIZATION_GUIDE.md`

**Must Include**:
- Date column standardization (`date` vs `timestamp` vs `date_time`)
- Required metadata fields (`ingest_timestamp`, `source`, `data_quality_flag`)
- Partitioning/clustering standards
- Schema migration scripts

### 3. Orchestration Options (NOT CREATED)
**Status**: Not created  
**Priority**: HIGH - Needed for execution  
**Needed**: `docs/plans/ORCHESTRATION_OPTIONS.md`

**Must Include**:
- How to execute Phase 0-9 (step-by-step)
- Cron/workflow examples
- Error handling and retry logic
- Monitoring/alerting setup

### 4. Documentation Governance (NOT CREATED)
**Status**: Not created  
**Priority**: MEDIUM - Needed for long-term maintenance  
**Needed**: `docs/plans/DOC_GOVERNANCE.md`

**Must Include**:
- Documentation map (what lives where)
- Retention rules (what to delete vs archive)
- Update procedures

### 5. Missing Scripts (CRITICAL)
**Status**: Scripts don't exist  
**Priority**: CRITICAL - Cannot execute without these

#### `scripts/upload_predictions.py` - DOES NOT EXIST
- **Purpose**: Upload local Mac M4 predictions → BigQuery `predictions.*`
- **Input**: Parquet/CSV files from `Models/` directory
- **Output**: BigQuery `predictions.horizon_*_production` tables

#### `scripts/view_dependency_analyzer.py` - DOES NOT EXIST
- **Purpose**: Analyze 100+ view dependencies, generate rebuild order
- **Input**: BigQuery view definitions
- **Output**: Ordered list of views with dependencies

#### `scripts/export_training_data.py` - EXISTS BUT NEEDS UPDATE
- **Current**: Exists but unclear if it supports full-feature exports
- **Needed**: Must support both:
  - Full-feature exports (1,948 columns) → `training.full_features_*`
  - Slim exports (290 columns) → `training.production_*`

### 6. Vegas Intel Clarification (NEEDS UPDATE)
**Status**: Understanding clarified but not reflected in plan  
**Priority**: HIGH - Critical for correct architecture

**Clarification Needed**:
- Vegas Intel = Sales intelligence layer (separate from forecasting)
- Data source: Glide API (READ-ONLY)
- Purpose: Kevin's upsell opportunity tool for US Oil Solutions restaurant customers
- Integration: Pulls ZL price from forecasting system (one-way)
- Location: `raw_intelligence.intelligence_vegas_*` (sales domain, not forecasting)

**Files to Update**:
- `docs/plans/DATASET_STRUCTURE_DESIGN.md` - Add Vegas Intel section
- `docs/plans/DATA_LINEAGE_MAP.md` - Add Vegas Intel flow
- `docs/plans/NAMING_CONVENTION_SPEC.md` - Add Vegas Intel examples

### 7. Archive-First Logic (NOT IMPLEMENTED)
**Status**: Plan mentions it but scripts don't implement  
**Priority**: CRITICAL - Required by GPT-5's original plan

**Needed**: Update `scripts/migrate_warehouse_rebuild.py` to:
- First copy ALL 341 objects to `cbi-v14.archive_legacy_nov12`
- Verify archive completeness before any migration
- No deletions until archive validated

### 8. Full Feature Strategy (NOT DOCUMENTED)
**Status**: Mentioned but not detailed  
**Priority**: HIGH - Critical for local training pipeline

**Needed**: Explicit documentation:
- `training.full_features_*` tables = 1,948 columns (all data)
- `training.production_*` tables = 290 columns (slim set)
- Local Mac M4 training uses full-feature tables
- Export script must support both

---

## 🎯 Next Steps (Priority Order)

### Immediate (Phase 0 - Tooling Readiness)

1. **Create `docs/plans/TABLE_MAPPING_MATRIX.md`**
   - Map all 341 objects with Vegas Intel, weather, regimes explicitly called out
   - CSV format with columns: `current_dataset`, `current_table`, `new_dataset`, `new_table`, `special_handling`, `notes`

2. **Update `scripts/migrate_warehouse_rebuild.py`**
   - Add archive-first logic (`cbi-v14.archive_legacy_nov12`)
   - Add Vegas Intel mapping (`raw_intelligence.intelligence_vegas_*`)
   - Add weather multi-location preservation
   - Add full-feature vs production table logic

3. **Create `scripts/upload_predictions.py`**
   - Upload local Parquet/CSV predictions → BigQuery `predictions.*`
   - Support all 5 horizons (1w, 1m, 3m, 6m, 12m)
   - Include validation and error handling

4. **Create `scripts/view_dependency_analyzer.py`**
   - Analyze 100+ views, output rebuild order
   - Generate dependency graph
   - Output ordered list for Phase 7

### Short-Term (Phase 1 - Architecture Finalization)

5. **Create `docs/plans/SCHEMA_NORMALIZATION_GUIDE.md`**
   - Date column standards, required fields, partitioning rules
   - Migration scripts for schema normalization

6. **Update `docs/plans/DATASET_STRUCTURE_DESIGN.md`**
   - Add Vegas Intel section (sales-only, separate domain)
   - Clarify weather multi-location structure
   - Document full-feature vs production training tables

7. **Update `docs/plans/DATA_LINEAGE_MAP.md`**
   - Add Vegas Intel flow (Glide → BigQuery → Dashboard, READ-ONLY)
   - Add local training loop (BigQuery → Parquet → Mac M4 → predictions → BigQuery)

8. **Create `docs/plans/ORCHESTRATION_OPTIONS.md`**
   - Step-by-step execution guide for all phases
   - Cron/workflow examples
   - Error handling procedures

### Medium-Term (Phase 2+ - Execution)

9. **Update `scripts/export_training_data.py`**
   - Support full-feature and production exports
   - Document usage in `docs/training/LOCAL_BASELINES_FULL_DATA.md`

10. **Create `docs/plans/DOC_GOVERNANCE.md`**
    - Documentation map and retention rules
    - Update procedures

11. **Execute Phase 2**: Create new datasets
12. **Execute Phase 3**: Archive everything first (`archive_legacy_nov12`)

---

## 📊 Completion Status

| Category | Status | Completion |
|----------|--------|------------|
| Architecture Documents | ✅ Complete | 100% |
| BigQuery Inventory | ✅ Complete | 100% |
| Data Exports | ✅ Complete | 100% |
| Plan Validation | ✅ Complete | 100% |
| Migration Scripts | ⚠️ Partial | 40% |
| Table Mapping Matrix | ❌ Missing | 0% |
| Schema Normalization | ❌ Missing | 0% |
| Orchestration Guide | ❌ Missing | 0% |
| Doc Governance | ❌ Missing | 0% |
| **Overall** | **⚠️ In Progress** | **65%** |

---

## 🚨 Critical Blockers

**Cannot proceed to Phase 2 (Create New Datasets) until**:
1. ✅ Table Mapping Matrix created
2. ✅ Archive-first logic implemented in migration script
3. ✅ Vegas Intel mapping clarified and documented
4. ✅ View dependency analyzer created

**Cannot proceed to Phase 5 (Local Training Integration) until**:
1. ✅ `scripts/upload_predictions.py` created
2. ✅ `scripts/export_training_data.py` updated for full-feature exports

---

## 📝 Notes

- **Vegas Intel**: Now understood as sales intelligence layer (separate from forecasting). Must be mapped to `raw_intelligence.intelligence_vegas_*` with clear separation from forecasting data.

- **Archive Strategy**: GPT-5's original plan requires ALL 341 objects copied to `cbi-v14.archive_legacy_nov12` BEFORE any migration. This is non-negotiable.

- **Full Feature Training**: Local Mac M4 pipeline requires access to full 1,948-column feature set. Must preserve both full-feature and production (290-column) tables.

- **Weather Data**: Multi-location structure (Argentina/Brazil/US/US_Midwest) must be preserved. Not just a single aggregated table.

---

**Last Updated**: November 13, 2025  
**Next Review**: After Phase 0 deliverables complete

