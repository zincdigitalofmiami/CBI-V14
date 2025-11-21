# CBI-V14 Documentation Index
**Last Updated**: November 20, 2025

## 🚨 Start Here
1. **[GPT_READ_FIRST.md](plans/GPT_READ_FIRST.md)** - Essential context for AI assistants
2. **[MASTER_PLAN.md](plans/MASTER_PLAN.md)** - Single source of truth for architecture
3. **[TRAINING_PLAN.md](plans/TRAINING_PLAN.md)** - Complete training strategy and execution

## 📋 Current Plans
- **[TABLE_MAPPING_MATRIX.md](plans/TABLE_MAPPING_MATRIX.md)** - BigQuery table structure
- **[BIGQUERY_MIGRATION_PLAN.md](plans/BIGQUERY_MIGRATION_PLAN.md)** - Data migration strategy
- **[DASHBOARD_PAGES_PLAN.md](plans/DASHBOARD_PAGES_PLAN.md)** - Dashboard implementation
- **[DATA_SOURCES_REFERENCE.md](plans/DATA_SOURCES_REFERENCE.md)** - All data sources

## 📊 Recent Reports
- **[ZL_1MIN_DOWNLOAD_ISSUES_RESOLVED.md](reports/ZL_1MIN_DOWNLOAD_ISSUES_RESOLVED.md)** - Why ZL downloads failed
- **[DATABENTO_DATA_INVENTORY.md](reports/DATABENTO_DATA_INVENTORY.md)** - Current data status
- **[COMPLETE_DATABENTO_DOWNLOAD_LIST.md](reports/data/COMPLETE_DATABENTO_DOWNLOAD_LIST.md)** - Full download plan
- **[CURRENT_STATUS_REPORT.md](status/md/CURRENT_STATUS_REPORT.md)** - Overall project status

## 🔧 Key Scripts

### Data Collection
- `scripts/ingest/download_ALL_databento_historical.py` - Download all historical data
- `scripts/ingest/download_zl_1min_databento.py` - ZL 1-minute specific
- `scripts/ingest/check_databento_jobs.py` - Monitor batch jobs

### Data Processing
- `scripts/ingest/aggregate_zl_intraday.py` - Process ZL intraday data
- `scripts/export_training_data.py` - Export to training format
- `scripts/data_quality_checks.py` - Validate data quality

### Training Pipeline
- `src/training/baselines/*.py` - Baseline models
- `vertex-ai/deployment/*.py` - Deployment scripts (local training, not cloud)

## ⚠️ Important Notes

### What's Current (USE THESE)
- Everything in main directories
- Files dated November 2025 or later
- DataBento for futures data
- Local M4 Mac training

### What's Legacy (IGNORE THESE)
- Everything in `archive/` directory
- Everything in `legacy/` directory
- References to BQML training
- References to AutoML
- References to Alpha Vantage

### Documentation That Doesn't Exist (Was Referenced Incorrectly)
- ❌ `TRAINING_MASTER_EXECUTION_PLAN.md` → Use `TRAINING_PLAN.md` instead
- ❌ `GPT5_READ_FIRST.md` → Use `docs/plans/GPT_READ_FIRST.md` instead

## 🎯 Current Focus

### Data Collection Status
- ✅ MES: Complete (1m, 1h, daily) 2019-2025
- ⚠️ ZL: Partial (1h, daily complete; 1m downloading)
- 🔄 Others: 24 symbols downloading now

### Why ZL 1-Minute Failed Previously
1. Wrong API call (`timeseries` vs `batch`)
2. Invalid parameters (`packaging="zip"`)
3. Wrong split duration format
4. Incorrect symbol format for parent contracts

All these issues have been fixed in current scripts.

### Next Steps
1. Monitor batch job completion (~1-2 hours)
2. Download completed files
3. Load to BigQuery
4. Build master features table
5. Begin training on M4 Mac

## 📞 Support

### Internal
- Check this index first
- Read `MASTER_PLAN.md` for architecture questions
- Review recent reports for current status

### External
- DataBento: support@databento.com
- BigQuery: Google Cloud Console
- Hardware: Apple M4 Mac mini documentation








