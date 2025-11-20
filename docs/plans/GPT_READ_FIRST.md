# GPT/AI Assistant: Read This First

## Primary Documentation
- **Source of Truth**: `docs/plans/MASTER_PLAN.md`
- **Training Strategy**: `docs/plans/TRAINING_PLAN.md`
- **Table Mapping**: `docs/plans/TABLE_MAPPING_MATRIX.md`
- **BigQuery Migration**: `docs/plans/BIGQUERY_MIGRATION_PLAN.md`
- **⚠️ Cost Lessons**: `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - AI created ~$250/month mistake during migration

## Current Architecture (November 2025)
- **Training**: Local M4 Mac only (NOT Vertex AI, NOT BQML)
- **Data**: DataBento primary (2010-present), Yahoo bridge (ZL 2000-2010)
- **Storage**: External drive + BigQuery
- **Deployment**: Mac inference → BigQuery predictions

## Critical Rules
1. **IGNORE** everything in `archive/` and `legacy/` directories
2. **NO** BQML training, AutoML, or cloud-based training
3. **USE** DataBento for all futures (GLBX.MDP3 dataset)
4. **PREFIX** all columns with source (e.g., `databento_`, `yahoo_`, `fred_`)
5. **⚠️ CRITICAL: us-central1 ONLY** - Never create resources in US multi-region or other regions
6. **⚠️ CRITICAL: NO COSTLY RESOURCES WITHOUT APPROVAL** - Do NOT create Cloud SQL, Cloud Workstations, Compute Engine, Vertex AI endpoints, or any paid resources without explicit user approval. See `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` for why (AI created ~$250/month mistake).

## Data Status
- ✅ MES data available (1m, 1h, daily) 2019-2025
- ✅ ZL data available (1h, daily) 2010-2025
- ❌ ZL 1-minute data MISSING (batch jobs running)
- ✅ Yahoo ZL bridge data 2000-2010

## Current Work
Downloading complete historical DataBento universe:
- 26 symbols total
- ~45 download jobs
- 8-10 GB estimated
- Script: `scripts/ingest/download_ALL_databento_historical.py`

## Known Issues Fixed
ZL 1-minute download failures were due to:
1. Wrong API call: `client.timeseries.submit_job` → `client.batch.submit_job`
2. Invalid parameter: `packaging="zip"` (removed)
3. Wrong split duration: `"1M"` or `"1d"` → `"month"` or `"day"`
4. Wrong symbology: `"ZL"` with `stype_in="continuous"` → `"ZL.FUT"` with `stype_in="parent"`

These have been corrected in all download scripts.
