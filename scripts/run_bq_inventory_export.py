import os
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import Forbidden, BadRequest
from tqdm import tqdm
import warnings

# Suppress pandas future warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIGURATION ---
PROJECT_ID = "cbi-v14"
OUTPUT_DIR = "GPT_Data"
# --- END CONFIGURATION ---

def execute_query(client, query, description="query"):
    """Executes a BigQuery query and returns a pandas DataFrame."""
    try:
        # TQDM progress bar setup
        with tqdm(total=1, desc=f"   Executing {description}", leave=False) as pbar:
            df = client.query(query).to_dataframe()
            pbar.update(1)
        return df
    except (Forbidden, BadRequest) as e:
        tqdm.write(f"   ⚠️ ERROR executing {description}: {e}")
        tqdm.write(f"   Query: {query[:500]}...")
        return pd.DataFrame() # Return empty dataframe on error

def get_datasets(client):
    """Get all datasets in the project."""
    datasets = [d.dataset_id for d in client.list_datasets()]
    return [d for d in datasets if d not in ('_SESSION')]

def get_full_inventory(client, datasets):
    """
    Builds a full inventory of all tables across all datasets and regions.
    This is the robust replacement for the original INFORMATION_SCHEMA query.
    """
    all_tables_df = pd.DataFrame()
    with tqdm(total=len(datasets), desc="1/10: Full Inventory", unit="dataset") as pbar:
        for dataset_id in datasets:
            try:
                dataset = client.get_dataset(dataset_id)
                region = dataset.location.lower()
                
                # Some locations are multi-region like 'US', some are specific like 'us-central1'
                # We need to handle both cases for INFORMATION_SCHEMA
                schema_region = f"region-{region}"

                query = f"""
                SELECT
                    table_catalog AS project_id,
                    table_schema AS dataset_name,
                    table_name,
                    table_type,
                    row_count,
                    creation_time,
                    last_modified_time
                FROM `{PROJECT_ID}.{schema_region}.INFORMATION_SCHEMA.TABLES`
                WHERE table_schema = '{dataset_id}'
                AND table_type IN ('BASE TABLE', 'VIEW', 'MATERIALIZED VIEW');
                """
                df = client.query(query).to_dataframe()
                if not df.empty:
                    all_tables_df = pd.concat([all_tables_df, df], ignore_index=True)
            
            except Exception as e:
                pbar.write(f"Could not process dataset {dataset_id}: {e}")
            finally:
                pbar.update(1)
    
    all_tables_df.sort_values(by=['dataset_name', 'table_name'], inplace=True)
    return all_tables_df
    
def get_all_columns(client, datasets):
    """Gets all column definitions."""
    all_columns_df = pd.DataFrame()
    with tqdm(total=len(datasets), desc="2/10: All Columns", unit="dataset") as pbar:
        for dataset_id in datasets:
            try:
                dataset = client.get_dataset(dataset_id)
                region = dataset.location.lower()
                schema_region = f"region-{region}"

                query = f"""
                SELECT
                    table_schema AS dataset_name,
                    table_name,
                    column_name,
                    ordinal_position,
                    data_type,
                    is_nullable
                FROM `{PROJECT_ID}.{schema_region}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_schema = '{dataset_id}';
                """
                df = client.query(query).to_dataframe()
                if not df.empty:
                    all_columns_df = pd.concat([all_columns_df, df], ignore_index=True)
            except Exception as e:
                pbar.write(f"Could not process columns for dataset {dataset_id}: {e}")
            finally:
                pbar.update(1)

    all_columns_df.sort_values(by=['dataset_name', 'table_name', 'ordinal_position'], inplace=True)
    return all_columns_df

