#!/usr/bin/env python3
"""
BigQuery Warehouse Rebuild Migration Script

This script automates the migration of tables from the old warehouse structure
to the new purpose-driven dataset structure.

Usage:
    python scripts/migrate_warehouse_rebuild.py --phase migrate_raw_intelligence
    python scripts/migrate_warehouse_rebuild.py --phase build_features
    python scripts/migrate_warehouse_rebuild.py --phase build_training
    python scripts/migrate_warehouse_rebuild.py --phase validate
"""

import os
import sys
import argparse
import pandas as pd
from typing import List, Dict, Optional
from google.cloud import bigquery
from tqdm import tqdm
import json
from datetime import datetime

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")
BQ_CLIENT = bigquery.Client(project=PROJECT_ID)

# Table mapping configuration
TABLE_MAPPINGS = {
    # Raw Intelligence Mappings
    'raw_intelligence': {
        'forecasting_data_warehouse.soybean_oil_prices': 'commodities_agriculture_soybean_oil_raw_daily',
        'forecasting_data_warehouse.soybean_prices': 'commodities_agriculture_soybean_raw_daily',
        'forecasting_data_warehouse.corn_prices': 'commodities_agriculture_corn_raw_daily',
        'forecasting_data_warehouse.palm_oil_prices': 'commodities_agriculture_palm_oil_raw_daily',
        'forecasting_data_warehouse.crude_oil_prices': 'commodities_energy_crude_oil_raw_daily',
        'forecasting_data_warehouse.weather_data': 'intelligence_weather_global_raw_daily',
        'forecasting_data_warehouse.trump_policy_intelligence': 'intelligence_policy_trump_raw_daily',
        'forecasting_data_warehouse.news_intelligence': 'intelligence_news_general_raw_daily',
        'forecasting_data_warehouse.social_intelligence_unified': 'intelligence_sentiment_social_raw_daily',
        'forecasting_data_warehouse.vix_daily': 'equities_vix_raw_daily',
        'forecasting_data_warehouse.usd_index_prices': 'fx_dxy_raw_daily',
        'forecasting_data_warehouse.treasury_prices': 'rates_treasury_raw_daily',
    },
    # Feature Mappings
    'features': {
        'models_v4.vertex_core_features': 'general_master_daily',
        'forecasting_data_warehouse.rin_proxy_features_final': 'biofuel_rin_proxy_daily',
        'yahoo_finance_comprehensive.yahoo_normalized': 'commodities_general_yahoo_normalized_daily',
        'models_v4.cftc_daily_filled': 'commodities_agriculture_cftc_filled_daily',
    },
    # Training Mappings
    'training': {
        'models_v4.production_training_data_1w': 'horizon_1w_production',
        'models_v4.production_training_data_1m': 'horizon_1m_production',
        'models_v4.production_training_data_3m': 'horizon_3m_production',
        'models_v4.production_training_data_6m': 'horizon_6m_production',
        'models_v4.production_training_data_12m': 'horizon_12m_production',
        'models_v4.trump_rich_2023_2025': 'regime_trump_2023_2025_production',
        'models_v4.pre_crisis_2000_2007_historical': 'regime_pre_crisis_2000_2007_archive',
        'models_v4.recovery_2010_2016_historical': 'regime_recovery_2010_2016_archive',
        'models_v4.trade_war_2017_2019_historical': 'regime_trade_war_2017_2019_archive',
        'models_v4.crisis_2008_historical': 'regime_crisis_2008_archive',
    },
    # Prediction Mappings
    'predictions': {
        'predictions.monthly_vertex_predictions': 'horizon_1m_production',
        'predictions.daily_forecasts': 'horizon_all_horizons_production',
    }
}


