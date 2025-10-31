# Cleanup Summary - October 31, 2025

**Date:** October 31, 2025 - 03:20 UTC  
**Scope:** Archive all legacy training/prediction/audit scripts

## Summary

**Total Files Archived:** 180+ files  
**Archive Location:** `archive/oct31_2025_cleanup/`  
**Archive Size:** ~1.6 MB

## What Was Cleaned

### 1. Root Directory (9 audit reports)
- BIGQUERY_AUDIT_20251030.md
- COMPREHENSIVE_AUDIT_20251030.md
- PREDICTIONS_AUDIT_20251030.md
- REBUILD_PLAN_20251030.md
- SCHEMA_AUDIT_* (3 files)
- UNDERSTANDING_AND_PLAN.md

### 2. automl/ Directory
**Archived:**
- 25+ old training scripts (run_*.py)
- 10+ batch prediction scripts
- 10+ deployment/endpoint scripts
- 15+ log files
- 10+ markdown status files
- SQL files (rebuild_*.sql, update_*.sql)
- JSON configs

**Kept (3 active files):**
- ✅ `explain_single_horizon.py` - Feature importance extraction
- ✅ `predict_single_horizon.py` - Prediction script (with use-existing mode)
- ✅ `run_all_predictions_safe.sh` - Hardened runner

### 3. scripts/ Directory
**Archived:**
- 100+ legacy data ingestion scripts
- Old training orchestration scripts  
- Old audit/fix/diagnostic scripts
- Uppercase diagnostic scripts (BACKFILL_, CHECK_, FIX_, TRAIN_, etc.)

**Kept (Core Active):**
- ✅ `export_feature_importance.py` - Feature importance export
- ✅ `daily_signals.py`, `daily_weather.py`, `hourly_prices.py`, `hourly_news.py` - Active data ingestion
- ✅ `monitoring_alerts.py` - Monitoring
- ~40 other potentially active scripts (needs further audit)

### 4. bigquery_sql/ Directory
**Archived:**
- 16 numbered rebuild scripts (01-16)
- Temporary schema fix scripts
- Old rebuild strategies

**Kept (6 active files):**
- ✅ `01_update_fx_data.sql` - FX updates
- ✅ `02_create_fx_view.sql` - FX view
- ✅ `03_capture_schema_contract.sql` - Schema contract
- ✅ `10_execute_rebuild.sql` - Main rebuild
- ✅ `create_horizon_training_views.sql` - Horizon views
- ✅ `create_harvest_biofuel_tables.sql` - Core tables

## Active File Structure

```
/Users/zincdigital/CBI-V14/
├── automl/
│   ├── explain_single_horizon.py ✅
│   ├── predict_single_horizon.py ✅
│   └── run_all_predictions_safe.sh ✅
├── scripts/
│   ├── export_feature_importance.py ✅
│   ├── daily_*.py (4 files) ✅
│   ├── hourly_*.py (2 files) ✅
│   └── ~40 other scripts (needs review)
├── bigquery_sql/
│   ├── 01_update_fx_data.sql ✅
│   ├── 02_create_fx_view.sql ✅
│   ├── 03_capture_schema_contract.sql ✅
│   ├── 10_execute_rebuild.sql ✅
│   ├── create_horizon_training_views.sql ✅
│   └── create_harvest_biofuel_tables.sql ✅
└── dashboard-nextjs/
    ├── src/app/api/v4/feature-importance/[horizon]/route.ts ✅
    └── src/components/dashboard/FeatureImportanceCard.tsx ✅
```

## Recovery

All archived files are in:
- File system: `/Users/zincdigital/CBI-V14/archive/oct31_2025_cleanup/`
- Git history: Commits 7c8f2b6, 858995d, and subsequent

## Next Cleanup (Future)

Consider archiving in scripts/:
- Old training orchestration scripts
- Duplicate data ingestion scripts
- Legacy audit scripts

Total potential: ~30 more files could be archived after verification they're not actively used.
