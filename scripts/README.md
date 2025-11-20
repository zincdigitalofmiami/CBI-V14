---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Scripts Directory

**Last Updated**: November 14, 2025

## Organization

Scripts are organized by purpose into subdirectories:

### Core Categories

- **`audits/`** - Data quality audits, system audits, schema audits
- **`backfill/`** - Historical data backfill scripts
- **`data_export/`** - Export scripts for BigQuery to Parquet, CSV, etc.
- **`deployment/`** - Deployment scripts, phase execution scripts
- **`features/`** - Feature calculation, verification, extraction scripts
- **`ingestion/`** - Data ingestion scripts (Yahoo, weather, news, etc.)
- **`migration/`** - Warehouse migration and reorganization scripts
- **`monitoring/`** - Monitoring and alerting scripts
- **`setup/`** - Setup and configuration scripts (cron, scheduler, etc.)
- **`specialized/`** - Specialized scripts (Trump sentiment, emergency fixes, etc.)
- **`training/`** - Training pipeline scripts
- **`utilities/`** - Utility scripts (checks, validations, diagnostics)

### Deprecated

- **`deprecated/`** - Deprecated wrapper scripts (kept for compatibility)

### Other

- **`scrapers/`** - Web scraping scripts
- **`test_data/`** - Test data files
- **`__pycache__/`** - Python cache files

## Root Scripts

Core scripts that don't fit into categories remain in root:
- `README.md` - This file
- `inventory_requirements.txt` - Python dependencies
- Core execution scripts

## Usage

Scripts are organized to make it easy to find what you need:
- Need to audit data? → `scripts/audits/`
- Need to backfill historical data? → `scripts/backfill/`
- Need to export training data? → `scripts/data_export/`
- Need to set up cron? → `scripts/setup/`

---

**Note**: All scripts maintain their original functionality. Organization is for clarity only.
