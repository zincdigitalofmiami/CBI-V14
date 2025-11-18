# Code Folder Consolidation - November 13, 2025

**Date**: November 13, 2025  
**Purpose**: Eliminate competing code folders and establish clear structure

---

## Changes Made

### 1. Consolidated Ingestion Code ✅

**Before:**
- `scripts/ingestion/` - 20 ingestion scripts
- `src/ingestion/` - 78 ingestion modules
- **Total**: 2 competing folders

**After:**
- `src/ingestion/` - All ingestion code (main + scripts)
- `src/ingestion/scripts/` - Execution scripts (20 files)
- `src/ingestion/` - Core modules (78 files)
- **Total**: 1 ingestion folder

**Files Moved:**
- All `scripts/ingestion/*.py` → `src/ingestion/scripts/`
- All `scripts/ingestion/*.sh` → `src/ingestion/scripts/`

### 2. Consolidated Training Code ✅

**Before:**
- `scripts/training/` - 7 training scripts
- `src/training/` - 9 training modules
- **Total**: 2 competing folders

**After:**
- `src/training/` - All training code (main + scripts)
- `src/training/scripts/` - Execution scripts (7 files)
- `src/training/baselines/` - Baseline modules (6 files)
- `src/training/` - Core modules (3 files)
- **Total**: 1 training folder

**Files Moved:**
- All `scripts/training/*.py` → `src/training/scripts/`
- All `scripts/training/*.sh` → `src/training/scripts/`

### 3. Removed Empty Folders ✅

- ❌ Deleted `scripts/analysis/` (empty)

---

## Final Structure

### Code Organization

**Single Source Locations:**
- `src/ingestion/` - All ingestion code
  - `src/ingestion/scripts/` - Execution scripts
  - `src/ingestion/*.py` - Core modules
- `src/training/` - All training code
  - `src/training/scripts/` - Execution scripts
  - `src/training/baselines/` - Baseline models
  - `src/training/*.py` - Core modules

**Documentation (Separate, Not Competing):**
- `docs/training/` - Training reports and documentation
- `docs/analysis/` - Analysis reports
- `docs/data-sources/ingestion/` - Ingestion documentation

---

## Rationale

**Convention:**
- `scripts/` = Standalone utility scripts (not domain-specific)
- `src/` = Source code modules and domain-specific code
- `docs/` = Documentation (separate from code)

**Consolidation Logic:**
- Domain-specific code belongs in `src/`
- Execution scripts for domain code belong with that domain
- Documentation stays in `docs/` (not competing with code)

---

## Result

✅ **Single source locations**: All ingestion code in `src/ingestion/`, all training code in `src/training/`  
✅ **No competing folders**: Removed `scripts/ingestion/` and `scripts/training/`  
✅ **Clear structure**: Code in `src/`, docs in `docs/`, utilities in `scripts/`  
✅ **Better organization**: Related code grouped together

---

## Access

- **Ingestion Code**: `src/ingestion/`
- **Ingestion Scripts**: `src/ingestion/scripts/`
- **Training Code**: `src/training/`
- **Training Scripts**: `src/training/scripts/`
- **Training Docs**: `docs/training/`
- **Analysis Docs**: `docs/analysis/`



