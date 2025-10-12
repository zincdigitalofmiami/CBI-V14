# CBI-V14 Production Execution Plan (2025-10-10)

## Phase 0 — Readiness & Audit (✅ Complete)
- Exported current schemas for key tables to `archive/audits/2025-10-10`.
- Archived existing forensic audit docs.
- Confirmed GCP IAM/project context.

## Phase 1 — Governance & Directory Cleanup (✅ Complete)
- Created BigQuery datasets: `raw`, `staging`, `curated`, `models`, `bkp`, `deprecated`.
- Documented naming/SLO conventions in `docs/governance/warehouse_governance.md`.
- Reorganized root docs under `docs/` (plans, operations, research, rules).
- Removed obsolete `cbi-v1-ingestion/` and other duplicates.

## Phase 2 — Curated Façade Views & Naming Alignment (✅ Complete)
- Created curated views: `vw_economic_daily`, `vw_weather_daily`, `vw_volatility_daily`, `vw_zl_features_daily`, `vw_social_intelligence`.
- Stored view SQL under `bigquery_sql/curated_facade/`.
- Validated data outputs and dropped misnamed `fct_*` and legacy warehouse views.

## Phase 3 — Data Integrity Audit (In Progress)
- Placeholder audit reports saved to `archive/audits/2025-10-10/placeholder_checks/`.
- Backed up `volatility_data`, `news_intelligence`, and `soybean_oil_prices` to `bkp`.
- Identified issues:
  - `volatility_data`: missing metadata rows → requires reload.
  - `news_intelligence`: 43 rows missing metadata → investigate/remove.
  - `soybean_oil_prices` parity check: confirm TradingEconomics ingest (primary) with Polygon fallback; stop Yahoo references.
  - `economic_indicators`: legacy logic flagged for rebuild (FRED + TradingEconomics + EPA/EIA inputs).

## Current State Snapshot — 2025-10-12
- **Commodity price tables** (`forecasting_data_warehouse`): ZL/ZS/ZM/ZC/CT all 524–525 rows (2023-09-12→2025-10-10) but still unpartitioned; `cocoa_prices` 446 rows (2024-01-03→2025-10-10); `treasury_prices` only 136 rows (2025-03-21→2025-10-03). Canonical metadata columns present.
- **Volatility & news**: `volatility_data` 780 rows (2025-10-03→2025-10-10) confirming freshness gap; `news_intelligence` 633 rows (2025-10-04→2025-10-12) with full articles + metadata; `social_sentiment` legacy Reddit only 22 rows (Oct 6–8).
- **Staging separation**: `staging.trump_policy_intelligence` 186 rows (2025-04-03→2025-10-06) healthy; `staging.ice_enforcement_intelligence` 4 rows (2025-10-06) newly split; `staging.market_prices` partitioned on `date` but awaiting validated loads.
- **Curated/models layer**: façade views live for economics, weather, volatility, soybean oil features/quote, and social intelligence (still Reddit until ScrapeCreators migration). Models dataset holds `vw_master_feature_set_v1`, `zl_price_training_base`, `zl_forecast_baseline_v1`, `zl_forecast_arima_plus_v1`, `zl_timesfm_training_v1` — schemas clean, need validation sweep.
- **Immediate audit follow-ups**: run project-level `INFORMATION_SCHEMA` inventory once regional syntax sorted; enforce partitioning on commodity tables; validate weather loaders + `market_prices` refresh after TradingEconomics/Polygon ingest; re-audit social/ICE pipelines post-ScrapeCreators migration.

## Phase 4 — Market Data Rebuild (Pending)
- Draft ingestion spec: TradingEconomics (primary) + Polygon (fallback), ≥5 min spacing between calls, 4 hr steady-state refresh window.
- Back up and replace price tables (`soybean_oil_prices`, `soybean_prices`, `soybean_meal_prices`, `corn_prices`, `cotton_prices`, FX tables).
- Version new ingestion code (connection config, API retries, lineage logging).
- Load clean data and validate against CME/Reuters before swap.

## Phase 5 — Volatility Suite Rebuild (Pending)
- Back up `volatility_data` and remove placeholder rows.
- Ingest:
  - VIX (CBOE API + FRED fallback) → `vw_vix_daily`.
  - Soybean CVOL (CME) → `vw_cvol_soybean_daily`.
  - Realized volatility (price-derived) → `vw_zl_realized_volatility_daily`.
- Align metadata and scoring across volatility views.

## Phase 6 — Fundamentals & Demand Drivers (Pending)
- Stand up ingestion for:
  - USDA/FAS export sales (China purchases).
  - CONAB/ABIOVE/BCR crop updates.
  - EPA RFS/EIA biodiesel data.
  - TradingEconomics macro series.
- Create staging tables with canonical metadata and expose curated views.

