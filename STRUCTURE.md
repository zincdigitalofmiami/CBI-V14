# CBI-V14 Project Structure

## Overview
This document describes the fully organized structure of the CBI-V14 project after the comprehensive Yahoo Finance historical data integration (November 12, 2025). The project now features **25+ years of historical data** with **365% more training data**, organized cleanly between production BQML models, Vertex AI pipelines, and extensive historical datasets.

## Path Relationship (Critical)

**The repository lives on the external drive, with a symlink for convenience:**

- **Actual Location (Primary)**: `/Volumes/Satechi Hub/Projects/CBI-V14/`
  - This is where the `.git` repository actually lives
  - All files, code, plans, configs are stored here
  - This is the working directory for all operations

- **Symlink (Convenience)**: `/Users/kirkmusick/Documents/GitHub/CBI-V14/`
  - Points to the external drive location via symlink
  - Created by `setup_new_machine.sh` for IDE/tool compatibility
  - **Both paths point to the same files** - edit either one

**When editing files:**
- Use either path - they're the same via symlink
- Git operations work from either location
- All tools (Cursor, VS Code, terminal) can use either path
- The external drive path is the "source of truth" (where `.git` lives)

**Why this setup:**
- External drive stores everything (code + large TrainingData/Models/Logs)
- Symlink provides standard GitHub path for tools expecting `~/Documents/GitHub/`
- Single source of truth, no sync needed

