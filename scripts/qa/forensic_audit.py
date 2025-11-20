#!/usr/bin/env python3
"""
Forensic Data Inventory - Phase 0.2
Audit existing data on external drive and identify gaps.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

def audit_existing_exports():
    """Check what training files already exist"""
    print("\n" + "="*80)
    print("FORENSIC AUDIT: EXISTING TRAINING EXPORTS")
    print("="*80)
    
    exports_dir = DRIVE / "TrainingData/exports"
    
    if not exports_dir.exists():
        print("❌ Exports directory not found")
        return []
    
    files_found = []
    
    for f in sorted(exports_dir.glob("*.parquet")):
        try:
            df = pd.read_parquet(f)
            date_col = 'date' if 'date' in df.columns else df.columns[0]
            
            info = {
                'file': f.name,
                'rows': len(df),
                'cols': len(df.columns),
                'size_mb': f.stat().st_size / 1024 / 1024,
                'min_date': df[date_col].min() if date_col in df.columns else 'N/A',
                'max_date': df[date_col].max() if date_col in df.columns else 'N/A',
            }
            
            files_found.append(info)
            
            print(f"\n{f.name}:")
            print(f"  Rows: {info['rows']:,}")
            print(f"  Cols: {info['cols']}")
            print(f"  Size: {info['size_mb']:.1f} MB")
            print(f"  Date range: {info['min_date']} to {info['max_date']}")
            
        except Exception as e:
            print(f"\n❌ {f.name}: Error reading - {e}")
    
    return files_found

def audit_raw_data():
    """Check what raw data sources exist"""
    print("\n" + "="*80)
    print("FORENSIC AUDIT: RAW DATA SOURCES")
    print("="*80)
    
    raw_dir = DRIVE / "TrainingData/raw"
    
    if not raw_dir.exists():
        print("❌ Raw directory not found")
        return []
    
    raw_files = []
    
    for f in sorted(raw_dir.glob("*.parquet")):
        try:
            df = pd.read_parquet(f)
            
            info = {
                'file': f.name,
                'rows': len(df),
                'cols': len(df.columns),
                'size_mb': f.stat().st_size / 1024 / 1024,
            }
            
            raw_files.append(info)
            
            print(f"\n{f.name}:")
            print(f"  Rows: {info['rows']:,}")
            print(f"  Cols: {info['cols']}")
            print(f"  Size: {info['size_mb']:.1f} MB")
            
        except Exception as e:
            print(f"\n❌ {f.name}: Error reading - {e}")
    
    return raw_files

def create_gap_analysis(exports, raw_files):
    """Identify what we need to collect"""
    print("\n" + "="*80)
    print("GAP ANALYSIS")
    print("="*80)
    
    # Check for historical coverage
    has_25yr_data = any(
        info.get('min_date', 'N/A') != 'N/A' and 
        str(info['min_date']).startswith('2000')
        for info in exports
    )
    
    print(f"\n📊 CURRENT STATE:")
    print(f"  Existing exports: {len(exports)} files")
    print(f"  Raw data files: {len(raw_files)} files")
    print(f"  25-year coverage: {'✅ YES' if has_25yr_data else '❌ NO (only 2020+)'}")
    
    print(f"\n📋 GAPS TO FILL:")
    print(f"  {'✅' if has_25yr_data else '❌'} Historical data (2000-2019)")
    print(f"  ❌ FRED macro data (30+ series)")
    print(f"  ❌ NOAA weather data")
    print(f"  ❌ CFTC positioning data")
    print(f"  ❌ USDA crop reports")
    print(f"  ❌ EIA biofuel data")
    print(f"  ❌ China demand composite")
    print(f"  ❌ Tariff intelligence")
    print(f"  ❌ Substitute oils data")
    print(f"  ❌ Biofuel policy prices")
    
    print(f"\n📌 DECISION:")
    if has_25yr_data:
        print(f"  KEEP existing exports, ENHANCE with new features")
    else:
        print(f"  REBUILD from scratch with 25-year data")
    
    return {
        'has_25yr_data': has_25yr_data,
        'existing_exports': len(exports),
        'raw_files': len(raw_files),
        'action': 'enhance' if has_25yr_data else 'rebuild'
    }

def main():
    print("\n" + "="*80)
    print("PHASE 0: FORENSIC DATA INVENTORY")
    print("="*80)
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Location: {DRIVE}")
    
    # Audit
    exports = audit_existing_exports()
    raw_files = audit_raw_data()
    gap_analysis = create_gap_analysis(exports, raw_files)
    
    # Save report
    report_file = DRIVE / "TrainingData/forensic_audit_20251116.json"
    import json
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'exports': exports,
            'raw_files': raw_files,
            'gap_analysis': gap_analysis
        }, f, indent=2, default=str)
    
    print(f"\n✅ Audit complete. Report saved to: {report_file}")
    
    return gap_analysis

if __name__ == '__main__':
    main()







