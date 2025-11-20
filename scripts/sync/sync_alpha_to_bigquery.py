#!/usr/bin/env python3
"""
Sync local Alpha Vantage data to BigQuery tables.
Run after local collection is complete.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from utils.data_validation import AlphaDataValidator

try:
    from google.cloud import bigquery
except ImportError:
    print("⚠️  google-cloud-bigquery not installed. Install with: pip install google-cloud-bigquery")
    bigquery = None

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData")

class AlphaToBigQuerySync:
    """Push local Alpha data to BigQuery"""
    
    def __init__(self):
        if bigquery is None:
            raise ImportError("google-cloud-bigquery required for BigQuery sync")
        
        self.client = bigquery.Client(project="cbi-v14")
        self.drive = DRIVE
        self.validator = AlphaDataValidator()
        
    def sync_technical_indicators(self):
        """Sync 50+ technical indicators to BigQuery"""
        
        print("\n" + "="*80)
        print("SYNCING TECHNICAL INDICATORS TO BIGQUERY")
        print("="*80)
        
        # Read staging file with all indicators
        staging_file = self.drive / "staging/alpha/daily/alpha_indicators_wide.parquet"
        
        if not staging_file.exists():
            print(f"⚠️  Staging file not found: {staging_file}")
            print("   Run: python3 scripts/staging/prepare_alpha_for_joins.py")
            return None
        
        df = pd.read_parquet(staging_file)
        
        # CRITICAL: Validate before BigQuery upload
        print("🔍 Validating indicators before BigQuery sync...")
        self.validator.validate_dataframe(df, 'indicators', 'BQ_SYNC')
        
        # Add metadata
        df['source'] = 'alpha_vantage'
        df['ingestion_ts'] = datetime.now()
        
        # BigQuery table (MATCHES EXISTING PATTERN)
        table_id = "cbi-v14.forecasting_data_warehouse.technical_indicators_alpha_daily"
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Replace entire table
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            ),
            clustering_fields=["symbol"]
        )
        
        # Load to BigQuery
        print(f"Loading {len(df)} rows to {table_id}...")
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()  # Wait for completion
        
        print(f"✅ Loaded {job.output_rows} rows to BigQuery")
        
        # Update manifest
        self._update_manifest('indicators', {
            'rows_synced': len(df),
            'bq_table': table_id,
            'sync_time': datetime.now().isoformat()
        })
        
        return job
    
    def sync_prices(self):
        """Sync commodity/FX prices to BigQuery"""
        
        print("\n" + "="*80)
        print("SYNCING PRICES TO BIGQUERY")
        print("="*80)
        
        # Commodity prices
        commodity_file = self.drive / "staging/alpha/daily/alpha_prices_combined.parquet"
        
        if not commodity_file.exists():
            print(f"⚠️  Prices file not found: {commodity_file}")
            return None
        
        df_commodity = pd.read_parquet(commodity_file)
        
        # CRITICAL: Validate before BigQuery upload
        print("🔍 Validating prices before BigQuery sync...")
        self.validator.validate_dataframe(df_commodity, 'daily', 'BQ_SYNC')
        
        df_commodity['source'] = 'alpha_vantage'
        df_commodity['ingestion_ts'] = datetime.now()
        
        # Load commodities (MATCHES EXISTING PATTERN)
        table_id = "cbi-v14.forecasting_data_warehouse.commodity_alpha_daily"
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            ),
            clustering_fields=["symbol"]
        )
        
        print(f"Loading {len(df_commodity)} commodity prices...")
        job = self.client.load_table_from_dataframe(
            df_commodity, table_id, job_config=job_config
        )
        job.result()
        
        print(f"✅ Loaded {job.output_rows} commodity prices")
        
        # Similar for FX, indices...
        # TODO: Add FX and indices sync when those files are created
        
        return job
    
    def sync_es_intraday(self):
        """Sync ES intraday data (11 timeframes)"""
        
        print("\n" + "="*80)
        print("SYNCING ES INTRADAY TO BIGQUERY")
        print("="*80)
        
        es_dir = self.drive / "raw/alpha/es_intraday"
        table_id = "cbi-v14.forecasting_data_warehouse.intraday_es_alpha"
        
        if not es_dir.exists():
            print(f"⚠️  ES intraday directory not found: {es_dir}")
            return None
        
        all_intervals = []
        
        for interval_dir in es_dir.iterdir():
            if not interval_dir.is_dir():
                continue
            
            interval = interval_dir.name  # '5min', '15min', etc.
            
            for parquet_file in interval_dir.glob("*.parquet"):
                df = pd.read_parquet(parquet_file)
                df['interval'] = interval
                df['source'] = 'alpha_vantage'
                df['ingestion_ts'] = datetime.now()
                all_intervals.append(df)
                print(f"  {interval}: {len(df)} bars")
        
        if not all_intervals:
            print("⚠️  No ES intraday files found")
            return None
        
        # Combine all intervals
        combined = pd.concat(all_intervals, ignore_index=True)
        
        # CRITICAL: Validate before BigQuery upload
        print("\n🔍 Validating ES intraday before BigQuery sync...")
        self.validator.validate_dataframe(combined, 'intraday', 'ES_BQ_SYNC')
        
        # Load to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            ),
            clustering_fields=["interval"]
        )
        
        print(f"\nLoading {len(combined)} total ES bars...")
        job = self.client.load_table_from_dataframe(
            combined, table_id, job_config=job_config
        )
        job.result()
        
        print(f"✅ Loaded {job.output_rows} ES intraday bars")
        
        return job
    
    def _update_manifest(self, data_type, info):
        """Update collection manifest with sync info"""
        
        manifest_dir = self.drive / "raw/alpha/manifests/daily"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        manifest_file = manifest_dir / f"sync_{today}.json"
        
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
        else:
            manifest = {}
        
        manifest[data_type] = info
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def sync_all(self):
        """Run complete sync pipeline"""
        
        print("\n" + "="*80)
        print("ALPHA VANTAGE → BIGQUERY SYNC")
        print("="*80)
        
        # 1. Sync technical indicators (50+ columns)
        self.sync_technical_indicators()
        
        # 2. Sync prices
        self.sync_prices()
        
        # 3. Sync ES intraday
        self.sync_es_intraday()
        
        print("\n" + "="*80)
        print("✅ ALL DATA SYNCED TO BIGQUERY")
        print("="*80)

if __name__ == "__main__":
    try:
        syncer = AlphaToBigQuerySync()
        syncer.sync_all()
    except ImportError as e:
        print(f"❌ {e}")
        print("\nInstall BigQuery client:")
        print("  pip install google-cloud-bigquery")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





