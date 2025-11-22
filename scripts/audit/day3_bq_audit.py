import os
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

client = bigquery.Client(project='cbi-v14')

def audit_datasets():
    print("\n🔍 Auditing Datasets...")
    required_datasets = ['utils', 'market_data', 'views']
    existing_datasets = [d.dataset_id for d in client.list_datasets()]
    
    for ds in required_datasets:
        status = "✅ Found" if ds in existing_datasets else "❌ Missing"
        print(f"  - {ds}: {status}")

def audit_udfs():
    print("\n🔍 Auditing UDFs in 'utils'...")
    required_udfs = ['ema', 'macd_full']
    
    for udf in required_udfs:
        try:
            client.get_routine(f'cbi-v14.utils.{udf}')
            print(f"  - utils.{udf}: ✅ Found")
        except NotFound:
            print(f"  - utils.{udf}: ❌ Missing")

def audit_table_schema():
    print("\n🔍 Auditing 'market_data.databento_futures_ohlcv_1d' Schema...")
    try:
        table = client.get_table('cbi-v14.market_data.databento_futures_ohlcv_1d')
        columns = {col.name: col.field_type for col in table.schema}
        
        # Check against Day 3 Plan expectations
        plan_columns = {
            'data_date': 'DATE',
            'symbol': 'STRING',
            'settle': 'FLOAT' # Critical for futures
        }
        
        print(f"  - Table Exists: ✅")
        print(f"  - Row Count: {table.num_rows}")
        
        for col, expected_type in plan_columns.items():
            if col in columns:
                print(f"  - Column '{col}': ✅ Found ({columns[col]})")
            else:
                # Check for likely aliases
                if col == 'data_date' and 'date' in columns:
                    print(f"  - Column '{col}': ⚠️  Mismatch (Found 'date' instead)")
                else:
                    print(f"  - Column '{col}': ❌ Missing")
                    
    except NotFound:
        print("  - Table: ❌ Missing")

def audit_view_validity():
    print("\n🔍 Auditing 'views.precomputed_features_daily'...")
    view_id = 'cbi-v14.views.precomputed_features_daily'
    try:
        view = client.get_table(view_id)
        print(f"  - View Exists: ✅")
        
        # Test query to verify it compiles and runs (Dry Run)
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query = f"SELECT * FROM `{view_id}` WHERE data_date = '2024-01-01'"
        
        try:
            job = client.query(query, job_config=job_config)
            print(f"  - Query Validation: ✅ Valid SQL")
            print(f"  - Estimated Bytes: {job.total_bytes_processed}")
        except Exception as e:
            print(f"  - Query Validation: ❌ Invalid SQL")
            print(f"    Error: {e}")
            
    except NotFound:
        print("  - View: ❌ Missing")

if __name__ == "__main__":
    print("="*60)
    print("BIGQUERY INFRASTRUCTURE AUDIT")
    print("="*60)
    audit_datasets()
    audit_udfs()
    audit_table_schema()
    audit_view_validity()
    print("\n" + "="*60)



