# START HERE - CBI-V14 Quick Orientation

**Last Updated**: November 13, 2025  
**Read Time**: 3 minutes  

---

## ⚡ WHAT IS THIS?

**CBI-V14** is a soybean oil (ZL) forecasting platform for U.S. Oil Solutions that:
- Predicts ZL prices across 5 horizons (1w to 12m)
- Powers BUY/WAIT/MONITOR procurement signals for Chris Stacy
- Identifies sales opportunities for Kevin's Vegas restaurant clients
- Uses 25 years of historical data (2000-2025) with 290 features

---

## 🎯 IF YOU'RE NEW, READ THESE IN ORDER

### **1. This File** (you're here) - 3 minutes
Quick orientation to the project

### **2. README.md** - 5 minutes
Full project overview, structure, commands

### **3. QUICK_REFERENCE.txt** - 2 minutes
Command cheatsheet for daily operations

### **4. active-plans/MASTER_EXECUTION_PLAN.md** - 10 minutes
7-day training strategy and execution plan

---

## ✅ PRODUCTION STATUS

### **What's Working**
- ✅ **5 BQML models** (MAPE 0.7-1.3%, R² > 0.95) serving live predictions
- ✅ **290-feature training tables** with 6,057 rows (2000-2025)
- ✅ **Next.js dashboard** live on Vercel
- ✅ **32 cron jobs** ingesting data daily
- ✅ **25 years of historical data** integrated (Nov 12)

### **What's In Progress**
- 🚧 **Surgical rebuild** - Organizing 340 tables into clean structure
- 🚧 **Mac M4 training** - Local baselines with TensorFlow Metal
- 🚧 **Vertex AI** - Neural models on 25-year history

---

## 🗂️ FOLDER GUIDE

```
Key Folders to Know:

active-plans/          ← Current execution plans (START HERE)
  ├── MASTER_EXECUTION_PLAN.md    (7-day training strategy)
  ├── BASELINE_STRATEGY.md        (Mac M4 training)
  └── SURGICAL_REBUILD_*          (Rebuild planning)

scripts/               ← Operational utilities (168 scripts)
  ├── export_training_data.py     (Export from BigQuery)
  ├── build_features.py           (Feature engineering)
  └── data_quality_checks.py      (Validation)

src/
  ├── training/baselines/         ← Day 2 training scripts
  ├── prediction/                 ← Forecast generation + SHAP
  └── ingestion/                  ← 78 data ingestion scripts

config/bigquery/bigquery-sql/
  ├── PRODUCTION_HORIZON_SPECIFIC/ ← 5 BQML training SQLs
  └── INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql

docs/
  ├── reference/         ← System docs (features, architecture)
  ├── audits/            ← Nov 12 comprehensive audits
  └── handoffs/          ← Transition documentation

vertex-ai/             ← Neural training pipeline
dashboard-nextjs/      ← Live dashboard (Vercel)
```

---

## 🚀 FIRST COMMANDS TO RUN

```bash
# Navigate to repo (external drive)
cd "/Volumes/Satechi Hub/Projects/CBI-V14"

# Or use the alias (if configured)
cbi

# Check system health
./scripts/status_check.sh

# Validate data quality
python3 scripts/data_quality_checks.py

# Export fresh training data
python3 scripts/export_training_data.py
```

---

## 🎓 KEY CONCEPTS

### **The Two Tracks**

**Track 1: BQML Production (Live)**
- 5 DART models trained in BigQuery
- MAPE 0.7-1.3%, R² > 0.95
- Serving predictions to dashboard
- Cost: ~$0.12 per training run

**Track 2: Neural Pipeline (In Progress)**
- Mac M4 local training + Vertex AI deployment
- Statistical, tree, and neural baselines
- 60-70 models trained sequentially
- Memory-optimized for 16GB RAM

### **The 340-Table Problem**

**Why rebuild?**
- 340 tables across 24 datasets = chaos
- Same data in multiple places with different names
- 97 duplicate sentiment columns
- 20+ columns 100% NULL in production
- **Gets worse every day**

**Solution:**
- Archive old structure → `archive_legacy_nov12`
- Rebuild with institutional naming (like Goldman Sachs)
- Organize by asset class, function, regime
- Create governance to prevent future chaos

---

## 📚 DOCUMENTATION PRIORITY

**Must Read** (15 minutes total):
1. ⭐ `active-plans/MASTER_EXECUTION_PLAN.md` - Current strategy
2. ⭐ `QUICK_REFERENCE.txt` - Command cheatsheet
3. ⭐ `README.md` - Full overview

**Reference As Needed**:
- `docs/reference/COMPLETE_FEATURE_LIST_290.md` - All features
- `docs/reference/COMPLETE_SYSTEM_FLOW.md` - Data architecture
- `docs/audits/FORENSIC_BIGQUERY_AUDIT_20251112.md` - 340 tables inventory

**Client Requirements**:
- `docs/reference/CHRIS_AND_KEVIN_NEEDS_COMPREHENSIVE.md`

---

## 🔥 MOST IMPORTANT FACTS

### **Data Reality**
- **6,057 rows** of soybean oil prices (2000-2025)
- **+365% increase** from 1,301 rows (Nov 12 integration)
- **290 features** in production training tables
- **4 regime datasets** for crisis-specific training

### **Production Models**
```
bqml_1w   (1-week forecasts)   MAPE 0.7-1.3%, R² > 0.95
bqml_1m   (1-month forecasts)  MAPE 0.7-1.3%, R² > 0.95
bqml_3m   (3-month forecasts)  MAPE 0.7-1.3%, R² > 0.95
bqml_6m   (6-month forecasts)  MAPE 0.7-1.3%, R² > 0.95
bqml_12m  (12-month forecasts) MAPE 0.7-1.3%, R² > 0.95
```

### **Critical DON'Ts**
- ❌ DON'T rename BQML models (breaks production)
- ❌ DON'T use `training_dataset_super_enriched` (legacy, broken)
- ❌ DON'T modify production tables without approval

---

## 🎯 WHAT TO DO NEXT

### **If You're Starting Training:**
1. Read `active-plans/MASTER_EXECUTION_PLAN.md`
2. Run `scripts/export_training_data.py`
3. Follow Day 2 baseline scripts in `src/training/baselines/`

### **If You're Debugging:**
1. Run `scripts/status_check.sh`
2. Check recent audits in `docs/audits/`
3. Review logs in `Logs/`

### **If You're Planning:**
1. Review `active-plans/` folder
2. Check surgical rebuild docs
3. Read client requirements in `docs/reference/`

---

## 📞 QUICK HELP

**Repository Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/`  
**Symlink**: `~/Documents/GitHub/CBI-V14`  
**Alias**: `cbi` (in ~/.zshrc)  
**Python Env**: `vertex-metal-312` (Python 3.12.6)

**Key Files**:
- Master plan: `active-plans/MASTER_EXECUTION_PLAN.md`
- Commands: `QUICK_REFERENCE.txt`
- Full overview: `README.md`

---

## ✅ YOU'RE READY!

You now know:
- ✅ What CBI-V14 is (soybean oil forecasting)
- ✅ What's working (5 BQML models live)
- ✅ What's in progress (surgical rebuild, Mac training)
- ✅ Where to find things (folder structure)
- ✅ What to read next (MASTER_EXECUTION_PLAN.md)

**Next step**: Open `README.md` for full details, then dive into `active-plans/MASTER_EXECUTION_PLAN.md`

---

🚀 **Welcome to CBI-V14!**
