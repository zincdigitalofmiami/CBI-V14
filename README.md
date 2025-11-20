---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14: Soybean Oil Forecasting Platform

**Last Updated**: November 14, 2025  
**Status**: ✅ Production-Ready Local Training Architecture  
**Version**: 2.0 (Local-First, November 2025)

---

## Overview

Institutional-grade soybean oil (ZL) price forecasting system using 25 years of historical data (2000-2025), regime-based training weights, and 100% local compute on Mac M4 with TensorFlow Metal.

**Core Architecture**:
- **Storage**: BigQuery (training data, predictions, monitoring)
- **Compute**: Mac M4 with TensorFlow Metal (100% local training + inference)
- **UI**: Next.js/Vercel dashboard (reads BigQuery)
- **NO Vertex AI**: Fully local control
- **NO BQML Training**: BigQuery for storage only

---

## Quick Start

### 1. Export Training Data

```bash
# Export all horizons for local training
python scripts/export_training_data.py --surface prod --horizon all

# Export specific horizon
python scripts/export_training_data.py --surface prod --horizon 1m
```

**Output**: `TrainingData/exports/zl_training_prod_allhistory_{horizon}.parquet`

### 2. Train Models Locally

```bash
# Train baseline tree models
python src/training/baselines/train_tree.py --horizon 1m --model all

# Train baseline neural models (LSTM, GRU)
python src/training/baselines/train_simple_neural.py --horizon 1m --model all

# Train statistical models (ARIMA, Prophet)
python src/training/baselines/train_statistical.py --horizon 1m --model all
```

**Output**: `Models/local/horizon_{h}/prod/baselines/{model}_v001/`

### 3. Generate Predictions Locally

```bash
# Generate all horizons
python src/prediction/generate_local_predictions.py --horizon all
```

**Output**: `predictions.parquet` in each model directory

### 4. Upload to BigQuery

```bash
# Upload all predictions to BigQuery
python scripts/upload_predictions.py
```

**Output**: `predictions.vw_zl_{horizon}_latest` views (dashboard-ready)

---

## Architecture

### Data Flow

```
┌──────────────────────────────────────────────────────────┐
│ BigQuery (Storage)                                        │
│ ├─ raw_intelligence.*        Raw data ingestion          │
│ ├─ features.*                Engineered features         │
│ ├─ training.zl_training_*    Training matrices           │
│ └─ predictions.*             Model outputs               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ 1. Export (scripts/export_training_data.py)
                     ↓
┌──────────────────────────────────────────────────────────┐
│ Mac M4 Local (100% Training + Inference)                 │
│ ├─ TrainingData/exports/     Parquet files               │
│ ├─ src/training/             Training scripts            │
│ ├─ src/prediction/           Inference scripts           │
│ └─ Models/local/             Trained models + metadata   │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ 2. Upload (scripts/upload_predictions.py)
                     ↓
┌──────────────────────────────────────────────────────────┐
│ BigQuery (Predictions)                                    │
│ └─ predictions.vw_zl_{h}_latest    Latest forecasts     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ 3. API Read
                     ↓
┌──────────────────────────────────────────────────────────┐
│ Vercel Dashboard (UI Only)                               │
│ └─ /api/forecast/{horizon}                               │
└──────────────────────────────────────────────────────────┘
```

**No cloud compute. No Vertex AI. No BQML training. 100% local control.**

---

## Datasets

### 8 Canonical Datasets

| Dataset | Purpose | Tables | Status |
|---------|---------|--------|--------|
| `raw_intelligence` | Raw data ingestion | 40+ | ✅ Active |
| `features` | Engineered features | Views | ✅ Active |
| `training` | Training matrices | 12 tables | ✅ Complete |
| `predictions` | Model outputs | Per-model | ✅ Active |
| `monitoring` | Performance tracking | 6 tables | ✅ Active |
| `vegas_intelligence` | Sales intel | 10 tables | ✅ Isolated |
| `archive` | Legacy snapshots | 10+ | ✅ Preserved |
| `yahoo_finance_comprehensive` | Historical data | Unchanged | ✅ Active |

### Training Tables (New Naming - November 2025)

