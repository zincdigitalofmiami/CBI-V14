CBI-V14 Unified Plan
====================

ZL / MES Forecasting • FX & Correlation Engine • Dataform • Mac Modeling • Cloud Ingestion • ScrapeCreators • Vegas Intel

Status: DESIGN – ready for incremental implementation  
Canonical Reference: QUAD-CHECK Plan (2025-11-21)

0. Purpose
----------

This document unifies:

- The denormalized BigQuery architecture approved in QUAD-CHECK (especially `features.daily_ml_matrix`)
- The Mac-first modeling strategy (all heavy math and training done locally)
- The Dataform transformation layer for BigQuery
- The Cloud Run ingestion and forecast APIs
- The ScrapeCreators “regime sensor” design
- The expanded data source set (Databento, FRED, NOAA, GDELT, Global Fishing Watch, Google Trends, etc.)
- The ZL and MES modeling families
- The Vegas Intel page for sales support (Kevin’s view)

The goal: a shippable V14 that does not collapse under schema fragility or BigQuery complexity, but still respects the QUAD-CHECK architecture and long-term vision.

1. Global Architecture
----------------------

### 1.1 High-Level Components

**Data Sources**

- Databento (CME/CBOT/NYMEX/COMEX futures, FX, options)
- FRED (macro series + VIXCLS)
- NOAA (GHCN, GSOD, ICOADS – weather & marine)
- GDELT (events + global knowledge graph)
- Global Fishing Watch (AIS-based maritime effort)
- Google Trends (demand / tourism interest)
- CFTC (commitment of traders)
- ScrapeCreators (policy, tariffs, logistics, weather, macro commentary)
- Vegas event feeds (LVCVA / venue APIs) – Phase 2 integration

**Ingestion Layer (Cloud Run + Cloud Scheduler)**

- Small Python/Go services that pull, normalize, and write to `raw_v2.*` tables
- Scheduler triggers ingestion on hourly/daily/weekly schedules  
dev.to

**Transformation Layer (Dataform + BigQuery)**

- Dataform orchestrates transformations from `raw_v2.*` → `staging_v2.*` → `features_v2.*`
- Produces the denormalized `features.daily_ml_matrix` with nested STRUCTs as per QUAD-CHECK

**Modeling Layer (Mac)**

- Mac pulls `features.daily_ml_matrix` (and small aux tables)
- Calculates advanced features (FX, correlations, vol, VRP, spreads, crush, weather–vol, regime scores)
- Builds and trains ZL / MES models
- Writes forecast tables back to BigQuery: `forecasts.*`

**Serving Layer (Cloud Run Forecast API + Vercel UI)**

- Cloud Run exposes `GET /forecasts/*` endpoints
- Vercel hosts the ZL, MES, and Vegas Intel front-end
- UI follows QUAD-CHECK UX & legal rules (probability language, SHAP, disclaimers)

2. Data Sources & Symbol Set
----------------------------

### 2.1 Databento Symbol Universe

**Core commodity + related futures (minimum set):**

- ZL – Soybean Oil (target asset)
- ZS – Soybeans
- ZM – Soybean Meal
- ZC – Corn
- RS – Canola/Rapeseed
- FCPO – Palm Oil (if available via Databento or parallel feed)
- CL – Crude Oil
- HO – Heating Oil
- RB – Gasoline

**Macro / risk proxies:**

- ES – S&P 500 E-mini
- Rates curve – SOFR, 2Y/5Y/10Y note futures (macro regime context)

**FX futures / proxies:**

- USDBRL – BRL FX (direct or via futures synthetic)
- USDCNY – CNY FX
- USDX – Dollar index (ICE futures)
- Optional: USDCAD, EURUSD, etc. as needed

These symbols are ingested as daily OHLCV and, where needed, intraday bars for microstructure features (MES) and curve construction.

### 2.2 Public BigQuery Datasets (Free)

These serve as additional feature sources:

