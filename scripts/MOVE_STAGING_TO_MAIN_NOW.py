#!/usr/bin/env python3
"""
MOVE CRITICAL STAGING DATA TO MAIN TABLES
This is blocking our training!
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("MOVING CRITICAL DATA FROM STAGING TO MAIN")
print("=" * 80)

# 1. Create CFTC COT main table if not exists
print("\n1. CFTC COT DATA")
print("-" * 40)

create_cftc = """
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.cftc_cot` AS
SELECT * FROM `cbi-v14.staging.cftc_cot` WHERE FALSE
"""
try:
    client.query(create_cftc).result()
    print("✅ Created cftc_cot table in main")
except Exception as e:
    print(f"Table might already exist: {e}")

# Move CFTC data
move_cftc = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.cftc_cot`
SELECT * FROM `cbi-v14.staging.cftc_cot` s
WHERE NOT EXISTS (
    SELECT 1 FROM `cbi-v14.forecasting_data_warehouse.cftc_cot` m
    WHERE m.report_date = s.report_date
    AND m.commodity = s.commodity
)
"""
try:
    job = client.query(move_cftc)
    job.result()
    print(f"✅ Moved {job.num_dml_affected_rows} CFTC COT rows to main")
except Exception as e:
    logger.error(f"Error moving CFTC: {e}")

# 2. Create USDA Export Sales main table if not exists  
print("\n2. USDA EXPORT SALES DATA")
print("-" * 40)

create_usda = """
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.usda_export_sales` AS
SELECT * FROM `cbi-v14.staging.usda_export_sales` WHERE FALSE
"""
try:
    client.query(create_usda).result()
    print("✅ Created usda_export_sales table in main")
except Exception as e:
    print(f"Table might already exist: {e}")

# Move USDA data
move_usda = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.usda_export_sales`
SELECT * FROM `cbi-v14.staging.usda_export_sales` s
WHERE NOT EXISTS (
    SELECT 1 FROM `cbi-v14.forecasting_data_warehouse.usda_export_sales` m
    WHERE m.week_ending = s.week_ending
    AND m.commodity = s.commodity
)
"""
try:
    job = client.query(move_usda)
    job.result()
    print(f"✅ Moved {job.num_dml_affected_rows} USDA export sales rows to main")
except Exception as e:
    logger.error(f"Error moving USDA: {e}")

# 3. Create Biofuel Policy main table if not exists
print("\n3. BIOFUEL POLICY DATA")
print("-" * 40)

# First check what columns are in staging
check_cols = """
SELECT column_name, data_type
FROM `cbi-v14.staging.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'biofuel_policy'
ORDER BY ordinal_position
"""
print("Staging biofuel_policy columns:")
for row in client.query(check_cols):
    print(f"  • {row.column_name}: {row.data_type}")

# Create main table
create_biofuel = """
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.biofuel_policy` AS
SELECT * FROM `cbi-v14.staging.biofuel_policy` WHERE FALSE
"""
try:
    client.query(create_biofuel).result()
    print("✅ Created biofuel_policy table in main")
except Exception as e:
    print(f"Table might already exist: {e}")

# Move biofuel data
move_biofuel = """
INSERT INTO `cbi-v14.forecasting_data_warehouse.biofuel_policy`
SELECT * FROM `cbi-v14.staging.biofuel_policy` s
WHERE NOT EXISTS (
    SELECT 1 FROM `cbi-v14.forecasting_data_warehouse.biofuel_policy` m
    WHERE m.date = s.date
)
"""
try:
    job = client.query(move_biofuel)
    job.result()
    print(f"✅ Moved {job.num_dml_affected_rows} biofuel policy rows to main")
except Exception as e:
    logger.error(f"Error moving biofuel: {e}")

# 4. Verify all data is in main
print("\n" + "=" * 80)
print("VERIFICATION - DATA NOW IN MAIN TABLES:")
print("=" * 80)

tables_to_check = [
    'cftc_cot',
    'usda_export_sales', 
    'biofuel_policy'
]

for table in tables_to_check:
    query = f"""
    SELECT COUNT(*) as row_count
    FROM `cbi-v14.forecasting_data_warehouse.{table}`
    """
    try:
        result = list(client.query(query))
        if result:
            print(f"✅ forecasting_data_warehouse.{table}: {result[0].row_count} rows")
    except Exception as e:
        print(f"❌ {table}: {e}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. Fix correlation NaN issues in training views")
print("2. Train 25 models (5 horizons × 5 algorithms)")
print("3. Include biofuel bridge features")
print("4. NO MORE STAGING REFERENCES!")
print("=" * 80)
