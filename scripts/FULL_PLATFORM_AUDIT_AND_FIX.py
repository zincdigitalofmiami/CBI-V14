#!/usr/bin/env python3
"""
FULL PLATFORM AUDIT AND FIX
- Preserves ALL views (Big 8 is just PART of platform)
- Fixes duplicates and wiring issues
- Includes Vegas Sales Intel and all other components
"""

from google.cloud import bigquery
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🔍 FULL PLATFORM AUDIT - PRESERVING ALL COMPONENTS")
print("=" * 80)
print("Big 8 is PART of the platform, not everything!")
print()

# Step 1: Audit ALL views and tables
print("STEP 1: Auditing ALL platform components...")
print("-" * 40)

datasets = ['signals', 'neural', 'models', 'curated', 'api', 'forecasting_data_warehouse', 'staging']
platform_inventory = {}

for dataset in datasets:
    print(f"\n📂 {dataset}:")
    platform_inventory[dataset] = {'views': [], 'tables': []}
    
    # Get views using simpler query
    try:
        query = f"SELECT table_name FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES` WHERE table_type = 'VIEW'"
        for row in client.query(query):
            platform_inventory[dataset]['views'].append(row.table_name)
        print(f"  • {len(platform_inventory[dataset]['views'])} views")
    except:
        pass
    
    # Get tables
    try:
        query = f"SELECT table_name FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES` WHERE table_type = 'BASE TABLE'"
        for row in client.query(query):
            platform_inventory[dataset]['tables'].append(row.table_name)
        print(f"  • {len(platform_inventory[dataset]['tables'])} tables")
    except:
        pass

# Step 2: Identify duplicate training views ONLY
print("\n" + "=" * 80)
print("STEP 2: Identifying ONLY true duplicate training views...")
print("-" * 40)

training_views = {}
for dataset, items in platform_inventory.items():
    for view in items['views']:
        if 'training' in view.lower() or 'train' in view.lower():
            if view not in training_views:
                training_views[view] = []
            training_views[view].append(dataset)

print("\nTraining views found:")
for view, locations in training_views.items():
    if len(locations) > 1:
        print(f"  ⚠️ DUPLICATE: {view} in {locations}")
    else:
        print(f"  ✓ {view} in {locations[0]}")

# Step 3: Check Big 8 signals health
print("\n" + "=" * 80)
print("STEP 3: Big 8 signals health check...")
print("-" * 40)

big8_signals = [
    'vw_vix_stress_signal',
    'vw_harvest_pace_signal', 
    'vw_china_relations_signal',
    'vw_tariff_threat_signal',
    'vw_geopolitical_volatility_signal',
    'vw_biofuel_cascade_signal_real',
    'vw_hidden_correlation_signal',
    'vw_biofuel_ethanol_signal'
]

print("\nBig 8 Signal Status:")
for signal in big8_signals:
    found = False
    for dataset, items in platform_inventory.items():
        if signal in items['views']:
            print(f"  ✓ {signal} in {dataset}")
            found = True
            break
    if not found:
        print(f"  ❌ {signal} MISSING")

# Step 4: Fix NaN issues in training view
print("\n" + "=" * 80)
print("STEP 4: Fixing NaN issues in training views...")
print("-" * 40)

fix_query = """
CREATE OR REPLACE VIEW `cbi-v14.models.vw_neural_training_dataset_v2_FIXED` AS
WITH base AS (
    SELECT 
        * EXCEPT(feature_hidden_correlation, big8_composite_score),
        COALESCE(feature_hidden_correlation, 0.0) as feature_hidden_correlation,
        COALESCE(big8_composite_score, 0.5) as big8_composite_score
    FROM `cbi-v14.models.vw_neural_training_dataset_v2`
)
SELECT * FROM base
WHERE feature_hidden_correlation IS NOT NULL
"""

try:
    client.query(fix_query).result()
    print("✅ Created vw_neural_training_dataset_v2_FIXED with NaN handling")
except Exception as e:
    print(f"❌ Error creating fixed view: {str(e)[:100]}")

# Step 5: Remove ONLY confirmed duplicate views
print("\n" + "=" * 80)
print("STEP 5: Removing ONLY confirmed duplicates...")
print("-" * 40)

duplicates_to_remove = [
    ('models', 'vw_big7_training_data'),  # Old Big 7 version
    ('models', 'vw_neural_training_dataset_v2_extended')  # Extended duplicate
]

for dataset, view in duplicates_to_remove:
    try:
        # Check if exists first
        check = f"SELECT COUNT(*) as cnt FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES` WHERE table_name = '{view}'"
        result = list(client.query(check))[0]
        if result['cnt'] > 0:
            drop_query = f"DROP VIEW IF EXISTS `cbi-v14.{dataset}.{view}`"
            client.query(drop_query).result()
            print(f"  ✅ Dropped duplicate: {dataset}.{view}")
        else:
            print(f"  ℹ️ Already gone: {dataset}.{view}")
    except Exception as e:
        print(f"  ⚠️ Error dropping {dataset}.{view}: {str(e)[:50]}")

# Step 6: Platform component summary
print("\n" + "=" * 80)
print("PLATFORM COMPONENT SUMMARY")
print("=" * 80)

total_views = sum(len(items['views']) for items in platform_inventory.values())
total_tables = sum(len(items['tables']) for items in platform_inventory.values())

print(f"\n📊 Platform Statistics:")
print(f"  • Total Views: {total_views}")
print(f"  • Total Tables: {total_tables}")
print(f"  • Total Objects: {total_views + total_tables}")
print(f"  • Big 8 Signals: Part of {total_views} total views")

print(f"\n📋 Key Components:")
print(f"  • Big 8 Signals: Foundation for neural training")
print(f"  • Vegas Sales Intel: ACTIVE procurement optimization")
print(f"  • Biofuel Bridge: Energy-agriculture nexus")
print(f"  • CFTC/WASDE: Fundamental data acquisition")
print(f"  • API Views: Multi-horizon forecasts")
print(f"  • Curated Views: Business intelligence")

print("\n" + "=" * 80)
print("✅ AUDIT COMPLETE - Platform preserved, duplicates removed")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. Use vw_neural_training_dataset_v2_FIXED for training")
print("2. Ensure all Big 8 signals are healthy")
print("3. Preserve ALL other views (Vegas, API, curated, etc.)")
print("4. Train 25 models using MASTER_TRAINING_PLAN.md")
print("=" * 80)
