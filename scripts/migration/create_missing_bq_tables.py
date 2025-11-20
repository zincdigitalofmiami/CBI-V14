#!/usr/bin/env python3
"""
Create missing BigQuery tables with schemas matching staging files.
This ensures BQ is ready to receive data from staging.
"""

import pandas as pd
from pathlib import Path
from google.cloud import bigquery
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.utils.gcp_utils import get_gcp_project_id

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
STAGING_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
PROJECT_ID = get_gcp_project_id()

def infer_bq_field_type(dtype):
    """Infer BigQuery field type from pandas dtype."""
    dtype_str = str(dtype)
    
    if 'int' in dtype_str:
        return 'INTEGER'
    elif 'float' in dtype_str:
        return 'FLOAT'
    elif 'bool' in dtype_str:
        return 'BOOLEAN'
    elif 'datetime' in dtype_str or 'date' in dtype_str:
        return 'DATE'
    elif 'object' in dtype_str:
        return 'STRING'
    else:
        return 'STRING'

def create_table_from_parquet(client, staging_file, dataset_id, table_name):
    """Create a BigQuery table with schema matching the staging file."""
    file_path = STAGING_DIR / staging_file
    
    if not file_path.exists():
        logger.error(f"Staging file not found: {staging_file}")
        return False
    
    try:
        # Load parquet to get schema
        df = pd.read_parquet(file_path)
        
        # Build BigQuery schema
        schema = []
        for col in df.columns:
            dtype = df[col].dtype
            field_type = infer_bq_field_type(dtype)
            
            # Special handling for date columns
            if col == 'date':
                field_type = 'DATE'
            elif col == 'timestamp':
                field_type = 'TIMESTAMP'
            
            schema.append(bigquery.SchemaField(col, field_type))
        
        # Create table
        table_id = f"{PROJECT_ID}.{dataset_id}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        
        # Set clustering fields
        if 'date' in df.columns:
            table.clustering_fields = ['date']
            if 'symbol' in df.columns:
                table.clustering_fields = ['date', 'symbol']
        
        # Create the table
        table = client.create_table(table, exists_ok=True)
        logger.info(f"✅ Created table: {dataset_id}.{table_name} with {len(schema)} columns")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating {dataset_id}.{table_name}: {str(e)}")
        return False

