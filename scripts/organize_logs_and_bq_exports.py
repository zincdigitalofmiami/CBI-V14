#!/usr/bin/env python3
"""
Organize log files and BigQuery exports on external drive.
Creates logical structure for logs and consolidates all BQ exports.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR

# Organization directories
LOGS_DIR = BASE_DIR / "logs"
BQ_EXPORTS_DIR = BASE_DIR / "bigquery" / "exports"

# Log file patterns and destinations
LOG_CATEGORIES = {
    "collection": {
        "patterns": [
            r".*_collection\.log$",
            r".*_collection_output\.log$",
        ],
        "destination": LOGS_DIR / "collection",
        "examples": ["alpha_vantage_collection.log", "yahoo_collection.log", "fred_collection.log"]
    },
    "execution": {
        "patterns": [
            r".*EXECUTION.*\.log$",
            r".*EXECUTION.*\.txt$",
            r".*DEPLOYMENT.*\.log$",
            r".*DEPLOYMENT.*\.txt$",
        ],
        "destination": LOGS_DIR / "execution",
        "examples": ["DEPLOYMENT_PHASE_1_EXECUTION.log"]
    },
    "schema": {
        "patterns": [
            r".*SCHEMA.*\.log$",
            r".*SCHEMA.*\.txt$",
        ],
        "destination": LOGS_DIR / "schema",
        "examples": ["SCHEMA_CREATION_FINAL.log", "SCHEMA_EXECUTION_LOG.txt"]
    },
    "audit": {
        "patterns": [
            r".*AUDIT.*\.txt$",
            r".*AUDIT.*\.log$",
        ],
        "destination": LOGS_DIR / "audit",
        "examples": ["AUDIT_SUMMARY_FINAL_20251114.txt"]
    },
    "daily": {
        "patterns": [
            r"daily_updates.*\.log$",
            r"daily.*\.log$",
        ],
        "destination": LOGS_DIR / "daily",
        "examples": ["daily_updates_20251116.log"]
    },
    "discovery": {
        "patterns": [
            r".*discovery.*\.log$",
            r".*marketplace.*\.log$",
        ],
        "destination": LOGS_DIR / "discovery",
        "examples": ["google_marketplace_discovery.log"]
    },
    "summary": {
        "patterns": [
            r".*SUMMARY.*\.txt$",
            r".*COMPLETE.*\.txt$",
            r".*MISSION.*\.txt$",
            r".*WORK.*\.txt$",
        ],
        "destination": LOGS_DIR / "summary",
        "examples": ["EXECUTION_COMPLETE_SUMMARY.txt", "MISSION_ACCOMPLISHED.txt", "WORK_COMPLETE_TONIGHT.txt"]
    },
    "requirements": {
        "patterns": [
            r"requirements.*\.txt$",
        ],
        "destination": LOGS_DIR / "requirements",
        "examples": ["requirements_training.txt"]
    }
}

# BigQuery export organization
BQ_EXPORT_STRUCTURE = {
    "training_data": {
        "patterns": [
            r".*training.*\.parquet$",
            r".*_training\.parquet$",
        ],
        "destination": BQ_EXPORTS_DIR / "training_data",
        "subdirs": ["by_asset", "by_horizon", "by_date"]
    },
    "features": {
        "patterns": [
            r".*features.*\.parquet$",
            r".*_features\.parquet$",
        ],
        "destination": BQ_EXPORTS_DIR / "features",
        "subdirs": ["by_type", "by_date"]
    },
    "predictions": {
        "patterns": [
            r".*predictions.*\.parquet$",
            r".*_predictions\.parquet$",
        ],
        "destination": BQ_EXPORTS_DIR / "predictions",
        "subdirs": ["by_asset", "by_horizon", "by_date"]
    },
    "backups": {
        "patterns": [
            r".*backup.*",
            r".*BACKUP.*",
        ],
        "destination": BQ_EXPORTS_DIR / "backups",
        "subdirs": ["by_date"]
    },
    "metadata": {
        "patterns": [
            r".*metadata.*",
            r".*METADATA.*",
        ],
        "destination": BQ_EXPORTS_DIR / "metadata",
        "subdirs": ["by_date"]
    },
    "quarantine": {
        "patterns": [
            r".*contaminated.*",
            r".*quarantine.*",
        ],
        "destination": BQ_EXPORTS_DIR / "quarantine",
        "subdirs": ["by_date"]
    },
    "raw_exports": {
        "patterns": [
            r"export_.*",
            r".*export.*",
        ],
        "destination": BQ_EXPORTS_DIR / "raw_exports",
        "subdirs": ["by_date"]
    }
}

def extract_date_from_filename(filename):
    """Extract date from filename if present"""
    # Look for dates in format YYYY-MM-DD, YYYYMMDD, or YYYY_MM_DD
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{4}\d{2}\d{2})",
        r"(\d{4}_\d{2}_\d{2})",
        r"(\d{4}_\d{2})",  # Year-month only
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1).replace("_", "-")
            # Normalize to YYYY-MM format for subdirectory
            if len(date_str) == 7:  # YYYY-MM
                return date_str
            elif len(date_str) == 10:  # YYYY-MM-DD
                return date_str[:7]  # Return YYYY-MM
    return None

def extract_asset_from_filename(filename):
    """Extract asset name (ZL, MES, ES) from filename"""
    filename_upper = filename.upper()
    assets = ["ZL", "MES", "ES"]
    for asset in assets:
        if asset in filename_upper:
            return asset
    return "other"

def extract_horizon_from_filename(filename):
    """Extract prediction horizon from filename"""
    filename_lower = filename.lower()
    horizons = ["1min", "5min", "15min", "1h", "1d", "1w", "1m", "3m", "6m"]
    for horizon in horizons:
        if horizon in filename_lower:
            return horizon
    return "other"

def create_directories():
    """Create all necessary directories"""
    directories = set()
    
    # Add log directories
    for category in LOG_CATEGORIES.values():
        directories.add(category["destination"])
    
    # Add BQ export directories
    for category in BQ_EXPORT_STRUCTURE.values():
        directories.add(category["destination"])
        # Add subdirectories
        for subdir in category.get("subdirs", []):
            directories.add(category["destination"] / subdir)
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {directory}")

def categorize_log_file(filename):
    """Categorize a log file"""
    for category, rules in LOG_CATEGORIES.items():
        for pattern in rules["patterns"]:
            if re.match(pattern, filename, re.IGNORECASE):
                return rules["destination"], category
    return None, "uncategorized"

def categorize_bq_export(filename, filepath):
    """Categorize a BigQuery export file"""
    # Check if it's in a known BQ export location
    filepath_str = str(filepath)
    
    # Check for backup folders
    if "backup" in filepath_str.lower() or "00_bigquery" in filepath_str:
        date = extract_date_from_filename(filepath_str) or datetime.now().strftime("%Y-%m")
        return BQ_EXPORTS_DIR / "backups" / "by_date" / date, "backup"
    
    # Check for quarantine
    if "quarantine" in filepath_str.lower() or "contaminated" in filepath_str.lower():
        date = extract_date_from_filename(filepath_str) or datetime.now().strftime("%Y-%m")
        return BQ_EXPORTS_DIR / "quarantine" / "by_date" / date, "quarantine"
    
    # Check for raw export folders
    if "export_evaluated" in filepath_str or "export_" in filename.lower():
        date = extract_date_from_filename(filepath_str) or datetime.now().strftime("%Y-%m")
        return BQ_EXPORTS_DIR / "raw_exports" / "by_date" / date, "raw_export"
    
    # Categorize by content
    for category, rules in BQ_EXPORT_STRUCTURE.items():
        if category in ["backups", "quarantine", "raw_exports"]:
            continue  # Already handled above
        
        for pattern in rules["patterns"]:
            if re.search(pattern, filename, re.IGNORECASE):
                # Determine subdirectory based on file type
                if category == "training_data":
                    asset = extract_asset_from_filename(filename)
                    horizon = extract_horizon_from_filename(filename)
                    if asset != "other":
                        return BQ_EXPORTS_DIR / "training_data" / "by_asset" / asset, category
                    elif horizon != "other":
                        return BQ_EXPORTS_DIR / "training_data" / "by_horizon" / horizon, category
                    else:
                        date = extract_date_from_filename(filename) or datetime.now().strftime("%Y-%m")
                        return BQ_EXPORTS_DIR / "training_data" / "by_date" / date, category
                else:
                    date = extract_date_from_filename(filename) or datetime.now().strftime("%Y-%m")
                    return rules["destination"] / "by_date" / date, category
    
    # Default: put in raw_exports by date
    date = extract_date_from_filename(filename) or datetime.now().strftime("%Y-%m")
    return BQ_EXPORTS_DIR / "raw_exports" / "by_date" / date, "uncategorized"

def organize_logs(dry_run=True):
    """Organize log files from root"""
    root_logs = list(ROOT_DIR.glob("*.log")) + list(ROOT_DIR.glob("*.txt"))
    
    # Filter out non-log files (like requirements_training.txt might be a dependency file)
    # But we'll include it in organization anyway
    
    moves = []
    uncategorized = []
    
    for filepath in root_logs:
        filename = filepath.name
        destination, category = categorize_log_file(filename)
        
        if destination:
            moves.append((filepath, destination, category))
        else:
            uncategorized.append((filename, category))
    
    print("\n" + "="*80)
    print("LOG FILE ORGANIZATION")
    print("="*80)
    print(f"\nTotal log files found: {len(root_logs)}")
    print(f"Files to move: {len(moves)}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if moves:
        print("\n📦 LOGS TO MOVE:")
        by_category = {}
        for filepath, dest, category in moves:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((filepath.name, dest))
        
        for category, files in sorted(by_category.items()):
            print(f"\n  {category.upper()}:")
            for filename, dest in files:
                print(f"    → {filename}")
                print(f"      {dest}")
    
    if uncategorized:
        print("\n⚠️  UNCATEGORIZED LOGS:")
        for filename, category in uncategorized:
            print(f"  ? {filename} - {category}")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING LOG MOVES...")
        print("="*80)
        
        for filepath, destination, category in moves:
            try:
                dest_file = destination / filepath.name
                if dest_file.exists():
                    print(f"⚠️  Skipping {filepath.name} - already exists at destination")
                else:
                    shutil.move(str(filepath), str(dest_file))
                    print(f"✓ Moved: {filepath.name} → {destination}")
            except Exception as e:
                print(f"✗ Error moving {filepath.name}: {e}")
    
    return len(moves), len(uncategorized)

def organize_bq_exports(dry_run=True):
    """Organize BigQuery exports"""
    # Find all BQ export locations
    export_locations = [
        BASE_DIR / "TrainingData" / "exports",
        BASE_DIR / "TrainingData" / "00_bigquery_backup_20251119",
        BASE_DIR / "TrainingData" / "quarantine" / "bq_contaminated_exports",
        BASE_DIR / "TrainingData" / "raw" / "export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z",
        BASE_DIR / "cache" / "bigquery_results",
    ]
    
    moves = []
    files_processed = []
    
    for location in export_locations:
        if not location.exists():
            continue
        
        if location.is_file():
            # It's a single file
            filename = location.name
            destination, category = categorize_bq_export(filename, location)
            moves.append((location, destination, category))
            files_processed.append(filename)
        else:
            # It's a directory - process all files
            for filepath in location.rglob("*"):
                if filepath.is_file() and not filepath.name.startswith("."):
                    filename = filepath.name
                    destination, category = categorize_bq_export(filename, filepath)
                    moves.append((filepath, destination, category))
                    files_processed.append(str(filepath.relative_to(BASE_DIR)))
    
    print("\n" + "="*80)
    print("BIGQUERY EXPORT ORGANIZATION")
    print("="*80)
    print(f"\nTotal BQ export files/dirs found: {len(files_processed)}")
    print(f"Files to move: {len(moves)}")
    
    if moves:
        print("\n📦 BQ EXPORTS TO MOVE:")
        by_category = {}
        for filepath, dest, category in moves:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((filepath.name if filepath.is_file() else str(filepath.relative_to(BASE_DIR)), dest))
        
        for category, files in sorted(by_category.items()):
            print(f"\n  {category.upper()}:")
            for filename, dest in files[:10]:  # Show first 10
                print(f"    → {filename}")
                print(f"      {dest}")
            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING BQ EXPORT MOVES...")
        print("="*80)
        
        for filepath, destination, category in moves:
            try:
                # Ensure destination directory exists
                destination.mkdir(parents=True, exist_ok=True)
                
                if filepath.is_file():
                    dest_file = destination / filepath.name
                    if dest_file.exists():
                        print(f"⚠️  Skipping {filepath.name} - already exists at destination")
                    else:
                        shutil.move(str(filepath), str(dest_file))
                        print(f"✓ Moved: {filepath.name} → {destination}")
                else:
                    # It's a directory - move entire directory
                    dest_dir = destination / filepath.name
                    if dest_dir.exists():
                        print(f"⚠️  Skipping {filepath.name} - already exists at destination")
                    else:
                        shutil.move(str(filepath), str(dest_dir))
                        print(f"✓ Moved: {filepath.name} → {destination}")
            except Exception as e:
                print(f"✗ Error moving {filepath.name}: {e}")
    
    return len(moves)

def main():
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("="*80)
        print("DRY RUN MODE - No files will be moved")
        print("Add --execute flag to actually move files")
        print("="*80)
    else:
        print("="*80)
        print("EXECUTION MODE - Files will be moved")
        print("="*80)
    
    print("\nCreating directory structure...")
    create_directories()
    
    print("\nOrganizing log files...")
    logs_moved, logs_uncategorized = organize_logs(dry_run)
    
    print("\nOrganizing BigQuery exports...")
    bq_moved = organize_bq_exports(dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  Logs moved: {logs_moved}")
    print(f"  Logs uncategorized: {logs_uncategorized}")
    print(f"  BQ exports moved: {bq_moved}")

if __name__ == "__main__":
    main()

