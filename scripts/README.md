# Scripts Directory Organization

## Overview
This directory contains 148+ operational scripts for the CBI-V14 project, organized by function. Scripts are primarily Python (105) and Shell (40) with a few additional utilities.

**Last Updated**: November 12, 2025  
**Status**: Organized after Yahoo Finance integration

---

## 📊 Data Quality & Validation (Priority)

### Core Validation Scripts
- `data_quality_checks.py` - **PRIMARY** - Validate data before exports
- `export_training_data.py` - Export training data to Parquet format
- `validate_export_data.py` - Verify exported data integrity

### Yahoo Finance Integration (NEW - Nov 12)
- `audit_yahoo_finance_comprehensive.py` - Comprehensive Yahoo data audit
- `check_historical_sources.py` - Verify historical data sources
- `find_hidden_data_fast.py` - Discover hidden datasets
- `find_missing_data.py` - Identify data gaps
- `validate_yahoo_schema.py` - Schema validation for Yahoo data
- `yahoo_quality_report.py` - Quality assessment report
- `deep_dive_historical.py` - Deep historical data analysis

### Table & Schema Auditing
- `audit_table_schemas.py` - Audit BigQuery table schemas
- `analyze_data_gaps.py` - Analyze missing data patterns
- `check_stale_data.py` - Identify stale data issues

---

## 🔄 Data Pipeline & Ingestion

### Consolidation Scripts
- `run_ultimate_consolidation.sh` - **PRIMARY** - Master consolidation script
- `consolidate_training_data.sh` - Consolidate training datasets
- `sync_training_data.sh` - Sync data between environments

### Ingestion Verification
- `verify_ingestion_schedules.py` - Check ingestion schedule health
- `verify_ingestion.py` - Verify ingestion pipeline status
- `run_priority_scrapers.sh` - Execute priority data scrapers

---

## 📈 Model Training & Export

### Training Data Management
- `rebuild_training_tables.py` - Rebuild production training tables
- `rebuild_production_tables.py` - Alternative rebuilder
- `populate_train_tables.sh` - Populate training tables

### Export Scripts
- `export_gcs_models.sh` - Export models to Google Cloud Storage
- `export_to_parquet.py` - Convert data to Parquet format
- `fetch_and_export_training_data.py` - Fetch and export combined

---

## 🔧 System Operations

### Health & Status
- `status_check.sh` - **PRIMARY** - System health check
- `diagnose_local_environment.sh` - Diagnose local setup issues
- `verify_setup.sh` - Verify installation and configuration

### Backup & Recovery
- `create_backups.sh` - Create data backups (NEW)
- `rollback_integration.sh` - Rollback integration changes (NEW)
- `run_pre_integration_audit.sh` - Pre-integration safety checks (NEW)
- `run_automated_audit.sh` - Automated audit execution (NEW)

---

## ⏰ Scheduling & Automation

### Cron Management
- `crontab_setup.sh` - Basic cron setup
- `crontab_optimized.sh` - Optimized cron configuration
- `enhanced_cron_setup.sh` - Enhanced scheduling
- `setup_cron_schedule.sh` - Configure schedules
- `setup_cron_jobs.sh` - Job configuration
- `check_cron_logs.sh` - Monitor cron execution

---

## 📝 Documentation & Reporting

### Report Generation
- `generate_daily_summary.py` - Daily performance summary
- `generate_performance_report.py` - Model performance reports
- `track_training_progress.py` - Training progress tracker

### System Reports
- `project_overview_report.py` - Project status overview
- `source_code_explorer.py` - Code structure analysis

---

## 🔐 API & Credentials

### API Testing
- `test_api.py` - API endpoint testing
- `test_fred_api.py` - FRED API validation
- `test_quandl_api.py` - Quandl API testing

### Authentication
- `test_auth_cloud.sh` - Cloud authentication testing
- `setup_gcp_auth.sh` - GCP authentication setup

---

## 🗂️ Legacy & Archive

### Migration Scripts
- `migrate_legacy_features.py` - Migrate old features
- `clean_legacy_tables.py` - Clean up old tables
- `archive_old_models.sh` - Archive deprecated models

### Historical Scripts
- `compare_v3_v4_results.py` - Version comparison
- `test_vegas_locally.py` - Vegas model testing

---

## 🚀 Quick Start Commands

### Daily Operations
```bash
# System health check
./status_check.sh

# Validate data quality
python data_quality_checks.py

# Export training data
python export_training_data.py

# Run consolidation
./run_ultimate_consolidation.sh
```

### Yahoo Finance Operations (NEW)
```bash
# Audit Yahoo data
python audit_yahoo_finance_comprehensive.py

# Check historical sources
python check_historical_sources.py

# Create backups before changes
./create_backups.sh

# Rollback if needed
./rollback_integration.sh
```

### Model Training
```bash
# Rebuild training tables
python rebuild_training_tables.py

# Export to GCS
./export_gcs_models.sh

# Check training progress
python track_training_progress.py
```

---

## 📊 Script Statistics

| Type | Count | Primary Use |
|------|-------|-------------|
| Python (.py) | 105 | Data processing, validation, ML |
| Shell (.sh) | 40 | System operations, automation |
| SQL (.sql) | 2 | Direct database queries |
| CSV (.csv) | 1 | Configuration data |

---

## ⚠️ Important Notes

1. **Always run `data_quality_checks.py` before exports**
2. **Create backups before major operations** (`./create_backups.sh`)
3. **Check system status regularly** (`./status_check.sh`)
4. **Yahoo Finance scripts are production-ready** (integrated Nov 12)
5. **Use `run_ultimate_consolidation.sh` for full refresh**

---

## 🔄 Recent Updates (November 12, 2025)

### Added Scripts (Yahoo Finance Integration)
- 11 new validation and audit scripts
- 3 new backup/rollback utilities
- 5 new data discovery tools

### Enhanced Scripts
- Updated export scripts for 25-year data
- Enhanced validation for historical data
- Improved schema checking

### Next Steps
- Automate historical data refresh
- Create regime-specific export scripts
- Build crisis detection utilities

---

For detailed documentation on individual scripts, check inline comments or refer to `docs/reference/`.