**Production Surface** (~290-450 features):
- `training.zl_training_prod_allhistory_1w` (1,472 rows, 305 cols)
- `training.zl_training_prod_allhistory_1m` (1,404 rows, 449 cols)
- `training.zl_training_prod_allhistory_3m` (1,475 rows, 305 cols)
- `training.zl_training_prod_allhistory_6m` (1,473 rows, 305 cols)
- `training.zl_training_prod_allhistory_12m` (1,473 rows, 306 cols)

**Full Surface** (1,948+ features - to be rebuilt):
- `training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}`

**Regime Support**:
- `training.regime_calendar` (13,102 rows) - Maps dates to regimes
- `training.regime_weights` (11 rows) - Training weights (50-5000 scale)

---

## Naming Convention

**Pattern**: `{asset}_{function}_{scope}_{regime}_{horizon}`

**Components**:
- **asset**: `zl` (soybean oil), or cross-assets: `dxy`, `vix`, `spx`, `wti`, etc.
- **function**: `training`, `feat`, `commodity`, `fx`, `vol`, `rates`, `macro`, `policy`, `trade`, `news`, `social`, `weather`, `shipping`
- **scope**: `full` (1,948+ features) or `prod` (~290 features)
- **regime**: `allhistory`, `trump_2023_2025`, `tradewar_2017_2019`, etc.
- **horizon**: `1w`, `1m`, `3m`, `6m`, `12m`

**Examples**:
- `training.zl_training_prod_allhistory_1m`
- `raw_intelligence.commodity_soybean_oil_daily`
- `features.zl_feat_crossasset_daily`
- `predictions.vw_zl_1m_latest`

**Rules**:
- All lowercase, underscores only
- No "clean", "fixed", "final" in names
- Use views for "latest"

**Documentation**: `docs/plans/NAMING_CONVENTION_SPEC.md`

---

## Regime-Based Training

### 11 Market Regimes (1990-2025)

| Regime | Period | Weight | Purpose |
|--------|--------|--------|---------|
| trump_2023_2025 | 2023-2025 | 5000 | Current policy regime (max recency) |
| structural_events | Various | 2000 | Extreme event learning |
| tradewar_2017_2019 | 2017-2019 | 1500 | Policy similarity to current |
| inflation_2021_2023 | 2021-2023 | 1200 | Current macro dynamics |
| covid_2020_2021 | 2020-2021 | 800 | Supply chain disruption |
| financial_crisis_2008_2009 | 2008-2009 | 500 | Volatility spike learning |
| commodity_crash_2014_2016 | 2014-2016 | 400 | Crash dynamics |
| qe_supercycle_2010_2014 | 2010-2014 | 300 | Commodity boom patterns |
| precrisis_2000_2007 | 2000-2007 | 100 | Baseline patterns |
| historical_pre2000 | Pre-2000 | 50 | Pattern learning only |
| allhistory | All data | 1000 | Default baseline |

**Weight Scale**: 50-5000 (100x differential)  
**Effective Distribution**: Trump era ~40-50% influence despite <6% of rows  
**Research**: `scripts/migration/REGIME_WEIGHTS_RESEARCH.md`

---

## Features

### Production Surface (~290 Features)

**Price & Technical** (40 features):
- ZL price, returns, volatility
- RSI, MACD, Bollinger bands
- Volume patterns, liquidity metrics

**Cross-Asset** (60 features):
- Palm oil (FCPO), crude oil (WTI), natural gas
- VIX, S&P 500, USD index (DXY)
- Gold, silver, copper
- Corn, wheat, soybean, soybean meal
- Treasury yields (multiple tenors)

**Macro & Rates** (40 features):
- GDP, CPI, unemployment
- Fed funds rate, yield curve (10Y-2Y)
- Economic indicators
- 3M T-bill (risk-free rate)

**Policy & Trade** (30 features):
- Trump policy intelligence
- Biofuel mandates (B35, B40, RFS, 45Z)
- CFTC positioning (commercial, managed money)
- China import quotas, reserve actions
- USDA export sales

**Weather & Shipping** (40 features):
- Brazil, Argentina, U.S. Midwest weather
- GDD, soil moisture, precipitation
- Drought indices, ENSO status
- Baltic Dry Index, freight rates
- Logistics disruptions (Panama, Mississippi, Santos)

