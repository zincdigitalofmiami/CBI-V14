# FRESH START MASTER PLAN
**Date:** November 18, 2025  
**Status:** Complete Rebuild - Clean Architecture  
**Purpose:** Single source of truth for new architecture with source prefixing, DataBento live futures, expanded FRED, and a canonical feature table (`master_features_2000_2025.parquet`) that mirrors to BigQuery for Ultimate Signal, Big 8, MAPE, and Sharpe dashboards.

---

## PHILOSOPHY

**"Clean slate, proper architecture, source-prefixed columns, robust data collection"**

- **Source Prefixing:** ALL columns prefixed with source (`yahoo_`, `databento_`, `fred_`, etc.) - industry best practice
- **Mac M4:** ALL training + ALL feature engineering (local, deterministic)
- **BigQuery:** Storage + Scheduling + Dashboard (NOT training)
- **External Drive:** PRIMARY data storage + Backup
- **Dual Storage:** Parquet (external drive) + BigQuery (mirror)
- **Staging + Quarantine:** No bad data reaches training
- **Declarative joins:** YAML spec with automated tests
- **QA gates:** Block between every phase

---

## QUICK DATA SOURCES OVERVIEW

- New live source: DataBento GLBX.MDP3 (CME/CBOT/NYMEX/COMEX)
  - Schemas: `ohlcv-1m`, `ohlcv-1h`, `ohlcv-1d`
  - Usage: forward-only from cutover; store local Parquet under `TrainingData/live/` and `TrainingData/live_continuous/`
  - Symbology: `{ROOT}.FUT` via `stype_in='parent'` (e.g., `ES.FUT`, `ZL.FUT`); exclude spreads (`symbol` contains `-`)

- Existing pulls (historical remains in place):
  - Yahoo Finance: ZL=F OHLCV + indicators (46+) for 2000-2010 bridge
  - DataBento: ALL futures 2010-present (primary source)
  - FRED: 55–60 macro series
  - EIA / USDA / EPA / World Bank / CFTC: domain‑specific datasets (biofuels, exports, RINs, pink sheet, positioning)

- What we have now (high level):
  - Historical OHLCV + indicators (ZL via Yahoo 2000-2010; ALL via DataBento 2010+)
  - Macro (FRED) and domain series (EIA/USDA/etc.) staged and/or mirrored
  - Live futures via DataBento GLBX.MDP3, continuous front built hourly/daily

- Vercel (serverless) API endpoints (basic):
  - `GET https://<your-app>.vercel.app/api/v1/market/ohlcv?root=ES&tf=1m&minutes=90`
  - `GET https://<your-app>.vercel.app/api/v1/market/latest-1m?root=ES`
  - Server env: set `DATABENTO_API_KEY` (server‑only). No client secrets.

---

## DATA SOURCE RESPONSIBILITIES

### DataBento (Futures Live + Forward)
**Role:** Primary live futures provider (CME/CBOT/NYMEX/COMEX) from cutover date forward  
**Scope:** 15 years available; preserve all historical already collected and begin forward-only via DataBento.

**Datasets/Schemas:**
- Dataset: `GLBX.MDP3`
- Schemas: `ohlcv-1m` (intraday), `ohlcv-1h` (summaries), `ohlcv-1d` (daily)
- Symbology: `stype_in='parent'`, symbols: `{ROOT}.FUT` (e.g., `ES.FUT`, `ZL.FUT`)
- Exclude calendar spreads (symbols containing `-`)

**Cutover Strategy:**
- Keep historical exactly as-is (Yahoo/DataBento/BigQuery).  
- Begin forward-only ingestion today via DataBento and store Parquet under `TrainingData/live/` and continuous under `TrainingData/live_continuous/`.
- Stitch historical + live at query time (or via stitcher) to form unified continuous series.

**Security:**
- Key: `DATABENTO_API_KEY` (server-side only). Store via macOS Keychain.  
  See `docs/setup/KEYCHAIN_API_KEYS.md` for the Keychain command and export snippet.

**Quality Controls:**
- Tick sizes per root: `registry/universe/tick_sizes.yaml`
- Spread filter (drop `symbol` with `-`)
- No future timestamps; outlier guards; variance checks

**Implemented Utilities:**
- Live poller (forward-only 1m): `scripts/live/databento_live_poller.py`
- Build forward continuous (front-by-volume): `scripts/ingest/build_forward_continuous.py`
- Serverless helpers/endpoints (development):  
  - Range: `scripts/api/databento_ohlcv_range.py`  
  - Latest 1m: `scripts/api/databento_latest_1m.py`  
  - API routes: `dashboard-nextjs/src/app/api/v1/market/{ohlcv,latest-1m}/route.ts`

### Yahoo Finance
**Role:** ZL Historical Bridge (2000-2010 ONLY)  
**Provides:**
- ZL=F raw OHLCV (2000-2010)
- ZL=F technical indicators (46+): RSI_14, MACD, SMA_5, etc.
- **Prefix:** `yahoo_` on ALL columns except `date`, `symbol`

**Why Yahoo for Historical:**
- DataBento only goes back to 2010-06-06
- Need 2000-2010 for 25-year training window
- One-time backfill, then static (no updates)

---

### DataBento (Primary Live Feed)
**Role:** All futures (CME/CBOT/NYMEX/COMEX) - REPLACING Alpha Vantage  
**Provides:**
- **All Futures:** ZL, ES, MES, ZS, ZM, CL, NG, RB, HO, GC, SI, HG (29 total)
- **FX Futures:** 6L (BRL), CNH (Yuan), 6E (EUR) - direct CME contracts
- **Microstructure:** trades, TBBO, MBP-10 for orderflow analysis
- **Calendar Spreads:** All month-to-month spreads
- **Historical:** Back to 2010-06-06 (Yahoo fills 2000-2010)
- **Collection Frequency:** 
  - ZL: 5-minute priority
  - MES: 1-minute for intraday
  - Others: 1-hour standard
- **Prefix:** `databento_` on ALL columns except `date`, `symbol`

**Does NOT Provide:**
- Palm oil futures (not on CME)
- Pre-2010 history (use Yahoo)
- Calculated indicators (compute locally)
- News/sentiment (use ScrapeCreators)

---

### FRED (Federal Reserve Economic Data)
**Role:** Comprehensive US economic indicators (PRIMARY source)  
**Provides:** 55-60 economic series (expanded from 34)

**Current (34 series):**
- Interest Rates: DFF, DGS10, DGS2, DGS30, DGS5, DGS3MO, DGS1, DFEDTARU, DFEDTARL
- Inflation: CPIAUCSL, CPILFESL, PCEPI, DPCCRV1Q225SBEA
- Employment: UNRATE, PAYEMS, CIVPART, EMRATIO
- GDP & Production: GDP, GDPC1, INDPRO, DGORDER
- Money Supply: M2SL, M1SL, BOGMBASE
- Market Indicators: VIXCLS, DTWEXBGS, DTWEXEMEGS
- Credit Spreads: BAAFFM, T10Y2Y, T10Y3M
- Commodities: DCOILWTICO, GOLDPMGBD228NLBM
- Other: HOUST, UMCSENT, DEXUSEU

**Additional to Add (~20-25 series):**
- **PPI (Producer Price Index):** PPIACO, PPICRM, PPIFIS, PPIIDC (agricultural inputs)
- **Trade/Currency:** DTWEXAFEGS, DEXCHUS, DEXBZUS, DEXMXUS
- **Energy:** DCOILBRENTEU, DHHNGSP, GASREGW
- **Financial Conditions:** NFCI, NFCILEVERAGE, NFCILEVERAGE (Risk), NFCILEVERAGE (Credit)
- **Consumer Sentiment:** UMCSENT1Y, UMCSENT5Y
- **Manufacturing:** ISM Manufacturing PMI (if available)
- **Housing:** HOUST1F, HOUSTMW
- **Money Markets:** SOFR, EFFR

**Prefix:** `fred_` on ALL columns except `date`

**Why Keep FRED:**
- Comprehensive macro coverage (55-60 series)
- Authoritative (direct from Fed/agencies)
- Free (120 calls/min)
- Complements DataBento futures data

---

### Other Sources (Keep Separate)
- **EIA:** Biofuel production, RIN prices. Key series must be separated.
  - **Strategy:** Granular wide format by series ID.
  - **Key Series:** Biodiesel production (PADD 1-5), Ethanol production (US total), D4/D6 RIN prices.
  - **Column Naming:** `eia_biodiesel_prod_padd2`, `eia_rin_price_d4`, etc.
- **USDA:** Agricultural reports, export sales. Key reports must be separated.
  - **Strategy:** Granular wide format by report and field.
  - **Key Reports:** WASDE, Export Sales, Crop Progress.
  - **Column Naming:** `usda_wasde_world_soyoil_prod`, `usda_exports_soybeans_net_sales_china`, `usda_cropprog_illinois_soybeans_condition_pct`, etc.
- **EPA:** RIN prices (if different from EIA)
- **World Bank:** Pink sheet commodity prices
- **Palm Oil (Barchart/ICE):** Dedicated palm futures + spot feed.  
  - **Prefix:** `barchart_palm_` on price/volume/volatility columns.  
  - **Files:** `raw/barchart/palm_oil/`, staged to `staging/barchart_palm_daily.parquet`.
