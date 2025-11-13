# CBI-V14 Commodity Forecasting Platform

## Overview
CBI-V14 delivers institutional-grade soybean oil (ZL) forecasting for Chris Stacy (US Oil Solutions) with two complementary production paths:

1. **Production BQML DART models** (1w, 1m, 3m, 6m, 12m horizons) that power the current BUY / WAIT / MONITOR signals.
2. **Next-generation Vertex AI & local neural pipeline** trained on the Apple M4 Mac mini (tensorflow-metal) and deployed as custom SavedModels to Vertex AI.

Both paths rely on an expanded data warehouse with **25+ years of historical data** (2000-2025), featuring **365% more training data** after the Yahoo Finance integration, comprehensive feature catalog, and extensive documentation on the external Satechi Hub drive.

## Current Status (November 12, 2025)
| Component | Status | Notes |
|-----------|--------|-------|
| **BQML Production** | ✅ Active | MAPE 0.7–1.3%, R² > 0.95, 5 horizons (1w, 1m, 3m, 6m, 12m) |
| **Historical Data** | ✅ INTEGRATED | 25+ years (2000-2025), 338K+ pre-2020 rows, 4 regime datasets |
| **Training Data** | ✅ EXPANDED | Soybean oil: 6,057 rows (was 1,301), +365% improvement |
| **Baseline Training Scripts** | ✅ COMPLETE | Day 2 scripts ready: statistical, tree, neural (M4 Metal GPU optimized) |
| **Feature Engineering** | ✅ COMPLETE | Automated pipeline: `scripts/build_features.py` |
| **Prediction Pipeline** | ✅ COMPLETE | Daily forecasts + SHAP explainability scripts |
| **Backtesting Engine** | ✅ COMPLETE | Procurement strategy validation: `src/analysis/backtesting_engine.py` |
| **Cron Automation** | ✅ UPDATED | ML pipeline jobs scheduled (3:30 AM features, 4 AM training, 5 AM predictions) |
| **Mac Neural Pipeline** | 🚧 In progress | Environment verified (`vertex-metal-312`), ready for expanded dataset |
| **Vertex AI AutoML** | ✅ Ready to relaunch | Can now train on 25-year historical patterns |
| **Dashboard** | 🔄 Next.js app | Lives in `dashboard-nextjs/` (aligned with docs/vegas-intel) |

## Getting Started
1. **Hardware & External Drive**  
   Plug in the Satechi Hub and confirm it mounts at `/Volumes/Satechi Hub`.

2. **One-time machine setup**  
   ```bash
   cd "/Volumes/Satechi Hub/Projects/CBI-V14"
   ./setup_new_machine.sh
   ```
   - Creates `vertex-metal-312` (Python 3.12.6) with tensorflow-metal 2.16.2
   - Installs MLX, Polars, DuckDB, MLflow, GS Quant tooling, etc.
   - Configures aliases: `cbi` → repo root, `cbdata` → training data

3. **Daily workflow**  
   ```bash
   cbi
   ./scripts/status_check.sh            # review pipeline health
   ./scripts/run_ultimate_consolidation.sh   # refresh training tables
   ```

4. **Docs & plans**  
   - `START_HERE.md` → 5-minute orientation (this file is in the repo root)
   - `active-plans/` → current execution (Vertex AI, Trump-era, Mac training)
   - `docs/` → detailed handoffs, audits, reference material

## Data Resources (November 12, 2025)

### Historical Data (25+ Years Available)
| Dataset | Rows | Date Range | Pre-2020 Coverage |
|---------|------|------------|-------------------|
| **Yahoo Finance Normalized** | 314,381 | 2000-2025 | 233,060 rows (74%) |
| **Soybean Oil Prices** | 6,057 | 2000-2025 | 4,756 rows (78%) |
| **Economic Indicators** | 7,523 | 1900-2026 | 126 years available |
| **All Symbols 20yr** | 57,397 | 2000-2025 | 44,147 rows (77%) |
| **Biofuel Components** | 42,367 | 2000-2025 | 30,595 rows (72%) |

### Regime-Specific Datasets (Created Nov 12)
- **Pre-Crisis (2000-2007)**: 1,737 rows
- **2008 Financial Crisis**: 253 rows
- **Recovery (2010-2016)**: 1,760 rows
- **Trade War (2017-2019)**: 754 rows

## Repository Layout
```
CBI-V14/
├── active-plans/                    # Current working plans
├── archive/                         # Historical work & backups
├── config/
│   ├── bigquery/bigquery-sql/       # Production SQL (BQML + features)
│   │   ├── PRODUCTION_HORIZON_SPECIFIC/  # 5 horizon training SQLs
│   │   └── INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql  # Historical integration
│   └── terraform/                   # Infrastructure as code
├── dashboard-nextjs/                # Decision hub frontend
├── data/                            # Local scratch data (small)
├── docs/                            # Documentation library
│   ├── audits/                      # Integration & system audits
│   ├── handoffs/                    # Transition documentation
│   └── vegas-intel/                 # Strategic intelligence
├── legacy/                          # BQML-era & deprecated assets
├── Logs/                            # Runtime logs (training/ingestion/deployment)
├── Models/                          # Saved models (local/vertex-ai/bqml)
├── scripts/                         # Operational utilities (148+ scripts)
├── src/                             # Application source
│   ├── ingestion/                   # 78 data ingestion scripts
│   ├── training/                    # Model training pipelines
│   │   └── baselines/               # Day 2 baseline scripts (statistical, tree, neural)
│   ├── prediction/                  # Inference engines (forecasts, SHAP)
│   └── analysis/                    # Backtesting and strategy validation
├── TrainingData/                    # Raw/processed/export datasets
├── vertex-ai/                       # Neural pipeline deployment
└── README.md, START_HERE.md, QUICK_REFERENCE.txt
```
See `STRUCTURE.md` for the authoritative directory map.