- NOAA GHCN Daily / GSOD  
  Regional weather anomalies for U.S. Midwest, Brazil, Argentina
- NOAA ICOADS  
  Marine/oceanic weather observations (shipping routes)
- GDELT v2  
  Event counts and tone for agriculture, biofuel, logistics, macro events  
  gdeltproject.org  
  gdeltproject.org
- Global Fishing Watch  
  Fishing effort as proxy for vessel density and maritime activity
- Google Trends  
  Terms related to:  
  - Cooking oil / restaurant demand  
  - Tourism (Vegas)  
  - Biofuel demand
- OpenAQ (optional)  
  Air quality, potential proxy for certain weather or policy shocks

### 2.3 ScrapeCreators “Regime Sensors”

ScrapeCreators jobs are intent-labeled scrapers. Each job feeds one regime family:

**Examples:**

- `trump_zl_signal`
- `tariffs_agriculture`
- `biofuel_legislation`
- `saf_mandates`
- `weather_midwest_drought`
- `weather_brazil_drought`
- `logistics_panama`
- `logistics_redsea`
- `fomc_commentary`
- `refinery_outage`
- `macro_recession_headlines`

Each job is configured to send its results tagged with a `source_slug` corresponding to one of these identifiers.

3. Ingestion Layer (Cloud Run + Cloud Scheduler)
-----------------------------------------------

### 3.1 Cloud Run Services

**Raw Ingestion Services:**

- `ingest_databento_daily`  
  Pulls daily OHLCV (and intraday where needed) for selected symbols
- `ingest_fred_series`  
  Macro series (rates, CPI, GDP, etc.)
- `ingest_vixcls`  
  VIXCLS daily close from FRED
- `ingest_cftc`  
  CFTC Disaggregated Commitment of Traders
- `ingest_weather_daily`  
  Reads NOAA / GHCN / GSOD / ICOADS public BQ tables and writes region aggregates to `raw_v2.weather_raw`
- `ingest_gdelt_daily`  
  Aggregates GDELT events/GKG into a curated daily feed (or the staging can query directly)
- `ingest_scrape_event`  
  HTTP endpoint for ScrapeCreators; writes to `raw_v2.scrape_events`

**All ingest services:**

- Normalize fields to consistent types
- Write either NDJSON or Parquet to GCS and then to BigQuery via load jobs
- Avoid streaming inserts

### 3.2 Cloud Scheduler

Cloud Scheduler triggers services on cron-style cadence  
dev.to
:

- `ingest_databento_daily` – EOD (once per day)
- `ingest_fred_series` / `ingest_vixcls` – daily
- `ingest_cftc` – weekly
- `ingest_weather_daily` – daily
- `ingest_gdelt_daily` – daily
- `ingest_scrape_event` – event-driven (ScrapeCreators posts)
- Optional `run_training_job` – daily / weekly for Mac sync (if automated)

Cloud Scheduler is used purely as a cron service with HTTP targets; it does not run logic itself  
dev.to
.

4. Dataform Layer (BigQuery Transformations)
--------------------------------------------

All BigQuery transformations (non-trivial ones) are defined in Dataform. No ad-hoc CREATE TABLE AS SELECT in the console.

### 4.1 Datasets & Naming

- `raw_v2` – ingestion landing tables
- `staging_v2` – cleaned, typed staging tables
- `features_v2` – intermediate feature tables
- `features` – includes canonical `features.daily_ml_matrix`
- `ref` – reference tables (regimes, buckets, mappings)
- `forecasts` – all forecast tables

### 4.2 Key Dataform Models

**Staging models:**

- `staging_v2.market_daily`  
  Cleaned daily OHLCV for all tracked futures
- `staging_v2.fred_macro`
- `staging_v2.vixcls`
- `staging_v2.weather_regions`
- `staging_v2.cftc_positions`
- `staging_v2.scrape_events_bucketed`  
  Joins `raw_v2.scrape_events` with `ref.scraper_to_bucket`
