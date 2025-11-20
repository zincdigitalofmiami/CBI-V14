#!/usr/bin/env python3
"""
Download VIX data from Databento download center using request ID.
Request ID: OPRA-20251120-U3F99GTFES
This ingests VIX for macro volatility overlay. CVOL is discontinued.
"""

import os
import sys
from pathlib import Path
import subprocess
import json
import zipfile
import shutil

try:
    import databento as db
except ImportError:
    print("Installing databento...")
    subprocess.run([sys.executable, "-m", "pip", "install", "databento"], check=True)
    import databento as db

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.keychain_manager import get_api_key

# Configuration
DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
OUTPUT_DIR = DRIVE / "TrainingData/raw/databento_vix"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Request ID from download center
REQUEST_ID = "OPRA-20251120-U3F99GTFES"

def get_api_key():
    """Get Databento API key from keychain or environment."""
    # Try keychain manager first
    try:
        key = get_api_key("DATABENTO_API_KEY")
        if key:
            return key
    except:
        pass
    
    # Try macOS keychain
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-w", "-a", "databento", "-s", "databento_api_key"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Try environment
    if os.environ.get("DATABENTO_API_KEY"):
        return os.environ["DATABENTO_API_KEY"]
    
    # Try file
    key_file = Path.home() / ".databento.key"
    if key_file.exists():
        return key_file.read_text().strip()
    
    return None

def download_from_request_id(client, request_id, output_dir):
    """Download data from Databento using request/job ID."""
    print(f"Downloading request: {request_id}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Try to get job info first
        try:
            job = client.batch.get_job(request_id)
            print(f"Job status: {job.state}")
            print(f"Job ID: {job.id}")
            
            if job.state != 'done':
                print(f"⚠️  Job status is '{job.state}', not 'done'")
                print("   Data may not be ready yet.")
                return False
        except Exception as e:
            print(f"⚠️  Could not get job info: {e}")
            print("   Proceeding with download attempt...")
        
        # Download the job
        print("\nDownloading files...")
        download_path = output_dir / f"{request_id}.zip"
        
        # Use batch download method
        try:
            # Download via API
            client.batch.download(request_id, str(download_path))
            print(f"✅ Downloaded to: {download_path}")
        except Exception as e:
            print(f"❌ API download failed: {e}")
            print("\nAlternative: Download manually from portal:")
            print(f"  https://databento.com/portal/batch/jobs/{request_id}")
            print(f"\nThen extract to: {output_dir}")
            return False
        
        # Extract if zip file
        if download_path.exists() and download_path.suffix == '.zip':
            print(f"\nExtracting {download_path.name}...")
            extract_dir = output_dir / request_id
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"✅ Extracted to: {extract_dir}")
            
            # List extracted files
            files = list(extract_dir.rglob("*"))
            print(f"\nExtracted {len(files)} files")
            for f in files[:10]:
                if f.is_file():
                    size_mb = f.stat().st_size / (1024 * 1024)
                    print(f"  - {f.name}: {size_mb:.2f} MB")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
            
            return True
        else:
            print(f"⚠️  Downloaded file is not a zip: {download_path}")
            return False
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_vix_data(data_dir):
    """Process VIX data from Databento OPRA files."""
    print("\n" + "="*80)
    print("PROCESSING VIX DATA")
    print("="*80)
    
    # Find all JSON files
    json_files = list(data_dir.rglob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found")
        return None
    
    print(f"Found {len(json_files)} JSON files")
    
    # Process files to extract VIX data
    import pandas as pd
    
    vix_records = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                # Databento JSON files can be line-delimited or single JSON
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        
                        # Check if this is VIX-related data
                        # OPRA data structure varies - need to check actual format
                        if 'symbol' in record:
                            symbol = record['symbol']
                            if 'VIX' in str(symbol).upper() or 'VIX' in str(record.get('instrument_id', '')):
                                vix_records.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️  Error reading {json_file.name}: {e}")
            continue
    
    if not vix_records:
        print("⚠️  No VIX records found in files")
        print("   Files may need different parsing - checking file structure...")
        
        # Try to read first file to understand structure
        if json_files:
            sample_file = json_files[0]
            print(f"\nSample file structure ({sample_file.name}):")
            with open(sample_file, 'r') as f:
                first_line = f.readline()
                try:
                    sample = json.loads(first_line)
                    print(f"  Keys: {list(sample.keys())[:10]}")
                except:
                    print(f"  First 200 chars: {first_line[:200]}")
        
        return None
    
    print(f"✅ Found {len(vix_records)} VIX records")
    
    # Convert to DataFrame
    df = pd.DataFrame(vix_records)
    
    # Save processed VIX data
    output_file = OUTPUT_DIR / "vix_processed.parquet"
    df.to_parquet(output_file, index=False)
    print(f"✅ Saved processed VIX data: {output_file}")
    print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
    
    return df

def main():
    print("="*80)
    print("DATABENTO VIX DOWNLOAD - OPRA DATA")
    print("="*80)
    print(f"\nRequest ID: {REQUEST_ID}")
    print(f"Purpose: VIX data for macro volatility overlay (no CVOL)")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ DATABENTO_API_KEY not found!")
        print("\nSet your API key:")
        print("  security add-generic-password -a databento -s databento_api_key -w 'YOUR_KEY' -U")
        print("\nOr check manually:")
        print(f"  https://databento.com/portal/batch/jobs/{REQUEST_ID}")
        return 1
    
    print("✅ API key found")
    
    # Initialize client
    try:
        client = db.Historical(api_key)
        print("✅ Connected to Databento")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Download data
    success = download_from_request_id(client, REQUEST_ID, OUTPUT_DIR)
    
    if not success:
        print("\n⚠️  Automatic download failed")
        print(f"Please download manually from: https://databento.com/portal/batch/jobs/{REQUEST_ID}")
        print(f"Then extract to: {OUTPUT_DIR / REQUEST_ID}")
        return 1
    
    # Process VIX data
    data_dir = OUTPUT_DIR / REQUEST_ID
    if data_dir.exists():
        vix_df = process_vix_data(data_dir)
        
        if vix_df is not None:
            print("\n" + "="*80)
            print("✅ VIX DATA DOWNLOADED AND PROCESSED")
            print("="*80)
            print(f"Next steps:")
            print(f"  1. Review processed data: {OUTPUT_DIR / 'vix_processed.parquet'}")
            print(f"  2. Integrate into volatility staging")
            print(f"  3. Use in volatility overlay (no CVOL)")
        else:
            print("\n⚠️  VIX data processing needs manual review")
            print(f"   Check files in: {data_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())




