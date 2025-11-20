#!/usr/bin/env python3
"""
BigQuery Deployment Validation Script
Date: November 18, 2025
Purpose: Comprehensive validation battery for BigQuery deployment
"""

import os
import argparse
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import sys
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

# Expected datasets
EXPECTED_DATASETS = [
    "market_data",
    "raw_intelligence",
    "signals",
    "features",
    "training",
    "regimes",
    "drivers",
    "neural",
    "predictions",
    "monitoring",
    "dim",
    "ops",
]

# Critical tables that must exist
CRITICAL_TABLES = {
    "market_data": [
        "databento_futures_ohlcv_1m",
        "databento_futures_ohlcv_1d",
        "databento_futures_continuous_1d",
        "yahoo_zl_historical_2000_2010",
    ],
    "signals": [
        "big_eight_live",
        "crush_oilshare_daily",
        "hidden_relationship_signals",
    ],
    "features": [
        "master_features",
    ],
    "training": [
        "regime_calendar",
        "regime_weights",
        "zl_training_prod_allhistory_1w",
        "mes_training_prod_allhistory_1min",
    ],
    "regimes": [
        "market_regimes",
    ],
    "ops": [
        "ingestion_runs",
        "data_quality_events",
    ],
}

# Expected overlay views
EXPECTED_VIEWS = {
    "api": [
        "vw_futures_overlay_1w",
        "vw_futures_overlay_1m",
        "vw_futures_overlay_3m",
        "vw_futures_overlay_6m",
        "vw_futures_overlay_12m",
        "vw_futures_overlay_1min",
        "vw_futures_overlay_5min",
        "vw_futures_overlay_15min",
        "vw_futures_overlay_30min",
        "vw_futures_overlay_1hr",
        "vw_futures_overlay_4hr",
        "vw_futures_overlay_1d",
        "vw_futures_overlay_7d",
        "vw_futures_overlay_30d",
    ],
    "predictions": [
        "vw_zl_1w_latest",
        "vw_zl_1m_latest",
        "vw_zl_3m_latest",
        "vw_zl_6m_latest",
        "vw_zl_12m_latest",
    ],
    "regimes": [
        "vw_live_regime_overlay",
    ],
    "training": [
        "vw_zl_training_prod_allhistory_1w",
        "vw_zl_training_prod_allhistory_1m",
        "vw_zl_training_prod_allhistory_3m",
        "vw_zl_training_prod_allhistory_6m",
        "vw_zl_training_prod_allhistory_12m",
    ],
    "signals": [
        "vw_big8_signals",
    ],
    "features": [
        "vw_mes_intraday_overlay",
        "vw_mes_daily_aggregated",
    ],
}

def get_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)

def check_dataset_exists(client, dataset_id):
    """Check if dataset exists"""
    try:
        client.get_dataset(dataset_id)
        return True
    except NotFound:
        return False

def list_tables(client, dataset_id):
    """List all tables in dataset"""
    try:
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))
        return [table.table_id for table in tables]
    except NotFound:
        return []

def list_views(client, dataset_id):
    """List all views in dataset"""
    try:
        query = f"""
        SELECT table_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.VIEWS`
        """
        results = client.query(query).result()
        return [row.table_name for row in results]
    except Exception as e:
        return []

def get_table_info(client, dataset_id, table_id):
    """Get table information"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        table = client.get_table(table_ref)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{dataset_id}.{table_id}`"
        count_result = client.query(count_query).result()
        row_count = list(count_result)[0].cnt if count_result else 0
        
        return {
            "exists": True,
            "num_rows": row_count,
            "num_columns": len(table.schema),
            "partitioning": table.time_partitioning is not None,
            "clustering": table.clustering_fields is not None if hasattr(table, 'clustering_fields') else False,
        }
    except NotFound:
        return {"exists": False}
    except Exception as e:
        return {"exists": False, "error": str(e)}

def check_column_prefixes(client, dataset_id, table_id, required_prefixes):
    """Check if columns have required prefixes"""
    try:
        query = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_id}'
          AND column_name NOT IN ('date', 'symbol', 'as_of', 'collection_timestamp', 'ts_event')
        """
        results = client.query(query).result()
        columns = [row.column_name for row in results]
        
        issues = []
        for col in columns:
            has_prefix = any(col.startswith(prefix) for prefix in required_prefixes)
            if not has_prefix:
                issues.append(col)
        
        return {"valid": len(issues) == 0, "issues": issues}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def validate_datasets(client):
    """Validate all datasets exist"""
    print("📁 Validating Datasets...")
    print("-" * 60)
    
    all_exist = True
    for dataset_id in EXPECTED_DATASETS:
        exists = check_dataset_exists(client, dataset_id)
        status = "✅" if exists else "❌"
        print(f"{status} {dataset_id}")
        if not exists:
            all_exist = False
    
    print()
    return all_exist

