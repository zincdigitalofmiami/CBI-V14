#!/usr/bin/env python3
"""
CHECK FOR ALL DUPLICATES AND EXISTING VIEWS/SIGNALS
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("🔍 COMPLETE SYSTEM AUDIT - FINDING ALL DUPLICATES")
print("=" * 80)

# 1. Check SIGNALS dataset
print("\n1️⃣ SIGNALS DATASET:")
try:
    query = "SELECT table_name, table_type FROM `cbi-v14.signals.INFORMATION_SCHEMA.TABLES` ORDER BY table_name"
    for row in client.query(query):
        print(f"  • {row.table_name} ({row.table_type})")
except Exception as e:
    print(f"  Error: {e}")

# 2. Check NEURAL dataset
print("\n2️⃣ NEURAL DATASET:")
try:
    query = "SELECT table_name, table_type FROM `cbi-v14.neural.INFORMATION_SCHEMA.TABLES` ORDER BY table_name"
    for row in client.query(query):
        print(f"  • {row.table_name} ({row.table_type})")
except Exception as e:
    print(f"  Error: {e}")

# 3. Check MODELS dataset
print("\n3️⃣ MODELS DATASET (Training Views & Models):")
try:
    query = "SELECT table_name, table_type FROM `cbi-v14.models.INFORMATION_SCHEMA.TABLES` ORDER BY table_name"
    count = 0
    for row in client.query(query):
        if row.table_name.startswith('vw_') or row.table_name.startswith('zl_'):
            print(f"  • {row.table_name} ({row.table_type})")
            count += 1
    print(f"  Total: {count} views/models")
except Exception as e:
    print(f"  Error: {e}")

# 4. Find all signal-related views across datasets
print("\n4️⃣ ALL SIGNAL-RELATED VIEWS:")
signal_views = {}
datasets = ['signals', 'neural', 'models', 'curated']

for dataset in datasets:
    try:
        query = f"SELECT table_name FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES` WHERE LOWER(table_name) LIKE '%signal%'"
        for row in client.query(query):
            if row.table_name not in signal_views:
                signal_views[row.table_name] = []
            signal_views[row.table_name].append(dataset)
    except:
        pass

for view_name, locations in sorted(signal_views.items()):
    if len(locations) > 1:
        print(f"  ⚠️ DUPLICATE: {view_name} in {', '.join(locations)}")
    else:
        print(f"  ✓ {view_name} in {locations[0]}")

# 5. Check for training-related views
print("\n5️⃣ TRAINING-RELATED VIEWS:")
training_views = {}
for dataset in datasets:
    try:
        query = f"SELECT table_name FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.TABLES` WHERE LOWER(table_name) LIKE '%training%' OR LOWER(table_name) LIKE '%correlation%' OR LOWER(table_name) LIKE '%feature%'"
        for row in client.query(query):
            if row.table_name not in training_views:
                training_views[row.table_name] = []
            training_views[row.table_name].append(dataset)
    except:
        pass

for view_name, locations in sorted(training_views.items()):
    if len(locations) > 1:
        print(f"  ⚠️ DUPLICATE: {view_name} in {', '.join(locations)}")
    else:
        print(f"  ✓ {view_name} in {locations[0]}")

# 6. Test if vw_big_eight_signals exists and works
print("\n6️⃣ BIG 8 SIGNALS STATUS:")
try:
    # First check if it exists
    check_exists = "SELECT COUNT(*) as cnt FROM `cbi-v14.neural.INFORMATION_SCHEMA.TABLES` WHERE table_name = 'vw_big_eight_signals'"
    exists = list(client.query(check_exists))[0]['cnt']
    
    if exists > 0:
        print("  ✅ neural.vw_big_eight_signals EXISTS")
        # Now check its data
        test_query = """
        SELECT COUNT(*) as rows
        FROM `cbi-v14.neural.vw_big_eight_signals`
        LIMIT 1
        """
        result = list(client.query(test_query))[0]
        print(f"     Contains {result['rows']} rows")
    else:
        print("  ❌ neural.vw_big_eight_signals DOES NOT EXIST")
except Exception as e:
    print(f"  ❌ Error checking vw_big_eight_signals: {str(e)[:100]}")

# 7. Check for vw_big_seven_signals (old version)
print("\n7️⃣ CHECKING FOR OLD BIG 7 SIGNALS:")
try:
    check_old = "SELECT COUNT(*) as cnt FROM `cbi-v14.neural.INFORMATION_SCHEMA.TABLES` WHERE table_name = 'vw_big_seven_signals'"
    exists = list(client.query(check_old))[0]['cnt']
    if exists > 0:
        print("  ⚠️ neural.vw_big_seven_signals STILL EXISTS (old version)")
    else:
        print("  ✓ No old vw_big_seven_signals found")
except:
    pass

# 8. Check what correlation features exist
print("\n8️⃣ CORRELATION FEATURES:")
try:
    query = """
    SELECT table_name, table_schema 
    FROM `cbi-v14.models.INFORMATION_SCHEMA.TABLES` 
    WHERE LOWER(table_name) LIKE '%corr%'
    """
    for row in client.query(query):
        print(f"  • {row.table_schema}.{row.table_name}")
except:
    print("  No correlation views found")

# 9. Check what training datasets exist
print("\n9️⃣ TRAINING DATASETS:")
try:
    query = """
    SELECT table_name 
    FROM `cbi-v14.models.INFORMATION_SCHEMA.TABLES` 
    WHERE table_name LIKE 'vw_%training%' OR table_name LIKE 'vw_%neural%'
    ORDER BY table_name
    """
    for row in client.query(query):
        print(f"  • models.{row.table_name}")
except:
    print("  No training views found")

print("\n" + "=" * 80)
print("DUPLICATES TO DELETE:")
print("=" * 80)

# List all duplicates found
duplicates_to_delete = []
for view_name, locations in signal_views.items():
    if len(locations) > 1:
        duplicates_to_delete.append(f"{view_name} (in: {', '.join(locations)})")

for view_name, locations in training_views.items():
    if len(locations) > 1 and view_name not in [v.split(' ')[0] for v in duplicates_to_delete]:
        duplicates_to_delete.append(f"{view_name} (in: {', '.join(locations)})")

if duplicates_to_delete:
    print("\nFound these duplicates to clean up:")
    for dup in duplicates_to_delete:
        print(f"  ❌ {dup}")
else:
    print("\n✅ No duplicates found!")

print("\n" + "=" * 80)
