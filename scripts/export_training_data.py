#!/usr/bin/env python3
"""
Export Training Data from BigQuery to Parquet
Exports all training datasets to external drive for local training
"""
from google.cloud import bigquery
from datetime import datetime
import os
import sys
from pathlib import Path

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"

# External drive paths
EXTERNAL_DRIVE = os.getenv("EXTERNAL_DRIVE", "/Volumes/Satechi Hub")
CBI_V14_REPO = os.getenv("CBI_V14_REPO", f"{EXTERNAL_DRIVE}/Projects/CBI-V14")
TRAINING_DATA_EXPORTS = f"{CBI_V14_REPO}/TrainingData/exports"
TRAINING_DATA_RAW = f"{CBI_V14_REPO}/TrainingData/raw"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("📤 EXPORTING TRAINING DATA FROM BIGQUERY TO PARQUET")
print("="*80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Project: {PROJECT_ID}")
print(f"Dataset: {DATASET_ID}")
print(f"Export Directory: {TRAINING_DATA_EXPORTS}")
print("="*80)

# Ensure directories exist
os.makedirs(TRAINING_DATA_EXPORTS, exist_ok=True)
os.makedirs(TRAINING_DATA_RAW, exist_ok=True)

# Tables to export
EXPORT_CONFIG = [
    {
        'table': 'trump_rich_2023_2025',
        'output_file': f'{TRAINING_DATA_EXPORTS}/trump_rich_2023_2025.parquet',
        'description': 'Trump-era training table (42 features, 782 rows)'
    },
    {
        'table': 'production_training_data_1w',
        'output_file': f'{TRAINING_DATA_EXPORTS}/production_training_data_1w.parquet',
        'description': '1W horizon training data (290 features)'
    },
    {
        'table': 'production_training_data_1m',
        'output_file': f'{TRAINING_DATA_EXPORTS}/production_training_data_1m.parquet',
        'description': '1M horizon training data (290 features)'
    },
    {
        'table': 'production_training_data_3m',
        'output_file': f'{TRAINING_DATA_EXPORTS}/production_training_data_3m.parquet',
        'description': '3M horizon training data (290 features)'
    },
    {
        'table': 'production_training_data_6m',
        'output_file': f'{TRAINING_DATA_EXPORTS}/production_training_data_6m.parquet',
        'description': '6M horizon training data (290 features)'
    },
    {
        'table': 'production_training_data_12m',
        'output_file': f'{TRAINING_DATA_EXPORTS}/production_training_data_12m.parquet',
        'description': '12M horizon training data (290 features)'
    }
]

def export_table_to_parquet(table_name, output_path, description):
    """Export a BigQuery table to Parquet format"""
    print(f"\n{'='*80}")
    print(f"📤 EXPORTING: {table_name}")
    print(f"   {description}")
    print(f"   Output: {output_path}")
    print(f"{'='*80}")
    
    try:
        # Check table exists
        query = f"""
        SELECT COUNT(*) as table_exists
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table_name}'
        """
        result = client.query(query).to_dataframe()
        
        if result.iloc[0]['table_exists'] == 0:
            print(f"  ⚠️  Table '{table_name}' does not exist - SKIPPING")
            return False
        
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        count_result = client.query(count_query).to_dataframe()
        row_count = int(count_result.iloc[0]['row_count'])
        
        print(f"  📊 Rows to export: {row_count:,}")
        
        if row_count == 0:
            print(f"  ⚠️  Table is empty - SKIPPING")
            return False
        
        # Export to Parquet
        print(f"  ⏳ Exporting to Parquet...")
        
        query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}` ORDER BY date"
        
        # Use to_dataframe() and save as Parquet
        df = client.query(query).to_dataframe()
        
        # Save to Parquet
        df.to_parquet(output_path, index=False, engine='pyarrow')
        
        # Verify file was created
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"  ✅ Export complete: {file_size:.2f} MB")
        print(f"  📊 Exported {len(df):,} rows × {len(df.columns)} columns")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Export failed: {e}")
        return False

def export_historical_data():
    """Export full historical dataset (125 years) with regime labels"""
    print(f"\n{'='*80}")
    print(f"📤 EXPORTING: Full Historical Dataset (125 years)")
    print(f"   Output: {TRAINING_DATA_RAW}/historical_full.parquet")
    print(f"{'='*80}")
    
    try:
        # Export from forecasting_data_warehouse
        # This is a complex query - adjust based on actual schema
        query = """
        SELECT 
            date,
            zl_price as close_price,
            -- Add regime labels based on date ranges
            CASE
                WHEN date >= '2023-01-01' THEN 'trump_2.0'
                WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN 'trade_war'
                WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 'inflation'
                WHEN date >= '2008-01-01' AND date < '2009-01-01' OR 
                     date >= '2020-01-01' AND date < '2021-01-01' THEN 'crisis'
                ELSE 'historical'
            END as regime
        FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
        WHERE date IS NOT NULL
        ORDER BY date
        """
        
        print(f"  ⏳ Querying historical data...")
        df = client.query(query).to_dataframe()
        
        output_path = f"{TRAINING_DATA_RAW}/historical_full.parquet"
        df.to_parquet(output_path, index=False, engine='pyarrow')
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"  ✅ Export complete: {file_size:.2f} MB")
        print(f"  📊 Exported {len(df):,} rows × {len(df.columns)} columns")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Historical export failed: {e}")
        print(f"  ⚠️  Note: Historical export may need schema adjustments")
        return False

def export_regime_datasets():
    """Export regime-specific datasets"""
    print(f"\n{'='*80}")
    print(f"📤 EXPORTING: Regime-Specific Datasets")
    print(f"{'='*80}")
    
    regimes = [
        {
            'name': 'trump_2.0_2023_2025',
            'date_filter': "date >= '2023-01-01' AND date < '2026-01-01'",
            'weight': 5000
        },
        {
            'name': 'trade_war_2017_2019',
            'date_filter': "date >= '2017-01-01' AND date < '2020-01-01'",
            'weight': 1500
        },
        {
            'name': 'inflation_2021_2022',
            'date_filter': "date >= '2021-01-01' AND date < '2023-01-01'",
            'weight': 1200
        },
        {
            'name': 'crisis_2008_2020',
            'date_filter': "(date >= '2008-01-01' AND date < '2009-01-01') OR (date >= '2020-01-01' AND date < '2021-01-01')",
            'weight': 500
        },
        {
            'name': 'historical_pre2000',
            'date_filter': "date < '2000-01-01'",
            'weight': 50
        }
    ]
    
    results = []
    
    for regime in regimes:
        try:
            print(f"\n  📤 Exporting {regime['name']} (weight ×{regime['weight']})...")
            
            # Use production_training_data_1m as base (has all features)
            query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET_ID}.production_training_data_1m`
            WHERE {regime['date_filter']}
            ORDER BY date
            """
            
            df = client.query(query).to_dataframe()
            
            if len(df) == 0:
                print(f"    ⚠️  No data for {regime['name']} - SKIPPING")
                continue
            
            output_path = f"{TRAINING_DATA_EXPORTS}/{regime['name']}.parquet"
            df.to_parquet(output_path, index=False, engine='pyarrow')
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"    ✅ Exported {len(df):,} rows ({file_size:.2f} MB)")
            
            results.append(True)
            
        except Exception as e:
            print(f"    ❌ Export failed: {e}")
            results.append(False)
    
    return all(results)

# Run exports
print("\n" + "="*80)
print("STARTING EXPORTS")
print("="*80)

export_results = []

# Export main training tables
for config in EXPORT_CONFIG:
    success = export_table_to_parquet(
        config['table'],
        config['output_file'],
        config['description']
    )
    export_results.append(success)

# Export historical data
historical_success = export_historical_data()
export_results.append(historical_success)

# Export regime-specific datasets
regime_success = export_regime_datasets()
export_results.append(regime_success)

# Final summary
print("\n" + "="*80)
print("📋 EXPORT SUMMARY")
print("="*80)

successful = sum(export_results)
total = len(export_results)

print(f"✅ Successful: {successful}/{total}")
print(f"❌ Failed: {total - successful}/{total}")

if successful == total:
    print("\n🎉 ALL EXPORTS COMPLETE!")
    print(f"📁 Files saved to: {TRAINING_DATA_EXPORTS}")
    print(f"📁 Historical data: {TRAINING_DATA_RAW}")
else:
    print("\n⚠️  SOME EXPORTS FAILED - Review errors above")
    sys.exit(1)

print("="*80)

