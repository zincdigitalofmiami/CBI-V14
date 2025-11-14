# GPT-5 / FUTURE AI: READ THIS FIRST
**Critical: Current vs Legacy Work**

---

## 🎯 **CURRENT ARCHITECTURE** (Use This)

### **Source of Truth**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - **PRIMARY SOURCE**
- `CURRENT_WORK.md` - Current active work summary
- `README_CURRENT.md` - Current state overview

### **Current Training Strategy**
- **Local M4 Mac** training (TensorFlow Metal GPU)
- **Vertex AI** deployment (for online predictions)
- **BQML production** (5 horizons, live)

### **Current Files**
- `scripts/data_quality_checks.py` - Day 1 validation
- `scripts/export_training_data.py` - Data export
- `src/training/baselines/*.py` - Baseline training
- `vertex-ai/deployment/*.py` - Deployment pipeline

---

## ❌ **LEGACY WORK** (Do NOT Use)

### **Legacy Locations**
- `archive/` - All old attempts
- `legacy/` - Very old work
- `docs/plans/archive/` - Old plans
- `scripts/deprecated/` - Deprecated scripts

### **Legacy Approaches**
- ❌ **BQML training** - Replaced by Vertex AI
- ❌ **AutoML** - Replaced by custom neural models
- ❌ **Old architecture plans** - Replaced by MASTER_EXECUTION_PLAN

---

## 🚨 **CRITICAL RULES**

1. **ONLY reference** files in `docs/plans/` that are NOT in `archive/`
2. **ONLY use** scripts in `scripts/` that are NOT in `deprecated/`
3. **IGNORE** everything in `archive/` and `legacy/`
4. **IGNORE** BQML training plans (we use Vertex AI now)
5. **USE** `TRAINING_MASTER_EXECUTION_PLAN.md` as source of truth

---

## 📋 **QUICK CHECKLIST**

Before referencing any file, check:
- [ ] Is it in `archive/`? → **IGNORE**
- [ ] Is it in `legacy/`? → **IGNORE**
- [ ] Is it in `docs/plans/archive/`? → **IGNORE**
- [ ] Does it mention BQML training? → **IGNORE** (we use Vertex AI)
- [ ] Is it dated before November 12, 2025? → **Check if legacy**

---

## ✅ **SAFE TO USE**

- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` ✅
- `docs/plans/BASELINE_STRATEGY.md` ✅
- `docs/plans/PHASE_1_PRODUCTION_GAPS.md` ✅
- `scripts/data_quality_checks.py` ✅
- `scripts/export_training_data.py` ✅
- `src/training/` ✅
- `vertex-ai/deployment/` ✅

---

**Last Updated**: November 12, 2025  
**Status**: Active work - Local M4 → Vertex AI architecture

