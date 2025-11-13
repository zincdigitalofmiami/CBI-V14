# CBI-V14 Soybean Oil Forecasting Platform

**Institutional-grade commodity forecasting for U.S. Oil Solutions**  
**Last Updated**: November 13, 2025  
**Status**: ✅ Production (BQML) | 🚧 Rebuild Planning (340 tables)

---

## 🎯 WHAT THIS IS

A **dual-client forecasting platform** serving:

### **Client 1: Chris Stacy (Procurement)**
- **Need**: "Should I buy soybean oil (ZL) today or wait?"
- **Output**: BUY/WAIT/MONITOR signals + price targets
- **Horizons**: 1w, 1m, 3m, 6m, 12m forecasts
- **Models**: 5 BQML DART models (MAPE 0.7-1.3%, R² > 0.95)

### **Client 2: Kevin (Vegas Restaurant Sales)**
- **Need**: "Which casino restaurants need oil this week?"
- **Output**: Top 20 sales opportunities ranked by revenue
- **Data**: 151 restaurants, 408 fryers, event calendars, fryer economics

---

## ✅ PRODUCTION SYSTEM (WORKING)

### **BQML Models (Live, Serving Predictions)**
```
cbi-v14.models_v4.bqml_1w    (MAPE 0.7-1.3%, R² > 0.95)
cbi-v14.models_v4.bqml_1m    (MAPE 0.7-1.3%, R² > 0.95)
cbi-v14.models_v4.bqml_3m    (MAPE 0.7-1.3%, R² > 0.95)
cbi-v14.models_v4.bqml_6m    (MAPE 0.7-1.3%, R² > 0.95)
cbi-v14.models_v4.bqml_12m   (MAPE 0.7-1.3%, R² > 0.95)
```

### **Training Tables (290 Features, 25-Year History)**
```
cbi-v14.models_v4.production_training_data_1w   (6,057 rows, 2000-2025)
cbi-v14.models_v4.production_training_data_1m   (6,057 rows, 2000-2025)
cbi-v14.models_v4.production_training_data_3m   (6,057 rows, 2000-2025)
cbi-v14.models_v4.production_training_data_6m   (6,057 rows, 2000-2025)
cbi-v14.models_v4.production_training_data_12m  (6,057 rows, 2000-2025)
```

### **Dashboard (Live on Vercel)**
- Next.js app serving Chris & Kevin
- Real-time API routes pulling from BigQuery
- Vegas Intel page with fryer revenue calculations

### **Automated Ingestion (32 Cron Jobs)**
- Mac M4 external drive (always on)
- Daily: Weather, prices, volatility, RIN, Baltic, Argentina
- Every 4-6h: Social intel, Trump, GDELT
- Weekly: CFTC, USDA, EIA, EPA

---

## 🔥 THE PROBLEM (Why Rebuild Needed)

### **340 Tables Across 24 Datasets = CHAOS**

**Symptoms**:
- Same data in 3+ places with different column names
- 97 duplicate sentiment columns
- 20+ columns 100% NULL in production
- Empty datasets (`models_v5`, `performance`, `raw` - all 0 objects)
- Can't find data (which soybean oil table is right?)
- Sidebar explorer growing every day

**Impact**:
- Data hard to find
- Ingestion duplicates
- Schema drift
- **Every day makes it worse**

---

## 🎯 THE SURGICAL REBUILD PLAN

### **Goal**: Organize 340 tables into institutional structure

**NOT doing**:
- ❌ Reducing functionality
- ❌ Deleting datasets
- ❌ Breaking production models
- ❌ Starting from scratch

**ARE doing**:
- ✅ Archive old structure → `archive_legacy_nov12`
- ✅ Organize by asset class, function, regime (like Goldman Sachs)
- ✅ Deduplicate data (same data stored once)
- ✅ Standardize schemas (same column names)
- ✅ Create governance to prevent future chaos

### **Collaboration Model**
1. **GPT-5**: Strategic architecture (naming, structure, migration sequence)
2. **Claude**: Tactical execution (inventory, scripts, validation)
3. **Kirk**: Decision-maker (approve designs, green-light execution)

**Status**: Architecture design in progress

---

## 📁 REPOSITORY STRUCTURE

