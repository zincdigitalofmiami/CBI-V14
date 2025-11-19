#!/usr/bin/env python3
"""
BigQuery Current State Scanner
Date: November 18, 2025
Purpose: Automatically scan BigQuery and compare against PRODUCTION_READY_BQ_SCHEMA.sql
"""

import os
import re
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"
SCHEMA_FILE = "PRODUCTION_READY_BQ_SCHEMA.sql"
REPORT_FILE = "BQ_CURRENT_STATE_REPORT.md"

def get_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)

def parse_schema_file():
    """Parse PRODUCTION_READY_BQ_SCHEMA.sql to extract expected datasets and tables"""
    if not os.path.exists(SCHEMA_FILE):
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        return {}, {}
    
    expected_datasets = set()
    expected_tables = {}
    
    with open(SCHEMA_FILE, 'r') as f:
        content = f.read()
    
    # Extract table definitions
    table_pattern = r'CREATE (?:OR REPLACE )?TABLE\s+([a-z_]+)\.([a-z_0-9]+)'
    matches = re.findall(table_pattern, content)
    
    for dataset, table in matches:
        expected_datasets.add(dataset)
        if dataset not in expected_tables:
            expected_tables[dataset] = []
        expected_tables[dataset].append(table)
    
    return expected_datasets, expected_tables

def scan_current_state(client):
    """Scan current BigQuery state"""
    current_datasets = set()
    current_tables = {}
    
    try:
        datasets = list(client.list_datasets())
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            current_datasets.add(dataset_id)
            
            try:
                tables = list(client.list_tables(dataset_id))
                current_tables[dataset_id] = [table.table_id for table in tables]
            except NotFound:
                current_tables[dataset_id] = []
    
    except Exception as e:
        print(f"❌ Error scanning BigQuery: {e}")
        return set(), {}
    
    return current_datasets, current_tables

