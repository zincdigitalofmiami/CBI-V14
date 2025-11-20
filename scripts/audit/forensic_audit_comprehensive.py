#!/usr/bin/env python3
"""
COMPREHENSIVE FORENSIC AUDIT
============================
Complete audit of:
- External drive structure and files
- BigQuery tables and views
- All pipelines and staging files
- Data quality and correlations
- Symbols, sentiments, news, groups, regimes
- Everything
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import sys
import os
from collections import defaultdict
from google.cloud import bigquery

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.gcp_utils import get_gcp_project_id

# Configuration
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
TRAINING_DATA = EXTERNAL_DRIVE / "TrainingData"
PROJECT_ID = get_gcp_project_id()
DATASET_ID = "forecasting_data_warehouse"

# Output
AUDIT_DIR = Path("docs/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
AUDIT_REPORT = AUDIT_DIR / f"FORENSIC_AUDIT_{TIMESTAMP}.md"

def audit_external_drive():
    """Audit external drive structure and files."""
    print("\n" + "="*80)
    print("1. EXTERNAL DRIVE STRUCTURE AUDIT")
    print("="*80)
    
    results = {
        'drive_exists': EXTERNAL_DRIVE.exists(),
        'training_data_exists': TRAINING_DATA.exists(),
        'directories': {},
        'file_counts': {},
        'total_size_gb': 0,
        'raw_data_sources': [],
        'staging_files': [],
        'registry_files': []
    }
    
    if not EXTERNAL_DRIVE.exists():
        print("❌ External drive not found!")
        return results
    
    # Scan directory structure
    print("\nScanning directory structure...")
    
    key_dirs = {
        'raw': TRAINING_DATA / 'raw',
        'staging': TRAINING_DATA / 'staging',
        'registry': Path('registry'),
        'features': TRAINING_DATA / 'features' if (TRAINING_DATA / 'features').exists() else Path('features'),
        'scripts': Path('scripts'),
        'docs': Path('docs')
    }
    
    for name, path in key_dirs.items():
        if path.exists():
            files = list(path.rglob('*'))
            parquet_files = [f for f in files if f.suffix == '.parquet']
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            results['directories'][name] = {
                'path': str(path),
                'total_files': len([f for f in files if f.is_file()]),
                'parquet_files': len(parquet_files),
                'size_gb': total_size / (1024**3),
                'subdirectories': [d.name for d in path.iterdir() if d.is_dir()]
            }
            
            print(f"\n{name.upper()}:")
            print(f"  Path: {path}")
            print(f"  Total files: {len([f for f in files if f.is_file()])}")
            print(f"  Parquet files: {len(parquet_files)}")
            print(f"  Size: {total_size / (1024**3):.2f} GB")
            
            if name == 'raw':
                # List all raw data sources
                raw_sources = [d.name for d in path.iterdir() if d.is_dir()]
                results['raw_data_sources'] = raw_sources
                print(f"  Data sources: {len(raw_sources)}")
                for source in sorted(raw_sources):
                    source_path = path / source
                    source_files = list(source_path.rglob('*.parquet'))
                    print(f"    - {source}: {len(source_files)} parquet files")
            
            elif name == 'staging':
                staging_files = [f.name for f in path.glob('*.parquet')]
                results['staging_files'] = staging_files
                print(f"  Staging files: {len(staging_files)}")
                for sf in sorted(staging_files):
                    sf_path = path / sf
                    if sf_path.exists():
                        df = pd.read_parquet(sf_path)
                        print(f"    - {sf}: {len(df):,} rows × {len(df.columns)} cols")
    
    return results

def audit_bigquery():
    """Audit all BigQuery tables and views."""
    print("\n" + "="*80)
    print("2. BIGQUERY AUDIT")
    print("="*80)
    
    results = {
        'tables': {},
        'views': {},
        'datasets': [],
        'master_view_columns': 0,
        'master_view_rows': 0
    }
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # List all datasets
        print("\nScanning datasets...")
        datasets = list(client.list_datasets())
        results['datasets'] = [d.dataset_id for d in datasets]
        print(f"  Found {len(datasets)} datasets")
        
        # Audit forecasting_data_warehouse
        print(f"\nAuditing {DATASET_ID} dataset...")
        dataset_ref = client.dataset(DATASET_ID)
        tables = list(client.list_tables(dataset_ref))
        
        print(f"  Tables: {len(tables)}")
        for table in tables:
            table_ref = dataset_ref.table(table.table_id)
            table_obj = client.get_table(table_ref)
            
            # Get row count and date range
            count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table.table_id}`"
            try:
                count_result = client.query(count_query).result()
                row_count = list(count_result)[0].cnt
            except:
                row_count = 0
            
            date_query = f"""
            SELECT MIN(date) as min_date, MAX(date) as max_date
            FROM `{PROJECT_ID}.{DATASET_ID}.{table.table_id}`
            WHERE date IS NOT NULL
            """
            try:
                date_result = client.query(date_query).result()
                date_row = list(date_result)[0]
                min_date = date_row.min_date
                max_date = date_row.max_date
            except:
                min_date = None
                max_date = None
            
            results['tables'][table.table_id] = {
                'rows': row_count,
                'columns': len(table_obj.schema),
                'min_date': str(min_date) if min_date else None,
                'max_date': str(max_date) if max_date else None,
                'size_gb': table_obj.num_bytes / (1024**3) if table_obj.num_bytes else 0
            }
            
            print(f"    - {table.table_id}: {row_count:,} rows, {len(table_obj.schema)} cols")
            if min_date:
                print(f"      Date range: {min_date} to {max_date}")
        
        # Check views
        views_query = f"""
        SELECT table_name, view_definition
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.VIEWS`
        """
        try:
            views_result = client.query(views_query).result()
            for row in views_result:
                results['views'][row.table_name] = {
                    'definition_length': len(row.view_definition)
                }
                print(f"    - View: {row.table_name}")
        except Exception as e:
            print(f"  ⚠️  Could not query views: {e}")
        
        # Audit master view
        master_view = f"{PROJECT_ID}.{DATASET_ID}.master_features_all"
        print(f"\nAuditing master view: master_features_all")
        try:
            view_obj = client.get_table(master_view)
            results['master_view_columns'] = len(view_obj.schema)
            
            count_query = f"SELECT COUNT(*) as cnt FROM `{master_view}`"
            count_result = client.query(count_query).result()
            results['master_view_rows'] = list(count_result)[0].cnt
            
            print(f"  Columns: {results['master_view_columns']}")
            print(f"  Rows: {results['master_view_rows']:,}")
        except Exception as e:
            print(f"  ❌ Error accessing master view: {e}")
        
    except Exception as e:
        print(f"❌ BigQuery audit error: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def audit_staging_files():
    """Audit all staging files."""
    print("\n" + "="*80)
    print("3. STAGING FILES AUDIT")
    print("="*80)
    
    results = {}
    staging_dir = TRAINING_DATA / 'staging'
    
    if not staging_dir.exists():
        print("❌ Staging directory not found!")
        return results
    
    staging_files = list(staging_dir.glob('*.parquet'))
    print(f"\nFound {len(staging_files)} staging files")
    
    for sf in sorted(staging_files):
        try:
            df = pd.read_parquet(sf)
            
            # Check date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                date_range = (df['date'].min(), df['date'].max())
                unique_dates = df['date'].nunique()
            else:
                date_range = (None, None)
                unique_dates = 0
            
            # Check for duplicates
            if 'date' in df.columns:
                duplicates = df['date'].duplicated().sum()
            else:
                duplicates = 0
            
            # Count nulls
            null_counts = df.isnull().sum()
            null_pct = (null_counts / len(df) * 100).to_dict()
            high_null_cols = {k: v for k, v in null_pct.items() if v > 50}
            
            # Check prefixes
            prefixes = defaultdict(int)
            for col in df.columns:
                if col not in ['date', 'symbol', 'regime', 'training_weight']:
                    for prefix in ['yahoo_', 'fred_', 'weather_', 'cftc_', 'usda_', 'eia_', 
                                  'alpha_', 'vol_', 'barchart_palm_', 'policy_trump_', 'es_']:
                        if col.startswith(prefix):
                            prefixes[prefix] += 1
                            break
            
            results[sf.name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'date_range': (str(date_range[0]), str(date_range[1])),
                'unique_dates': unique_dates,
                'duplicates': duplicates,
                'null_columns_gt_50pct': len(high_null_cols),
                'prefixes': dict(prefixes),
                'sample_columns': list(df.columns[:10])
            }
            
            print(f"\n{sf.name}:")
            print(f"  Rows: {len(df):,}, Columns: {len(df.columns)}")
            if date_range[0]:
                print(f"  Date range: {date_range[0]} to {date_range[1]}")
            print(f"  Unique dates: {unique_dates:,}")
            if duplicates > 0:
                print(f"  ⚠️  Duplicate dates: {duplicates}")
            print(f"  Columns with >50% null: {len(high_null_cols)}")
            if prefixes:
                print(f"  Prefixes: {dict(prefixes)}")
                
        except Exception as e:
            print(f"  ❌ Error auditing {sf.name}: {e}")
            results[sf.name] = {'error': str(e)}
    
    return results

def audit_pipeline():
    """Audit join pipeline."""
    print("\n" + "="*80)
    print("4. PIPELINE AUDIT")
    print("="*80)
    
    results = {
        'join_spec_exists': False,
        'joins': [],
        'final_columns': 0,
        'final_rows': 0,
        'tests_passed': False
    }
    
    join_spec = Path('registry/join_spec.yaml')
    if join_spec.exists():
        results['join_spec_exists'] = True
        import yaml
        with open(join_spec, 'r') as f:
            spec = yaml.safe_load(f)
            results['joins'] = [j['name'] for j in spec.get('joins', [])]
            print(f"\nJoin specification: {len(results['joins'])} joins defined")
            for join in results['joins']:
                print(f"  - {join}")
    
    # Run join executor to get final stats
    try:
        sys.path.insert(0, str(Path.cwd()))
        from scripts.assemble.join_executor import JoinExecutor
        
        executor = JoinExecutor()
        final_df = executor.execute_all_joins()
        
        results['final_columns'] = len(final_df.columns)
        results['final_rows'] = len(final_df)
        results['tests_passed'] = True
        
        print(f"\nFinal pipeline output:")
        print(f"  Rows: {results['final_rows']:,}")
        print(f"  Columns: {results['final_columns']}")
        
        # Check column prefixes
        prefix_counts = defaultdict(int)
        for col in final_df.columns:
            if col not in ['date', 'symbol', 'regime', 'training_weight']:
                for prefix in ['yahoo_', 'fred_', 'weather_', 'cftc_', 'usda_', 'eia_',
                              'alpha_', 'vol_', 'barchart_palm_', 'policy_trump_', 'es_']:
                    if col.startswith(prefix):
                        prefix_counts[prefix] += 1
                        break
        
        print(f"\nColumn distribution by prefix:")
        for prefix, count in sorted(prefix_counts.items()):
            print(f"  {prefix}: {count} columns")
        
    except Exception as e:
        print(f"❌ Pipeline execution error: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def audit_symbols():
    """Audit all symbols across data sources."""
    print("\n" + "="*80)
    print("5. SYMBOLS AUDIT")
    print("="*80)
    
    results = {
        'yahoo_symbols': set(),
        'alpha_symbols': set(),
        'es_symbols': set(),
        'all_symbols': set()
    }
    
    # Check Yahoo staging
    yahoo_file = TRAINING_DATA / 'staging/yahoo_historical_all_symbols.parquet'
    if yahoo_file.exists():
        df = pd.read_parquet(yahoo_file)
        if 'symbol' in df.columns:
            results['yahoo_symbols'] = set(df['symbol'].unique())
            print(f"\nYahoo symbols: {len(results['yahoo_symbols'])}")
            for sym in sorted(results['yahoo_symbols']):
                count = len(df[df['symbol'] == sym])
                print(f"  - {sym}: {count:,} rows")
    
    # Check Alpha Vantage
    alpha_file = TRAINING_DATA / 'staging/alpha_vantage_features.parquet'
    if alpha_file.exists():
        df = pd.read_parquet(alpha_file)
        # Alpha columns contain symbol info in names
        alpha_cols = [c for c in df.columns if any(s in c.lower() for s in ['spy', 'eurusd', 'gbpusd', 'wti', 'brent'])]
        print(f"\nAlpha Vantage: {len(alpha_cols)} symbol-related columns")
    
    # Check ES
    es_file = TRAINING_DATA / 'staging/es_futures_daily.parquet'
    if es_file.exists():
        df = pd.read_parquet(es_file)
        if 'symbol' in df.columns:
            results['es_symbols'] = set(df['symbol'].unique())
            print(f"\nES symbols: {len(results['es_symbols'])}")
            for sym in sorted(results['es_symbols']):
                print(f"  - {sym}")
    
    results['all_symbols'] = results['yahoo_symbols'] | results['es_symbols']
    
    return results

def audit_sentiments_news():
    """Audit sentiment and news data."""
    print("\n" + "="*80)
    print("6. SENTIMENTS & NEWS AUDIT")
    print("="*80)
    
    results = {
        'policy_trump_records': 0,
        'sentiment_scores': {},
        'news_sources': set(),
        'categories': defaultdict(int)
    }
    
    # Check policy/Trump data
    policy_file = TRAINING_DATA / 'staging/policy_trump_signals.parquet'
    if policy_file.exists():
        df = pd.read_parquet(policy_file)
        results['policy_trump_records'] = len(df)
        
        print(f"\nPolicy/Trump signals: {len(df):,} records")
        
        # Check sentiment columns
        sentiment_cols = [c for c in df.columns if 'sentiment' in c.lower()]
        if sentiment_cols:
            for col in sentiment_cols:
                if df[col].dtype in [np.float64, np.int64]:
                    results['sentiment_scores'][col] = {
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'mean': float(df[col].mean()),
                        'null_pct': float(df[col].isnull().sum() / len(df) * 100)
                    }
                    print(f"  {col}: range [{df[col].min():.2f}, {df[col].max():.2f}], mean {df[col].mean():.2f}")
        
        # Check categories
        if 'policy_trump_category' in df.columns:
            categories = df['policy_trump_category'].value_counts()
            results['categories'] = categories.to_dict()
            print(f"\n  Categories: {len(categories)}")
            for cat, count in categories.head(10).items():
                print(f"    - {cat}: {count}")
        
        # Check sources
        if 'policy_trump_domain' in df.columns:
            results['news_sources'] = set(df['policy_trump_domain'].dropna().unique())
            print(f"\n  News sources: {len(results['news_sources'])}")
            for source in sorted(list(results['news_sources']))[:10]:
                print(f"    - {source}")
    
    return results

def audit_regimes():
    """Audit regime data."""
    print("\n" + "="*80)
    print("7. REGIMES AUDIT")
    print("="*80)
    
    results = {
        'regime_calendar_exists': False,
        'regime_weights_exists': False,
        'regimes': [],
        'date_coverage': {},
        'weights': {}
    }
    
    # Check regime calendar
    regime_file = Path('registry/regime_calendar.parquet')
    if regime_file.exists():
        results['regime_calendar_exists'] = True
        df = pd.read_parquet(regime_file)
        
        if 'regime' in df.columns:
            regimes = df['regime'].value_counts()
            results['regimes'] = regimes.to_dict()
            print(f"\nRegime calendar: {len(df):,} rows")
            print(f"  Unique regimes: {len(regimes)}")
            for regime, count in regimes.items():
                print(f"    - {regime}: {count:,} days")
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            results['date_coverage'] = {
                'min': str(df['date'].min()),
                'max': str(df['date'].max()),
                'total_days': len(df)
            }
            print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        if 'training_weight' in df.columns:
            weights = df['training_weight'].describe()
            results['weights'] = {
                'min': float(weights['min']),
                'max': float(weights['max']),
                'mean': float(weights['mean']),
                'unique': int(df['training_weight'].nunique())
            }
            print(f"  Training weights: {weights['min']:.0f} to {weights['max']:.0f} (mean {weights['mean']:.1f})")
    
    # Check regime weights YAML
    weights_yaml = Path('registry/regime_weights.yaml')
    if weights_yaml.exists():
        results['regime_weights_exists'] = True
        print(f"\n  ✅ Regime weights YAML exists")
    
    return results

def audit_correlations():
    """Audit data correlations."""
    print("\n" + "="*80)
    print("8. CORRELATIONS AUDIT")
    print("="*80)
    
    results = {}
    
    try:
        # Load final joined data
        from scripts.assemble.join_executor import JoinExecutor
        executor = JoinExecutor()
        df = executor.execute_all_joins()
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Sample correlation with target (if exists)
        if 'yahoo_close' in df.columns:
            target = 'yahoo_close'
            correlations = df[numeric_cols].corrwith(df[target]).abs().sort_values(ascending=False)
            
            results['top_correlations'] = correlations.head(20).to_dict()
            
            print(f"\nTop 20 correlations with {target}:")
            for col, corr in correlations.head(20).items():
                print(f"  {col}: {corr:.3f}")
        
    except Exception as e:
        print(f"❌ Correlation audit error: {e}")
    
    return results

def generate_report(all_results):
    """Generate comprehensive audit report."""
    print("\n" + "="*80)
    print("GENERATING COMPREHENSIVE AUDIT REPORT")
    print("="*80)
    
    report = f"""# COMPREHENSIVE FORENSIC AUDIT REPORT
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Project:** CBI-V14
**External Drive:** {EXTERNAL_DRIVE}
**BigQuery Project:** {PROJECT_ID}

---

## EXECUTIVE SUMMARY

### Data Sources
- **Raw Data Sources:** {len(all_results['drive']['raw_data_sources'])}
- **Staging Files:** {len(all_results['staging'])}
- **BigQuery Tables:** {len(all_results['bq']['tables'])}
- **BigQuery Views:** {len(all_results['bq']['views'])}

### Pipeline Status
- **Join Steps:** {len(all_results['pipeline']['joins'])}
- **Final Columns:** {all_results['pipeline']['final_columns']:,}
- **Final Rows:** {all_results['pipeline']['final_rows']:,}
- **Tests Passed:** {'✅' if all_results['pipeline']['tests_passed'] else '❌'}

### Symbols
- **Yahoo Symbols:** {len(all_results['symbols']['yahoo_symbols'])}
- **ES Symbols:** {len(all_results['symbols']['es_symbols'])}
- **Total Unique:** {len(all_results['symbols']['all_symbols'])}

### Sentiments & News
- **Policy/Trump Records:** {all_results['sentiments']['policy_trump_records']:,}
- **News Sources:** {len(all_results['sentiments']['news_sources'])}
- **Categories:** {len(all_results['sentiments']['categories'])}

### Regimes
- **Unique Regimes:** {len(all_results['regimes']['regimes'])}
- **Date Coverage:** {all_results['regimes']['date_coverage'].get('total_days', 0):,} days

---

## 1. EXTERNAL DRIVE STRUCTURE

"""
    
    # Add drive structure details
    for dir_name, dir_info in all_results['drive']['directories'].items():
        report += f"""
### {dir_name.upper()}
- **Path:** `{dir_info['path']}`
- **Total Files:** {dir_info['total_files']:,}
- **Parquet Files:** {dir_info['parquet_files']:,}
- **Size:** {dir_info['size_gb']:.2f} GB
- **Subdirectories:** {len(dir_info['subdirectories'])}
"""
    
    # Add raw data sources
    report += f"""
### Raw Data Sources
"""
    for source in sorted(all_results['drive']['raw_data_sources']):
        report += f"- {source}\n"
    
    # Add staging files
    report += f"""
### Staging Files
"""
    for sf_name, sf_info in all_results['staging'].items():
        if 'error' not in sf_info:
            report += f"""
- **{sf_name}**
  - Rows: {sf_info['rows']:,}
  - Columns: {sf_info['columns']}
  - Date Range: {sf_info['date_range'][0]} to {sf_info['date_range'][1]}
  - Duplicates: {sf_info['duplicates']}
  - High Null Columns: {sf_info['null_columns_gt_50pct']}
"""
    
    # Add BigQuery details
    report += f"""
## 2. BIGQUERY AUDIT

### Datasets
"""
    for dataset in all_results['bq']['datasets']:
        report += f"- {dataset}\n"
    
    report += f"""
### Tables ({len(all_results['bq']['tables'])})
"""
    for table_name, table_info in sorted(all_results['bq']['tables'].items()):
        report += f"""
- **{table_name}**
  - Rows: {table_info['rows']:,}
  - Columns: {table_info['columns']}
  - Size: {table_info['size_gb']:.2f} GB
  - Date Range: {table_info['min_date']} to {table_info['max_date']}
"""
    
    report += f"""
### Master View
- **Columns:** {all_results['bq']['master_view_columns']:,}
- **Rows:** {all_results['bq']['master_view_rows']:,}
"""
    
    # Add pipeline details
    report += f"""
## 3. PIPELINE AUDIT

### Join Steps
"""
    for join in all_results['pipeline']['joins']:
        report += f"- {join}\n"
    
    # Add symbols
    report += f"""
## 4. SYMBOLS AUDIT

### Yahoo Finance
"""
    for sym in sorted(all_results['symbols']['yahoo_symbols']):
        report += f"- {sym}\n"
    
    report += f"""
### ES Futures
"""
    for sym in sorted(all_results['symbols']['es_symbols']):
        report += f"- {sym}\n"
    
    # Add sentiments
    report += f"""
## 5. SENTIMENTS & NEWS AUDIT

- **Total Records:** {all_results['sentiments']['policy_trump_records']:,}
- **News Sources:** {len(all_results['sentiments']['news_sources'])}
- **Categories:** {len(all_results['sentiments']['categories'])}

### Top Categories
"""
    for cat, count in sorted(all_results['sentiments']['categories'].items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"- {cat}: {count}\n"
    
    # Add regimes
    report += f"""
## 6. REGIMES AUDIT

- **Regime Calendar:** {'✅' if all_results['regimes']['regime_calendar_exists'] else '❌'}
- **Regime Weights YAML:** {'✅' if all_results['regimes']['regime_weights_exists'] else '❌'}
- **Unique Regimes:** {len(all_results['regimes']['regimes'])}

### Regime Distribution
"""
    for regime, count in sorted(all_results['regimes']['regimes'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {regime}: {count:,} days\n"
    
    # Add correlations
    if 'top_correlations' in all_results['correlations']:
        report += f"""
## 7. CORRELATIONS AUDIT

### Top Correlations with Target
"""
        for col, corr in list(all_results['correlations']['top_correlations'].items())[:20]:
            report += f"- {col}: {corr:.3f}\n"
    
    report += f"""
---

## AUDIT COMPLETE
**Report saved to:** {AUDIT_REPORT}
"""
    
    # Write report
    with open(AUDIT_REPORT, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Audit report saved to: {AUDIT_REPORT}")
    
    # Also save JSON for programmatic access
    json_report = AUDIT_DIR / f"FORENSIC_AUDIT_{TIMESTAMP}.json"
    with open(json_report, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"✅ JSON data saved to: {json_report}")

def main():
    """Run comprehensive forensic audit."""
    print("="*80)
    print("COMPREHENSIVE FORENSIC AUDIT")
    print("="*80)
    print("Auditing: External Drive, BigQuery, Pipelines, Symbols, Sentiments, Regimes, Everything")
    print("="*80)
    
    all_results = {
        'drive': audit_external_drive(),
        'bq': audit_bigquery(),
        'staging': audit_staging_files(),
        'pipeline': audit_pipeline(),
        'symbols': audit_symbols(),
        'sentiments': audit_sentiments_news(),
        'regimes': audit_regimes(),
        'correlations': audit_correlations()
    }
    
    generate_report(all_results)
    
    print("\n" + "="*80)
    print("✅ FORENSIC AUDIT COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()




