# CBI-V14 Commodity Forecasting Platform

## Overview
CBI-V14 delivers institutional-grade soybean oil (ZL) forecasting for Chris Stacy (US Oil Solutions) with two complementary production paths:

1. **Production BQML DART models** (1w, 1m, 3m, 6m horizons) that power the current BUY / WAIT / MONITOR signals.
2. **Next-generation Vertex AI & local neural pipeline** trained on the Apple M4 Mac mini (tensorflow-metal) and deployed as custom SavedModels to Vertex AI.

Both paths rely on the same curated data warehouse, feature catalog, and documentation that now live on the external Satechi Hub drive.

## Current Status (November 2025)
| Component | Status | Notes |
|-----------|--------|-------|
| **BQML Production** | ✅ Active | MAPE 0.7–1.3%, configs in `config/bigquery/PRODUCTION_HORIZON_SPECIFIC/` |
| **Data Freshness** | ⚠️ Requires consolidation | Run `./scripts/run_ultimate_consolidation.sh` to update training tables |
| **Mac Neural Pipeline** | 🚧 In progress | Environment verified (`vertex-metal-312`), directory scaffolding next |
| **Vertex AI AutoML** | ✅ Ready to relaunch | Naming conventions & job configs in `active-plans/VERTEX_AI_TRUMP_ERA_PLAN.md` |
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

## Repository Layout
```
CBI-V14/
├── active-plans/                    # Current working plans
├── archive/                         # Immutable snapshots
├── config/
│   ├── bigquery/bigquery-sql/       # Production SQL (BQML + features)
│   └── terraform/                   # Infrastructure as code
├── dashboard-nextjs/                # Decision hub frontend
├── data/                            # Local scratch data (small)
├── docs/                            # Documentation library (analysis, audits, handoffs, reference)
├── legacy/                          # BQML-era & deprecated assets
├── Logs/                            # Runtime logs (training / ingestion / deployment)
├── Models/                          # Saved models (local / Vertex AI / BQML)
├── scripts/                         # Operational shell + Python utilities
├── src/                             # Application source (ingestion, training, prediction)
├── TrainingData/                    # Raw / processed / export datasets (external drive)
├── vertex-ai/                       # Neural pipeline data, training, deployment scripts
└── README.md, START_HERE.md, ...
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
| Consolidate stale data | `./scripts/run_ultimate_consolidation.sh` |
| View heavy-hitter correlations | `docs/analysis/THE_REAL_BIG_HITTERS_DATA_DRIVEN.md` |
| Run priority scrapers | `python src/ingestion/ingest_epa_rin_prices.py` (etc.) |
| Train & deploy Vertex AI model | `python vertex-ai/deployment/train_local_deploy_vertex.py --horizon=1m` |

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

## Support & Next Steps
- Finish Phase 2 of the Mac training plan (`active-plans/MAC_TRAINING_SETUP_PLAN.md` → directory scaffolding & loaders)
- Export fresh training datasets to `TrainingData/exports/`
- Relaunch Vertex AI AutoML jobs using the curated staging tables
- Continue to keep documentation synchronized with the external-drive layout

For any inconsistencies, update the relevant doc in `docs/` and cross-link it from `README.md` or `START_HERE.md` so it stays discoverable.