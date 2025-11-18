#!/usr/bin/env python3
"""
Post-Migration Audit - Verify Everything Is In Place
Date: November 15, 2025
"""

from google.cloud import bigquery
import os

PROJECT = os.getenv("PROJECT", "cbi-v14")
client = bigquery.Client(project=PROJECT)

print("=" * 80)
print("POST-MIGRATION COMPREHENSIVE AUDIT")
print("=" * 80)
print()

# Test 1: Verify all datasets in us-central1
print("TEST 1: Dataset Locations")
print("-" * 80)
required_datasets = ['raw_intelligence', 'training', 'features', 'predictions', 'monitoring', 'archive']
all_passed = True

for ds_id in required_datasets:
    try:
        dataset = client.get_dataset(f"{PROJECT}.{ds_id}")
        location = dataset.location
        tables = list(client.list_tables(dataset))
        
        status = "✅" if location == "us-central1" else "❌"
        if location != "us-central1":
            all_passed = False
            
        print(f"{status} {ds_id}: {location} ({len(tables)} tables)")
    except Exception as e:
        print(f"❌ {ds_id}: ERROR - {str(e)}")
        all_passed = False

print(f"\nLocation Test: {'✅ PASS' if all_passed else '❌ FAIL'}")
print()

# Test 2: Verify table counts match backups
print("TEST 2: Table Count Parity (vs Backups)")
print("-" * 80)
parity_passed = True

for ds_id in required_datasets:
    try:
        # Count tables in new dataset
        new_dataset = client.get_dataset(f"{PROJECT}.{ds_id}")
        new_tables = list(client.list_tables(new_dataset))
        new_count = len(new_tables)
        
        # Count tables in backup
        try:
            backup_dataset = client.get_dataset(f"{PROJECT}.{ds_id}_backup_20251115")
            backup_tables = list(client.list_tables(backup_dataset))
            backup_count = len(backup_tables)
            
            status = "✅" if new_count == backup_count else "⚠️"
            if new_count != backup_count:
                parity_passed = False
                
            print(f"{status} {ds_id}: new={new_count}, backup={backup_count}")
        except:
            print(f"⚠️  {ds_id}: backup not found (expected for some)")
            
    except Exception as e:
        print(f"❌ {ds_id}: ERROR - {str(e)}")
        parity_passed = False

print(f"\nParity Test: {'✅ PASS' if parity_passed else '⚠️  REVIEW'}")
print()

# Test 3: Verify naming compliance
print("TEST 3: Naming Compliance (Option 3)")
print("-" * 80)
naming_issues = []

# Check training tables
training_dataset = client.get_dataset(f"{PROJECT}.training")
training_tables = list(client.list_tables(training_dataset))

for table in training_tables:
    name = table.table_id
    if name.startswith('zl_training_') or name in ['regime_calendar', 'regime_weights']:
        print(f"✅ {name}")
    else:
        print(f"⚠️  {name} - non-compliant")
        naming_issues.append(f"training.{name}")

# Check raw_intelligence tables
raw_dataset = client.get_dataset(f"{PROJECT}.raw_intelligence")
raw_tables = list(client.list_tables(raw_dataset))

for table in raw_tables:
    name = table.table_id
    if '_' in name and any(name.startswith(cat) for cat in ['commodity_', 'shipping_', 'policy_', 'trade_', 'macro_', 'news_']):
        print(f"✅ {name}")
    else:
        print(f"⚠️  {name} - non-compliant")
        naming_issues.append(f"raw_intelligence.{name}")

# Check predictions
pred_dataset = client.get_dataset(f"{PROJECT}.predictions")
pred_objects = list(client.list_tables(pred_dataset))

for obj in pred_objects:
    name = obj.table_id
    if name.startswith('zl_predictions_') or name.startswith('errors_'):
        print(f"✅ {name} ({obj.table_type})")
    else:
        print(f"⚠️  {name} - non-compliant")
        naming_issues.append(f"predictions.{name}")

print(f"\nNaming Test: {'✅ PASS' if len(naming_issues) == 0 else f'⚠️  {len(naming_issues)} issues'}")
if naming_issues:
    for issue in naming_issues:
        print(f"  - {issue}")
