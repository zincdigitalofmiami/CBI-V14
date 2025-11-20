#!/usr/bin/env python3
"""
Organize loose markdown files in external drive CBI-V14 root directory.
Based on DOCUMENT_ORGANIZATION_RULES.md
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import re

# Base directory
BASE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
ROOT_DIR = BASE_DIR
DOCS_DIR = BASE_DIR / "docs"
ARCHIVE_DIR = BASE_DIR / "archive"

# Protected files (never move)
PROTECTED_FILES = {
    "README.md",
    "GPT5_READ_FIRST.md",
    "CONTRIBUTING.md",
    "LICENSE.md"
}

# Organization rules
ORGANIZATION_RULES = {
    "audits": {
        "patterns": [
            r".*AUDIT.*\.md$",
            r".*_AUDIT_.*\.md$",
            r".*AUDIT_REPORT.*\.md$",
            r".*AUDIT_RESULTS.*\.md$",
            r".*NULL.*AUDIT.*\.md$",
            r".*DATA.*AUDIT.*\.md$",
            r".*COMPREHENSIVE.*AUDIT.*\.md$",
            r".*FORENSIC.*AUDIT.*\.md$",
        ],
        "destination": DOCS_DIR / "audits",
        "exceptions": ["ACTIVE", "CURRENT", "2025"]  # Keep in root if contains these
    },
    "deployment": {
        "patterns": [
            r".*DEPLOY.*\.md$",
            r".*DEPLOYMENT.*\.md$",
            r".*_DEPLOY_.*\.md$",
        ],
        "destination": ARCHIVE_DIR / "deployment-history",
        "exceptions": ["CURRENT", "ACTIVE", "NOW"]
    },
    "migration": {
        "patterns": [
            r".*MIGRATION.*\.md$",
            r".*MIGRATION_.*\.md$",
            r".*_MIGRATION_.*\.md$",
        ],
        "destination": DOCS_DIR / "migration",
        "exceptions": ["CURRENT", "ACTIVE", "NOW"]
    },
    "bigquery": {
        "patterns": [
            r".*BIGQUERY.*\.md$",
            r".*BQ_.*\.md$",
            r".*BQ_.*\.md$",
        ],
        "destination": DOCS_DIR / "reports" / "bigquery",
        "exceptions": []
    },
    "costs": {
        "patterns": [
            r".*COST.*\.md$",
            r".*COSTS.*\.md$",
        ],
        "destination": DOCS_DIR / "reports" / "costs",
        "exceptions": []
    },
    "reports": {
        "patterns": [
            r".*REPORT.*\.md$",
            r".*SUMMARY.*\.md$",
            r".*ANALYSIS.*\.md$",
            r".*INVENTORY.*\.md$",
            r".*COMPLETENESS.*\.md$",
            r".*VERIFICATION.*\.md$",
        ],
        "destination": DOCS_DIR / "reports",
        "exceptions": ["CURRENT", "ACTIVE"]
    },
    "plans": {
        "patterns": [
            r".*PLAN.*\.md$",
            r".*_PLAN_.*\.md$",
            r".*EXECUTION.*PLAN.*\.md$",
            r".*IMPLEMENTATION.*PLAN.*\.md$",
            r".*PHASE.*PLAN.*\.md$",
            r".*\.plan\.md$",
        ],
        "destination": DOCS_DIR / "plans",
        "exceptions": ["CURRENT", "ACTIVE", "WORKING", "LIVE", "NOW", "MASTER", "FRESH_START"]
    },
    "status": {
        "patterns": [
            r".*STATUS.*\.md$",
            r".*HANDOFF.*\.md$",
            r".*UPDATE.*\.md$",
            r".*COMPLETE.*\.md$",
            r".*SUCCESS.*\.md$",
        ],
        "destination": DOCS_DIR / "status",
        "exceptions": ["CURRENT", "ACTIVE", "NOW"]
    },
    "setup": {
        "patterns": [
            r".*SETUP.*\.md$",
            r".*GUIDE.*\.md$",
            r".*CHECKLIST.*\.md$",
            r".*INSTRUCTIONS.*\.md$",
            r".*SCHEDULE.*\.md$",
        ],
        "destination": DOCS_DIR / "setup",
        "exceptions": []
    },
    "architecture": {
        "patterns": [
            r".*ARCHITECTURE.*\.md$",
            r".*DESIGN.*\.md$",
            r".*ORGANIZATION.*\.md$",
            r".*PATTERNS.*\.md$",
            r".*METHODOLOGIES.*\.md$",
        ],
        "destination": DOCS_DIR / "reference",
        "exceptions": ["CURRENT", "ACTIVE"]
    },
    "data": {
        "patterns": [
            r".*DATA.*\.md$",
            r".*SOURCE.*\.md$",
            r".*GAPS.*\.md$",
            r".*RECOVERY.*\.md$",
            r".*COVERAGE.*\.md$",
        ],
        "destination": DOCS_DIR / "reports" / "data",
        "exceptions": ["CURRENT", "ACTIVE", "STRATEGY"]
    },
    "fixes": {
        "patterns": [
            r".*FIX.*\.md$",
            r".*FIXES.*\.md$",
        ],
        "destination": DOCS_DIR / "reports" / "fixes",
        "exceptions": []
    },
    "training": {
        "patterns": [
            r".*TRAINING.*\.md$",
            r".*HORIZON.*\.md$",
        ],
        "destination": DOCS_DIR / "training",
        "exceptions": ["CURRENT", "ACTIVE", "MASTER"]
    },
    "reference": {
        "patterns": [
            r".*REFERENCE.*\.md$",
            r".*CLARIFICATION.*\.md$",
            r".*ANSWERS.*\.md$",
            r".*VALIDATION.*\.md$",
            r".*IMPLEMENTATION.*\.md$",
        ],
        "destination": DOCS_DIR / "reference",
        "exceptions": []
    },
    "instructions": {
        "patterns": [
            r".*DOWNLOAD.*\.md$",
            r".*FETCH.*\.md$",
        ],
        "destination": DOCS_DIR / "setup",
        "exceptions": []
    },
    "execution": {
        "patterns": [
            r".*READY.*EXECUTION.*\.md$",
            r".*READY.*FOR.*\.md$",
        ],
        "destination": DOCS_DIR / "status",
        "exceptions": []
    }
}

def is_recent_file(filepath):
    """Check if file was modified in last 7 days"""
    try:
        mtime = os.path.getmtime(filepath)
        file_date = datetime.fromtimestamp(mtime)
        return (datetime.now() - file_date) < timedelta(days=7)
    except:
        return False

def should_keep_in_root(filename, category_rules):
    """Check if file should stay in root based on exceptions"""
    filename_upper = filename.upper()
    for exception in category_rules.get("exceptions", []):
        if exception.upper() in filename_upper:
            return True
    return False

def categorize_file(filename):
    """Categorize a file based on organization rules"""
    # Check if protected
    if filename in PROTECTED_FILES:
        return None, "PROTECTED"
    
    # Check each category
    for category, rules in ORGANIZATION_RULES.items():
        for pattern in rules["patterns"]:
            if re.match(pattern, filename, re.IGNORECASE):
                # Check exceptions
                if should_keep_in_root(filename, rules):
                    return None, f"KEEP_IN_ROOT ({category})"
                return rules["destination"], category
    
    return None, "UNCATEGORIZED"

def create_directories():
    """Create all necessary directories"""
    directories = set()
    
    # Add all destinations
    for rules in ORGANIZATION_RULES.values():
        directories.add(rules["destination"])
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {directory}")

def organize_files(dry_run=True):
    """Organize files based on rules"""
    root_files = list(ROOT_DIR.glob("*.md"))
    
    moves = []
    protected = []
    keep_in_root = []
    uncategorized = []
    
    for filepath in root_files:
        filename = filepath.name
        destination, category = categorize_file(filename)
        
        if category == "PROTECTED":
            protected.append((filename, category))
        elif category.startswith("KEEP_IN_ROOT"):
            keep_in_root.append((filename, category))
        elif destination:
            moves.append((filepath, destination, category))
        else:
            uncategorized.append((filename, category))
    
    # Print summary
    print("\n" + "="*80)
    print("MARKDOWN FILE ORGANIZATION SUMMARY")
    print("="*80)
    print(f"\nTotal files found: {len(root_files)}")
    print(f"Protected (staying in root): {len(protected)}")
    print(f"Keep in root (active/recent): {len(keep_in_root)}")
    print(f"Files to move: {len(moves)}")
    print(f"Uncategorized: {len(uncategorized)}")
    
    if protected:
        print("\n📌 PROTECTED FILES (staying in root):")
        for filename, category in protected:
            print(f"  ✓ {filename}")
    
    if keep_in_root:
        print("\n📌 KEEPING IN ROOT (active/recent):")
        for filename, category in keep_in_root:
            print(f"  ✓ {filename} - {category}")
    
    if moves:
        print("\n📦 FILES TO MOVE:")
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
        print("\n⚠️  UNCATEGORIZED FILES:")
        for filename, category in uncategorized:
            print(f"  ? {filename} - {category}")
    
    # Execute moves if not dry run
    if not dry_run:
        print("\n" + "="*80)
        print("EXECUTING MOVES...")
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
    
    return {
        "protected": len(protected),
        "keep_in_root": len(keep_in_root),
        "moved": len(moves) if not dry_run else 0,
        "uncategorized": len(uncategorized)
    }

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
    
    print("\nCategorizing files...")
    results = organize_files(dry_run=dry_run)
    
    print("\n" + "="*80)
    print("ORGANIZATION COMPLETE")
    print("="*80)
    print(f"\nSummary:")
    print(f"  Protected: {results['protected']}")
    print(f"  Kept in root: {results['keep_in_root']}")
    print(f"  Moved: {results['moved']}")
    print(f"  Uncategorized: {results['uncategorized']}")

if __name__ == "__main__":
    main()