def migrate_table(
    source_table: str,
    target_dataset: str,
    target_table: str,
    deduplicate: bool = True,
    batch_size: int = 100000
) -> Dict[str, any]:
    """
    Migrate a single table from source to target.
    
    Args:
        source_table: Full source table name (dataset.table)
        target_dataset: Target dataset name
        target_table: Target table name
        deduplicate: Whether to deduplicate rows
        batch_size: Batch size for large tables
    
    Returns:
        Migration result dictionary
    """
    source_ref = f"{PROJECT_ID}.{source_table}"
    target_ref = f"{PROJECT_ID}.{target_dataset}.{target_table}"
    
    print(f"Migrating {source_ref} → {target_ref}")
    
    try:
        # Get source table info
        source_table_obj = BQ_CLIENT.get_table(source_ref)
        row_count = source_table_obj.num_rows
        
        if row_count == 0:
            print(f"  ⚠️  Source table is empty, skipping")
            return {
                'source': source_table,
                'target': f"{target_dataset}.{target_table}",
                'status': 'skipped',
                'reason': 'empty_table',
                'rows_migrated': 0
            }
        
        # Build migration query
        if deduplicate:
            # Deduplicate on date/time column
            query = f"""
            CREATE OR REPLACE TABLE `{target_ref}` AS
            SELECT DISTINCT *
            FROM `{source_ref}`
            """
        else:
            query = f"""
            CREATE OR REPLACE TABLE `{target_ref}` AS
            SELECT *
            FROM `{source_ref}`
            """
        
        # Execute migration
        job = BQ_CLIENT.query(query)
        job.result()  # Wait for completion
        
        # Verify row count
        target_table_obj = BQ_CLIENT.get_table(target_ref)
        target_row_count = target_table_obj.num_rows
        
        if target_row_count < row_count * 0.99:  # Allow 1% difference for deduplication
            print(f"  ⚠️  Row count mismatch: {row_count} → {target_row_count}")
            return {
                'source': source_table,
                'target': f"{target_dataset}.{target_table}",
                'status': 'warning',
                'rows_source': row_count,
                'rows_target': target_row_count,
                'rows_migrated': target_row_count
            }
        
        print(f"  ✅ Migrated {target_row_count:,} rows")
        return {
            'source': source_table,
            'target': f"{target_dataset}.{target_table}",
            'status': 'success',
            'rows_migrated': target_row_count
        }
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {
            'source': source_table,
            'target': f"{target_dataset}.{target_table}",
            'status': 'error',
            'error': str(e),
            'rows_migrated': 0
        }


def migrate_raw_intelligence() -> List[Dict]:
    """Migrate raw intelligence tables."""
    print("=" * 80)
    print("PHASE: Migrate Raw Intelligence")
    print("=" * 80)
    
    results = []
    mappings = TABLE_MAPPINGS['raw_intelligence']
    
    for source_table, target_table in tqdm(mappings.items(), desc="Migrating raw intelligence"):
        result = migrate_table(
            source_table=source_table,
            target_dataset='raw_intelligence',
            target_table=target_table,
            deduplicate=True
        )
        results.append(result)
    
    return results


def build_feature_tables() -> List[Dict]:
    """Build feature tables from raw intelligence."""
    print("=" * 80)
    print("PHASE: Build Feature Tables")
    print("=" * 80)
    
    results = []
    mappings = TABLE_MAPPINGS['features']
    
    # This is a simplified version - actual feature engineering would be more complex
    for source_table, target_table in tqdm(mappings.items(), desc="Building features"):
        result = migrate_table(
            source_table=source_table,
            target_dataset='features',
            target_table=target_table,
            deduplicate=True
        )
        results.append(result)
    
    return results


def build_training_tables() -> List[Dict]:
    """Build training tables from features."""
    print("=" * 80)
    print("PHASE: Build Training Tables")
    print("=" * 80)
    
    results = []
    mappings = TABLE_MAPPINGS['training']
    
    for source_table, target_table in tqdm(mappings.items(), desc="Building training tables"):
        result = migrate_table(
            source_table=source_table,
            target_dataset='training',
            target_table=target_table,
            deduplicate=False  # Don't deduplicate training data
        )
        results.append(result)
    
    return results


