# CBI-V14 - CURRENT STATE (November 12, 2025)
**⚠️ THIS IS THE CURRENT WORK - ALL ELSE IS LEGACY**

---

## 🎯 **CURRENT ARCHITECTURE**

### **Training Strategy** (ACTIVE)
- **Local M4 Mac training** with TensorFlow Metal GPU
- **Vertex AI deployment** for online predictions
- **BQML production** (5 horizons: 1w, 1m, 3m, 6m, 12m)

### **Key Difference from Legacy**
- **LEGACY**: BQML training, AutoML, cloud-first approach
- **CURRENT**: Local M4 training → Vertex AI deployment, local-first approach

---

## 📁 **CURRENT FILES** (Use These)

### **Current Plans**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - 7-day institutional system
- `docs/plans/BASELINE_STRATEGY.md` - Baseline training approach
- `docs/plans/PHASE_1_PRODUCTION_GAPS.md` - Production gaps to fix

### **Current Scripts**
- `scripts/data_quality_checks.py` - Day 1 validation
- `scripts/export_training_data.py` - BigQuery → Parquet (16 files)
- `scripts/audit_training_data_complete.py` - Complete data audit
- `src/training/baselines/*.py` - Day 2 baseline training
- `src/training/config_mlflow.py` - MLflow setup
- `EXECUTE_DAY_1.sh` - Day 1 execution script

### **Current Deployment**
- `vertex-ai/deployment/train_local_deploy_vertex.py` - Local → Vertex pipeline
- `vertex-ai/deployment/export_savedmodel.py` - SavedModel export
- `vertex-ai/deployment/upload_to_vertex.py` - Vertex upload
- `vertex-ai/deployment/create_endpoint.py` - Endpoint deployment

### **Current Data**
- `models_v4.production_training_data_*` - 5 horizons (needs rebuild for 2000-2025)
- `forecasting_data_warehouse.soybean_oil_prices` - 6,057 rows (2000-2025) ✅
- Historical regime tables (4 tables, 4,504 rows) ✅

---

## ❌ **LEGACY FILES** (Do NOT Use)

### **Legacy Plans** (Archived)
- `docs/plans/archive/` - All old plans (30+ files)
- `legacy/old-plans/` - Very old plans
- `legacy/bqml-work/` - BQML training plans (replaced by Vertex AI)

### **Legacy Scripts** (Archived)
- `archive/oct31_2025_cleanup/scripts_legacy/` - Old scripts
- `archive/legacy_scripts/` - Very old scripts
- `scripts/deprecated/` - Deprecated scripts

### **Legacy Architecture**
- `archive/` - All old attempts
- `docs/handoffs/` (pre-November 12, 2025) - Old handoffs
- All BQML training references - We use Vertex AI now

---

## 🚨 **FOR GPT-5 / FUTURE AI**

### **READ FIRST:**
1. `CURRENT_WORK.md` - Current active work
2. `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Source of truth
3. `TRAINING_DATA_AUDIT_SUMMARY.md` - Current data state

### **IGNORE:**
- Everything in `archive/` - Legacy work
- Everything in `docs/plans/archive/` - Old plans
- Everything in `legacy/` - Legacy work
- BQML training plans - We use Vertex AI now
- Old README.md - Outdated, use this file instead

### **KEY MARKERS:**
- Files with `LEGACY` in name or path = OLD
- Files in `archive/` = OLD
- Files in `legacy/` = OLD
- Files in `docs/plans/archive/` = OLD
- Files dated before November 12, 2025 in handoffs = OLD

---

## 📊 **CURRENT STATUS**

### **What's Ready**
- ✅ Historical data backfilled (2000-2025)
- ✅ Export scripts ready (16 Parquet files)
- ✅ Baseline training scripts ready
- ✅ Vertex AI deployment pipeline ready
- ✅ MLflow tracking configured

### **What Needs Work**
- ⚠️ Production tables need rebuild (2000-2025 range)
- ⚠️ Day 1 execution pending (manual steps)
- ⚠️ Day 2 baselines not yet trained

---

**Last Updated**: November 12, 2025  
**Status**: Active work in progress  
**Architecture**: Local M4 → Vertex AI (NOT BQML)