- **CFTC:** COT positioning data
- **Weather (NOAA/INMET/SMN):** Multi-country, multi-region weather data. Each region is a unique dataset.
  - **Strategy:** Granular wide format. One row per date, with separate columns for each key agricultural region.
  - **Key Regions:**
    - US Midwest: `illinois`, `iowa`, `indiana`, `nebraska`, `ohio`
    - Brazil: `mato_grosso`, `parana`, `rio_grande_do_sul`
    - Argentina: `buenos_aires`, `cordoba`, `santa_fe`
  - **Column Naming:** `weather_{country}_{region}_{variable}` (e.g., `weather_us_iowa_tavg_c`).
  - **Feature Engineering:** Enables creation of production-weighted ensembles in `build_all_features.py` (e.g., `feature_weather_us_midwest_weighted_tavg`).

**Prefixes:** Granular prefixes for all sources (e.g., `eia_biodiesel_prod_padd2`, `usda_wasde_world_soyoil_prod`, `weather_us_illinois_`) on all columns except `date`.

---

### Volatility & VIX (Macro Risk Layer)
- **Source:** FRED VIX + realized vol calculations from DataBento on ZL, ES
- **Raw Files:** `raw/volatility/vix_daily.parquet`, `raw/volatility/zl_intraday.parquet`
- **Staging:** `staging/volatility_daily.parquet` with prefixes `vol_vix_`, `vol_zl_`, `vol_palm_`
- **Features:** `zl_realized_vol_20d`, `palm_realized_vol_20d`, `es_intraday_vol_5d`, `vol_regime`, `vix_level`, `vix_zscore`
- **Usage:** Drives regime detection, Big 8 “VIX stress” pillar, and ES aggregation logic

### Policy & Trump Intelligence
- **Scripts:** `scripts/predictions/trump_action_predictor.py` (Truth Social + policy wires) and `scripts/predictions/zl_impact_predictor.py`
- **Raw/Staging:** `raw/policy/trump_policy_events.parquet` → `staging/policy_trump_signals.parquet`
- **Prefix:** `policy_trump_` (e.g., `policy_trump_action_prob`, `policy_trump_expected_zl_move`, `policy_trump_procurement_alert`)
- **Sources Covered:** ScrapeCreators (Truth Social + Twitter/Facebook/LinkedIn), aggregated news (NewsAPI, trusted RSS), ICE announcements, USTR/Federal Register tariff notices, White House executive orders, ScrapeCreators Google Search queries for trade/biofuel/agriculture/energy keywords
- **Classification:** Each record tagged into `policy_*`, `trade_*`, `biofuel_*`, `logistics_*`, `macro_*` buckets with region/source metadata and ZL sentiment score
- **Cadence:** Truth Social/ScrapeCreators social feeds and Google Search queries every 15 minutes (matching Big 8 refresh); aggregated news/ICE/USTR/EO scrapes hourly with a daily full backfill so nothing is missed over weekends/holidays
- **Integration:** Feeds dashboard policy cards and becomes the "Policy Shock" pillar inside `signals.big_eight_live`
- **Cadence:** Every 15 minutes alongside the Big 8 refresh cycle
- **Table Relationship:** `sync_signals_big8.py` writes snapshots to `signals.big_eight_live` table. Dashboards read directly from `signals.big_eight_live` for the latest record. The same staged feed also powers the "Sentiment & Policy" dashboard lane—stories, social hits, lobbying/regulatory events, tariffs, and executive orders show up there with their sentiment tags so the front-end can explain shocks in plain English.

---

## FOLDER STRUCTURE (Clean)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/                    # Immutable source zone
│   │   ├── yahoo_finance/      # ZL=F ONLY
│   │   │   └── prices/commodities/ZL_F.parquet
│   │   ├── databento/          # DataBento futures data
│   │   │   ├── prices/
│   │   │   │   ├── commodities/ (CORN, WHEAT, WTI, etc.)
│   │   │   │   ├── fx/          (USD/BRL, USD/CNY, etc.)
│   │   │   │   └── mes_intraday/ (12 horizons: 1min, 5min, 15min, 30min, 1hr, 4hr, 1d, 7d, 30d, 3m, 6m, 12m)
│   │   │   └── indicators/
│   │   │       ├── daily/      (50+ indicators per symbol)
│   │   │       └── intraday/   (MES indicators)
│   │   ├── fred/               # FRED Economic Data (55-60 series)
│   │   │   ├── processed/      # One parquet per series
│   │   │   └── combined/       # Wide format combined
│   │   ├── weather/            # NOAA/INMET/SMN
│   │   │   ├── noaa/           # US Midwest (NOAA GHCN-D stations per state)
│   │   │   ├── inmet/          # Brazil (INMET stations per state)
│   │   │   └── smn/            # Argentina (SMN stations per province)
│   │   ├── cftc/               # CFTC COT
│   │   ├── usda/               # USDA Agricultural (separated by report: WASDE, Exports, etc.)
│   │   ├── eia/                # EIA Biofuels (separated by series: Biodiesel, Ethanol, RINs)
│   │   └── .cache/             # Cache (outside raw/)
│   │
│   ├── staging/                # Validated, conformed, PREFIXED
│   │   ├── yahoo_zl_only.parquet          # ZL=F with yahoo_ prefix
│   │   ├── databento_futures_daily.parquet   # All futures with databento_ prefix
│   │   ├── databento_mes_1min.parquet # MES 1min with databento_ prefix
│   │   ├── databento_mes_5min.parquet # MES 5min with databento_ prefix
│   │   ├── databento_mes_15min.parquet # MES 15min with databento_ prefix
│   │   ├── databento_mes_30min.parquet # MES 30min with databento_ prefix
│   │   ├── databento_mes_1hr.parquet # MES 1hr with databento_ prefix
│   │   ├── databento_mes_4hr.parquet # MES 4hr with databento_ prefix
│   │   ├── barchart_palm_daily.parquet    # Palm oil prices with barchart_palm_ prefix
│   │   ├── fred_macro_expanded.parquet    # 55-60 series with fred_ prefix
│   │   ├── weather_granular_daily.parquet # GRANULAR WIDE FORMAT: one column per region
│   │   ├── usda_reports_granular.parquet  # GRANULAR WIDE FORMAT: one column per report/field
│   │   ├── eia_energy_granular.parquet    # GRANULAR WIDE FORMAT: one column per series ID
│   │   ├── cftc_cot_2006_2025.parquet    # With cftc_ prefix
│   │   ├── usda_nass_2000_2025.parquet   # With usda_ prefix
│   │   ├── eia_biofuels_2010_2025.parquet # With eia_ prefix
│   │   ├── volatility_daily.parquet       # VIX + realized vol with vol_* prefixes
│   │   └── policy_trump_signals.parquet   # Policy forecasts with policy_trump_ prefix
│   │
│   ├── features/               # Engineered signals
│   │   └── master_features_2000_2025.parquet  # Canonical feature table mirrored to BigQuery for Ultimate Signal, Big 8, MAPE/Sharpe
│   │
│   ├── exports/                # Final training parquet per horizon
│   │   ├── zl_training_prod_allhistory_1w.parquet
│   │   ├── zl_training_prod_allhistory_1m.parquet
│   │   ├── mes_training_prod_allhistory_1min.parquet
│   │   ├── mes_training_prod_allhistory_5min.parquet
│   │   ├── mes_training_prod_allhistory_15min.parquet
│   │   ├── mes_training_prod_allhistory_30min.parquet
│   │   ├── mes_training_prod_allhistory_1hr.parquet
│   │   ├── mes_training_prod_allhistory_4hr.parquet
│   │   ├── mes_training_prod_allhistory_1d.parquet
│   │   ├── mes_training_prod_allhistory_7d.parquet
│   │   ├── mes_training_prod_allhistory_30d.parquet
│   │   ├── mes_training_prod_allhistory_3m.parquet
│   │   ├── mes_training_prod_allhistory_6m.parquet
│   │   ├── mes_training_prod_allhistory_12m.parquet
│   │   └── ... (all horizons)
│   │   # Daily exports feed training + BigQuery mirrors, while a separate 15-minute Big 8 lane reads the latest MES/policy/palm signals for dashboard refresh
│   │
│   └── quarantine/            # Failed validations
│
├── registry/
│   ├── join_spec.yaml          # Declarative joins (updated for prefixes)
│   └── regime_calendar.parquet # Regime assignments
│
└── scripts/
    ├── ingest/                 # API pulls → raw/
    │   ├── collect_yahoo_zl_only.py
    │   ├── collect_databento_live.py
    │   ├── collect_fred_expanded.py      # NEW: 55-60 series
    │   ├── collect_databento_mes_intraday.py  # NEW: MES intraday (1min, 5min, 15min, 30min, 1hr, 4hr) + daily+ (1d, 7d, 30d, 3m, 6m, 12m)
    │   ├── collect_palm_barchart.py      # NEW: dedicated palm feed
    │   ├── collect_volatility_intraday.py # NEW: realized vol snapshots
    │   └── collect_policy_trump.py       # NEW: Trump policy event scraper
    ├── staging/                # raw/ → staging/ (with prefixes)
    │   ├── create_staging_files.py      # Prefixes all sources
    │   └── prepare_databento_for_joins.py   # Prefixes DataBento data
    ├── assemble/               # staging/ → features/
    │   └── execute_joins.py    # Uses prefixed columns
    ├── features/               # Feature engineering
    │   ├── build_all_features.py        # Daily joins + engineered signals
    │   └── build_mes_intraday_features.py # Aggregates intraday MES → daily features + Big 8 snapshots
    └── qa/                     # Validation
