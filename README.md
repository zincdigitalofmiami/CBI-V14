# CBI-V14 - CURRENT STATE

**Last Updated**: November 12, 2025  
**Status**: Active Development - Local M4 → Vertex AI Architecture

---

## 🚨 **FOR GPT-5 / FUTURE AI: READ FIRST**

**⚠️ CRITICAL**: This repository contains both CURRENT and LEGACY work.

**READ THESE FIRST:**
1. `GPT5_READ_FIRST.md` - **START HERE** - Current vs Legacy guide
2. `CURRENT_WORK.md` - Current active work summary
3. `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Source of truth

**IGNORE:**
- Everything in `archive/` - Legacy work
- Everything in `legacy/` - Legacy work
- BQML training plans - We use Vertex AI now

---

## 🎯 **CURRENT ARCHITECTURE** (Active)

---

### **Training Strategy**
- **Local M4 Mac** training (TensorFlow Metal GPU)
- **Vertex AI** deployment (for online predictions)
- **BQML production** (5 horizons: 1w, 1m, 3m, 6m, 12m)

### **Current Status**
- ✅ Historical data backfilled (2000-2025, 6,057 rows)
- ✅ Export scripts ready (16 Parquet files)
- ✅ Baseline training scripts ready (Day 2)
- ✅ Vertex AI deployment pipeline ready
- ⚠️ Production tables need rebuild (2000-2025 range)
- ⚠️ Day 1 execution pending (manual steps)

---

## 📁 **REPOSITORY STRUCTURE**

### **CURRENT WORK** (Use These)
```
CBI-V14/
├── docs/plans/
│   ├── TRAINING_MASTER_EXECUTION_PLAN.md  # ⭐ SOURCE OF TRUTH
│   ├── BASELINE_STRATEGY.md               # Current baseline approach
│   └── PHASE_1_PRODUCTION_GAPS.md         # Current gaps
├── scripts/
│   ├── data_quality_checks.py            # Day 1 validation
│   ├── export_training_data.py            # Data export
│   └── audit_training_data_complete.py     # Data audit
├── src/training/
│   └── baselines/                         # Day 2 baseline training
├── vertex-ai/deployment/                  # Deployment pipeline
└── TrainingData/                          # Training data (external drive)
```

### **LEGACY WORK** (Do NOT Use)
```
CBI-V14/
├── archive/              # ⚠️ LEGACY - Old attempts
├── legacy/               # ⚠️ LEGACY - Very old work
├── docs/plans/archive/   # ⚠️ LEGACY - Old plans
└── scripts/deprecated/   # ⚠️ LEGACY - Deprecated scripts
```

---

## 📋 **QUICK REFERENCE**

### **Current Plans**
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - 7-day institutional system
- `docs/plans/BASELINE_STRATEGY.md` - Baseline training approach

### **Current Scripts**
- `scripts/data_quality_checks.py` - Day 1 validation
- `scripts/export_training_data.py` - Data export (16 files)
- `src/training/baselines/*.py` - Baseline training

### **Current Data**
- `models_v4.production_training_data_*` - 5 horizons (needs rebuild)
- `forecasting_data_warehouse.soybean_oil_prices` - 6,057 rows (2000-2025) ✅

---

## 🎯 **KEY DIFFERENCES: LEGACY vs CURRENT**

| Aspect | LEGACY | CURRENT |
|--------|--------|---------|
| **Training** | BQML, AutoML | Local M4 → Vertex AI |
| **Approach** | Cloud-first | Local-first |
| **Plans** | 18+ old plans | MASTER_EXECUTION_PLAN.md |
| **Architecture** | Scattered | Unified pipeline |

---

## 📚 **DOCUMENTATION**

- `GPT5_READ_FIRST.md` - **START HERE** for future AI
- `CURRENT_WORK.md` - Current active work
- `README_CURRENT.md` - Current state overview
- `TRAINING_DATA_AUDIT_SUMMARY.md` - Data audit results

---

**Last Updated**: November 12, 2025  
**Architecture**: Local M4 → Vertex AI (NOT BQML)