**News & Sentiment** (30 features):
- News sentiment scores (FinBERT)
- Social media sentiment
- China relations score
- Tariff threat indicators
- Breaking news events

**Seasonality** (25 features):
- Month, quarter, week of year
- Harvest season flags (US, Brazil, Argentina)
- Policy cycle indicators

**Correlations & Spreads** (25 features):
- Soy-palm ratio (substitution)
- Crush margins (ZS/ZM/ZL)
- Soy-crude correlation
- Cross-asset correlation matrices

**Total**: ~290 production features (exact count varies by horizon)

### Full Surface (1,948+ Features)

Includes all production features PLUS:
- Extended technical indicators (100+ variants)
- Additional cross-asset relationships
- Granular weather metrics
- Policy sub-components
- Advanced correlation structures
- Interaction terms
- Regime-specific features

**Status**: Tables created, to be rebuilt from `ULTIMATE_DATA_CONSOLIDATION.sql`

---

## Training Enhancements (November 2025)

### Regime-Based Weighting
- **Research-optimized weights**: 50-5000 scale
- **Recency bias**: Trump era 100x historical
- **Sample compensation**: Small but critical regimes amplified
- **Gradient impact**: Multiplicative scale affects optimization

### Data Quality Improvements
- **25 years integrated**: 2000-2025 (was ~3 years)
- **6,057 ZL rows**: 365% increase
- **338K+ pre-2020 rows**: Full market cycle coverage
- **Duplicate removal**: Zero duplicates in training tables
- **Null handling**: Complete validation pipeline

### Model Enhancements
- **Baselines**: ARIMA, Prophet, LightGBM, XGBoost, LSTM, GRU
- **Advanced**: Multi-layer LSTM/GRU, TCN, CNN-LSTM, Tiny Transformers
- **Regime-specific**: Crisis, trade war, inflation specialists
- **Ensemble**: Regime-aware meta-learner
- **Quantile**: Uncertainty quantification (planned)

### Hardware Optimization
- **Apple M4 Mac Mini**: 16GB unified memory
- **TensorFlow Metal**: GPU acceleration
- **FP16 mixed precision**: Memory efficiency
- **Sequential training**: Thermal management
- **External SSD**: Model + checkpoint storage

---

## Scripts & Tools

### Core Workflow
- `scripts/export_training_data.py` - Export from BigQuery
- `scripts/upload_predictions.py` - Upload to BigQuery
- `src/training/baselines/train_*.py` - Local model training
- `src/prediction/generate_local_predictions.py` - Local inference

### Migration (November 2025)
- `scripts/migration/archive_legacy_tables.py` - Archive-first safety
- `scripts/migration/03_create_new_training_tables.py` - New tables
- `scripts/migration/04_create_regime_tables.sql` - Regime setup
- `scripts/migration/05_create_shim_views.py` - Backward compatibility

### Monitoring
- `scripts/monitoring/` - Performance tracking
- `scripts/audits/` - Data quality validation

### Ingestion
- `src/ingestion/` - 93 ingestion scripts
- `scripts/scrapers/` - External data collection
- `scripts/backfill/` - Historical data backfill

---

## Documentation

### Start Here
- **`GPT5_READ_FIRST.md`** - Architecture overview (current vs legacy)
- **`CURRENT_WORK.md`** - Current status and active work
- **`INSTITUTIONAL_FRAMEWORK_COMPLETE.md`** - Framework summary

### Core Frameworks
- **`docs/reference/CONVICTION_VS_CONFIDENCE.md`** - Critical conceptual distinction
- **`docs/reference/SIGNAL_TREATMENT_RULES.md`** - 12 institutional guidelines
- **`docs/reference/CURSOR_MASTER_INSTRUCTION_SET.md`** - Audit protocol
- **`docs/reference/INSTITUTIONAL_FRAMEWORK_INDEX.md`** - Central index

### Planning & Execution
- **`docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`** - 7-day execution plan
- **`docs/plans/TABLE_MAPPING_MATRIX.md`** - Legacy→new mappings
- **`docs/plans/REGIME_BASED_TRAINING_STRATEGY.md`** - Regime methodology

