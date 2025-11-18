# BigQuery Mirror for Live Futures (Optional)

This adds a mirror of live 1-minute OHLCV bars into BigQuery for analytics and dashboards, while keeping live endpoints serverless/local.

## Overview
- Live source: DataBento GLBX.MDP3 (`ohlcv-1m`)
- Local sink: Parquet under `TrainingData/live/{root}/1m/date=YYYY-MM-DD/part-*.parquet`
- Mirror: Upload new Parquet parts to GCS, then load into a partitioned BQ table
- Rollups: Scheduled Queries produce 1h/1d tables

## Prerequisites
- Google Cloud project (e.g., `cbi-v14`)
- GCS bucket (e.g., `gs://cbi-live-parquet/`)
- Service account with permissions:
  - Storage Object Admin on the bucket
  - BigQuery Data Editor on the dataset (e.g., `market_data`)
- Application Default Credentials (ADC) configured on the host running the poller:
  - `gcloud auth application-default login` OR set `GOOGLE_APPLICATION_CREDENTIALS`

## Create Tables
Apply the DDL:
```
bq query --use_legacy_sql=false < scripts/sql/bq_live_tables.sql
```

This creates:
- `market_data.futures_ohlcv_1m_live` partitioned by `DATE(ts_event)` and clustered by `root,symbol`
- `market_data.futures_ohlcv_1h_live` and `market_data.futures_ohlcv_1d_live` rollups

## Run Poller with Mirror Enabled
```
python3 scripts/live/databento_live_poller.py \
  --roots ES,ZL,CL \
  --interval 60 \
  --mirror-bq \
  --gcs-bucket cbi-live-parquet \
  --gcs-prefix market_data/futures_ohlcv_1m_live \
  --bq-project cbi-v14 \
  --bq-dataset market_data
```
Notes:
- The poller uploads only new Parquet parts (tracked in `gcs_mirror_state.json`) and loads them with BQ load jobs (`WRITE_APPEND`, `PARQUET`, `autodetect`).
- Spread rows are already filtered out before writing.

## Scheduled Queries (Recommended)
Create BQ scheduled queries (every 5–10 minutes) to refresh:
- `market_data.futures_ohlcv_1h_live`
- `market_data.futures_ohlcv_1d_live`

Use the SQL in `scripts/sql/bq_live_tables.sql` as the body of `CREATE OR REPLACE TABLE` statements in scheduled queries.

## Cost & Quality Notes
- Load jobs are cheaper and more stable than streaming inserts.
- Partition pruning reduces scan costs.
- Apply tick-size / outlier guards in the poller before upload; see `registry/universe/tick_sizes.yaml`.

## Troubleshooting
- If uploads or loads fail, verify ADC and permissions.
- Ensure the Parquet files include the timestamp index; the poller writes the index by default.
- Confirm `DATABENTO_API_KEY` for live pulls.