## Directory Structure (Updated Nov 12, 2025)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
│
├── 📁 active-plans/              # Current working plans (9 strategic files)
│   ├── MASTER_EXECUTION_PLAN.md              # PRIMARY - 7-day institutional system
│   ├── VERTEX_AI_TRUMP_ERA_PLAN.md
│   ├── TRUMP_ERA_EXECUTION_PLAN.md
│   ├── MAC_TRAINING_SETUP_PLAN.md
│   ├── MAC_TRAINING_EXPANDED_STRATEGY.md
│   ├── HARDWARE_OPTIMIZED_TRAINING_GUIDE.md
│   ├── BASELINE_STRATEGY.md
│   ├── PHASE_1_PRODUCTION_GAPS.md
│   └── REGIME_BASED_TRAINING_STRATEGY.md
│
├── 📁 archive/                   # Historical snapshots and legacy packages
│   ├── audit_consolidation_nov1_2025/        # Pre-integration audits
│   ├── baseline_training_session_oct27/      # Historical training sessions
│   ├── csv_backups_oct27/                    # Data backups
│   ├── legacy_cleanup_oct28_2025/            # Old cleanup efforts
│   ├── legacy_rebuild_scripts/               # Historical rebuild scripts
│   ├── legacy_scripts/                       # Deprecated Python scripts
│   ├── md_status_oct27/                      # Old documentation snapshots
│   ├── oct31_2025_cleanup/                   # Halloween cleanup
│   └── py_tasks_oct27/                       # Historical Python tasks
│
├── 📁 config/                    # Configuration files
│   ├── bigquery/                # SQL queries and views (210+ files)
│   │   ├── bigquery-sql/
│   │   │   ├── PRODUCTION_HORIZON_SPECIFIC/  # 5 horizon training SQLs
│   │   │   ├── PRODUCTION_STANDARD_258_FEATURES/
│   │   │   ├── INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql  # NEW - Historical integration
│   │   │   └── TRUMP_RICH_DART_V1.sql       # Trump-era model SQL
│   │   └── vertex-ai/
│   ├── system/                  # System configuration
│   └── terraform/               # Infrastructure as code
│
├── 📁 dashboard-nextjs/          # Frontend dashboard (Next.js)
│   ├── src/                     # 57 React components (34 .tsx, 22 .ts)
│   └── docs/                    # Dashboard-specific documentation
│
├── 📁 data/                      # Local cache / temporary datasets
│   ├── active/                  # Current working data
│   └── csv/                     # CSV exports
│
├── 📁 docs/                      # Documentation library (Expanded)
│   ├── analysis/                # Data & model analysis (14 reports)
│   ├── audits/                  # Verification & audit reports (80+ files)
│   │   ├── INTEGRATION_SUCCESS_REPORT_20251112.md
│   │   ├── HISTORICAL_DATA_TREASURE_TROVE_20251112.md
│   │   ├── YAHOO_FINANCE_COMPREHENSIVE_FULL_AUDIT_20251112.md
│   │   └── [8+ new integration audit reports]
│   ├── code-reviews/            # Code review documents (4 files)
│   ├── data/                    # Data documentation (11 files)
│   ├── forecast/                # Forecast models and configs
│   ├── handoffs/                # Session handoffs (49 files)
│   │   ├── YAHOO_FINANCE_INTEGRATION_HANDOFF.md
│   │   └── PRE_INTEGRATION_AUDIT_COMPLETE_20251112.md
│   ├── operations/              # Operational documentation
│   ├── plans/                   # Historical planning documents (23 files)
│   ├── production/              # Production documentation (6 files)
│   ├── reference/               # Reference guides (30 files)
│   ├── training/                # Training documentation (6 files)
│   ├── vegas/                   # Vegas strategy docs
│   └── vegas-intel/             # Vegas intelligence (24 files)
│
├── 📁 legacy/                    # All legacy work & deprecated assets
│   ├── bqml-work/              # BQML specific files (4 docs)
│   ├── old-analysis/
│   ├── old-plans/              # Historical plans (12 files)
│   ├── old-scripts/
│   └── old-training/
│
├── 📁 Logs/                      # Execution logs (training/ingestion/deployment)
│   ├── audit_run_20251112_164309.log         # Latest audit log
│   ├── cron/                                 # Scheduled job logs
│   ├── deployment/                           # Deployment logs
│   ├── ingestion/                            # Data ingestion logs
│   ├── pre_integration_audit_20251112_*/     # Integration audit logs
│   └── training/                             # Model training logs
│
├── 📁 Models/                    # Trained model artifacts
│   ├── bqml/                    # BigQuery ML models (5 horizons)
│   ├── local/                   # Local TensorFlow models
│   ├── mlflow/                  # MLflow experiment tracking
│   └── vertex-ai/               # Vertex AI deployments
│
├── 📁 scripts/                   # Operational utilities (148+ scripts)
│   ├── Python Scripts (105 .py files):
│   │   ├── data_quality_checks.py           # Data validation
│   │   ├── export_training_data.py          # Export to Parquet
│   │   ├── audit_yahoo_finance_comprehensive.py  # NEW - Yahoo audit
│   │   ├── check_historical_sources.py      # NEW - Historical validation
│   │   ├── find_hidden_data_fast.py         # NEW - Data discovery
│   │   ├── validate_yahoo_schema.py         # NEW - Schema validation
│   │   └── [99+ other Python utilities]
│   ├── Shell Scripts (40 .sh files):
│   │   ├── status_check.sh                  # System health check
│   │   ├── run_ultimate_consolidation.sh    # Data consolidation
│   │   ├── create_backups.sh                # NEW - Backup creation
│   │   ├── rollback_integration.sh          # NEW - Integration rollback
│   │   ├── run_pre_integration_audit.sh     # NEW - Pre-integration audit
│   │   └── [35+ other shell scripts]
│   └── cron/ automation scripts
│
├── 📁 src/                       # Application source code
│   ├── ingestion/               # 78 data ingestion scripts
│   │   ├── ingest_epa_rin_prices.py
│   │   ├── ingest_baltic_dry_index.py
│   │   ├── trump_truth_social_monitor.py
│   │   └── [75+ other ingestion scripts]
│   ├── prediction/              # Prediction pipelines
│   ├── training/                # Model training (6 files)
│   └── utils/                   # Utility functions (3 files)
│
├── 📁 TrainingData/              # Training datasets on external drive
│   ├── raw/                     # Raw data inputs
│   ├── processed/               # Processed features
│   └── exports/                 # BigQuery exports (landing zone)
│
├── 📁 vertex-ai/                 # Vertex AI implementation
│   ├── data/                    # Data validation (6 .py, 2 .txt)
│   ├── deployment/              # Model deployment (10 files)
│   │   ├── train_local_deploy_vertex.py
│   │   ├── export_savedmodel.py
│   │   ├── upload_to_vertex.py
│   │   └── create_endpoint.py
│   ├── evaluation/              # Model explainability (1 file)
│   ├── prediction/              # Prediction generation (5 files)
│   └── training/                # Training scripts
│
├── Root Files (Critical Documents):
├── README.md                     # Project overview (UPDATED)
├── QUICK_REFERENCE.txt           # Fast reference (UPDATED with historical)
├── START_HERE.md                 # Session kickoff guide
├── STRUCTURE.md                  # (this file - UPDATED)
├── INTEGRATION_COMPLETE.md       # NEW - Integration success report
├── DAY_1_DATA_EXPORT_MANIFEST.md # Data export documentation
├── DAY_1_FINAL_STATUS.md         # Day 1 completion status
├── DAY_1_CHECKLIST.md            # Execution checklist
├── HANDOFF_DAY_1_TO_EXECUTION.md # Handoff documentation
├── SESSION_COMPLETE_HANDOFF.md   # Session completion
├── SETUP_VALIDATION_REPORT.md    # Setup validation
├── CBI-V14.code-workspace        # Cursor/VS Code workspace
├── setup_new_machine.sh          # M4 Mac mini setup script
├── setup_on_new_mac.sh           # Legacy migration helper
├── migrate_to_new_mac.sh         # Migration script
├── install_mac_training_dependencies.sh  # Mac training setup
├── fix_satechi_permissions.sh    # External drive permissions
└── EXECUTE_DAY_1.sh               # Day 1 execution script
```

## Key Data Resources (November 12, 2025)

### Production BigQuery Datasets
```
cbi-v14.models_v4/
├── production_training_data_1w   # 290+ features, 6,057 rows
├── production_training_data_1m   # 290+ features, 6,057 rows
├── production_training_data_3m   # 290+ features, 6,057 rows
├── production_training_data_6m   # 290+ features, 6,057 rows
├── production_training_data_12m  # 290+ features, 6,057 rows
├── trump_rich_2023_2025          # 42 features, 782 rows
├── pre_crisis_2000_2007_historical  # NEW - 1,737 rows
├── crisis_2008_historical           # NEW - 253 rows
├── recovery_2010_2016_historical    # NEW - 1,760 rows
└── trade_war_2017_2019_historical   # NEW - 754 rows
```

### Historical Data Sources (Integrated Nov 12)
```
cbi-v14.yahoo_finance_comprehensive/
├── yahoo_normalized              # 314,381 rows (233,060 pre-2020)
├── all_symbols_20yr              # 57,397 rows (44,147 pre-2020)
├── biofuel_components_raw       # 42,367 rows (30,595 pre-2020)
├── biofuel_components_canonical # 6,475 rows (5,001 pre-2020)
└── rin_proxy_features_final     # 6,475 rows (5,001 pre-2020)
```

## Key Organization Principles

### 1. Active vs Legacy Separation
- **active-plans/**: Current initiatives (Vertex AI + neural Mac pipeline)
- **legacy/**: Deprecated BQML plans, scripts, and archives for reference
- **archive/**: Immutable snapshots and previous turnovers

### 2. Source Code Layout
- **src/** contains all Python/TypeScript source by responsibility
- **scripts/** stores operational utilities (148+ scripts organized)
- **vertex-ai/** encapsulates neural model training/deployment

### 3. Documentation Layout
- **docs/** houses all documentation organized by category
- **docs/audits/** contains 80+ audit reports including Yahoo Finance integration
- **docs/handoffs/** contains 49 transition documents
- Root documentation stays concise and current

### 4. Data & Model Assets
- **TrainingData/**, **Models/**, and **Logs/** stored on external drive
- `TrainingData/exports/` is the canonical BigQuery export zone
- `Logs/` contains structured execution history

## Navigation Guide

### For Daily Work
1. Review `active-plans/MASTER_EXECUTION_PLAN.md` for priorities
2. Check `QUICK_REFERENCE.txt` for quick commands
3. Run `./scripts/status_check.sh` for system health
4. Use `scripts/data_quality_checks.py` before exports

### For Historical Data
1. `docs/handoffs/YAHOO_FINANCE_INTEGRATION_HANDOFF.md` → integration guide
2. `docs/audits/INTEGRATION_SUCCESS_REPORT_20251112.md` → results
3. `config/bigquery/bigquery-sql/INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql` → SQL

### For New Team Members
1. Start with `START_HERE.md` (5-minute orientation)
2. Read `README.md` for platform overview
3. Review `INTEGRATION_COMPLETE.md` for latest capabilities
4. Follow `active-plans/` for current execution

## Maintenance Guidelines

### Adding New Files
- Source code → `src/` or `vertex-ai/`
- Automation scripts → `scripts/`
- Documentation → appropriate subfolder in `docs/`
- Deprecated assets → `legacy/` or `archive/`

### Archiving Old Work
- Use `legacy/old-*` for retired scripts and plans
- Snapshot full turnovers into `archive/` (date-stamped)
- Move completed integration work to `archive/` after stabilization

### Updating Plans & Docs
- Keep `active-plans/` limited to in-flight efforts
- Update root files when major capabilities change
- Use `docs/` for detailed documentation

## External Drive Structure
```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/                     # Raw data inputs
│   ├── processed/               # Feature engineering outputs
│   └── exports/                 # BigQuery Parquet exports
├── Models/
│   ├── local/                   # Local TensorFlow models
│   ├── vertex-ai/               # Vertex AI SavedModels
│   ├── bqml/                    # BQML model exports
│   └── mlflow/                  # MLflow artifacts
└── Logs/
    ├── training/                # Training runs
    ├── ingestion/               # Data pipeline logs
    ├── deployment/              # Deployment history
    └── audit_runs/              # Audit execution logs
```

## Success Metrics
- ✅ 25+ years of historical data integrated (2000-2025)
- ✅ 365% increase in training data (1,301 → 6,057 rows)
- ✅ 4 historical regime datasets created
- ✅ 148+ operational scripts organized
- ✅ 78 ingestion scripts operational
- ✅ Clear separation between active, legacy, and archive
- ✅ External storage documented and organized

## Last Updated
November 12, 2025 - Post Yahoo Finance Historical Data Integration (+365% data expansion)