### Migration
- **`docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md`** - Execution log
- **`scripts/migration/PHASE_1_3_COMPLETION_REPORT.md`** - Status report
- **`scripts/migration/REGIME_WEIGHTS_RESEARCH.md`** - Weight optimization

### Data Sources
- **`docs/data-sources/`** - Ingestion documentation
- **`DATASET_INVENTORY_COMPLETE.md`** - Full data catalog
- **`DATASET_QUICK_REFERENCE.md`** - Quick lookup

---

## Migration Status (November 2025)

### ✅ Completed Phases

**Phase 1: Archive** - 10 legacy tables archived to `archive.legacy_20251114__*`  
**Phase 2: Datasets** - All 7 datasets verified  
**Phase 3: Tables** - 12 training tables created with new naming  
**Phase 4: Scripts** - 15 Python scripts updated to new convention  
**Phase 6: Shim Views** - 5 backward compatibility views created

### Key Updates
- ✅ Naming convention: `{asset}_{function}_{scope}_{regime}_{horizon}`
- ✅ Regime weights: Research-optimized (50-5000 scale)
- ✅ Upload pipeline: Complete workflow
- ✅ Local-first: 100% Mac M4 training
- ✅ Documentation: Institutional framework complete

### Remaining Work
- ⏳ Phase 5: Update SQL consolidation files
- ⏳ Phase 7: Enhanced model metadata
- ⏳ Phase 8: Ingestion script updates

**Details**: `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md`

---

## Performance Benchmarks

### BQML Production Models (Reference)
| Horizon | MAPE | R² | Status |
|---------|------|-----|--------|
| 1 week | 0.7% | 0.96 | Live |
| 1 month | 1.0% | 0.95 | Live |
| 3 month | 1.1% | 0.95 | Live |
| 6 month | 1.2% | 0.94 | Live |
| 12 month | 1.3% | 0.93 | Live |

**Note**: BQML used for reference only. All new training is local.

### Local Training Targets
- Ensemble MAPE: <1.5% (realistic for M4 16GB)
- Regime detection: >95% accuracy
- Volatility forecast: <0.5% MAE
- SHAP coverage: >80% variance explained

---

## Environment Setup

### Requirements
- **Hardware**: Mac M4 (16GB+ RAM recommended)
- **Python**: 3.12.6 (conda environment: `vertex-metal-312`)
- **TensorFlow**: 2.15+ with tensorflow-metal
- **Storage**: External SSD recommended for models

### Installation

