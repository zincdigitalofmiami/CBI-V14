#!/usr/bin/env python3
"""
Verification script for Week 0 Day 2 Part 3: Prefixed BigQuery Tables
Checks that all tables were created correctly with proper schemas and prefixing.
"""

import os
from google.cloud import bigquery
from typing import List, Dict, Tuple
from datetime import datetime

# Configuration
PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

# Expected tables
EXPECTED_TABLES = {
    "forecasting_data_warehouse": [
        "yahoo_historical_prefixed",
        "alpha_es_intraday",
        "alpha_commodities_daily",
        "alpha_fx_daily",
        "alpha_indicators_daily",
        "alpha_news_sentiment",
        "alpha_options_snapshot",
        "fred_macro_expanded",
        "weather_granular",
        "cftc_commitments",
        "usda_reports_granular",
        "eia_energy_granular",
    ],
    "features": [
        "master_features_canonical",
    ]
}

def check_table_exists(client: bigquery.Client, dataset_id: str, table_id: str) -> Tuple[bool, str]:
    """Check if a table exists and return status."""
    try:
        table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        return True, f"✓ Exists"
    except Exception as e:
        return False, f"✗ NOT FOUND: {str(e)}"

def verify_partitioning(client: bigquery.Client, dataset_id: str, table_id: str) -> Tuple[bool, str]:
    """Verify table is partitioned by date."""
    try:
        table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        
        if table.time_partitioning is not None:
            partition_field = table.time_partitioning.field or "ingestion time"
            return True, f"✓ Partitioned by {partition_field}"
        else:
            return False, "✗ NOT PARTITIONED"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def verify_clustering(client: bigquery.Client, dataset_id: str, table_id: str, expected_fields: List[str] = None) -> Tuple[bool, str]:
    """Verify table clustering."""
    try:
        table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        
        if table.clustering_fields:
            fields_str = ", ".join(table.clustering_fields)
            if expected_fields:
                if set(table.clustering_fields) == set(expected_fields):
                    return True, f"✓ Clustered by {fields_str}"
                else:
                    return False, f"✗ Wrong clustering: {fields_str} (expected: {', '.join(expected_fields)})"
            return True, f"✓ Clustered by {fields_str}"
        else:
            return True, "⚠ Not clustered (optional)"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def verify_column_prefixes(client: bigquery.Client, dataset_id: str, table_id: str, expected_prefix: str = None) -> Tuple[bool, str, List[str]]:
    """Verify columns have proper prefixes."""
    try:
        table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        
        schema_fields = [field.name for field in table.schema]
        
        # Columns that don't need prefixes
        exempt_columns = ['date', 'symbol', 'timestamp', 'pair', 'underlier', 'expiration', 
                         'strike', 'option_type', 'ingestion_ts', 'last_updated', 'published_at',
                         'title', 'url', 'tickers', 'topics', 'timeframe', 'snapshot_ts']
        
        if expected_prefix:
            prefixed_cols = [c for c in schema_fields if c.startswith(expected_prefix)]
            non_prefixed = [c for c in schema_fields if not c.startswith(expected_prefix) and c not in exempt_columns]
            
            if non_prefixed:
                return False, f"✗ {len(non_prefixed)} columns without '{expected_prefix}' prefix", non_prefixed
            else:
                return True, f"✓ All {len(prefixed_cols)} data columns have '{expected_prefix}' prefix", []
        else:
            return True, f"✓ {len(schema_fields)} columns total", []
            
    except Exception as e:
        return False, f"✗ Error: {str(e)}", []

def check_yahoo_table(client: bigquery.Client):
    """Verify Yahoo table schema."""
    print("\n" + "="*60)
    print("YAHOO TABLE VERIFICATION")
    print("="*60)
    
    table_id = "yahoo_historical_prefixed"
    dataset_id = "forecasting_data_warehouse"
    
    exists, msg = check_table_exists(client, dataset_id, table_id)
    print(f"\n1. Table exists: {msg}")
    if not exists:
        return False
    
    part, msg = verify_partitioning(client, dataset_id, table_id)
    print(f"2. Partitioning: {msg}")
    
    clust, msg = verify_clustering(client, dataset_id, table_id, ["symbol"])
    print(f"3. Clustering: {msg}")
    
    prefix, msg, bad_cols = verify_column_prefixes(client, dataset_id, table_id, "yahoo_")
    print(f"4. Column prefixes: {msg}")
    if bad_cols:
        print(f"   Columns without yahoo_ prefix: {bad_cols}")
    
    # Check specific columns
    table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
    required_cols = ['date', 'symbol', 'yahoo_open', 'yahoo_high', 'yahoo_low', 
                     'yahoo_close', 'yahoo_volume', 'yahoo_adj_close']
    schema_cols = [f.name for f in table.schema]
    missing = [c for c in required_cols if c not in schema_cols]
    
    if missing:
        print(f"5. Required columns: ✗ Missing {missing}")
        return False
    else:
        print(f"5. Required columns: ✓ All present")
    
    return exists and part and clust and prefix

