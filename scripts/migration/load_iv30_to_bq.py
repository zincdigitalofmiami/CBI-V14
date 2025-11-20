#!/usr/bin/env python3
"""
Load IV30 daily outputs into BigQuery (features.iv30_daily)
==========================================================

Reads IV30 parquet(s) and upserts into features.iv30_daily with (date, symbol) key.

Search order for inputs:
- TrainingData/features/iv30_daily.parquet
- TrainingData/features/iv30_*.parquet (glob)
- /Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/features/iv30_*.parquet (fallback)

Idempotent: loads into temp table then MERGEs into target.
"""

import os
import sys
import glob
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from google.cloud import bigquery

# Project utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.gcp_utils import get_gcp_project_id  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_parquet_inputs() -> list:
    candidates = []
    local_main = Path("TrainingData/features/iv30_daily.parquet")
    if local_main.exists():
        candidates.append(str(local_main))

    local_glob = glob.glob("TrainingData/features/iv30_*.parquet")
    candidates.extend(local_glob)

    external_glob = glob.glob("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/features/iv30_*.parquet")
    candidates.extend(external_glob)

    # Deduplicate preserving order
    seen = set()
    uniq = []
    for p in candidates:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Expected columns
    cols = {
        "date": "date",
        "symbol": "symbol",
        "iv30": "iv30",
        "obs_count": "obs_count",
        "moneyness_span": "moneyness_span",
        "quality_flag": "quality_flag",
        "asof_source_time": "asof_source_time",
    }
    # Basic renames (tolerate slight variants)
    for c in list(df.columns):
        lc = c.lower().strip()
        if lc in cols and c != cols[lc]:
            df.rename(columns={c: cols[lc]}, inplace=True)

    # Subset to known columns, add missing
    out = pd.DataFrame()
    for c in cols.values():
        if c in df.columns:
            out[c] = df[c]
        else:
            out[c] = pd.Series([None] * len(df))

    # Types
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out["symbol"] = out["symbol"].astype(str).str.upper()
    out["iv30"] = pd.to_numeric(out["iv30"], errors="coerce")
    out["obs_count"] = pd.to_numeric(out["obs_count"], errors="coerce").fillna(0).astype("Int64")
    out["moneyness_span"] = pd.to_numeric(out["moneyness_span"], errors="coerce")
    out["quality_flag"] = out["quality_flag"].astype(str)
    out["asof_source_time"] = pd.to_datetime(out["asof_source_time"], errors="coerce")
    out["as_of"] = pd.Timestamp.utcnow()

    # Drop rows missing essential keys
    out = out.dropna(subset=["date", "symbol"]).copy()
    return out


def load_to_bq(df: pd.DataFrame, project_id: str):
    client = bigquery.Client(project=project_id)
    target = f"{project_id}.features.iv30_daily"
    tmp = f"{project_id}.features._iv30_daily_load_tmp"

    # Create temp table (auto schema from DF)
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    logger.info(f"Loading {len(df)} rows into {tmp}...")
    client.load_table_from_dataframe(df, tmp, job_config=job_config).result()

    # MERGE into target
    merge_sql = f"""
    CREATE TABLE IF NOT EXISTS `{target}` (
      date DATE,
      symbol STRING,
      iv30 FLOAT64,
      obs_count INT64,
      moneyness_span FLOAT64,
      quality_flag STRING,
      asof_source_time TIMESTAMP,
      as_of TIMESTAMP
    ) PARTITION BY date CLUSTER BY date, symbol;

    MERGE `{target}` T
    USING `{tmp}` S
    ON T.date = S.date AND T.symbol = S.symbol
    WHEN MATCHED THEN UPDATE SET
      iv30 = S.iv30,
      obs_count = S.obs_count,
      moneyness_span = S.moneyness_span,
      quality_flag = S.quality_flag,
      asof_source_time = S.asof_source_time,
      as_of = S.as_of
    WHEN NOT MATCHED THEN INSERT ROW;

    DROP TABLE `{tmp}`;
    """
    logger.info("Merging temp into target features.iv30_daily...")
    client.query(merge_sql).result()
    logger.info("✅ IV30 upsert complete.")


def main():
    project_id = get_gcp_project_id()
    inputs = find_parquet_inputs()
    if not inputs:
        logger.error("No IV30 parquet inputs found.")
        sys.exit(1)

    frames = []
    for p in inputs:
        try:
            df = pd.read_parquet(p)
            if len(df) == 0:
                continue
            frames.append(normalize_df(df))
            logger.info(f"Loaded {len(df)} rows from {p}")
        except Exception as e:
            logger.warning(f"Skipping {p}: {e}")

    if not frames:
        logger.error("No valid IV30 dataframes loaded.")
        sys.exit(2)

    df_all = pd.concat(frames, ignore_index=True)
    if df_all.empty:
        logger.error("Aggregated IV30 dataframe is empty.")
        sys.exit(3)

    # Deduplicate by (date, symbol)
    df_all.sort_values(["date", "symbol", "asof_source_time"], inplace=True)
    df_all = df_all.drop_duplicates(subset=["date", "symbol"], keep="last")

    load_to_bq(df_all, project_id)


if __name__ == "__main__":
    main()

