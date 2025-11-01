#!/usr/bin/env python3
"""
Generate Schema Contract - Immutable Contract for AutoML Predictions
Exports ALL 210 columns from training_dataset_super_enriched to config/schema_contract.json
This becomes the single source of truth for prediction payloads.
"""
import json
import logging
from datetime import datetime
from google.cloud import bigquery
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def generate_schema_contract():
    """Generate immutable schema contract from training dataset"""
    logger.info("Generating schema contract from training dataset...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = """
    SELECT COLUMN_NAME 
    FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS` 
    WHERE TABLE_NAME = 'training_dataset_super_enriched'
    ORDER BY COLUMN_NAME
    """
    
    df = client.query(query).to_dataframe()
    columns = list(df['COLUMN_NAME'].values)
    
    schema_contract = {
        "version": "1.0.0",
        "source_table": "cbi-v14.models_v4.training_dataset_super_enriched",
        "exported_at": datetime.utcnow().isoformat() + 'Z',
        "total_columns": len(columns),
        "columns": columns,
        "description": "Immutable schema contract - ALL columns must be present in prediction payload. Target columns (target_1w, target_1m, target_3m, target_6m) must exist but can be None."
    }
    
    # Ensure config directory exists
    config_path = Path('config')
    config_path.mkdir(exist_ok=True)
    
    contract_path = config_path / 'schema_contract.json'
    with open(contract_path, 'w') as f:
        json.dump(schema_contract, f, indent=2)
    
    logger.info(f"✅ Schema contract generated: {contract_path}")
    logger.info(f"  Total columns: {len(columns)}")
    logger.info(f"  Target columns: {[c for c in columns if c.startswith('target_')]}")
    
    return schema_contract

if __name__ == "__main__":
    try:
        contract = generate_schema_contract()
        print(f"\n✅ Success! Schema contract saved to config/schema_contract.json")
        print(f"Columns: {contract['total_columns']}")
    except Exception as e:
        print(f"❌ Failed to generate schema contract: {e}")
        exit(1)

