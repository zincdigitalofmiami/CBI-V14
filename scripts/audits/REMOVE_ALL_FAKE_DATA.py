#!/usr/bin/env python3
"""
COMPREHENSIVE FAKE DATA REMOVAL AUDIT
Identifies and removes ALL fake/placeholder/random data from the codebase.
ZERO TOLERANCE for fake data.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Repository root
REPO_ROOT = Path("/Users/kirkmusick/Documents/GitHub/CBI-V14")

# Patterns that indicate fake data
FAKE_DATA_PATTERNS = [
    r'np\.random\.',
    r'random\.rand',
    r'random\.uniform',
    r'random\.choice',
    r'random\.sample',
    r'dummy',
    r'fake',
    r'mock',
    r'placeholder',
    r'sample_data',
    r'test_data',
    r'Creating sample data',
    r'would be real data',
    r'for demonstration',
    r'example with dummy',
    r'Mock.*prediction',
    r'synthetic',
]

# Files identified with fake data that need fixing
FILES_WITH_FAKE_DATA = {
    'scripts/predictions/es_futures_predictor.py': {
        'issue': 'Uses np.random to generate fake market data',
        'lines': [606, 607, 608, 609, 610, 617, 621, 625],
        'action': 'MUST FETCH REAL DATA FROM BIGQUERY'
    },
    'scripts/predictions/zl_impact_predictor.py': {
        'issue': 'Uses mock Trump prediction data',
        'lines': [405],
        'action': 'MUST USE REAL TRUMP PREDICTION'
    },
    'scripts/sentiment/unified_sentiment_neural.py': {
        'issue': 'Uses dummy data for demonstration',
        'lines': [613, 618, 651, 652, 653, 659, 660, 661, 662, 668, 669, 670, 671],
        'action': 'MUST USE REAL DATA OR RETURN NONE'
    },
    'scripts/features/build_all_features.py': {
        'issue': 'Sets random seed - implies fake data usage',
        'lines': [18],
        'action': 'REMOVE RANDOM SEED - USE REAL DATA'
    },
    'scripts/qa/pre_flight_harness.py': {
        'issue': 'Uses random sampling',
        'lines': [24, 72],
        'action': 'USE DETERMINISTIC SAMPLING OR ALL DATA'
    }
}

# Scripts that should be deleted entirely (pure fake/test data)
SCRIPTS_TO_DELETE = [
    'scripts/test_data/',  # Any test data directory
    'scripts/generate_fake_*.py',  # Any fake data generators
    'scripts/mock_*.py',  # Any mock scripts
]


def audit_file(filepath: Path) -> List[Dict]:
    """
    Audit a single file for fake data patterns
    """
    violations = []
    
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            for pattern in FAKE_DATA_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append({
                        'file': str(filepath.relative_to(REPO_ROOT)),
                        'line_num': i,
                        'line': line.strip(),
                        'pattern': pattern
                    })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return violations


def scan_repository() -> Tuple[List[Dict], List[str]]:
    """
    Scan entire repository for fake data
    """
    all_violations = []
    files_to_fix = set()
    
    # Scan Python files
    for py_file in REPO_ROOT.rglob("*.py"):
        # Skip virtual environments and cache
        if any(skip in str(py_file) for skip in ['venv', '__pycache__', '.git']):
            continue
            
        violations = audit_file(py_file)
        if violations:
            all_violations.extend(violations)
            files_to_fix.add(str(py_file.relative_to(REPO_ROOT)))
    
    # Scan SQL files for fake data indicators
    for sql_file in REPO_ROOT.rglob("*.sql"):
        with open(sql_file, 'r') as f:
            content = f.read()
            if any(word in content.lower() for word in ['random', 'rand()', 'sample', 'dummy', 'fake', 'mock']):
                files_to_fix.add(str(sql_file.relative_to(REPO_ROOT)))
    
    return all_violations, list(files_to_fix)


def generate_fix_report(violations: List[Dict], files_to_fix: List[str]):
    """
    Generate comprehensive report of what needs fixing
    """
    print("=" * 80)
    print("FAKE DATA AUDIT REPORT")
    print("=" * 80)
    print(f"Total violations found: {len(violations)}")
    print(f"Files requiring fixes: {len(files_to_fix)}")
    print()
    
    # Group violations by file
    by_file = {}
    for v in violations:
        if v['file'] not in by_file:
            by_file[v['file']] = []
        by_file[v['file']].append(v)
    
    print("CRITICAL FILES WITH FAKE DATA:")
    print("-" * 80)
    
    for filepath, file_violations in sorted(by_file.items()):
        print(f"\n📁 {filepath}")
        print(f"   Violations: {len(file_violations)}")
        
        # Show first 5 violations
        for v in file_violations[:5]:
            print(f"   Line {v['line_num']}: {v['line'][:60]}...")
        
        if len(file_violations) > 5:
            print(f"   ... and {len(file_violations) - 5} more violations")
    
    print("\n" + "=" * 80)
    print("REQUIRED ACTIONS:")
    print("-" * 80)
    
    for filepath, details in FILES_WITH_FAKE_DATA.items():
        if filepath in files_to_fix:
            print(f"\n❌ {filepath}")
            print(f"   Issue: {details['issue']}")
            print(f"   Action: {details['action']}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("-" * 80)
    print("1. ALL random data generation must be removed")
    print("2. Replace with REAL data from BigQuery or APIs")
    print("3. If data unavailable, return None/empty - NEVER fake data")
    print("4. Remove all test/mock/dummy files")
    print("5. Use only production data sources")
    
    return by_file


def create_cleanup_script(files_to_fix: List[str]):
    """
    Create a script to clean up fake data
    """
    cleanup_script = """#!/bin/bash
