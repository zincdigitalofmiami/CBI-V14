#!/usr/bin/env python3
"""
Organize all CBI-V14 project data into properly named folders with nested structure.
Organize BigQuery backup into "Full BQ Data Backup" with proper nested folders.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR

# Main project data folder
PROJECT_DATA_DIR = BASE_DIR / "CBI-V14 Project Data"

# BigQuery backup folder
BQ_BACKUP_DIR = BASE_DIR / "Full BQ Data Backup"

def create_project_data_structure():
    """Create organized structure for all project data"""
    structure = {
        "TrainingData": {
            "description": "Training data pipeline (raw → staging → features → exports)",
            "subdirs": [
                "raw",           # Immutable source data
                "staging",       # Validated, conformed data
                "features",      # Engineered features
                "labels",        # Target labels
                "exports",       # Final training exports
                "processed",     # Processed data
                "precalc",      # Pre-calculated features
                "quarantine",   # Failed validations
            ]
        },
        "Models": {
            "description": "Trained model artifacts",
            "subdirs": [
                "local",        # Local M4 Mac models
                "vertex-ai",    # Vertex AI models (legacy)
                "bqml",         # BigQuery ML models
            ]
        },
        "Data": {
            "description": "External data sources and exports",
            "subdirs": [
                "gpt",          # GPT data exports
                "csv",          # CSV data files
                "active",       # Active data files
            ]
        },
        "BigQuery": {
            "description": "BigQuery exports and sync data",
            "subdirs": [
                "exports",      # BQ exports (already organized)
            ]
        },
        "Cache": {
            "description": "Cached API responses and processed data",
            "subdirs": [
                "api_responses",
                "bigquery_results",
                "economic_data",
                "file_downloads",
                "news_data",
                "processed_data",
                "social_data",
                "trump_intel",
                "weather_data",
            ]
        },
        "Logs": {
            "description": "Application and collection logs",
            "subdirs": [
                "collection",
                "execution",
                "schema",
                "audit",
                "daily",
                "discovery",
                "summary",
                "requirements",
            ]
        },
        "Config": {
            "description": "Configuration files",
            "subdirs": [
                "bigquery",
                "system",
                "terraform",
            ]
        },
        "Scripts": {
            "description": "Python scripts organized by function",
            "subdirs": [
                "data_export",
                "migration",
                "training",
                "prediction",
                "analysis",
            ]
        },
        "Documentation": {
            "description": "Project documentation",
            "subdirs": [
                "plans",
                "reports",
                "audits",
                "migration",
                "setup",
                "status",
                "reference",
            ]
        },
    }
    
    return structure

def create_bq_backup_structure():
    """Create organized structure for BigQuery backup"""
    structure = {
        "Datasets": {
            "description": "BigQuery dataset backups",
            "subdirs": [
                "forecasting_data_warehouse",
                "models_v4",
                "training",
                "raw_intelligence",
                "staging",
                "curated",
                "signals",
                "yahoo_finance_comprehensive",
                "predictions",
                "monitoring",
            ]
        },
        "Metadata": {
            "description": "Dataset and table metadata",
            "subdirs": [
                "schemas",
                "table_lists",
                "backup_summaries",
            ]
        },
        "Exports": {
            "description": "Exported table data",
            "subdirs": [
                "training_data",
                "features",
                "predictions",
                "raw_data",
            ]
        },
        "Quarantine": {
            "description": "Contaminated or problematic exports",
            "subdirs": [
                "by_date",
                "by_regime",
            ]
        },
    }
    
    return structure

def organize_project_data(dry_run=True):
    """Organize all project data into CBI-V14 Project Data folder"""
    structure = create_project_data_structure()
    
    # Mapping of existing folders to new structure
    folder_mapping = {
        "TrainingData": BASE_DIR / "TrainingData",
        "Models": BASE_DIR / "Models",
        "Data": BASE_DIR / "data",
        "BigQuery": BASE_DIR / "bigquery",
        "Cache": BASE_DIR / "cache",
        "Logs": BASE_DIR / "logs",
        "Config": BASE_DIR / "config",
        "Scripts": BASE_DIR / "scripts",
        "Documentation": BASE_DIR / "docs",
    }
    
    moves = []
    
    print("\n" + "="*80)
    print("PROJECT DATA ORGANIZATION")
    print("="*80)
    
    # Check if we should create the main folder or use existing structure
    # Actually, let's keep the existing structure but ensure it's organized
    # The user wants nested folders, so we'll ensure proper nesting
    
    for folder_name, source_path in folder_mapping.items():
        if source_path.exists():
            print(f"\n✓ {folder_name}: {source_path}")
            # Verify subdirectories exist
            expected_subdirs = structure.get(folder_name, {}).get("subdirs", [])
            if expected_subdirs:
                for subdir in expected_subdirs:
                    subdir_path = source_path / subdir
                    if not subdir_path.exists():
                        if not dry_run:
                            subdir_path.mkdir(parents=True, exist_ok=True)
                            print(f"  ✓ Created: {subdir}")
                        else:
                            print(f"  → Would create: {subdir}")
    
    return len(moves)

def organize_bq_backup(dry_run=True):
    """Organize BigQuery backup into 'Full BQ Data Backup' with proper structure"""
    structure = create_bq_backup_structure()
    
    # Find existing backup
    existing_backups = [
        BASE_DIR / "TrainingData" / "00_bigquery_backup_20251119",
        BASE_DIR / "bigquery" / "exports" / "backups",
    ]
    
    print("\n" + "="*80)
    print("BIGQUERY BACKUP ORGANIZATION")
    print("="*80)
    
    # Create Full BQ Data Backup structure
    if not dry_run:
        BQ_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n✓ Created: {BQ_BACKUP_DIR}")
    
    moves = []
    
    # Create nested structure
    for main_area, area_info in structure.items():
        area_path = BQ_BACKUP_DIR / main_area
        
        if not dry_run:
            area_path.mkdir(parents=True, exist_ok=True)
            print(f"\n✓ Created: {main_area}/")
            print(f"  Description: {area_info['description']}")
        
        # Create subdirectories
        for subdir in area_info.get("subdirs", []):
            subdir_path = area_path / subdir
            if not dry_run:
                subdir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✓ Created: {main_area}/{subdir}/")
    
    # Move existing backup data
    for backup_path in existing_backups:
        if backup_path.exists():
            if backup_path.is_dir():
                # Move entire directory
                dest_path = BQ_BACKUP_DIR / "Datasets" / backup_path.name
                if not dry_run:
                    if dest_path.exists():
                        print(f"⚠️  {backup_path.name} already exists in backup")
                    else:
                        shutil.move(str(backup_path), str(dest_path))
                        print(f"✓ Moved: {backup_path.name} → Full BQ Data Backup/Datasets/")
                else:
                    print(f"→ Would move: {backup_path.name} → Full BQ Data Backup/Datasets/")
                moves.append((backup_path, dest_path))
    
    # Move backup metadata files
    backup_metadata_patterns = [
        (BASE_DIR / "bigquery" / "exports" / "backups", BQ_BACKUP_DIR / "Metadata"),
    ]
    
    for source, dest in backup_metadata_patterns:
        if source.exists():
            for item in source.iterdir():
                if item.is_file():
                    dest_file = dest / "backup_summaries" / item.name
                    if not dry_run:
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        if dest_file.exists():
                            print(f"⚠️  {item.name} already exists")
                        else:
                            shutil.move(str(item), str(dest_file))
                            print(f"✓ Moved: {item.name} → Full BQ Data Backup/Metadata/backup_summaries/")
                    else:
                        print(f"→ Would move: {item.name} → Full BQ Data Backup/Metadata/backup_summaries/")
                    moves.append((item, dest_file))
    
    return len(moves)

def create_readme_files(dry_run=True):
    """Create README files explaining the structure"""
    readme_content = {
        BQ_BACKUP_DIR / "README.md": """# Full BQ Data Backup