def get_historical_summary(client):
    """Dynamically finds date columns and summarizes historical tables."""
    tables_to_summarise = [
      ('forecasting_data_warehouse', 'soybean_oil_prices'),
      ('forecasting_data_warehouse', 'corn_prices'),
      ('forecasting_data_warehouse', 'wheat_prices'),
      ('yahoo_finance_comprehensive', 'yahoo_normalized'),
      ('models_v4', 'pre_crisis_2000_2007_historical'),
      ('models_v4', 'crisis_2008_historical'),
      ('models_v4', 'recovery_2010_2016_historical'),
      ('models_v4', 'trade_war_2017_2019_historical'),
      ('models_v4', 'trump_rich_2023_2025')
    ]
    
    results = []
    with tqdm(total=len(tables_to_summarise), desc="9/10: Historical Sources", unit="table") as pbar:
        for dataset, table_name in tables_to_summarise:
            try:
                table_ref = client.get_table(f"{PROJECT_ID}.{dataset}.{table_name}")
                schema = table_ref.schema
                
                # Dynamically find the date/timestamp column
                date_col = None
                for col in schema:
                    if 'date' in col.name.lower() and col.field_type in ('DATE', 'TIMESTAMP', 'DATETIME'):
                        date_col = col.name
                        break
                if not date_col: # Fallback if no obvious date column
                    for col in schema:
                         if col.field_type in ('DATE', 'TIMESTAMP', 'DATETIME'):
                            date_col = col.name
                            break
                
                if not date_col:
                    pbar.write(f"   ⚠️ No date column found for {dataset}.{table_name}. Skipping summary.")
                    results.append({'dataset': dataset, 'table_name': table_name, 'row_count': table_ref.num_rows, 'earliest_date': None, 'latest_date': None, 'error': 'No date column found'})
                    pbar.update(1)
                    continue

                query = f"""
                SELECT
                    '{dataset}' as dataset,
                    '{table_name}' as table_name,
                    COUNT(*) AS row_count,
                    MIN(CAST({date_col} AS DATE)) AS earliest_date,
                    MAX(CAST({date_col} AS DATE)) AS latest_date
                FROM `{PROJECT_ID}.{dataset}.{table_name}`
                """
                df = client.query(query).to_dataframe()
                results.append(df)

            except Exception as e:
                pbar.write(f"   ⚠️ Could not query {dataset}.{table_name}: {e}")
                results.append({'dataset': dataset, 'table_name': table_name, 'row_count': 0, 'earliest_date': None, 'latest_date': None, 'error': str(e)})

            finally:
                pbar.update(1)
    
    # Concatenate all results, handling potential empty/error dataframes
    final_df_list = []
    for r in results:
        if isinstance(r, pd.DataFrame):
            final_df_list.append(r)
        elif isinstance(r, dict):
             final_df_list.append(pd.DataFrame([r]))
             
    if not final_df_list:
        return pd.DataFrame()

    return pd.concat(final_df_list, ignore_index=True)