```bash
# Create environment
conda create -n vertex-metal-312 python=3.12.6
conda activate vertex-metal-312

# Install dependencies
pip install -r requirements_training.txt

# Verify Metal GPU
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

## Project Structure

```
CBI-V14/
├── config/                    Configuration files
│   ├── bigquery/             BigQuery SQL (205+ files)
│   └── system/               System config
├── dashboard-nextjs/         Vercel dashboard (UI)
├── docs/                     Documentation
│   ├── reference/            Core frameworks (NEW)
│   ├── plans/                Execution plans
│   ├── migrations/           Migration logs
│   └── audits/               System audits
├── scripts/                  Python scripts
│   ├── export_training_data.py        Export workflow
│   ├── upload_predictions.py          Upload workflow (NEW)
│   ├── migration/            Migration scripts
│   ├── audits/               Data quality
│   └── monitoring/           Performance tracking
├── src/                      Source code
│   ├── training/             Training scripts
│   │   ├── baselines/        Statistical, tree, simple neural
│   │   ├── advanced/         Multi-layer, TCN, attention
│   │   ├── ensemble/         Regime-aware ensemble
│   │   └── regime/           Regime classifier
│   ├── prediction/           Prediction generation
│   └── ingestion/            Data ingestion (93 scripts)
├── Models/local/             Trained models
│   └── horizon_{h}/{surface}/{family}/{model}_v{ver}/
│       ├── model.bin
│       ├── predictions.parquet
│       ├── columns_used.txt
│       ├── run_id.txt
│       └── feature_importance.csv
└── TrainingData/exports/     Exported Parquet files
```

---

## Key Features & Capabilities

### Institutional Quant Framework
- ✅ **Conviction vs Confidence**: Proper separation of directional certainty vs forecast precision
- ✅ **12 Signal Treatment Rules**: Professional methodology for market signals
- ✅ **Post-Move Audit Protocol**: Mandatory data validation after major moves
- ✅ **Regime-Based Training**: Research-optimized weighting (50-5000 scale)

### Data Pipeline
- ✅ **Archive-first**: All legacy tables preserved before changes
- ✅ **25-year history**: Soybean oil 2000-2025 (6,057 rows)
- ✅ **Zero duplicates**: Complete deduplication
- ✅ **Full provenance**: source, ingest_timestamp, provenance_uuid

### Model Training
- ✅ **Local-first**: 100% Mac M4, zero cloud dependency
- ✅ **Multi-family**: Statistical, tree-based, neural, ensemble
- ✅ **Regime-aware**: Specialized models per market regime
- ✅ **Hardware-optimized**: FP16, Metal GPU, sequential execution

### Monitoring
- ✅ **MAPE tracking**: Forecast accuracy by regime
- ✅ **Sharpe ratio**: Risk-adjusted returns
- ✅ **Feature drift**: Importance change detection
- ✅ **Correlation monitoring**: Breakdown alerts

---

## Dependencies

**Core**:
- pandas, numpy, polars
- scikit-learn
- lightgbm, xgboost
- tensorflow, tensorflow-metal (Apple Silicon)
- google-cloud-bigquery

**Statistical**:
- statsmodels (ARIMA)
- prophet

**Monitoring**:
- mlflow
- mapie (conformal prediction)

**Full list**: `requirements_training.txt`

---

## API Endpoints (Dashboard)

### Forecast APIs
- `GET /api/forecast/[horizon]` - Latest predictions
- `GET /api/predictions` - All horizons
- `GET /api/market/intelligence` - Real-time signals

### Monitoring APIs
- `GET /api/monitoring/performance` - MAPE tracking
- `GET /api/monitoring/sharpe` - Sharpe ratios
- `GET /api/regime/current` - Current regime

### Vegas Intel
- `GET /api/vegas/*` - Sales intelligence (isolated)

**Source**: Dashboard reads from BigQuery views only

---

## Legacy vs Current

### ❌ Legacy (Do NOT Use)
- `archive/` - All old attempts
- `legacy/` - Very old work
- `vertex-ai/` - **NO LONGER USED** (kept for reference)
- `models_v4.production_training_data_*` - Old naming (shim views only)
- Any BQML training references
- Any Vertex AI training references

### ✅ Current (Use These)
- `training.zl_training_*` - New naming convention
- `scripts/export_training_data.py` - Current export
- `scripts/upload_predictions.py` - Current upload
- `src/training/baselines/` - Current training scripts
- `docs/reference/` - Current frameworks

**Guide**: `GPT5_READ_FIRST.md`

---

## Contributing

### Before Making Changes

1. Read `GPT5_READ_FIRST.md` - Understand current vs legacy
2. Read `CURSOR_MASTER_INSTRUCTION_SET.md` - Follow audit protocol
3. Check `CURRENT_WORK.md` - See active work
4. Follow naming convention - No exceptions

### Adding Features

1. Add to `features.*` views (not new tables)
2. Update feature catalog
3. Rebuild training tables
4. Document in feature list

### Training New Models

1. Export data: `scripts/export_training_data.py`
2. Train locally: `src/training/baselines/train_*.py`
3. Generate predictions: `src/prediction/generate_local_predictions.py`
4. Upload: `scripts/upload_predictions.py`
5. Verify: Check `predictions.vw_zl_{h}_latest`

---

## License

Proprietary - Chris Musick / CBI

---

## Contact

**Project**: CBI-V14 Soybean Oil Forecasting  
**Owner**: Chris Musick  
**Developer**: Kirk Musick  
**Status**: Production-Ready (November 2025)

---

**Last Migration**: November 14, 2025 (Option 3 naming, local-first architecture)  
**Next Steps**: End-to-end testing, Phase 5 SQL updates