def generate_report(expected_datasets, expected_tables, current_datasets, current_tables):
    """Generate reconciliation report"""
    report_lines = []
    
    report_lines.append("# BigQuery Current State Report")
    report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Project:** {PROJECT_ID}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Dataset Analysis
    report_lines.append("## Dataset Analysis")
    report_lines.append("")
    
    missing_datasets = expected_datasets - current_datasets
    extra_datasets = current_datasets - expected_datasets
    existing_datasets = expected_datasets & current_datasets
    
    report_lines.append(f"- **Expected:** {len(expected_datasets)} datasets")
    report_lines.append(f"- **Current:** {len(current_datasets)} datasets")
    report_lines.append(f"- **Existing:** {len(existing_datasets)} datasets")
    report_lines.append(f"- **Missing:** {len(missing_datasets)} datasets")
    report_lines.append(f"- **Extra:** {len(extra_datasets)} datasets (legacy)")
    report_lines.append("")
    
    if missing_datasets:
        report_lines.append("### Missing Datasets (Need Creation)")
        report_lines.append("")
        for dataset in sorted(missing_datasets):
            report_lines.append(f"- ❌ `{dataset}`")
        report_lines.append("")
    
    if extra_datasets:
        report_lines.append("### Extra Datasets (Legacy/Backup)")
        report_lines.append("")
        for dataset in sorted(extra_datasets):
            report_lines.append(f"- ⚠️  `{dataset}`")
        report_lines.append("")
    
    # Table Analysis
    report_lines.append("## Table Analysis by Dataset")
    report_lines.append("")
    
    total_expected_tables = sum(len(tables) for tables in expected_tables.values())
    total_current_tables = sum(len(tables) for tables in current_tables.values())
    
    report_lines.append(f"- **Expected Total:** {total_expected_tables} tables")
    report_lines.append(f"- **Current Total:** {total_current_tables} tables")
    report_lines.append("")
    
    # Analyze each expected dataset
    for dataset in sorted(expected_datasets):
        report_lines.append(f"### Dataset: `{dataset}`")
        report_lines.append("")
        
        expected_table_set = set(expected_tables.get(dataset, []))
        current_table_set = set(current_tables.get(dataset, []))
        
        missing_tables = expected_table_set - current_table_set
        existing_tables = expected_table_set & current_table_set
        extra_tables = current_table_set - expected_table_set
        
        report_lines.append(f"- Expected: {len(expected_table_set)} tables")
        report_lines.append(f"- Existing: {len(existing_tables)} tables")
        report_lines.append(f"- Missing: {len(missing_tables)} tables")
        report_lines.append(f"- Extra: {len(extra_tables)} tables")
        report_lines.append("")
        
        if missing_tables:
            report_lines.append("**Missing Tables:**")
            report_lines.append("")
            for table in sorted(missing_tables):
                report_lines.append(f"- ❌ `{dataset}.{table}`")
            report_lines.append("")
        
        if existing_tables:
            report_lines.append("**Existing Tables:**")
            report_lines.append("")
            for table in sorted(list(existing_tables)[:10]):  # Limit to 10 for brevity
                report_lines.append(f"- ✅ `{dataset}.{table}`")
            if len(existing_tables) > 10:
                report_lines.append(f"- ... and {len(existing_tables) - 10} more")
            report_lines.append("")
    
    # Recommendations
    report_lines.append("## Recommendations")
    report_lines.append("")
    
    if missing_datasets:
        report_lines.append("### 1. Create Missing Datasets")
        report_lines.append("")
        report_lines.append("Run the deployment script to create missing datasets:")
        report_lines.append("```bash")
        report_lines.append("./scripts/deployment/deploy_bq_schema.sh")
        report_lines.append("```")
        report_lines.append("")
    
    if missing_datasets or any(expected_tables.get(d, []) for d in missing_datasets):
        report_lines.append("### 2. Create Missing Tables")
        report_lines.append("")
        report_lines.append("The schema deployment will create all missing tables.")
        report_lines.append("")
    
    if extra_datasets:
        report_lines.append("### 3. Handle Legacy Datasets")
        report_lines.append("")
        report_lines.append("Consider archiving or removing legacy datasets after migration:")
        for dataset in sorted(extra_datasets):
            if 'backup' in dataset or 'archive' in dataset:
                report_lines.append(f"- `{dataset}` (can be removed after verification)")
        report_lines.append("")
    
    # Status
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Status")
    report_lines.append("")
    
    if missing_datasets or any(expected_tables.get(d, []) for d in expected_datasets if expected_tables.get(d)):
        report_lines.append("**Status:** ❌ NOT READY - Missing datasets and/or tables")
        report_lines.append("")
        report_lines.append("**Next Steps:**")
        report_lines.append("1. Run `./scripts/deployment/deploy_bq_schema.sh`")
        report_lines.append("2. Re-run this scanner to verify")
    else:
        report_lines.append("**Status:** ✅ READY - All expected datasets and tables exist")
    
    return "\n".join(report_lines)

def main():
    """Main execution"""
    print("=" * 60)
    print("BigQuery Current State Scanner")
    print("=" * 60)
    print()
    
    print(f"📊 Parsing schema file: {SCHEMA_FILE}")
    expected_datasets, expected_tables = parse_schema_file()
    print(f"   Found {len(expected_datasets)} expected datasets")
    print(f"   Found {sum(len(t) for t in expected_tables.values())} expected tables")
    print()
    
    print(f"🔍 Scanning BigQuery project: {PROJECT_ID}")
    client = get_client()
    current_datasets, current_tables = scan_current_state(client)
    print(f"   Found {len(current_datasets)} current datasets")
    print(f"   Found {sum(len(t) for t in current_tables.values())} current tables")
    print()
    
    print(f"📝 Generating report: {REPORT_FILE}")
    report = generate_report(expected_datasets, expected_tables, current_datasets, current_tables)
    
    with open(REPORT_FILE, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {REPORT_FILE}")
    print()
    
    # Summary
    missing_datasets = expected_datasets - current_datasets
    if missing_datasets:
        print("❌ Missing datasets detected - deployment required")
        return 1
    else:
        print("✅ All expected datasets exist")
        return 0

if __name__ == "__main__":
    exit(main())