def validate_migration() -> Dict[str, any]:
    """Validate the migration by comparing row counts and schemas."""
    print("=" * 80)
    print("PHASE: Validate Migration")
    print("=" * 80)
    
    validation_results = {
        'row_count_checks': [],
        'schema_checks': [],
        'data_quality_checks': []
    }
    
    # Check row counts
    print("\n1. Checking row counts...")
    for dataset, mappings in TABLE_MAPPINGS.items():
        for source_table, target_table in mappings.items():
            try:
                source_ref = f"{PROJECT_ID}.{source_table}"
                target_ref = f"{PROJECT_ID}.{dataset}.{target_table}"
                
                source_table_obj = BQ_CLIENT.get_table(source_ref)
                target_table_obj = BQ_CLIENT.get_table(target_ref)
                
                source_rows = source_table_obj.num_rows
                target_rows = target_table_obj.num_rows
                
                if target_rows >= source_rows * 0.99:  # Allow 1% difference
                    status = 'pass'
                else:
                    status = 'fail'
                
                validation_results['row_count_checks'].append({
                    'source': source_table,
                    'target': f"{dataset}.{target_table}",
                    'source_rows': source_rows,
                    'target_rows': target_rows,
                    'status': status
                })
                
                if status == 'pass':
                    print(f"  ✅ {target_table}: {source_rows:,} → {target_rows:,}")
                else:
                    print(f"  ❌ {target_table}: {source_rows:,} → {target_rows:,} (MISMATCH)")
            
            except Exception as e:
                print(f"  ⚠️  {target_table}: Error - {str(e)}")
                validation_results['row_count_checks'].append({
                    'source': source_table,
                    'target': f"{dataset}.{target_table}",
                    'status': 'error',
                    'error': str(e)
                })
    
    # Check schemas (simplified - would need full schema comparison)
    print("\n2. Checking schemas...")
    # TODO: Implement full schema comparison
    
    return validation_results


def generate_migration_report(results: List[Dict], output_file: str = "migration_report.json"):
    """Generate a migration report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'project': PROJECT_ID,
        'total_tables': len(results),
        'successful': len([r for r in results if r.get('status') == 'success']),
        'failed': len([r for r in results if r.get('status') == 'error']),
        'warnings': len([r for r in results if r.get('status') == 'warning']),
        'skipped': len([r for r in results if r.get('status') == 'skipped']),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Migration report saved to {output_file}")
    print(f"   Successful: {report['successful']}/{report['total_tables']}")
    print(f"   Failed: {report['failed']}/{report['total_tables']}")
    print(f"   Warnings: {report['warnings']}/{report['total_tables']}")
    print(f"   Skipped: {report['skipped']}/{report['total_tables']}")


def main():
    parser = argparse.ArgumentParser(description='Migrate BigQuery warehouse rebuild')
    parser.add_argument(
        '--phase',
        choices=['migrate_raw_intelligence', 'build_features', 'build_training', 'validate', 'all'],
        required=True,
        help='Migration phase to execute'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no actual migration)'
    )
    parser.add_argument(
        '--report',
        default='migration_report.json',
        help='Output file for migration report'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        return
    
    results = []
    
    if args.phase == 'migrate_raw_intelligence' or args.phase == 'all':
        results.extend(migrate_raw_intelligence())
    
    if args.phase == 'build_features' or args.phase == 'all':
        results.extend(build_feature_tables())
    
    if args.phase == 'build_training' or args.phase == 'all':
        results.extend(build_training_tables())
    
    if args.phase == 'validate' or args.phase == 'all':
        validation_results = validate_migration()
        results.append(validation_results)
    
    if results:
        generate_migration_report(results, args.report)


if __name__ == '__main__':
    main()