def validate_tables(client):
    """Validate critical tables exist"""
    print("📊 Validating Critical Tables...")
    print("-" * 60)
    
    all_exist = True
    for dataset_id, table_list in CRITICAL_TABLES.items():
        print(f"\n{dataset_id}:")
        for table_id in table_list:
            info = get_table_info(client, dataset_id, table_id)
            if info.get("exists"):
                row_count = info.get("num_rows", 0)
                col_count = info.get("num_columns", 0)
                part = "📅" if info.get("partitioning") else ""
                cluster = "🔗" if info.get("clustering") else ""
                print(f"  ✅ {table_id} ({row_count:,} rows, {col_count} cols) {part}{cluster}")
            else:
                print(f"  ❌ {table_id} - MISSING")
                all_exist = False
    
    print()
    return all_exist

def validate_views(client):
    """Validate overlay views exist"""
    print("👁️  Validating Overlay Views...")
    print("-" * 60)
    
    all_exist = True
    total_views = 0
    for dataset_id, view_list in EXPECTED_VIEWS.items():
        print(f"\n{dataset_id}:")
        existing_views = list_views(client, dataset_id)
        for view_id in view_list:
            if view_id in existing_views:
                print(f"  ✅ {view_id}")
                total_views += 1
            else:
                print(f"  ❌ {view_id} - MISSING")
                all_exist = False
    
    print(f"\nTotal views found: {total_views}/{sum(len(v) for v in EXPECTED_VIEWS.values())}")
    print()
    return all_exist

def validate_master_features(client):
    """Validate master_features table"""
    print("🔍 Validating master_features...")
    print("-" * 60)
    
    info = get_table_info(client, "features", "master_features")
    if not info.get("exists"):
        print("❌ master_features table does not exist")
        return False
    
    row_count = info.get("num_rows", 0)
    col_count = info.get("num_columns", 0)
    
    print(f"  Rows: {row_count:,}")
    print(f"  Columns: {col_count}")
    
    # Check column prefixes
    required_prefixes = ['yahoo_', 'databento_', 'fred_', 'eia_', 'usda_', 'cftc_', 'weather_', 'policy_']
    prefix_check = check_column_prefixes(client, "features", "master_features", required_prefixes)
    
    if prefix_check.get("valid"):
        print(f"  ✅ Column prefixes valid")
    else:
        issues = prefix_check.get("issues", [])
        if issues:
            print(f"  ⚠️  Columns without prefixes: {issues[:10]}...")
        else:
            print(f"  ⚠️  Could not validate prefixes")
    
    # Check for required columns
    query = f"""
    SELECT column_name
    FROM `{PROJECT_ID}.features.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'master_features'
      AND column_name IN ('yahoo_zl_close', 'databento_zl_close', 'fred_dgs10', 'big8_composite_score')
    """
    results = client.query(query).result()
    found_cols = [row.column_name for row in results]
    
    print(f"  Required columns found: {len(found_cols)}/4")
    for col in ['yahoo_zl_close', 'databento_zl_close', 'fred_dgs10', 'big8_composite_score']:
        status = "✅" if col in found_cols else "❌"
        print(f"    {status} {col}")
    
    print()
    return col_count >= 400 and len(found_cols) >= 3

