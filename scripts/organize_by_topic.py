#!/usr/bin/env python3
"""
Organize files by topic/context, not by file type.
Files go to their logical project location based on purpose.
"""

import os
import shutil
from pathlib import Path
import re
import json

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR

# Topic-based file organization
# Format: topic -> {patterns, destination_base, create_subdirs}
TOPIC_ORGANIZATION = {
    "verification": {
        "patterns": {
            "json": [r"verification.*\.json$"],
            "sql": [r"verification.*\.sql$"],
            "md": [r"verification.*\.md$"],
            "txt": [r"verification.*\.txt$"],
        },
        "destination": BASE_DIR / "docs" / "audits" / "verification",
        "create_subdirs": True,  # Creates sql/, json/, md/ subdirs
    },
    "migration": {
        "patterns": {
            "json": [r"migration.*\.json$"],
            "sql": [r"migration.*\.sql$"],
            "md": [r"migration.*\.md$", r".*MIGRATION.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "migration",
        "create_subdirs": True,
    },
    "schemas": {
        "patterns": {
            "sql": [
                r".*SCHEMA.*\.sql$",
                r".*schema.*\.sql$",
                r"COMPLETE.*SCHEMA.*\.sql$",
                r"FINAL.*SCHEMA.*\.sql$",
                r"PRODUCTION.*SCHEMA.*\.sql$",
                r"VENUE.*SCHEMA.*\.sql$",
            ],
            "md": [r".*SCHEMA.*\.md$", r".*schema.*\.md$"],
        },
        "destination": BASE_DIR / "sql" / "schemas",
        "create_subdirs": False,  # SQL files go directly here
    },
    "bigquery": {
        "patterns": {
            "json": [r".*BQ.*\.json$", r".*BIGQUERY.*\.json$", r"REAL_BQ_COSTS\.json$"],
            "sql": [r".*BQ.*\.sql$", r".*BIGQUERY.*\.sql$"],
            "md": [r".*BIGQUERY.*\.md$", r".*BQ.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "reports" / "bigquery",
        "create_subdirs": True,
    },
    "costs": {
        "patterns": {
            "json": [r".*COST.*\.json$", r".*cost.*\.json$"],
            "md": [r".*COST.*\.md$", r".*cost.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "reports" / "costs",
        "create_subdirs": True,
    },
    "training": {
        "patterns": {
            "json": [r".*training.*\.json$", r"verification_training.*\.json$"],
            "sql": [r".*training.*\.sql$"],
            "md": [r".*TRAINING.*\.md$", r".*training.*\.md$"],
        },
        "destination": BASE_DIR / "TrainingData",
        "create_subdirs": True,  # Creates sql/, json/, docs/ subdirs
    },
    "data_sources": {
        "patterns": {
            "json": [r"verification_data_sources\.json$"],
            "md": [r".*DATA.*SOURCE.*\.md$", r".*DATA.*INVENTORY.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "reports" / "data",
        "create_subdirs": True,
    },
    "status": {
        "patterns": {
            "md": [r".*STATUS.*\.md$", r"CURRENT_STATUS.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "status",
        "create_subdirs": True,
    },
    "setup": {
        "patterns": {
            "md": [r".*DOWNLOAD.*\.md$", r".*FETCH.*\.md$", r".*INSTRUCTIONS.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "setup",
        "create_subdirs": True,
    },
    "fixes": {
        "patterns": {
            "md": [r".*FIX.*\.md$", r".*FIXES.*\.md$", r".*PIPELINE.*FIX.*\.md$"],
        },
        "destination": BASE_DIR / "docs" / "reports" / "fixes",
        "create_subdirs": True,
    },
    "audits": {
        "patterns": {
            "json": [r".*AUDIT.*\.json$"],
            "md": [r".*AUDIT.*\.md$"],
            "txt": [r".*AUDIT.*\.txt$"],
        },
        "destination": BASE_DIR / "docs" / "audits",
        "create_subdirs": True,
    },
}

# Folder consolidation
FOLDER_CONSOLIDATION = {
    "logs": {
        "source": BASE_DIR / "Logs",
        "destination": BASE_DIR / "logs",
        "action": "merge",  # Merge contents
    },
    "gpt_data": {
        "source": BASE_DIR / "GPT_Data",
        "destination": BASE_DIR / "data" / "gpt",
        "action": "move",
    },
    "py_knowledge": {
        "source": BASE_DIR / "Py Knowledge",
        "destination": BASE_DIR / "docs" / "reference" / "py_knowledge",
        "action": "move",
    },
}

def get_file_type(filename):
    """Determine file type from extension"""
    ext = Path(filename).suffix.lower()
    if ext == ".json":
        return "json"
    elif ext == ".sql":
        return "sql"
    elif ext == ".md":
        return "md"
    elif ext == ".txt":
        return "txt"
    elif ext == ".log":
        return "log"
    return "other"

def categorize_file(filepath):
    """Categorize a file by topic based on filename patterns"""
    filename = filepath.name
    file_type = get_file_type(filename)
    
    # Skip if not a file type we organize
    if file_type not in ["json", "sql", "md", "txt"]:
        return None, None, None
    
    # Check each topic category
    for topic, rules in TOPIC_ORGANIZATION.items():
        patterns = rules["patterns"].get(file_type, [])
        
        for pattern in patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                destination = rules["destination"]
                
                # If create_subdirs is True, add file type subdirectory
                if rules.get("create_subdirs", False):
                    destination = destination / file_type
                
                return destination, topic, file_type
    
    return None, "uncategorized", file_type

def create_directories():
    """Create all necessary directories"""
    directories = set()
    
    # Add topic directories
    for topic, rules in TOPIC_ORGANIZATION.items():
        base_dir = rules["destination"]
        directories.add(base_dir)
        
        if rules.get("create_subdirs", False):
            # Add subdirectories for each file type that has patterns
            for file_type in rules["patterns"].keys():
                directories.add(base_dir / file_type)
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {directory}")

def organize_files(dry_run=True):
    """Organize files from root by topic"""
    # Get all files in root
    root_files = []
    for ext in ["*.json", "*.sql", "*.md", "*.txt"]:
        root_files.extend(list(ROOT_DIR.glob(ext)))
    
    # Filter to only root-level files
    root_files = [f for f in root_files if f.parent == ROOT_DIR]
    
    # Exclude protected files
    protected = ["README.md", "GPT5_READ_FIRST.md"]
    root_files = [f for f in root_files if f.name not in protected]
    
    moves = []
    uncategorized = []
    
    for filepath in root_files:
        destination, topic, file_type = categorize_file(filepath)
        
        if destination:
            moves.append((filepath, destination, topic, file_type))
        else:
            uncategorized.append((filepath.name, topic, file_type))
    
    print("\n" + "="*80)
    print("FILE ORGANIZATION BY TOPIC")
    print("="*80)
    print(f"\nTotal files found in root: {len(root_files)}")
    print(f"Files to move: {len(moves)}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if moves:
        print("\n📦 FILES TO MOVE:")
        by_topic = {}
        for filepath, dest, topic, file_type in moves:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append((filepath.name, dest, file_type))
        
        for topic, files in sorted(by_topic.items()):
            print(f"\n  {topic.upper()}:")
            for filename, dest, file_type in files:
                print(f"    → {filename} ({file_type})")
                print(f"      {dest}")
    
    if uncategorized:
        print("\n⚠️  UNCATEGORIZED FILES:")
        for filename, topic, file_type in uncategorized:
            print(f"  ? {filename} ({file_type}) - {topic}")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING FILE MOVES...")
        print("="*80)
        
        for filepath, destination, topic, file_type in moves:
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
    
    for folder_name, rules in FOLDER_CONSOLIDATION.items():
        source = rules["source"]
        destination = rules["destination"]
        action = rules["action"]
        
        if not source.exists() or not source.is_dir():
            continue
        
        if action == "merge":
            # Merge contents into destination
            if destination.exists():
                for item in source.iterdir():
                    dest_item = destination / item.name
                    if dest_item.exists():
                        consolidations.append((item, destination, f"⚠️  {item.name} already exists"))
                    else:
                        consolidations.append((item, destination, f"✓ Merge {item.name}"))
            else:
                consolidations.append((source, destination.parent, f"✓ Rename {source.name} to {destination.name}"))
        else:
            # Move entire folder
            consolidations.append((source, destination.parent, f"✓ Move {source.name} to {destination.name}"))
    
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
                    try:
                        if not any(source.iterdir()):
                            source.rmdir()
                            print(f"✓ Removed empty directory: {source}")
                    except:
                        pass
                elif "Rename" in message:
                    # Rename directory
                    dest_dir = dest_parent / source.name.lower()
                    if dest_dir.exists():
                        print(f"⚠️  Skipping {source.name} - destination already exists")
                    else:
                        dest_dir.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(dest_dir))
                        print(f"✓ Renamed: {source} → {dest_dir}")
                else:
                    # Move directory
                    dest_dir = dest_parent / destination.name
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
    
    print("\nOrganizing files by topic...")
    files_moved, files_uncategorized = organize_files(dry_run)
    
    print("\nConsolidating folders...")
    folders_consolidated = consolidate_folders(dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  Files moved: {files_moved}")
    print(f"  Files uncategorized: {files_uncategorized}")
    print(f"  Folders consolidated: {folders_consolidated}")

if __name__ == "__main__":
    main()

