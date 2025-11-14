# GPT-5 / FUTURE AI: READ THIS FIRST
**Critical: Current vs Legacy Work**

---

## 🎯 **CURRENT ARCHITECTURE** (Use This)

### **Source of Truth**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - **PRIMARY SOURCE**
- `CURRENT_WORK.md` - Current active work summary
- `README_CURRENT.md` - Current state overview

### **Current Training Strategy** (November 2025)
- **100% Local M4 Mac training** (TensorFlow Metal GPU)
- **BigQuery for storage only** (training data + predictions)
- **NO Vertex AI** (not used for training or inference)
- **NO BQML training** (deprecated, local training only)

### **Core Workflow**
1. BigQuery exports training data → Parquet
2. Mac M4 trains all models locally (baselines + advanced)
3. Mac M4 generates all predictions locally
4. Predictions uploaded to BigQuery via scripts
5. Vercel dashboard reads from BigQuery

### **Current Files**
- `scripts/export_training_data.py` - Export training data from BigQuery
- `scripts/upload_predictions.py` - Upload local predictions to BigQuery
- `src/training/baselines/*.py` - Local baseline training
- `src/training/advanced/*.py` - Local advanced models
- `src/prediction/generate_local_predictions.py` - Local prediction generation

---

## ❌ **LEGACY WORK** (Do NOT Use)

### **Legacy Locations**
- `archive/` - All old attempts
- `legacy/` - Very old work
- `docs/plans/archive/` - Old plans
- `scripts/deprecated/` - Deprecated scripts
- `vertex-ai/` - **NO LONGER USED** (kept for reference only)

### **Legacy Approaches**
- ❌ **Vertex AI training** - Replaced by local M4 training
- ❌ **Vertex AI inference** - Replaced by local prediction generation
- ❌ **BQML training** - Deprecated (BigQuery is storage only)
- ❌ **AutoML** - Replaced by custom local models
- ❌ **Cloud-first training** - Replaced by local-first approach

---

## 🚨 **CRITICAL RULES**

1. **ONLY reference** files in `docs/plans/` that are NOT in `archive/`
2. **ONLY use** scripts in `scripts/` that are NOT in `deprecated/`
3. **IGNORE** everything in `archive/` and `legacy/`
4. **IGNORE** Vertex AI references (local training only)
5. **IGNORE** BQML training plans (BigQuery is storage, not compute)
6. **USE** `TRAINING_MASTER_EXECUTION_PLAN.md` as source of truth

---

## 📋 **QUICK CHECKLIST**

Before referencing any file, check:
- [ ] Is it in `archive/`? → **IGNORE**
- [ ] Is it in `legacy/`? → **IGNORE**
- [ ] Is it in `docs/plans/archive/`? → **IGNORE**
- [ ] Does it reference Vertex AI for training? → **IGNORE** (local only)
- [ ] Does it reference BQML training? → **IGNORE** (deprecated)
- [ ] Is it dated before November 12, 2025? → **Check if legacy**

---

## ✅ **SAFE TO USE**

- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` ✅
- `docs/plans/BASELINE_STRATEGY.md` ✅
- `scripts/export_training_data.py` ✅
- `scripts/upload_predictions.py` ✅
- `src/training/` ✅ (all local training)
- `src/prediction/` ✅ (local prediction generation)

---

## 🏗️ **ARCHITECTURE SUMMARY**

**Storage**: BigQuery (training data, predictions, monitoring)  
**Compute**: Mac M4 with TensorFlow Metal (all training + inference)  
**UI**: Vercel dashboard (reads BigQuery only)  
**Workflow**: Export → Train Local → Predict Local → Upload → Dashboard

**No cloud compute. No Vertex AI. No BQML training. 100% local control.**

---

**Last Updated**: November 14, 2025  
**Status**: Active work - Local M4 training architecture (local-first, cloud for storage only)


---

## Migration Audit Reports (November 14, 2025)

**Location**: `docs/audits/20251114_*` and `scripts/migration/*AUDIT*.md`

After completing the naming architecture migration, comprehensive audit reports were generated to verify the migration state and identify remaining issues.

### Quick Access:
- **Index**: `docs/audits/20251114_MIGRATION_AUDIT_INDEX.md`
- **Pre-Fix Audit**: `docs/audits/20251114_PRE_FIX_AUDIT.md` (start here)
- **Final Audit**: `docs/audits/20251114_FINAL_AUDIT.md` (complete analysis)
- **Naming Structure**: `docs/audits/20251114_NAMING_STRUCTURE_AUDIT.md` (naming rules)

### Key Findings:
- Migration Status: 98% complete
- Critical Issues: 3 (all fixable, <20 minutes)
- Naming Compliance: ✅ All verified
- Data Integrity: ✅ All data exists

**Before making any changes**, review the audit reports to understand:
1. Current migration state
2. Naming convention requirements
3. Remaining issues and fixes
4. Verification procedures

