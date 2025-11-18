#!/usr/bin/env python3
"""
Week 0 Day 3: Refactor BigQuery Views to Use Prefixed Tables
Updates 12 views to reference new prefixed table architecture.
"""

import os
from google.cloud import bigquery
from typing import List, Dict, Tuple
from datetime import datetime

PROJECT_ID = "cbi-v14"
LOCATION = "us-central1"

# Views to refactor
VIEWS_TO_REFACTOR = {
    "models_v4": [
        "vw_arg_crisis_score"
    ],
    "signals": [
        "vw_bear_market_regime",
        "vw_biofuel_policy_intensity",
        "vw_biofuel_substitution_aggregates_daily",
        "vw_geopolitical_aggregates_comprehensive_daily",
        "vw_harvest_pace_signal",
        "vw_hidden_correlation_signal",
        "vw_master_signal_processor",
        "vw_sentiment_price_correlation",
        "vw_supply_glut_indicator",
        "vw_technical_aggregates_comprehensive_daily",
        "vw_trade_war_impact"
    ]
}

def get_view_definition(client: bigquery.Client, dataset_id: str, view_id: str) -> str:
    """Get the SQL definition of a view."""
    view_ref = f"{PROJECT_ID}.{dataset_id}.{view_id}"
    view = client.get_table(view_ref)
    return view.view_query

def backup_view_definition(dataset_id: str, view_id: str, sql: str):
    """Save view definition to file for backup."""
    backup_dir = "/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/migration/view_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    filename = f"{backup_dir}/{dataset_id}_{view_id}_backup.sql"
    with open(filename, 'w') as f:
        f.write(f"-- Backup of {dataset_id}.{view_id}\n")
        f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(sql)
    
    print(f"  ✓ Backed up to {filename}")

def update_view(client: bigquery.Client, dataset_id: str, view_id: str, new_sql: str) -> bool:
    """Update a view with new SQL definition."""
    try:
        view_ref = f"{PROJECT_ID}.{dataset_id}.{view_id}"
        view = client.get_table(view_ref)
        view.view_query = new_sql
        client.update_table(view, ["view_query"])
        return True
    except Exception as e:
        print(f"  ✗ Error updating view: {e}")
        return False

def refactor_models_v4_views(client: bigquery.Client):
    """Refactor views in models_v4 dataset."""
    print("\n" + "="*60)
    print("REFACTORING models_v4 VIEWS")
    print("="*60)
    
    dataset_id = "models_v4"
    view_id = "vw_arg_crisis_score"
    
    print(f"\n{view_id}:")
    print("-" * 60)
    
    # Get current definition
    original_sql = get_view_definition(client, dataset_id, view_id)
    print(f"  Original references: production_training_data")
    
    # Backup
    backup_view_definition(dataset_id, view_id, original_sql)
    
    # This view references production_training_data - need to understand what table that is
    # For now, let's just backup and note it needs manual review
    print(f"  ⚠ Requires manual review - 'production_training_data' table mapping unclear")
    print(f"  → May reference training.zl_training_prod_allhistory_baseline")
    
    return False  # Return False to indicate manual review needed

def refactor_signals_views(client: bigquery.Client):
    """Refactor views in signals dataset that reference soybean_oil_prices."""
    print("\n" + "="*60)
    print("REFACTORING signals VIEWS")
    print("="*60)
    
    dataset_id = "signals"
    views_updated = 0
    views_failed = 0
    
    for view_id in VIEWS_TO_REFACTOR["signals"]:
        print(f"\n{view_id}:")
        print("-" * 60)
        
        try:
            # Get current definition
            original_sql = get_view_definition(client, dataset_id, view_id)
            print(f"  Original references: forecasting_data_warehouse.soybean_oil_prices")
            
            # Backup
            backup_view_definition(dataset_id, view_id, original_sql)
            
            # Replace table reference
            # forecasting_data_warehouse.soybean_oil_prices → forecasting_data_warehouse.yahoo_historical_prefixed
            # WHERE symbol = 'ZL'
            # AND update column references (close → yahoo_close, etc.)
            
            new_sql = original_sql
            
            # Replace table name
            new_sql = new_sql.replace(
                "forecasting_data_warehouse.soybean_oil_prices",
                "forecasting_data_warehouse.yahoo_historical_prefixed"
            )
            
            # Add WHERE symbol = 'ZL' if not already present
            if "symbol = 'ZL'" not in new_sql and "symbol='ZL'" not in new_sql:
                # This is tricky - need to understand the view structure
                # For now, let's just note it
                print(f"  ⚠ May need WHERE symbol = 'ZL' clause added")
            
            # Replace column references (assuming they use: date, close, open, high, low, volume)
            column_mapping = {
                " close ": " yahoo_close ",
                " open ": " yahoo_open ",
                " high ": " yahoo_high ",
                " low ": " yahoo_low ",
                " volume ": " yahoo_volume ",
                "(close ": "(yahoo_close ",
                "(open ": "(yahoo_open ",
                "(high ": "(yahoo_high ",
                "(low ": "(yahoo_low ",
                "(volume ": "(yahoo_volume ",
                ",close,": ",yahoo_close,",
                ",open,": ",yahoo_open,",
                ",high,": ",yahoo_high,",
                ",low,": ",yahoo_low,",
                ",volume,": ",yahoo_volume,",
                ".close": ".yahoo_close",
                ".open": ".yahoo_open",
                ".high": ".yahoo_high",
                ".low": ".yahoo_low",
                ".volume": ".yahoo_volume"
            }
            
            for old_col, new_col in column_mapping.items():
                new_sql = new_sql.replace(old_col, new_col)
            
            # Save updated view definition
            updated_file = f"/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/migration/view_updates/{dataset_id}_{view_id}_updated.sql"
            os.makedirs(os.path.dirname(updated_file), exist_ok=True)
            with open(updated_file, 'w') as f:
                f.write(f"-- Updated {dataset_id}.{view_id}\n")
                f.write(f"-- Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(new_sql)
            
            print(f"  ✓ Updated SQL saved to {updated_file}")
            print(f"  ⚠ Review before applying - column mapping may need adjustment")
            
            views_updated += 1
            
        except Exception as e:
            print(f"  ✗ Error processing view: {e}")
            views_failed += 1
    
    return views_updated, views_failed

def main():
    """Execute Week 0 Day 3: Refactor views."""
    
    print("\n" + "="*60)
    print("Week 0 Day 3: Refactor BigQuery Views")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    print(f"\n✓ Connected to project: {PROJECT_ID}")
    
    # Create backup directories
    os.makedirs("/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/migration/view_backups", exist_ok=True)
    os.makedirs("/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/migration/view_updates", exist_ok=True)
    
    # Refactor models_v4 views
    models_v4_success = refactor_models_v4_views(client)
    
    # Refactor signals views
    signals_updated, signals_failed = refactor_signals_views(client)
    
    # Summary
    print("\n" + "="*60)
    print("REFACTORING SUMMARY")
    print("="*60)
    
    print(f"\nmodels_v4 views:")
    print(f"  - 1 view backed up (requires manual review)")
    
    print(f"\nsignals views:")
    print(f"  - {signals_updated} views processed")
    print(f"  - {signals_failed} views failed")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Review updated SQL files in docs/migration/view_updates/")
    print("2. Manually verify column mappings are correct")
    print("3. Add WHERE symbol = 'ZL' clauses where needed")
    print("4. Run view update script to apply changes")
    print("5. Test each view after update")
    print("="*60)

if __name__ == "__main__":
    main()

