# Warehouse Governance & Naming (CBI-V14)

_Last updated: 2025-10-10_

## Medallion Datasets
- `raw` — append-only ingestion landing (no transformations, partitioned by event date).
- `staging` — normalized & unit-fixed tables, feature pivots (prefixed `ftr_`).
- `curated` — dashboard-ready views (prefixed `vw_`).
- `models` — featuresets, predictions, monitoring tables (`ml_*`, `model_*`).
- `bkp` — point-in-time backups prior to destructive operations.
- `deprecated` — quarantined legacy assets pending deletion.
- `forecasting_data_warehouse` — legacy dataset; transitioning to layered namespaces via façade views.

## Object Naming
- **Tables:** snake_case (`soybean_oil_prices`). No prefixes except `ftr_` in staging.
- **Views:** `vw_[domain]_[purpose]_[granularity]` (e.g., `vw_economic_daily`).
- **Models:** `ml_[target]_[horizon]_[algo]_v#`.
- **Featuresets:** `ftr_[domain]_[granularity]` stored in `staging`.
- **Columns (ingestion):** include `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`, and appropriate time key (`time` or `date`).

## Schema Evolution
1. Light optimizations in staging (per Google migration guidance).
2. Introduce façade views in curated dataset pointing to legacy tables.
3. Migrate upstream/downstream objects sequentially; deprecate legacy views only after validation.

## Data Freshness SLOs
- ZL/ZS/ZM, FX: ≤ 15 minutes.
- Macro (VIX, DXY, Fed, 10Y): ≤ same day.
- Weather cropsheds: ≤ 24 hours.
- USDA export sales, CFTC COT: next business day from release.

## Governance Notes
- No mock or placeholder data permitted in production namespaces.
- All scripts must respect credit budgets for external APIs (ScrapeCreators, etc.).
- Document each pipeline run and backfill in `/logs` with timestamped filename.
