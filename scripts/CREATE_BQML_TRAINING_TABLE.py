#!/usr/bin/env python3
"""
CREATE PROPER BQML-COMPATIBLE TRAINING TABLE
With ALL features but NO correlated subqueries
"""

from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')

print("=" * 80)
print("CREATING BQML-COMPATIBLE TRAINING TABLE WITH ALL FEATURES")
print("=" * 80)

# Strategy: Materialize the view by actually executing it and saving results
# This breaks the correlated subquery chain

query = """
CREATE OR REPLACE TABLE `cbi-v14.models.training_full_materialized`
CLUSTER BY date
AS
SELECT *
FROM `cbi-v14.models.vw_neural_training_dataset`
WHERE date >= '2020-01-01'
"""

print("\nAttempting to materialize vw_neural_training_dataset...")
print("(This will scan the view and save as a table)")

try:
    job = client.query(query)
    result = job.result()
    
    # Verify
    check = list(client.query("""
    SELECT 
        COUNT(*) as row_count,
        COUNT(DISTINCT date) as dates
    FROM `cbi-v14.models.training_full_materialized`
    """).result())[0]
    
    # Get columns
    cols = list(client.query("""
    SELECT COUNT(*) as col_count
    FROM `cbi-v14.models.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'training_full_materialized'
    """).result())[0]
    
    print(f"\n✅ SUCCESS!")
    print(f"   Rows: {check.row_count:,}")
    print(f"   Unique dates: {check.dates:,}")
    print(f"   Columns: {cols.col_count}")
    
    # Test BQML compatibility
    print("\nTesting BQML compatibility...")
    test = """
    CREATE OR REPLACE MODEL `cbi-v14.models.test_bqml_compat`
    OPTIONS(
        model_type='LINEAR_REG',
        input_label_cols=['target_1w'],
        max_iterations=1
    ) AS
    SELECT * EXCEPT(date, target_1w, target_1m, target_3m, target_6m), target_1w
    FROM `cbi-v14.models.training_full_materialized`
    WHERE target_1w IS NOT NULL
    LIMIT 100
    """
    
    client.query(test).result()
    print("✅ BQML COMPATIBLE!")
    
    # Cleanup
    client.query("DROP MODEL `cbi-v14.models.test_bqml_compat`").result()
    
    print("\n" + "=" * 80)
    print("✅ READY FOR TRAINING")
    print("=" * 80)
    print(f"Use table: models.training_full_materialized")
    print(f"Features: {cols.col_count - 5} (excluding date + 4 targets)")
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ FAILED: {error_msg[:200]}")
    
    if "Correlated subqueries" in error_msg:
        print("\n⚠️  MATERIALIZATION FAILED - VIEW HAS CORRELATED SUBQUERIES")
        print("\nALTERNATIVE APPROACH NEEDED:")
        print("  Cannot materialize a view with correlated subqueries")
        print("  Must rebuild view definition WITHOUT window functions over JOINs")













