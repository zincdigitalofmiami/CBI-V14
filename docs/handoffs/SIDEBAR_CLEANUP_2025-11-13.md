# Sidebar Cleanup - November 13, 2025

**Date**: November 13, 2025  
**Purpose**: Consolidate overlapping files and clean up sidebar structure

---

## Changes Made

### 1. Archived Mac Training Files (3 files)
**Location**: `active-plans/archive/`

- `MAC_TRAINING_SETUP_PLAN.md` → Archived (content merged into TRAINING_MASTER_EXECUTION_PLAN.md)
- `MAC_TRAINING_EXPANDED_STRATEGY.md` → Archived (content merged into TRAINING_MASTER_EXECUTION_PLAN.md)
- `HARDWARE_OPTIMIZED_TRAINING_GUIDE.md` → Archived (content merged into TRAINING_MASTER_EXECUTION_PLAN.md)

**Reason**: These files overlapped significantly with `TRAINING_MASTER_EXECUTION_PLAN.md`. The master plan now contains all Mac training information.

### 2. Archived Rebuild Plans (4 files)
**Location**: `docs/plans/archive/`

- `SURGICAL_REBUILD_CRITICAL_REVIEW.md` → Archived (review complete, content in BIGQUERY_REBUILD_MASTER_PLAN.md)
- `SURGICAL_REBUILD_PLAN_DRAFT_GPT5.md` → Archived (draft preserved, final plan in BIGQUERY_REBUILD_MASTER_PLAN.md)
- `REBUILD_PLAN_SUMMARY.md` → Archived (summary merged into BIGQUERY_REBUILD_MASTER_PLAN.md)
- `REBUILD_STATUS_REPORT.md` → Archived (status merged into BIGQUERY_REBUILD_MASTER_PLAN.md)

**Reason**: Multiple overlapping rebuild documents. `BIGQUERY_REBUILD_MASTER_PLAN.md` is now the single source of truth.

### 3. Moved Legacy React Files
**Location**: `archive/legacy_react/`

- `src/App.tsx` → Moved to archive
- `src/main.tsx` → Moved to archive
- `src/App.css` → Moved to archive

**Reason**: These are legacy React files. The active dashboard is in `dashboard-nextjs/`.

### 4. Moved Twitter Data
**Location**: `TrainingData/raw/twitter/`

- `src/ingestion/data/twitter/bulk_backfill.ndjson` → Moved to TrainingData/raw/twitter/

**Reason**: Data files should be in TrainingData/, not in source code directories.

---

## Final Structure

### active-plans/ (6 files)
- `BASELINE_STRATEGY.md`
- `PHASE_1_PRODUCTION_GAPS.md`
- `REGIME_BASED_TRAINING_STRATEGY.md`
- `TRAINING_MASTER_EXECUTION_PLAN.md` ⭐ **Master training plan**
- `TRUMP_ERA_EXECUTION_PLAN.md`
- `VERTEX_AI_TRUMP_ERA_PLAN.md`

### docs/plans/ (9 files)
- `BIGQUERY_REBUILD_MASTER_PLAN.md` ⭐ **Master rebuild plan**
- `COMPLETE_DATA_INTEGRATION_PLAN.md`
- `DATASET_STRUCTURE_DESIGN.md`
- `DATA_LINEAGE_MAP.md`
- `DEDUPLICATION_RULES.md`
- `NAMING_CONVENTION_SPEC.md`
- `REBUILD_PLAN_VALIDATION.md` (kept as reference)
- `ROLLBACK_PROCEDURE.md`
- `VALIDATION_CHECKLIST.md`

---

## Result

- **Reduced clutter**: 7 files archived, 1 data file moved
- **Clear hierarchy**: Single master plans for training and rebuild
- **Better organization**: Data files in TrainingData/, legacy code in archive/
- **Sidebar cleaner**: Fewer overlapping documents visible

---

## Accessing Archived Files

All archived files remain in the repository and can be accessed:
- Mac training: `active-plans/archive/`
- Rebuild plans: `docs/plans/archive/`
- Legacy React: `archive/legacy_react/`

