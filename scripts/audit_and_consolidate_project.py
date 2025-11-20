#!/usr/bin/env python3
"""
Audit CBI-V14 project structure and ensure all folders and work are located in the project.
Consolidate duplicates and organize everything properly.
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR

# Expected project structure
EXPECTED_FOLDERS = {
    "TrainingData": "Training data pipeline",
    "Models": "Trained model artifacts",
    "data": "External data sources",
    "bigquery": "BigQuery exports",
    "cache": "Cached API responses",
    "logs": "Application logs (lowercase)",
    "config": "Configuration files",
    "scripts": "Python scripts",
    "docs": "Documentation",
    "src": "Source code",
    "sql": "SQL files",
    "archive": "Archived files",
    "legacy": "Legacy code",
    "registry": "Registry files",
    "state": "State files",
    "vertex-ai": "Vertex AI code",
    "dashboard-nextjs": "Dashboard frontend",
    "Full BQ Data Backup": "BigQuery backup",
}

# Folders that should be consolidated
CONSOLIDATION_RULES = {
    "Logs": {
        "target": "logs",
        "action": "merge",  # Merge contents into logs/
    },
    "CBI-V14 Project Data": {
        "target": None,
        "action": "remove_if_empty",  # Remove if empty, otherwise investigate
    },
}

def audit_project_structure():
    """Audit the current project structure"""
    print("\n" + "="*80)
    print("CBI-V14 PROJECT STRUCTURE AUDIT")
    print("="*80)
    
    # Get all top-level directories
    all_dirs = [d for d in ROOT_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    # Categorize directories
    expected = []
    unexpected = []
    duplicates = []
    
    for dir_path in sorted(all_dirs):
        dir_name = dir_path.name
        
        if dir_name in EXPECTED_FOLDERS:
            expected.append((dir_name, EXPECTED_FOLDERS[dir_name]))
        elif dir_name in CONSOLIDATION_RULES:
            duplicates.append((dir_name, CONSOLIDATION_RULES[dir_name]))
        else:
            unexpected.append(dir_name)
    
    print(f"\n📁 Total directories found: {len(all_dirs)}")
    print(f"✓ Expected folders: {len(expected)}")
    print(f"⚠️  Duplicates/consolidation needed: {len(duplicates)}")
    print(f"❓ Unexpected folders: {len(unexpected)}")
    
    print("\n✓ EXPECTED FOLDERS:")
    for name, description in expected:
        size = get_folder_size(ROOT_DIR / name)
        print(f"  {name:30} - {description:40} ({size})")
    
    if duplicates:
        print("\n⚠️  DUPLICATES/CONSOLIDATION NEEDED:")
        for name, rule in duplicates:
            target = rule.get("target") or "N/A"
            action = rule.get("action", "unknown")
            print(f"  {name:30} → {target:30} (action: {action})")
    
    if unexpected:
        print("\n❓ UNEXPECTED FOLDERS:")
        for name in unexpected:
            size = get_folder_size(ROOT_DIR / name)
            print(f"  {name:30} ({size})")
    
    return {
        "expected": expected,
        "duplicates": duplicates,
        "unexpected": unexpected,
        "all_dirs": all_dirs
    }

def get_folder_size(path):
    """Get human-readable folder size"""
    try:
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except:
                    pass
        
        # Convert to human-readable
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total < 1024.0:
                return f"{total:.1f} {unit}"
            total /= 1024.0
        return f"{total:.1f} PB"
    except:
        return "unknown"

def consolidate_duplicates(dry_run=True):
    """Consolidate duplicate folders"""
    print("\n" + "="*80)
    print("CONSOLIDATING DUPLICATES")
    print("="*80)
    
    consolidations = []
    
    for folder_name, rule in CONSOLIDATION_RULES.items():
        source = ROOT_DIR / folder_name
        target_name = rule.get("target")
        action = rule.get("action")
        
        if not source.exists():
            continue
        
        if action == "merge" and target_name:
            target = ROOT_DIR / target_name
            if target.exists():
                # Merge contents
                items_to_merge = list(source.iterdir())
                for item in items_to_merge:
                    dest_item = target / item.name
                    if dest_item.exists():
                        consolidations.append((item, target, f"⚠️  {item.name} already exists in {target_name}/"))
                    else:
                        consolidations.append((item, target, f"✓ Merge {item.name} from {folder_name}/ to {target_name}/"))
            else:
                # Rename source to target
                consolidations.append((source, ROOT_DIR, f"✓ Rename {folder_name}/ to {target_name}/"))
        
        elif action == "remove_if_empty":
            items = list(source.iterdir())
            if len(items) == 0:
                consolidations.append((source, None, f"✓ Remove empty {folder_name}/"))
            else:
                print(f"\n⚠️  {folder_name}/ is not empty ({len(items)} items)")
                print(f"   Contents: {[item.name for item in items[:5]]}")
                consolidations.append((source, None, f"❓ Investigate {folder_name}/ ({len(items)} items)"))
    
    if consolidations:
        print("\n📦 CONSOLIDATIONS TO PERFORM:")
        for source, target, message in consolidations:
            print(f"  {message}")
            if target:
                print(f"    Source: {source}")
                print(f"    Target: {target}")
    
    # Execute consolidations if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING CONSOLIDATIONS...")
        print("="*80)
        
        for source, target, message in consolidations:
            try:
                if "Remove" in message or "Investigate" in message:
                    if "empty" in message.lower():
                        source.rmdir()
                        print(f"✓ Removed empty: {source.name}")
                    else:
                        print(f"⚠️  Skipping {source.name} - needs manual review")
                elif "Merge" in message:
                    if source.is_file():
                        dest_file = target / source.name
                        if dest_file.exists():
                            print(f"⚠️  Skipping {source.name} - already exists")
                        else:
                            target.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(source), str(dest_file))
                            print(f"✓ Merged file: {source.name}")
                    else:
                        # It's a directory - merge contents
                        target.mkdir(parents=True, exist_ok=True)
                        for item in source.iterdir():
                            dest_item = target / item.name
                            if dest_item.exists():
                                print(f"⚠️  Skipping {item.name} - already exists in {target}")
                            else:
                                shutil.move(str(item), str(dest_item))
                                print(f"✓ Merged: {item.name} → {target}")
                        # Remove empty source
                        try:
                            if not any(source.iterdir()):
                                source.rmdir()
                                print(f"✓ Removed empty: {source.name}")
                        except:
                            pass
                elif "Rename" in message:
                    dest_dir = target / target_name
                    if dest_dir.exists():
                        print(f"⚠️  Skipping {source.name} - target already exists")
                    else:
                        target.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(dest_dir))
                        print(f"✓ Renamed: {source.name} → {target_name}")
            except Exception as e:
                print(f"✗ Error: {source.name} - {e}")
    
    return len(consolidations)

def check_orphaned_files():
    """Check for files that should be in subdirectories"""
    print("\n" + "="*80)
    print("CHECKING FOR ORPHANED FILES")
    print("="*80)
    
    # Files that should be organized
    root_files = []
    for ext in ["*.json", "*.sql", "*.md", "*.txt", "*.log", "*.py", "*.sh"]:
        root_files.extend(list(ROOT_DIR.glob(ext)))
    
    # Filter out protected files
    protected = ["README.md", "GPT5_READ_FIRST.md"]
    root_files = [f for f in root_files if f.name not in protected]
    
    if root_files:
        print(f"\n⚠️  Found {len(root_files)} files in root that might need organization:")
        for f in sorted(root_files)[:20]:
            size = f.stat().st_size
            print(f"  {f.name:40} ({size:,} bytes)")
        if len(root_files) > 20:
            print(f"  ... and {len(root_files) - 20} more")
    else:
        print("\n✓ No orphaned files found in root")
    
    return len(root_files)

def main():
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("="*80)
        print("DRY RUN MODE - No changes will be made")
        print("Add --execute flag to actually consolidate")
        print("="*80)
    else:
        print("="*80)
        print("EXECUTION MODE - Consolidating project structure")
        print("="*80)
    
    # Audit structure
    audit_results = audit_project_structure()
    
    # Check for orphaned files
    orphaned_count = check_orphaned_files()
    
    # Consolidate duplicates
    consolidation_count = consolidate_duplicates(dry_run)
    
    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  Expected folders: {len(audit_results['expected'])}")
    print(f"  Duplicates found: {len(audit_results['duplicates'])}")
    print(f"  Unexpected folders: {len(audit_results['unexpected'])}")
    print(f"  Orphaned files: {orphaned_count}")
    print(f"  Consolidations: {consolidation_count}")

if __name__ == "__main__":
    main()