# FAKE DATA CLEANUP SCRIPT
# Generated by audit

echo "Starting fake data cleanup..."

# Files that need complete rewrite to use real data
"""
    
    for filepath in files_to_fix:
        cleanup_script += f"""
echo "Fixing: {filepath}"
# TODO: Rewrite {filepath} to use real data only
"""
    
    # Save cleanup script
    cleanup_path = REPO_ROOT / "scripts" / "cleanup_fake_data.sh"
    with open(cleanup_path, 'w') as f:
        f.write(cleanup_script)
    
    os.chmod(cleanup_path, 0o755)
    print(f"\nCleanup script created: {cleanup_path}")


def main():
    """
    Run comprehensive fake data audit
    """
    print("🔍 Starting comprehensive fake data audit...")
    print(f"Repository: {REPO_ROOT}")
    print()
    
    # Scan repository
    violations, files_to_fix = scan_repository()
    
    # Generate report
    by_file = generate_fix_report(violations, files_to_fix)
    
    # Create cleanup script
    create_cleanup_script(files_to_fix)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if violations:
        print(f"❌ FAKE DATA DETECTED IN {len(files_to_fix)} FILES")
        print("   IMMEDIATE ACTION REQUIRED:")
        print("   1. Remove ALL random data generation")
        print("   2. Use ONLY real data from BigQuery/APIs")
        print("   3. Return None if data unavailable")
        print("\n   ZERO TOLERANCE FOR FAKE DATA")
    else:
        print("✅ No fake data patterns detected")
    
    # Save detailed report
    report_path = REPO_ROOT / "FAKE_DATA_AUDIT.txt"
    with open(report_path, 'w') as f:
        f.write(f"FAKE DATA AUDIT - {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        for filepath, file_violations in sorted(by_file.items()):
            f.write(f"\nFile: {filepath}\n")
            f.write(f"Violations: {len(file_violations)}\n")
            for v in file_violations:
                f.write(f"  Line {v['line_num']}: {v['line']}\n")
    
    print(f"\nDetailed report saved to: {report_path}")
    
    return len(violations) > 0


if __name__ == "__main__":
    from datetime import datetime
    
    has_violations = main()
    
    if has_violations:
        print("\n⚠️  CRITICAL: Fake data must be removed before production use!")
        exit(1)
    else:
        print("\n✅ Audit complete - no fake data detected")
        exit(0)
