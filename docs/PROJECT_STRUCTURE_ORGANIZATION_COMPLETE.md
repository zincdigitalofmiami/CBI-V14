---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Project Structure Organization - Complete
**Date:** November 19, 2025  
**Status:** ✅ Complete

---

## 📊 Organization Summary

### Project Data Structure
All CBI-V14 project data is now properly organized under the main project folder with nested folders for each functional area.

### BigQuery Backup Structure
BigQuery backup has been organized into **"Full BQ Data Backup"** with properly nested folders for main areas.

---

## 📁 Project Data Organization

All project data is organized under `/Volumes/Satechi Hub/Projects/CBI-V14/` with the following structure:

```
CBI-V14/
│
├── TrainingData/              # Training data pipeline
│   ├── raw/                   # Immutable source data
│   ├── staging/               # Validated, conformed data
│   ├── features/              # Engineered features
│   ├── labels/                # Target labels
│   ├── exports/               # Final training exports
│   ├── processed/             # Processed data
│   ├── precalc/               # Pre-calculated features
│   ├── quarantine/            # Failed validations
│   ├── sql/                   # Training-related SQL files
│   ├── json/                  # Training-related JSON files
│   └── md/                    # Training-related documentation
│
├── Models/                    # Trained model artifacts
│   ├── local/                 # Local M4 Mac models
│   ├── vertex-ai/             # Vertex AI models (legacy)
│   └── bqml/                  # BigQuery ML models
│
├── data/                      # External data sources
│   ├── gpt/                   # GPT data exports
│   ├── csv/                   # CSV data files
│   └── active/                 # Active data files
│
├── bigquery/                  # BigQuery exports and sync
│   └── exports/               # BQ exports (organized)
│
├── cache/                     # Cached API responses
│   ├── api_responses/
│   ├── bigquery_results/
│   ├── economic_data/
│   ├── file_downloads/
│   ├── news_data/
│   ├── processed_data/
│   ├── social_data/
│   ├── trump_intel/
│   └── weather_data/
│
├── logs/                      # Application and collection logs
│   ├── collection/
│   ├── execution/
│   ├── schema/
│   ├── audit/
│   ├── daily/
│   ├── discovery/
│   ├── summary/
│   └── requirements/
│
├── config/                    # Configuration files
│   ├── bigquery/
│   ├── system/
│   └── terraform/
│
├── scripts/                   # Python scripts
│   ├── data_export/
│   ├── migration/
│   ├── training/
│   ├── prediction/
│   └── analysis/
│
└── docs/                      # Project documentation
    ├── plans/
    ├── reports/
    ├── audits/
    ├── migration/
    ├── setup/
    ├── status/
    └── reference/
```

---

## 📦 Full BQ Data Backup Structure

BigQuery backup is organized in **"Full BQ Data Backup"** with the following structure:

```
Full BQ Data Backup/
│
├── Datasets/                  # BigQuery dataset backups
│   ├── 00_bigquery_backup_20251119/  # Original backup folder
│   ├── backups/               # Additional backup data
│   ├── forecasting_data_warehouse/   # Production dataset backup
│   ├── models_v4/             # Models dataset backup
│   ├── training/              # Training dataset backup
│   ├── raw_intelligence/      # Intelligence data backup
│   ├── staging/               # Staging data backup
│   ├── curated/               # Curated views backup
│   ├── signals/               # Signals backup
│   ├── yahoo_finance_comprehensive/  # Yahoo Finance backup
│   ├── predictions/           # Predictions backup
│   └── monitoring/            # Monitoring backup
│
├── Metadata/                  # Dataset and table metadata
│   ├── schemas/               # Schema definitions
│   ├── table_lists/           # Table inventory lists
│   └── backup_summaries/     # Backup summary documents
│       ├── BACKUP_SUMMARY.md
│       ├── dataset_list.txt
│       ├── datasets_list.json
│       └── datasets_list_pretty.json
│
├── Exports/                   # Exported table data
│   ├── training_data/        # Training data exports
│   │   ├── by_asset/         # Organized by asset (ZL, MES, ES)
│   │   ├── by_horizon/       # Organized by time horizon
│   │   └── by_date/          # Organized by date
│   ├── features/              # Feature exports
│   ├── predictions/           # Prediction exports
│   └── raw_data/             # Raw data exports
│
└── Quarantine/                # Contaminated or problematic exports
    ├── by_date/              # Organized by date
    │   ├── 2000-20/          # Pre-crisis data
    │   ├── 2008-20/          # Crisis data
    │   ├── 2010-20/          # Recovery data
    │   ├── 2017-20/          # Trade war data
    │   ├── 2021-20/          # Inflation data
    │   ├── 2023-20/          # Trump 2.0 data
    │   └── 2025-11/          # Recent contaminated exports
    └── by_regime/            # Organized by market regime
```

---

## 🎯 Organization Principles

### 1. Functional Organization
- Files organized by **function** (training, models, data, etc.)
- Related files kept together regardless of file type
- Clear separation of concerns

### 2. Hierarchical Nesting
- Main folders for major functional areas
- Subfolders for specific purposes
- Date-based organization for time-series data

### 3. Logical Grouping
- Training data pipeline: raw → staging → features → exports
- BigQuery backup: datasets, metadata, exports, quarantine
- All related files grouped by topic/context

### 4. Scalability
- Structure supports growth
- Easy to add new data types
- Clear naming conventions

---

## ✅ Benefits

1. **Easy Navigation:** Find files by function, not file type
2. **Logical Grouping:** Related files kept together
3. **Clear Structure:** Hierarchical organization makes sense
4. **Scalable:** Structure supports future growth
5. **Complete Backup:** All BigQuery data properly backed up and organized

---

## 📝 Notes

- All project data properly nested under CBI-V14
- BigQuery backup organized in "Full BQ Data Backup" with proper structure
- All files kept together as they are supposed to fit
- README files created to explain structure
- Script can be re-run to maintain organization

---

**Organization Complete:** November 19, 2025





