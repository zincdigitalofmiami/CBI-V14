# Legacy vs Current Marking - Complete
**Date**: November 12, 2025  
**Status**: ✅ **COMPLETE** - All legacy work clearly marked

---

## ✅ **MARKERS CREATED**

### **Entry Points for GPT-5**
1. **`GPT5_READ_FIRST.md`** - **START HERE** - Critical read-first guide
2. **`CURRENT_WORK.md`** - Current active work summary
3. **`README_CURRENT.md`** - Current state overview
4. **`CURRENT_VS_LEGACY_INDEX.md`** - Complete reference index

### **Legacy Warnings**
1. **`LEGACY_MARKER.md`** - General legacy warning
2. **`archive/README.md`** - Archive directory warning
3. **`legacy/README.md`** - Legacy directory warning
4. **`docs/plans/README.md`** - Plans directory guide

### **Pattern File**
1. **`.LEGACY_IGNORE_PATTERNS`** - File patterns to ignore

### **Updated Files**
1. **`README.md`** - Updated to point to current work

---

## 🎯 **CURRENT WORK CLEARLY MARKED**

### **Source of Truth**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - **PRIMARY SOURCE**

### **Current Architecture**
- **Training**: Local M4 Mac → Vertex AI deployment
- **NOT**: BQML training, AutoML, cloud-first

### **Current Files**
- `scripts/data_quality_checks.py`
- `scripts/export_training_data.py`
- `src/training/baselines/*.py`
- `vertex-ai/deployment/*.py`

---

## ❌ **LEGACY WORK CLEARLY MARKED**

### **Legacy Locations**
- `archive/` - **ENTIRE DIRECTORY** marked as legacy
- `legacy/` - **ENTIRE DIRECTORY** marked as legacy
- `docs/plans/archive/` - All old plans
- `scripts/deprecated/` - Deprecated scripts

### **Legacy Approaches**
- ❌ BQML training (replaced by Vertex AI)
- ❌ AutoML (replaced by custom neural models)
- ❌ Cloud-first training (replaced by local-first)

---

## 📋 **FOR GPT-5 / FUTURE AI**

### **READ FIRST:**
1. `GPT5_READ_FIRST.md` - Entry point
2. `CURRENT_WORK.md` - Current work summary
3. `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Source of truth

### **IGNORE:**
- Everything in `archive/`
- Everything in `legacy/`
- Everything in `docs/plans/archive/`
- BQML training plans
- AutoML references

### **QUICK CHECKLIST:**
Before referencing any file:
- [ ] Is it in `archive/`? → **IGNORE**
- [ ] Is it in `legacy/`? → **IGNORE**
- [ ] Does it mention BQML? → **IGNORE**
- [ ] Does it mention AutoML? → **IGNORE**

---

## ✅ **VERIFICATION**

All legacy directories now have:
- ✅ README.md with warning
- ✅ Clear "DO NOT USE" messaging
- ✅ Pointers to current work

All current work clearly marked:
- ✅ Source of truth identified
- ✅ Current files listed
- ✅ Current architecture documented

---

**Status**: ✅ **COMPLETE** - GPT-5 will not reference legacy work  
**Last Updated**: November 12, 2025

