#!/usr/bin/env python3
"""
Organize BQ backup and CBI-V14 project structure to match BigQuery dataset organization.
Based on BigQuery interface structure: Repositories, Queries, Notebooks, Data canvases,
Data preparations, Pipelines, and Connections (with datasets).
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR

# BigQuery dataset structure (from screenshot)
BQ_DATASETS = [
    "api",
    "features",
    "market_data",
    "monitoring",
    "predictions",
    "raw_intelligence",
    "training",
    "z_archive_20251119",
]

# BigQuery organization structure
BQ_ORGANIZATION = {
    "Repositories": {
        "description": "Code repositories and version control",
    },
    "Queries": {
        "description": "Saved SQL queries",
    },
    "Notebooks": {
        "description": "Jupyter notebooks and analysis",
    },
    "Data Canvases": {
        "description": "Data visualization and exploration",
    },
    "Data Preparations": {
        "description": "Data preparation and transformation",
    },
    "Pipelines": {
        "description": "Data pipelines and workflows",
    },
    "Connections": {
        "description": "Dataset connections",
        "datasets": BQ_DATASETS,
    },
}

def create_bq_backup_structure(dry_run=True):
    """Reorganize Full BQ Data Backup to match BigQuery structure"""
    backup_dir = BASE_DIR / "Full BQ Data Backup"
    
    print("\n" + "="*80)
    print("REORGANIZING FULL BQ DATA BACKUP")
    print("="*80)
    
    # Create new structure
    new_structure = {}
    
    for category, info in BQ_ORGANIZATION.items():
        category_path = backup_dir / category
        new_structure[category] = category_path
        
        if not dry_run:
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"\n✓ Created: {category}/")
            print(f"  Description: {info['description']}")
        
        # For Connections, create dataset subdirectories
        if category == "Connections" and "datasets" in info:
            for dataset in info["datasets"]:
                dataset_path = category_path / dataset
                if not dry_run:
                    dataset_path.mkdir(parents=True, exist_ok=True)
                    print(f"  ✓ Created: Connections/{dataset}/")
    
    # Map existing datasets to Connections
    existing_datasets = backup_dir / "Datasets"
    connections_dir = backup_dir / "Connections"
    
    if existing_datasets.exists():
        print("\n📦 MAPPING EXISTING DATASETS TO CONNECTIONS:")
        
        # Map existing dataset folders to Connections structure
        dataset_mapping = {
            "forecasting_data_warehouse": "market_data",
            "models_v4": "training",
            "training": "training",
            "raw_intelligence": "raw_intelligence",
            "staging": "features",
            "curated": "features",
            "signals": "features",
            "yahoo_finance_comprehensive": "market_data",
            "predictions": "predictions",
            "monitoring": "monitoring",
        }
        
        moves = []
        
        for item in existing_datasets.iterdir():
            if item.is_dir():
                dataset_name = item.name
                # Check if it maps to a Connections dataset
                target_dataset = dataset_mapping.get(dataset_name)
                
                if target_dataset:
                    target_path = connections_dir / target_dataset / dataset_name
                    moves.append((item, target_path, f"✓ Map {dataset_name} → Connections/{target_dataset}/"))
                else:
                    # Archive datasets go to z_archive
                    if "archive" in dataset_name.lower() or "backup" in dataset_name.lower():
                        target_path = connections_dir / "z_archive_20251119" / dataset_name
                        moves.append((item, target_path, f"✓ Archive {dataset_name} → Connections/z_archive_20251119/"))
                    else:
                        # Unknown datasets go to appropriate category or archive
                        target_path = connections_dir / "z_archive_20251119" / dataset_name
                        moves.append((item, target_path, f"✓ Archive {dataset_name} → Connections/z_archive_20251119/"))
        
        if moves:
            print("\n📦 DATASET MAPPINGS:")
            for source, target, message in moves:
                print(f"  {message}")
        
        # Execute moves if not dry run
        if not dry_run:
            print("\n" + "="*80)
            print("EXECUTING DATASET MOVES...")
            print("="*80)
            
            for source, target, message in moves:
                try:
                    target.mkdir(parents=True, exist_ok=True)
                    if target.exists() and target.is_dir():
                        # Move into target directory
                        final_path = target / source.name
                        if final_path.exists():
                            print(f"⚠️  {source.name} already exists in {target}")
                        else:
                            shutil.move(str(source), str(final_path))
                            print(f"✓ Moved: {source.name} → {target}")
                    else:
                        shutil.move(str(source), str(target))
                        print(f"✓ Moved: {source.name} → {target}")
                except Exception as e:
                    print(f"✗ Error moving {source.name}: {e}")
    
    # Organize Exports, Metadata, Quarantine into appropriate categories
    exports_dir = backup_dir / "Exports"
    metadata_dir = backup_dir / "Metadata"
    quarantine_dir = backup_dir / "Quarantine"
    
    if exports_dir.exists():
        # Move exports to Connections/training/exports or appropriate dataset
        training_exports = exports_dir / "training_data"
        if training_exports.exists():
            target = connections_dir / "training" / "exports"
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
                shutil.move(str(training_exports), str(target / "training_data"))
                print(f"✓ Moved training exports → Connections/training/exports/")
            else:
                print(f"→ Would move training exports → Connections/training/exports/")
    
    if metadata_dir.exists():
        # Move metadata to appropriate location
        target = backup_dir / "Data Preparations" / "metadata"
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
            for item in metadata_dir.iterdir():
                shutil.move(str(item), str(target / item.name))
            print(f"✓ Moved metadata → Data Preparations/metadata/")
        else:
            print(f"→ Would move metadata → Data Preparations/metadata/")
    
    if quarantine_dir.exists():
        # Move quarantine to Connections/training/quarantine
        target = connections_dir / "training" / "quarantine"
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
            for item in quarantine_dir.iterdir():
                shutil.move(str(item), str(target / item.name))
            print(f"✓ Moved quarantine → Connections/training/quarantine/")
        else:
            print(f"→ Would move quarantine → Connections/training/quarantine/")
    
    return new_structure

def organize_cbi_v14_structure(dry_run=True):
    """Organize CBI-V14 project to match BigQuery structure where applicable"""
    print("\n" + "="*80)
    print("ORGANIZING CBI-V14 PROJECT STRUCTURE")
    print("="*80)
    
    # Create structure that aligns with BigQuery organization
    structure = {
        "Repositories": {
            "path": BASE_DIR / "repositories",
            "description": "Code repositories",
            "source_folders": ["scripts", "src"],
        },
        "Queries": {
            "path": BASE_DIR / "queries",
            "description": "SQL queries",
            "source_folders": ["sql"],
        },
        "Notebooks": {
            "path": BASE_DIR / "notebooks",
            "description": "Jupyter notebooks and analysis",
            "source_folders": [],
        },
        "Data Canvases": {
            "path": BASE_DIR / "data_canvases",
            "description": "Data visualization",
            "source_folders": ["dashboard-nextjs"],
        },
        "Data Preparations": {
            "path": BASE_DIR / "data_preparations",
            "description": "Data preparation and transformation",
            "source_folders": ["TrainingData"],
        },
        "Pipelines": {
            "path": BASE_DIR / "pipelines",
            "description": "Data pipelines",
            "source_folders": ["scripts"],
        },
        "Connections": {
            "path": BASE_DIR / "connections",
            "description": "Dataset connections",
            "datasets": BQ_DATASETS,
        },
    }
    
    # Note: We're creating a parallel structure, not moving everything
    # The existing structure should remain, but we create organized views
    
    if not dry_run:
        for category, info in structure.items():
            category_path = info["path"]
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"\n✓ Created: {category}/")
            print(f"  Description: {info['description']}")
            
            # For Connections, create dataset subdirectories
            if "datasets" in info:
                for dataset in info["datasets"]:
                    dataset_path = category_path / dataset
                    dataset_path.mkdir(parents=True, exist_ok=True)
                    print(f"  ✓ Created: Connections/{dataset}/")
    
    return structure

def create_readme_files(dry_run=True):
    """Create README files explaining the new structure"""
    backup_dir = BASE_DIR / "Full BQ Data Backup"
    
    readme_content = f"""# Full BQ Data Backup - Organized by BigQuery Structure