```

---

## COLUMN NAMING CONVENTION

### Industry Best Practice: Source Prefix Pattern

**All columns prefixed with source identifier:**
- `yahoo_open`, `yahoo_high`, `yahoo_close`, `yahoo_rsi_14`, `yahoo_macd`
- `databento_open`, `databento_high`, `databento_close`, `databento_volume`, `databento_oi`
- `fred_fed_funds_rate`, `fred_vix`, `fred_treasury_10y`
- `weather_us_iowa_tavg_c`, `weather_us_illinois_prcp_mm`, `weather_br_mato_grosso_tavg_c`
- `cftc_open_interest`, `cftc_noncommercial_long`
- `usda_wasde_world_soyoil_prod`, `usda_exports_soybeans_net_sales_china`
- `eia_biodiesel_prod_padd2`, `eia_rin_price_d4`

**Unprefixed (Join Keys Only):**
- `date` - Universal join key
- `symbol` - Multi-symbol joins

**Benefits:**
- Clear source identification
- No naming conflicts
- Future-proof (easy to add new sources)
- Industry standard (data warehouse best practice)

---

## DATA COLLECTION PRIORITIES

### Phase 0: Futures Live Cutover (Immediate)
0. **DataBento (GLBX.MDP3):** Start forward-only 1m ingestion for Phase‑A roots (ES/MES, ZL/ZS/ZM/ZC/ZW, CL/NG/RB/HO, GC/SI/HG).  
   - Run: `python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL --interval 60`  
   - Build continuous: `python3 scripts/ingest/build_forward_continuous.py --root ES --days 1`
   - Keep historical sources intact; stitch at analysis time.

### Phase 1: Core Data (Week 1)
1. **Yahoo:** ZL=F historical (2000-2010) + indicators → `yahoo_` prefix
2. **DataBento:** ALL futures (2010-present) → `databento_` prefix
   - Use `scripts/live/databento_live_poller.py` for real-time collection
   - Historical backfill via `databento.timeseries.get_range()`
   - Store in `TrainingData/live/` and `TrainingData/live_continuous/`
3. **FRED:** Expand to 55-60 series → `fred_` prefix
   - Use `scripts/ingest/collect_fred_comprehensive.py` with a valid API key (32-char lowercase alphanumeric, no hyphens). Store via `security add-generic-password -s "FRED_API_KEY" -w "<key>"`. Official docs: https://fred.stlouisfed.org/docs/api/fred/
   - Default real-time period is "today" (FRED). Only set `realtime_start`/`realtime_end` if we explicitly need ALFRED vintage data; most users want latest revisions, so stick with FRED defaults.
   - Series catalog curated to 53 valid IDs (removed `NAPMPI`, `NAPM`, `GOLDPMGBD228NLBM` which no longer exist). Drop FRED's `series_id` column before merging so each series becomes a single `fred_*` column in the wide frame.
4. **Technical Indicators:** Calculate locally from OHLCV data → prefix by source
5. **Microstructure:** DataBento trades/TBBO/MBP-10 → `databento_` prefix

### Phase 2: Supporting Data (Week 2)
7. **Weather:** All key regions (US states, Brazil states, Argentina provinces) → Granular wide format with region-specific prefixes.
8. **CFTC:** Replace contaminated data → `cftc_` prefix
9. **USDA:** Granular reports (WASDE, Exports, Crop Progress) → Granular `usda_*` prefixes.
10. **EIA:** Granular series (Biodiesel, Ethanol, RINs) → Granular `eia_*` prefixes.
11. **Volatility & VIX:** Daily vol snapshots (VIX + realized vol) → `vol_*` prefixes
12. **Policy & Trump Intelligence:** Truth Social + policy feeds every 15 min → `policy_trump_*`

### Phase 3: Additional Sources (Week 3-4)
13. **EPA:** RIN prices → `epa_` prefix
14. **World Bank:** Pink sheet → `worldbank_` prefix
15. **USDA FAS:** Export sales → `usda_` prefix

---

## JOIN SPECIFICATION (Updated)

### Join Sequence with Prefixes:

1. **base_prices** (Yahoo ZL=F)
   - Columns: `date`, `symbol`, `yahoo_open`, `yahoo_high`, `yahoo_low`, `yahoo_close`, `yahoo_volume`, `yahoo_rsi_14`, `yahoo_macd`, etc.

2. **add_macro** (FRED)
   - Columns: `date`, `fred_fed_funds_rate`, `fred_vix`, `fred_treasury_10y`, etc.
   - Join: `on: ["date"]`

3. **add_weather** (Weather - GRANULAR WIDE FORMAT)
   - **Structure:** One row per date, with a unique column for each key region's variables.
   - **Columns:** `date`, `weather_us_iowa_tavg_c`, `weather_us_iowa_prcp_mm`, `weather_br_mato_grosso_tavg_c`, etc.
   - **Feature Engineering:** Enables production-weighted ensembles (e.g., `feature_weather_us_midwest_weighted_tavg`).
   - Join: `on: ["date"]`

4. **add_cftc** (CFTC)
   - Columns: `date`, `cftc_open_interest`, `cftc_noncommercial_long`, etc.
   - Join: `on: ["date"]`

5. **add_usda** (USDA - Granular Wide Format)
   - **Structure:** One row per date, with unique columns for key report fields.
   - **Columns:** `date`, `usda_wasde_world_soyoil_prod`, `usda_exports_soybeans_net_sales_china`, etc.
   - Join: `on: ["date"]`

6. **add_eia** (EIA - Granular Wide Format)
   - **Structure:** One row per date, with unique columns for key series.
   - **Columns:** `date`, `eia_biodiesel_prod_padd2`, `eia_rin_price_d4`, etc.
   - Join: `on: ["date"]`

7. **add_palm** (Barchart/ICE Palm)
   - Columns: `date`, `barchart_palm_close`, `barchart_palm_volume`, `barchart_palm_vol_20d`
   - Join: `on: ["date"]`

8. **add_volatility** (VIX + realized vol)
   - Columns: `date`, `vol_vix_level`, `vol_zl_realized_20d`, `vol_palm_realized_20d`, `vol_regime`
   - Join: `on: ["date"]`

9. **add_policy_trump** (Policy & Trump forecasts)
   - Columns: `date`, `policy_trump_action_prob`, `policy_trump_expected_zl_move`, `policy_trump_procurement_alert`
   - Join: `on: ["date"]`

10. **add_regimes** (Regime Calendar)
   - Columns: `date`, `market_regime`, `training_weight`
   - Join: `on: ["date"]`

11. **add_databento_enhanced** (DataBento)
   - Columns: `date`, `symbol`, `databento_open`, `databento_high`, `databento_close`, `databento_volume`, etc.
   - Join: `on: ["date", "symbol"]`
   - **Note:** Pre-2010 rows use Yahoo data, post-2010 use DataBento

**MES Handling:** `collect_databento_mes_intraday.py` collects MES data across all 12 horizons (1min, 5min, 15min, 30min, 1hr, 4hr, 1d, 7d, 30d, 3m, 6m, 12m) from DataBento. For intraday horizons (1min-4hr), `build_mes_intraday_features.py` collapses them into daily aggregates (returns, vol, session bias) before the join above. Latest 15-minute snapshots also flow directly to the Big 8 service without waiting for the daily build.

---

## SCRIPT UPDATES REQUIRED

### 1. `scripts/staging/create_staging_files.py`
- ✅ Already updated: Prefixes Yahoo with `yahoo_`
- ✅ Already updated: Prefixes FRED with `fred_` (when expanded)
- ⚠️ **CRITICAL UPDATE NEEDED:** Weather staging logic must be rewritten.
  - **Old:** Generic wide format (`weather_us_*`).
  - **New:** Granular wide format. Must load data per-region (e.g., from `raw/noaa/iowa.parquet`), prefix columns (`weather_us_iowa_`), and merge all regions into a single wide `weather_granular_daily.parquet`.
- ⚠️ **CRITICAL UPDATE NEEDED:** USDA staging logic must be rewritten to create granular wide format from different report types.
- ⚠️ **CRITICAL UPDATE NEEDED:** EIA staging logic must be rewritten to create granular wide format from different series IDs.

### 2. `scripts/staging/prepare_databento_for_joins.py`
- ✅ Prefixes DataBento with `databento_`
- ✅ Handles OHLCV and microstructure data

### 2.5. `scripts/staging/create_weather_staging.py` (REVISED)
- **Responsibility:** Create the single, granular `weather_granular_daily.parquet`.
- **Logic:**
  1. Define key regions (US states, BR states, AR provinces).
  2. Loop through each region:
     a. Load raw data (e.g., `raw/noaa/iowa_daily.parquet`).
     b. Prefix columns: `tavg_c` -> `weather_us_iowa_tavg_c`.
     c. Store prefixed DataFrame.
  3. Merge all region DataFrames on `date` to create one wide table.
- **Result:** A single file with `date` and dozens of region-specific weather columns.

### 3. `scripts/ingest/collect_fred_expanded.py` (NEW)
- Collect 55-60 FRED series (up from 34)
- Robust error handling, retry logic, cache fallback
- Wide format output with `fred_` prefix
- Manifest tracking

### 4. `scripts/ingest/collect_databento_live.py` (NEW)
- Collect all futures via GLBX.MDP3
- MES: 1-minute for intraday horizons
- ZL: 5-minute priority
- Others: 1-hour standard
- Manifest tracking

### 5. `scripts/ingest/collect_palm_barchart.py` (NEW)
- Fetch palm futures/spot from Barchart/ICE
- Output `barchart_palm_` prefixed staging file
- Keep cadence aligned with DataBento refresh schedule

### 6. `scripts/ingest/collect_volatility_intraday.py` (NEW)
- Pull VIX + intraday ZL/ES slices for realized vol calc
- Store `volatility_daily.parquet` with `vol_*` prefixes

### 7. `scripts/ingest/collect_policy_trump.py` (NEW)
- Pull Truth Social + policy wires for Trump activity
- Write staging rows consumed by `trump_action_predictor.py`
- Triggered every 15 minutes (same cycle as Big 8 refresh)

### 8. `registry/join_spec.yaml`
- ✅ Already updated: References prefixed columns
- ✅ Already updated: Handles missing data properly

### 9. `scripts/features/build_all_features.py`
- ✅ Already updated: Detects `databento_` prefixed features
- ✅ Already updated: Uses `yahoo_` indicators for ZL
- ⚠️ **NEW:** Load regime weights from `registry/regime_weights.yaml` (or parquet), drop hard-coded dict
- ⚠️ **NEW:** Incorporate palm, volatility, and policy_trump joins + computed vol regimes
- ⚠️ **NEW:** Compute shock flags/scores (policy/vol/supply/biofuel) and decayed scores; apply capped weight multiplier (≤1000)

### 10. `scripts/features/build_mes_intraday_features.py` (NEW)
- Build MES features from DataBento 1-minute data
- Output: `features/mes_intraday_daily.parquet` and latest snapshot for Big 8 lane

### 11. `scripts/sync/sync_staging_to_bigquery.py` (NEW)
- Load staging parquet files into temporary BigQuery tables then MERGE into production landing tables (partition + cluster aware)
- Used for any staging-level mirrors (e.g., weather, palm, policy)

### 12. `scripts/sync/sync_features_to_bigquery.py` (NEW)
- MERGE `features/master_features_*.parquet` + exports into BigQuery `features.master_features` and `training.*` tables
- Reusable helper for ZL + MES exports (avoids WRITE_TRUNCATE)

### 13. `scripts/sync/sync_signals_big8.py` (NEW)
- Writes Big 8 snapshots (every 15 min) into `signals.big_eight_live` using MERGE on `signal_timestamp`

### 14. `scripts/features/shock_detectors.py` (NEW)
- Vectorized helpers for policy/vol/supply/biofuel shock detection (thresholds + decay); imported by `build_all_features.py`.

---

## VALIDATION REQUIREMENTS

### Data Quality Checks:
- ❌ NO empty DataFrames
- ❌ NO placeholder values (0, -999, sequential numbers)
- ❌ NO static columns (must have variance)
- ❌ NO impossible values (RSI outside 0-100, High < Low)
- ❌ NO stale data (Daily <5d old, Weekly <14d, Monthly <60d; enforced via per-series frequency metadata in `src/utils/data_validation.py`)
- ✅ MINIMUM 100 rows for daily data
- ✅ MINIMUM 50+ indicators calculated locally
- ✅ ALL columns properly prefixed (except `date`, `symbol`)
- ✅ Shock flags are sparse (target 2–6% of days per type) and scores ∈ [0,1]
- ✅ Post-shock weight cap respected (all `training_weight` ≤ 1000)
- ✅ News/policy feeds must have monotonic timestamps + symbol whitelist
- ✅ Cross-source sanity checks (validate fred_* vs databento_* where applicable)
- ✅ Join density checks (overall + per-source non-null ratios logged after `execute_joins.py`)

### Validation Scripts:
- `src/utils/data_validation.py` - Core validation framework
- `scripts/validation/final_databento_validation.py` - Final checkpoint

---

## REGIMES & SHOCKS (Single Source + Local Engine)

### Regime Weights (Single Source of Truth)
- Add `registry/regime_weights.yaml` as the canonical set of regime names, date ranges, and weights on the 50–1000 scale.
- YAML schema:
  - `version`, `last_updated`, `description`
  - `regimes: [{ regime, start_date, end_date, weight, description, aliases: [] }]`
- Implementation:
  - `scripts/regime/create_regime_definitions.py` loads the YAML and emits `registry/regime_calendar.parquet` and `registry/regime_weights.parquet` with canonical names and weights; aliases are normalized.
  - `scripts/features/build_all_features.py` reads the YAML (or emitted parquet) to apply weights; validates min ≥ 50 and max ≤ 1000 and errors on unmapped regimes.
  - QA: `scripts/qa/triage_surface.py` checks weight range and logs regime × row counts.

### Shock Analysis (Local, Optimized)
- Purpose: Detect transient, high-impact events; add shock features and weight emphasis with decay and caps.
- Why local: Complex multi-signal logic and decay runs faster and cheaper with vectorized pandas/NumPy/Polars than repeating SQL windows.

## Policy Shock Scoring Formula

Every policy/news record receives a `policy_trump_score` (0-1) calculated as:

```
policy_trump_score = source_confidence × topic_multiplier × abs(sentiment_score) × recency_decay × frequency_penalty
```

### Component Definitions

**source_confidence (0.50-1.00):**
- Gov (USDA, USTR, EPA, WhiteHouse) → 1.00
- Premium press (Reuters/Bloomberg/WSJ) → 0.95
- Major press (FT/WSJ regional, CNBC, AP) → 0.90
- Trade publications (AgWeb, DTN, Co-ops) → 0.80
- Unknown blog or unverified domain → 0.50

**topic_multiplier:**
- `policy_lobbying` / `policy_legislation` / `policy_regulation` / tariffs → 1.00
- `trade_china` / `trade_argentina` / `trade_palm` → 0.95
- `biofuel_policy` / `biofuel_spread` / `energy_crude` → 0.85
- `supply_farm_reports` / `supply_weather` / `supply_labour` → 0.80
- `logistics_water` / `logistics_port` → 0.70
- `macro_volatility` / `macro_fx` / `macro_rate` → 0.60
- `market_structure` / `market_positioning` → 0.50

**sentiment_score ∈ [-1, 1]:**
- Calculated via keyword matching (bullish keywords - bearish keywords) / (total + 1)
- `sentiment_class` = sign(sentiment_score) → 'bullish', 'bearish', or 'neutral'

**recency_decay = exp(-Δhours / 24):**
- Yesterday's headline (~24 hours old) → ~0.37× today's
- 12 hours old → ~0.61×
- 1 hour old → ~0.96×
- Current (0 hours) → 1.0×

**frequency_penalty:**
- Set to 0.8 if ≥3 similar headlines (same domain + query) in past 3 hours
- Otherwise 1.0

### Signed Score for Training

For training, use `policy_trump_score_signed`:
```
policy_trump_score_signed = policy_trump_score × sign(sentiment_score)
```

This preserves direction: positive for bullish shocks, negative for bearish shocks.

### Examples

**Example 1:** White House executive order (gov 1.0) about biofuel waivers (topic 0.85), sentiment -0.8, published 1 hour ago:
```
score = 1.0 × 0.85 × 0.8 × exp(-1/24) × 1.0 ≈ 0.65
```

**Example 2:** River level note (logistics 0.70), trade publication (0.8), mild sentiment -0.3, 12 hours old:
```
score = 0.8 × 0.70 × 0.3 × exp(-12/24) ≈ 0.09
```

### Usage in Training

In `build_all_features.py`, multiply training weights by:
```
weight_multiplier = 1 + 0.2 × policy_trump_score_signed
```

This gives:
- Bullish policy shocks: weight multiplier up to 1.2×
- Bearish policy shocks: weight multiplier down to 0.8×
- Neutral/no policy: weight multiplier = 1.0×

### Per-Bucket Scores

The same formula applies to other buckets (`trade_*`, `biofuel_*`, etc.) by swapping the topic multiplier. High-impact topics (policy/China) dominate, while modest logistics stories remain low unless extremely negative and fresh.

### Output Fields

Every record includes:
- `policy_trump_score`: 0-1 (unsigned magnitude)
- `policy_trump_score_signed`: -1 to +1 (signed for training)
- `policy_trump_confidence`: Source credibility (0.5-1.0)
- `policy_trump_topic_multiplier`: Topic impact multiplier
- `policy_trump_recency_decay`: Time decay factor
- `policy_trump_frequency_penalty`: Duplicate penalty factor
- `policy_trump_sentiment_score`: Raw sentiment (-1 to +1)
- `policy_trump_sentiment_class`: 'bullish', 'bearish', 'neutral'

Shock set (initial):
- Policy shock: `abs(policy_trump_expected_zl_move) ≥ 0.015`; score = normalized move (cap 4%); decay half-life = 5d.
- Volatility shock: `vix_zscore_30d > 2.0` OR `es_realized_vol_5d / median > 1.8`; score = normalized max; decay = 5d.
- Supply (weather) shock: per-region weather z > 2.0 for ≥2 days; weighted by production mix; decay = 7d.
- Biofuel shock: weekly delta z > 2.5 in `eia_*` (RIN/production); decay = 7d.

Outputs added to feature frame:
- Flags: `shock_policy_flag`, `shock_vol_flag`, `shock_supply_flag`, `shock_biofuel_flag`.
- Scores (0–1): `shock_*_score` and decayed variants `shock_*_score_decayed`.

Weight multipliers (capped at ≤1000):
- `multiplier = 1 + 0.20*policy_decayed + 0.10*vol_decayed + 0.15*supply_decayed + 0.10*biofuel_decayed`.
- Final `training_weight` is capped at 1000; clamp events are logged.

Performance notes:
- Use Polars/Arrow projection for IO; vectorize in NumPy/pandas; numba for realized-vol loops if needed.
- Optional: create lightweight BQ views for dashboard-only mirrors of the above; local remains the training source.

---

## PRE-EXECUTION SETUP

### External Drive Cleanup
- Archive legacy `/TrainingData/raw|staging|features|exports|quarantine` directories to `/TrainingData/archive/<date>/` or dedicated backup drive.
- Recreate empty folder structure exactly as defined earlier (including new palm/volatility/policy directories) so ingestion scripts drop files deterministically.
- Verify `/Volumes/Satechi Hub/Projects/CBI-V14/` mount path exists, has >2 TB free, and user has read/write permissions.

### BigQuery Cleanup & Migration Strategy (Week 0)
> **Goal:** Transition to the prefixed schema without any data loss or downtime. No tables are dropped during this phase.

1. **Dependency Analysis (Read-Only)**
   - Query `INFORMATION_SCHEMA.VIEWS` across every dataset to capture all views that reference the legacy tables (e.g., `market_data.soybean_oil_prices`).
   - Use `INFORMATION_SCHEMA.JOBS_BY_PROJECT` (30-day window) to list scheduled queries, CREATE MODEL jobs, Looker/Studio extracts, etc., that read from those tables.
   - Write the results to `docs/migration/bq_dependency_manifest.md`; this becomes the refactor checklist for the cutover.

2. **Create Backup Datasets**
   - For each production dataset, create a timestamped backup (e.g., `cbi-v14.market_data_backup_20251118`, `cbi-v14.training_backup_20251118`).
   - These backups live in `us-central1` and provide a rollback path for months.

3. **Snapshot, Don’t Drop**
   - Copy every legacy table into its backup dataset via BigQuery COPY jobs (safer than CTAS).
   - After copying, run verification queries that compare row counts and simple checksums (e.g., `SELECT COUNT(*)`, `SELECT SUM(CAST(x AS INT64))`) between source and backup. Only proceed when every table matches 100%.

4. **Build the Prefixed Architecture in Parallel**
   - Execute the DDL script `PRODUCTION_READY_BQ_SCHEMA.sql` to create all prefixed tables (`market_data.databento_futures_ohlcv_1d`, `features.master_features`, `training.zl_training_prod_allhistory_*`, `training.mes_training_prod_allhistory_*`, etc.) in `us-central1`.
   - The old tables remain online; both schemas coexist until cutover.

5. **Run Pipelines & Reconcile**
   - Populate the prefixed tables by running the Full Backfill pipeline (local collectors, staging promotion, feature build, sync).
   - For at least one week, run both the legacy and prefixed pipelines in parallel.
   - Use reconciliation SQL (e.g., `SELECT date, close FROM old_table EXCEPT DISTINCT SELECT date, yahoo_close FROM new_table`) to confirm the new data matches the old results for every downstream table/view.

6. **Cutover (Final Switch)**
   - Using the dependency manifest, refactor every downstream consumer (views, scheduled queries, dashboards) to point to the prefixed tables.
   - Disable the legacy ingestion/export paths so only the prefixed pipeline runs.
   - Monitor all dashboards/API endpoints for 24–48 hours to ensure no hidden dependencies were missed.

7. **Decommission Later**
   - Keep the original datasets intact, labeled `_legacy_archived_YYYYMMDD`, for at least 1–3 months. Drop/purge only after the new system has run flawlessly and audits confirm no remaining consumers.

8. **IAM & Region Enforcement**
   - As part of the rebuild, ensure every dataset is in `us-central1`.
   - Restrict write access to ingestion service accounts and designated operators; dashboards/readers get read-only roles. Document final IAM in `docs/setup/KEYCHAIN_API_KEYS.md`.
   - Store API credentials (DataBento, ScrapeCreators, etc.) only in `KEYCHAIN_API_KEYS.md` + secure environment variables; BigQuery tables should reference these keys indirectly (no plaintext keys in SQL/DDL). Rotate keys quarterly and update the keychain doc + IAM bindings together.

### Incremental Sync Scripts
- Add `scripts/sync/sync_staging_to_bigquery.py`: reads staging parquet(s) and performs MERGE into BigQuery landing tables (key = date+symbol). Use `WRITE_TRUNCATE` only for first load.
- Add `scripts/sync/sync_features_to_bigquery.py`: MERGE `features/master_features_*.parquet` into `features.master_features` (matching on date & symbol).
- Update `scripts/sync/sync_databento_to_bigquery.py` to call MERGE helper instead of `WRITE_TRUNCATE`.

**MERGE Pattern Example:**
```sql
MERGE `cbi-v14.features.master_features` T
USING `cbi-v14.tmp.master_features_batch` S
ON T.date = S.date AND T.symbol = S.symbol
WHEN MATCHED THEN UPDATE SET
  yahoo_zl_close = S.yahoo_zl_close,
  databento_zl_volume = S.databento_zl_volume,
  -- list every column explicitly