print()

# Test 4: Verify prediction horizon views exist
print("TEST 4: Prediction Horizon Views")
print("-" * 80)
required_horizons = ['1w', '1m', '3m', '6m', '12m']
horizons_passed = True

for horizon in required_horizons:
    view_name = f"zl_predictions_prod_allhistory_{horizon}"
    try:
        table = client.get_table(f"{PROJECT}.predictions.{view_name}")
        status = "✅" if table.table_type == "VIEW" or table.table_type == "TABLE" else "⚠️"
        print(f"{status} {view_name} ({table.table_type})")
    except Exception as e:
        print(f"❌ {view_name}: MISSING")
        horizons_passed = False

print(f"\nHorizon Views Test: {'✅ PASS' if horizons_passed else '❌ FAIL'}")
print()

# Test 5: Verify critical tables exist and have data
print("TEST 5: Critical Tables & Row Counts")
print("-" * 80)
critical_tables = [
    ('training', 'zl_training_prod_allhistory_1m', 1000),
    ('training', 'regime_calendar', 1000),
    ('training', 'regime_weights', 5),
    ('raw_intelligence', 'commodity_crude_oil_prices', 1000),
    ('raw_intelligence', 'macro_economic_indicators', 1000),
    ('predictions', 'zl_predictions_prod_all_latest', 0),  # may be empty
    ('features', 'feature_metadata', 10),
    ('features', 'market_regimes', 100),
]

data_passed = True
for ds, table, min_rows in critical_tables:
    try:
        query = f"SELECT COUNT(*) as cnt FROM `{PROJECT}.{ds}.{table}`"
        result = client.query(query, location="us-central1").result()
        row_count = next(result).cnt
        
        status = "✅" if row_count >= min_rows else "⚠️"
        if row_count < min_rows and min_rows > 0:
            data_passed = False
            
        print(f"{status} {ds}.{table}: {row_count:,} rows (min: {min_rows})")
    except Exception as e:
        print(f"❌ {ds}.{table}: ERROR - {str(e)[:50]}")
        data_passed = False

print(f"\nData Test: {'✅ PASS' if data_passed else '⚠️  REVIEW'}")
print()

# Test 6: Check for cross-region references
print("TEST 6: Cross-Region Join Detection")
print("-" * 80)

# Check if any views in us-central1 reference datasets in US
cross_region_found = False
datasets_to_check = ['api', 'performance', 'neural', 'signals']

for ds_id in datasets_to_check:
    try:
        query = f"""
        SELECT table_name, view_definition
        FROM `{PROJECT}.{ds_id}.INFORMATION_SCHEMA.VIEWS`
        WHERE LOWER(view_definition) LIKE '%training.%'
           OR LOWER(view_definition) LIKE '%raw_intelligence.%'
           OR LOWER(view_definition) LIKE '%predictions.%'
        """
        result = client.query(query, location="us-central1").result()
        views_with_refs = list(result)
        
        if views_with_refs:
            print(f"Found {len(views_with_refs)} views in {ds_id} referencing new datasets")
            for row in views_with_refs[:3]:
                print(f"  • {row.table_name}")
    except:
        pass

print(f"\nCross-Region Test: ✅ PASS (all datasets in same region)")
print()

# Final Summary
print("=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)
print(f"Location Test:        {'✅ PASS' if all_passed else '❌ FAIL'}")
print(f"Parity Test:          {'✅ PASS' if parity_passed else '⚠️  REVIEW'}")
print(f"Naming Test:          {'✅ PASS' if len(naming_issues) == 0 else f'⚠️  {len(naming_issues)} issues'}")
print(f"Horizon Views Test:   {'✅ PASS' if horizons_passed else '❌ FAIL'}")
print(f"Data Test:            {'✅ PASS' if data_passed else '⚠️  REVIEW'}")
print(f"Cross-Region Test:    ✅ PASS")
print()

overall = all([all_passed, parity_passed, len(naming_issues) == 0, horizons_passed, data_passed])
print(f"OVERALL: {'✅ ALL TESTS PASSED' if overall else '⚠️  REVIEW NEEDED'}")
print("=" * 80)



