# Training Dataset Location - ALWAYS READ THIS FIRST

## PRIMARY TRAINING DATASET

**MAIN TABLE:** `cbi-v14.models_v4.training_dataset_super_enriched`

This is the **ONLY** authoritative training dataset. All other training datasets have been archived.

## Quick Access

### BigQuery Console
```
https://console.cloud.google.com/bigquery?project=cbi-v14&ws=!1m5!1m4!4m3!1scbi-v14!2smodels_v4!3straining_dataset_super_enriched
```

### SQL Query
```sql
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
ORDER BY date DESC
LIMIT 100
```

## Training Views (Horizon-Specific)

These views automatically filter the main dataset for specific prediction horizons:

- **1-Week:** `cbi-v14.models_v4.train_1w`
- **1-Month:** `cbi-v14.models_v4.train_1m`
- **3-Month:** `cbi-v14.models_v4.train_3m`
- **6-Month:** `cbi-v14.models_v4.train_6m`

## Dataset Structure

- **Location:** `cbi-v14` project, `models_v4` dataset
- **Type:** Table (not a view)
- **Features:** 210 columns
- **Rows:** ~1,840 dates
- **Date Range:** 2020-10-21 to present

## Related Files

- **Create views:** `bigquery_sql/create_horizon_training_views.sql`
- **Training SQL:** `bigquery_sql/train_bqml_[1w|1m|3m|6m]_mean.sql`
- **Extend dataset:** `scripts/extend_training_dataset.py`
- **Backfill:** `bigquery_sql/backfill_from_scraped_data.sql`

## DO NOT USE (Archived)

The following datasets have been archived and should NOT be used:
- Any dataset with "legacy", "old", "backup", "temp" in the name
- Any dataset in the `archive` BigQuery dataset

## Last Updated

2025-11-03



