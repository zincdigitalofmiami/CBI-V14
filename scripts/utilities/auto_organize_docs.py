#!/usr/bin/env python3
"""
CBI-V14 Automatic Document Organization System
Automatically categorizes and moves MD files to appropriate folders based on naming patterns
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path("/Users/zincdigital/CBI-V14")

# Organization rules - Pattern matching for automatic categorization
ORGANIZATION_RULES = {
    # KEEP IN ROOT - Critical active documents (never move)
    "root_protected": [
        r"^README\.md$",
        r"^CONTRIBUTING\.md$",
        r"^LICENSE\.md$",
        r"^CBI_V14.*PLAN\.md$",
        r"^HANDOFF.*\.md$",
        r"^MASTER.*PLAN\.md$",
    ],
    
    # AUDITS -> docs/audits/
    "audits": [
        r".*AUDIT.*\.md$",
        r".*_AUDIT_.*\.md$",
        r".*AUDIT_REPORT.*\.md$",
        r".*AUDIT_RESULTS.*\.md$",
        r".*NULL.*AUDIT.*\.md$",
        r".*DATA.*AUDIT.*\.md$",
        r".*COMPREHENSIVE.*AUDIT.*\.md$",
    ],
    
    # PLANS -> docs/older-plans/ (completed) or ROOT (active)
    "plans": [
        r".*PLAN\.md$",
        r".*_PLAN_.*\.md$",
        r".*EXECUTION.*PLAN.*\.md$",
        r".*IMPLEMENTATION.*PLAN.*\.md$",
        r".*PHASE.*PLAN.*\.md$",
    ],
    
    # CODE REVIEWS -> docs/reference-archive/
    "code_reviews": [
        r".*REVIEW\.md$",
        r".*CODE.*REVIEW.*\.md$",
        r".*_REVIEW_.*\.md$",
        r".*DRY.*TEST.*\.md$",
    ],
    
    # DEPLOYMENT DOCS -> archive/deployment-history/
    "deployment": [
        r".*DEPLOY.*\.md$",
        r".*DEPLOYMENT.*\.md$",
        r".*_DEPLOY_.*\.md$",
    ],
    
    # SYSTEM REFERENCE -> docs/
    "system_docs": [
        r".*README.*\.md$",
        r".*DOCUMENTATION.*\.md$",
        r".*REFERENCE.*\.md$",
        r".*INTEGRATION.*\.md$",
        r".*SYSTEM.*\.md$",
        r".*API.*REFERENCE.*\.md$",
        r".*GUIDE.*\.md$",
    ],
    
    # ANALYSIS/REPORTS -> docs/audits/ or docs/reference-archive/
    "analysis": [
        r".*ANALYSIS.*\.md$",
        r".*REPORT.*\.md$",
        r".*SUMMARY.*\.md$",
        r".*INVESTIGATION.*\.md$",
        r".*ASSESSMENT.*\.md$",
    ],
    
    # STATUS UPDATES -> Keep latest in root, archive older
    "status": [
        r".*STATUS.*\.md$",
        r".*HANDOFF.*\.md$",
        r".*UPDATE.*\.md$",
    ],
}

# Destination folders for each category
DESTINATIONS = {
    "audits": "docs/audits/",
    "plans": "docs/older-plans/",  # Will check if should stay in root
    "code_reviews": "docs/reference-archive/",
    "deployment": "archive/deployment-history/",
    "system_docs": "docs/",
    "analysis": "docs/audits/",
    "status": "docs/",  # Will check if most recent
}

# Keywords that indicate a document is ACTIVE and should stay in root
ACTIVE_KEYWORDS = [
    "CURRENT", "ACTIVE", "WORKING", "LIVE", "NOW",
    datetime.now().strftime("%Y"),  # Current year
    "V14", "MASTER", "MAIN"
]


def is_protected(filename: str) -> bool:
    """Check if file should NEVER be moved from root"""
    for pattern in ORGANIZATION_RULES["root_protected"]:
        if re.match(pattern, filename, re.IGNORECASE):
            return True
    return False


def is_active_document(filepath: Path) -> bool:
    """Check if document appears to be active/current"""
    filename = filepath.name.upper()
    
    # Check filename for active keywords
    for keyword in ACTIVE_KEYWORDS:
        if keyword.upper() in filename:
            return True
    
    # Check if file was modified in last 7 days
    if filepath.exists():
        mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        days_old = (datetime.now() - mod_time).days
        if days_old < 7:
            return True
    
    # Check first few lines of content for active indicators
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            header = f.read(500).upper()
            if any(keyword.upper() in header for keyword in ["ACTIVE", "CURRENT", "IN PROGRESS", "WORKING"]):
                return True
    except:
        pass
    
    return False


def categorize_file(filename: str, filepath: Path) -> tuple:
    """
    Categorize a markdown file and return (category, destination)
    Returns (None, None) if file should stay in current location
    """
    # Protected files stay in root
    if is_protected(filename):
        return ("protected", None)
    
    # Check each category
    for category, patterns in ORGANIZATION_RULES.items():
        if category == "root_protected":
            continue
            
        for pattern in patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                # Special handling for plans - keep active ones in root
                if category == "plans" and is_active_document(filepath):
                    return ("active_plan", None)
                
                # Special handling for status - keep most recent in root
                if category == "status":
                    if is_active_document(filepath):
                        return ("active_status", None)
                    else:
                        return (category, "docs/")
                
                # Return destination from mapping
                destination = DESTINATIONS.get(category)
                return (category, destination)
    
    # No match - check if it's in root and looks like reference material
    if filepath.parent == PROJECT_ROOT:
        # If it's not protected and not categorized, it might be reference
        return ("uncategorized", "docs/")
    
    return (None, None)


def organize_markdown_files(dry_run=True, verbose=True):
    """
    Scan project root for markdown files and organize them
    
    Args:
        dry_run: If True, only show what would be done without moving files
        verbose: Print detailed information
    """
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║     CBI-V14 AUTOMATIC DOCUMENT ORGANIZATION SYSTEM             ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be moved\n")
    else:
        print("⚠️  LIVE MODE - Files will be moved!\n")
    
    # Scan root directory for markdown files
    root_md_files = list(PROJECT_ROOT.glob("*.md"))
    
    if not root_md_files:
        print("✅ No markdown files found in root directory\n")
        return
    
    print(f"📄 Found {len(root_md_files)} markdown files in root\n")
    
    # Track actions
    actions = {
        "protected": [],
        "active_plan": [],
        "active_status": [],
        "to_move": [],
        "uncategorized": []
    }
    
    # Categorize each file
    for filepath in root_md_files:
        filename = filepath.name
        category, destination = categorize_file(filename, filepath)
        
        if category == "protected":
            actions["protected"].append(filename)
        elif category == "active_plan":
            actions["active_plan"].append(filename)
        elif category == "active_status":
            actions["active_status"].append(filename)
        elif destination:
            actions["to_move"].append((filename, destination))
        else:
            actions["uncategorized"].append(filename)
    
    # Report findings
    print("═══════════════════════════════════════════════════════════════\n")
    
    if actions["protected"]:
        print(f"🔒 PROTECTED - Keep in Root ({len(actions['protected'])}):")
        for f in actions["protected"]:
            print(f"   ✓ {f}")
        print()
    
    if actions["active_plan"]:
        print(f"📋 ACTIVE PLANS - Keep in Root ({len(actions['active_plan'])}):")
        for f in actions["active_plan"]:
            print(f"   ✓ {f}")
        print()
    
    if actions["active_status"]:
        print(f"📊 ACTIVE STATUS - Keep in Root ({len(actions['active_status'])}):")
        for f in actions["active_status"]:
            print(f"   ✓ {f}")
        print()
    
    if actions["to_move"]:
        print(f"📦 TO ORGANIZE - Move to Folders ({len(actions['to_move'])}):")
        for filename, dest in actions["to_move"]:
            print(f"   → {filename}")
            print(f"      Destination: {dest}")
            
            if not dry_run:
                # Create destination directory if needed
                dest_path = PROJECT_ROOT / dest
                dest_path.mkdir(parents=True, exist_ok=True)
                
                # Move file
                src = PROJECT_ROOT / filename
                dst = dest_path / filename
                
                # Handle duplicates
                if dst.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dst = dest_path / f"{filename.replace('.md', '')}_{timestamp}.md"
                
                shutil.move(str(src), str(dst))
                print(f"      ✅ Moved to {dst.relative_to(PROJECT_ROOT)}")
        print()
    
    if actions["uncategorized"]:
        print(f"❓ UNCATEGORIZED - Review Manually ({len(actions['uncategorized'])}):")
        for f in actions["uncategorized"]:
            print(f"   ? {f}")
        print()
    
    # Summary
    print("═══════════════════════════════════════════════════════════════")
    print("📊 SUMMARY:")
    print(f"   • Protected (stay in root): {len(actions['protected'])}")
    print(f"   • Active plans (stay in root): {len(actions['active_plan'])}")
    print(f"   • Active status (stay in root): {len(actions['active_status'])}")
    print(f"   • Organized: {len(actions['to_move'])}")
    print(f"   • Needs manual review: {len(actions['uncategorized'])}")
    print("═══════════════════════════════════════════════════════════════\n")
    
    if dry_run and actions["to_move"]:
        print("💡 To execute moves, run: python scripts/auto_organize_docs.py --execute\n")


if __name__ == "__main__":
    import sys
    
    # Check for --execute flag
    execute = "--execute" in sys.argv or "-x" in sys.argv
    
    organize_markdown_files(dry_run=not execute, verbose=True)







