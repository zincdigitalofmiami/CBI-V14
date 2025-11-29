#!/usr/bin/env python3
"""
Comprehensive audit of V14 external drive and BigQuery
Reports what exists and what needs to be exported to V15
"""
from pathlib import Path
from google.cloud import bigquery
from datetime import datetime
import json

PROJECT_ID = "cbi-v14"
V14_ROOT = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
V15_ROOT = Path("/Volumes/Satechi Hub/Projects/CBI-V15")

def audit_external_drive():
    """Audit external drive V14 folder"""
    print("="*80)
    print("EXTERNAL DRIVE AUDIT (V14)")
    print("="*80)
    
    if not V14_ROOT.exists():
        print(f"❌ V14 folder not found: {V14_ROOT}")
        return {}
    
    # Get total size
    import subprocess
    result = subprocess.run(['du', '-sh', str(V14_ROOT)], capture_output=True, text=True)
    total_size = result.stdout.split()[0] if result.returncode == 0 else "Unknown"
    print(f"Total size: {total_size}")
    
    # Count parquet files
    parquet_files = list(V14_ROOT.rglob("*.parquet"))
    print(f"Parquet files: {len(parquet_files)}")
    
    # Check key data locations
    findings = {
        'fred_data': [],
        'databento_data': [],
        'scrapecreators_data': [],
        'vegas_data': [],
        'training_exports': []
    }
    
    # FRED data
    fred_files = list(V14_ROOT.rglob("*fred*.parquet"))
    findings['fred_data'] = [str(f.relative_to(V14_ROOT)) for f in fred_files[:10]]
    print(f"\nFRED data files: {len(fred_files)}")
    for f in fred_files[:5]:
        print(f"  - {f.relative_to(V14_ROOT)}")
    
    # Databento data
    databento_dirs = [d for d in (V14_ROOT / "TrainingData/raw").iterdir() if d.is_dir() and "databento" in d.name.lower()]
    findings['databento_data'] = [d.name for d in databento_dirs]
    print(f"\nDatabento symbol folders: {len(databento_dirs)}")
    for d in databento_dirs[:10]:
        print(f"  - {d.name}")
    
    # ScrapeCreators/Trump data
    trump_files = list(V14_ROOT.rglob("*trump*.parquet")) + list(V14_ROOT.rglob("*policy*.parquet"))
    findings['scrapecreators_data'] = [str(f.relative_to(V14_ROOT)) for f in trump_files[:10]]
    print(f"\nTrump/Policy data files: {len(trump_files)}")
    for f in trump_files[:5]:
        print(f"  - {f.relative_to(V14_ROOT)}")
    
    # Vegas data
    vegas_files = list(V14_ROOT.rglob("*vegas*.parquet")) + list(V14_ROOT.rglob("*glide*.parquet"))
    findings['vegas_data'] = [str(f.relative_to(V14_ROOT)) for f in vegas_files]
    print(f"\nVegas data files: {len(vegas_files)}")
    for f in vegas_files[:5]:
        print(f"  - {f.relative_to(V14_ROOT)}")
    
    # Training exports
    training_exports = list((V14_ROOT / "TrainingData/exports").glob("*.parquet")) if (V14_ROOT / "TrainingData/exports").exists() else []
    findings['training_exports'] = [f.name for f in training_exports]
    print(f"\nTraining exports: {len(training_exports)}")
    for f in training_exports:
        print(f"  - {f.name}")
    
    return findings


