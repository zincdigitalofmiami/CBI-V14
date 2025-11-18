# FRESH START MASTER PLAN
**Date:** November 17, 2025  
**Status:** Complete Rebuild - Clean Architecture  
**Purpose:** Single source of truth for new architecture with source prefixing, Alpha Vantage, ES futures, expanded FRED, and a canonical feature table (`master_features_2000_2025.parquet`) that mirrors to BigQuery for Ultimate Signal, Big 8, MAPE, and Sharpe dashboards.

---

## PHILOSOPHY

**"Clean slate, proper architecture, source-prefixed columns, robust data collection"**

- **Source Prefixing:** ALL columns prefixed with source (`yahoo_`, `alpha_`, `fred_`, etc.) - industry best practice
- **Mac M4:** ALL training + ALL feature engineering (local, deterministic)
- **BigQuery:** Storage + Scheduling + Dashboard (NOT training)
- **External Drive:** PRIMARY data storage + Backup
- **Dual Storage:** Parquet (external drive) + BigQuery (mirror)
- **Staging + Quarantine:** No bad data reaches training
- **Declarative joins:** YAML spec with automated tests
- **QA gates:** Block between every phase

---

## DATA SOURCE RESPONSIBILITIES

### Yahoo Finance
**Role:** ZL=F ONLY (prices + ALL 46+ indicators)  
**Provides:**
- ZL=F raw OHLCV
- ZL=F technical indicators (46+): RSI_14, MACD, SMA_5, etc.
- **Prefix:** `yahoo_` on ALL columns except `date`, `symbol`

**Why Only ZL:**
- Alpha Vantage does NOT have ZL futures or ZL indicators
- ZL is primary target asset
- All other symbols from Alpha

---

### Alpha Vantage
**Role:** Everything except ZL  
**Provides:**
- **ES Futures:** S&P 500 E-mini (all 11 timeframes: 5min, 15min, 1hr, 4hr, 8hr, 1day, 3day, 7day, 30day, 3mo, 6mo)
- **Commodities:** CORN, WHEAT, WTI, BRENT, NATURAL_GAS, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM (Palm handled separately via Barchart/ICE feed)
- **FX:** Key currency pairs for ZL model: `USD/BRL`, `USD/CNY`, `USD/ARS`, `EUR/USD`, `USD/MYR` (for Palm)
- **Indices:** SPY, DIA, QQQ, VIX, etc.
- **50+ Technical Indicators:** For ALL symbols (except ZL)
- **Options:** SOYB, CORN, WEAT, DBA, SPY options chains
- **News & Sentiment:** Tagged with symbols/keywords
- **Prefix:** `alpha_` on ALL columns except `date`, `symbol`