def smoke_test_views(client):
    """Smoke test overlay views"""
    print("💨 Smoke Testing Overlay Views...")
    print("-" * 60)
    
    test_views = [
        ("api", "vw_futures_overlay_1w"),
        ("predictions", "vw_zl_1w_latest"),
        ("regimes", "vw_live_regime_overlay"),
        ("signals", "vw_big8_signals"),
    ]
    
    all_pass = True
    for dataset_id, view_id in test_views:
        try:
            query = f"SELECT * FROM `{PROJECT_ID}.{dataset_id}.{view_id}` LIMIT 1"
            result = client.query(query).result()
            rows = list(result)
            print(f"  ✅ {dataset_id}.{view_id} - Query successful ({len(rows)} rows)")
        except Exception as e:
            print(f"  ❌ {dataset_id}.{view_id} - Query failed: {str(e)[:100]}")
            all_pass = False
    
    print()
    return all_pass

def validate_training_tables(client):
    """Validate training tables"""
    print("🎓 Validating Training Tables...")
    print("-" * 60)
    
    # Check ZL tables
    zl_tables = [
        "zl_training_prod_allhistory_1w",
        "zl_training_prod_allhistory_1m",
        "zl_training_prod_allhistory_3m",
        "zl_training_prod_allhistory_6m",
        "zl_training_prod_allhistory_12m",
    ]
    
    print("ZL Training Tables:")
    zl_ok = True
    for table_id in zl_tables:
        info = get_table_info(client, "training", table_id)
        if info.get("exists"):
            row_count = info.get("num_rows", 0)
            print(f"  ✅ {table_id} ({row_count:,} rows)")
        else:
            print(f"  ❌ {table_id} - MISSING")
            zl_ok = False
    
    # Check MES tables
    mes_tables = [
        "mes_training_prod_allhistory_1min",
        "mes_training_prod_allhistory_5min",
        "mes_training_prod_allhistory_15min",
        "mes_training_prod_allhistory_30min",
        "mes_training_prod_allhistory_1hr",
        "mes_training_prod_allhistory_4hr",
        "mes_training_prod_allhistory_1d",
        "mes_training_prod_allhistory_7d",
        "mes_training_prod_allhistory_30d",
        "mes_training_prod_allhistory_3m",
        "mes_training_prod_allhistory_6m",
        "mes_training_prod_allhistory_12m",
    ]
    
    print("\nMES Training Tables:")
    mes_ok = True
    for table_id in mes_tables:
        info = get_table_info(client, "training", table_id)
        if info.get("exists"):
            row_count = info.get("num_rows", 0)
            print(f"  ✅ {table_id} ({row_count:,} rows)")
        else:
            print(f"  ❌ {table_id} - MISSING")
            mes_ok = False
    
    print()
    return zl_ok and mes_ok

def main():
    """Main validation execution"""
    parser = argparse.ArgumentParser(
        description="Validate BigQuery deployment"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Validate specific deployment phase (1=schema, 3=views, 4=data, 5=full)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CBI-V14 BigQuery Deployment Validation")
    if args.phase:
        print(f"Phase: {args.phase}")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    client = get_client()
    
    results = {}
    
    # Run validations based on phase
    if args.phase == 1:
        # Phase 1: Schema only
        results["datasets"] = validate_datasets(client)
        results["tables"] = validate_tables(client)
    elif args.phase == 3:
        # Phase 3: Views only
        results["views"] = validate_views(client)
    elif args.phase == 4:
        # Phase 4: Data migration
        results["master_features"] = validate_master_features(client)
        results["training_tables"] = validate_training_tables(client)
    elif args.phase == 5 or args.phase is None:
        # Phase 5 or full validation
        results["datasets"] = validate_datasets(client)
        results["tables"] = validate_tables(client)
        results["views"] = validate_views(client)
        results["master_features"] = validate_master_features(client)
        results["training_tables"] = validate_training_tables(client)
        results["smoke_tests"] = smoke_test_views(client)
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_pass = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
        if not passed:
            all_pass = False
    
    print()
    print("=" * 60)
    if all_pass:
        print("✅ ALL VALIDATIONS PASSED - Deployment Ready!")
    else:
        print("❌ SOME VALIDATIONS FAILED - Review issues above")
    print("=" * 60)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
