#!/usr/bin/env python3
"""
Process VIX data from Databento OPRA download.
Request ID: OPRA-20251120-U3F99GTFES

This script processes downloaded VIX data for macro volatility overlay. CVOL is discontinued.
"""

import json
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
REQUEST_ID = "OPRA-20251120-U3F99GTFES"
RAW_DIR = DRIVE / "TrainingData/raw/databento_vix" / REQUEST_ID
OUTPUT_DIR = DRIVE / "TrainingData/raw/databento_vix"
STAGING_DIR = DRIVE / "TrainingData/staging"

def process_vix_csv(csv_file):
    """Process VIX data from Databento OPRA CSV file."""
    print(f"\nProcessing CSV: {csv_file.name}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df):,} rows")
        
        # Filter for VIX symbols
        vix_df = df[df['symbol'].str.contains('VIX', case=False, na=False)].copy()
        print(f"✅ Found {len(vix_df):,} VIX records")
        
        if vix_df.empty:
            print("⚠️  No VIX records found in CSV")
            return None
        
        # Process timestamps
        vix_df['timestamp'] = pd.to_datetime(vix_df['ts_event'], errors='coerce')
        vix_df['date'] = vix_df['timestamp'].dt.date
        
        # Sort by timestamp
        vix_df = vix_df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"\nDate range: {vix_df['date'].min()} to {vix_df['date'].max()}")
        print(f"Columns: {list(vix_df.columns)}")
        
        # Save processed data
        output_file = OUTPUT_DIR / "vix_opra_processed.parquet"
        vix_df.to_parquet(output_file, index=False)
        print(f"\n✅ Saved: {output_file}")
        
        # Create daily aggregated VIX
        # CVOL discontinued; VIX used directly from source
        # For now, aggregate by date using close prices
        vix_daily = vix_df.groupby('date').agg({
            'close': 'last',  # Last price of day
            'open': 'first',  # First price of day
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
        }).reset_index()
        
        vix_daily.columns = ['date', 'vix_close', 'vix_open', 'vix_high', 'vix_low', 'vix_volume']
        
        # Save daily VIX
        daily_file = OUTPUT_DIR / "vix_daily_opra.parquet"
        vix_daily.to_parquet(daily_file, index=False)
        print(f"✅ Saved daily VIX: {daily_file}")
        print(f"   Rows: {len(vix_daily)}, Date range: {vix_daily['date'].min()} to {vix_daily['date'].max()}")
        
        return vix_daily
        
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_vix_files(data_dir):
    """Process VIX data from Databento OPRA JSON or CSV files."""
    print("="*80)
    print("PROCESSING DATABENTO VIX DATA")
    print("="*80)
    print(f"Source: {data_dir}")
    
    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        print(f"\nPlease download the data first:")
        print(f"  1. Go to: https://databento.com/portal/batch/jobs/{REQUEST_ID}")
        print(f"  2. Click 'Download'")
        print(f"  3. Extract to: {data_dir}")
        return None
    
    # Find CSV files first (OPRA data often comes as CSV)
    csv_files = list(data_dir.rglob("*.csv"))
    json_files = list(data_dir.rglob("*.json"))
    
    # Process CSV files if found
    if csv_files:
        print(f"\nFound {len(csv_files)} CSV file(s)")
        return process_vix_csv(csv_files[0])
    
    if not json_files:
        print(f"❌ No JSON or CSV files found in {data_dir}")
        return None
    
    print(f"\nFound {len(json_files)} JSON files")
    
    # Process files
    vix_records = []
    processed_files = 0
    
    for json_file in json_files:
        # Skip metadata files
        if any(skip in json_file.name.lower() for skip in ['manifest', 'metadata', 'symbology', 'condition']):
            continue
        
        try:
            with open(json_file, 'r') as f:
                file_records = 0
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        
                        # OPRA data structure - check for VIX-related fields
                        # Common fields: ts_event, symbol, instrument_id, price, size, etc.
                        symbol = record.get('symbol', '')
                        instrument_id = record.get('instrument_id', '')
                        
                        # Check if VIX-related
                        if 'VIX' in str(symbol).upper() or 'VIX' in str(instrument_id):
                            # Extract relevant fields
                            vix_record = {
                                'timestamp': record.get('ts_event'),
                                'symbol': symbol,
                                'instrument_id': instrument_id,
                                'price': record.get('price'),
                                'size': record.get('size'),
                                'volume': record.get('volume'),
                                'open': record.get('open'),
                                'high': record.get('high'),
                                'low': record.get('low'),
                                'close': record.get('close'),
                            }
                            
                            # Add any other relevant fields
                            for key in ['bid_px', 'ask_px', 'bid_size', 'ask_size', 'open_interest']:
                                if key in record:
                                    vix_record[key] = record[key]
                            
                            vix_records.append(vix_record)
                            file_records += 1
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        if line_num <= 5:  # Only log first few errors
                            print(f"  ⚠️  Error parsing line {line_num} in {json_file.name}: {e}")
                
                if file_records > 0:
                    processed_files += 1
                    if processed_files % 10 == 0:
                        print(f"  Processed {processed_files} files, {len(vix_records)} VIX records...")
        
        except Exception as e:
            print(f"  ⚠️  Error reading {json_file.name}: {e}")
            continue
    
    if not vix_records:
        print("\n⚠️  No VIX records found")
        print("\nChecking file structure...")
        
        # Sample first file
        if json_files:
            sample_file = json_files[0]
            print(f"\nSample from {sample_file.name}:")
            with open(sample_file, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 3:
                        break
                    if line.strip():
                        try:
                            sample = json.loads(line)
                            print(f"  Keys: {list(sample.keys())[:15]}")
                            print(f"  Sample values: {str(sample)[:200]}")
                        except:
                            print(f"  Raw line: {line[:200]}")
        
        return None
    
    print(f"\n✅ Processed {processed_files} files")
    print(f"✅ Found {len(vix_records)} VIX records")
    
    # Convert to DataFrame
    df = pd.DataFrame(vix_records)
    
    # Process timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ns', errors='coerce')
        df['date'] = df['timestamp'].dt.date
    
    # Sort by timestamp
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"\nDataFrame: {len(df)} rows × {len(df.columns)} columns")
    if 'date' in df.columns:
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Save processed data
    output_file = OUTPUT_DIR / "vix_opra_processed.parquet"
    df.to_parquet(output_file, index=False)
    print(f"\n✅ Saved: {output_file}")
    
    # Create daily aggregated VIX
    if 'date' in df.columns and 'close' in df.columns:
        vix_daily = df.groupby('date').agg({
            'close': 'last',  # Last price of day
            'open': 'first',  # First price of day
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
            'open_interest': 'last',
        }).reset_index()
        
        vix_daily.columns = ['date', 'vix_close', 'vix_open', 'vix_high', 'vix_low', 'vix_volume', 'vix_oi']
        
        # Save daily VIX
        daily_file = OUTPUT_DIR / "vix_daily_opra.parquet"
        vix_daily.to_parquet(daily_file, index=False)
        print(f"✅ Saved daily VIX: {daily_file}")
        print(f"   Rows: {len(vix_daily)}, Date range: {vix_daily['date'].min()} to {vix_daily['date'].max()}")
        
        return vix_daily
    
    return df