### Weather & Biofuel Data Collection Priorities
- **Variables to capture in every agronomic feed:** precipitation (mm), temperature max (°C), temperature min (°C), soil moisture (where source supports it), calculated growing degree days.
- **Regional timing windows:** Brazil (Oct–Mar planting/growing), Argentina (Nov–Apr summer season), US Midwest (May–Sep planting through harvest).
- **Update cadence targets:** Brazil INMET daily load by 07:00 local; NOAA (US + Argentina GHCND/GFS) refreshed by 06:00 local; enforce freshness SLO ≤24 h.
- **Coverage expansion:** add Paraguay (emerging soybean producer), Ukraine (sunflower competitor), Canada Prairies (canola) to weather ingest manifest.
- **Supplemental weather sources:** evaluate ECMWF ERA5 reanalysis, NOAA GFS forecast grids, NASA POWER satellite data for resilience and backfill.
- **Shipping chokepoint monitoring:** integrate Panama Canal water levels, Santos (BR) port throughput, Rosario (AR) river stage/export stats, US Gulf port status into fundamentals layer.

#### Strategic Weather Intelligence Framework (Working Plan)
- **Executive synthesis:** convert Brazil/Argentina/US Midwest meteorology into region-weighted signals explaining 35–45 % of ZL variance; Brazil ingestion and rollups are the gating item.
- **Current gaps:** finish Brazil INMET daily pipeline + two-year backfill, publish daily composites for BR/AR/US, add freshness/coverage monitors, and surface dashboard tiles + weekly executive rollups.
- **Station manifest:**
  - *Brazil* (85.8 % production) — Mato Grosso (A901, A923, A936, A908), Paraná (A807, A835), Rio Grande do Sul (A801, A833), Goiás (A012, A063), Mato Grosso do Sul (A702, A736).
  - *Argentina* — Buenos Aires Aero (AR000875760), Rosario Aero (AR000875850), plus Córdoba/Santa Fe/Entre Ríos coverage.
  - *US Midwest* — Iowa (USW00014933 + support), Illinois (USW00094846 + core), and flagship stations across IN/MN/NE/OH/SD/KS.
- **Data model:** raw canonical table (`forecasting_data_warehouse.weather_data` or endpoint) with station metadata and canonical columns; regional composites (`vw_weather_daily_brazil`, `vw_weather_daily_argentina`, `vw_weather_daily_us_midwest`), plus a master `vw_weather_features_daily` aligned to market calendar with rolling means/anomalies.
- **Weighting:** intra-region station weights, inter-region production weights, composite outputs (precip/tavg/humidity, 7/14/30-day rolls, z-scores, critical-window flags).
- **Backfill & QA:** 24‑month backfill in monthly chunks, dedupe on date+station, quarantine implausible values, coverage goals ≥90 % (Brazil/US) and ≥85 % (Argentina).
- **Monitoring SLOs:** raw <48 h, composites <24 h, feature view <24 h, dropout alerts after 3 missed days, composite continuity checks for trading days.
- **Dashboard/reporting:** tiles for Brazil precip & temp anomalies, Rosario corridor status, US GDD vs normal; analyst heatmaps, weather-vs-ZL correlations, regime detector; weekly auto-report with regional highlights and correlation deltas.
- **Model integration:** enrich `vw_weather_features_daily` with lagged composites prior to retraining short-horizon models; clip/winsorize extremes.
- **Enhancement roadmap:** add Paraguay, Ukraine, Canada Prairies weather, shipping chokepoint metrics, seasonal-normal anomalies, and integrate into scenario engine.
- **Execution checklist (immediate):** (1) enable Brazil ingestion daily & run 24‑month backfill, (2) publish Brazil composite view + coverage report, (3) render 14-day window tile, (4) stand up Argentina/US composites, (5) wire monitoring, (6) add anomalies vs normals, (7) integrate into feature view + retrain, (8) ship weekly executive email with weather/ZL deltas.
- **Acceptance criteria:** Brazil composite coverage ≥90 % over trailing 24 months, <24 h freshness for 10 consecutive trading days, feature view populated ≥500 trading days, dashboard tiles stable, measurable correlation uplift in backtests.

## Phase 7 — Social Intelligence Migration (In Progress)
- Build `staging.social_intel_events` with ScrapeCreators payloads.
- Split Trump vs ICE pipelines: `staging.trump_policy_intelligence` & `staging.ice_enforcement_intelligence` live.
- Backfill 100 posts per social source (Facebook + LinkedIn) and reroute view to staging table.
- Integrate neural scoring and confidence metrics before BigQuery load.

## Phase 8 — Pipeline Freshness & Monitoring (Pending)
- Update CI to enforce dataset naming and metadata requirements.
- Implement nightly placeholder audit + upstream spot checks.
- Log freshness metrics to `models.pipeline_freshness_log`.
- Document pipeline SLOs and dependencies.

## Phase 9 — Final Cleanup & Documentation (Pending)
- Drop deprecated tables/views after confirmations.
- Publish updated warehouse map and ingestion runbooks.
- Summarize credit usage, freshness status, and open data gaps.
