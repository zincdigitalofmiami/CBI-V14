#!/usr/bin/env python3
"""
Update all training scripts to use new naming convention.
Updates file paths and table references.
"""
import re
from pathlib import Path

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "src" / "training").exists():
            return parent
    return current_path.parent.parent

def update_file_paths(file_path: Path):
    """Update file paths in a Python script."""
    content = file_path.read_text()
    original = content
    
    # Update data path: production_training_data_{horizon}.parquet → zl_training_{surface}_allhistory_{horizon}.parquet
    content = re.sub(
        r'production_training_data_(\w+)\.parquet',
        r'zl_training_prod_allhistory_\1.parquet',
        content
    )
    
    # Update model save paths: Models/local/baselines → Models/local/horizon_{h}/prod/baselines/{model}_v001/
    # This is more complex and will need manual review
    
    # Update BigQuery table references: models_v4.production_training_data_* → training.zl_training_prod_allhistory_*
    content = re.sub(
        r'models_v4\.production_training_data_(\w+)',
        r'training.zl_training_prod_allhistory_\1',
        content
    )
    
    if content != original:
        file_path.write_text(content)
        return True
    return False

def main():
    """Update all training scripts."""
    repo_root = get_repo_root()
    training_dir = repo_root / "src" / "training"
    
    print("="*80)
    print("UPDATING TRAINING SCRIPTS")
    print("="*80)
    print()
    
    updated_files = []
    
    # Find all Python files in training directory
    for py_file in training_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        
        print(f"Checking {py_file.relative_to(repo_root)}...")
        if update_file_paths(py_file):
            updated_files.append(py_file)
            print(f"  ✅ Updated")
        else:
            print(f"  ⏭️  No changes needed")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Updated: {len(updated_files)} files")
    
    if updated_files:
        print("\nUpdated files:")
        for f in updated_files:
            print(f"  - {f.relative_to(repo_root)}")
    
    print("\n⚠️  NOTE: Model save paths need manual update to new structure:")
    print("    Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/")

if __name__ == "__main__":
    main()