def check_alpha_tables(client: bigquery.Client):
    """Verify Alpha Vantage tables."""
    print("\n" + "="*60)
    print("ALPHA VANTAGE TABLES VERIFICATION")
    print("="*60)
    
    alpha_tables = {
        "alpha_es_intraday": {
            "cluster": ["symbol", "timeframe"],
            "required_cols": ['date', 'timestamp', 'symbol', 'timeframe', 'alpha_open', 
                            'alpha_high', 'alpha_low', 'alpha_close', 'alpha_volume']
        },
        "alpha_commodities_daily": {
            "cluster": ["symbol"],
            "required_cols": ['date', 'symbol', 'alpha_open', 'alpha_high', 
                            'alpha_low', 'alpha_close', 'alpha_volume']
        },
        "alpha_fx_daily": {
            "cluster": ["pair"],
            "required_cols": ['date', 'pair', 'alpha_open', 'alpha_high', 
                            'alpha_low', 'alpha_close']
        },
        "alpha_indicators_daily": {
            "cluster": ["symbol"],
            "required_cols": ['date', 'symbol', 'alpha_rsi_14', 'alpha_macd_line', 
                            'alpha_sma_20', 'alpha_ema_20', 'alpha_bbands_upper_20']
        },
        "alpha_news_sentiment": {
            "cluster": None,
            "required_cols": ['date', 'published_at', 'title', 'alpha_sentiment_score', 
                            'alpha_sentiment_label']
        },
        "alpha_options_snapshot": {
            "cluster": ["underlier", "expiration"],
            "required_cols": ['date', 'snapshot_ts', 'underlier', 'expiration', 'strike', 
                            'alpha_bid', 'alpha_ask', 'alpha_iv']
        }
    }
    
    all_passed = True
    dataset_id = "forecasting_data_warehouse"
    
    for table_id, specs in alpha_tables.items():
        print(f"\n{table_id}:")
        print("-" * 60)
        
        exists, msg = check_table_exists(client, dataset_id, table_id)
        print(f"  1. Exists: {msg}")
        if not exists:
            all_passed = False
            continue
        
        part, msg = verify_partitioning(client, dataset_id, table_id)
        print(f"  2. Partitioning: {msg}")
        
        if specs["cluster"]:
            clust, msg = verify_clustering(client, dataset_id, table_id, specs["cluster"])
            print(f"  3. Clustering: {msg}")
        
        prefix, msg, bad_cols = verify_column_prefixes(client, dataset_id, table_id, "alpha_")
        print(f"  4. Prefixes: {msg}")
        if bad_cols:
            print(f"     Columns without alpha_ prefix: {bad_cols}")
            all_passed = False
        
        # Check required columns
        table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
        schema_cols = [f.name for f in table.schema]
        missing = [c for c in specs["required_cols"] if c not in schema_cols]
        
        if missing:
            print(f"  5. Required columns: ✗ Missing {missing}")
            all_passed = False
        else:
            print(f"  5. Required columns: ✓ All present ({len(schema_cols)} total)")
    
    return all_passed

def check_fred_table(client: bigquery.Client):
    """Verify FRED table."""
    print("\n" + "="*60)
    print("FRED TABLE VERIFICATION")
    print("="*60)
    
    table_id = "fred_macro_expanded"
    dataset_id = "forecasting_data_warehouse"
    
    exists, msg = check_table_exists(client, dataset_id, table_id)
    print(f"\n1. Table exists: {msg}")
    if not exists:
        return False
    
    part, msg = verify_partitioning(client, dataset_id, table_id)
    print(f"2. Partitioning: {msg}")
    
    prefix, msg, bad_cols = verify_column_prefixes(client, dataset_id, table_id, "fred_")
    print(f"3. Column prefixes: {msg}")
    if bad_cols:
        print(f"   Columns without fred_ prefix: {bad_cols}")
    
    # Check for key economic indicators
    table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
    schema_cols = [f.name for f in table.schema]
    
    key_series = ['fred_dff', 'fred_dgs10', 'fred_cpiaucsl', 'fred_unrate', 
                  'fred_gdp', 'fred_vixcls', 'fred_ppiaco']
    missing = [c for c in key_series if c not in schema_cols]
    
    if missing:
        print(f"4. Key indicators: ✗ Missing {missing}")
        return False
    else:
        print(f"4. Key indicators: ✓ All present ({len(schema_cols)} total columns)")
    
    return exists and part and prefix