def main():
    """Create all missing tables."""
    logger.info("="*80)
    logger.info("CREATING MISSING BIGQUERY TABLES")
    logger.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Tables to create
    tables_to_create = [
        # market_data tables
        ("yahoo_historical_prefixed.parquet", "market_data", "yahoo_historical_prefixed"),
        ("es_futures_daily.parquet", "market_data", "es_futures_daily"),
        
        # raw_intelligence tables
        ("palm_oil_daily.parquet", "raw_intelligence", "palm_oil_daily"),
        
        # features tables
        # regime_calendar will be created separately as it comes from registry/
    ]
    
    success_count = 0
    failed_count = 0
    
    for staging_file, dataset_id, table_name in tables_to_create:
        logger.info(f"\nCreating {dataset_id}.{table_name} from {staging_file}...")
        
        if create_table_from_parquet(client, staging_file, dataset_id, table_name):
            success_count += 1
        else:
            failed_count += 1
    
    # Create core signals tables (schemas defined here)
    logger.info("\nCreating core signals tables...")
    def ensure_table(table_id: str, schema_fields: list, clustering: list = None):
        table_ref = f"{PROJECT_ID}.{table_id}"
        table = bigquery.Table(table_ref, schema=schema_fields)
        # Time partition on date if present
        if any(f.name == "date" and f.field_type == "DATE" for f in schema_fields):
            table.time_partitioning = bigquery.TimePartitioning(field="date")
        if clustering:
            table.clustering_fields = clustering
        try:
            client.create_table(table, exists_ok=True)
            logger.info(f"✅ Created table: {table_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating {table_id}: {e}")
            return False

    sf = bigquery.SchemaField
    ensure_table(
        "signals.crush_oilshare_daily",
        [sf("date", "DATE"), sf("crush_oilshare_pressure", "FLOAT")],
        clustering=["date"],
    )
    ensure_table(
        "signals.energy_proxies_daily",
        [sf("date", "DATE"), sf("energy_biofuel_shock", "FLOAT")],
        clustering=["date"],
    )
    ensure_table(
        "signals.calculated_signals",
        [
            sf("date", "DATE"),
            sf("vix_stress", "FLOAT"),
            sf("fx_pressure", "FLOAT"),
            sf("weather_supply_risk", "FLOAT"),
            sf("china_demand", "FLOAT"),
            sf("positioning_pressure", "FLOAT"),
        ],
        clustering=["date"],
    )
    ensure_table(
        "signals.hidden_relationship_signals",
        [
            sf("date", "DATE"),
            sf("hidden_relationship_composite_score", "FLOAT"),
            sf("correlation_override_flag", "BOOL"),
            sf("primary_hidden_domain", "STRING"),
        ],
        clustering=["date"],
    )
    ensure_table(
        "signals.big_eight_live",
        [
            sf("date", "DATE"),
            sf("symbol", "STRING"),
            sf("big8_crush_oilshare_pressure", "FLOAT"),
            sf("big8_policy_shock", "FLOAT"),
            sf("big8_weather_supply_risk", "FLOAT"),
            sf("big8_china_demand", "FLOAT"),
            sf("big8_vix_stress", "FLOAT"),
            sf("big8_positioning_pressure", "FLOAT"),
            sf("big8_energy_biofuel_shock", "FLOAT"),
            sf("big8_fx_pressure", "FLOAT"),
            sf("big8_composite_score", "FLOAT"),
            sf("big8_signal_direction", "STRING"),
            sf("big8_signal_strength", "FLOAT"),
            sf("as_of", "TIMESTAMP"),
        ],
        clustering=["date", "symbol"],
    )

    # IV30 daily features (options-based; optional if options add-on enabled)
    logger.info("\nCreating features.iv30_daily (if missing)...")
    ensure_table(
        "features.iv30_daily",
        [
            sf("date", "DATE"),
            sf("symbol", "STRING"),
            sf("iv30", "FLOAT"),
            sf("obs_count", "INTEGER"),
            sf("moneyness_span", "FLOAT"),
            sf("quality_flag", "STRING"),
            sf("asof_source_time", "TIMESTAMP"),
            sf("as_of", "TIMESTAMP"),
        ],
        clustering=["date", "symbol"],
    )

    # Create regime_calendar table
    logger.info("\nCreating features.regime_calendar...")
    regime_file = Path("/Volumes/Satechi Hub/Projects/CBI-V14/registry/regime_calendar.parquet")
    if regime_file.exists():
        df = pd.read_parquet(regime_file)
        
        schema = [
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("regime", "STRING"),
            bigquery.SchemaField("training_weight", "INTEGER"),
        ]
        
        table_id = f"{PROJECT_ID}.features.regime_calendar"
        table = bigquery.Table(table_id, schema=schema)
        table.clustering_fields = ['date', 'regime']
        
        try:
            table = client.create_table(table, exists_ok=True)
            logger.info(f"✅ Created table: features.regime_calendar")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error creating regime_calendar: {str(e)}")
            failed_count += 1
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Tables created: {success_count}")
    logger.info(f"❌ Failed: {failed_count}")
    
    if failed_count == 0:
        logger.info("\n🎉 ALL TABLES CREATED SUCCESSFULLY!")
        
        # Now fix existing table schemas if needed
        logger.info("\nFIXING EXISTING TABLE SCHEMAS...")
        fix_existing_schemas(client)
    
    return success_count, failed_count

def fix_existing_schemas(client):
    """Fix schema mismatches in existing tables."""
    
    # Tables that need schema updates
    schema_fixes = {
        "raw_intelligence.fred_economic": {
            "expected_cols": 17,  # From fred_macro_expanded.parquet
            "staging_file": "fred_macro_expanded.parquet"
        },
        "raw_intelligence.weather_segmented": {
            "expected_cols": 61,  # From weather_granular.parquet
            "staging_file": "weather_granular.parquet"
        },
        "raw_intelligence.cftc_positioning": {
            "expected_cols": 195,  # From cftc_commitments.parquet
            "staging_file": "cftc_commitments.parquet"
        },
        "raw_intelligence.eia_biofuels": {
            "expected_cols": 3,  # From eia_energy_granular.parquet
            "staging_file": "eia_energy_granular.parquet"
        },
        "raw_intelligence.volatility_daily": {
            "expected_cols": 21,  # From volatility_features.parquet
            "staging_file": "volatility_features.parquet"
        },
        "raw_intelligence.policy_events": {
            "expected_cols": 13,  # From policy_trump_signals.parquet
            "staging_file": "policy_trump_signals.parquet"
        }
    }
    
    for table_id, info in schema_fixes.items():
        dataset_id, table_name = table_id.split('.')
        staging_file = info['staging_file']
        
        logger.info(f"\nChecking schema for {table_id}...")
        
        try:
            # Get current table schema
            table_ref = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_name}")
            current_cols = len(table_ref.schema)
            
            if current_cols != info['expected_cols']:
                logger.warning(f"  Schema mismatch: BQ has {current_cols} cols, staging has {info['expected_cols']} cols")
                logger.info(f"  Recreating table with correct schema...")
                
                # Drop and recreate
                client.delete_table(table_ref)
                create_table_from_parquet(client, staging_file, dataset_id, table_name)
            else:
                logger.info(f"  ✅ Schema OK: {current_cols} columns")
                
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)[:100]}")

if __name__ == "__main__":
    success, failed = main()
    sys.exit(0 if failed == 0 else 1)