**Does NOT Provide:**
- ZL futures (use Yahoo)
- ZL indicators (use Yahoo)
- EIA biofuel data
- USDA agricultural data
- EPA RIN prices
- World Bank pink sheet
- Agency-specific data

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
- More comprehensive (55-60 series vs Alpha's ~10)
- Authoritative (direct from Fed/agencies)
- Free (120 calls/min)
- Alpha does NOT provide more up-to-date feeds

---

### Other Sources (Keep Separate)
- **EIA:** Biofuel production, RIN prices (Alpha doesn't have). Key series must be separated.
  - **Strategy:** Granular wide format by series ID.
  - **Key Series:** Biodiesel production (PADD 1-5), Ethanol production (US total), D4/D6 RIN prices.
  - **Column Naming:** `eia_biodiesel_prod_padd2`, `eia_rin_price_d4`, etc.
- **USDA:** Agricultural reports, export sales (Alpha doesn't have). Key reports must be separated.
  - **Strategy:** Granular wide format by report and field.
  - **Key Reports:** WASDE, Export Sales, Crop Progress.
  - **Column Naming:** `usda_wasde_world_soyoil_prod`, `usda_exports_soybeans_net_sales_china`, `usda_cropprog_illinois_soybeans_condition_pct`, etc.
- **EPA:** RIN prices (if different from EIA)
- **World Bank:** Pink sheet commodity prices (Alpha doesn't have)
- **Palm Oil (Barchart/ICE):** Dedicated palm futures + spot feed continues outside Alpha.  
  - **Prefix:** `barchart_palm_` on price/volume/volatility columns.  
  - **Files:** `raw/barchart/palm_oil/`, staged to `staging/barchart_palm_daily.parquet`.
- **CFTC:** COT positioning data (Alpha doesn't have)
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
- **Source:** Alpha Vantage VIX + realized vol calculations on ZL, palm, ES
- **Raw Files:** `raw/volatility/vix_daily.parquet`, `raw/volatility/zl_intraday.parquet`
- **Staging:** `staging/volatility_daily.parquet` with prefixes `vol_vix_`, `vol_zl_`, `vol_palm_`
- **Features:** `zl_realized_vol_20d`, `palm_realized_vol_20d`, `es_intraday_vol_5d`, `vol_regime`, `vix_level`, `vix_zscore`
- **Usage:** Drives regime detection, Big 8 “VIX stress” pillar, and ES aggregation logic

### Policy & Trump Intelligence
- **Scripts:** `scripts/predictions/trump_action_predictor.py` (Truth Social + policy wires) and `scripts/predictions/zl_impact_predictor.py`
- **Raw/Staging:** `raw/policy/trump_policy_events.parquet` → `staging/policy_trump_signals.parquet`
- **Prefix:** `policy_trump_` (e.g., `policy_trump_action_prob`, `policy_trump_expected_zl_move`, `policy_trump_procurement_alert`)
- **Integration:** Feeds dashboard policy cards and becomes the “Policy Shock” pillar inside `neural.vw_big_eight_signals`
- **Cadence:** Every 15 minutes alongside the Big 8 refresh cycle
- **View Relationship:** `sync_signals_big8.py` writes snapshots to `signals.big_eight_live`, and `neural.vw_big_eight_signals` simply selects from that table so dashboards always read the latest record.

---

## FOLDER STRUCTURE (Clean)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/                    # Immutable source zone
│   │   ├── yahoo_finance/      # ZL=F ONLY
│   │   │   └── prices/commodities/ZL_F.parquet
│   │   ├── alpha/              # Alpha Vantage data
│   │   │   ├── prices/
│   │   │   │   ├── commodities/ (CORN, WHEAT, WTI, etc.)
│   │   │   │   ├── fx/          (USD/BRL, USD/CNY, etc.)
│   │   │   │   └── es_intraday/ (11 timeframes)
│   │   │   └── indicators/
│   │   │       ├── daily/      (50+ indicators per symbol)
│   │   │       └── intraday/   (ES indicators)
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
│   │   ├── alpha_complete_daily.parquet   # All Alpha symbols with alpha_ prefix
│   │   ├── alpha_es_intraday_5min.parquet # ES 5min with alpha_ prefix
│   │   ├── alpha_es_intraday_15min.parquet
│   │   ├── ... (all 11 ES timeframes)
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
│   │   ├── es_training_prod_allhistory_5min.parquet
│   │   ├── es_training_prod_allhistory_15min.parquet
│   │   └── ... (all horizons)
│   │   # Daily exports feed training + BigQuery mirrors, while a separate 15-minute Big 8 lane reads the latest ES/policy/palm signals for dashboard refresh
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
    │   ├── collect_alpha_master.py
    │   ├── collect_fred_expanded.py      # NEW: 55-60 series
    │   ├── collect_es_intraday_alpha.py  # NEW: 11 timeframes
    │   ├── collect_palm_barchart.py      # NEW: dedicated palm feed
    │   ├── collect_volatility_intraday.py # NEW: realized vol snapshots
    │   └── collect_policy_trump.py       # NEW: Trump policy event scraper
    ├── staging/                # raw/ → staging/ (with prefixes)
    │   ├── create_staging_files.py      # Prefixes all sources
    │   └── prepare_alpha_for_joins.py   # Prefixes Alpha data
    ├── assemble/               # staging/ → features/
    │   └── execute_joins.py    # Uses prefixed columns
    ├── features/               # Feature engineering
    │   ├── build_all_features.py        # Daily joins + engineered signals
    │   └── build_es_intraday_features.py # Aggregates intraday ES → daily features + Big 8 snapshots
    └── qa/                     # Validation
```

---

## COLUMN NAMING CONVENTION

### Industry Best Practice: Source Prefix Pattern

**All columns prefixed with source identifier:**
- `yahoo_open`, `yahoo_high`, `yahoo_close`, `yahoo_rsi_14`, `yahoo_macd`
- `alpha_open`, `alpha_high`, `alpha_close`, `alpha_rsi_14`, `alpha_macd`
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

### Phase 1: Core Data (Week 1)
1. **Yahoo:** ZL=F only (prices + all indicators) → `yahoo_` prefix
2. **FRED:** Expand to 55-60 series → `fred_` prefix
3. **Alpha:** ES futures (all 11 timeframes) → `alpha_` prefix
4. **Alpha:** Core commodities (CORN, WHEAT, WTI, etc.) → `alpha_` prefix
5. **Alpha:** 50+ technical indicators for all symbols → `alpha_` prefix
6. **Palm (Barchart/ICE):** Daily palm futures + volatility → `barchart_palm_` prefix

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

11. **add_alpha_enhanced** (Alpha Vantage)
   - Columns: `date`, `symbol`, `alpha_open`, `alpha_high`, `alpha_close`, `alpha_rsi_14`, `alpha_macd`, etc.
   - Join: `on: ["date", "symbol"]`
   - **Note:** ZL rows get NaN for all Alpha columns (Alpha has no ZL data)

**ES Intraday Handling:** `collect_es_intraday_alpha.py` stores all 11 timeframes, `build_es_intraday_features.py` collapses them into daily aggregates (returns, vol, session bias) before the join above. Latest 15-minute snapshots also flow directly to the Big 8 service without waiting for the daily build.

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

### 2. `scripts/staging/prepare_alpha_for_joins.py`
- ✅ Already updated: Prefixes Alpha with `alpha_`
- ✅ Already updated: Handles indicators and prices

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

### 4. `scripts/ingest/collect_alpha_master.py` (NEW)
- Collect ES futures (11 timeframes)
- Collect commodities (CORN, WHEAT, etc.)
- Collect 50+ indicators per symbol
- Rate limiting (75 calls/min - Plan75)
- Manifest tracking

### 5. `scripts/ingest/collect_palm_barchart.py` (NEW)
- Fetch palm futures/spot from Barchart/ICE
- Output `barchart_palm_` prefixed staging file
- Keep cadence aligned with Alpha commodity refresh

### 6. `scripts/ingest/collect_volatility_intraday.py` (NEW)
- Pull VIX + intraday ZL/ES slices for realized vol calc
- Store `volatility_daily.parquet` with `vol_*` prefixes

### 7. `scripts/ingest/collect_policy_trump.py` (NEW)
- Pull Truth Social + policy wires for Trump activity
- Write staging rows consumed by `trump_action_predictor.py`
- Triggered every 15 minutes (same cycle as Big 8 refresh)

### 8. `registry/join_spec.yaml`
- ✅ Already updated: References prefixed columns
- ✅ Already updated: Alpha join notes ZL gets NaN

### 9. `scripts/features/build_all_features.py`
- ✅ Already updated: Detects `alpha_` prefixed indicators
- ✅ Already updated: Uses `yahoo_` indicators for ZL
- ⚠️ **NEW:** Load regime weights from `registry/regime_weights.yaml` (or parquet), drop hard-coded dict
- ⚠️ **NEW:** Incorporate palm, volatility, and policy_trump joins + computed vol regimes
- ⚠️ **NEW:** Compute shock flags/scores (policy/vol/supply/biofuel) and decayed scores; apply capped weight multiplier (≤1000)

### 10. `scripts/features/build_es_intraday_features.py` (NEW)
- Collapse the 11 Alpha ES timeframes into daily ES features before join
- Output: `features/es_intraday_daily.parquet` and latest snapshot for Big 8 lane

### 11. `scripts/sync/sync_staging_to_bigquery.py` (NEW)
- Load staging parquet files into temporary BigQuery tables then MERGE into production landing tables (partition + cluster aware)
- Used for any staging-level mirrors (e.g., weather, palm, policy)

### 12. `scripts/sync/sync_features_to_bigquery.py` (NEW)
- MERGE `features/master_features_*.parquet` + exports into BigQuery `features.master_features` and `training.*` tables
- Reusable helper for ZL + ES exports (avoids WRITE_TRUNCATE)

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
- ✅ MINIMUM 50+ indicators from Alpha
- ✅ ALL columns properly prefixed (except `date`, `symbol`)
- ✅ Shock flags are sparse (target 2–6% of days per type) and scores ∈ [0,1]
- ✅ Post-shock weight cap respected (all `training_weight` ≤ 1000)
- ✅ Alpha news/policy feeds must have monotonic timestamps + symbol whitelist
- ✅ Cross-source sanity checks (spot-check fred_* vs overlapping alpha_* macro where applicable)
- ✅ Join density checks (overall + per-source non-null ratios logged after `execute_joins.py`)

### Validation Scripts:
- `src/utils/data_validation.py` - Core validation framework
- `scripts/validation/final_alpha_validation.py` - Final checkpoint

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
   - Query `INFORMATION_SCHEMA.VIEWS` across every dataset to capture all views that reference the legacy tables (e.g., `forecasting_data_warehouse.soybean_oil_prices`).
   - Use `INFORMATION_SCHEMA.JOBS_BY_PROJECT` (30-day window) to list scheduled queries, CREATE MODEL jobs, Looker/Studio extracts, etc., that read from those tables.
   - Write the results to `docs/migration/bq_dependency_manifest.md`; this becomes the refactor checklist for the cutover.

2. **Create Backup Datasets**
   - For each production dataset, create a timestamped backup (e.g., `cbi-v14.forecasting_data_warehouse_backup_20251118`, `cbi-v14.models_v4_backup_20251118`).
   - These backups live in `us-central1` and provide a rollback path for months.

3. **Snapshot, Don’t Drop**
   - Copy every legacy table into its backup dataset via BigQuery COPY jobs (safer than CTAS).
   - After copying, run verification queries that compare row counts and simple checksums (e.g., `SELECT COUNT(*)`, `SELECT SUM(CAST(x AS INT64))`) between source and backup. Only proceed when every table matches 100%.

4. **Build the Prefixed Architecture in Parallel**
   - Execute the new DDL scripts (stored under `config/bigquery/schemas/`) to create the prefixed tables (`forecasting_data_warehouse.alpha_commodity_daily`, `features.master_features`, `training.zl_training_prod_allhistory_*`, etc.) in `us-central1`.
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
   - Store API credentials (Alpha, ScrapeCreators, etc.) only in `KEYCHAIN_API_KEYS.md` + secure environment variables; BigQuery tables should reference these keys indirectly (no plaintext keys in SQL/DDL). Rotate keys quarterly and update the keychain doc + IAM bindings together.

### Incremental Sync Scripts
- Add `scripts/sync/sync_staging_to_bigquery.py`: reads staging parquet(s) and performs MERGE into BigQuery landing tables (key = date+symbol). Use `WRITE_TRUNCATE` only for first load.
- Add `scripts/sync/sync_features_to_bigquery.py`: MERGE `features/master_features_*.parquet` into `features.master_features` (matching on date & symbol).
- Update `scripts/sync/sync_alpha_to_bigquery.py` to call MERGE helper instead of `WRITE_TRUNCATE`.

**MERGE Pattern Example:**
```sql
MERGE `cbi-v14.features.master_features` T
USING `cbi-v14.tmp.master_features_batch` S
ON T.date = S.date AND T.symbol = S.symbol
WHEN MATCHED THEN UPDATE SET
  yahoo_close = S.yahoo_close,
  alpha_rsi_14 = S.alpha_rsi_14,
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
2. `scripts/ingest/collect_alpha_master.py`
3. `scripts/ingest/collect_palm_barchart.py`
4. `scripts/ingest/collect_volatility_intraday.py`
5. `scripts/ingest/collect_policy_trump.py`
6. `scripts/ingest/collect_fred_expanded.py` + other government feeds (weather, CFTC, USDA, EIA, etc.)
7. `scripts/staging/create_staging_files.py` + `create_weather_staging.py`
8. `scripts/staging/prepare_alpha_for_joins.py`
9. `scripts/features/build_es_intraday_features.py`
10. `scripts/assemble/execute_joins.py`
11. `scripts/features/build_all_features.py`
12. `scripts/sync/sync_features_to_bigquery.py`
13. `scripts/qa/triage_surface.py` + validation suite
14. (Optional) `scripts/sync/sync_features_to_bigquery.py --exports-only` to push finalized training exports

### Daily Incremental Refresh (Once Backfill Complete)
1. Run all ingestion scripts scheduled for that day (per cadence table below)
2. `create_staging_files.py` (promote new raw → staging)
3. `prepare_alpha_for_joins.py` (updates Alpha staging)
4. `build_es_intraday_features.py` (daily aggregation)
5. `execute_joins.py`
6. `build_all_features.py`
7. `sync_features_to_bigquery.py` (MERGE incremental rows)
8. `scripts/qa/pre_flight_harness.py` + `triage_surface.py`

### 15-Minute Big 8 Refresh
1. `collect_es_intraday_alpha.py` (latest snapshots)
2. `collect_policy_trump.py` (Truth Social + policy)
3. `collect_volatility_intraday.py` (incremental)
4. `build_es_intraday_features.py` (latest window only)
5. Materialize latest Big 8 record (SQL view auto-pulls refreshed tables)
6. `scripts/sync/sync_signals_big8.py` (MERGE new timestamp)

Each DAG should be orchestrated with cron or a scheduler (future section) ensuring upstream completes with success status before downstream triggers.

---

## BACKFILL STRATEGY

### Scope
- Historical coverage: 2000-01-01 → present for all daily sources; 2+ years for ES intraday (per Alpha limits).
- Sources: Yahoo ZL, Alpha commodities/FX/indicators, FRED (55-60 series), palm (Barchart), volatility (recomputed from intraday), policy/trump (limited to 2020+ due to availability), weather, CFTC, USDA, EIA.

### Approach
1. **Alpha API Limits:** Plan75 = 75 calls/min. Batch symbols/timeframes to avoid throttling; use retry logic with exponential backoff.
2. **Yahoo Backfill:** Use historical CSV download or yfinance fork to pull 25 years of ZL OHLCV + indicators.
3. **Palm Backfill:** If KO*0 page limits history, iterate contract codes (KOF26, KOM25, etc.) and stitch into one continuous series offline before writing to staging.
4. **ES Intraday:** For older than 2 years, rely on the maximum history Alpha provides; document any gaps and note in feature metadata.
5. **Government Data:** FRED, CFTC, USDA, EIA allow bulk downloads; run once per source to seed raw/bronze folders.
6. **Parallelization:** Run ingestion scripts sequentially per source to respect rate limits, but you can execute independent sources in parallel (e.g., FRED + Yahoo) if system resources allow.
7. **Validation:** After each source backfill, run source-specific QA (row counts, freshness, staleness) before promoting to staging.
8. **Timeline Estimate:** Expect 4-6 hours for Alpha historical pull (depending on symbols × indicators), <1 hour for Yahoo, <30 min for government data, 1-2 hours for palm contract stitching.

### Recovery
- If an API fails mid-backfill, write the failed batch metadata (symbol, timeframe, last successful date) to `quarantine/alpha_backfill_failures.json` and resume later.
- Keep raw snapshots intact so parsers can be re-run without re-hitting the API unless necessary.

---

## EXECUTION TIMELINE

### Week 1: Core Infrastructure
- Day 1-2: Delete legacy MDs/plans, clean up scripts
- Day 3-4: Build new staging scripts with prefixes
- Day 5-7: Build FRED expanded collection (55-60 series)

### Week 2: Alpha Vantage Integration
- Day 1-3: Build Alpha master collection script
- Day 4-5: Collect ES futures (11 timeframes)
- Day 6-7: Collect commodities + indicators + palm feed + volatility snapshots

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
- Day 2: Create prefixed BigQuery tables in `forecasting_data_warehouse`, `training`, `features`, `signals`, `curated` (partition + cluster); copy legacy tables into `*_backup_YYYYMMDD`; lock new schemas in us-central1
- Day 3: Refactor 64 BigQuery views to point at prefixed tables; add MERGE-based sync scripts
- Day 4: Backfill 2000-2019 data into `training.zl_training_prod_allhistory_*` and `features.master_features`; verify row counts and regimes
- Day 5: Replace contaminated CFTC/USDA pulls and migrate remaining US-region datasets into us-central1
- Day 6-7: QA the new schemas, ensure no unprefixed columns remain, and only then start Week 1 tasks

---

## SUCCESS CRITERIA

### Data Collection:
- ✅ Yahoo: ZL=F only, all columns prefixed `yahoo_`
- ✅ Alpha: ES (11 timeframes), commodities, indicators, all prefixed `alpha_`
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
- ✅ ZL rows get NaN for Alpha columns (correct behavior)
- ✅ Other symbols get Alpha data
- ✅ Date range: 2000-2025 (25 years)
- ✅ No cartesian products
- ✅ ES intraday collapsed to daily aggregates before join (no timeframe mismatch)
- ✅ Policy/volatility/palm joins land prior to regime + alpha enrichment

### Feature Engineering:
- ✅ ZL uses Yahoo indicators (`yahoo_rsi_14`, etc.)
- ✅ Other symbols use Alpha indicators (`alpha_rsi_14`, etc.)
- ✅ Custom features calculated for all
- ✅ Regime weights applied (50-1000 scale)
- ✅ Volatility regime + VIX z-scores computed (`vol_*`)
- ✅ Policy shock pillar sourced from Trump predictors (`policy_trump_*`)
- ✅ Shock features present: `shock_*_flag`, `shock_*_score`, decayed variants; final weights capped ≤ 1000

### Training Exports:
- ✅ ZL exports: All horizons (1w, 1m, 3m, 6m, 12m)
- ✅ ES exports: All 11 timeframes
- ✅ All columns properly prefixed
- ✅ Validation certificate generated
- ✅ `master_features_2000_2025.parquet` mirrored to BigQuery and serves as single feed for Ultimate Signal, Big 8 (Big 8 replaces Big 7), and MAPE/Sharpe dashboards

---

**Last Updated:** November 17, 2025  
**Status:** Ready for Execution  
**Next Step:** Delete legacy files, start fresh build