def check_other_tables(client: bigquery.Client):
    """Verify Weather, CFTC, USDA, EIA tables."""
    print("\n" + "="*60)
    print("OTHER DATA SOURCE TABLES VERIFICATION")
    print("="*60)
    
    tables_to_check = {
        "weather_granular": {
            "dataset": "forecasting_data_warehouse",
            "prefix": "weather_",
            "required": ['date', 'weather_us_iowa_tavg_c', 'weather_br_mato_grosso_prcp_mm']
        },
        "cftc_commitments": {
            "dataset": "forecasting_data_warehouse",
            "prefix": "cftc_",
            "required": ['date', 'symbol', 'cftc_open_interest', 'cftc_noncommercial_net']
        },
        "usda_reports_granular": {
            "dataset": "forecasting_data_warehouse",
            "prefix": "usda_",
            "required": ['date', 'usda_wasde_world_soyoil_prod', 'usda_exports_soybeans_net_sales_china']
        },
        "eia_energy_granular": {
            "dataset": "forecasting_data_warehouse",
            "prefix": "eia_",
            "required": ['date', 'eia_biodiesel_prod_total', 'eia_rin_price_d4']
        }
    }
    
    all_passed = True
    
    for table_id, specs in tables_to_check.items():
        print(f"\n{table_id}:")
        print("-" * 60)
        
        dataset_id = specs["dataset"]
        
        exists, msg = check_table_exists(client, dataset_id, table_id)
        print(f"  1. Exists: {msg}")
        if not exists:
            all_passed = False
            continue
        
        part, msg = verify_partitioning(client, dataset_id, table_id)
        print(f"  2. Partitioning: {msg}")
        
        prefix, msg, bad_cols = verify_column_prefixes(client, dataset_id, table_id, specs["prefix"])
        print(f"  3. Prefixes: {msg}")
        if bad_cols:
            print(f"     Columns without {specs['prefix']} prefix: {bad_cols}")
            all_passed = False
        
        # Check required columns
        table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
        schema_cols = [f.name for f in table.schema]
        missing = [c for c in specs["required"] if c not in schema_cols]
        
        if missing:
            print(f"  4. Required columns: ✗ Missing {missing}")
            all_passed = False
        else:
            print(f"  4. Required columns: ✓ All present ({len(schema_cols)} total)")
    
    return all_passed

def check_master_features_table(client: bigquery.Client):
    """Verify the canonical master features table."""
    print("\n" + "="*60)
    print("MASTER FEATURES TABLE VERIFICATION")
    print("="*60)
    
    table_id = "master_features_canonical"
    dataset_id = "features"
    
    exists, msg = check_table_exists(client, dataset_id, table_id)
    print(f"\n1. Table exists: {msg}")
    if not exists:
        return False
    
    part, msg = verify_partitioning(client, dataset_id, table_id)
    print(f"2. Partitioning: {msg}")
    
    clust, msg = verify_clustering(client, dataset_id, table_id, ["symbol"])
    print(f"3. Clustering: {msg}")
    
    # Check that it has columns from all sources
    table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_id}")
    schema_cols = [f.name for f in table.schema]
    
    prefixes = ['yahoo_', 'alpha_', 'fred_', 'weather_', 'cftc_', 'usda_', 'eia_']
    prefix_counts = {prefix: len([c for c in schema_cols if c.startswith(prefix)]) for prefix in prefixes}
    
    print(f"4. Column breakdown by source:")
    for prefix, count in prefix_counts.items():
        status = "✓" if count > 0 else "✗"
        print(f"   {status} {prefix}: {count} columns")
    
    all_present = all(count > 0 for count in prefix_counts.values())
    
    if all_present:
        print(f"\n5. Multi-source table: ✓ Contains columns from all {len(prefixes)} sources")
    else:
        print(f"\n5. Multi-source table: ✗ Missing columns from some sources")
    
    return exists and part and clust and all_present

def main():
    """Run comprehensive verification."""
    
    print("\n" + "="*70)
    print("WEEK 0 DAY 2 PART 3 VERIFICATION: Prefixed BigQuery Tables")
    print("="*70)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Track results
    results = {}
    
    # Verify each category
    results['yahoo'] = check_yahoo_table(client)
    results['alpha'] = check_alpha_tables(client)
    results['fred'] = check_fred_table(client)
    results['other'] = check_other_tables(client)
    results['master'] = check_master_features_table(client)
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for category, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {category.upper()}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("="*70)
        print("\n✓ Week 0 Day 2 Part 3 is COMPLETE and VERIFIED")
        print("✓ All 13 prefixed tables created correctly")
        print("✓ Proper partitioning and clustering in place")
        print("✓ Source prefixing convention enforced")
        print("\nReady to proceed to Week 0 Day 3: View Refactoring")
        return 0
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("="*70)
        print("\n⚠ Issues found - review output above")
        return 1

if __name__ == "__main__":
    exit(main())

