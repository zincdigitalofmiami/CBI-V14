#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBI-V14 - Week 2: Create Alpha Vantage BigQuery Tables
======================================================

This script provisions all necessary BigQuery tables for the Alpha Vantage
data, as defined in the FRESH_START_MASTER_PLAN.

- Creates tables in the `forecasting_data_warehouse` dataset.
- Enforces `alpha_` column prefixing for clear data lineage.
- Sets clustering on `date` and `symbol` for query performance.
"""
import os
import sys
import logging
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

# --- Setup Project Root ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.utils.gcp_utils import get_gcp_project_id
except ImportError:
    print("Could not import gcp_utils. Ensure you are running from the project root.")
    sys.exit(1)

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = get_gcp_project_id()
if not PROJECT_ID:
    logger.error("GCP_PROJECT_ID not found in environment or config. Exiting.")
    sys.exit(1)

client = bigquery.Client(project=PROJECT_ID)
DATASET_ID = "forecasting_data_warehouse"

# --- Table Definitions ---
TABLE_SCHEMAS = {
    "alpha_technicals_daily": [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        # Example technicals - the full list is extensive and will be inferred on load
        # to keep this schema definition manageable.
        bigquery.SchemaField("alpha_sma_20", "FLOAT64"),
        bigquery.SchemaField("alpha_ema_50", "FLOAT64"),
        bigquery.SchemaField("alpha_rsi_14", "FLOAT64"),
        bigquery.SchemaField("alpha_macd_signal", "FLOAT64"),
        bigquery.SchemaField("alpha_bbands_upper", "FLOAT64"),
    ],
    "alpha_commodities_daily": [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("alpha_wti_price", "FLOAT64"),
        bigquery.SchemaField("alpha_brent_price", "FLOAT64"),
        bigquery.SchemaField("alpha_natural_gas_price", "FLOAT64"),
        bigquery.SchemaField("alpha_copper_price", "FLOAT64"),
        bigquery.SchemaField("alpha_corn_price", "FLOAT64"),
        bigquery.SchemaField("alpha_soybeans_price", "FLOAT64"),
        bigquery.SchemaField("alpha_wheat_price", "FLOAT64"),
    ],
    "alpha_forex_daily": [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"), # e.g., EURUSD
        bigquery.SchemaField("alpha_open", "FLOAT64"),
        bigquery.SchemaField("alpha_high", "FLOAT64"),
        bigquery.SchemaField("alpha_low", "FLOAT64"),
        bigquery.SchemaField("alpha_close", "FLOAT64"),
    ],
    "alpha_treasuries_daily": [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("alpha_yield_3m", "FLOAT64"),
        bigquery.SchemaField("alpha_yield_2y", "FLOAT64"),
        bigquery.SchemaField("alpha_yield_10y", "FLOAT64"),
        bigquery.SchemaField("alpha_yield_30y", "FLOAT64"),
    ]
}

def create_table(table_id: str, schema: list, clustering_fields: list):
    """Creates a BigQuery table with specified schema and clustering."""
    full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    logger.info(f"Attempting to create table: {full_table_id}")
    
    table = bigquery.Table(full_table_id, schema=schema)
    table.clustering_fields = clustering_fields
    
    try:
        table = client.create_table(table)
        logger.info(f"✅ Successfully created table {full_table_id} with clustering on {clustering_fields}")
    except Conflict:
        logger.warning(f"⚠️ Table {full_table_id} already exists. Skipping creation.")
    except Exception as e:
        logger.error(f"❌ Failed to create table {full_table_id}: {e}")

def main():
    """Main execution function to create all Alpha Vantage tables."""
    logger.info("="*80)
    logger.info("Creating Alpha Vantage BigQuery Tables")
    logger.info("="*80)
    
    # Technicals table will have many columns, so we define a few and let the rest be inferred
    # during the first load if needed, or we can expand this schema later. For now, this is a placeholder.
    # A better approach for wide tables is often to let the first load define the schema.
    # However, for clarity, we define a few key columns here.
    create_table("alpha_technicals_daily", TABLE_SCHEMAS["alpha_technicals_daily"], ["date", "symbol"])
    create_table("alpha_commodities_daily", TABLE_SCHEMAS["alpha_commodities_daily"], ["date"])
    create_table("alpha_forex_daily", TABLE_SCHEMAS["alpha_forex_daily"], ["date", "symbol"])
    create_table("alpha_treasuries_daily", TABLE_SCHEMAS["alpha_treasuries_daily"], ["date"])

    logger.info("="*80)
    logger.info("BigQuery Table Creation Script Finished")
    logger.info("="*80)

if __name__ == "__main__":
    main()