## Key Workflows
### 1. Production BQML (Trump-era DART)
- SQL lives in `config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/`
- End-to-end instructions: `active-plans/TRUMP_ERA_EXECUTION_PLAN.md`
- Quick commands:
  ```bash
  cd "${CBI_V14_REPO:-/Volumes/Satechi Hub/Projects/CBI-V14}"
  bq query --nouse_legacy_sql < config/bigquery/bigquery-sql/TRUMP_RICH_DART_V1.sql
  ```

### 2. Vertex AI Custom Models + Local Training
- Plan & naming conventions: `active-plans/VERTEX_AI_TRUMP_ERA_PLAN.md`
- TensorFlow / Mac setup: `active-plans/MAC_TRAINING_SETUP_PLAN.md`
- Local orchestration: `vertex-ai/deployment/train_local_deploy_vertex.py`
- Deploy components:
  - `vertex-ai/deployment/export_savedmodel.py`
  - `vertex-ai/deployment/upload_to_vertex.py`
  - `vertex-ai/deployment/create_endpoint.py`

### 3. Data Ingestion & Intelligence
- Source scripts: `src/ingestion/`
- Priority automation: `scripts/run_ultimate_consolidation.sh`, `scripts/status_check.sh`
- BigQuery exports land in `TrainingData/exports/`

## Operational Shortcuts
| Task | Command |
|------|---------|
| Health check | `./scripts/status_check.sh` |
| Validate data quality | `python scripts/data_quality_checks.py` |
| Export training data | `python scripts/export_training_data.py` |
| Build features | `python scripts/build_features.py --horizon=all` |
| Train statistical baselines | `python src/training/baselines/train_statistical.py --horizon=1m` |
| Train tree baselines | `python src/training/baselines/train_tree.py --horizon=1m` |
| Train neural baselines | `python src/training/baselines/train_simple_neural.py --horizon=1m --model-type=lstm` |
| Generate forecasts | `python src/prediction/generate_forecasts.py --horizon=all` |
| Generate SHAP explanations | `python src/prediction/shap_explanations.py --horizon=1m` |
| Run backtesting | `python src/analysis/backtesting_engine.py --start-date=2024-01-01 --end-date=2024-12-31` |
| Audit Yahoo Finance data | `python scripts/audit_yahoo_finance_comprehensive.py` |
| Check historical sources | `python scripts/check_historical_sources.py` |
| Run priority scrapers | `python src/ingestion/ingest_epa_rin_prices.py` (etc.) |
| Train BQML (1w horizon) | `bq query --nouse_legacy_sql < config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/TRAIN_BQML_1W_PRODUCTION.sql` |
| Train & deploy Vertex AI | `python vertex-ai/deployment/train_local_deploy_vertex.py --horizon=1m` |

## Documentation Map
| Need | Where to look |
|------|---------------|
| Master strategy & execution | `active-plans/MASTER_EXECUTION_PLAN.md` ⭐
| Baseline training strategy | `active-plans/BASELINE_STRATEGY.md`
| 5-minute orientation | `START_HERE.md`
| Quick reference / commands | `QUICK_REFERENCE.txt`
| Detailed handover | `docs/handoffs/COMPREHENSIVE_HANDOVER_DOCUMENT_NOV6.md`
| Full audit trail | `docs/audits/COMPREHENSIVE_AUDIT_NOV6.md`
| Vegas intel & dashboard notes | `docs/vegas-intel/`
| Legacy BQML work | `legacy/bqml-work/`
| Historical Data Integration | `docs/handoffs/YAHOO_FINANCE_INTEGRATION_HANDOFF.md`

## Next Steps (Post-Integration)

### Immediate Priorities
1. **Rebuild production training tables** with 25-year historical data
2. **Train regime-specific models** using new crisis/recovery datasets  
3. **Export expanded datasets** for local Mac training pipeline
4. **Update Vertex AI pipelines** to leverage 365% more data

### This Week
- [ ] Rebuild all `production_training_data_*` tables (5 horizons)
- [ ] Test model performance on historical regimes
- [ ] Validate walk-forward accuracy on 2008 crisis data
- [ ] Create automated historical data refresh jobs

### Strategic Initiatives
- Implement regime-aware ensemble models
- Build crisis detection early-warning system
- Deploy multi-decade backtesting framework
- Create institutional-grade reporting suite

## Support & Documentation
- **Integration Report**: `INTEGRATION_COMPLETE.md`
- **Master Strategy**: `active-plans/MASTER_EXECUTION_PLAN.md` ⭐
- **Quick Reference**: `QUICK_REFERENCE.txt` (updated with historical sources)
- **Audit Trail**: `docs/audits/` (8+ integration reports)
- **Yahoo Finance Handoff**: `docs/handoffs/YAHOO_FINANCE_INTEGRATION_HANDOFF.md`

For any issues, check the comprehensive audit reports in `docs/audits/` or review the integration scripts in `scripts/`.