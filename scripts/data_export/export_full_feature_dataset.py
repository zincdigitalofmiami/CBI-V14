#!/usr/bin/env python3
"""Export the wide BigQuery feature table for local training."""

import argparse
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

DEFAULT_TABLE = "models_v4.full_220_comprehensive_2yr"
DEFAULT_OUTPUT = "TrainingData/exports/full_220_comprehensive_2yr.parquet"


def main():
    parser = argparse.ArgumentParser(description="Export full feature table from BigQuery to Parquet.")
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help=f"BigQuery table to export (default: {DEFAULT_TABLE})"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Local Parquet output path (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--project",
        default="cbi-v14",
        help="BigQuery project ID (default: cbi-v14)"
    )
    args = parser.parse_args()

    client = bigquery.Client(project=args.project)
    table_id = f"{args.project}.{args.table}" if args.project not in args.table else args.table

    print(f"📥 Exporting {table_id} ...")
    query = f"SELECT * FROM `{table_id}`"
    df = client.query(query).to_dataframe()
    print(f"   Rows: {len(df):,}  Columns: {len(df.columns):,}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"✅ Saved to {output_path.resolve()}")


if __name__ == "__main__":
    main()
