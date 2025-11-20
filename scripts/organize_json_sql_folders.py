#!/usr/bin/env python3
"""
Organize JSON, SQL files, and nested folders on external drive.
Creates logical structure based on project usage patterns.
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
JSON_DIR = BASE_DIR / "data" / "json"
SQL_DIR = BASE_DIR / "sql"
CONFIG_DIR = BASE_DIR / "config"

# JSON file categories
JSON_CATEGORIES = {
    "verification": {
        "patterns": [
            r"verification.*\.json$",
            r".*verification.*\.json$",
        ],
        "destination": JSON_DIR / "verification",
        "examples": ["verification_data_sources.json", "verification_row_counts.json"]
    },
    "migration": {
        "patterns": [
            r"migration.*\.json$",
            r".*migration.*\.json$",
        ],
        "destination": JSON_DIR / "migration",
        "examples": ["migration_completeness_report_20251115.json"]
    },
    "costs": {
        "patterns": [
            r".*cost.*\.json$",
            r".*COST.*\.json$",
        ],
        "destination": JSON_DIR / "costs",
        "examples": ["REAL_BQ_COSTS.json"]
    },
    "config": {
        "patterns": [
            r".*config.*\.json$",
            r".*CONFIG.*\.json$",
            r"package\.json$",
            r"tsconfig\.json$",
            r".*\.json$",  # Catch-all for other JSON files in root
        ],
        "destination": JSON_DIR / "config",
        "exceptions": ["verification", "migration", "cost"]  # Don't match if already categorized
    }
}

# SQL file categories
SQL_CATEGORIES = {
    "schemas": {
        "patterns": [
            r".*SCHEMA.*\.sql$",
            r".*schema.*\.sql$",
        ],
        "destination": SQL_DIR / "schemas",
        "examples": ["COMPLETE_BIGQUERY_SCHEMA.sql", "FINAL_COMPLETE_BQ_SCHEMA.sql"]
    },
    "verification": {
        "patterns": [
            r"verification.*\.sql$",
            r".*verification.*\.sql$",
        ],
        "destination": SQL_DIR / "verification",
        "examples": ["verification_sql_queries.sql"]
    },
    "queries": {
        "patterns": [
            r".*\.sql$",  # Catch-all for other SQL files
        ],
        "destination": SQL_DIR / "queries",
        "exceptions": ["SCHEMA", "schema", "verification"]  # Don't match if already categorized
    }
}

# Folder consolidation rules
FOLDER_CONSOLIDATION = {
    "logs": {
        "source": BASE_DIR / "Logs",  # Capital L
        "destination": BASE_DIR / "logs",  # lowercase
        "merge": True,  # Merge contents
    },
    "cache": {
        "source_patterns": [
            BASE_DIR / ".cache",
        ],
        "destination": BASE_DIR / "cache",
        "merge": True,
    }
}

# Folders that should be organized
FOLDER_ORGANIZATION = {
    "gpt_data": {
        "source": BASE_DIR / "GPT_Data",
        "destination": BASE_DIR / "data" / "gpt",
        "merge": False,
    },
    "py_knowledge": {
        "source": BASE_DIR / "Py Knowledge",
        "destination": BASE_DIR / "docs" / "reference" / "py_knowledge",
        "merge": False,
    }
}

def should_keep_in_root(filename, category_rules):
    """Check if file should stay in root based on exceptions"""
    filename_upper = filename.upper()
    for exception in category_rules.get("exceptions", []):
        if exception.upper() in filename_upper:
            return False  # Don't keep if matches exception
    return True

def categorize_json_file(filename):
    """Categorize a JSON file"""
    # Check each category in order (most specific first)
    for category, rules in JSON_CATEGORIES.items():
        # Skip if matches exception
        if not should_keep_in_root(filename, rules):
            continue
        
        for pattern in rules["patterns"]:
            if re.match(pattern, filename, re.IGNORECASE):
                return rules["destination"], category
    
    return None, "uncategorized"

def categorize_sql_file(filename):
    """Categorize a SQL file"""
    # Check each category in order (most specific first)
    for category, rules in SQL_CATEGORIES.items():
        # Skip if matches exception
        if not should_keep_in_root(filename, rules):
            continue
        
        for pattern in rules["patterns"]:
            if re.match(pattern, filename, re.IGNORECASE):
                return rules["destination"], category
    
    return None, "uncategorized"

def create_directories():
    """Create all necessary directories"""
    directories = set()
    
    # Add JSON directories
    for category in JSON_CATEGORIES.values():
        directories.add(category["destination"])
    
    # Add SQL directories
    for category in SQL_CATEGORIES.values():
        directories.add(category["destination"])
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {directory}")

def organize_json_files(dry_run=True):
    """Organize JSON files from root"""
    root_json = list(ROOT_DIR.glob("*.json"))
    
    moves = []
    uncategorized = []
    protected = []
    
    for filepath in root_json:
        filename = filepath.name
        
        # Skip package.json and config files in subdirectories
        if filepath.parent != ROOT_DIR:
            continue
        
        destination, category = categorize_json_file(filename)
        
        if destination:
            moves.append((filepath, destination, category))
        else:
            uncategorized.append((filename, category))
    
    print("\n" + "="*80)
    print("JSON FILE ORGANIZATION")
    print("="*80)
    print(f"\nTotal JSON files found in root: {len(root_json)}")
    print(f"Files to move: {len(moves)}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if moves:
        print("\n📦 JSON FILES TO MOVE:")
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
        print("\n⚠️  UNCATEGORIZED JSON FILES:")
        for filename, category in uncategorized:
            print(f"  ? {filename} - {category}")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING JSON MOVES...")
        print("="*80)
        
        for filepath, destination, category in moves:
            try:
                destination.mkdir(parents=True, exist_ok=True)
                dest_file = destination / filepath.name
                if dest_file.exists():
                    print(f"⚠️  Skipping {filepath.name} - already exists at destination")
                else:
                    shutil.move(str(filepath), str(dest_file))
                    print(f"✓ Moved: {filepath.name} → {destination}")
            except Exception as e:
                print(f"✗ Error moving {filepath.name}: {e}")
    
    return len(moves), len(uncategorized)

def organize_sql_files(dry_run=True):
    """Organize SQL files from root"""
    root_sql = list(ROOT_DIR.glob("*.sql"))
    
    moves = []
    uncategorized = []
    
    for filepath in root_sql:
        filename = filepath.name
        
        # Only process files in root
        if filepath.parent != ROOT_DIR:
            continue
        
        destination, category = categorize_sql_file(filename)
        
        if destination:
            moves.append((filepath, destination, category))
        else:
            uncategorized.append((filename, category))
    
    print("\n" + "="*80)
    print("SQL FILE ORGANIZATION")
    print("="*80)
    print(f"\nTotal SQL files found in root: {len(root_sql)}")
    print(f"Files to move: {len(moves)}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if moves:
        print("\n📦 SQL FILES TO MOVE:")
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
        print("\n⚠️  UNCATEGORIZED SQL FILES:")
        for filename, category in uncategorized:
            print(f"  ? {filename} - {category}")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING SQL MOVES...")
        print("="*80)
        
        for filepath, destination, category in moves:
            try:
                destination.mkdir(parents=True, exist_ok=True)
                dest_file = destination / filepath.name
                if dest_file.exists():
                    print(f"⚠️  Skipping {filepath.name} - already exists at destination")
                else:
                    shutil.move(str(filepath), str(dest_file))
                    print(f"✓ Moved: {filepath.name} → {destination}")
            except Exception as e:
                print(f"✗ Error moving {filepath.name}: {e}")
    
    return len(moves), len(uncategorized)

def consolidate_folders(dry_run=True):
    """Consolidate nested folders"""
    consolidations = []
    
    # Handle Logs -> logs consolidation
    logs_source = BASE_DIR / "Logs"
    logs_dest = BASE_DIR / "logs"
    
    if logs_source.exists() and logs_source.is_dir():
        if logs_dest.exists():
            # Merge: move contents from Logs to logs
            for item in logs_source.iterdir():
                dest_item = logs_dest / item.name
                if dest_item.exists():
                    consolidations.append((item, logs_dest, f"⚠️  {item.name} already exists in logs/"))
                else:
                    consolidations.append((item, logs_dest, f"✓ Merge {item.name} from Logs/ to logs/"))
        else:
            consolidations.append((logs_source, BASE_DIR, f"✓ Rename Logs/ to logs/"))
    
    # Handle GPT_Data -> data/gpt
    gpt_source = BASE_DIR / "GPT_Data"
    gpt_dest = BASE_DIR / "data" / "gpt"
    
    if gpt_source.exists() and gpt_source.is_dir():
        consolidations.append((gpt_source, gpt_dest.parent, f"✓ Move GPT_Data/ to data/gpt/"))
    
    # Handle Py Knowledge -> docs/reference/py_knowledge
    py_source = BASE_DIR / "Py Knowledge"
    py_dest = BASE_DIR / "docs" / "reference" / "py_knowledge"
    
    if py_source.exists() and py_source.is_dir():
        consolidations.append((py_source, py_dest.parent, f"✓ Move Py Knowledge/ to docs/reference/py_knowledge/"))
    
    print("\n" + "="*80)
    print("FOLDER CONSOLIDATION")
    print("="*80)
    print(f"\nFolders to consolidate: {len(consolidations)}")
    
    if consolidations:
        print("\n📁 FOLDERS TO CONSOLIDATE:")
        for source, dest_parent, message in consolidations:
            print(f"  {message}")
            print(f"    Source: {source}")
            print(f"    Dest: {dest_parent}")
    
    # Execute consolidations if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING FOLDER CONSOLIDATIONS...")
        print("="*80)
        
        for source, dest_parent, message in consolidations:
            try:
                if source.is_file():
                    # It's a file being moved
                    dest_file = dest_parent / source.name
                    if dest_file.exists():
                        print(f"⚠️  Skipping {source.name} - already exists")
                    else:
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(dest_file))
                        print(f"✓ Moved file: {source.name} → {dest_file}")
                elif "Merge" in message:
                    # Merge contents
                    dest_dir = dest_parent
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    for item in source.iterdir():
                        dest_item = dest_dir / item.name
                        if dest_item.exists():
                            print(f"⚠️  Skipping {item.name} - already exists in {dest_dir}")
                        else:
                            shutil.move(str(item), str(dest_item))
                            print(f"✓ Merged: {item.name} → {dest_dir}")
                    # Remove empty source directory
                    if not any(source.iterdir()):
                        source.rmdir()
                        print(f"✓ Removed empty directory: {source}")
                elif "Rename" in message:
                    # Rename directory
                    dest_dir = dest_parent / source.name.lower()
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(dest_dir))
                    print(f"✓ Renamed: {source} → {dest_dir}")
                else:
                    # Move directory
                    dest_dir = dest_parent / source.name
                    if dest_dir.exists():
                        print(f"⚠️  Skipping {source.name} - destination already exists")
                    else:
                        dest_dir.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(dest_dir))
                        print(f"✓ Moved: {source} → {dest_dir}")
            except Exception as e:
                print(f"✗ Error consolidating {source}: {e}")
    
    return len(consolidations)

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
    
    print("\nOrganizing JSON files...")
    json_moved, json_uncategorized = organize_json_files(dry_run)
    
    print("\nOrganizing SQL files...")
    sql_moved, sql_uncategorized = organize_sql_files(dry_run)
    
    print("\nConsolidating folders...")
    folders_consolidated = consolidate_folders(dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  JSON files moved: {json_moved}")
    print(f"  JSON uncategorized: {json_uncategorized}")
    print(f"  SQL files moved: {sql_moved}")
    print(f"  SQL uncategorized: {sql_uncategorized}")
    print(f"  Folders consolidated: {folders_consolidated}")

if __name__ == "__main__":
    main()





