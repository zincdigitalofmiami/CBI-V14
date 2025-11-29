#!/usr/bin/env python3
"""
Export CBI-V14 data to V15 external drive structure
Exports critical data from BigQuery and organizes calculator code
"""
import os
import sys
from pathlib import Path
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import shutil

PROJECT_ID = "cbi-v14"
V14_ROOT = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
V15_ROOT = Path("/Volumes/Satechi Hub/Projects/CBI-V15")

# BigQuery tables to export
BQ_EXPORTS = {
    "02_Data/FRED/fred_economic.parquet": "raw_intelligence.fred_economic",
    "02_Data/Databento/databento_futures_ohlcv_1d.parquet": "market_data.databento_futures_ohlcv_1d",
    "02_Data/ScrapeCreators/news_bucketed.parquet": "raw_intelligence.news_bucketed",
    "03_Features/zl_daily_v1.parquet": "features.zl_daily_v1",
    "03_Features/macro_features_daily.parquet": "features.macro_features_daily",
    "03_Features/volatility_signals.parquet": "features.volatility_signals",
    "03_Features/fx_features_daily.parquet": "features.fx_features_daily",
    "04_Training_Exports/zl_training_prod_allhistory_1w.parquet": "training.zl_training_prod_allhistory_1w",
    "04_Training_Exports/zl_training_prod_allhistory_1m.parquet": "training.zl_training_prod_allhistory_1m",
    "04_Training_Exports/zl_training_prod_allhistory_3m.parquet": "training.zl_training_prod_allhistory_3m",
    "04_Training_Exports/zl_training_prod_allhistory_6m.parquet": "training.zl_training_prod_allhistory_6m",
}

# Files to copy from V14
CODE_COPIES = {
    "01_Calculators/Palm_Features/palm.py": "cbi_v14/features/palm.py",
    "01_Calculators/Technical_Indicators/feature_calculations.py": "scripts/features/feature_calculations.py",
    "01_Calculators/Trump_Predictor/trump_action_predictor.py": "scripts/predictions/trump_action_predictor.py",
    "01_Calculators/Trump_Predictor/zl_impact_predictor.py": "scripts/predictions/zl_impact_predictor.py",
    "01_Calculators/Fibonacci/fibonacci_levels.sql": "sql/features/fib_levels_daily.sql",
    "07_Scripts/ingest/collect_fred_comprehensive.py": "scripts/ingest/collect_fred_comprehensive.py",
    "07_Scripts/training/train_zl_baselines.py": "scripts/train/train_zl_baselines.py",
    "07_Scripts/training/export_training_data.py": "scripts/export_training_data.py",
}

# Docs to copy
DOC_COPIES = {
    "06_Documentation/Dataform_Architecture/DATAFORM_STRUCTURE_REVISED_20251124.md": "Quant Check Plan/DATAFORM_STRUCTURE_REVISED_20251124.md",
    "06_Documentation/Plans/MASTER_PLAN.md": "docs/plans/MASTER_PLAN.md",
    "06_Documentation/Plans/TRAINING_PLAN.md": "docs/plans/TRAINING_PLAN.md",
    "06_Documentation/Reference/FIBONACCI_MATH.md": "docs/reference/FIBONACCI_MATH.md",
}


def create_v15_structure():
    """Create V15 folder structure"""
    print("Creating V15 folder structure...")
    folders = [
        "01_Calculators/Crush_Margin",
        "01_Calculators/Palm_Features",
        "01_Calculators/Fibonacci",
        "01_Calculators/Trump_Predictor",
        "01_Calculators/Technical_Indicators",
        "01_Calculators/Cross_Asset_Correlations",
        "02_Data/FRED",
        "02_Data/Databento",
        "02_Data/ScrapeCreators",
        "02_Data/USDA",
        "02_Data/CFTC",
        "02_Data/Weather",
        "02_Data/Vegas_Intel",
        "03_Features",
        "04_Training_Exports",
        "05_Models/zl_baselines",
        "06_Documentation/Dataform_Architecture",
        "06_Documentation/Plans",
        "06_Documentation/Reference",
        "07_Scripts/ingest",
        "07_Scripts/training",
    ]
    
    for folder in folders:
        (V15_ROOT / folder).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {folder}")