```
CBI-V14/
├── active-plans/              # Current execution plans
│   ├── MASTER_EXECUTION_PLAN.md           # 7-day training plan ⭐
│   ├── BASELINE_STRATEGY.md               # Mac M4 training strategy
│   ├── SURGICAL_REBUILD_*                 # Rebuild planning docs
│   └── [other execution plans]
│
├── config/
│   └── bigquery/bigquery-sql/
│       ├── PRODUCTION_HORIZON_SPECIFIC/   # 5 BQML training SQLs
│       ├── INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql
│       └── TRUMP_RICH_DART_V1.sql
│
├── dashboard-nextjs/          # Next.js dashboard (Vercel)
│
├── docs/
│   ├── audits/                # System audits (Nov 12 comprehensive)
│   ├── handoffs/              # Transition docs (60+ files)
│   ├── reference/             # System docs (features, flow, arch)
│   └── vegas-intel/           # Strategic intelligence
│
├── scripts/                   # 168 operational scripts
│   ├── export_training_data.py
│   ├── build_features.py
│   ├── data_quality_checks.py
│   └── [165 more]
│
├── src/
│   ├── ingestion/             # 78 data ingestion scripts
│   ├── training/
│   │   └── baselines/         # Statistical, tree, neural baselines
│   ├── prediction/            # Forecast generation + SHAP
│   └── analysis/              # Backtesting engine
│
├── vertex-ai/                 # Neural pipeline (Mac M4 + Vertex AI)
│   ├── training/
│   ├── deployment/
│   ├── data/
│   ├── evaluation/
│   └── prediction/
│
├── TrainingData/              # Local datasets
│   ├── exports/               # BigQuery Parquet exports
│   ├── processed/             # Engineered features
│   └── raw/                   # Raw downloads
│
├── Models/                    # Trained artifacts
│   ├── local/                 # Mac training outputs
│   ├── vertex-ai/             # SavedModels
│   ├── bqml/                  # BQML metadata
│   └── mlflow/                # Experiment tracking
│
├── archive/                   # Historical backups
│   ├── day1_complete_nov12_2025/
│   ├── audit_consolidation_nov1_2025/
│   └── [other dated archives]
│
├── README.md                  # This file ⭐
├── START_HERE.md              # Quick orientation
├── QUICK_REFERENCE.txt        # Command cheatsheet
└── STRUCTURE.md               # Full directory map
```

---

## 🚀 QUICK START

### **1. One-Time Setup (New Machine)**
```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
./setup_new_machine.sh
```
- Creates `vertex-metal-312` Python environment
- Installs TensorFlow Metal, MLX, Polars, DuckDB, MLflow
- Configures aliases: `cbi` → repo root

### **2. Daily Workflow**
```bash
cbi                                          # Navigate to repo
./scripts/status_check.sh                    # Check pipeline health
python3 scripts/export_training_data.py      # Export fresh data
python3 scripts/build_features.py --horizon=all  # Build features
```

### **3. Training (Mac M4 Local)**
```bash
# Statistical baselines
python3 src/training/baselines/train_statistical.py --horizon=1m

# Tree baselines
python3 src/training/baselines/train_tree.py --horizon=1m

# Neural baselines (TensorFlow Metal GPU)
python3 src/training/baselines/train_simple_neural.py --horizon=1m --model-type=lstm
```

### **4. BQML Training (Production)**
```bash
bq query --nouse_legacy_sql < config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/TRAIN_BQML_1M_PRODUCTION.sql
```

---

## 📊 DATA FOUNDATION

### **Historical Coverage (25 Years)**
- **Soybean Oil Prices**: 6,057 rows (2000-2025), +365% from 1,301
- **Economic Indicators**: 7,523 rows (1900-2026), 126 years
- **Yahoo Finance**: 314,381 rows, 233,060 pre-2020
- **12 Commodities**: Full 2000-2025 coverage

### **Regime Datasets (Created Nov 12)**
- **Pre-Crisis (2000-2007)**: 1,737 rows
- **2008 Financial Crisis**: 253 rows
- **Recovery (2010-2016)**: 1,760 rows
- **Trade War (2017-2019)**: 754 rows

### **290 Production Features**
See `docs/reference/COMPLETE_FEATURE_LIST_290.md` for full catalog.

**Key Feature Categories**:
- Price Data (10): ZL, corn, wheat, soybeans, oil, meal
- Big 8 Signals (9): VIX stress, harvest, China, tariffs, etc.
- Correlations (50+): ZL vs palm, crude, VIX, DXY, grains
- China Data (20): Imports, sentiment, policy, mentions
- Argentina/Brazil (30): Weather, exports, conditions
- Trump Intelligence (25): Policy events, mentions, sentiment
- CFTC Positioning (10): Commercial/managed positions
- Technical Indicators (30): RSI, MACD, Bollinger Bands
- Economic (15): GDP, CPI, Fed funds, yields
- Calendar Events (15): WASDE, FOMC, options expiry

