#!/usr/bin/env python3
"""
Forensic Data Inventory Script
Audits all existing parquet files and identifies gaps for 25-year enrichment
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
LOCAL_REPO = Path("/Users/kirkmusick/Documents/GitHub/CBI-V14")

def audit_parquet_file(file_path):
    """Audit a single parquet file."""
    try:
        df = pd.read_parquet(file_path)
        
        # Get date columns
        date_cols = [c for c in df.columns if 'date' in c.lower()]
        
        # Determine date range
        date_range = None
        if date_cols:
            for col in date_cols:
                try:
                    dates = pd.to_datetime(df[col])
                    date_range = {
                        'min': dates.min().strftime('%Y-%m-%d') if pd.notna(dates.min()) else None,
                        'max': dates.max().strftime('%Y-%m-%d') if pd.notna(dates.max()) else None
                    }
                    break
                except:
                    continue
        
        # Check for placeholder patterns
        placeholder_checks = {
            '0.5_values': 0,
            'allhistory_regime': 0,
            'weight_1': 0,
            'null_percentage': 0
        }
        
        # Check for 0.5 placeholder
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if (df[col] == 0.5).sum() > len(df) * 0.5:  # More than 50% are 0.5
                placeholder_checks['0.5_values'] += 1
        
        # Check for regime placeholders
        if 'market_regime' in df.columns:
            if (df['market_regime'] == 'allhistory').any():
                placeholder_checks['allhistory_regime'] = (df['market_regime'] == 'allhistory').sum()
        
        if 'training_weight' in df.columns:
            if (df['training_weight'] == 1).all():
                placeholder_checks['weight_1'] = len(df)
        
        # Calculate null percentage
        placeholder_checks['null_percentage'] = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        
        return {
            'file': str(file_path),
            'rows': len(df),
            'columns': len(df.columns),
            'date_range': date_range,
            'placeholder_checks': placeholder_checks,
            'column_sample': list(df.columns)[:10],
            'status': 'OK' if placeholder_checks['0.5_values'] == 0 and placeholder_checks['allhistory_regime'] == 0 else 'ISSUES'
        }
    except Exception as e:
        return {
            'file': str(file_path),
            'error': str(e),
            'status': 'ERROR'
        }

def audit_directory(base_path, pattern="*.parquet"):
    """Audit all parquet files in a directory."""
    results = []
    base = Path(base_path)
    
    if not base.exists():
        return results
    
    for file in base.rglob(pattern):
        # Skip .git and other system directories
        if '.git' in str(file) or '__pycache__' in str(file):
            continue
        
        print(f"Auditing: {file.name}")
        result = audit_parquet_file(file)
        results.append(result)
    
    return results

def generate_gap_analysis(audit_results):
    """Generate gap analysis from audit results."""
    
    gaps = {
        'missing_historical_data': [],
        'placeholder_issues': [],
        'schema_errors': [],
        'date_coverage_gaps': [],
        'recommendations': []
    }
    
    # Analyze results
    for result in audit_results:
        if result['status'] == 'ERROR':
            gaps['schema_errors'].append({
                'file': result['file'],
                'error': result.get('error', 'Unknown error')
            })
            continue
        
        # Check date ranges
        if result.get('date_range'):
            date_range = result['date_range']
            if date_range.get('min'):
                min_date = pd.to_datetime(date_range['min'])
                if min_date.year > 2000:
                    gaps['missing_historical_data'].append({
                        'file': result['file'],
                        'starts_at': date_range['min'],
                        'missing_years': 2000 - min_date.year
                    })
        
        # Check for placeholders
        if result['status'] == 'ISSUES':
            placeholder_checks = result.get('placeholder_checks', {})
            if placeholder_checks.get('allhistory_regime', 0) > 0:
                gaps['placeholder_issues'].append({
                    'file': result['file'],
                    'issue': f"{placeholder_checks['allhistory_regime']} rows with 'allhistory' regime"
                })
            if placeholder_checks.get('weight_1', 0) > 0:
                gaps['placeholder_issues'].append({
                    'file': result['file'],
                    'issue': f"All {placeholder_checks['weight_1']} rows have weight=1"
                })
    
    # Generate recommendations
    if gaps['schema_errors']:
        gaps['recommendations'].append("CRITICAL: Fix schema errors before proceeding")
    
    if gaps['missing_historical_data']:
        gaps['recommendations'].append("HIGH: Collect pre-2000 data from BigQuery historical tables")
    
    if gaps['placeholder_issues']:
        gaps['recommendations'].append("HIGH: Fix regime assignments and weights")
    
    # Check for specific data needs
    required_sources = [
        'FRED macro data (30+ series)',
        'Yahoo Finance (55 symbols, 2000-2025)',
        'NOAA weather data',
        'CFTC COT positioning',
        'USDA crop data',
        'EIA biofuel data'
    ]
    
    gaps['required_data_sources'] = required_sources
    
    return gaps

def main():
    """Main audit function."""
    
    print("=" * 60)
    print("FORENSIC DATA INVENTORY")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Audit external drive
    print("📁 Auditing External Drive TrainingData...")
    if EXTERNAL_DRIVE.exists():
        external_results = audit_directory(EXTERNAL_DRIVE / "TrainingData")
        all_results.extend(external_results)
        print(f"   Found {len(external_results)} files")
    else:
        print("   ⚠️ External drive not mounted")
    
    # Audit local repo TrainingData
    print("\n📁 Auditing Local Repo TrainingData...")
    local_results = audit_directory(LOCAL_REPO / "TrainingData")
    all_results.extend(local_results)
    print(f"   Found {len(local_results)} files")
    
    # Audit GPT_Data
    print("\n📁 Auditing GPT_Data...")
    gpt_results = audit_directory(LOCAL_REPO / "GPT_Data")
    all_results.extend(gpt_results)
    print(f"   Found {len(gpt_results)} files")
    
    # Generate gap analysis
    print("\n" + "=" * 60)
    print("GAP ANALYSIS")
    print("=" * 60)
    
    gaps = generate_gap_analysis(all_results)
    
    # Print summary
    print("\n📊 SUMMARY:")
    print(f"Total files audited: {len(all_results)}")
    print(f"Files with errors: {len(gaps['schema_errors'])}")
    print(f"Files with placeholder issues: {len(gaps['placeholder_issues'])}")
    print(f"Files missing historical data: {len(gaps['missing_historical_data'])}")
    
    print("\n⚠️ CRITICAL ISSUES:")
    for error in gaps['schema_errors'][:5]:  # Show first 5
        print(f"  - {Path(error['file']).name}: {error['error']}")
    
    print("\n📋 REQUIRED DATA SOURCES TO COLLECT:")
    for source in gaps['required_data_sources']:
        print(f"  - {source}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in gaps['recommendations']:
        print(f"  - {rec}")
    
    # Save detailed report
    report_path = LOCAL_REPO / "scripts/audits/forensic_inventory_report.json"
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files': len(all_results),
            'error_files': len(gaps['schema_errors']),
            'placeholder_files': len(gaps['placeholder_issues']),
            'missing_historical': len(gaps['missing_historical_data'])
        },
        'gaps': gaps,
        'detailed_results': all_results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Decision point
    print("\n" + "=" * 60)
    print("DECISION POINT")
    print("=" * 60)
    
    if gaps['schema_errors'] or gaps['placeholder_issues']:
        print("⚠️ RECOMMENDATION: REBUILD FROM SCRATCH")
        print("   - Too many schema/placeholder issues to fix incrementally")
        print("   - Better to start fresh with clean 25-year data pipeline")
    else:
        print("✅ Data quality acceptable - can proceed with enrichment")
    
    return report

if __name__ == "__main__":
    main()