def audit_bigquery():
    """Audit BigQuery datasets and tables"""
    print("\n" + "="*80)
    print("BIGQUERY AUDIT")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    datasets = list(client.list_datasets())
    
    print(f"Total datasets: {len(datasets)}\n")
    
    audit_results = {
        'datasets': {},
        'total_tables': 0,
        'total_views': 0,
        'key_tables': {},
        'empty_tables': [],
        'archive_tables': 0
    }
    
    for ds in sorted(datasets, key=lambda x: x.dataset_id):
        dataset_id = ds.dataset_id
        try:
            tables = list(client.list_tables(dataset_id))
            table_list = []
            view_list = []
            
            for t in tables:
                tbl = client.get_table(t)
                if tbl.table_type == 'TABLE':
                    table_list.append({
                        'name': tbl.table_id,
                        'rows': tbl.num_rows or 0,
                        'size_bytes': tbl.num_bytes or 0
                    })
                    if tbl.num_rows == 0:
                        audit_results['empty_tables'].append(f"{dataset_id}.{tbl.table_id}")
                else:
                    view_list.append(tbl.table_id)
            
            audit_results['datasets'][dataset_id] = {
                'tables': len(table_list),
                'views': len(view_list),
                'total_rows': sum(t['rows'] for t in table_list),
                'total_size_gb': sum(t['size_bytes'] for t in table_list) / (1024**3)
            }
            
            audit_results['total_tables'] += len(table_list)
            audit_results['total_views'] += len(view_list)
            
            # Count archive tables
            if 'archive' in dataset_id.lower():
                audit_results['archive_tables'] += len(table_list)
            
            print(f"{dataset_id}:")
            print(f"  Tables: {len(table_list)}, Views: {len(view_list)}")
            print(f"  Total rows: {sum(t['rows'] for t in table_list):,}")
            print(f"  Total size: {sum(t['size_bytes'] for t in table_list) / (1024**3):.4f} GB")
            
            # Show key tables
            key_tables_in_ds = [
                ('databento_futures_ohlcv_1d', 'market_data'),
                ('fred_economic', 'raw_intelligence'),
                ('zl_daily_v1', 'features'),
                ('macro_features_daily', 'features'),
                ('regime_weights', 'training'),
            ]
            
            for table_name, expected_ds in key_tables_in_ds:
                if dataset_id == expected_ds:
                    for t in table_list:
                        if t['name'] == table_name:
                            audit_results['key_tables'][f"{dataset_id}.{table_name}"] = {
                                'rows': t['rows'],
                                'size_gb': t['size_bytes'] / (1024**3)
                            }
                            print(f"  ✅ {table_name}: {t['rows']:,} rows, {t['size_bytes'] / (1024**3):.4f} GB")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\nSUMMARY:")
    print(f"  Total tables: {audit_results['total_tables']}")
    print(f"  Total views: {audit_results['total_views']}")
    print(f"  Archive tables: {audit_results['archive_tables']}")
    print(f"  Empty tables: {len(audit_results['empty_tables'])}")
    
    return audit_results


def generate_report(external_findings, bq_findings):
    """Generate comprehensive audit report"""
    report = {
        'audit_date': datetime.now().isoformat(),
        'external_drive': {
            'v14_path': str(V14_ROOT),
            'v15_path': str(V15_ROOT),
            'findings': external_findings
        },
        'bigquery': {
            'project': PROJECT_ID,
            'findings': bq_findings
        },
        'recommendations': []
    }
    
    # Recommendations
    if bq_findings['archive_tables'] > 0:
        report['recommendations'].append(
            f"Delete {bq_findings['archive_tables']} archive tables to reduce costs"
        )
    
    if len(bq_findings['empty_tables']) > 50:
        report['recommendations'].append(
            f"Delete {len(bq_findings['empty_tables'])} empty tables"
        )
    
    report['recommendations'].append(
        "Export all critical data to V15 before deleting BigQuery tables"
    )
    
    report['recommendations'].append(
        "Keep only active datasets: market_data, features, training, raw_intelligence"
    )
    
    # Save report
    report_path = Path(__file__).parent / "v14_to_v15_audit_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*80)
    print("AUDIT REPORT SAVED")
    print("="*80)
    print(f"Location: {report_path}")
    
    return report


def main():
    print("CBI-V14 TO V15 AUDIT")
    print(f"Date: {datetime.now().isoformat()}\n")
    
    external_findings = audit_external_drive()
    bq_findings = audit_bigquery()
    report = generate_report(external_findings, bq_findings)
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")


if __name__ == "__main__":
    main()

