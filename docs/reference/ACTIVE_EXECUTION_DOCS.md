---
**Purpose:** Single index of the small set of execution-critical docs so humans and AI assistants don't have to hunt across folders.
**Canonical plan:** `docs/plans/MASTER_PLAN.md`
---

## Data & Ingestion
- `Quant Check Plan/PHASE2_DATA_PULL_PLAN.md` – Phase 2 complete data pull plan (Databento + FRED + supporting feeds).
- `Quant Check Plan/DATABENTO_DOCUMENTATION_REVIEW.md` – Databento GLBX.MDP3 documentation, coverage, pricing.
- `Quant Check Plan/DATABENTO_SYMBOL_FORMAT_REFERENCE.md` – Confirmed Databento symbology (`{ROOT}.FUT`, options formats).
- `Quant Check Plan/FX_DATA_SOURCE_CLARIFICATION.md` – FX source and feature calculations (FRED primary, Databento FX optional).
- `cbi_v14/api/databento/__init__.py` – Databento→BigQuery ingestion interface (wrapper around download_ALL_databento_historical).
- `cbi_v14/api/fred/__init__.py` – FRED→BigQuery ingestion interface (wrapper around FRED collectors).
- `COMPLETE_BIGQUERY_DATASET_TABLE_BREAKDOWN_20251124.md` – Canonical BigQuery dataset/table/column schemas.
- `bigquery-sql/build_weather_history.sql` – Weather and storm-event feature builder (`weather_segmented`, `weather_daily_region`, `storm_events_daily`).
- `Quant Check Plan/PHASE1_DATA_DOMAINS_TIPS_AND_GAPS.md` – Phase 1 weather/FX/vol domains, simplified feature sets and SQL examples.

## Modeling & Training
- `docs/plans/TRAINING_PLAN.md` – High-level training strategy and phases.
- `docs/plans/ZL_PRODUCTION_SPEC.md` – Locked production specification for the ZL baseline engine (targets, features, splits, metrics).
- `Quant Check Plan/ZL_EXECUTION_PLAN.md` – ZL modeling and execution details.
- `Quant Check Plan/MES_MASTER_PLAN.md` – MES modeling and execution details.
- `Quant Check Plan/BQ_SETUP_AND_BASELINE_TRAINING_PLAN.md` – Initial BigQuery + baseline training setup (older; superseded for day-to-day by EXECUTION_START_20251124.md but useful as a regime/calendar SQL reference).
- `cbi_v14/backtest/specs.py` – Dataclasses for DatasetSpec/ModelSpec/BacktestRun used to log training/backtest runs.
- `cbi_v14/markets/zl.py` – Canonical ZL engine configuration (roots, supporting symbols, horizon day counts).

## Sentiment & Buckets
- `Quant Check Plan/NEWS_BUCKET_TAXONOMY.md` – News/sentiment bucket taxonomy.
- `cbi_v14/api/scrapecreators/README.md` – ScrapeCreators ingestion interface and bucket→BigQuery mapping.
- `scripts/scrapecreators/buckets/biofuel_policy.py` – Biofuel policy news collector.
- `scripts/scrapecreators/buckets/china_demand.py` – China demand news collector.
- `scripts/scrapecreators/buckets/tariffs_trade_policy.py` – Tariffs/trade policy news collector.
- `scripts/scrapecreators/buckets/base_bucket.py` – Base ScrapeCreators bucket collector (shared logic for all buckets).
- `scripts/scrapers/comprehensive_social_scraper.sh` – Bulk ScrapeCreators social/news scraper (manual deep-dive tool; not part of the core daily pipeline).

## System Status & Audits (Reference)
- `MACHINE_STATUS_REPORT_20251124.md` – Verified M4 Pro 24GB machine specs and implications for training capacity.
- `Quant Check Plan/CORRECTED_DATA_ARCHITECTURE_20251124.md` – Summary of corrected BigQuery + Mac architecture after v2 removal.
- `Quant Check Plan/BQ_BASELINE_EXECUTION_PLAN_20251124.md` – Baseline BigQuery execution plan for initial training tables (reference; superseded by EXECUTION_START_20251124.md for day-to-day).
- `DATAFORM_STRUCTURE_REVISED_20251124.md` – Revised Dataform structure and dataset wiring (reference for Dataform, not primary execution path).
- `AUDIT_REPORT_V2_REMOVAL_20251124.md` – Vertex/v2 removal audit; explains why v2 tables are gone and how the clean schema was established.
- `Quant Check Plan/PLAN_CONSOLIDATION_SUMMARY.md` – How the legacy plans were consolidated into ZL_EXECUTION_PLAN, MES_MASTER_PLAN, and PHASE2_DATA_PULL_PLAN.
- `INSTALLATION_SUMMARY_20251124.md` – Final package install summary and known issues (e.g., tensorflow-metal GPU bug) on the current Mac.

## Rules & System
- `docs/reference/CURSOR_MASTER_INSTRUCTION_SET.md` – Master rules for AI assistants (no fake data, us-central1 only, etc.).
- `docs/reference/BEST_PRACTICES_DRAFT.md` – Best practices for working in this repo.
- `UPDATED_COLLECTION_SCHEDULE.md` – Live ingestion schedule (cron-style).

> When in doubt, start with `MASTER_PLAN.md` and this file; treat other docs as supporting material only.
