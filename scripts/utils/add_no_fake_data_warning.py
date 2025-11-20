#!/usr/bin/env python3
"""
Add "NO FAKE DATA" warning to all plans, markdown, and SQL files.
This ensures no placeholder or fake data is used anywhere in the codebase.
"""

import os
from pathlib import Path
import re

# Standard warning text
WARNING_MD = """---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

"""

WARNING_SQL = """-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

"""

WARNING_YAML = """# ⚠️ CRITICAL: NO FAKE DATA ⚠️
# This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
# All data must come from authenticated APIs, official sources, or validated historical records.
#

"""

def has_warning(content: str, warning_type: str) -> bool:
    """Check if file already has the warning."""
    if warning_type == "md":
        return "NO FAKE DATA" in content or "⚠️ CRITICAL: NO FAKE DATA" in content
    elif warning_type == "sql":
        return "-- ⚠️ CRITICAL: NO FAKE DATA" in content
    elif warning_type == "yaml":
        return "# ⚠️ CRITICAL: NO FAKE DATA" in content
    return False

def add_warning_to_file(file_path: Path, warning_type: str):
    """Add warning to a file if it doesn't already have it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if has_warning(content, warning_type):
            print(f"  ⏭️  Already has warning: {file_path}")
            return False
        
        # Determine warning text
        if warning_type == "md":
            warning = WARNING_MD
        elif warning_type == "sql":
            warning = WARNING_SQL
        elif warning_type == "yaml":
            warning = WARNING_YAML
        else:
            return False
        
        # Add warning at the beginning (after frontmatter if present)
        if warning_type == "md" and content.startswith("---"):
            # Find end of frontmatter
            end_idx = content.find("\n---\n", 3)
            if end_idx > 0:
                new_content = content[:end_idx+5] + warning + content[end_idx+5:]
            else:
                new_content = warning + content
        else:
            new_content = warning + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ Added warning: {file_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def main():
    """Process all markdown, SQL, and YAML files."""
    root = Path(__file__).parent.parent.parent
    
    # Directories to process
    dirs_to_process = [
        root / "docs",
        root / "scripts",
        root / "config",
        root / "sql",
        root / "registry",
    ]
    
    # Also process root-level files
    root_files = list(root.glob("*.md")) + list(root.glob("*.sql")) + list(root.glob("*.yaml"))
    
    md_count = 0
    sql_count = 0
    yaml_count = 0
    
    print("=" * 80)
    print("ADDING 'NO FAKE DATA' WARNING TO ALL FILES")
    print("=" * 80)
    print()
    
    # Process markdown files
    print("Processing Markdown files...")
    for dir_path in dirs_to_process:
        if dir_path.exists():
            for md_file in dir_path.rglob("*.md"):
                if add_warning_to_file(md_file, "md"):
                    md_count += 1
    
    # Process root-level markdown files
    for md_file in root_files:
        if md_file.suffix == ".md" and md_file.exists():
            if add_warning_to_file(md_file, "md"):
                md_count += 1
    
    print()
    print("Processing SQL files...")
    for dir_path in dirs_to_process:
        if dir_path.exists():
            for sql_file in dir_path.rglob("*.sql"):
                if add_warning_to_file(sql_file, "sql"):
                    sql_count += 1
    
    # Process root-level SQL files
    for sql_file in root_files:
        if sql_file.suffix == ".sql" and sql_file.exists():
            if add_warning_to_file(sql_file, "sql"):
                sql_count += 1
    
    print()
    print("Processing YAML files...")
    for dir_path in dirs_to_process:
        if dir_path.exists():
            for yaml_file in dir_path.rglob("*.yaml"):
                if add_warning_to_file(yaml_file, "yaml"):
                    yaml_count += 1
            for yaml_file in dir_path.rglob("*.yml"):
                if add_warning_to_file(yaml_file, "yaml"):
                    yaml_count += 1
    
    # Process root-level YAML files
    for yaml_file in root_files:
        if yaml_file.suffix in [".yaml", ".yml"] and yaml_file.exists():
            if add_warning_to_file(yaml_file, "yaml"):
                yaml_count += 1
    
    print()
    print("=" * 80)
    print(f"✅ COMPLETE: Added warnings to {md_count} markdown, {sql_count} SQL, {yaml_count} YAML files")
    print("=" * 80)

if __name__ == "__main__":
    main()