def main():
    """Main function to generate all inventory CSVs."""
    print("======================================================================")
    print("    🤖  CBI-V14 BigQuery Inventory Exporter for GPT-5")
    print("======================================================================")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✅ Authenticated to BigQuery project: {PROJECT_ID}")
    except Exception as e:
        print(f"❌ CRITICAL: Could not authenticate to BigQuery. {e}")
        print("   Please ensure you have run 'gcloud auth application-default login'")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✅ Created output directory: {OUTPUT_DIR}")
        
    # --- Execute Queries ---
    
    # 1. Full Inventory (Robust version)
    inventory_df = get_full_inventory(client, get_datasets(client))
    inventory_df.to_csv(os.path.join(OUTPUT_DIR, "inventory_340_objects.csv"), index=False)
    tqdm.write("   ✅ 1/10: Saved inventory_340_objects.csv")

    # 2. All Columns (Robust version)
    columns_df = get_all_columns(client, get_datasets(client))
    columns_df.to_csv(os.path.join(OUTPUT_DIR, "schema_all_columns.csv"), index=False)
    tqdm.write("   ✅ 2/10: Saved schema_all_columns.csv")

    # 3. Production Training Tables
    prod_tables_df = execute_query(client, """
        WITH cols AS (
          SELECT table_schema, table_name, COUNT(*) AS column_count
          FROM `cbi-v14.us.INFORMATION_SCHEMA.COLUMNS`
          WHERE table_schema = 'models_v4' AND table_name LIKE 'production_training_data_%'
          GROUP BY 1, 2
        )
        SELECT t.table_schema AS dataset_name, t.table_name, t.row_count, c.column_count
        FROM `cbi-v14.us.INFORMATION_SCHEMA.TABLES` t JOIN cols c ON t.table_schema = c.table_schema AND t.table_name = c.table_name
        WHERE t.table_schema = 'models_v4' AND t.table_name LIKE 'production_training_data_%'
        ORDER BY t.table_name;
    """, "3/10: Prod Tables")
    prod_tables_df.to_csv(os.path.join(OUTPUT_DIR, "production_tables_detail.csv"), index=False)
    tqdm.write("   ✅ 3/10: Saved production_tables_detail.csv")

    # 4. Dataset Summary
    dataset_summary_df = execute_query(client, """
        SELECT
          table_schema  AS dataset_name,
          COUNTIF(table_type = 'BASE TABLE') AS table_count,
          COUNTIF(table_type = 'VIEW') AS view_count,
          COUNTIF(table_type = 'MATERIALIZED VIEW') AS materialized_view_count,
          COUNT(*) AS total_objects
        FROM `cbi-v14.us.INFORMATION_SCHEMA.TABLES`
        GROUP BY 1 ORDER BY 1;
    """, "4/10: Dataset Summary")
    dataset_summary_df.to_csv(os.path.join(OUTPUT_DIR, "dataset_summary.csv"), index=False)
    tqdm.write("   ✅ 4/10: Saved dataset_summary.csv")

    # 5. Empty/Minimal Tables
    empty_tables_df = execute_query(client, """
        SELECT table_schema  AS dataset_name, table_name, row_count, creation_time
        FROM `cbi-v14.us.INFORMATION_SCHEMA.TABLES`
        WHERE (row_count IS NULL OR row_count = 0) AND table_type = 'BASE TABLE'
        ORDER BY 1, 2;
    """, "5/10: Empty Tables")
    empty_tables_df.to_csv(os.path.join(OUTPUT_DIR, "empty_minimal_tables.csv"), index=False)
    tqdm.write("   ✅ 5/10: Saved empty_minimal_tables.csv")
    
    # 6. Duplicate Table Names
    duplicates_df = execute_query(client, """
        SELECT
          table_name,
          ARRAY_TO_STRING(ARRAY_AGG(DISTINCT table_schema ORDER BY table_schema), ', ') AS datasets,
          COUNT(DISTINCT table_schema) AS dataset_count
        FROM `cbi-v14.us.INFORMATION_SCHEMA.TABLES`
        GROUP BY 1 HAVING COUNT(DISTINCT table_schema) > 1 ORDER BY 3 DESC, 1;
    """, "6/10: Duplicates")
    duplicates_df.to_csv(os.path.join(OUTPUT_DIR, "duplicate_table_names.csv"), index=False)
    tqdm.write("   ✅ 6/10: Saved duplicate_table_names.csv")

    # 7. Column Name Frequency
    column_freq_df = execute_query(client, """
        SELECT
          column_name,
          COUNT(*) AS occurrences,
          ARRAY_TO_STRING(ARRAY_AGG(DISTINCT CONCAT(table_schema, '.', table_name)), ', ') AS tables
        FROM `cbi-v14.us.INFORMATION_SCHEMA.COLUMNS`
        GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 500;
    """, "7/10: Column Freq")
    column_freq_df.to_csv(os.path.join(OUTPUT_DIR, "column_name_frequency.csv"), index=False)
    tqdm.write("   ✅ 7/10: Saved column_name_frequency.csv")

    # 8. Production Features (290)
    prod_features_df = execute_query(client, """
        SELECT column_name, ordinal_position, data_type
        FROM `cbi-v14.us.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_schema = 'models_v4' AND table_name = 'production_training_data_1m'
        ORDER BY 2;
    """, "8/10: Prod Features")
    prod_features_df.to_csv(os.path.join(OUTPUT_DIR, "production_features_290.csv"), index=False)
    tqdm.write("   ✅ 8/10: Saved production_features_290.csv")

    # 9. Historical Sources (Robust version)
    historical_df = get_historical_summary(client)
    historical_df.to_csv(os.path.join(OUTPUT_DIR, "historical_data_sources.csv"), index=False)
    tqdm.write("   ✅ 9/10: Saved historical_data_sources.csv")
    
    # 10. Models & Training Inventory
    models_inv_df = execute_query(client, """
        WITH column_counts AS (
          SELECT table_schema, table_name, COUNT(*) AS column_count
          FROM `cbi-v14.us.INFORMATION_SCHEMA.COLUMNS`
          WHERE table_schema LIKE 'models%' GROUP BY 1, 2
        )
        SELECT t.table_schema AS dataset_name, t.table_name, t.table_type, t.row_count, c.column_count
        FROM `cbi-v14.us.INFORMATION_SCHEMA.TABLES` t JOIN column_counts c USING(table_schema, table_name)
        WHERE t.table_schema LIKE 'models%' ORDER BY 1, 2;
    """, "10/10: Models Inv")
    models_inv_df.to_csv(os.path.join(OUTPUT_DIR, "models_training_inventory.csv"), index=False)
    tqdm.write("   ✅ 10/10: Saved models_training_inventory.csv")

    print("----------------------------------------------------------------------")
    print(f"✅ SUCCESS: All 10 inventory files exported to '{OUTPUT_DIR}'")
    print("----------------------------------------------------------------------")
    print("\nNEXT STEPS:")
    print(f"1. Commit and push the '{OUTPUT_DIR}' folder to GitHub.")
    print("2. Send the CSV files to GPT-5 for architectural design.")

if __name__ == "__main__":
    main()
