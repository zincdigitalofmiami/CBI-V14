# Folder Consolidation - November 13, 2025

**Date**: November 13, 2025  
**Purpose**: Eliminate competing folders and consolidate all plans into single location

---

## Changes Made

### 1. Consolidated Plan Folders ✅

**Before:**
- `active-plans/` - 6 training plans
- `docs/plans/` - 9 rebuild plans
- **Total**: 2 competing folders

**After:**
- `docs/plans/` - 15 active plans (all plans consolidated)
- `docs/plans/archive/` - 30 archived plans
- **Total**: 1 plan folder

**Files Moved:**
- `TRAINING_MASTER_EXECUTION_PLAN.md` → `docs/plans/`
- `BASELINE_STRATEGY.md` → `docs/plans/`
- `PHASE_1_PRODUCTION_GAPS.md` → `docs/plans/`
- `REGIME_BASED_TRAINING_STRATEGY.md` → `docs/plans/`
- `TRUMP_ERA_EXECUTION_PLAN.md` → `docs/plans/`
- `VERTEX_AI_TRUMP_ERA_PLAN.md` → `docs/plans/`

### 2. Consolidated Archives ✅

**Before:**
- `active-plans/archive/` - 3 files
- `docs/plans/archive/` - 7 files
- `docs/plans/old/` - 23 files
- **Total**: 3 archive locations

**After:**
- `docs/plans/archive/` - 30 files (all archives consolidated)
- **Total**: 1 archive location

### 3. Removed Competing Folders ✅

- ❌ Deleted `active-plans/` folder
- ❌ Deleted `docs/plans/old/` folder (merged into archive)

---

## Final Structure

### Single Plan Location: `docs/plans/`

**Active Plans (15 files):**
- Training Plans (6)
- BigQuery Rebuild Plans (9)

**Archived Plans (30 files):**
- Historical plans and drafts preserved in `docs/plans/archive/`

### Other Documentation (Not Competing)

These folders serve different purposes and are NOT competing:

- `docs/training/` - Training reports and status (not plans)
- `docs/production/` - Production system configs (not plans)
- `docs/handoffs/` - Session handoff documents
- `docs/audits/` - Audit reports
- `docs/analysis/` - Analysis reports
- `docs/reference/` - Reference documentation

---

## Result

✅ **Single source of truth**: All plans in `docs/plans/`  
✅ **No competing folders**: Removed `active-plans/`  
✅ **Clean archives**: All archived plans in `docs/plans/archive/`  
✅ **Clear structure**: Each folder has distinct purpose

---

## Access

- **Active Plans**: `docs/plans/*.md`
- **Archived Plans**: `docs/plans/archive/*.md`
- **Plan README**: `docs/plans/README.md`