def integrate_vix_to_volatility(vix_daily_df):
    """Integrate VIX data into volatility staging."""
    print("\n" + "="*80)
    print("INTEGRATING VIX INTO VOLATILITY STAGING")
    print("="*80)
    
    # Load existing volatility staging
    vol_file = STAGING_DIR / "volatility_features.parquet"
    
    if not vol_file.exists():
        print(f"⚠️  Volatility staging not found: {vol_file}")
        print("   VIX data saved separately, will be integrated when volatility staging is regenerated")
        return
    
    vol_df = pd.read_parquet(vol_file)
    print(f"Loaded volatility staging: {len(vol_df)} rows")
    
    # Merge VIX data
    if 'date' in vol_df.columns and 'date' in vix_daily_df.columns:
        # Convert dates
        vol_df['date'] = pd.to_datetime(vol_df['date']).dt.date
        vix_daily_df['date'] = pd.to_datetime(vix_daily_df['date']).dt.date
        
        # Merge
        vol_df = vol_df.merge(
            vix_daily_df[['date', 'vix_close', 'vix_open', 'vix_high', 'vix_low']],
            on='date',
            how='left',
            suffixes=('', '_opra')
        )
        
        # Update VIX columns if OPRA data is better
        if 'vix_close_opra' in vol_df.columns:
            vol_df['vol_vix_level'] = vol_df['vix_close_opra'].fillna(vol_df.get('vol_vix_level', 0))
            vol_df = vol_df.drop(columns=['vix_close_opra', 'vix_open_opra', 'vix_high_opra', 'vix_low_opra'])
        
        # Save updated volatility
        vol_df.to_parquet(vol_file, index=False)
        print(f"✅ Updated volatility staging: {vol_file}")
        print(f"   Rows: {len(vol_df)}, Columns: {len(vol_df.columns)}")
    else:
        print("⚠️  Date columns not found, cannot merge")

def main():
    print("="*80)
    print("DATABENTO VIX PROCESSOR")
    print("="*80)
    print(f"Request ID: {REQUEST_ID}")
    print(f"Purpose: Process VIX for macro volatility overlay (no CVOL)")
    print()
    
    # Process VIX files
    vix_df = process_vix_files(RAW_DIR)
    
    if vix_df is None:
        print("\n⚠️  Processing failed or no data found")
        print("\nManual download instructions:")
        print(f"  1. Go to: https://databento.com/portal/batch/jobs/{REQUEST_ID}")
        print(f"  2. Click 'Download' button")
        print(f"  3. Save zip file to ~/Downloads")
        print(f"  4. Extract:")
        print(f"     cd ~/Downloads")
        print(f"     unzip -o {REQUEST_ID}.zip -d \"{RAW_DIR}\"")
        print(f"  5. Run this script again:")
        print(f"     python3 scripts/ingest/process_databento_vix.py")
        return 1
    
    # Integrate into volatility staging
    if isinstance(vix_df, pd.DataFrame) and 'date' in vix_df.columns:
        integrate_vix_to_volatility(vix_df)
    
    print("\n" + "="*80)
    print("✅ VIX DATA PROCESSED")
    print("="*80)
    print(f"\nNext steps:")
    print(f"  1. Review: {OUTPUT_DIR / 'vix_daily_opra.parquet'}")
    print(f"  2. Regenerate volatility staging to include OPRA VIX")
    print(f"  3. Feed volatility overlay (no CVOL)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