---

## 📖 DOCUMENTATION

### **Start Here**
1. **README.md** (this file) - Project overview
2. **START_HERE.md** - 5-minute orientation
3. **QUICK_REFERENCE.txt** - Command cheatsheet
4. **active-plans/MASTER_EXECUTION_PLAN.md** - 7-day training plan ⭐

### **Key Reference Docs**
- `docs/reference/COMPLETE_FEATURE_LIST_290.md` - All 290 features
- `docs/reference/CHRIS_AND_KEVIN_NEEDS_COMPREHENSIVE.md` - Client requirements
- `docs/reference/COMPLETE_SYSTEM_FLOW.md` - Data flow architecture
- `docs/reference/PROPER_VERTEX_AI_ARCHITECTURE.md` - Vertex AI design

### **Audit Trail**
- `docs/audits/FORENSIC_BIGQUERY_AUDIT_20251112.md` - 340 tables inventory
- `docs/audits/COMPLETE_FORENSIC_AUDIT_20251112.md` - System-wide audit
- `docs/audits/AUDIT_EXECUTIVE_SUMMARY_20251112.md` - Summary

### **Integration Docs**
- `INTEGRATION_COMPLETE.md` - Yahoo Finance integration report
- `docs/handoffs/YAHOO_FINANCE_INTEGRATION_HANDOFF.md` - Integration details

---

## 🔧 KEY COMMANDS

| Task | Command |
|------|---------|
| **Health check** | `./scripts/status_check.sh` |
| **Validate data** | `python3 scripts/data_quality_checks.py` |
| **Export training data** | `python3 scripts/export_training_data.py` |
| **Build features** | `python3 scripts/build_features.py --horizon=all` |
| **Train statistical** | `python3 src/training/baselines/train_statistical.py --horizon=1m` |
| **Train tree models** | `python3 src/training/baselines/train_tree.py --horizon=1m` |
| **Train neural (GPU)** | `python3 src/training/baselines/train_simple_neural.py --horizon=1m --model-type=lstm` |
| **Generate forecasts** | `python3 src/prediction/generate_forecasts.py --horizon=all` |
| **SHAP explanations** | `python3 src/prediction/shap_explanations.py --horizon=1m` |
| **Backtest strategies** | `python3 src/analysis/backtesting_engine.py --start-date=2024-01-01` |
| **Train BQML** | `bq query --nouse_legacy_sql < config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/TRAIN_BQML_1M_PRODUCTION.sql` |

---

## 🎓 IMPORTANT NOTES

### **DO NOT**
- ❌ Rename BQML models (breaks production dashboard)
- ❌ Use `training_dataset_super_enriched` (legacy, 11 columns, broken)
- ❌ Modify production tables without approval
- ❌ Delete any archive folders

### **ALWAYS**
- ✅ Check `QUICK_REFERENCE.txt` for latest commands
- ✅ Run `scripts/status_check.sh` before major changes
- ✅ Export fresh data before training
- ✅ Document any schema changes

---

## 📞 SUPPORT

- **Repository**: `/Volumes/Satechi Hub/Projects/CBI-V14/`
- **Symlink**: `~/Documents/GitHub/CBI-V14`
- **Alias**: `cbi` (in ~/.zshrc)
- **Environment**: `vertex-metal-312` (Python 3.12.6)

---

## 🚀 CURRENT STATUS (November 13, 2025)

| Component | Status | Notes |
|-----------|--------|-------|
| **BQML Production** | ✅ Active | 5 models live, serving predictions |
| **Historical Data** | ✅ Integrated | 25 years (2000-2025), +365% training data |
| **Training Pipeline** | ✅ Complete | Statistical, tree, neural baselines ready |
| **Dashboard** | ✅ Live | Vercel deployment, serving Chris & Kevin |
| **Cron Automation** | ✅ Active | 32 jobs ingesting daily |
| **Surgical Rebuild** | 🚧 Planning | Architecture design with GPT-5 |
| **Mac M4 Training** | 🚧 Ready | Environment configured, awaiting execution |
| **Vertex AI** | 🚧 Ready | Can train on 25-year history |

---

**Next Steps**: Surgical rebuild planning → Archive 340 tables → Rebuild clean structure → Resume training

---

*For detailed execution plans, see `active-plans/MASTER_EXECUTION_PLAN.md`*
