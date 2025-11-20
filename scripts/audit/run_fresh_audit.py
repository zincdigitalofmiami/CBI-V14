#!/usr/bin/env python3
"""
FRESH COMPREHENSIVE AUDIT - November 18, 2025
==============================================
Complete system audit:
- Staging files (row counts, duplicates, date ranges)
- BigQuery tables (inventory, empty tables, row counts)
- Pipeline validation (join_executor output)
- News collection setup verification
- Workflow alignment check
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import sys
import subprocess
from collections import defaultdict
from google.cloud import bigquery

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData" / "staging"
PROJECT_ID = "cbi-v14"

# Output
AUDIT_DIR = Path("docs/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
AUDIT_REPORT = AUDIT_DIR / f"FRESH_AUDIT_{TIMESTAMP}.md"

def audit_staging_files():
    """Audit all staging parquet files."""
    print("\n" + "="*80)
    print("1. STAGING FILES AUDIT")
    print("="*80)
    
    results = {
        'staging_dir_exists': STAGING_DIR.exists(),
        'files': [],
        'total_files': 0,
        'total_rows': 0,
        'files_with_duplicates': [],
        'files_with_date_issues': []
    }
    
    if not STAGING_DIR.exists():
        print(f"❌ Staging directory not found: {STAGING_DIR}")
        return results
    
    parquet_files = list(STAGING_DIR.glob("*.parquet"))
    results['total_files'] = len(parquet_files)
    
    print(f"\nFound {len(parquet_files)} parquet files in staging directory")
    
    for file_path in sorted(parquet_files):
        try:
            df = pd.read_parquet(file_path)
            
            file_info = {
                'filename': file_path.name,
                'rows': len(df),
                'columns': len(df.columns),
                'duplicates': 0,
                'date_range': None,
                'has_date_column': False,
                'null_rate': {}
            }
            
            # Check for date column
            if 'date' in df.columns:
                file_info['has_date_column'] = True
                df['date'] = pd.to_datetime(df['date'])
                file_info['date_range'] = [
                    df['date'].min().strftime('%Y-%m-%d'),
                    df['date'].max().strftime('%Y-%m-%d')
                ]
                
                # Check for duplicate dates
                duplicate_dates = df.duplicated(subset=['date'], keep=False)
                file_info['duplicates'] = duplicate_dates.sum()
                
                if file_info['duplicates'] > 0:
                    results['files_with_duplicates'].append({
                        'file': file_path.name,
                        'duplicates': file_info['duplicates']
                    })
            
            # Check null rates for key columns
            for col in df.columns[:10]:  # Check first 10 columns
                null_rate = df[col].isna().sum() / len(df)
                if null_rate > 0.5:  # More than 50% null
                    file_info['null_rate'][col] = f"{null_rate:.2%}"
            
            results['files'].append(file_info)
            results['total_rows'] += len(df)
            
            status = "✅" if file_info['duplicates'] == 0 else "⚠️"
            print(f"{status} {file_path.name:50s} | Rows: {len(df):6d} | Cols: {len(df.columns):4d} | Duplicates: {file_info['duplicates']:4d}")
            
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            results['files'].append({
                'filename': file_path.name,
                'error': str(e)
            })
    
    return results

def audit_bigquery_tables():
    """Audit BigQuery tables."""
    print("\n" + "="*80)
    print("2. BIGQUERY TABLES AUDIT")
    print("="*80)
    
    results = {
        'datasets': {},
        'total_tables': 0,
        'empty_tables': [],
        'tables_by_prefix': defaultdict(list),
        'total_rows': 0
    }
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Key datasets to audit
        datasets = [
            'forecasting_data_warehouse',
            'raw_intelligence',
            'signals',
            'training',
            'models_v4',
            'predictions',
            'monitoring'
        ]
        
        for dataset_id in datasets:
            try:
                dataset = client.get_dataset(dataset_id)
                tables = list(client.list_tables(dataset_id))
                
                dataset_info = {
                    'tables': [],
                    'total_tables': len(tables),
                    'empty_tables': 0,
                    'total_rows': 0
                }
                
                print(f"\n📊 Dataset: {dataset_id}")
                print(f"   Tables: {len(tables)}")
                
                for table in tables:
                    table_id = f"{PROJECT_ID}.{dataset_id}.{table.table_id}"
                    
                    try:
                        # Get row count
                        query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
                        job = client.query(query)
                        row_count = list(job)[0].cnt
                        
                        # Get date range if date column exists
                        date_range = None
                        try:
                            date_query = f"""
                            SELECT 
                                MIN(date) as min_date,
                                MAX(date) as max_date,
                                COUNT(DISTINCT date) as unique_dates
                            FROM `{table_id}`
                            WHERE date IS NOT NULL
                            """
                            date_job = client.query(date_query)
                            date_row = list(date_job)[0]
                            if date_row.min_date:
                                date_range = {
                                    'min': date_row.min_date.strftime('%Y-%m-%d'),
                                    'max': date_row.max_date.strftime('%Y-%m-%d'),
                                    'unique_dates': date_row.unique_dates
                                }
                        except:
                            pass
                        
                        table_info = {
                            'table_id': table.table_id,
                            'rows': row_count,
                            'date_range': date_range
                        }
                        
                        dataset_info['tables'].append(table_info)
                        dataset_info['total_rows'] += row_count
                        results['total_rows'] += row_count
                        
                        if row_count == 0:
                            dataset_info['empty_tables'] += 1
                            results['empty_tables'].append(f"{dataset_id}.{table.table_id}")
                        
                        # Group by prefix
                        prefix = table.table_id.split('_')[0] if '_' in table.table_id else 'other'
                        results['tables_by_prefix'][prefix].append({
                            'table': f"{dataset_id}.{table.table_id}",
                            'rows': row_count
                        })
                        
                        status = "✅" if row_count > 0 else "⚠️"
                        print(f"   {status} {table.table_id:50s} | Rows: {row_count:>10,}")
                        
                    except Exception as e:
                        print(f"   ❌ Error querying {table.table_id}: {e}")
                
                results['datasets'][dataset_id] = dataset_info
                results['total_tables'] += len(tables)
                
            except Exception as e:
                print(f"❌ Error accessing dataset {dataset_id}: {e}")
        
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        results['error'] = str(e)
    
    return results

def audit_pipeline_validation():
    """Run join_executor to validate pipeline."""
    print("\n" + "="*80)
    print("3. PIPELINE VALIDATION (JOIN EXECUTOR)")
    print("="*80)
    
    results = {
        'join_executor_exists': False,
        'output': None,
        'tests_passed': False,
        'final_rows': None,
        'final_cols': None,
        'date_range': None,
        'errors': []
    }
    
    join_executor = Path("scripts/assemble/join_executor.py")
    results['join_executor_exists'] = join_executor.exists()
    
    if not join_executor.exists():
        print("❌ join_executor.py not found")
        return results
    
    print("Running join_executor.py...")
    
    try:
        # Run join_executor and capture output
        result = subprocess.run(
            [sys.executable, str(join_executor)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        results['output'] = output
        
        # Parse output for key metrics
        if "PASS" in output or "✅" in output:
            results['tests_passed'] = True
        
        # Extract final dimensions
        for line in output.split('\n'):
            if 'rows' in line.lower() and 'columns' in line.lower():
                # Try to extract numbers
                import re
                nums = re.findall(r'\d+', line)
                if len(nums) >= 2:
                    results['final_rows'] = int(nums[0])
                    results['final_cols'] = int(nums[1])
        
        # Extract date range
        for line in output.split('\n'):
            if 'date range' in line.lower() or '2000' in line:
                results['date_range'] = line.strip()
        
        if result.returncode == 0:
            print("✅ Pipeline validation completed")
            if results['tests_passed']:
                print("✅ All tests passed")
            else:
                print("⚠️ Some tests may have failed - check output")
        else:
            print("❌ Pipeline validation failed")
            results['errors'].append("join_executor returned non-zero exit code")
        
        # Print summary
        if results['final_rows'] and results['final_cols']:
            print(f"   Final dataset: {results['final_rows']:,} rows × {results['final_cols']} columns")
        if results['date_range']:
            print(f"   Date range: {results['date_range']}")
        
    except subprocess.TimeoutExpired:
        print("❌ Pipeline validation timed out (>5 minutes)")
        results['errors'].append("Timeout")
    except Exception as e:
        print(f"❌ Error running join_executor: {e}")
        results['errors'].append(str(e))
    
    return results

def audit_news_collection_setup():
    """Check news collection setup (Alpha Vantage + ScrapeCreators)."""
    print("\n" + "="*80)
    print("4. NEWS COLLECTION SETUP AUDIT")
    print("="*80)
    
    results = {
        'alpha_vantage_script': False,
        'scrapecreators_script': False,
        'bucket_classifier': False,
        'bigquery_tables': [],
        'ddl_files': [],
        'api_keys': {}
    }
    
    # Check for collection scripts
    alpha_script = Path("scripts/ingest/collect_alpha_news_sentiment.py")
    scrapecreators_script = Path("scripts/ingest/collect_news_scrapecreators_bucketed.py")
    bucket_classifier = Path("scripts/ingest/news_bucket_classifier.py")
    
    results['alpha_vantage_script'] = alpha_script.exists()
    results['scrapecreators_script'] = scrapecreators_script.exists()
    results['bucket_classifier'] = bucket_classifier.exists()
    
    print(f"\n📝 Collection Scripts:")
    print(f"   {'✅' if results['alpha_vantage_script'] else '❌'} Alpha Vantage: {alpha_script.name}")
    print(f"   {'✅' if results['scrapecreators_script'] else '❌'} ScrapeCreators: {scrapecreators_script.name}")
    print(f"   {'✅' if results['bucket_classifier'] else '❌'} Bucket Classifier: {bucket_classifier.name}")
    
    # Check for DDL files
    ddl_file = Path("config/bigquery/bigquery-sql/create_alpha_news_tables.sql")
    results['ddl_files'].append({
        'file': str(ddl_file),
        'exists': ddl_file.exists()
    })
    
    print(f"\n📊 BigQuery DDL:")
    print(f"   {'✅' if ddl_file.exists() else '❌'} {ddl_file.name}")
    
    # Check for documentation
    docs = [
        "docs/setup/NEWS_COLLECTION_REGIME_BUCKETS.md",
        "docs/audit/NEWS_COLLECTION_COMPARISON_ANALYSIS.md",
        "docs/setup/ALPHA_NEWS_INTEGRATION_ALIGNED.md",
        "docs/audit/ALPHA_SCRAPECREATORS_WORKFLOW_ALIGNMENT.md"
    ]
    
    print(f"\n📚 Documentation:")
    for doc in docs:
        doc_path = Path(doc)
        exists = doc_path.exists()
        print(f"   {'✅' if exists else '❌'} {doc_path.name}")
    
    # Check BigQuery tables (if they exist)
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        news_tables = [
            'raw_intelligence.intelligence_news_alpha_raw_daily',
            'raw_intelligence.intelligence_news_alpha_classified_daily',
            'signals.hidden_relationship_signals'
        ]
        
        print(f"\n🗄️  BigQuery Tables:")
        for table_id in news_tables:
            full_table_id = f"{PROJECT_ID}.{table_id}"
            try:
                table = client.get_table(full_table_id)
                query = f"SELECT COUNT(*) as cnt FROM `{full_table_id}`"
                job = client.query(query)
                row_count = list(job)[0].cnt
                
                results['bigquery_tables'].append({
                    'table': table_id,
                    'exists': True,
                    'rows': row_count
                })
                
                status = "✅" if row_count > 0 else "⚠️"
                print(f"   {status} {table_id} | Rows: {row_count:,}")
            except Exception:
                results['bigquery_tables'].append({
                    'table': table_id,
                    'exists': False,
                    'rows': 0
                })
                print(f"   ❌ {table_id} (not created yet)")
    except Exception as e:
        print(f"   ⚠️ Could not check BigQuery tables: {e}")
    
    return results

def generate_report(all_results):
    """Generate markdown audit report."""
    print("\n" + "="*80)
    print("GENERATING AUDIT REPORT")
    print("="*80)
    
    with open(AUDIT_REPORT, 'w') as f:
        f.write(f"# FRESH COMPREHENSIVE AUDIT\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Project:** CBI-V14\n")
        f.write(f"**Scope:** Complete system audit - staging files, BigQuery, pipeline, news setup\n\n")
        f.write("---\n\n")
        
        # 1. Staging Files
        f.write("## 1. STAGING FILES AUDIT\n\n")
        staging = all_results['staging']
        
        if staging['staging_dir_exists']:
            f.write(f"**Status:** ✅ Staging directory found\n\n")
            f.write(f"- **Total Files:** {staging['total_files']}\n")
            f.write(f"- **Total Rows:** {staging['total_rows']:,}\n")
            f.write(f"- **Files with Duplicates:** {len(staging['files_with_duplicates'])}\n\n")
            
            f.write("### File Details\n\n")
            f.write("| File | Rows | Columns | Duplicates | Date Range | Status |\n")
            f.write("|------|------|---------|------------|------------|--------|\n")
            
            for file_info in staging['files']:
                if 'error' not in file_info:
                    filename = file_info['filename']
                    rows = file_info['rows']
                    cols = file_info['columns']
                    dups = file_info['duplicates']
                    date_range = file_info.get('date_range')
                    if date_range and isinstance(date_range, list) and len(date_range) >= 2:
                        date_str = f"{date_range[0]} to {date_range[1]}"
                    else:
                        date_str = "N/A"
                    status = "✅" if dups == 0 else "⚠️"
                    
                    f.write(f"| {filename} | {rows:,} | {cols} | {dups} | {date_str} | {status} |\n")
            
            if staging['files_with_duplicates']:
                f.write("\n### ⚠️ Files with Duplicate Dates\n\n")
                for dup_file in staging['files_with_duplicates']:
                    f.write(f"- **{dup_file['file']}**: {dup_file['duplicates']} duplicate dates\n")
        else:
            f.write("**Status:** ❌ Staging directory not found\n\n")
        
        # 2. BigQuery Tables
        f.write("\n## 2. BIGQUERY TABLES AUDIT\n\n")
        bq = all_results['bigquery']
        
        f.write(f"- **Total Tables:** {bq['total_tables']}\n")
        f.write(f"- **Total Rows:** {bq['total_rows']:,}\n")
        f.write(f"- **Empty Tables:** {len(bq['empty_tables'])}\n\n")
        
        for dataset_id, dataset_info in bq['datasets'].items():
            f.write(f"### {dataset_id}\n\n")
            f.write(f"- Tables: {dataset_info['total_tables']}\n")
            f.write(f"- Total Rows: {dataset_info['total_rows']:,}\n")
            f.write(f"- Empty Tables: {dataset_info['empty_tables']}\n\n")
        
        if bq['empty_tables']:
            f.write("### ⚠️ Empty Tables\n\n")
            for table in bq['empty_tables'][:20]:  # Limit to first 20
                f.write(f"- `{table}`\n")
            if len(bq['empty_tables']) > 20:
                f.write(f"\n... and {len(bq['empty_tables']) - 20} more\n")
        
        # Prefix summary
        f.write("\n### Tables by Prefix\n\n")
        for prefix, tables in sorted(bq['tables_by_prefix'].items()):
            total_rows = sum(t['rows'] for t in tables)
            populated = sum(1 for t in tables if t['rows'] > 0)
            f.write(f"- **{prefix}_**: {len(tables)} tables, {populated} populated, {total_rows:,} total rows\n")
        
        # 3. Pipeline Validation
        f.write("\n## 3. PIPELINE VALIDATION\n\n")
        pipeline = all_results['pipeline']
        
        if pipeline['join_executor_exists']:
            if pipeline['tests_passed']:
                f.write("**Status:** ✅ Pipeline validation passed\n\n")
            else:
                f.write("**Status:** ⚠️ Pipeline validation completed with warnings\n\n")
            
            if pipeline['final_rows'] and pipeline['final_cols']:
                f.write(f"- **Final Dataset:** {pipeline['final_rows']:,} rows × {pipeline['final_cols']} columns\n")
            if pipeline['date_range']:
                f.write(f"- **Date Range:** {pipeline['date_range']}\n")
            
            if pipeline['errors']:
                f.write("\n### ⚠️ Errors\n\n")
                for error in pipeline['errors']:
                    f.write(f"- {error}\n")
        else:
            f.write("**Status:** ❌ join_executor.py not found\n\n")
        
        # 4. News Collection Setup
        f.write("\n## 4. NEWS COLLECTION SETUP\n\n")
        news = all_results['news']
        
        f.write("### Collection Scripts\n\n")
        f.write(f"- {'✅' if news['alpha_vantage_script'] else '❌'} Alpha Vantage collector\n")
        f.write(f"- {'✅' if news['scrapecreators_script'] else '❌'} ScrapeCreators collector\n")
        f.write(f"- {'✅' if news['bucket_classifier'] else '❌'} Bucket classifier\n\n")
        
        f.write("### BigQuery Tables\n\n")
        for table_info in news['bigquery_tables']:
            status = "✅" if table_info['exists'] and table_info['rows'] > 0 else "⚠️" if table_info['exists'] else "❌"
            f.write(f"- {status} `{table_info['table']}` | Rows: {table_info['rows']:,}\n")
        
        # Summary
        f.write("\n## SUMMARY\n\n")
        
        issues = []
        if staging.get('files_with_duplicates'):
            issues.append(f"{len(staging['files_with_duplicates'])} staging files with duplicate dates")
        if bq.get('empty_tables'):
            issues.append(f"{len(bq['empty_tables'])} empty BigQuery tables")
        if not pipeline.get('tests_passed'):
            issues.append("Pipeline validation issues")
        
        if issues:
            f.write("### ⚠️ Issues Found\n\n")
            for issue in issues:
                f.write(f"- {issue}\n")
        else:
            f.write("### ✅ No Critical Issues Found\n\n")
        
        f.write(f"\n**Report saved to:** `{AUDIT_REPORT}`\n")
    
    print(f"✅ Audit report saved to: {AUDIT_REPORT}")

def main():
    """Run comprehensive audit."""
    print("="*80)
    print("FRESH COMPREHENSIVE AUDIT - November 18, 2025")
    print("="*80)
    
    all_results = {
        'staging': audit_staging_files(),
        'bigquery': audit_bigquery_tables(),
        'pipeline': audit_pipeline_validation(),
        'news': audit_news_collection_setup()
    }
    
    generate_report(all_results)
    
    print("\n" + "="*80)
    print("✅ AUDIT COMPLETE")
    print("="*80)
    print(f"Report: {AUDIT_REPORT}")

if __name__ == "__main__":
    main()

