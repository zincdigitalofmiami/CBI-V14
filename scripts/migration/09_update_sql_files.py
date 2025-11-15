#!/usr/bin/env python3
"""
Phase 5: Update SQL files to use new naming convention.
Updates references from production_training_data_* to training.zl_training_*
"""
import re
from pathlib import Path

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "config" / "bigquery").exists():
            return parent
    return current_path.parent.parent

def update_sql_file(file_path: Path):
    """Update a single SQL file."""
    content = file_path.read_text()
    original = content
    changes = []
    
    # Update table references: models_v4.production_training_data_* → training.zl_training_prod_allhistory_*
    if 'production_training_data_' in content:
        # Pattern 1: Full reference with dataset
        content = re.sub(
            r'`cbi-v14\.models_v4\.production_training_data_(\w+)`',
            r'`cbi-v14.training.zl_training_prod_allhistory_\1`',
            content
        )
        changes.append("table reference")
        
        # Pattern 2: Just table name (in comments or strings)
        content = re.sub(
            r'production_training_data_(\w+)',
            r'zl_training_prod_allhistory_\1',
            content
        )
        changes.append("table name")
    
    if content != original:
        file_path.write_text(content)
        return True, changes
    return False, []

def main():
    """Update all SQL files."""
    repo_root = get_repo_root()
    sql_dir = repo_root / "config" / "bigquery" / "bigquery-sql"
    
    print("="*80)
    print("PHASE 5: UPDATING SQL FILES")
    print("="*80)
    print()
    
    updated_files = []
    skipped_files = [
        "BUILD_TRAINING_TABLES_NEW_NAMING.sql",  # New file, skip
        "ULTIMATE_DATA_CONSOLIDATION.sql",  # Keep as legacy reference
    ]
    
    for sql_file in sorted(sql_dir.rglob("*.sql")):
        if sql_file.name in skipped_files:
            print(f"Skipping {sql_file.relative_to(repo_root)} (legacy/new file)")
            continue
        
        rel_path = sql_file.relative_to(repo_root)
        print(f"Checking {rel_path}...")
        
        updated, changes = update_sql_file(sql_file)
        
        if updated:
            updated_files.append((sql_file, changes))
            print(f"  ✅ Updated: {', '.join(changes)}")
        else:
            print(f"  ⏭️  No changes needed")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Updated: {len(updated_files)} files")
    
    if updated_files:
        print("\nUpdated files:")
        for f, changes in updated_files:
            print(f"  - {f.relative_to(repo_root)}")
            print(f"    Changes: {', '.join(changes)}")
    
    print("\n⚠️  NOTE: ULTIMATE_DATA_CONSOLIDATION.sql kept as legacy reference")
    print("    New builds should use BUILD_TRAINING_TABLES_NEW_NAMING.sql")

if __name__ == "__main__":
    main()

