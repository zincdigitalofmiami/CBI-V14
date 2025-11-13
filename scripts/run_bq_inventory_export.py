import os
import pandas as pd
from typing import List, Dict
from google.cloud import bigquery
from tqdm import tqdm
import warnings

warnings.simplefilter("ignore", category=FutureWarning)

PROJECT_ID = "cbi-v14"
OUTPUT_DIR = "GPT_Data"


def list_datasets(client: bigquery.Client) -> List[Dict[str, str]]:
    datasets = []
    for dataset_item in client.list_datasets():
        dataset_ref = client.get_dataset(dataset_item.reference)
        datasets.append({
            "dataset_id": dataset_ref.dataset_id,
            "location": dataset_ref.location
        })
    return datasets


def build_inventory(client: bigquery.Client, datasets: List[Dict[str, str]]) -> pd.DataFrame:
    records = []
    with tqdm(total=len(datasets), desc="1/10: Full Inventory", unit="dataset") as pbar:
        for dataset in datasets:
            dataset_id = dataset["dataset_id"]
            location = dataset["location"]
            try:
                tables = client.list_tables(dataset_id)
                for table_item in tables:
                    table = client.get_table(table_item.reference)
                    records.append({
                        "dataset_name": dataset_id,
                        "table_name": table.table_id,
                        "table_type": table.table_type,
                        "row_count": table.num_rows if table.table_type == "TABLE" else None,
                        "created": table.created,
                        "modified": table.modified,
                        "location": location,
                        "partitioning": getattr(table.time_partitioning, "type_", None) if getattr(table, "time_partitioning", None) else None,
                        "clustering": ", ".join(table.clustering_fields) if getattr(table, "clustering_fields", None) else None
                    })
            except Exception as exc:
                pbar.write(f"   ⚠️ Could not process dataset {dataset_id}: {exc}")
            finally:
                pbar.update(1)
    inventory_df = pd.DataFrame(records)
    if inventory_df.empty:
        raise RuntimeError("Failed to gather inventory from BigQuery; no records returned.")
    inventory_df.sort_values(["dataset_name", "table_name"], inplace=True)
    return inventory_df.reset_index(drop=True)


def build_columns(client: bigquery.Client, datasets: List[Dict[str, str]]) -> pd.DataFrame:
    records = []
    with tqdm(total=len(datasets), desc="2/10: All Columns", unit="dataset") as pbar:
        for dataset in datasets:
            dataset_id = dataset["dataset_id"]
            try:
                tables = client.list_tables(dataset_id)
                for table_item in tables:
                    table = client.get_table(table_item.reference)
                    for idx, column in enumerate(table.schema, start=1):
                        records.append({
                            "dataset_name": dataset_id,
                            "table_name": table.table_id,
                            "column_name": column.name,
                            "ordinal_position": idx,
                            "data_type": column.field_type,
                            "is_nullable": column.is_nullable
                        })
            except Exception as exc:
                pbar.write(f"   ⚠️ Could not retrieve columns for {dataset_id}: {exc}")
            finally:
                pbar.update(1)
    columns_df = pd.DataFrame(records)
    if columns_df.empty:
        raise RuntimeError("Column enumeration returned no records; aborting.")
    columns_df.sort_values(["dataset_name", "table_name", "ordinal_position"], inplace=True)
    return columns_df.reset_index(drop=True)


def summarize_historical_tables(client: bigquery.Client) -> pd.DataFrame:
    targets = [
        ("forecasting_data_warehouse", "soybean_oil_prices"),
        ("forecasting_data_warehouse", "corn_prices"),
        ("forecasting_data_warehouse", "wheat_prices"),
        ("yahoo_finance_comprehensive", "yahoo_normalized"),
        ("models_v4", "pre_crisis_2000_2007_historical"),
        ("models_v4", "crisis_2008_historical"),
        ("models_v4", "recovery_2010_2016_historical"),
        ("models_v4", "trade_war_2017_2019_historical"),
        ("models_v4", "trump_rich_2023_2025")
    ]
    rows = []
    with tqdm(total=len(targets), desc="9/10: Historical Sources", unit="table") as pbar:
        for dataset_id, table_name in targets:
            try:
                table = client.get_table(f"{PROJECT_ID}.{dataset_id}.{table_name}")
                date_column = None
                for column in table.schema:
                    if column.field_type in {"DATE", "TIMESTAMP", "DATETIME"}:
                        if "date" in column.name.lower():
                            date_column = column.name
                            break
                if not date_column:
                    for column in table.schema:
                        if column.field_type in {"DATE", "TIMESTAMP", "DATETIME"}:
                            date_column = column.name
                            break
                if not date_column:
                    rows.append({
                        "dataset": dataset_id,
                        "table_name": table_name,
                        "row_count": table.num_rows,
                        "earliest_date": None,
                        "latest_date": None,
                        "error": "No date-like column"
                    })
                else:
                    query = f"""
                        SELECT
                          COUNT(*) AS row_count,
                          MIN(CAST({date_column} AS DATE)) AS earliest_date,
                          MAX(CAST({date_column} AS DATE)) AS latest_date
                        FROM `{PROJECT_ID}.{dataset_id}.{table_name}`
                    """
                    result = client.query(query).to_dataframe().iloc[0]
                    rows.append({
                        "dataset": dataset_id,
                        "table_name": table_name,
                        "row_count": int(result["row_count"]),
                        "earliest_date": result["earliest_date"],
                        "latest_date": result["latest_date"],
                        "error": None
                    })
            except Exception as exc:
                rows.append({
                    "dataset": dataset_id,
                    "table_name": table_name,
                    "row_count": None,
                    "earliest_date": None,
                    "latest_date": None,
                    "error": str(exc)
                })
            finally:
                pbar.update(1)
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, filename: str):
    df.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)


