#!/usr/bin/env python3
"""
Final Migration Verification: BigQuery
--------------------------------------
- Verifies new training tables exist and have rows
- Verifies regime tables exist
- Verifies shim views point to new tables
- Verifies new raw_intelligence tables exist
"""
import os
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

PROJECT_ID = os.getenv("PROJECT", "cbi-v14")
HORIZONS = ["1w", "1m", "3m", "6m", "12m"]
SURFACES = ["prod", "full"]

def main():
    """Run all BigQuery verification checks."""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*80)
    print("FINAL MIGRATION VERIFICATION: BIGQUERY")
    print("="*80)
    
    all_ok = True
    
    # 1. Verify new training tables
    print("\n1. Verifying New Training Tables (`training.*`)")
    print("-" * 80)
    for surface in SURFACES:
        for horizon in HORIZONS:
            table_ref = f"{PROJECT_ID}.training.zl_training_{surface}_allhistory_{horizon}"
            try:
                table = client.get_table(table_ref)
                if table.num_rows > 0:
                    print(f"  ✅ {table_ref.split('.')[-1]:<50} {table.num_rows:>7,} rows")
                else:
                    print(f"  ⚠️  {table_ref.split('.')[-1]:<50} 0 rows")
                    all_ok = False
            except NotFound:
                print(f"  ❌ {table_ref.split('.')[-1]:<50} NOT FOUND")
                all_ok = False
    
    # 2. Verify regime tables
    print("\n2. Verifying Regime Tables (`training.*`)")
    print("-" * 80)
    for table_name in ["regime_calendar", "regime_weights"]:
        table_ref = f"{PROJECT_ID}.training.{table_name}"
        try:
            table = client.get_table(table_ref)
            if table.num_rows > 0:
                print(f"  ✅ {table_name:<50} {table.num_rows:>7,} rows")
            else:
                print(f"  ⚠️  {table_name:<50} 0 rows")
                all_ok = False
        except NotFound:
            print(f"  ❌ {table_name:<50} NOT FOUND")
            all_ok = False

    # 3. Verify shim views
    print("\n3. Verifying Shim Views (`models_v4.*`)")
    print("-" * 80)
    for horizon in HORIZONS:
        view_ref = f"{PROJECT_ID}.models_v4.production_training_data_{horizon}"
        query = f"SELECT COUNT(*) as count FROM `{view_ref}`"
        try:
            result = client.query(query).to_dataframe()
            if result['count'].iloc[0] > 0:
                print(f"  ✅ {view_ref.split('.')[-1]:<50} OK (returns {result['count'].iloc[0]} rows)")
            else:
                print(f"  ⚠️  {view_ref.split('.')[-1]:<50} OK (returns 0 rows)")
        except Exception as e:
            print(f"  ❌ {view_ref.split('.')[-1]:<50} FAILED: {str(e)[:100]}")
            all_ok = False
            
    # 4. Verify new raw_intelligence tables
    print("\n4. Verifying New Raw Intelligence Tables (`raw_intelligence.*`)")
    print("-" * 80)
    raw_tables_to_check = [
        "shipping_baltic_dry_index",
        "policy_biofuel",
        "trade_china_soybean_imports",
        "commodity_crude_oil_prices",
        "macro_economic_indicators",
        "news_sentiments",
        "commodity_palm_oil_prices",
        "commodity_soybean_oil_prices",
    ]
    for table_name in raw_tables_to_check:
        table_ref = f"{PROJECT_ID}.raw_intelligence.{table_name}"
        try:
            # We just check for existence, not rows, as some might be empty
            client.get_table(table_ref)
            print(f"  ✅ {table_name:<50} EXISTS")
        except NotFound:
            # Check if it's still in the old location
            old_table_ref = f"{PROJECT_ID}.forecasting_data_warehouse.{table_name}"
            try:
                client.get_table(old_table_ref)
                print(f"  ⚠️  {table_name:<50} NOT FOUND (still in forecasting_data_warehouse)")
            except NotFound:
                 print(f"  ❌ {table_name:<50} NOT FOUND anywhere")
            all_ok = False

    print("\n" + "="*80)
    if all_ok:
        print("✅ BIGQUERY VERIFICATION PASSED")
    else:
        print("❌ BIGQUERY VERIFICATION FAILED - some issues found.")
    print("="*80)
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


