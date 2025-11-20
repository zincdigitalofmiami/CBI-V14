#!/usr/bin/env python3
"""
Phase 8: Update ingestion scripts to write to new table names.
Maps old forecasting_data_warehouse.* tables to new raw_intelligence.* names.
"""
import re
from pathlib import Path
from typing import Dict, Tuple

# Mapping from old table names to new names (from TABLE_MAPPING_MATRIX.md)
TABLE_MAPPING: Dict[str, str] = {
    # Raw intelligence mappings
    'forecasting_data_warehouse.baltic_dry_index': 'raw_intelligence.shipping_baltic_dry_index',
    'forecasting_data_warehouse.biofuel_policy': 'raw_intelligence.policy_biofuel',
    'forecasting_data_warehouse.china_soybean_imports': 'raw_intelligence.trade_china_soybean_imports',
    'forecasting_data_warehouse.crude_oil_prices': 'raw_intelligence.commodity_crude_oil_prices',
    'forecasting_data_warehouse.economic_indicators': 'raw_intelligence.macro_economic_indicators',
    'forecasting_data_warehouse.news_intelligence': 'raw_intelligence.news_sentiments',
    'forecasting_data_warehouse.palm_oil_prices': 'raw_intelligence.commodity_palm_oil_prices',
    'forecasting_data_warehouse.soybean_oil_prices': 'raw_intelligence.commodity_soybean_oil_prices',
    'forecasting_data_warehouse.vix_data': 'raw_intelligence.market_vix_data',
    'forecasting_data_warehouse.vix_daily': 'raw_intelligence.market_vix_daily',
    # Add more mappings as needed
}

def get_repo_root():
    """Find repository root."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "src" / "ingestion").exists():
            return parent
    return current_path.parent.parent

def update_ingestion_script(file_path: Path) -> Tuple[bool, list]:
    """Update a single ingestion script."""
    content = file_path.read_text()
    original = content
    changes = []
    
    # Update table references
    for old_table, new_table in TABLE_MAPPING.items():
        # Pattern 1: Full reference with backticks
        if old_table in content:
            content = content.replace(old_table, new_table)
            changes.append(f"{old_table.split('.')[-1]} → {new_table.split('.')[-1]}")
        
        # Pattern 2: Just dataset.table in strings
        old_dataset, old_table_name = old_table.split('.')
        new_dataset, new_table_name = new_table.split('.')
        
        # Update dataset references
        if f'"{old_dataset}' in content or f"'{old_dataset}" in content:
            content = re.sub(
                rf'(["\']){old_dataset}\.',
                rf'\1{new_dataset}.',
                content
            )
            if old_table_name not in [c.split('→')[0].strip() for c in changes]:
                changes.append(f"{old_dataset} → {new_dataset}")
        
        # Update table name in variable assignments
        if f'table_id = "{old_table_name}"' in content or f"table_id = '{old_table_name}'" in content:
            # Keep old table name for now (may be used in multiple places)
            # Just update the dataset reference
            pass
    
    if content != original:
        file_path.write_text(content)
        return True, changes
    return False, []

def main():
    """Update all ingestion scripts."""
    repo_root = get_repo_root()
    ingestion_dir = repo_root / "src" / "ingestion"
    
    print("="*80)
    print("PHASE 8: UPDATING INGESTION SCRIPTS")
    print("="*80)
    print()
    print("⚠️  NOTE: This is a conservative update.")
    print("    Only updates dataset references (forecasting_data_warehouse → raw_intelligence).")
    print("    Table names may need manual review based on TABLE_MAPPING_MATRIX.md")
    print()
    
    updated_files = []
    
    for py_file in sorted(ingestion_dir.glob("ingest_*.py")):
        rel_path = py_file.relative_to(repo_root)
        print(f"Checking {rel_path}...")
        
        updated, changes = update_ingestion_script(py_file)
        
        if updated:
            updated_files.append((py_file, changes))
            print(f"  ✅ Updated: {', '.join(set(changes))}")
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
            for change in set(changes):
                print(f"    • {change}")
    
    print("\n⚠️  NOTE: Manual review recommended for:")
    print("    • Table name mappings (see TABLE_MAPPING_MATRIX.md)")
    print("    • Schema compatibility")
    print("    • Any hardcoded table references")

if __name__ == "__main__":
    main()