def main():
    print("======================================================================")
    print("    🤖  CBI-V14 BigQuery Inventory Exporter for GPT-5")
    print("======================================================================")

    client = bigquery.Client(project=PROJECT_ID)
    print(f"✅ Authenticated to BigQuery project: {PROJECT_ID}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✅ Output directory ready: {OUTPUT_DIR}")

    datasets = list_datasets(client)
    inventory_df = build_inventory(client, datasets)
    write_csv(inventory_df, "inventory_340_objects.csv")
    print("   ✅ 1/10: Saved inventory_340_objects.csv")

    columns_df = build_columns(client, datasets)
    write_csv(columns_df, "schema_all_columns.csv")
    print("   ✅ 2/10: Saved schema_all_columns.csv")

    # 3. Production tables detail
    prod_tables = inventory_df[
        (inventory_df["dataset_name"] == "models_v4") &
        (inventory_df["table_name"].str.startswith("production_training_data_"))
    ].copy()
    column_counts = columns_df.groupby(["dataset_name", "table_name"]).size().reset_index(name="column_count")
    prod_tables = prod_tables.merge(column_counts, on=["dataset_name", "table_name"], how="left")
    write_csv(prod_tables, "production_tables_detail.csv")
    print("   ✅ 3/10: Saved production_tables_detail.csv")

    # 4. Dataset summary
    summary = inventory_df.groupby(["dataset_name", "table_type"]).size().unstack(fill_value=0)
    summary["total_objects"] = summary.sum(axis=1)
    summary = summary.reset_index().rename(columns={
        "TABLE": "table_count",
        "VIEW": "view_count",
        "MATERIALIZED_VIEW": "materialized_view_count"
    })
    write_csv(summary, "dataset_summary.csv")
    print("   ✅ 4/10: Saved dataset_summary.csv")

    # 5. Empty/minimal tables
    empty_tables = inventory_df[(inventory_df["row_count"].isna()) | (inventory_df["row_count"] == 0)].copy()
    write_csv(empty_tables, "empty_minimal_tables.csv")
    print("   ✅ 5/10: Saved empty_minimal_tables.csv")

    # 6. Duplicate table names
    duplicates = inventory_df.groupby("table_name")["dataset_name"].agg(lambda x: sorted(set(x))).reset_index()
    duplicates["dataset_count"] = duplicates["dataset_name"].apply(len)
    duplicates = duplicates[duplicates["dataset_count"] > 1].copy()
    duplicates["datasets"] = duplicates["dataset_name"].apply(lambda x: ", ".join(x))
    duplicates.drop(columns=["dataset_name"], inplace=True)
    write_csv(duplicates, "duplicate_table_names.csv")
    print("   ✅ 6/10: Saved duplicate_table_names.csv")

    # 7. Column name frequency
    column_freq = columns_df.groupby("column_name")["table_name"].agg(list).reset_index()
    column_freq["occurrences"] = column_freq["table_name"].apply(len)
    column_freq["tables"] = column_freq["table_name"].apply(lambda x: ", ".join(sorted(set(x))))
    column_freq.drop(columns=["table_name"], inplace=True)
    column_freq.sort_values(["occurrences", "column_name"], ascending=[False, True], inplace=True)
    write_csv(column_freq, "column_name_frequency.csv")
    print("   ✅ 7/10: Saved column_name_frequency.csv")

    # 8. Production features (1m horizon)
    production_features = columns_df[
        (columns_df["dataset_name"] == "models_v4") &
        (columns_df["table_name"] == "production_training_data_1m")
    ].copy()
    write_csv(production_features, "production_features_290.csv")
    print("   ✅ 8/10: Saved production_features_290.csv")

    # 9. Historical data sources
    historical_df = summarize_historical_tables(client)
    write_csv(historical_df, "historical_data_sources.csv")
    print("   ✅ 9/10: Saved historical_data_sources.csv")

    # 10. Models & training inventory
    models_inventory = inventory_df[inventory_df["dataset_name"].str.startswith("models")].copy()
    models_inventory = models_inventory.merge(column_counts, on=["dataset_name", "table_name"], how="left")
    write_csv(models_inventory, "models_training_inventory.csv")
    print("   ✅ 10/10: Saved models_training_inventory.csv")

    print("----------------------------------------------------------------------")
    print(f"✅ All inventory files generated in '{OUTPUT_DIR}'")
    print("----------------------------------------------------------------------")


if __name__ == "__main__":
    main()