WHEN NOT MATCHED THEN INSERT ROW;
```
Temporary tables can be loaded via `load_table_from_dataframe` or `LOAD DATA`.

### Naming Enforcement
- Follow `docs/plans/NAMING_ARCHITECTURE_PLAN.md` Option 3: first artifacts have no `_v2`. Only introduce suffixes after breaking changes. Track releases via plan versioning (`Fresh Start Master Plan v1.1`) instead of renaming tables/files.

---

## EXECUTION ORDER & DEPENDENCIES

### Full Backfill (Clean Install)
1. `scripts/ingest/collect_yahoo_zl_only.py`
2. `scripts/ingest/collect_databento_live.py`
3. `scripts/ingest/collect_palm_barchart.py`
4. `scripts/ingest/collect_volatility_intraday.py`
5. `scripts/ingest/collect_policy_trump.py`
6. `scripts/ingest/collect_fred_expanded.py` + other government feeds (weather, CFTC, USDA, EIA, etc.)
7. `scripts/staging/create_staging_files.py` + `create_weather_staging.py`
8. `scripts/staging/prepare_databento_for_joins.py`
9. `scripts/features/build_mes_intraday_features.py`
10. `scripts/assemble/execute_joins.py`
11. `scripts/features/build_all_features.py`
12. `scripts/sync/sync_features_to_bigquery.py`
13. `scripts/qa/triage_surface.py` + validation suite
14. (Optional) `scripts/sync/sync_features_to_bigquery.py --exports-only` to push finalized training exports

### Daily Incremental Refresh (Once Backfill Complete)
1. Run all ingestion scripts scheduled for that day (per cadence table below)
2. `create_staging_files.py` (promote new raw → staging)
3. `prepare_databento_for_joins.py` (updates DataBento staging)
4. `build_mes_intraday_features.py` (daily aggregation)
5. `execute_joins.py`
6. `build_all_features.py`
7. `sync_features_to_bigquery.py` (MERGE incremental rows)
8. `scripts/qa/pre_flight_harness.py` + `triage_surface.py`

### 15-Minute Big 8 Refresh
1. `collect_databento_mes_intraday.py` (latest snapshots)
2. `collect_policy_trump.py` (Truth Social + policy)
3. `collect_volatility_intraday.py` (incremental)
4. `build_mes_intraday_features.py` (latest window only)
5. Calculate Big 8 components:
   - Read latest `signals.crush_oilshare_daily`
   - Read latest `signals.energy_proxies_daily`
   - Read latest `raw_intelligence.policy_events` (with `policy_trump_score`)
   - Read latest `signals.hidden_relationship_signals`
   - Read latest `raw_intelligence.volatility_daily` (VIX/CVOL)
   - Read latest `raw_intelligence.cftc_positioning` (positioning pressure)
   - Read latest `market_data.fx_daily` (FX pressure)
   - Read latest `raw_intelligence.weather_weighted` (weather supply risk)
6. Apply regime-aware weighting and override flags
7. `scripts/sync/sync_signals_big8.py` (MERGE new timestamp into `signals.big_eight_live`)

Each DAG should be orchestrated with cron or a scheduler (future section) ensuring upstream completes with success status before downstream triggers.

---

## BACKFILL STRATEGY

### Scope
- Historical coverage: 2000-01-01 → present for all daily sources; DataBento from 2010-06-06.
- Sources: Yahoo ZL (2000-2010), DataBento futures (2010+), FRED (55-60 series), palm (Barchart), volatility (computed from DataBento), policy/trump (limited to 2020+ due to availability), weather, CFTC, USDA, EIA.

### Approach
1. **DataBento Limits:** Manage API calls efficiently; use batch requests where possible.
2. **Yahoo Backfill:** Use historical CSV download or yfinance fork to pull 25 years of ZL OHLCV + indicators.
3. **Palm Backfill:** If KO*0 page limits history, iterate contract codes (KOF26, KOM25, etc.) and stitch into one continuous series offline before writing to staging.
4. **MES Intraday:** DataBento provides full history from 2010-06-06; 1-minute data for all intraday horizons.
5. **Government Data:** FRED, CFTC, USDA, EIA allow bulk downloads; run once per source to seed raw/bronze folders.
6. **Parallelization:** Run ingestion scripts sequentially per source to respect rate limits, but you can execute independent sources in parallel (e.g., FRED + Yahoo) if system resources allow.
7. **Validation:** After each source backfill, run source-specific QA (row counts, freshness, staleness) before promoting to staging.
8. **Timeline Estimate:** Expect 2-3 hours for DataBento historical pull, <1 hour for Yahoo (2000-2010), <30 min for government data, 1-2 hours for palm contract stitching.

### Recovery
- If an API fails mid-backfill, write the failed batch metadata (symbol, timeframe, last successful date) to `quarantine/databento_backfill_failures.json` and resume later.
- Keep raw snapshots intact so parsers can be re-run without re-hitting the API unless necessary.

---

## EXECUTION TIMELINE

### Week 1: Core Infrastructure
- Day 1-2: Delete legacy MDs/plans, clean up scripts
- Day 3-4: Build new staging scripts with prefixes
- Day 5-7: Build FRED expanded collection (55-60 series)

### Week 2: DataBento Integration
- Day 1-3: Build DataBento live collection script
- Day 4-5: Collect all futures (29 symbols, multiple timeframes)
- Day 6-7: Setup continuous contracts + microstructure features

### Week 3: Supporting Data
- Day 1-2: Fix CFTC collection and build granular USDA/EIA staging scripts.
- Day 3-4: Build granular weather staging script and collect all regional weather data.
- Day 5-7: Test joins with prefixed columns (verify no cartesian products) + run first policy/trump 15-min loop

### Week 4: Validation & Testing
- Day 1-3: Run complete pipeline, validate output
- Day 4-5: Fix any issues + measure join density + cross-source sanity checks
- Day 6-7: Generate final training exports + sync canonical feature table to BigQuery

### Week 0 (Schema Cleanup Prereq)
- Day 1: Run `scripts/staging/create_staging_files.py` to enforce prefixes locally; archive old staging files
- Day 2: Create prefixed BigQuery tables in `market_data`, `raw_intelligence`, `training`, `features`, `signals`, `regimes`, `drivers`, `neural`, `predictions`, `monitoring`, `dim`, `ops` (partition + cluster); copy legacy tables into `*_backup_YYYYMMDD`; lock new schemas in us-central1
- Day 3: Refactor 64 BigQuery views to point at prefixed tables; add MERGE-based sync scripts
- Day 4: Backfill 2000-2019 data into `training.zl_training_prod_allhistory_*` and `features.master_features`; verify row counts and regimes
- Day 5: Replace contaminated CFTC/USDA pulls and migrate remaining US-region datasets into us-central1
- Day 6-7: QA the new schemas, ensure no unprefixed columns remain, and only then start Week 1 tasks

---

## SUCCESS CRITERIA

### Data Collection:
- ✅ Yahoo: ZL=F (2000-2010), all columns prefixed `yahoo_`
- ✅ DataBento: All futures (29 symbols), all columns prefixed `databento_`
- ✅ FRED: 55-60 series, all prefixed `fred_`
- ✅ Weather: Granular wide format, with a unique column for each key agricultural region (e.g., `weather_us_iowa_tavg_c`).
- ✅ CFTC: Prefixed `cftc_`.
- ✅ USDA: Granular wide format with unique columns for key reports/fields (e.g., `usda_wasde_world_soyoil_prod`).
- ✅ EIA: Granular wide format with unique columns for key series (e.g., `eia_biodiesel_prod_padd2`).
- ✅ Palm: Dedicated Barchart/ICE feed with `barchart_palm_*`
- ✅ Volatility: VIX + realized vol snapshots stored as `vol_*`
- ✅ Policy/Trump: 15-min Truth Social + policy feed with `policy_trump_*`

### Join Pipeline:
- ✅ All joins work with prefixed columns
- ✅ ZL uses Yahoo for 2000-2010, DataBento for 2010+
- ✅ All symbols get DataBento data from 2010+
- ✅ Date range: 2000-2025 (25 years)
- ✅ No cartesian products
- ✅ MES intraday collapsed to daily aggregates before join (no timeframe mismatch)
- ✅ Policy/volatility/palm joins land prior to regime enrichment

### Feature Engineering:
- ✅ ZL uses Yahoo indicators for historical period
- ✅ All symbols use locally calculated indicators from DataBento data
- ✅ Custom features calculated for all
- ✅ Regime weights applied (50-1000 scale)
- ✅ Volatility regime + VIX z-scores computed (`vol_*`)
- ✅ Policy shock pillar sourced from Trump predictors (`policy_trump_*`)
- ✅ Shock features present: `shock_*_flag`, `shock_*_score`, decayed variants; final weights capped ≤ 1000

### Training Exports:
- ✅ ZL exports: All horizons (1w, 1m, 3m, 6m, 12m)
- ✅ MES exports: All 12 horizons (4 min + 2 hr + 3 day + 3 month)
- ✅ All columns properly prefixed
- ✅ Validation certificate generated
- ✅ `master_features_2000_2025.parquet` mirrored to BigQuery and serves as single feed for Ultimate Signal, Big 8 (Big 8 replaces Big 7), and MAPE/Sharpe dashboards

---

## MODELING ARCHITECTURE (Aligned with Training Master Execution Plan)

**Goal:** Progressive modeling stack that respects Mac M4 thermals/memory (16GB unified) while driving 60-85% uplift from baseline. All training is 100% local on M4 Mac.

**Reference:** See `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` for detailed day-by-day execution plan.

### Phase 1: Local Baselines
*Purpose:* Comprehensive baselines on expanded 25-year dataset (2000-2025) with feature screening.

**Statistical Baselines:**
- ARIMA/Prophet (25-year patterns)
- Exponential smoothing (validated on 2008 crisis)
- Naive seasonal (period=252)

**Tree-Based Baselines:**
- LightGBM with DART dropout (trained on all regimes)
- XGBoost with regime weighting (using regime tables)
- CatBoost (calibrated quantiles for MAPE)

**Regime-Specific Models:**
- Crisis model (2008, 2020)
- Trade War model (2017-2019)
- Recovery model (2010-2016)
- Pre-Crisis baseline (2000-2007)
- Trump-era model (2023-2025)

**Neural Baselines:**
- Simple LSTM (1-2 layers)
- GRU with attention
- Feedforward dense networks

**Baseline Datasets:**
1. Full history (25 years) with regime weighting
2. Trump-era only (2023–2025)
3. Crisis periods (2008, 2020)
4. Trade war periods (2017–2019)

**Outputs:** Baseline MAPE/directional accuracy + ranked features for downstream phases.

### Phase 2: Regime-Aware Training
*Purpose:* Specialize models per regime cluster with weighting scheme.

**Regime Weighting:**
- Trump 2.0 (2023–2025): weight ×5000
- Trade War (2017–2019): weight ×1500
- Inflation (2021–2022): weight ×1200
- Crisis (2008, 2020): weight ×500–800
- Historical (<2000): weight ×50

**Regime Router:**
```python
class RegimeRouter:
    def __init__(self):
        self.regime_detector = LightGBMClassifier(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.regime_models = {}

    def predict(self, features):
        regime = self.regime_detector.predict(features)[0]
        return self.regime_models[regime].predict(features)
```

**Regime-Specific Models:**
- Crisis regime: 2-layer LSTM + GRU (most important for risk)
- Bull/Bear/Normal: 1 architecture each
- Count: 8-10 regime models total

### Phase 3: Horizon-Specific Optimization

**ZL Horizons** (5 total - Daily forecast horizons only):
- 1 week, 1 month, 3 months, 6 months, 12 months
- Model count: 30-35 models (baselines + regime + advanced)
- Features: Daily features, focus on fundamentals

**MES Horizons** (12 total - Intraday + multi-day horizons):
- **Intraday (minutes):** 1 min, 5 min, 15 min, 30 min
  - Neural nets (LSTM, TCN, CNN-LSTM)
  - Features: 150-200 (microstructure, orderflow, volume)
- **Intraday (hours):** 1 hour, 4 hours
  - Neural nets (LSTM, TCN, CNN-LSTM)
  - Features: 150-200 (microstructure, orderflow, volume)
- **Multi-day:** 1 day, 7 days, 30 days
  - Tree models (LightGBM, XGBoost)
  - Features: 100-150 (macro, sentiment, positioning)
- **Multi-month:** 3 months, 6 months, 12 months
  - Tree models (LightGBM, XGBoost)
  - Features: 100-150 (macro, sentiment, positioning)
- Model count: 35-40 models

**For Each Horizon:**
- Compare all baselines on holdout data
- Select top performer
- Add horizon-specific features
- Fine-tune architecture

### Phase 4: Advanced Neural & Ensemble

**Advanced Neural Architectures:**
- 2-layer LSTM (2-3 variants, units 64-128)
- 2-layer GRU (2-3 variants)
- TCN (1-2 variants, kernel_size 3-5)
- CNN-LSTM hybrid (1-2 variants)
- Optional: 1-2 TINY attention (heads ≤4, d_model ≤256, seq_len ≤256)

**Memory Constraints:**
- FP16 mixed precision (MANDATORY for 16GB RAM)
- Batch sizes: LSTM ≤32, TCN ≤32, attention ≤16
- Sequential training (one GPU job at a time)
- Gradient checkpointing and memory cleanup
- External SSD for all checkpoints/logs

**Ensemble & Meta-Learning:**
- Regime-aware weighting (crisis = weight 1W more, calm = weight 6M more)
- LightGBM meta-learner on OOF predictions + regime context
- Weighted averaging with dynamic regime-aware weights
- Uncertainty quantification (MAPIE conformal prediction for 90% confidence bands)

**Production Optimization:**
- Quantize neural models via TFLite FP16
- Convert tree models to ONNX
- `ProductionPredictor` class handles scaling, feature selection, regime routing, monotonicity checks, and bounds enforcement (±30% annualized)

### Memory & Scheduling Controls

**Hardware Constraints:**
- Mac M4: 16GB unified memory + TensorFlow Metal GPU
- Environment: `vertex-metal-312` (Python 3.12.6)
- Sequential training: One GPU job at a time (prevent thermal throttling)

**Memory Management:**
```python
# Aggressive cleanup between models
import gc
import tensorflow as tf

def cleanup_session():
    gc.collect()
    tf.keras.backend.clear_session()
    tf.compat.v1.reset_default_graph()

# Forced cooldown between neural models
import time
time.sleep(60)  # Prevent thermal throttling
```

**Feature Counts by Phase:**
- Phase 1 (Baselines): 400 features (full feature set)
- Phase 2 (Regime): 60-80 features (regime-specific)
- Phase 3 (Horizon): 40-60 features (horizon-optimized)
- Phase 4 (Neural): 30-40 features (temporal windows)

**Training Schedule:**
- Sequential execution (not parallel)
- Clear Keras sessions after each model
- Monitor Activity Monitor for memory pressure
- Use `model.partial_fit` for large datasets

### Summary

- **Total models:** 65-75 total
  - ZL: 30-35 models (5 horizons)
  - MES: 35-40 models (12 horizons)
- **Training time:** ~22 hours spread across execution plan (Day 1-7 intensive, then ongoing)
- **Expected uplift:** Phase 1 → Phase 4 yields 60-85% accuracy improvement, with regime-specific + neural phases contributing incremental gains before the final ensemble.

**See:** `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` for detailed day-by-day execution plan (Day 1-7) with specific scripts, memory management, and production deployment steps.

---

## SUPER-OPTIMIZED API-FACING OVERLAY LAYER

**Purpose:** Curated views that combine raw tables into dashboard-ready, single-query endpoints. These views eliminate complex joins at query time and provide consistent interfaces for the Vercel dashboard and training exports.

### API-Facing Overlay Views

#### 1. `api.vw_futures_overlay_{horizon}` (Per-Horizon Views)
**Purpose:** Single view per horizon combining ZL and MES continuous series with key drivers (spread/crush/energy proxies + macro).

**Horizons:** `1w`, `1m`, `3m`, `6m`, `12m` (ZL) + `1min`, `5min`, `15min`, `30min`, `1hr`, `4hr`, `1d`, `7d`, `30d`, `3m`, `6m`, `12m` (MES)

**Structure:**
```sql
CREATE OR REPLACE VIEW api.vw_futures_overlay_1w AS
SELECT 
  f.date,
  f.symbol,
  -- Continuous futures (ZL or MES)
  cont.close AS price,
  cont.volume,
  cont.open_interest,
  -- Key drivers
  s.crush_oilshare_pressure,
  s.energy_biofuel_shock,
  s.fx_pressure,
  -- Macro context
  r.fred_dgs10,
  r.fred_vix_level,
  -- Regime context
  reg.regime,
  reg.regime_confidence,
  -- Metadata
  f.as_of
FROM features.master_features f
LEFT JOIN market_data.databento_futures_continuous_1d cont
  ON f.date = cont.date AND f.symbol = cont.root
LEFT JOIN signals.crush_oilshare_daily s
  ON f.date = s.date
LEFT JOIN raw_intelligence.fred_economic r
  ON f.date = r.date
LEFT JOIN regimes.market_regimes reg
  ON f.date = reg.date AND f.symbol = reg.symbol
WHERE f.symbol IN ('ZL', 'MES')
  AND cont.cont_id LIKE '%BACKADJ'
ORDER BY f.date DESC, f.symbol;
```

**Usage:** Dashboard queries one view per horizon instead of joining 5+ tables.

#### 2. `predictions.vw_zl_{horizon}_latest` (Prediction Overlays)
**Purpose:** Overlay views that add prediction metadata (model version, regime weight tags) on top of raw predictions table.

**Horizons:** `1w`, `1m`, `3m`, `6m`, `12m`

**Structure:**
```sql
CREATE OR REPLACE VIEW predictions.vw_zl_1w_latest AS
SELECT 
  p.date,
  p.symbol,
  p.prediction,
  p.prediction_lower_90,
  p.prediction_upper_90,
  p.confidence_score,
  -- Model metadata
  p.model_version,
  p.model_type,
  p.ensemble_weight,
  -- Regime context
  r.regime,
  r.regime_weight,
  r.regime_confidence,
  -- Training metadata
  p.training_date_range,
  p.feature_count,
  p.as_of
FROM predictions.zl_predictions_1w p
LEFT JOIN regimes.market_regimes r
  ON p.date = r.date AND p.symbol = r.symbol
WHERE p.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY p.date DESC
LIMIT 1000;
```

**Usage:** Dashboard reads latest predictions with full context in one query.

### Regime Overlay Views

#### 3. `regimes.vw_live_regime_overlay`
**Purpose:** Big 8 + hidden drivers "regime spine" that collapses VIX stress, biofuel policy, trade risk, etc. into a single daily row with override_flag logic.

**Structure:**
```sql
CREATE OR REPLACE VIEW regimes.vw_live_regime_overlay AS
SELECT 
  date,
  symbol DEFAULT 'ZL',
  -- Big 8 composite
  big8.big8_composite_score,
  big8.big8_signal_direction,
  big8.big8_signal_strength,
  -- Individual Big 8 components
  big8.big8_crush_oilshare_pressure,
  big8.big8_policy_shock,
  big8.big8_weather_supply_risk,
  big8.big8_china_demand,
  big8.big8_vix_cvol_stress,
  big8.big8_positioning_pressure,
  big8.big8_energy_biofuel_shock,
  big8.big8_fx_pressure,
  -- Hidden relationship overlay
  hidden.hidden_relationship_composite_score,
  hidden.correlation_override_flag,
  hidden.primary_hidden_domain,
  -- Regime classification
  reg.regime,
  reg.regime_type,
  reg.regime_value,
  reg.confidence,
  -- Override logic
  CASE 
    WHEN hidden.correlation_override_flag THEN 'hidden_relationships'
    WHEN big8.big8_signal_strength > 0.8 THEN 'big8_strong'
    ELSE reg.regime_value
  END AS effective_regime,
  -- Metadata
  CURRENT_TIMESTAMP() AS as_of
FROM signals.big_eight_live big8
LEFT JOIN signals.hidden_relationship_signals hidden
  ON big8.signal_timestamp = TIMESTAMP(hidden.date)
LEFT JOIN regimes.market_regimes reg
  ON DATE(big8.signal_timestamp) = reg.date AND big8.symbol = reg.symbol
WHERE DATE(big8.signal_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY big8.signal_timestamp DESC;
```

**Usage:** Single query for complete regime context with override logic.

### Compatibility Views for Training Tables

#### 4. `training.vw_zl_training_prod_allhistory_{horizon}`
**Purpose:** Compatibility views so applications still hit the same names even after cutover to venue-pure tables.

**Horizons:** `1w`, `1m`, `3m`, `6m`, `12m`

**Structure:**
```sql
CREATE OR REPLACE VIEW training.vw_zl_training_prod_allhistory_1w AS
SELECT * FROM training.zl_training_prod_allhistory_1w;
-- Simple passthrough for backward compatibility during migration
```

**Usage:** Legacy applications continue working during migration period.

### Signals-Driver Composite Views

#### 5. `signals.vw_big_seven_signals` (Big 7 → Big 8 Evolution)
**Purpose:** Combines crush, spreads, energy proxies, hidden composite, etc. into unified signal view. This is the predecessor to Big 8, maintained for compatibility.

**Structure:**
```sql
CREATE OR REPLACE VIEW signals.vw_big_seven_signals AS
SELECT 
  date,
  symbol DEFAULT 'ZL',
  -- Crush/Oilshare
  crush.crush_oilshare_pressure AS signal_crush,
  -- Energy/Biofuel
  energy.energy_biofuel_shock AS signal_energy,
  -- FX Pressure
  fx.fx_pressure AS signal_fx,
  -- Weather Supply Risk
  weather.weather_supply_risk AS signal_weather,
  -- China Demand
  china.china_demand AS signal_china,
  -- VIX/CVOL Stress
  vol.vix_cvol_stress AS signal_volatility,
  -- Positioning Pressure
  pos.positioning_pressure AS signal_positioning,
  -- Hidden Composite (7th signal)
  hidden.hidden_relationship_composite_score AS signal_hidden,
  -- Composite Score
  (
    crush.crush_oilshare_pressure * 0.20 +
    energy.energy_biofuel_shock * 0.15 +
    fx.fx_pressure * 0.15 +
    weather.weather_supply_risk * 0.15 +
    china.china_demand * 0.15 +
    vol.vix_cvol_stress * 0.10 +
    hidden.hidden_relationship_composite_score * 0.10
  ) AS big_seven_composite_score,
  CURRENT_TIMESTAMP() AS as_of
FROM signals.crush_oilshare_daily crush
LEFT JOIN signals.energy_proxies_daily energy ON crush.date = energy.date
LEFT JOIN signals.calculated_signals fx ON crush.date = fx.date
LEFT JOIN signals.calculated_signals weather ON crush.date = weather.date
LEFT JOIN signals.calculated_signals china ON crush.date = china.date
LEFT JOIN signals.calculated_signals vol ON crush.date = vol.date
LEFT JOIN signals.calculated_signals pos ON crush.date = pos.date
LEFT JOIN signals.hidden_relationship_signals hidden ON crush.date = hidden.date
ORDER BY date DESC;
```

**Note:** Big 8 replaces Big 7, but this view maintained for historical compatibility.

#### 6. `signals.hidden_relationship_signals` (Table)
**Status:** ✅ Already defined in schema (Table 25)

**Purpose:** Hidden cross-domain intelligence signals (defense-agri, tech-agri, CBDC corridors, etc.)

**Usage:** Feeds into Big 8 composite and regime overlay views.

### MES Overlay Views

#### 7. `features.vw_mes_intraday_overlay`
**Purpose:** Rolls up the 1/5/15/30 minute tables into a single wide dataset for downstream training.

**Structure:**
```sql
CREATE OR REPLACE VIEW features.vw_mes_intraday_overlay AS
SELECT 
  date,
  -- 1-minute features
  m1.close AS mes_1min_close,
  m1.volume AS mes_1min_volume,
  m1.realized_vol_5min AS mes_1min_rv_5m,
  -- 5-minute features
  m5.close AS mes_5min_close,
  m5.volume AS mes_5min_volume,
  m5.realized_vol_15min AS mes_5min_rv_15m,
  -- 15-minute features
  m15.close AS mes_15min_close,
  m15.volume AS mes_15min_volume,
  m15.realized_vol_30min AS mes_15min_rv_30m,
  -- 30-minute features
  m30.close AS mes_30min_close,
  m30.volume AS mes_30min_volume,
  m30.realized_vol_1hr AS mes_30min_rv_1hr,
  -- Aggregated microstructure
  m1.order_imbalance AS mes_order_imbalance,
  m1.microprice_deviation AS mes_microprice_dev,
  -- Metadata
  CURRENT_TIMESTAMP() AS as_of
FROM features.mes_intraday_1min m1
LEFT JOIN features.mes_intraday_5min m5 ON m1.date = m5.date
LEFT JOIN features.mes_intraday_15min m15 ON m1.date = m15.date
LEFT JOIN features.mes_intraday_30min m30 ON m1.date = m30.date
ORDER BY date DESC;
```

**Usage:** Training exports read from this view instead of joining 4+ tables.

#### 8. `features.vw_mes_daily_aggregated`
**Purpose:** Intraday→daily aggregator (1h/4h, 1d/7d/30d) feeding the features layer.

**Structure:**
```sql
CREATE OR REPLACE VIEW features.vw_mes_daily_aggregated AS
SELECT 
  DATE(ts_event) AS date,
  -- Hourly aggregates
  AVG(CASE WHEN horizon = '1hr' THEN close END) AS mes_1hr_avg_close,
  SUM(CASE WHEN horizon = '1hr' THEN volume END) AS mes_1hr_total_volume,
  AVG(CASE WHEN horizon = '4hr' THEN close END) AS mes_4hr_avg_close,
  SUM(CASE WHEN horizon = '4hr' THEN volume END) AS mes_4hr_total_volume,
  -- Daily aggregates
  AVG(CASE WHEN horizon = '1d' THEN close END) AS mes_1d_avg_close,
  SUM(CASE WHEN horizon = '1d' THEN volume END) AS mes_1d_total_volume,
  -- Multi-day aggregates
  AVG(CASE WHEN horizon IN ('7d', '30d') THEN close END) AS mes_multi_day_avg_close,
  -- Volatility aggregates
  STDDEV(CASE WHEN horizon = '1hr' THEN close END) AS mes_1hr_realized_vol,
  STDDEV(CASE WHEN horizon = '4hr' THEN close END) AS mes_4hr_realized_vol,
  CURRENT_TIMESTAMP() AS as_of
FROM (
  SELECT ts_event, '1hr' AS horizon, close, volume FROM training.mes_training_prod_allhistory_1hr
  UNION ALL
  SELECT ts_event, '4hr' AS horizon, close, volume FROM training.mes_training_prod_allhistory_4hr
  UNION ALL
  SELECT DATE(ts_event) AS ts_event, '1d' AS horizon, close, volume FROM training.mes_training_prod_allhistory_1d
  UNION ALL
  SELECT DATE(ts_event) AS ts_event, '7d' AS horizon, close, volume FROM training.mes_training_prod_allhistory_7d
  UNION ALL
  SELECT DATE(ts_event) AS ts_event, '30d' AS horizon, close, volume FROM training.mes_training_prod_allhistory_30d
)
GROUP BY DATE(ts_event)
ORDER BY date DESC;
```

**Usage:** Features layer reads daily aggregates from this view.

### Big 8 Refresh Job

#### Scheduled Job: `scripts/sync/sync_signals_big8.py`
**Purpose:** Recalculates `signals.big_eight_live` with overlays for policy/trump/regime overrides.

**Schedule:** Every 15 minutes (matching policy/trump collection cadence)

**Process:**
1. Read latest `signals.crush_oilshare_daily`
2. Read latest `signals.energy_proxies_daily`
3. Read latest `raw_intelligence.policy_events` (with `policy_trump_score`)
4. Read latest `signals.hidden_relationship_signals`
5. Read latest `raw_intelligence.volatility_daily` (VIX/CVOL)
6. Read latest `raw_intelligence.cftc_positioning` (positioning pressure)
7. Read latest `market_data.fx_daily` (FX pressure)
8. Read latest `raw_intelligence.weather_weighted` (weather supply risk)
9. Calculate composite scores with regime-aware weighting
10. Apply override flags (hidden relationships, policy shocks)
11. MERGE into `signals.big_eight_live` on `signal_timestamp`

**Output:** Single row per timestamp with all Big 8 components + composite score + narrative

**Dependencies:**
- `signals.crush_oilshare_daily` (updated hourly)
- `signals.energy_proxies_daily` (updated hourly)
- `raw_intelligence.policy_events` (updated every 15 min)
- `signals.hidden_relationship_signals` (updated daily)
- `raw_intelligence.volatility_daily` (updated daily)
- `raw_intelligence.cftc_positioning` (updated weekly)
- `market_data.fx_daily` (updated daily)
- `raw_intelligence.weather_weighted` (updated daily)

### View Creation Order

**Dependencies:**
1. Create base tables first (via `PRODUCTION_READY_BQ_SCHEMA.sql`)
2. Create compatibility views (training.vw_*)
3. Create signals composite views (`vw_big_seven_signals`)
4. Create MES overlay views (`vw_mes_intraday_overlay`, `vw_mes_daily_aggregated`)
5. Create regime overlay view (`regimes.vw_live_regime_overlay`)
6. Create API overlay views (`api.vw_futures_overlay_*`)
7. Create prediction overlay views (`predictions.vw_zl_*_latest`)

**Script:** `scripts/deployment/create_overlay_views.sql` (to be created)

**Note:** The `api` dataset already exists in BigQuery. Overlay views will be created in this existing dataset.

---

## DASHBOARD EXECUTION BACKLOG (Post-Data Phase)

These cards capture how Chris consumes intelligence. Build them once staging + modeling are live so the dashboard answers his five core questions (“What moved?”, “Is this normal?”, “What do I do?”, “How does it compare?”, “Is risk rising?”).

1. **Inline Explainables**
   - Top 3 SHAP drivers per forecast with plain-English text (“Palm spread widening + BRL weakness drove +0.8% bias”).
   - Macro/news injectors (USDA flashes, palm export chatter, Fed signals) rendered as a one-sentence causal chain.

2. **Regime Indicator Panel**
   - Compact widget: regime name, days active, historical impact profile, and confidence (“Volatility-High | Active since Oct 12 | soy oil reacts 1.4× to palm shocks”).

3. **“What Changed Since Yesterday” Tile**
   - Delta list (palm +1.8%, USD/BRL −0.7%, crush +0.3%, weather +12 % rain, funds +4k) with net effect classification (+0.3σ upward pressure).

4. **Substitution Economics Analyzer**
   - Live palm/ZL spread, percentile rank, spread regime (tight/normal/wide), historical analog callouts, and mean-reversion vs breakout probability.

5. **Scenario Buttons (“If this→then that”)**
   - Palm +5%, BRL +3%, crude −8%, Brazil drought, Indo quota cut etc. Buttons recalc fair value shift, forecast shift, risk status, explainer snippet.

6. **Confidence & Signal Reliability Meter**
   - Confidence score, historical hit rate for current driver combo, volatility drag, ensemble distribution width, and a “Why lowered/raised?” caption.

7. **Positioning & Flow Intelligence**
   - Market pressure gauge combining CFTC fund deltas, crush rate change, export velocity, front/back roll, short vs long pressure.

8. **Historical Analog Finder**
   - Auto text: “Last 5 times (Vol-High + Palm Up + BRL Weak) → ZL rose 4/5 with avg +2.1% over 20 days.” Confidence boost module.

9. **Procurement Timing Heat Map**
   - Horizon table (1w/1m/3m/6m) with signal, confidence, recommended action (HOLD/SMALL BUY/WAIT/BUY HEAVY) color-coded.

10. **Risk Alerts & Threshold Alarms**
    - Alert engine for palm surge >3 %, BRL vol spike, Indo policy chatter, crush collapse, weather anomaly, regime switch, VIX >30. Each alert explains consequence (e.g., “Palm +3.9 % → substitution pressure ↑ next 5–15 d”).

11. **Narrative Strip**
    - 1–2 sentence auto summary of today’s drivers, shifts, forecast direction, and risk tone (“Mild bullish window: palm strength + weaker BRL vs soft crude; confidence moderate.”).

12. **Procurement Value at Risk (P‑VaR)**
    - Quantifies dollar impact of waiting vs buying now: expected return, vol, position size, risk window → cost avoidance, worst-case slippage, probability-weighted outcomes.

13. **Model Drift Panel**
    - Change log for feature ranks, regime weights, prediction variance vs prior run. Explains “Why did the model change?” for trust.

> When ready to implement, spin up a dedicated dashboard spec covering wireframes, color system, BigQuery views/API endpoints. Use this backlog as the checklist.

---

**Last Updated:** November 17, 2025  
**Status:** Ready for Execution  
**Next Step:** Delete legacy files, start fresh build
