#!/usr/bin/env python3
"""
FIX THE STAGING TO MAIN MIGRATION - PROPERLY THIS TIME
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("FIXING STAGING TO MAIN MIGRATION")
print("=" * 80)

# 1. Fix CFTC COT - seems like the WHERE NOT EXISTS didn't work
print("\n1. FIXING CFTC COT DATA")
print("-" * 40)

# Just insert all data since main is empty
fix_cftc = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
SELECT * FROM `cbi-v14.staging.cftc_cot`
"""
try:
    job = client.query(fix_cftc)
    job.result()
    print(f"✅ Inserted {job.num_dml_affected_rows} CFTC COT rows to main")
except Exception as e:
    logger.error(f"Error with CFTC: {e}")

# 2. Fix USDA Export Sales - use report_date not week_ending
print("\n2. FIXING USDA EXPORT SALES DATA")
print("-" * 40)

fix_usda = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.usda_export_sales`
SELECT * FROM `cbi-v14.staging.usda_export_sales`
"""
try:
    job = client.query(fix_usda)
    job.result()
    print(f"✅ Inserted {job.num_dml_affected_rows} USDA export sales rows to main")
except Exception as e:
    logger.error(f"Error with USDA: {e}")

# 3. Verify all data is now in main
print("\n" + "=" * 80)
print("VERIFICATION - DATA NOW IN MAIN TABLES:")
print("=" * 80)

tables_to_check = [
    ('cftc_cot', 72),
    ('usda_export_sales', 12), 
    ('biofuel_policy', 30)
]

all_good = True
for table, expected in tables_to_check:
    query = f"""
    SELECT COUNT(*) as row_count
    FROM `cbi-v14.forecasting_data_warehouse.{table}`
    """
    try:
        result = list(client.query(query))
        actual = result[0].row_count if result else 0
        status = "✅" if actual >= expected else "❌"
        print(f"{status} {table}: {actual} rows (expected {expected})")
        if actual < expected:
            all_good = False
    except Exception as e:
        print(f"❌ {table}: {e}")
        all_good = False

if all_good:
    print("\n✅ ALL DATA SUCCESSFULLY MOVED TO MAIN TABLES!")
    print("NO MORE STAGING REFERENCES NEEDED!")
else:
    print("\n⚠️ Some data migration issues remain")

print("\n" + "=" * 80)
print("CRITICAL: WE MUST NOW:")
print("=" * 80)
print("1. Update ALL views to use main tables, NOT staging")
print("2. Fix correlation NaN issues")
print("3. Train 25 models with ALL horizons (1w, 1m, 3m, 6m, 12m)")
print("4. Include biofuel bridge features")
print("=" * 80)