- `staging_v2.gdelt_events_filtered`  
  Filters GDELT GKG for ag/biofuel/logistics/macro topics

**Reference tables:**

- `ref.regime_calendar`
- `ref.regime_weights`
- `ref.scraper_to_bucket`
- `ref.bucket_to_regime`
- `ref.weather_regions` (station → region mapping, etc.)

**Feature builders:**

- `features_v2.news_bucket_daily`  
  Aggregates bucketed events per date/bucket (event_count, avg_tone)
- `features_v2.weather_daily`  
  Region-level temperature/precip anomalies
- `features_v2.fx_daily`  
  Daily FX closes, possibly from Databento or FRED

### 4.3 features.daily_ml_matrix (BQ Version)

Dataform assembles the minimal BigQuery version of `features.daily_ml_matrix` with:

- `symbol`, `data_date`, `timestamp`
- `market_data` STRUCT (OHLCV, VWAP, basic `realized_vol_1h`)
- `pivots` STRUCT (daily pivots and distances)
- `policy` STRUCT (Trump/policy family – baseline fields from QUAD-CHECK)
- `golden_zone` STRUCT (for MES)
- `regime` STRUCT (name, weight from `ref.regime_calendar` + `ref.regime_weights`)
- Initial macro and news variables if they are simple enough

Important: No heavy math like correlations, spreads, advanced vol metrics, or compressive news embeddings is computed in BQ. Those are computed on the Mac.

5. Mac Modeling Engine
----------------------

All heavy computation runs on the Mac, using data exported from BigQuery.

### 5.1 Data Flow

Mac pulls a snapshot of `features.daily_ml_matrix` (and small aux tables like `features_v2.news_bucket_daily`, `features_v2.weather_daily`, `staging_v2.fx_daily` if needed).

Mac builds extended features and targets:

- FX & correlation features
- Spreads & crush
- Volatility & CVOL & VRP
- Weather–volatility interaction
- Event/sentiment features
- Training targets

Mac trains models and writes forecasts back to BigQuery in `forecasts.*`.

### 5.2 FX & Correlation Calculators

For each day:

- Extract ZL returns (1d log return).
- Extract daily returns for:
  - CL, ES, FCPO, RS, ZS, ZM, ZC
  - USDBRL, USDCNY, USDX
- Compute rolling correlations and/or betas (e.g., 60d, 120d, 252d):
  - `corr_zl_cl_60d`, `corr_zl_usdbrl_60d`, etc.
- Optionally OLS betas: slope of ZL on each factor.

These become features in a correlations STRUCT or scalar columns:

- Provide regime context (e.g., when ZL is strongly tracking BRL + CL vs when it is decoupled).

### 5.3 Technical Indicators

Compute, per symbol:

- SMA (5,10,20,50,100,200)
- EMA (12, 26)
- RSI(14)
- MACD(12,26,9)
- ATR(14)
- Realized volatility windows
- Term structure factors (for ZL, CL, some FX):
  - Level (front)
  - Slope (second - front)
  - Curvature (third - 2*second + front)

These can be stored in an auxiliary feature table and then merged into `features.daily_ml_matrix` as additional STRUCT fields or scalar columns.

### 5.4 Volatility & VRP

ZL-specific vol metrics:

- Realized volatility (e.g., 10d, 20d).
- Implied volatility from ZL options (30d tenor).
- `VRP_zl = iv_30d – rv_20d`.

Write as:

- `volatility.zl_rv_20d`, `volatility.zl_iv_30d`, `volatility.zl_vrp`.

### 5.5 Weather–Volatility Coupling

Using weather anomalies for:

- U.S. Midwest
- Brazil
- Argentina

Calculate:

- Weather shock indices (e.g. z-score of temperature/precip anomalies).
- Interaction term with recent ZL volatility.

Example feature:

- `weather_vol_shock_score = drought_anomaly_z * zl_rv_20d`.

This is used for regime gating and scenario analysis.

### 5.6 Spreads & Crush Engine

On Mac:

- Compute spreads:
  - `ZL–FCPO`, `ZL–RS`, `ZL–CL` (normalized to ¢/lb)
  - `ZL–ZS`, `ZL–ZM–ZS` combinations reflecting crush economics
- Compute crush margin:
  - Using CME board crush approximations:  
    1 bushel soybeans → ~11 lb oil + ~44 lb meal  
    Convert ZL (¢/lb) and ZM ($/ton) appropriately and subtract soybean price.

Write features:

- `spread.zl_fcpo`, `spread.zl_rs`, `spread.zl_cl`, etc.
- `crush.margin`, `crush.zscore`.

### 5.7 Training Targets

For ZL:

- `target_1w = (zl_close[t+5] / zl_close[t]) - 1`
- `target_1m = (zl_close[t+21] / zl_close[t]) - 1`
- `target_3m = (zl_close[t+63] / zl_close[t]) - 1`
- `target_6m = (zl_close[t+126] / zl_close[t]) - 1`
- `target_12m = (zl_close[t+252] / zl_close[t]) - 1`

For MES (MAIN and SPECIAL), follow QUAD-CHECK target definitions.

### 5.8 Modeling

**ZL multi-horizon models:**

- Seq2seq / LSTM / transformer‐style encoder
- Multi-horizon outputs: 1w, 1m, 3m, 6m, 12m
- Regime-gated ensembles (regime weights from `ref.regime_weights` + regime signals in features)
- Conformal prediction intervals

**MES models:**

- SPECIAL: hourly 3-target predictor (direction, vol regime, key level)
- MAIN: daily multi-horizon (1d → 12m)

### 5.9 Forecast Tables

Mac writes:

- `forecasts.zl_forecasts_daily`
- `forecasts.zl_scenarios_grid`
- `forecasts.zl_explainers_daily`
- `forecasts.zl_regimes_daily`
- `forecasts.mes_main_daily`
- `forecasts.mes_special_hourly`

Each table is narrow, with clear, documented schema, and no joins at query time.

6. ScrapeCreators & News Buckets
--------------------------------

### 6.1 Mapping

Use `ref.scraper_to_bucket`:

**Columns:**

- `source_slug` – ScrapeCreators job id
- `bucket_id` – e.g. TRUMP, TARIFFS, BIOFUEL, WEATHER_US, LOGISTICS_PANAMA, LOGISTICS_REDSEA
- `regime_family` – e.g. `trump_policy`, `trade_war`, `biofuel_policy`, `weather_shock`, `logistics_stress`
- `regime_name` – if mapping directly to canonical regimes
- `weight_override` – optional

### 6.2 Dataform Aggregation

`staging_v2.scrape_events_bucketed` joins `raw_v2.scrape_events` to `ref.scraper_to_bucket` to attach bucket & regime metadata.

`features_v2.news_bucket_daily`:

Aggregates per date, `bucket_id`:

- `event_count`
- `avg_tone`
- Optional: can store per `regime_family` as well.

### 6.3 Integration into daily_ml_matrix

On Mac or in Dataform, join `news_bucket_daily` into `features.daily_ml_matrix` as:

- `news.buckets` STRUCT or as scalar fields, e.g.:
  - `news_trump_event_count_7d`
  - `news_tariffs_event_count_14d`
  - `news_logistics_panama_event_count_7d`
  - `news_weather_us_event_count_7d`

Mac uses `ref.regime_weights` to convert these into risk/scenario scores.

7. Forecast API (Cloud Run)
---------------------------

Implement a small REST API with these endpoints:

- `GET /forecasts/zl`  
  Returns latest ZL forecasts across all horizons per date
- `GET /forecasts/zl/scenarios`  
  Returns scenario grid for ZL (VIX × FX × weather × policy × logistics)
