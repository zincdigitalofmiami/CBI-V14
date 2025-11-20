---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

**📋 BEST PRACTICES:** See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices including: no fake data, always check before creating, always audit after work, us-central1 only, no costly resources without approval, research best practices, research quant finance modeling.

# BigQuery‑Centric Architecture Migration Plan
Date: November 18, 2025
Status: Adopted

## Overview
- Data plane (GCP): Ingest to BigQuery, transform via Scheduled Queries/Dataform, curate training/serving surfaces, and host views for the dashboard.
- Model plane (Mac M4): Pull Parquet bundles from GCS, train/score locally, push predictions/diagnostics back to BigQuery.
- UI plane (Vercel): Read‑only against BigQuery views; no direct access to external APIs or private datasets.

## Data Authority Policy
- Futures OHLCV (intraday + daily): DataBento is authoritative (2010→present). Yahoo ZL retained only as pre‑2010 bridge. Deprecate Alpha/Vendor bars where DataBento exists.
- Macro/risk: FRED is canonical (rates, VIXCLS, credit). Discontinued: CME CVOL indices (SOVL/SVL) — not used.
- TA: Compute indicators in‑house off stored prices (retire Yahoo/Alpha TA endpoints).

## Latency & Cost
- Ingest cadence: 5‑minute batches for futures to BigQuery (load jobs). Daily/weekly/monthly for macro/agencies.
- Dashboard: Poll BigQuery every 5 minutes (partition‑pruned queries). Streaming inserts are optional, not required.

## Handoff Contracts
- BQ→GCS: Parquet bundles + manifest (dataset_version, feature_hash, window, row_counts).
- Mac pulls bundles, trains/scores, then writes predictions + diagnostics to GCS with return‑manifest.
- Cloud Run ingestor loads results into BigQuery (`predictions.*`, `performance.*`, `explainability.*`).

## Separation (MES private, ZL public)
- Isolate MES data/models in private datasets (or separate project). Dashboard SA has no IAM to these.
- Public views expose only ZL and allowed context symbols.

## Symbol Adds & Derived Features
- Adds: ZC, ZW, 6L, CU (plus retain CL/HO/RB; NQ/MNQ, RTY/M2K for routers). Ingest daily (and intraday where noted).
  (Removed) CME CVOL indices (SOVL/SVL) — not collected.
- Derived: calendar spreads (front–second), BOHO spread (HO − ZL×factor), soy crush margin (ZS/ZM/ZL).

## Phased Rollout
1) Stand up ingestion (DataBento → GCS → BQ raw; agencies → BQ raw).
2) Curate in BQ (PIT‑correct features/training tables; scheduled queries/Dataform).
3) Handoff (BQ→GCS Parquet + manifest; Mac pulls; return to BQ).
4) Serving (BQ overlays; Vercel reads views).
5) Decommission legacy (Alpha/Vendor bars, external TA calls).

## Security/IAM
- Least‑privilege service accounts; dashboard SA read‑only to public datasets; Mac uses scoped SA for GCS/BQ.
- Keys via macOS Keychain and Vercel secrets; no client‑side secrets.

## Next Steps
- Add DataBento roots (ZC/ZW/6L/CU; NQ/MNQ/RTY/M2K intraday).
- Implement derived spreads in BQ; do not provision CME CVOL tables.
- Update feature builders; remove Alpha/Vendor duplicates post‑stitch.
- Enable 5‑minute BQ exports + Mac pull agent; wire return ingestor; update dashboard to BQ views.

## Optional GCP Services
- **Datastream (optional)** – Datastream API is available for project `cbi-v14`; metrics console: `https://console.cloud.google.com/apis/api/datastream.googleapis.com/metrics?project=cbi-v14&authuser=2`. Keep this in mind if we decide to use managed stream ingestion into BigQuery instead of custom loaders.
- **Earth Engine API (optional)** – Earth Engine API library is available/to-be-enabled for project `cbi-v14`; API library console: `https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project=cbi-v14&authuser=2`. We still need to enable and verify access, but this could be useful for geospatial/environmental features feeding BigQuery.
- **Data Catalog API (optional)** – Data Catalog can help organize BigQuery datasets/tables with centralized metadata, tags, and search/lineage. Library console: `https://console.cloud.google.com/apis/library/datacatalog.googleapis.com?project=cbi-v14&authuser=2`. Worth enabling later if we formalize dataset labeling and governance.