This backup is organized to match the BigQuery dataset structure for easy navigation and reference.

## Structure

### Repositories
Code repositories and version control artifacts.

### Queries
Saved SQL queries and query templates.

### Notebooks
Jupyter notebooks and data analysis notebooks.

### Data Canvases
Data visualization and exploration tools.

### Data Preparations
Data preparation, transformation, and metadata.

### Pipelines
Data pipelines and workflow definitions.

### Connections
Dataset connections organized by dataset:

- **api**: API-related datasets
- **features**: Feature engineering datasets
- **market_data**: Market data datasets
- **monitoring**: Monitoring and performance datasets
- **predictions**: Prediction datasets
- **raw_intelligence**: Raw intelligence data
- **training**: Training datasets and exports
- **z_archive_20251119**: Archived datasets

## Organization Date

Last organized: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Usage

This structure mirrors the BigQuery interface organization for:
- Easy dataset lookup
- Consistent navigation
- Clear data lineage
- Simplified backup management
"""
    
    if not dry_run:
        readme_path = backup_dir / "README.md"
        readme_path.write_text(readme_content)
        print(f"\n✓ Created: Full BQ Data Backup/README.md")

def main():
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("="*80)
        print("DRY RUN MODE - No changes will be made")
        print("Add --execute flag to actually reorganize")
        print("="*80)
    else:
        print("="*80)
        print("EXECUTION MODE - Reorganizing by BigQuery structure")
        print("="*80)
    
    print("\nReorganizing Full BQ Data Backup...")
    bq_structure = create_bq_backup_structure(dry_run)
    
    print("\nOrganizing CBI-V14 project structure...")
    cbi_structure = organize_cbi_v14_structure(dry_run)
    
    print("\nCreating README files...")
    create_readme_files(dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nStructure now matches BigQuery organization:")
    print(f"  - Repositories")
    print(f"  - Queries")
    print(f"  - Notebooks")
    print(f"  - Data Canvases")
    print(f"  - Data Preparations")
    print(f"  - Pipelines")
    print(f"  - Connections (with {len(BQ_DATASETS)} datasets)")

if __name__ == "__main__":
    main()