def export_bq_table(output_path: Path, table_ref: str):
    """Export BigQuery table to Parquet"""
    client = bigquery.Client(project=PROJECT_ID)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting {table_ref} → {output_path.name}")
    try:
        query = f"SELECT * FROM `{PROJECT_ID}.{table_ref}`"
        df = client.query(query).to_dataframe()
        
        if df.empty:
            print(f"  ⚠️  No data")
            return False
        
        # Convert date columns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'timestamp' in col.lower()]
        for col in date_cols:
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass
        
        df.to_parquet(output_path, index=False, engine='pyarrow')
        print(f"  ✅ {len(df):,} rows, {len(df.columns)} columns")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def copy_from_v14(dest_path: Path, source_path: Path):
    """Copy file from V14 to V15"""
    source = V14_ROOT / source_path
    dest = V15_ROOT / dest_path
    
    if not source.exists():
        print(f"  ⚠️  Source not found: {source}")
        return False
    
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(f"  ✅ Copied: {source_path} → {dest_path}")
    return True


def create_readme(folder_path: Path, content: str):
    """Create README file"""
    readme_path = folder_path / "README.md"
    readme_path.write_text(content)
    print(f"  ✅ Created README: {readme_path}")


def main():
    print("="*80)
    print("CBI-V15 EXPORT SCRIPT")
    print("="*80)
    print()
    
    # Check external drive
    if not V14_ROOT.exists():
        print(f"❌ V14 folder not found: {V14_ROOT}")
        sys.exit(1)
    
    if not V15_ROOT.parent.exists():
        print(f"❌ External drive not found: {V15_ROOT.parent}")
        sys.exit(1)
    
    # Create structure
    create_v15_structure()
    print()
    
    # Export from BigQuery
    print("="*80)
    print("EXPORTING FROM BIGQUERY")
    print("="*80)
    client = bigquery.Client(project=PROJECT_ID)
    
    success_count = 0
    for output_path_str, table_ref in BQ_EXPORTS.items():
        output_path = V15_ROOT / output_path_str
        if export_bq_table(output_path, table_ref):
            success_count += 1
        print()
    
    print(f"✅ Exported {success_count}/{len(BQ_EXPORTS)} tables")
    print()
    
    # Copy code files
    print("="*80)
    print("COPYING CODE FILES")
    print("="*80)
    code_success = 0
    for dest, source in CODE_COPIES.items():
        if copy_from_v14(Path(dest), Path(source)):
            code_success += 1
    print(f"✅ Copied {code_success}/{len(CODE_COPIES)} files")
    print()
    
    # Copy docs
    print("="*80)
    print("COPYING DOCUMENTATION")
    print("="*80)
    doc_success = 0
    for dest, source in DOC_COPIES.items():
        if copy_from_v14(Path(dest), Path(source)):
            doc_success += 1
    print(f"✅ Copied {doc_success}/{len(DOC_COPIES)} files")
    print()
    
    # Create README files
    print("="*80)
    print("CREATING README FILES")
    print("="*80)
    
    create_readme(V15_ROOT / "02_Data/FRED", 
        "# FRED Economic Data\n\nExported from BigQuery `raw_intelligence.fred_economic`\n\nDate: {}\n".format(datetime.now().isoformat()))
    
    create_readme(V15_ROOT / "02_Data/Databento",
        "# Databento Market Data\n\nExported from BigQuery `market_data.databento_futures_ohlcv_1d`\n\nDate: {}\n".format(datetime.now().isoformat()))
    
    create_readme(V15_ROOT,
        "# CBI-V15 Data Export\n\nExported from CBI-V14 on {}\n\n## Structure\n\n- `01_Calculators/` - Calculation logic (SQL + Python)\n- `02_Data/` - Raw data exports\n- `03_Features/` - Feature engineering outputs\n- `04_Training_Exports/` - Training-ready datasets\n- `05_Models/` - Model artifacts\n- `06_Documentation/` - Architecture docs\n- `07_Scripts/` - Ingestion and training scripts\n".format(datetime.now().isoformat()))
    
    # Write export date
    (V15_ROOT / "export_date.txt").write_text(f"Exported: {datetime.now().isoformat()}\n")
    
    print()
    print("="*80)
    print("EXPORT COMPLETE")
    print("="*80)
    print(f"V15 location: {V15_ROOT}")


if __name__ == "__main__":
    main()

