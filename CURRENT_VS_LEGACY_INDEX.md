# Current vs Legacy Index
**Complete reference for GPT-5 and future AI assistants**

---

## ✅ **CURRENT WORK** (Use These)

### **Source of Truth**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - **PRIMARY SOURCE**
- `CURRENT_WORK.md` - Current active work summary
- `README_CURRENT.md` - Current state overview

### **Current Plans**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - 7-day institutional system
- `docs/plans/BASELINE_STRATEGY.md` - Baseline training approach
- `docs/plans/PHASE_1_PRODUCTION_GAPS.md` - Production gaps to fix
- `docs/plans/VERTEX_AI_TRUMP_ERA_PLAN.md` - Vertex AI deployment

### **Current Scripts**
- `scripts/data_quality_checks.py` - Day 1 validation
- `scripts/export_training_data.py` - BigQuery → Parquet export
- `scripts/audit_training_data_complete.py` - Complete data audit
- `src/training/baselines/statistical.py` - Statistical baselines
- `src/training/baselines/tree_models.py` - Tree baselines
- `src/training/baselines/neural_baseline.py` - Neural baselines
- `src/training/config_mlflow.py` - MLflow setup
- `EXECUTE_DAY_1.sh` - Day 1 execution

### **Current Deployment**
- `vertex-ai/deployment/train_local_deploy_vertex.py` - Local → Vertex pipeline
- `vertex-ai/deployment/export_savedmodel.py` - SavedModel export
- `vertex-ai/deployment/upload_to_vertex.py` - Vertex upload
- `vertex-ai/deployment/create_endpoint.py` - Endpoint deployment

### **Current Data**
- `models_v4.production_training_data_1w` - 1-week horizon
- `models_v4.production_training_data_1m` - 1-month horizon
- `models_v4.production_training_data_3m` - 3-month horizon
- `models_v4.production_training_data_6m` - 6-month horizon
- `models_v4.production_training_data_12m` - 12-month horizon
- `forecasting_data_warehouse.soybean_oil_prices` - 6,057 rows (2000-2025)

---

## ❌ **LEGACY WORK** (Do NOT Use)

### **Legacy Plans**
- `docs/plans/archive/` - **ALL FILES** (30+ old plans)
- `legacy/old-plans/` - Very old plans
- `legacy/bqml-work/` - BQML training plans (replaced by Vertex AI)
- Any plan mentioning BQML training

### **Legacy Scripts**
- `archive/oct31_2025_cleanup/scripts_legacy/` - Old scripts
- `archive/legacy_scripts/` - Very old scripts
- `scripts/deprecated/` - Deprecated scripts
- Any script in `archive/` subdirectories

### **Legacy Architecture**
- `archive/` - **ENTIRE DIRECTORY** - All old attempts
- `docs/handoffs/` (files dated before November 12, 2025) - Old handoffs
- All BQML training references
- All AutoML references

### **Legacy Approaches**
- ❌ **BQML training** - Replaced by Vertex AI
- ❌ **AutoML** - Replaced by custom neural models
- ❌ **Cloud-first training** - Replaced by local-first

---

## 🚨 **CRITICAL RULES FOR GPT-5**

### **DO:**
1. Read `GPT5_READ_FIRST.md` first
2. Use `TRAINING_MASTER_EXECUTION_PLAN.md` as source of truth
3. Reference files in `docs/plans/` (NOT in `archive/`)
4. Use scripts in `scripts/` (NOT in `deprecated/`)
5. Follow Local M4 → Vertex AI architecture

### **DON'T:**
1. Reference anything in `archive/`
2. Reference anything in `legacy/`
3. Reference BQML training plans
4. Reference AutoML approaches
5. Use old architecture plans

---

## 📋 **QUICK CHECKLIST**

Before referencing any file:
- [ ] Is it in `archive/`? → **IGNORE**
- [ ] Is it in `legacy/`? → **IGNORE**
- [ ] Is it in `docs/plans/archive/`? → **IGNORE**
- [ ] Does it mention BQML training? → **IGNORE**
- [ ] Does it mention AutoML? → **IGNORE**
- [ ] Is it in `scripts/deprecated/`? → **IGNORE**
- [ ] Is it dated before November 12, 2025? → **Check if legacy**

---

## 🎯 **KEY DIFFERENCES**

| Aspect | LEGACY | CURRENT |
|--------|--------|---------|
| **Training** | BQML, AutoML | Local M4 → Vertex AI |
| **Approach** | Cloud-first | Local-first |
| **Source of Truth** | 18+ old plans | MASTER_EXECUTION_PLAN.md |
| **Architecture** | Scattered | Unified pipeline |
| **Data** | 5 years (2020-2025) | 25 years (2000-2025) |

---

## 📁 **DIRECTORY MARKERS**

All legacy directories have `README.md` files with warnings:
- `archive/README.md` - ⚠️ LEGACY warning
- `legacy/README.md` - ⚠️ LEGACY warning
- `docs/plans/README.md` - Current vs Legacy guide

---

**Last Updated**: November 12, 2025  
**Status**: Active work - Local M4 → Vertex AI architecture

