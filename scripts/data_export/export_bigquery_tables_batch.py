#!/usr/bin/env python3
"""Batch-export BigQuery tables to local Parquet files for local training/archive."""

import argparse
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

DEFAULT_MANIFEST = "GPT_Data/inventory_340_objects.csv"
DEFAULT_RAW_DIR = "TrainingData/raw"
DEFAULT_REPO_COPY_DIR = "GPT_Data/raw_exports"


def load_manifest(manifest_path: Path, dataset_filter: str | None) -> pd.DataFrame:
    df = pd.read_csv(manifest_path)
    if dataset_filter:
        df = df[df["dataset_name"] == dataset_filter]
    # Include all tables/views, even if row_count is NaN (views don't have row_count)
    return df


def export_table(client: bigquery.Client, project: str, dataset: str, table: str, table_type: str, raw_dir: Path, repo_dir: Path | None):
    table_id = f"{project}.{dataset}.{table}"
    print(f"📥 Exporting {table_id} ({table_type})...")
    try:
        query = f"SELECT * FROM `{table_id}`"
        df = client.query(query).to_dataframe()
        print(f"   Rows: {len(df):,}  Columns: {len(df.columns):,}")

        target_dir = raw_dir / dataset
        target_dir.mkdir(parents=True, exist_ok=True)
        raw_path = target_dir / f"{table}.parquet"
        df.to_parquet(raw_path, index=False)
        print(f"   ✅ Saved raw copy to {raw_path}")

        if repo_dir:
            repo_dir.mkdir(parents=True, exist_ok=True)
            repo_path = repo_dir / f"{dataset}.{table}.parquet"
            df.to_parquet(repo_path, index=False)
            print(f"   ✅ Saved repo copy to {repo_path}")
    except Exception as e:
        print(f"   ❌ ERROR exporting {table_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Batch export BigQuery tables to Parquet.")
    parser.add_argument("--project", default="cbi-v14", help="BigQuery project ID")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="CSV manifest (inventory) path")
    parser.add_argument("--dataset", default=None, help="Dataset name to filter (default: ALL datasets)")
    parser.add_argument("--raw-dir", default=DEFAULT_RAW_DIR, help="Local raw directory (default TrainingData/raw)")
    parser.add_argument("--repo-copy", default=DEFAULT_REPO_COPY_DIR, help="Repo copy directory (set empty string to skip)")

    args = parser.parse_args()

    client = bigquery.Client(project=args.project)

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    raw_dir = Path(args.raw_dir)
    repo_dir = Path(args.repo_copy) if args.repo_copy else None

    df = load_manifest(manifest_path, args.dataset)
    if args.dataset:
        print(f"Found {len(df)} objects to export from dataset '{args.dataset}'")
    else:
        print(f"Found {len(df)} objects to export from ALL datasets")
        print(f"Datasets: {df['dataset_name'].nunique()}")

    for _, row in df.iterrows():
        export_table(client, args.project, row["dataset_name"], row["table_name"], row.get("table_type", "UNKNOWN"), raw_dir, repo_dir)

    print("\nAll exports complete.")


if __name__ == "__main__":
    main()
