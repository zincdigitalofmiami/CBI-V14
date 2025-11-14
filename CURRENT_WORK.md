# CURRENT WORK - ACTIVE AS OF NOVEMBER 12, 2025
**⚠️ THIS IS THE ONLY ACTIVE WORK - ALL ELSE IS LEGACY**

---

## ✅ **CURRENT ARCHITECTURE** (Active)

### **Training Strategy**
- **Local M4 Mac training** (TensorFlow Metal GPU)
- **Vertex AI deployment** (for online predictions)
- **BQML production** (5 horizons, live predictions)

### **Current Plans** (Active)
- `active-plans/MASTER_EXECUTION_PLAN.md` - 7-day institutional system build
- `active-plans/HARDWARE_OPTIMIZED_TRAINING_GUIDE.md` - M4 16GB training specs
- `active-plans/BASELINE_STRATEGY.md` - Baseline training approach

### **Current Scripts** (Active)
- `scripts/data_quality_checks.py` - Day 1 validation
- `scripts/export_training_data.py` - BigQuery → Parquet export
- `scripts/audit_training_data_complete.py` - Data audit
- `src/training/baselines/*.py` - Day 2 baseline training
- `src/training/config_mlflow.py` - MLflow setup
- `EXECUTE_DAY_1.sh` - Day 1 execution

### **Current Deployment** (Active)
- `vertex-ai/deployment/train_local_deploy_vertex.py` - Local → Vertex pipeline
- `vertex-ai/deployment/export_savedmodel.py` - SavedModel export
- `vertex-ai/deployment/upload_to_vertex.py` - Vertex upload
- `vertex-ai/deployment/create_endpoint.py` - Endpoint deployment

### **Current Data** (Active)
- `models_v4.production_training_data_*` - 5 horizons (1w, 1m, 3m, 6m, 12m)
- `forecasting_data_warehouse.soybean_oil_prices` - 6,057 rows (2000-2025)
- Historical regime tables (4 tables, 4,504 rows)

---

## ❌ **LEGACY WORK** (DO NOT USE)

### **Legacy Training Approaches**
- ❌ **BQML training** - Replaced by local M4 + Vertex AI
- ❌ **AutoML** - Replaced by custom neural models
- ❌ **Old baseline strategies** - Replaced by new baseline plan

### **Legacy Plans** (Archived)
- All plans in `docs/plans/` - OLD, replaced by active-plans/
- All plans in `legacy/old-plans/` - OLD
- BQML-specific plans in `legacy/bqml-work/` - OLD

### **Legacy Scripts** (Archived)
- `archive/oct31_2025_cleanup/scripts_legacy/` - OLD scripts
- `archive/legacy_scripts/` - OLD scripts
- `scripts/deprecated/` - Deprecated scripts

### **Legacy Architecture**
- ❌ **18+ old architecture plans** - All replaced by MASTER_EXECUTION_PLAN.md
- ❌ **Old dashboard** - Broken, being rebuilt
- ❌ **Old ingestion patterns** - Replaced by src/ingestion/

---

## 📋 **CURRENT STATUS** (November 12, 2025)

### **What's Working**
- ✅ Historical data backfilled (2000-2025)
- ✅ Export scripts ready (16 Parquet files)
- ✅ Baseline training scripts ready (Day 2)
- ✅ Vertex AI deployment pipeline ready
- ✅ MLflow tracking configured

### **What Needs Work**
- ⚠️ Production tables need rebuild (2000-2025 range)
- ⚠️ Day 1 execution pending (manual steps)
- ⚠️ Day 2 baselines not yet trained

---

## 🎯 **FOR GPT-5: READ THIS FIRST**

**CURRENT WORK ONLY:**
- Use `active-plans/MASTER_EXECUTION_PLAN.md` as source of truth
- Use `scripts/` and `src/training/` for current scripts
- Use `vertex-ai/deployment/` for deployment pipeline
- Use `models_v4.production_training_data_*` for training data

**IGNORE:**
- Everything in `archive/` - Legacy work
- Everything in `docs/plans/` - Old plans
- Everything in `legacy/` - Legacy work
- BQML training plans - We use Vertex AI now
- Old architecture plans - Replaced by MASTER_EXECUTION_PLAN.md

**KEY DIFFERENCE:**
- **OLD**: BQML training, AutoML, cloud-first
- **NEW**: Local M4 training, Vertex AI deployment, local-first

---

**Last Updated**: November 12, 2025  
**Status**: Active work in progress

