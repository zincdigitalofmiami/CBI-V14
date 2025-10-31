# Archive: October 31, 2025 Cleanup

**Date:** October 31, 2025 - 03:15 UTC  
**Reason:** Post-feature importance infrastructure implementation cleanup

## What Was Archived

### Audit Reports (9 files)
- BIGQUERY_AUDIT_20251030.md
- BIGQUERY_AUDIT_REPORT.md
- COMPREHENSIVE_AUDIT_20251030.md
- CURRENT_STATE_AUDIT_20251030.md
- PREDICTIONS_AUDIT_20251030.md
- REBUILD_PLAN_20251030.md
- SCHEMA_AUDIT_20251030.md
- SCHEMA_AUDIT_COMPLETE.md
- UNDERSTANDING_AND_PLAN.md

### AutoML Legacy Scripts
- All old training scripts (run_*.py)
- Old prediction scripts (batch_predictions_*, get_predictions_*)
- Old deployment scripts (deploy_serverless_*, quick_endpoint_*)
- Legacy validation scripts (check_*, validate_*)
- All .log files from training/prediction runs
- All .md status/audit files

### Scripts Legacy
- All uppercase diagnostic scripts (BACKFILL_, CHECK_, FIX_, TRAIN_, etc.)
- Old data ingestion scripts
- Legacy training scripts
- Old audit scripts
- Old comprehensive scripts

### SQL Legacy
- Numbered rebuild scripts (01-16)
- Temporary schema fix scripts
- Old rebuild strategies

## What Was Kept (Active Files)

### AutoML (3 files)
- `predict_single_horizon.py` - Current prediction script
- `explain_single_horizon.py` - Feature importance extraction
- `run_all_predictions_safe.sh` - Hardened runner

### Scripts (Minimal Set)
- `export_feature_importance.py` - Feature importance export
- Core data ingestion scripts (if actively used)
- Active cron scripts

### SQL
- `01_update_fx_data.sql` - FX data updates
- `02_create_fx_view.sql` - FX view creation
- `03_capture_schema_contract.sql` - Schema contract
- `10_execute_rebuild.sql` - Main rebuild script
- `create_horizon_training_views.sql` - Horizon views
- `create_harvest_biofuel_tables.sql` - Core tables

## Recovery

If any archived file is needed, it can be restored from:
`/Users/zincdigital/CBI-V14/archive/oct31_2025_cleanup/`

All archived files are also in git history (commit: 858995d).
