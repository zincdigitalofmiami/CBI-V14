#!/usr/bin/env python3
"""
run_ingestion.py - Runner script for Cloud Shell
Execute this to process all your commodity CSV files
"""

import os
import sys
from datetime import datetime

# First, install required packages if needed
def install_requirements():
    """Install required packages"""
    import subprocess
    packages = ['pandas', 'numpy', 'google-cloud-storage', 'google-cloud-bigquery', 'chardet']
    
    print("📦 Checking/Installing required packages...")
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install requirements first
install_requirements()

# Now import everything
import pandas as pd
import numpy as np
from google.cloud import storage
from google.cloud import bigquery
import json
import logging

# Import our intelligent ingestion system
from intelligent_ingestion import IntelligentIngestionSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main execution function with menu
    """
    print("\n" + "="*60)
    print("🚀 CBI-V14 INTELLIGENT INGESTION SYSTEM")
    print("="*60)
    print("\nThis system will process your commodity CSV files:")
    print("  • Auto-detect commodity types (ZL, ZC, ZS, etc.)")
    print("  • Handle various CSV formats and date formats")
    print("  • Clean and standardize data")
    print("  • Load to BigQuery for analysis")
    print("\n" + "="*60)
    
    # Configuration
    PROJECT_ID = 'cbi-v14'
    BUCKET_NAME = 'forecasting-app-raw-data-bucket'
    DATASET_ID = 'forecasting_data_warehouse'
    
    print(f"\nConfiguration:")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Dataset: {DATASET_ID}")
    
    # Initialize the ingestion system
    try:
        ingester = IntelligentIngestionSystem(
            project_id=PROJECT_ID,
            bucket_name=BUCKET_NAME,
            dataset_id=DATASET_ID
        )
        print("\n✓ Ingestion system initialized successfully")
    except Exception as e:
        print(f"\n❌ Error initializing: {e}")
        print("\nMake sure you're authenticated:")
        print("  gcloud auth application-default login")
        return
    
    # Menu
    while True:
        print("\n" + "-"*40)
        print("MENU:")
        print("1. Scan bucket for files (dry run)")
        print("2. Process ALL historical files")
        print("3. Process specific file")
        print("4. Check ingestion status")
        print("5. Show sample data from BigQuery")
        print("6. Exit")
        print("-"*40)
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            # Dry run to see what files will be processed
            print("\n🔍 Scanning bucket for CSV files...")
            processed, failed = ingester.scan_and_process_bucket(
                prefix='historical/',
                dry_run=True
            )
            
            print(f"\n📊 Results:")
            print(f"  Files that will be processed: {len(processed)}")
            print(f"  Files that cannot be parsed: {len(failed)}")
            
            if processed and len(processed) <= 20:
                print("\n✓ Files to process:")
                for f in processed:
                    print(f"    - {f}")
            elif processed:
                print(f"\n✓ First 20 files to process:")
                for f in processed[:20]:
                    print(f"    - {f}")
                print(f"  ... and {len(processed)-20} more")
            
            if failed:
                print("\n⚠ Failed files:")
                for f in failed:
                    print(f"    - {f}")
        
        elif choice == '2':
            # Process all files
            confirm = input("\n⚠️  This will process ALL CSV files. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                print("\n🚀 Starting full ingestion...")
                start_time = datetime.now()
                
                processed, failed = ingester.scan_and_process_bucket(
                    prefix='historical/',
                    dry_run=False
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n✅ INGESTION COMPLETE")
                print(f"  Time taken: {elapsed:.2f} seconds")
                print(f"  Processed: {len(processed)} files")
                print(f"  Failed: {len(failed)} files")
                
                # Show status
                status = ingester.get_ingestion_status()
                if status:
                    print("\n📊 Data now in BigQuery:")
                    for commodity in status.get('commodities', []):
                        print(f"  • {commodity['commodity']}: {commodity['record_count']:,} records")
                        print(f"    Date range: {commodity['earliest_date']} to {commodity['latest_date']}")
        
        elif choice == '3':
            # Process specific file
            file_path = input("\nEnter file path (e.g., historical/ZL_data.csv): ")
            print(f"\n🔄 Processing {file_path}...")
            
            success = ingester.process_single_file(file_path)
            if success:
                print("✅ File processed successfully")
            else:
                print("❌ Failed to process file")
        
        elif choice == '4':
            # Check status
            print("\n📊 Checking ingestion status...")
            status = ingester.get_ingestion_status()
            
            if status:
                print("\n📈 Current data in BigQuery:")
                print(f"  Total records: {status.get('total_records', 0):,}")
                print(f"  Total files: {status.get('total_files', 0):,}")
                
                print("\n  By commodity:")
                for commodity in status.get('commodities', []):
                    print(f"\n  {commodity['commodity'].upper()}:")
                    print(f"    Records: {commodity['record_count']:,}")
                    print(f"    Files: {commodity['file_count']}")
                    print(f"    Earliest: {commodity['earliest_date']}")
                    print(f"    Latest: {commodity['latest_date']}")
            else:
                print("No data found in BigQuery")
        
        elif choice == '5':
            # Show sample data
            commodity = input("\nEnter commodity to view (e.g., soybean_oil, corn, or 'all'): ").lower()
            
            try:
                if commodity == 'all':
                    query = f"""
                    SELECT commodity, timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                else:
                    query = f"""
                    SELECT timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    WHERE commodity = '{commodity}'
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                
                df = ingester.bq_client.query(query).to_dataframe()
                
                if not df.empty:
                    print(f"\n📊 Sample data for {commodity}:")
                    print(df.to_string())
                else:
                    print(f"No data found for {commodity}")
                    
            except Exception as e:
                print(f"Error querying data: {e}")
        
        elif choice == '6':
            print("\n👋 Exiting...")
            break
        
        else:
            print("\n⚠️  Invalid option, please try again")

    print("\n✅ Done!")


if __name__ == "__main__":
    # Check if running in Cloud Shell
    if os.environ.get('CLOUD_SHELL'):
        print("✓ Running in Google Cloud Shell")
    else:
        print("⚠️  Not running in Cloud Shell - make sure GCP credentials are configured")
    
    main()
#!/usr/bin/env python3
"""
run_ingestion.py - Runner script for Cloud Shell
Execute this to process all your commodity CSV files
"""

import os
import sys
from datetime import datetime

# First, install required packages if needed
def install_requirements():
    """Install required packages"""
    import subprocess
    packages = ['pandas', 'numpy', 'google-cloud-storage', 'google-cloud-bigquery', 'chardet']
    
    print("📦 Checking/Installing required packages...")
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install requirements first
install_requirements()

# Now import everything
import pandas as pd
import numpy as np
from google.cloud import storage
from google.cloud import bigquery
import json
import logging

# Import our intelligent ingestion system
from intelligent_ingestion import IntelligentIngestionSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main execution function with menu
    """
    print("\n" + "="*60)
    print("🚀 CBI-V14 INTELLIGENT INGESTION SYSTEM")
    print("="*60)
    print("\nThis system will process your commodity CSV files:")
    print("  • Auto-detect commodity types (ZL, ZC, ZS, etc.)")
    print("  • Handle various CSV formats and date formats")
    print("  • Clean and standardize data")
    print("  • Load to BigQuery for analysis")
    print("\n" + "="*60)
    
    # Configuration
    PROJECT_ID = 'cbi-v14'
    BUCKET_NAME = 'forecasting-app-raw-data-bucket'
    DATASET_ID = 'forecasting_data_warehouse'
    
    print(f"\nConfiguration:")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Dataset: {DATASET_ID}")
    
    # Initialize the ingestion system
    try:
        ingester = IntelligentIngestionSystem(
            project_id=PROJECT_ID,
            bucket_name=BUCKET_NAME,
            dataset_id=DATASET_ID
        )
        print("\n✓ Ingestion system initialized successfully")
    except Exception as e:
        print(f"\n❌ Error initializing: {e}")
        print("\nMake sure you're authenticated:")
        print("  gcloud auth application-default login")
        return
    
    # Menu
    while True:
        print("\n" + "-"*40)
        print("MENU:")
        print("1. Scan bucket for files (dry run)")
        print("2. Process ALL historical files")
        print("3. Process specific file")
        print("4. Check ingestion status")
        print("5. Show sample data from BigQuery")
        print("6. Exit")
        print("-"*40)
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            # Dry run to see what files will be processed
            print("\n🔍 Scanning bucket for CSV files...")
            processed, failed = ingester.scan_and_process_bucket(
                prefix='historical/',
                dry_run=True
            )
            
            print(f"\n📊 Results:")
            print(f"  Files that will be processed: {len(processed)}")
            print(f"  Files that cannot be parsed: {len(failed)}")
            
            if processed and len(processed) <= 20:
                print("\n✓ Files to process:")
                for f in processed:
                    print(f"    - {f}")
            elif processed:
                print(f"\n✓ First 20 files to process:")
                for f in processed[:20]:
                    print(f"    - {f}")
                print(f"  ... and {len(processed)-20} more")
            
            if failed:
                print("\n⚠ Failed files:")
                for f in failed:
                    print(f"    - {f}")
        
        elif choice == '2':
            # Process all files
            confirm = input("\n⚠️  This will process ALL CSV files. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                print("\n🚀 Starting full ingestion...")
                start_time = datetime.now()
                
                processed, failed = ingester.scan_and_process_bucket(
                    prefix='historical/',
                    dry_run=False
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n✅ INGESTION COMPLETE")
                print(f"  Time taken: {elapsed:.2f} seconds")
                print(f"  Processed: {len(processed)} files")
                print(f"  Failed: {len(failed)} files")
                
                # Show status
                status = ingester.get_ingestion_status()
                if status:
                    print("\n📊 Data now in BigQuery:")
                    for commodity in status.get('commodities', []):
                        print(f"  • {commodity['commodity']}: {commodity['record_count']:,} records")
                        print(f"    Date range: {commodity['earliest_date']} to {commodity['latest_date']}")
        
        elif choice == '3':
            # Process specific file
            file_path = input("\nEnter file path (e.g., historical/ZL_data.csv): ")
            print(f"\n🔄 Processing {file_path}...")
            
            success = ingester.process_single_file(file_path)
            if success:
                print("✅ File processed successfully")
            else:
                print("❌ Failed to process file")
        
        elif choice == '4':
            # Check status
            print("\n📊 Checking ingestion status...")
            status = ingester.get_ingestion_status()
            
            if status:
                print("\n📈 Current data in BigQuery:")
                print(f"  Total records: {status.get('total_records', 0):,}")
                print(f"  Total files: {status.get('total_files', 0):,}")
                
                print("\n  By commodity:")
                for commodity in status.get('commodities', []):
                    print(f"\n  {commodity['commodity'].upper()}:")
                    print(f"    Records: {commodity['record_count']:,}")
                    print(f"    Files: {commodity['file_count']}")
                    print(f"    Earliest: {commodity['earliest_date']}")
                    print(f"    Latest: {commodity['latest_date']}")
            else:
                print("No data found in BigQuery")
        
        elif choice == '5':
            # Show sample data
            commodity = input("\nEnter commodity to view (e.g., soybean_oil, corn, or 'all'): ").lower()
            
            try:
                if commodity == 'all':
                    query = f"""
                    SELECT commodity, timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                else:
                    query = f"""
                    SELECT timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    WHERE commodity = '{commodity}'
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                
                df = ingester.bq_client.query(query).to_dataframe()
                
                if not df.empty:
                    print(f"\n📊 Sample data for {commodity}:")
                    print(df.to_string())
                else:
                    print(f"No data found for {commodity}")
                    
            except Exception as e:
                print(f"Error querying data: {e}")
        
        elif choice == '6':
            print("\n👋 Exiting...")
            break
        
        else:
            print("\n⚠️  Invalid option, please try again")

    print("\n✅ Done!")


if __name__ == "__main__":
    # Check if running in Cloud Shell
    if os.environ.get('CLOUD_SHELL'):
        print("✓ Running in Google Cloud Shell")
    else:
        print("⚠️  Not running in Cloud Shell - make sure GCP credentials are configured")
    
    main()#!/usr/bin/env python3
"""
run_ingestion.py - Runner script for Cloud Shell
Execute this to process all your commodity CSV files
"""

import os
import sys
from datetime import datetime

# First, install required packages if needed
def install_requirements():
    """Install required packages"""
    import subprocess
    packages = ['pandas', 'numpy', 'google-cloud-storage', 'google-cloud-bigquery', 'chardet']
    
    print("📦 Checking/Installing required packages...")
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install requirements first
install_requirements()

# Now import everything
import pandas as pd
import numpy as np
from google.cloud import storage
from google.cloud import bigquery
import json
import logging

# Import our intelligent ingestion system
from intelligent_ingestion import IntelligentIngestionSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main execution function with menu
    """
    print("\n" + "="*60)
    print("🚀 CBI-V14 INTELLIGENT INGESTION SYSTEM")
    print("="*60)
    print("\nThis system will process your commodity CSV files:")
    print("  • Auto-detect commodity types (ZL, ZC, ZS, etc.)")
    print("  • Handle various CSV formats and date formats")
    print("  • Clean and standardize data")
    print("  • Load to BigQuery for analysis")
    print("\n" + "="*60)
    
    # Configuration
    PROJECT_ID = 'cbi-v14'
    BUCKET_NAME = 'forecasting-app-raw-data-bucket'
    DATASET_ID = 'forecasting_data_warehouse'
    
    print(f"\nConfiguration:")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Dataset: {DATASET_ID}")
    
    # Initialize the ingestion system
    try:
        ingester = IntelligentIngestionSystem(
            project_id=PROJECT_ID,
            bucket_name=BUCKET_NAME,
            dataset_id=DATASET_ID
        )
        print("\n✓ Ingestion system initialized successfully")
    except Exception as e:
        print(f"\n❌ Error initializing: {e}")
        print("\nMake sure you're authenticated:")
        print("  gcloud auth application-default login")
        return
    
    # Menu
    while True:
        print("\n" + "-"*40)
        print("MENU:")
        print("1. Scan bucket for files (dry run)")
        print("2. Process ALL historical files")
        print("3. Process specific file")
        print("4. Check ingestion status")
        print("5. Show sample data from BigQuery")
        print("6. Exit")
        print("-"*40)
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            # Dry run to see what files will be processed
            print("\n🔍 Scanning bucket for CSV files...")
            processed, failed = ingester.scan_and_process_bucket(
                prefix='historical/',
                dry_run=True
            )
            
            print(f"\n📊 Results:")
            print(f"  Files that will be processed: {len(processed)}")
            print(f"  Files that cannot be parsed: {len(failed)}")
            
            if processed and len(processed) <= 20:
                print("\n✓ Files to process:")
                for f in processed:
                    print(f"    - {f}")
            elif processed:
                print(f"\n✓ First 20 files to process:")
                for f in processed[:20]:
                    print(f"    - {f}")
                print(f"  ... and {len(processed)-20} more")
            
            if failed:
                print("\n⚠ Failed files:")
                for f in failed:
                    print(f"    - {f}")
        
        elif choice == '2':
            # Process all files
            confirm = input("\n⚠️  This will process ALL CSV files. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                print("\n🚀 Starting full ingestion...")
                start_time = datetime.now()
                
                processed, failed = ingester.scan_and_process_bucket(
                    prefix='historical/',
                    dry_run=False
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n✅ INGESTION COMPLETE")
                print(f"  Time taken: {elapsed:.2f} seconds")
                print(f"  Processed: {len(processed)} files")
                print(f"  Failed: {len(failed)} files")
                
                # Show status
                status = ingester.get_ingestion_status()
                if status:
                    print("\n📊 Data now in BigQuery:")
                    for commodity in status.get('commodities', []):
                        print(f"  • {commodity['commodity']}: {commodity['record_count']:,} records")
                        print(f"    Date range: {commodity['earliest_date']} to {commodity['latest_date']}")
        
        elif choice == '3':
            # Process specific file
            file_path = input("\nEnter file path (e.g., historical/ZL_data.csv): ")
            print(f"\n🔄 Processing {file_path}...")
            
            success = ingester.process_single_file(file_path)
            if success:
                print("✅ File processed successfully")
            else:
                print("❌ Failed to process file")
        
        elif choice == '4':
            # Check status
            print("\n📊 Checking ingestion status...")
            status = ingester.get_ingestion_status()
            
            if status:
                print("\n📈 Current data in BigQuery:")
                print(f"  Total records: {status.get('total_records', 0):,}")
                print(f"  Total files: {status.get('total_files', 0):,}")
                
                print("\n  By commodity:")
                for commodity in status.get('commodities', []):
                    print(f"\n  {commodity['commodity'].upper()}:")
                    print(f"    Records: {commodity['record_count']:,}")
                    print(f"    Files: {commodity['file_count']}")
                    print(f"    Earliest: {commodity['earliest_date']}")
                    print(f"    Latest: {commodity['latest_date']}")
            else:
                print("No data found in BigQuery")
        
        elif choice == '5':
            # Show sample data
            commodity = input("\nEnter commodity to view (e.g., soybean_oil, corn, or 'all'): ").lower()
            
            try:
                if commodity == 'all':
                    query = f"""
                    SELECT commodity, timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                else:
                    query = f"""
                    SELECT timestamp, open, high, low, close, volume
                    FROM `{PROJECT_ID}.{DATASET_ID}.commodity_prices`
                    WHERE commodity = '{commodity}'
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """
                
                df = ingester.bq_client.query(query).to_dataframe()
                
                if not df.empty:
                    print(f"\n📊 Sample data for {commodity}:")
                    print(df.to_string())
                else:
                    print(f"No data found for {commodity}")
                    
            except Exception as e:
                print(f"Error querying data: {e}")
        
        elif choice == '6':
            print("\n👋 Exiting...")
            break
        
        else:
            print("\n⚠️  Invalid option, please try again")

    print("\n✅ Done!")


if __name__ == "__main__":
    # Check if running in Cloud Shell
    if os.environ.get('CLOUD_SHELL'):
        print("✓ Running in Google Cloud Shell")
    else:
        print("⚠️  Not running in Cloud Shell - make sure GCP credentials are configured")
    
    main()# Paste the entire intelligent ingestion system code here
