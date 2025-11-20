#!/usr/bin/env python3
"""
Comprehensive update of all training scripts to use new naming convention.
Updates data paths, model save paths, and BigQuery references.
"""
import re
from pathlib import Path
from datetime import datetime

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "src" / "training").exists():
            return parent
    return current_path.parent.parent

def update_training_script(file_path: Path):
    """Update a single training script."""
    content = file_path.read_text()
    original = content
    changes = []
    
    # 1. Update data path: production_training_data_{h}.parquet → zl_training_prod_allhistory_{h}.parquet
    if 'production_training_data_' in content:
        content = re.sub(
            r'production_training_data_(\w+)\.parquet',
            r'zl_training_prod_allhistory_\1.parquet',
            content
        )
        changes.append("data path")
    
    # 2. Update model save paths based on directory
    if 'baselines' in str(file_path):
        # baselines → horizon_{h}/prod/baselines
        content = re.sub(
            r'Models/local/baselines',
            r'Models/local/horizon_{args.horizon}/prod/baselines',
            content
        )
        changes.append("model path (baselines)")
    elif 'advanced' in str(file_path):
        # advanced → horizon_{h}/prod/advanced
        content = re.sub(
            r'Models/local/advanced',
            r'Models/local/horizon_{args.horizon}/prod/advanced',
            content
        )
        changes.append("model path (advanced)")
    elif 'ensemble' in str(file_path):
        # ensemble → horizon_{h}/prod/ensemble
        content = re.sub(
            r'Models/local',
            r'Models/local/horizon_{args.horizon}/prod/ensemble',
            content
        )
        changes.append("model path (ensemble)")
    elif 'regime' in str(file_path):
        # regime → horizon_{h}/prod/regime
        content = re.sub(
            r'Models/local/regime',
            r'Models/local/horizon_{args.horizon}/prod/regime',
            content
        )
        changes.append("model path (regime)")
    
    # 3. Update BigQuery table references
    if 'models_v4.production_training_data' in content:
        content = re.sub(
            r'models_v4\.production_training_data_(\w+)',
            r'training.zl_training_prod_allhistory_\1',
            content
        )
        changes.append("BigQuery table")
    
    # 4. Add surface parameter support (if main function exists)
    if 'def main():' in content and 'surface' not in content:
        # Add surface parameter to argparse if it doesn't exist
        if 'parser.add_argument' in content and '--surface' not in content:
            # Find the horizon argument and add surface after it
            horizon_match = re.search(r'parser\.add_argument\(["\']--horizon["\']', content)
            if horizon_match:
                insert_pos = content.find('\n', horizon_match.end())
                surface_arg = '\n    parser.add_argument("--surface", choices=["prod", "full"], default="prod",\n                       help="Surface type: prod (≈290 cols) or full (1,948+ cols)")'
                content = content[:insert_pos] + surface_arg + content[insert_pos:]
                changes.append("surface parameter")
    
    if content != original:
        file_path.write_text(content)
        return True, changes
    return False, []

def update_model_save_patterns(file_path: Path):
    """Update model save patterns to new structure."""
    content = file_path.read_text()
    original = content
    
    # Pattern 1: model_dir / f"{model_name}_{horizon}.pkl"
    # → model_dir / f"{model_name}_v001" / "model.bin"
    patterns = [
        (r'model_dir\s*/\s*f["\']([^"\']+)_\{horizon\}\.pkl["\']',
         r'model_dir / "\1_v001" / "model.bin"'),
        (r'model_dir\s*/\s*f["\']([^"\']+)_\{horizon\}_importance\.csv["\']',
         r'model_dir / "\1_v001" / "feature_importance.csv"'),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
    
    # Add model subdirectory creation and metadata saving
    # This is complex and may need manual review
    
    if content != original:
        file_path.write_text(content)
        return True
    return False

def main():
    """Update all training scripts."""
    repo_root = get_repo_root()
    training_dir = repo_root / "src" / "training"
    
    print("="*80)
    print("UPDATING ALL TRAINING SCRIPTS")
    print("="*80)
    print()
    
    updated_files = []
    skipped_files = ["__init__.py", "config_mlflow.py", "gpu_optimization_template.py", 
                     "setup_tensorflow_cpu.py", "feature_catalog.py"]
    
    for py_file in sorted(training_dir.rglob("*.py")):
        if py_file.name in skipped_files:
            continue
        
        rel_path = py_file.relative_to(repo_root)
        print(f"Updating {rel_path}...")
        
        updated, changes = update_training_script(py_file)
        
        if updated:
            updated_files.append((py_file, changes))
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
    
    print("\n⚠️  NOTE: Model save patterns may need manual review")
    print("    New structure: Models/local/horizon_{h}/{surface}/{family}/{model}_v{ver}/")
    print("    Artifacts: model.bin, columns_used.txt, run_id.txt, feature_importance.csv")

if __name__ == "__main__":
    main()







