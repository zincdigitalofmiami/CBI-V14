#!/usr/bin/env python3
"""
Data Quality Check: Canonical Metadata Compliance
Runs nightly to ensure all base tables maintain canonical metadata standards
"""

import logging
from google.cloud import bigquery
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dq_canonical_check')

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'forecasting_data_warehouse'

# Canonical columns required on all base tables
CANONICAL_COLUMNS = [
    'source_name',
    'confidence_score',
    'ingest_timestamp_utc',
    'provenance_uuid'
]

# Tables exempt from canonical metadata (registries, forecasts, etc.)
EXEMPT_TABLES = [
    'feature_metadata',
    'extraction_labels',
    'raw_ingest',
    'backtest_forecast',
    'soybean_oil_forecast'
]

def check_canonical_compliance():
    """Check all base tables for canonical metadata compliance"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get all base tables
    query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
      AND table_name NOT LIKE '%_bkp_%'
      AND table_name NOT IN UNNEST({EXEMPT_TABLES})
    ORDER BY table_name
    """
    
    tables = client.query(query).to_dataframe()
    
    failures = []
    
    for table_name in tables['table_name']:
        # Check for canonical columns
        col_query = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name}'
          AND column_name IN UNNEST({CANONICAL_COLUMNS})
        """
        
        cols = client.query(col_query).to_dataframe()
        found_cols = set(cols['column_name'])
        missing_cols = set(CANONICAL_COLUMNS) - found_cols
        
        if missing_cols:
            failures.append({
                'table': table_name,
                'missing': list(missing_cols)
            })
            logger.error(f"❌ {table_name}: Missing {missing_cols}")
        
        # Check for NULL values in canonical columns
        if not missing_cols:
            null_check_query = f"""
            SELECT
              COUNTIF(source_name IS NULL) AS null_source,
              COUNTIF(confidence_score IS NULL) AS null_conf,
              COUNTIF(ingest_timestamp_utc IS NULL) AS null_ingest,
              COUNTIF(provenance_uuid IS NULL) AS null_prov
            FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
            """
            
            null_counts = client.query(null_check_query).to_dataframe().iloc[0]
            
            if null_counts.sum() > 0:
                logger.warning(f"⚠️ {table_name}: {null_counts.sum()} NULL values in canonical columns")
    
    # Summary
    logger.info("=" * 80)
    if not failures:
        logger.info("✅ ALL BASE TABLES CANONICAL METADATA COMPLIANT")
        return True
    else:
        logger.error(f"❌ {len(failures)} tables missing canonical metadata:")
        for failure in failures:
            logger.error(f"  - {failure['table']}: {failure['missing']}")
        return False

if __name__ == '__main__':
    success = check_canonical_compliance()
    exit(0 if success else 1)