- `GET /forecasts/zl/explainers`  
  Returns SHAP‐style drivers per date/horizon
- `GET /forecasts/zl/regimes`  
  Returns regime history & tags per date
- `GET /forecasts/mes/daily`
- `GET /forecasts/mes/hourly`

Each endpoint responds with JSON matching the front-end’s contract.

8. Front-End (Vercel) Pages
---------------------------

### 8.1 ZL Forecast Page

**Elements:**

- Multi-horizon probability forecasts with fan charts
- Confidence intervals (50/80/95%) in line with QUAD-CHECK
- Trump/Policy strip: one of 400+ features, not a command signal
- SHAP driver list (top 3–5): RINs, Trump, Weather, Crush, etc.
- Dual scenarios: “Consider locking if…” + “Consider waiting if…”
- Mandatory disclaimer: “Not financial advice. Consult your risk management team.”

### 8.2 MES Page

- Hourly A/B/C targets (direction, vol, key level)
- Daily multi-horizon outlook
- Confidence intervals
- SHAP drivers

### 8.3 Vegas Intel Page (Sales View)

**Inputs:**

- Vegas events (Phase 2 once feeds are connected)
- Tourism signals (Google Trends)
- Weather for Vegas
- Potential logistic risk (if relevant)

**Outputs:**

- Demand index for fry oil per day (based on event and seasonality factors)
- Priority customer clusters
- Suggested outreach conditions (never commands, always “consider if…”)

No price predictions / futures calls.  
This page is sales-strategy only and follows QUAD-CHECK’s non-price compliance rules for Vegas Intel.

9. Execution Sequence for V14
-----------------------------

**Phase 1 – Data & Dataform (5–7 days)**

- Set up `raw_v2`, `staging_v2`, `features_v2`, `forecasts`, `ref` datasets.
- Implement ingestion jobs for Databento, FRED, VIXCLS, weather, CFTC.
- Implement Dataform models for:
  - `staging_v2.market_daily`
  - `staging_v2.fred_macro`
  - `staging_v2.vixcls`
  - `staging_v2.weather_regions`
  - `staging_v2.cftc_positions`
  - `staging_v2.scrape_events_bucketed`
  - `features_v2.news_bucket_daily`
- Minimal `features.daily_ml_matrix` (market_data, pivots, policy, regime).

**Phase 2 – Mac Modeling Core (5–10 days)**

- Export `features.daily_ml_matrix`.
- Implement Mac calculators for:
  - FX + correlations
  - Vol + CVOL + VRP
  - Spreads + crush
  - Weather–vol coupling
- Define ZL targets and train first stable ZL model.
- Populate:
  - `forecasts.zl_forecasts_daily`
  - `forecasts.zl_scenarios_grid`
  - `forecasts.zl_explainers_daily`
  - `forecasts.zl_regimes_daily`

**Phase 3 – API & UI (5–7 days)**

- Implement Cloud Run Forecast API endpoints.
- Implement ZL page on Vercel (probabilities, SHAP, scenarios).
- Wire MES page skeleton, even if some “special” parts are Phase 2.
- Implement minimal Vegas Intel page using available demand proxies.

**Phase 4 – Hardening & Extensions**

- Add more advanced feature families:
  - Full Fib feature set
  - Additional FX and macro
  - Expanded MES features
- Optimize model performance
- Validate backtests and regime performance
- Expand Vegas Intel once event feeds and customer orders are structured.

This plan now:

- Respects your QUAD-CHECK architecture
- Brings in all the new data sources and ideas (FX, correlations, Mac calculators, VIX, weather, ScrapeCreators, Vegas Intel)
- Uses Dataform in exactly the way you need (thin, stable, canonical)
- Keeps BigQuery as a storage and light transformation engine, not a place for heavy logic
- Makes the Mac the true modeling and calculus engine
- Gives you a clear, staged V14 path that avoids another multi-month stall in schema hell.