This folder contains complete backups of BigQuery datasets, metadata, and exports.

## Structure

- **Datasets/**: Complete dataset backups organized by dataset name
- **Metadata/**: Schema definitions, table lists, and backup summaries
- **Exports/**: Exported table data organized by type
- **Quarantine/**: Contaminated or problematic exports

## Backup Date

Last backup: {date}

## Usage

This backup is used for:
- Disaster recovery
- Data migration verification
- Historical data reference
- Schema documentation
""".format(date=datetime.now().strftime("%Y-%m-%d")),
        
        PROJECT_DATA_DIR / "README.md": """# CBI-V14 Project Data

This folder contains all project data organized by function.

## Structure

- **TrainingData/**: Training data pipeline (raw → staging → features → exports)
- **Models/**: Trained model artifacts
- **Data/**: External data sources and exports
- **BigQuery/**: BigQuery exports and sync data
- **Cache/**: Cached API responses
- **Logs/**: Application and collection logs
- **Config/**: Configuration files
- **Scripts/**: Python scripts
- **Documentation/**: Project documentation

## Data Flow

```
Raw Data → Staging → Features → Training Data → Models → Predictions
```

## Organization

All data is organized by:
1. **Function**: What the data is used for
2. **Type**: Raw, processed, features, etc.
3. **Source**: Where the data came from
4. **Date**: When the data was collected/processed
""",
    }
    
    if not dry_run:
        for readme_path, content in readme_content.items():
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            readme_path.write_text(content)
            print(f"✓ Created: {readme_path}")
    else:
        for readme_path in readme_content.keys():
            print(f"→ Would create: {readme_path}")

def main():
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("="*80)
        print("DRY RUN MODE - No changes will be made")
        print("Add --execute flag to actually organize")
        print("="*80)
    else:
        print("="*80)
        print("EXECUTION MODE - Organizing project structure")
        print("="*80)
    
    print("\nOrganizing project data structure...")
    project_moves = organize_project_data(dry_run)
    
    print("\nOrganizing BigQuery backup...")
    bq_moves = organize_bq_backup(dry_run)
    
    print("\nCreating README files...")
    create_readme_files(dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  Project data organized: {project_moves} items")
    print(f"  BQ backup organized: {bq_moves} items")
    print(f"\nStructure:")
    print(f"  Project Data: {BASE_DIR}")
    print(f"  BQ Backup: {BQ_BACKUP_DIR}")

if __name__ == "__main__":
    main()





