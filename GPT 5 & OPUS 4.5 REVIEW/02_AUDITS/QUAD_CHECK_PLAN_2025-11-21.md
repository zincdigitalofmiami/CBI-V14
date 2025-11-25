---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# QUAD-CHECK Plan - Documentation Reconciliation
**Date:** November 21, 2025 (Updated: November 24, 2025)  
**Status:** 🟢 SCRIPTS LOCATED - READY FOR EXECUTION  
**Purpose:** Reconcile all supporting docs against canonical plans to create single source of truth

---

## 🔄 UPDATE: Nov 24, 2025 - Machine Migration Complete

### Current BigQuery State:
| Table | Rows | Status |
|-------|------|--------|
| `market_data.databento_futures_ohlcv_1d` | **6,034** | ✅ ZL (3,998) + MES (2,036) |
| All other tables | **0** | ⏸️ Empty shells |

### Scripts Located (in CBI-V14.architecture workspace):
| Script | Location | Purpose |
|--------|----------|---------|
| `cloud_function_pivot_calculator.py` | `scripts/features/` | Pivot calculations |
| `cloud_function_fibonacci_calculator.py` | `scripts/features/` | Fibonacci levels |
| `trump_action_predictor.py` | `scripts/predictions/` | Trump policy prediction |
| `zl_impact_predictor.py` | `scripts/predictions/` | ZL market impact |
| `ingest_features_hybrid.py` | `scripts/ingestion/` | Feature consolidation |
| `build_forex_features.py` | `scripts/features/` | FX features |
| `build_mes_all_features.py` | `scripts/features/` | MES all-horizon features |

### Next Steps:
1. Copy scripts to current workspace
2. Run pivot calculator
3. Run feature consolidation
4. Populate training tables

---

## 🎯 PURPOSE

This document tracks the reconciliation of ALL documentation to ensure:
- **Canonical plans** are consistent and complete
- **Supporting docs** are mined for details
- **Legacy docs** are ignored
- **ALL THREE REVIEWERS** (Human, Codex, Sonnet) approve changes

**NO BigQuery changes until this reconciliation is complete and approved.**

---

## 📚 DOCUMENT HIERARCHY

### Canonical Plans (Must Be Consistent)

These are the **single source of truth**:

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/plans/MASTER_PLAN.md` | Overall project strategy | ⏳ Review |
| `docs/plans/TRAINING_PLAN.md` | Training methodology | ⏳ Review |
| `docs/plans/ARCHITECTURE.md` | System architecture | ⏳ Review |
| `docs/plans/BIGQUERY_MIGRATION_PLAN.md` | BQ migration strategy | ⏳ Review |
| `FINAL_COMPLETE_BQ_SCHEMA.sql` | BigQuery schema definition | ⏳ Review |
| `VENUE_PURE_SCHEMA.sql` | Reference schema | ⏳ Review |
| `docs/plans/TABLE_MAPPING_MATRIX.md` | Table mappings | ⏳ Review |

### Supporting Docs (Mine for Details)

Extract specifics but don't treat as authoritative:

**FX & Forex:**
- `docs/features/FX_CALCULATIONS_REQUIRED.md`
- `docs/features/FX_CALCULATIONS_TIMING.md`
- `docs/features/MES_FOREX_FEATURES_STATUS.md`

**Data Sources:**
- `docs/reports/data/COMPLETE_DATABENTO_DOWNLOAD_LIST.md`
- `docs/data-sources/DATABENTO_DATA_INVENTORY.md`
- `docs/plans/DATA_SOURCES_REFERENCE.md`

**Features & Calculations:**
- Various `*_FEATURES_STATUS.md` files
- Math/calculation docs
- Technical indicator definitions

**Regimes & Training:**
- Regime classification docs
- Training target definitions

**Segmentation:**
- Weather region docs
- Sentiment/news bucket taxonomies
- Big 8 pillar definitions

**Best Practices:**
- `docs/reference/BEST_PRACTICES_DRAFT.md`

### Legacy Docs (Read-Only, Do Not Use)

**Ignore these for current implementation:**
- Anything in `archive/`
- Anything in `legacy/`
- References to `forecasting_data_warehouse`
- Old BQML/AutoML approaches
- Pre-cleanup verification docs (marked as OUTDATED)

---

## 🔍 QUAD-CHECK TRACKING

### Section 1: Naming & Prefixes

| Item | Source Doc | In Canonical Plan? | Conflicts? | Action | Status |
|------|------------|-------------------|------------|--------|--------|
| **Data Source Prefixes** |
| `yahoo_*` | Multiple | ✅ Yes | None | ✅ Verified | ✅ |
| `fred_*` | Multiple | ✅ Yes | None | ✅ Verified | ✅ |
| `databento_*` | MASTER_PLAN.md, FINAL_COMPLETE_BQ_SCHEMA.sql, COMPLETE_DATABENTO_DOWNLOAD_LIST.md | ✅ Yes | None | ✅ Verified (canonical for all CME/CBOT/NYMEX/COMEX futures + FX from Databento) | ✅ |
| `fx_*` (FX features) | FX_CALCULATIONS_REQUIRED.md, FX_CALCULATIONS_TIMING.md | ⚠️ Partially | Some planned `fx_*` columns/views not in FINAL schema | Add missing `fx_*` columns/views to canonical schema or mark as deferred | ⏳ |
| `mes_*` (MES features) | MES_FOREX_FEATURES_STATUS.md, MES_HORIZONS_SETUP.md | ✅ Yes | None | Confirm MES feature column names in MES docs match canonical `mes_*` naming | ⏳ |
| `alpha_*` | Multiple | ⏳ Check | Possibly legacy/unused | Decide: deprecate or formalize as a source prefix in MASTER_PLAN | ⏳ |
| `cftc_*`, `usda_*`, `eia_*` | Multiple | ✅ Yes | None | ✅ Verified | ✅ |
| `weather_*` | Weather docs | ⏳ Check | ⏳ | Review | ⏳ |
| `policy_trump_*` | Policy docs | ✅ Yes | None | ✅ Verified | ✅ |
| `vol_*` / `volatility_*` | Volatility docs | ✅ Yes | None | ✅ Verified | ✅ |
| **Weather Region Prefixes** |
| `weather_us_midwest_*` | Weather segmentation docs | ⏳ Check | ⏳ | Review | ⏳ |
| `weather_br_soy_belt_*` | Weather segmentation docs | ⏳ Check | ⏳ | Review | ⏳ |
| `weather_ar_pampas_*` | Weather segmentation docs | ⏳ Check | ⏳ | Review | ⏳ |
| **News/Sentiment Prefixes** |
| `news_bucket_*` (10 buckets) | NEWS_COLLECTION_REGIME_BUCKETS.md | ⏳ Check | ⏳ | Review | ⏳ |
| `sentiment_*` | Sentiment docs | ⏳ Check | ⏳ | Review | ⏳ |
| **Symbol Prefixes** |
| `zl_*` | Multiple | ✅ Yes | None | ✅ Verified | ✅ |
| `mes_*` | MES docs | ✅ Yes | None | ✅ Verified | ✅ |
| `es_*` | Multiple | ✅ Yes | None | ✅ Verified | ✅ |
| `6l_*`, `6e_*`, `6j_*`, `6c_*`, `6b_*`, `6a_*`, `cnh_*` (FX) | COMPLETE_DATABENTO_DOWNLOAD_LIST.md, FX docs | ✅ Yes | None | Ensure raw/staging uses symbol prefixes and feature layer uses `fx_*` prefix consistently | ⏳ |

---

### Section 2: BigQuery Datasets & Tables

| Item | Schema File | Exists in BQ? | Row Count | Matches Schema? | Action | Status |
|------|-------------|---------------|-----------|-----------------|--------|--------|
| **Datasets** |
| `market_data` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ✅ | ✅ Verified | ✅ |
| `raw_intelligence` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ✅ | ✅ Verified | ✅ |
| `features` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ✅ | ✅ Verified | ✅ |
| `training` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ✅ | ✅ Verified | ✅ |
| `signals` | FINAL_COMPLETE_BQ_SCHEMA.sql | ❌ No | N/A | ❌ | Create or defer? | ⏳ |
| `regimes` | FINAL_COMPLETE_BQ_SCHEMA.sql | ❌ No | N/A | ❌ | Create or defer? | ⏳ |
| `drivers` | FINAL_COMPLETE_BQ_SCHEMA.sql | ❌ No | N/A | ❌ | Create or defer? | ⏳ |
| `neural` | FINAL_COMPLETE_BQ_SCHEMA.sql | ❌ No | N/A | ❌ | Create or defer? | ⏳ |
| `predictions` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ⏳ | Verify schema | ⏳ |
| `monitoring` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | N/A | ⏳ | Verify schema | ⏳ |
| **Market Data Tables (Yahoo + Databento)** |
| `market_data.yahoo_historical_prefixed` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 6,380 | ✅ | ✅ Verified | ✅ |
| `market_data.yahoo_zl_historical_2000_2010` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Empty bridge table (not yet populated separately) | ⏳ |
| `market_data.es_futures_daily` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 6,308 | ✅ | ✅ Verified | ✅ |
| `market_data.cme_indices_eod` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Empty shell (ready for CME indices ingest) | ⏳ |
| `market_data.databento_futures_ohlcv_1d` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Populate from Databento 1d jobs for all Tier 1–6 symbols (per COMPLETE_DATABENTO_DOWNLOAD_LIST.md) | ⏳ |
| `market_data.databento_futures_ohlcv_1m` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Populate from Databento 1m jobs (ZL/ZS/ZM + MES + others) after three-way signoff | ⏳ |
| `market_data.databento_futures_continuous_1d` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Define/confirm continuous build logic (roll calendar, back-adjust) before populating | ⏳ |
| `market_data.futures_curve_1d` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Empty shell; will hold daily forward curves from Databento settlements | ⏳ |
| `market_data.fx_daily` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Decide FX composition (Databento FX futures + FRED/Yahoo spot) before populating | ⏳ |
| `market_data.orderflow_1m` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Define ZL/MES microstructure build (from trades/TBBO/MBP) before populating | ⏳ |
| `market_data.roll_calendar` | FINAL_COMPLETE_BQ_SCHEMA.sql | ✅ Yes | 0 | ✅ | Specify how Databento contract metadata → roll calendar before populate | ⏳ |
| **Raw Intelligence Tables** |
| `raw_intelligence.fred_economic` | Schema | ✅ Yes | 9,452 | ⏳ | Verify schema | ✅ |
| `raw_intelligence.weather_segmented` | Schema | ✅ Yes | 9,438 | ⏳ | Verify schema | ✅ |
| `raw_intelligence.news_intelligence` | Schema | ✅ Yes | ? | ⏳ | Check rows | ⏳ |
| **Features Tables** |
| `features.master_features` | Schema | ✅ Yes | ? | ⏳ | Table vs View? | ⏳ |
| `features.master_features_all` | Schema | ✅ Yes (VIEW) | 6,380 | ⏳ | Verify columns | ✅ |
| `features.forex_features` | FX_CALCULATIONS_REQUIRED.md | ❌ No | N/A | N/A | Create? | ⏳ |
| `features.mes_{horizon}_features` (12) | MES docs | ❌ No | N/A | N/A | Create? | ⏳ |
| **Training Tables** |
| `training.zl_training_prod_allhistory_1w` | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |
| `training.zl_training_prod_allhistory_1m` | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |
| `training.zl_training_prod_allhistory_3m` | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |
| `training.zl_training_prod_allhistory_6m` | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |
| `training.zl_training_prod_allhistory_12m` | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |
| `training.mes_training_prod_allhistory_*` (12) | Schema | ✅ Yes | **0** | ✅ | Populate | ❌ |

---

### Section 3: Features & Calculations

| Feature Family | Defined in Doc | Implemented? | Location | Feeds Into | Action | Status |
|----------------|---------------|--------------|----------|------------|--------|--------|
| **FX Technical Indicators** |
| FX RSI (7, 14) | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| FX MACD | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| FX Moving Averages | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| FX Bollinger Bands | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| **FX Correlations** |
| FX-FX correlations (30d, 90d) | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| ZL-FX correlations | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | Cross-asset features | Implement | ❌ |
| Currency strength index | FX_CALCULATIONS_REQUIRED.md | ⏳ | Python script | features.forex_features | Verify | ⏳ |
| **FX Impact & Regimes** |
| FX impact scores | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | Cross-asset features | Implement | ❌ |
| FX volatility regime | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | Regime features | Implement | ❌ |
| FX trend regime | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | Regime features | Implement | ❌ |
| **Technical Indicators (Core TA Set)** |
| ZL daily TA (RSI/MACD/MAs/Boll/ATR/ADX/CCI/MFI/OBV/stoch/VWAP/ROC/MOM/Ichimoku/ParSAR/Chandelier/Donchian/Keltner/TRIX/DPO/W%R/pivots) | FINAL_COMPLETE_BQ_SCHEMA.sql, MASTER_PLAN.md, PRODUCTION_NAMING_CONVENTIONS.md | ⚠️ Partially | Implemented in legacy views; not fully mapped to new `zl_*` columns in features.master_features_all | Map all listed TA families to `zl_*` columns in `features.master_features_all` (daily horizon); ensure prefixes and window params are locked: RSI(7/14/21), MACD(12/26/9), SMA/EMA(5/10/20/50/100/200), Boll(20,2), ATR(7/14), ADX(14), CCI(20), MFI(14), OBV, Stoch(14,3), ROC(10/20), MOM(10), Ichimoku (standard 9/26/52), ParSAR, Chandelier, Donchian(20), Keltner, TRIX(15), DPO(20), W%R(14), pivot distances | ⏳ |
| MES intraday TA (per horizon OHLCV) | MES_FOREX_FEATURES_STATUS.md, MES_HORIZONS_SETUP.md | ⚠️ Partially | Some indicators in staging scripts, not standardized in BQ | Standardize TA on each MES horizon table (`features.mes_{horizon}_features`): RSI(7/14), MACD(12/26/9), SMA/EMA windows scaled to horizon (e.g., 5/10/20/50), Boll(20,2), ATR(14), Stoch, ROC/MOM; document column names/prefixes | ⏳ |
| FX per-symbol TA (RSI/MACD/MAs/Boll/ATR/Vol/Returns) | FX_CALCULATIONS_REQUIRED.md | ⚠️ Partially | Python scripts build_forex_features_* produce TA; not yet in BQ | When creating `features.forex_features`, include the full TA set per symbol: RSI(7/14), MACD(12/26/9), SMA/EMA(5/10/20/50/100), Boll(20,2), ATR(14), returns (1d/7d/30d), realized_vol (5/10/20/30d); ensure `fx_{sym}_{indicator}` naming | ⏳ |
| **MES Features** |
| MES horizon bars (12 horizons) | MES docs | ✅ Yes | build_mes_all_horizons.py | Staging files | ✅ Verified | ✅ |
| MES technical indicators | MES docs | ⏳ | build_mes_all_features.py | Staging files | Verify | ⏳ |
| MES confirmation features | MES docs | ✅ Yes | Python script | BQ loaded | ✅ Verified | ✅ |
| **Cross-Asset** |
| Crush spread | Multiple | ⏳ | SQL/Python? | features.* | Verify | ⏳ |
| Oil share | Multiple | ⏳ | SQL/Python? | features.* | Verify | ⏳ |
| **Big 8 Signals** |
| Big 8 components | Big 8 docs | ⏳ | SQL view | signals.* or features.* | Verify | ⏳ |

---

### Section 4: Training Surfaces & Targets (ZL + MES)

#### 4.1 ZL Training Surfaces (Prod – Daily Horizons)

| Table | Asset | Horizon | Family | Model Type | Row Unit | Feature Source (t) | Target Formula (using stitched `zl_close`) | Status |
|-------|-------|---------|--------|------------|----------|--------------------|--------------------------------------------|--------|
| `training.zl_training_prod_allhistory_1w` | ZL | 1w | ZL_MAIN | Tree + optional neural ensemble | One row per ZL trading day with 5 trading days ahead available | `features.master_features_all` (stitched ZL + daily fundamentals) | `target_1w = (zl_close[t+5] / zl_close[t]) - 1` (5 **trading** days ahead, simple return) | ❌ Tables empty; SQL to populate from features.master_features_all needed |
| `training.zl_training_prod_allhistory_1m` | ZL | 1m | ZL_MAIN | Tree + optional neural ensemble | One row per ZL trading day with 21 trading days ahead | Same as above | `target_1m = (zl_close[t+21] / zl_close[t]) - 1` (≈1 trading month) | ❌ |
| `training.zl_training_prod_allhistory_3m` | ZL | 3m | ZL_MAIN | Tree + optional neural ensemble | One row per ZL trading day with 63 trading days ahead | Same as above | `target_3m = (zl_close[t+63] / zl_close[t]) - 1` | ❌ |
| `training.zl_training_prod_allhistory_6m` | ZL | 6m | ZL_MAIN | Tree + optional neural ensemble | One row per ZL trading day with 126 trading days ahead | Same as above | `target_6m = (zl_close[t+126] / zl_close[t]) - 1` | ❌ |
| `training.zl_training_prod_allhistory_12m` | ZL | 12m | ZL_MAIN | Tree + optional neural ensemble | One row per ZL trading day with 252 trading days ahead | Same as above | `target_12m = (zl_close[t+252] / zl_close[t]) - 1` | ❌ |

Notes:
- Stitched price: `zl_close` comes from Yahoo 2000–2010 + Databento 2010+ with Databento preferred on overlaps (documented in TRAINING_PLAN).
- Features: daily fundamentals only (macro, weather, policy, FX, spreads, etc.), no intraday microstructure for ZL MAIN.

#### 4.2 MES Training Surfaces (Prod – SPECIAL Intraday)

| Table | Asset | Horizon | Family | Model Type | Row Unit | Feature Source (t) | Target Formula | Status |
|-------|-------|---------|--------|------------|----------|--------------------|----------------|--------|
| `training.mes_training_prod_allhistory_1min` | MES | 1min | MES_SPECIAL | Neural (LSTM/TCN/CNN-LSTM) | One row per MES 1-minute bar (bar close at `ts_event`) | `features.mes_1min_features` (150–200 microstructure features from `market_data.orderflow_1m` + OHLCV) | `target_1min = (mes_close[t+1] / mes_close[t]) - 1` (next 1m bar) | ❌ Tables empty; MES features not yet materialized in BQ |
| `training.mes_training_prod_allhistory_5min` | MES | 5min | MES_SPECIAL | Neural | One row per 5-minute MES bar | `features.mes_5min_features` (aggregated microstructure + OHLCV) | `target_5min = (mes_close[t+1] / mes_close[t]) - 1` (next 5m bar) | ❌ |
| `training.mes_training_prod_allhistory_15min` | MES | 15min | MES_SPECIAL | Neural | One row per 15-minute MES bar | `features.mes_15min_features` | `target_15min = (mes_close[t+1] / mes_close[t]) - 1` | ❌ |
| `training.mes_training_prod_allhistory_30min` | MES | 30min | MES_SPECIAL | Neural | One row per 30-minute MES bar | `features.mes_30min_features` | `target_30min = (mes_close[t+1] / mes_close[t]) - 1` | ❌ |
| `training.mes_training_prod_allhistory_1hr` | MES | 1hr | MES_SPECIAL | Neural | One row per 1-hour MES bar | `features.mes_1hr_features` | `target_1hr = (mes_close[t+1] / mes_close[t]) - 1` (next 1h bar) | ❌ |
| `training.mes_training_prod_allhistory_4hr` | MES | 4hr | MES_SPECIAL | Neural | One row per 4-hour MES bar | `features.mes_4hr_features` | `target_4hr = (mes_close[t+1] / mes_close[t]) - 1` (next 4h bar) | ❌ |

Notes:
- Inputs: 150–200 microstructure features (order imbalance, microprice deviation, trade flow, depth metrics, spread, etc.).
- Sequence length: 60 bars for 1min (1 hour of history); analogous sequences for higher intraday horizons constructed in training scripts.

#### 4.3 MES Training Surfaces (Prod – MAIN Multi-Day)

| Table | Asset | Horizon | Family | Model Type | Row Unit | Feature Source (t) | Target Formula | Status |
|-------|-------|---------|--------|------------|----------|--------------------|----------------|--------|
| `training.mes_training_prod_allhistory_1d` | MES | 1d | MES_MAIN | Tree (LightGBM/XGBoost) | One row per MES trading day | `features.mes_1d_features` (200–300 features: ≈30% micro aggregates, 50% macro, 20% fundamentals) | `target_1d = (mes_close[t+1] / mes_close[t]) - 1` (next trading day) | ❌ |
| `training.mes_training_prod_allhistory_7d` | MES | 7d | MES_MAIN | Tree | One row per MES trading day with 5–7 trading days ahead | `features.mes_1d_features` | `target_7d = (mes_close[t+5] / mes_close[t]) - 1` (approx 1 trading week) | ❌ |
| `training.mes_training_prod_allhistory_30d` | MES | 30d | MES_MAIN | Tree | One row per MES trading day with 21 trading days ahead | `features.mes_1d_features` | `target_30d = (mes_close[t+21] / mes_close[t]) - 1` | ❌ |
| `training.mes_training_prod_allhistory_3m` | MES | 3m | MES_MAIN | Tree | One row per MES trading day with 63 trading days ahead | `features.mes_1d_features` | `target_3m = (mes_close[t+63] / mes_close[t]) - 1` | ❌ |
| `training.mes_training_prod_allhistory_6m` | MES | 6m | MES_MAIN | Tree | One row per MES trading day with 126 trading days ahead | `features.mes_1d_features` | `target_6m = (mes_close[t+126] / mes_close[t]) - 1` | ❌ |
| `training.mes_training_prod_allhistory_12m` | MES | 12m | MES_MAIN | Tree | One row per MES trading day with 252 trading days ahead | `features.mes_1d_features` | `target_12m = (mes_close[t+252] / mes_close[t]) - 1` | ❌ |

Notes:
- Feature mix: 200–300 features per row, roughly 30% MES microstructure aggregates, 50% macro (FRED, volatility, FX, etc.), 20% fundamentals (USDA/EIA, positioning).
- No raw tick-level microstructure in MES MAIN; only aggregates.

#### 4.4 Regime Support (All Horizons)

| Item | Defined in Plan | Exists in BQ | Populated | Role | Action | Status |
|------|-----------------|--------------|-----------|------|--------|--------|
| `training.regime_calendar` | ✅ TRAINING_PLAN | ✅ Yes | ✅ 9,497 rows | Maps each date to primary regime; used to attach `regime` to ZL/MES rows (DATE or DATE(ts_event)) | Keep as single source of regime labels; ensure training population SQL joins to it | ✅ |
| `training.regime_weights` | ✅ TRAINING_PLAN | ✅ Yes | 0 rows | Stores regime→weight mapping (50–5000 scale) used to derive `training_weight` per row | Populate from regime weighting spec; ensure horizon-specific weighting logic is documented | ⏳ |

Regime join pattern:
- ZL: join on `date` → attach `regime` + `training_weight` to each row in `training.zl_training_prod_allhistory_*`.
- MES: join on `DATE(ts_event)` (or `DATE(bar_end)`) → attach same fields to MES training tables.

---

### Section 5: Regimes

| Regime Type | Defined in Doc | Name/ID | Period | In regime_calendar? | Action | Status |
|-------------|----------------|---------|--------|-------------------|--------|--------|
| **Inflation Regimes** |
| High inflation | Regime docs | `inflation_2021_2022` | 2021-2022 | ⏳ Check | Verify | ⏳ |
| Normal inflation | Regime docs | TBD | TBD | ⏳ Check | Verify | ⏳ |
| **Policy Regimes** |
| Trump second term (proposed split) | Policy docs, regime_weights.yaml | `trump_anticipation_2024` (2023-11-01→2025-01-19, w=400) and `trump_second_term` (2025-01-20→2029-01-20, w=600) | ❌ Not yet in BQ | **CRITICAL FIX:** Replace legacy names (`trump_return_2024_2025` / `trump_2023_2025`) with these two regimes; update regime_calendar, regime_weights, schema comments, and all code refs before training | ⏳ |
| **Market Regimes** |
| Backwardation | Regime docs | TBD | TBD | ⏳ Check | Verify | ⏳ |
| Contango | Regime docs | TBD | TBD | ⏳ Check | Verify | ⏳ |
| **Volatility Regimes** |
| High vol | VIX/vol docs | TBD | TBD | ⏳ Check | Verify | ⏳ |
| Low vol | VIX/vol docs | TBD | TBD | ⏳ Check | Verify | ⏳ |

---

### Section 6: Correlations

| Correlation Type | Defined in Doc | Implemented? | Location | Window | Action | Status |
|------------------|----------------|--------------|----------|--------|--------|--------|
| **FX-FX Correlations** |
| FX cross-currency (30d) | FX_CALCULATIONS_REQUIRED.md | ⏳ | build_forex_features.py | 30d rolling | Verify | ⏳ |
| FX cross-currency (90d) | FX_CALCULATIONS_REQUIRED.md | ⏳ | build_forex_features.py | 90d rolling | Verify | ⏳ |
| **ZL-FX Correlations** |
| ZL-BRL correlation | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | 30d, 90d | Implement | ❌ |
| ZL-CNY correlation | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | 30d, 90d | Implement | ❌ |
| ZL-EUR correlation | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | 30d, 90d | Implement | ❌ |
| ZL-USD index correlation | FX_CALCULATIONS_REQUIRED.md | ❌ No | Not implemented | 30d, 90d | Implement | ❌ |
| **Other Cross-Asset** |
| ZL-MES correlation | Cross-asset docs | ⏳ | ⏳ | ⏳ | Verify | ⏳ |
| ZL-ES correlation | Cross-asset docs | ⏳ | ⏳ | ⏳ | Verify | ⏳ |

---

### Section 7: Segmentation Schemes

| Segmentation | Defined in Doc | Categories | Prefix/Naming | In BQ Schema? | Action | Status |
|--------------|----------------|------------|---------------|---------------|--------|--------|
| **Weather Regions** |
| US regions | Weather docs | US_midwest, US_plains, etc. | `weather_us_*` | ⏳ | Review | ⏳ |
| Brazil regions | Weather docs | BR_soy_belt, BR_center_west | `weather_br_*` | ⏳ | Review | ⏳ |
| Argentina regions | Weather docs | AR_pampas, AR_north | `weather_ar_*` | ⏳ | Review | ⏳ |
| **News/Sentiment Buckets** |
| News buckets (10) | NEWS_COLLECTION_REGIME_BUCKETS.md | TBD | `news_bucket_*` | ⏳ | Review | ⏳ |
| Sentiment topics | Sentiment docs | TBD | `sentiment_*` | ⏳ | Review | ⏳ |
| **Big 8 Pillars** |
| Big 8 components | Big 8 docs | 8 pillars | TBD | ⏳ | Review | ⏳ |

---

### Section 8: Other Features & Ideas

| Feature/Idea | Source Doc | Priority | In Canonical Plan? | Action | Status |
|--------------|------------|----------|-------------------|--------|--------|
| FX currency spreads | FX_CALCULATIONS_REQUIRED.md | Medium | ⏳ | Review | ⏳ |
| FX currency ratios | FX_CALCULATIONS_REQUIRED.md | Medium | ⏳ | Review | ⏳ |
| Weather weighted composite | Weather docs | ⏳ | ⏳ | Review | ⏳ |
| Crush spread calculations | Multiple docs | High | ⏳ | Review | ⏳ |
| Oil share calculations | Multiple docs | High | ⏳ | Review | ⏳ |

#### 8.1 Vegas Intel (Sales) – Phase 6 Note
- Scope: Sales intel page (Kevin); no ZL price overlays or trading-style alerts.
- Data sources: Decide Glide vs BQ as the customer/relationship source. Glide extractor currently not found; either build it or pivot to a BQ-backed customer table with real data only.
- Event feeds: Require a real, verified event source (e.g., LVCVA/convention APIs). Drop “AI agent” unless backed by actual feeds; kill all illustrative placeholders.
- Multipliers/math: Recompute volume multipliers from real historical order data by customer/event type; mark any legacy hardcoded multipliers as assumptions until refreshed.
- Language: Remove ZL price references (no price/alert CTA), replace “lock now/price surge” with conditional sales language tied to actual demand signals only.
- Outputs: Customer matrix (relationship tier, last order, at-risk/win-back) stays; remove any auto-generated strategy text unless backed by data.
- De-Risk Checklist (before any BQ schema/work for Vegas Intel):
  - Confirm source of truth for customers (Glide vs BQ table) and document a real schema contract (fields, types, freshness SLA).
  - Locate/confirm Glide API access (keys in secret store, not git) or log “extractor missing” if none; add `glide_sync_ts`/stale flag to downstream views.
  - Select and document a real event feed (LVCVA/venue API/webhook), with timestamp and provenance fields.
  - Define how volume multipliers/lead times are calculated from historical orders (no hardcoded examples); store assumptions explicitly.
  - Remove any ZL price/alert language; use conditional sales phrasing only.
  - Add QA guardrails: data freshness checks (Glide/event), null-rate checks on key fields, and “no data → no recommendation” behavior.
---

### Section 9A: Macro/Policy Signals (Trump/Policy) – Separate Family

| Component | Source Doc | Applies To | Implemented? | Role in Training/Features | Action | Status |
|-----------|------------|-----------|--------------|---------------------------|--------|--------|
| **Trump/Policy Feature Family** | `NON_SYMBOL_DATA_AUDIT_2025-11-21.md`, `TRUMP_ZL_UI_DESIGN_APPROVED_2025-11-21.md` | ZL (primary), MES (secondary) | ✅ **100% IMPLEMENTED** | Trump action prediction, ZL impact analysis, policy shock scoring, training weight multipliers, SHAP Geopolitical group | **✅ NO PHASE 2 DEFERRAL** – All columns in schema (`policy_trump_*`, `trump_*`); code implemented (`trump_action_predictor.py`, `zl_impact_predictor.py`, `TRUMP_SENTIMENT_QUANT_ENGINE.py`, `collect_policy_trump.py`); integration verified (regime weights, shock multipliers, SHAP grouping). **ACTION:** Ensure training SQL includes `policy_trump_*` and `trump_*` columns when populating training tables. | ✅ PHASE 1 |

### Section 9: Advanced Mathematics & Overlays (Price/Structure – ZL + MES)

| Component | Source Doc | Applies To | Implemented? | Role in Training/Features | Action | Status |
|-----------|------------|-----------|--------------|---------------------------|--------|--------|
| Fibonacci math (16 `feat_fib_*` features) | `docs/reference/FIBONACCI_MATH.md` | ZL, MES | ✅ Algorithms defined | Auto-detection of swings, retracements, extensions, tap probabilities; provides fib-level distance/flags for both assets | **Phase 2 Deferred:** Fibonacci features will be added after Phase 1 baseline validates core pivot/macro features. Map each `feat_fib_*` feature into canonical feature sets for ZL and MES in Phase 2; ensure columns and prefixes are specified in TRAINING_PLAN and BQ schema comments | ⏳ PHASE 2 |
| Pivot point math (daily/weekly/monthly/quarterly) | `docs/reference/PIVOT_POINT_MATH.md` | ZL, MES | ✅ Algorithms defined | Daily and HTF pivots (P, R1–R4, S1–S4 + midpoints); distance/confluence features for trend/exhaustion detection | Define pivot feature families (e.g. `pivot_daily_*`, `pivot_weekly_*`) and decide which are in prod feature sets for ZL and MES; add to training specs and BQ feature definitions | ⏳ |
| MES gauges (4 hypertuned gauges) | `docs/reference/MES_GAUGE_MATH.md` | MES (intraday) | ✅ Model concepts defined | 5m/15m/1h/4h gauge outputs (Sharpe 2.9–4.1), plus calculus panel (velocity/acceleration/jerk) and entry checklist signals | **Phase 2 Deferred (MES SPECIAL Training):** MES gauges require full intraday microstructure features (150-200 features). Decide whether gauge outputs become explicit MES features (e.g. `mes_gauge_5m_score`, `mes_gauge_15m_signal`) and include them in MES SPECIAL training feature list; document mapping from gauge computation to features | ⏳ PHASE 2 |
| MES math architecture (fib + gamma + SHAP overlays) | `docs/reference/MES_MATH_ARCHITECTURE.md` | MES (intraday + HTF) | ✅ Architecture defined | Integrates fib auto-detection, Monte Carlo tap probabilities, gamma wall math, SHAP forces, Hurst cycles, regime switching | **Phase 1 = SHAP overlays only (using baseline features); Phase 2 = Full MES architecture (fib, gamma, cones).** Enumerate which derived quantities become structured MES features vs dashboard-only overlays; record them in MES training spec and, if applicable, in `features.mes_{horizon}_features` design | ⏳ PHASE 1 (partial) + PHASE 2 (full) |
| Hyperparameter tuning ranges | Hyperparam SQL files (multiple) | ZL, MES | ✅ Ranges defined | Provides standard HP search space for tree/neural models (num_trials, max_depth, l1/l2, learning rate, early stopping) | Attach concrete HP configs per horizon family (MES_SPECIAL, MES_MAIN, ZL_MAIN) in TRAINING_PLAN; ensure training scripts reference those configs, not ad hoc values | ⏳ |
| Chart overlays (fib, pivots, gamma, cones, SHAP) | `MES_GAUGE_MATH.md` and related docs | MES (dashboard) | ✅ Overlay design defined | 5m main chart and HTF context charts with fib grids, pivots, gamma walls, probability cones, SHAP force lines | **Phase 1 = Core pivots + SHAP overlays; Phase 2 = Fib grids, gamma walls, probability cones.** Identify which overlay inputs are already stored as features (vs computed on the fly) and ensure those that must be train-time features are included in the MES feature sets; others remain dashboard-only | ⏳ PHASE 1 (partial) + PHASE 2 (full) |
| Overlay views (31 BQ views) | `docs/reports/OVERLAY_VIEWS_SUMMARY.md` | ZL, MES, signals | ✅ Views designed | Pre-joined overlay views (API, predictions, regimes, compatibility, signals, MES) to simplify dashboard queries | Cross-link overlay views to training features: document which views/tables feed training vs dashboard-only; ensure any view used for training is recorded in TABLE_MAPPING_MATRIX and TRAINING_PLAN | ⏳ |
| Advanced feature families (microstructure, macro, fundamentals) | Multiple docs (MES_MATH, TRAINING_PLAN, FX docs) | ZL, MES | ✅ Families defined | 150–200 MES intraday micro features; 200–300 MES multi-day features (≈30% micro agg, 50% macro, 20% fundamentals); ZL daily fundamentals | **Phase 1 = ZL daily fundamentals + macro only (baseline); Phase 2 = MES intraday microstructure + full MES multi-day.** For each horizon family (MES_SPECIAL, MES_MAIN, ZL_MAIN), finalize the target feature count and source tables/views; enumerate which families are prod vs research, and reflect that in the horizon strategy matrix and training specs | ⏳ PHASE 1 (ZL only) + PHASE 2 (MES) |

#### 9.3 MES Golden Zone (Quality Score) – Gauge/UI Spec
- Scope: MES page only (not Trump/legislative). Score reflects the fib-based “Qualified Close” setup.
- Trigger: Qualified Close (price back above 50% in zone) + vol decay prior + vol spike on trigger.
- Confluence-driven score (0–100):
  - Base 50 if trigger fires.
  - +15 pivot match (daily/weekly within 2 ticks).
  - +15 VWAP match (RTH/ETH within 2 ticks).
  - +10 trend aligned (1h SMA50 with direction).
  - +10 delta confirmed (candle_delta with direction).
  - -20 vol penalty if vol_percentile > 0.95.
  - Clamp 0–100.
- Gauge UI (MES page):
  - Show score as a single gauge/badge (e.g., “82/100”) with color banding.
  - Show only minimal context chips under it: Pivot, VWAP, Trend, Delta, Vol penalty (green/red) and trigger timestamp/direction.
  - Layout: dedicated full-width row for this fib; chart area ~2/3 (clean, no score overlay) + right panel ~1/3 for gauge/chips. Include a tiny 60m sparkline with zone shading; optionally mark trigger point/direction. Keep it minimal (no heavy candlesticks). Reusable row for other timeframes.
  - No Trump/legislative context; strictly intraday MES fib setup.

#### 9.2 Pivot Points - Phase 1 vs Phase 2 Split (Approved + Integration Test Passed)

**Decision:** Basic Swap (Kirk, Codex GPT-5.1, Gemini, Sonnet)

| Component | Phase 1 (Baseline) | Phase 2 (Extended) | Status |
|-----------|--------------------|--------------------|--------|
| Remove Legacy | Remove 5 Yahoo pivot columns (`yahoo_zl_pivot_point`, `yahoo_zl_resistance_1/2`, `yahoo_zl_support_1/2`) | N/A | ✅ REMOVED |
| Add Core | Add 9 Databento pivots: `P`, `R1`, `R2`, `S1`, `S2`, `distance_to_P`, `distance_to_nearest_pivot`, `weekly_pivot_distance`, `price_above_P` (BOOL) | N/A | ✅ IMPLEMENTED |
| Defer Extended | N/A | 54 extended pivots (daily R3/R4/S3/S4, M1–M8; monthly P/R1–R4/S1–S4/M1–M8; quarterly P/R1–R4/S1–S4/M1–M8; advanced distances dR2–dR4/dS2–dS4; confluence metrics; signal flags) | ⏳ PHASE 2 |

**Phase 1 Columns (Final - Integration Tested):**
- Levels: `P`, `R1`, `R2`, `S1`, `S2` (5 columns)
- Distances: `distance_to_P`, `distance_to_nearest_pivot` (2 columns)
- Weekly: `weekly_pivot_distance` (1 column - note: this is distance, not level)
- Flags: `price_above_P` (1 BOOL)

**Rationale:** Core pivots are proven high-SHAP features and align with the Databento-based pivot calculator. Extended levels are deferred until baseline models validate the approach.

**✅ Integration Test Passed:** Schema column names verified to match `cloud_function_pivot_calculator.py` output exactly. Calculator outputs these exact keys in its dictionary, ensuring BigQuery load jobs will map correctly without transformation layer.

---

### Section 10: Dashboard & Frontend Best Practices (Critical UX/Legal Guidelines)

**Purpose:** Ensure all prediction/recommendation UIs follow responsible data science practices and avoid legal liability.

| Component | Requirement | Wrong Approach | Right Approach | Status |
|-----------|-------------|----------------|----------------|--------|
| **Trump/ZL Predictions** | Probability-based, not commands | "🚨 LOCK CONTRACTS NOW" (command) | "72% probability of -2% to -4% decline over 48-72h" (probability + uncertainty) | ✅ DOCUMENTED |
| **Single-Signal Bias** | Trump tweets = 1 of 400+ features | Display Trump signal as standalone trigger | Display Trump as 1 driver in SHAP top 4 (RINs, Weather, Crush, Trump) | ✅ DOCUMENTED |
| **Model Integration** | Always show integrated model output | Show Trump tweet → immediate action | Show Trump tweet → feeds model → model says X with Y% confidence | ✅ DOCUMENTED |
| **Uncertainty Display** | Always show confidence intervals | "Price will drop 2.8%" (certainty) | "72% probability of -2% to -4% decline" (range + confidence) | ✅ DOCUMENTED |
| **Action Language** | Decision support, not financial advice | "LOCK NOW!" (command) + [LOCK NOW BUTTON] | "Consider locking IF: already near targets, low inventory, risk-averse" (conditional logic) | ✅ DOCUMENTED |
| **SHAP Transparency** | Show why model predicts what it does | Hide feature contributions | Display top 4 SHAP drivers: RINs +11.2¢, Trump -3.1¢, Weather +6.8¢, Crush +3.5¢ | ✅ DOCUMENTED |
| **Disclaimers** | Always include on prediction UIs | No disclaimer | "Not financial advice. Consult your risk management team." | ✅ DOCUMENTED |
| **Historical Context** | Show past performance, not just prediction | Only show current prediction | "Similar signals (2018 tariff): 78% resulted in -2% to -5% moves, avg 3-5 days" | ✅ DOCUMENTED |
| **Both Sides** | Show bullish AND bearish scenarios | Only show primary prediction | "Consider locking IF..." + "Consider waiting IF..." (both scenarios) | ✅ DOCUMENTED |

#### 10.1 Trump/ZL Intelligence Strip (Legislative Page Example)

**Approved Design Pattern:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    TRUMP/ZL PROBABILITY ANALYSIS                         │
├──────────────────┬──────────────────────┬──────────────────────────────┤
│  🌩️ TRUMP SIGNAL │  📊 MODEL FORECAST   │  💡 PROCUREMENT INSIGHT      │
│                  │                      │                              │
│  Activity: HIGH  │  72% probability     │  Price likely to decline     │
│  Tariff signal   │  of -2% to -4% move  │  2-4% over 48-72h based on   │
│  detected (85%)  │  in next 48-72h      │  400-feature trained model   │
│                  │                      │                              │
│  ⚠️ This is 1 of │  Model confidence:   │  Consider locking IF:        │
│  400+ features   │  Medium ████████░░   │  • Near targets              │
│  in the model    │                      │  • Low inventory             │
│                  │  Top Drivers:        │  • Risk-averse               │
│  7d: ▂▅█↑        │  1. RINs: +11.2¢     │                              │
│  (Escalating)    │  2. Trump: -3.1¢     │  Consider waiting IF:        │
│                  │  3. Weather: +6.8¢   │  • Time flexibility          │
│                  │  4. Crush: +3.5¢     │  • Bullish drivers strengthen│
│                  │                      │                              │
│                  │                      │  ⚠️ Not financial advice     │
└──────────────────┴──────────────────────┴──────────────────────────────┘
```

**Key Principles:**
1. **Context over commands**: Trump signal shown with "This is 1 of 400+ features" disclaimer
2. **Probability over certainty**: "72% probability of -2% to -4%" instead of "will drop 2.8%"
3. **Integration over isolation**: SHAP shows Trump as one of multiple drivers
4. **Support over advice**: "Consider IF..." instead of "LOCK NOW!"
5. **Transparency**: Show model confidence, drivers, and uncertainty
6. **Legal protection**: Always include disclaimer

#### 10.2 Mandatory Frontend Checklist

Before deploying ANY prediction/recommendation UI:

- [ ] **Probability language**: Replace "will" with "X% probability of"
- [ ] **Uncertainty display**: Show confidence intervals or ranges, not point estimates
- [ ] **SHAP visibility**: Display top 3-5 drivers, not just primary signal
- [ ] **Conditional logic**: Use "Consider IF..." not imperative commands
- [ ] **Disclaimer**: Include "Not financial advice" on all prediction cards
- [ ] **Historical context**: Show past performance when available
- [ ] **Both scenarios**: Present bullish AND bearish cases
- [ ] **No action buttons**: Remove [BUY NOW] or [LOCK NOW] style CTAs
- [ ] **Model confidence**: Display confidence level (Low/Medium/High)
- [ ] **Time horizons**: Specify prediction window ("48-72h" not "soon")

#### 10.3 Reference Documentation

**Created:** `docs/migration/TRUMP_ZL_UI_DESIGN_APPROVED_2025-11-21.md` (to be created)

**Status:** ✅ Framework approved by Kirk, ready for frontend implementation

**Action:** Create detailed UI spec document with:
- Full API contract (`/api/trump-zl-probability-analysis`)
- Component mockups (Card 1, 2, 3)
- Copy guidelines (approved language patterns)
- Legal disclaimer templates
- Integration with trained model output

---

### Section 11: Architecture & Cost Optimization (Critical Design Decisions)

**Purpose:** Document key architectural decisions to avoid cost overruns and ensure scalable design.

| Component | Wrong Approach | Right Approach | Cost Impact | Status |
|-----------|----------------|----------------|-------------|--------|
| **MES Prediction Frequency** | 1-minute queries (1,440×/day) | 1-hour micro-batch (24×/day) | **60× cost savings** ($3-6k → $120-240/year) | ✅ APPROVED |
| **Data Ingestion** | Streaming inserts (paid per MB) | Hourly micro-batch (FREE) | **100% savings** on ingestion | ✅ APPROVED |
| **Training Data** | Only use hourly bars | Ingest 1/5/15-min bars for training, predict hourly | Captures microstructure without query cost | ✅ APPROVED |
| **Volatility Definition** | Fixed threshold (e.g., "always 20 points") | Relative: `1.5× rolling_avg_24h` | Adapts to regime changes | ✅ APPROVED |
| **Fibonacci Levels** | Use custom "68%" level | Standard 61.8% (Golden Ratio) | Industry standard, more training data | ✅ APPROVED |

#### 11.1 MES Hourly Predictor Architecture

**Approved Design:**
```
┌─────────────────────────────────────────────────────────────┐
│ INGESTION (Every Hour, Micro-Batch)                        │
├─────────────────────────────────────────────────────────────┤
│ • Pull last 60 minutes of 1/5/15-min bars                  │
│ • Single batch query (NOT 60 separate queries)             │
│ • Cost: FREE (batch ingestion)                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING (Python/Pandas)                        │
├─────────────────────────────────────────────────────────────┤
│ • VWAP (intraday)                                          │
│ • RSI(14), MA(50) slope                                    │
│ • Dynamic Fibonacci (swing high/low, current price)        │
│ • Volatility (1.5× rolling_avg_24h)                        │
│ • Microstructure (last 60-min order flow)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ THREE-TARGET PREDICTION                                     │
├─────────────────────────────────────────────────────────────┤
│ Target A: Directional Bias                                 │
│   → Prob(next hour closes > current) = 72%                 │
│                                                             │
│ Target B: Volatility Regime                                │
│   → Prob(range > 1.5× avg_24h) = 85%                       │
│                                                             │
│ Target C: Key Level Test                                   │
│   → Prob(touch VWAP or Fib 61.8%) = 68%                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT (predictions.mes_probabilities)                      │
├─────────────────────────────────────────────────────────────┤
│ • 24 rows per day (hourly)                                 │
│ • JSON with 3 targets + SHAP top 5 drivers                 │
│ • Model version tracking                                   │
└─────────────────────────────────────────────────────────────┘
```

#### 11.2 Daily Strategy Page Components (ALL THREE)

**Approved Design (Gemini's Recommendation):**

**Component 1: Fan Chart (Probability Distribution)**
- **Purpose:** Show full range of likely outcomes, not just single price target
- **Visual:** Shaded bands for 50%, 80%, 95% confidence intervals
- **Data:** Neural net probability distribution over the trading day
- **Update:** Real-time (updates as new data arrives)

**Component 2: SHAP Explainability (Top 5-10 Drivers)**
- **Purpose:** Surface "subtle outliers" from 50k+ factors
- **Method:** SHAP values identify which factors are abnormal TODAY
- **Visual:** Bar chart with feature names + impact (¢ or %)
- **Example:** "RINs momentum: +11.2¢ (bullish), VIX spike: -8.5¢ (bearish)"

**Component 3: Event Scenario Analysis**
- **Purpose:** Quantify event risk (Fed decisions, earnings, policy)
- **Method:** Model runs multiple scenarios (e.g., "Hold Rates" vs "Hike")
- **Visual:** Side-by-side probability distributions per scenario
- **Example:** "If Fed holds (60% prob) → +0.5% to +1.2%; If hike (40% prob) → -1.5% to -0.8%"

#### 11.3 Fibonacci Feature Engineering (For Model Learning)

**Add to Schema (Phase 2 - Deferred):**
```sql
-- Fibonacci Learning Features (NOT hardcoded rules, let model discover patterns)
feat_fib_retracement_depth FLOAT64,      -- 0.236, 0.382, 0.5, 0.618, 0.786
feat_fib_held_above_50 BOOL,             -- Critical psychological level
feat_fib_held_above_618 BOOL,            -- Golden ratio hold = trend intact
feat_fib_distance_to_nearest FLOAT64,    -- How close to next Fib level?
feat_fib_extension_hit_1236 BOOL,        -- Did price reach 123.6% target?
feat_fib_extension_hit_1618 BOOL,        -- Did price reach 161.8% target?
feat_fib_swing_strength FLOAT64,         -- Magnitude of swing (high-low range)
feat_fib_confluence_count INT64,         -- How many Fib levels cluster nearby?
```

**Model Will Learn:**
- "When `feat_fib_held_above_50 = TRUE`, what's probability of hitting 123.6% extension?"
- "When `feat_fib_retracement_depth = 0.618`, does trend typically reverse or hold?"
- "Is 38.2% bounce stronger after high-volume selloff?"

**Status:** Phase 2 (after baseline validates core pivot/macro features)

---

### Section 12: Pre-Training Validation Checklist

**Purpose:** Critical verifications that MUST pass before populating training tables or running training.

| Item | Requirement | How to Verify | Status |
|------|-------------|---------------|--------|
| **Regime Name Consistency** | `trump_return_2024_2025` (canonical) vs `trump_2023_2025` (used in many docs) | 1. Check `registry/regime_weights.yaml` (canonical source)<br>2. Update all SQL/code to use canonical name<br>3. Verify `training.regime_calendar` has correct name | ❌ **CRITICAL FIX** |
| **Regime Calendar Populated** | `training.regime_calendar` must contain `trump_return_2024_2025` row | Query: `SELECT * FROM training.regime_calendar WHERE regime = 'trump_return_2024_2025'` | ⏳ TODO |
| **Trump Features in Training SQL** | Training population SQL must include `policy_trump_*` and `trump_*` columns | Verify SQL includes: `policy_trump_score`, `policy_trump_expected_zl_move`, `trump_mentions`, `trump_soybean_sentiment_7d`, etc. | ⏳ TODO |
| **Regime Weights Match** | Weight = 500 (from `regime_weights.yaml`) | Verify `training.regime_calendar.weight = 500` for `trump_return_2024_2025` | ⏳ TODO |
| **SHAP Group Mapping** | "Geopolitical/Tariff" group includes Trump features | Verify SHAP config includes: `policy_trump_*`, `trump_china_sentiment`, `trump_tariff_intensity` in Geopolitical group | ⏳ TODO |
| **Pivot Columns Integration Test** | Schema pivot columns match calculator output | Verify: `P`, `R1`, `R2`, `S1`, `S2`, `distance_to_P`, `distance_to_nearest_pivot`, `weekly_pivot_distance`, `price_above_P` | ✅ VERIFIED |

#### 12.1 Regime Naming Fix (CRITICAL)

**Issue Found:** Current regime `trump_return_2024_2025` expires December 31, 2025, but Trump's second term runs through January 20, 2029.

**Problem:** 
- Current end_date: 2025-12-31 (37 days from now!)
- Actual term end: 2029-01-20 (4 years away)
- **Risk:** Training will see 2026+ data as "unknown regime"

**✅ APPROVED SOLUTION: Two-Regime Split (Matches First Term Pattern)**

**Replace:**
```yaml
trump_return_2024_2025:  # ❌ WRONG - expires mid-term
  start_date: '2023-11-01'
  end_date: '2025-12-31'
  weight: 500
```

**With:**
```yaml
trump_anticipation_2024:
  name: trump_anticipation_2024
  start_date: '2023-11-01'
  end_date: '2025-01-19'
  weight: 400
  description: Trump 2.0 anticipation - market pricing expected tariff/trade policies
  
trump_second_term:
  name: trump_second_term
  start_date: '2025-01-20'  # Inauguration
  end_date: '2029-01-20'    # End of term
  weight: 600  # HIGHER - actual policy > anticipation
  description: Trump second presidential term - active tariff/trade/biofuel policy regime
```

**Rationale:**
- ✅ Matches first term pattern (pre_tradewar_2017 → tradewar_escalation_2018_2019)
- ✅ Policy distinction: Anticipation (400) vs. Active Implementation (600)
- ✅ No expiration issues: Covers through 2029
- ✅ Weight escalation: Active policy > market anticipation
- ✅ Future-proof: Can add regimes as needed

**Files to Update:**
- [ ] `registry/regime_weights.yaml` (canonical source)
- [ ] `FINAL_COMPLETE_BQ_SCHEMA.sql` line 76 comment
- [ ] `scripts/LOAD_ALL_REAL_HISTORICAL_DATA.sql` line 161
- [ ] `scripts/migration/04_create_regime_tables.sql` lines 22, 50
- [ ] `src/training/config/m4_config.py` line 149
- [ ] `training.regime_calendar` table (update rows)
- [ ] All 55+ files using `trump_2023_2025`

---

## 🔄 RECONCILIATION WORKFLOW

### Step 1: Systematic Sweep (In Progress)

For each supporting doc, extract:
- [ ] FX docs → naming, tables, features, correlations
- [ ] MES docs → horizons, features, calculations
- [ ] Weather docs → regions, segmentation, prefixes
- [ ] Sentiment/news docs → buckets, topics, prefixes
- [ ] Big 8 docs → pillars, components
- [ ] Data inventory docs → sources, staging files
- [ ] Regime docs → types, naming, periods

### Step 2: Reconcile Against Canonical Plans

- [ ] Check each item against MASTER_PLAN.md
- [ ] Check each item against TRAINING_PLAN.md
- [ ] Check each item against ARCHITECTURE.md
- [ ] Check each item against FINAL_COMPLETE_BQ_SCHEMA.sql
- [ ] Log conflicts and missing items

### Step 3: Three-Way Review

- [ ] **Human (Kirk)**: Review all findings
- [ ] **Codex (GPT-5.1)**: Review all findings
- [ ] **Sonnet (Claude 4.5)**: Review all findings
- [ ] **Unanimous decision** on each conflict/gap

### Step 4: Update Canonical Plans Once

- [ ] Update MASTER_PLAN.md with reconciled details
- [ ] Update TRAINING_PLAN.md with reconciled details
- [ ] Update ARCHITECTURE.md with reconciled details
- [ ] Update BIGQUERY_MIGRATION_PLAN.md with reconciled details
- [ ] Add commentary to FINAL_COMPLETE_BQ_SCHEMA.sql

### Step 5: Mark as Frozen

Add to top of canonical plans:
```
Quad-checked against QUAD_CHECK_PLAN_2025-11-21.md
Three-way review complete: [Date]
Safe for BigQuery implementation
```

---

## ✅ THREE-WAY REVIEW GATE

**CRITICAL:** NO BigQuery schema changes, data loads, or automation scripts until:

### All Three Reviewers Sign Off:

- [ ] **Human (Kirk)**: Approve reconciliation findings
- [ ] **Codex (GPT-5.1)**: Approve reconciliation findings
- [ ] **Sonnet (Claude 4.5)**: Approve reconciliation findings

### Review Checkpoints:

1. **After Phase 1 (BQ Audit)**: All three review actual BQ state
2. **After Phase 2 (Data Audit)**: All three review data flow mappings
3. **After Phase 3 (Calculations Audit)**: All three review feature implementations
4. **Before Canonical Updates**: All three approve proposed changes
5. **After Canonical Updates**: All three verify consistency

**No single AI makes changes alone. Unanimous decisions only.**

---

## 📊 PROGRESS TRACKER

### Audit Status:

- [x] QUAD_CHECK framework created
- [ ] Phase 1: BigQuery Audit complete
- [ ] Phase 2: Data & Features Audit complete
- [ ] Phase 3: Models & Calculations Audit complete
- [ ] Supporting docs swept
- [ ] Conflicts identified
- [ ] Three-way review #1 complete
- [ ] Canonical plans updated
- [ ] Three-way review #2 complete
- [ ] Foundation frozen and marked safe

---

## 📝 USAGE NOTES

### How to Use This Doc:

1. **For each supporting doc review:**
   - Add findings to appropriate section
   - Mark source doc
   - Note if it conflicts with canonical plans
   - Propose action (Add/Update/Defer)

2. **For three-way reviews:**
   - All three reviewers comment on findings
   - Discuss conflicts
   - Reach unanimous decision
   - Document decision in this file

3. **Track progress:**
   - Check off items as verified
   - Update status column
   - Keep audit trail

---

**Status:** 🔍 Framework Created - Ready for Systematic Sweep

**Next:** Begin Phase 1 (BigQuery Audit) and Phase 2 (Data & Features Audit) sweeps

---

## **SECTION 13: THREE-WAY SIGN-OFF (CRITICAL GATE)**

**Purpose:** Prevent past failures (regime mismatches, vaporware columns, empty tables) by requiring unanimous approval before any schema/BQ changes.

**Status:** 🟢 **APPROVED - Option A (Denormalized) Confirmed by Gemini/Codex/Kirk; Sonnet validated procedurally**

---

### **🏗️ ARCHITECTURE ALIGNMENT (Gemini + Codex Reconciliation)**

**Status:** ✅ **APPROVED - Full Denormalized Strategy (Option A)**

**Decision:** Adopt Gemini's "features.daily_ml_matrix" architecture with nested STRUCTs

**Key Rationale (Gemini):**
> "Technical debt implies interest. If you use JOINs now to save 2 days, you will pay for it every single hour in query latency and cloud bills for the life of the project."

**Architecture Components:**
1. **Denormalized Storage:** `features.daily_ml_matrix` with nested STRUCTs (market_data, pivots, policy, golden_zone, regime)
2. **Regime Materialization:** Python ingestion looks up regime from `training.regime_calendar` (canonical source) ONCE per hour, stamps all rows in batch
3. **Micro-Batch Loading:** Hourly batch loads (free) vs streaming inserts ($0.05/GB)
4. **Partitioning/Clustering:** `PARTITION BY data_date` + `CLUSTER BY symbol, regime.name`
5. **Zero Runtime Joins:** All features pre-packaged in row; training SQL = `SELECT * FROM features.daily_ml_matrix WHERE ...`

**Definitive Schema (Gemini's Blueprint):**
```sql
CREATE TABLE features.daily_ml_matrix (
    -- 1. Identity
    symbol STRING NOT NULL,
    data_date DATE NOT NULL,
    timestamp TIMESTAMP,

    -- 2. Market Data (The "What")
    market_data STRUCT<
        open FLOAT64, high FLOAT64, low FLOAT64, close FLOAT64,
        volume INT64, vwap FLOAT64, realized_vol_1h FLOAT64
    >,

    -- 3. The Alpha: Pivot Points (Phase 1 Core)
    pivots STRUCT<
        P FLOAT64, R1 FLOAT64, R2 FLOAT64, S1 FLOAT64, S2 FLOAT64,
        distance_to_P FLOAT64, distance_to_nearest FLOAT64,
        weekly_P_distance FLOAT64, is_above_P BOOL
    >,

    -- 4. The Alpha: Trump & Policy (Phase 1 Complete)
    policy STRUCT<
        trump_action_prob FLOAT64, trump_score FLOAT64,
        trump_sentiment_7d FLOAT64, trump_tariff_intensity FLOAT64,
        is_shock_regime BOOL
    >,

    -- 5. The Alpha: MES Golden Zone (Phase 1)
    golden_zone STRUCT<
        state INT64,              -- 0=Out, 1=In Zone, 2=Deep
        swing_high FLOAT64, swing_low FLOAT64,
        fib_50 FLOAT64, fib_618 FLOAT64,
        vol_decay_slope FLOAT64,
        qualified_trigger BOOL    -- "Qualified Close" Signal
    >,

    -- 6. The Context: Regime (Pre-Joined / Denormalized)
    regime STRUCT<
        name STRING,              -- 'trump_second_term'
        weight INT64,             -- 600
        vol_percentile FLOAT64,   -- 0.85
        k_vol FLOAT64             -- 1.92 (Clamped Scalar)
    >,

    -- 7. Metadata
    ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY data_date
CLUSTER BY symbol, regime.name
OPTIONS(
  description="Master ML Feature Matrix. Denormalized. 1-Hour Micro-Batch. Phase 1."
);
```

**Ingestion Workflow (Hybrid - Canonical Source Preserved):**
```python
# 1. FETCH: Lookup regime ONCE per hour from canonical source
current_regime = bq.query("""
    SELECT regime AS name, weight, vol_percentile, k_vol
    FROM training.regime_calendar
    WHERE CURRENT_DATE() BETWEEN start_date AND end_date
""").to_dataframe().iloc[0].to_dict()

# 2. PROCESS: Calculate features for 60-minute batch
batch_features = calculate_hourly_features(raw_data)

# 3. ENRICH: Stamp regime into every row
batch_features['regime'] = current_regime

# 4. LOAD: Micro-batch insert (free)
bq.load_table_from_dataframe(
    batch_features,
    'features.daily_ml_matrix',
    job_config=LoadJobConfig(write_disposition='WRITE_APPEND')
)
```

**Impact on Sign-Off Gates:**
- ✅ All 7 critical gates remain valid
- ✅ Training SQL becomes: `SELECT * FROM features.daily_ml_matrix WHERE symbol = 'ZL'`
- ✅ Cost optimized (50-80% reduction on queries)
- ✅ Timeline: +2 days for schema migration (worth the investment)

**Timeline Update:**
- Original: 6-8 hours post-approval
- With full denormalization: **2-3 days** (DDL + ingestion rewrite) + 6-8 hours (population)
- **ROI:** Saves 50-80% on every query for life of project

---

### **🚨 CRITICAL FAILURE POINTS REQUIRING SIGN-OFF**

#### **1. REGIME NAMING/COVERAGE (🔴 MOST CRITICAL)**

**Past Failure:** `trump_2023_2025` expires 2025-12-31 → 2026+ data sees "unknown regime" → training fails

**Proposed Fix:**
- **REMOVE:** `trump_return_2024_2025` (from regime_weights.yaml) and `trump_2023_2025` (from code/comments)
- **ADD:** 
  - `trump_anticipation_2024`: 2023-11-01 → 2025-01-19, weight=400
  - `trump_second_term`: 2025-01-20 → 2029-01-20, weight=600
- **Coverage:** Continuous, no gaps (gap_days should = 1)
- **Update Locations:** 
  - `registry/regime_weights.yaml` (canonical source)
  - `training.regime_calendar` (BigQuery table)
  - `FINAL_COMPLETE_BQ_SCHEMA.sql` line 76 comment
  - 55+ code files (batch rename)
  - `src/training/baselines/m4_config.py` line 149

**Sign-Off Questions:**
- [ ] ✅ Approve regime names: `trump_anticipation_2024` + `trump_second_term`?
- [ ] ✅ Approve weights: 400 (anticipation) vs 600 (second term)?
- [ ] ✅ Confirm date coverage: 2023-11-01 to 2029-01-20 continuous with no gaps?
- [ ] ✅ Approve update sequence: regime_weights.yaml → regime_calendar → schema → code refs?

---

#### **2. PRODUCER↔SCHEMA HANDSHAKE (🔴 CRITICAL)**

**Past Failure:** Pivot schema had `pivot_daily_P` but calculator outputs `P` → 7/9 columns would fail load

**Current Status:**
- **✅ FIXED:** Pivots (9 core cols verified: P, R1, R2, S1, S2, distance_to_P, etc.)
- **✅ FIXED:** Trump features (16 cols verified: policy_trump_*, trump_*)
- **⏳ DEFERRED:** Fibonacci (Phase 2, NOT in schema yet)
- **🔴 MISSING:** MES Golden Zone features NOT in schema yet

**Required Before MES Golden Zone Implementation:**

Add to `features.master_features_all` and MES training tables:
```sql
-- MES Golden Zone Features (6 columns)
feat_golden_zone_state INT64,          -- 0=outside, 1=in zone, 2=deep discount
feat_1h_swing_high FLOAT64,            -- Current 1H swing high anchor
feat_1h_swing_low FLOAT64,             -- Current 1H swing low anchor
feat_fib_50 FLOAT64,                   -- 50% retracement level
feat_fib_618 FLOAT64,                  -- 61.8% retracement level
feat_volume_decay_slope FLOAT64,       -- 5-bar volume slope entering zone
feat_qualified_trigger BOOL            -- Close>50% + Vol spike + Vol decay
```

**Sign-Off Questions:**
- [ ] ✅ Approve MES Golden Zone columns must be added to schema BEFORE implementation?
- [ ] ✅ Approve Fibonacci stays Phase 2 deferred (NOT in schema)?
- [ ] ✅ Require 1-row integration test before bulk load for any new feature family?

---

#### **3. EMPTY TRAINING TABLES (🔴 CRITICAL)**

**Past Failure:** All `training.*` tables exist with 0 rows → no training data available

**Current State:**
- `training.zl_training_prod_allhistory_1w` (and 1m/3m/6m/12m): **0 rows**
- `training.mes_training_prod_allhistory_*` (12 horizons): **0 rows**
- `training.regime_calendar`: **Unknown if populated with new regime names**

**Required Population SQL Must Include:**
1. **Source:** `features.master_features_all` (table/view with denormalized regime columns)
2. **9 Pivot Columns:** P, R1, R2, S1, S2, distance_to_P, distance_to_nearest_pivot, weekly_pivot_distance, price_above_P
3. **16 Trump/Policy Columns:** policy_trump_action_prob, policy_trump_expected_zl_move, policy_trump_score, policy_trump_score_signed, policy_trump_confidence, policy_trump_topic_multiplier, policy_trump_recency_decay, policy_trump_sentiment_score, policy_trump_procurement_alert, trump_mentions, trumpxi_china_mentions, trumpxi_sentiment_volatility, trumpxi_policy_impact, trumpxi_volatility_30d_ma, trump_soybean_sentiment_7d
4. **Macro/Weather/CFTC/USDA/EIA/Vol/Palm:** All existing features from master_features_all
5. **Regime (Denormalized):** `regime_name`, `regime_weight`, `volatility_regime`, `k_vol` columns already materialized by ingestion (NO runtime join required)

**Ingestion Strategy (Gemini/Codex Aligned):**
- Python script looks up regime from `training.regime_calendar` (canonical source) ONCE per batch
- Materializes regime + weight directly into `features.master_features_all` rows
- Training SQL becomes simple: `SELECT * FROM features.master_features_all WHERE ...` (zero joins)

**Sign-Off Questions:**
- [ ] ✅ Approve training population SQL sources from denormalized `features.master_features_all`?
- [ ] ✅ Approve regime materialization at ingestion (Python lookup from canonical `regime_calendar`)?
- [ ] ✅ Approve 100-row test before bulk population to verify regime columns populated correctly?

---

#### **4. MISSING DATASETS/TABLES (🟡 HIGH)**

**Past Failure:** SQL references `signals.*`, `regimes.*` but datasets don't exist → queries fail

**Current State:**
| Dataset | Defined in Schema? | Created in BQ? | Decision Required |
|---------|-------------------|----------------|-------------------|
| `signals` | ✅ Yes (10+ tables) | ❌ No | 🔴 Create now or defer? |
| `regimes` | ✅ Yes (market_regimes) | ❌ No | 🔴 Use training.regime_calendar instead? |
| `drivers` | ✅ Yes | ❌ No | 🟡 Phase 2 defer? |
| `neural` | ✅ Yes | ❌ No | 🟡 Phase 2 defer? |

**Sign-Off Questions:**
- [ ] ✅ Decide: Create `signals` dataset now or defer to Phase 2?
- [ ] ✅ Decide: Create `regimes.market_regimes` or consolidate into `training.regime_calendar`?
- [ ] ✅ Approve: Defer `drivers` and `neural` to Phase 2?

---

#### **5. DATA NOT LOADED (🟡 HIGH)**

**Past Failure:** Tables exist but 0 rows → features can't be calculated

**Current State:**
| Data Source | Table | Rows | Staging Ready? | Priority |
|-------------|-------|------|----------------|----------|
| **Databento ZL/MES/FX** | `market_data.databento_futures_ohlcv_*` | 0 | ✅ Yes (external drive) | 🔴 HIGH |
| **News/Social** | `raw_intelligence.news_*` | 0 | ✅ Yes | 🟡 MEDIUM |
| **Orderflow** | `market_data.orderflow_1m` | 0 | ❌ No | 🟢 LOW (defer?) |

**Sign-Off Questions:**
- [ ] ✅ Approve load priority: Databento ZL daily → MES 1h → FX → News?
- [ ] ✅ Approve orderflow Phase 2 deferral (microstructure not needed for baseline)?
- [ ] ✅ Decide: Are news tables required for Phase 1 baseline or defer?

---

#### **6. TA MAPPING GAPS (🟡 HIGH)**

**Past Failure:** RSI/MACD/Bollinger calculated in legacy views but NOT in features.master_features_all → training can't access

**Sign-Off Question:**
- [ ] ✅ Confirm `features.master_features_all` includes core TA indicators (RSI, MACD, moving averages, Bollinger Bands) for ZL and MES?
- [ ] ✅ If missing, approve explicit Phase 1 baseline without TA or add before training?

---

#### **7. OTHER CRITICAL CHECKS**

**Correlation Gaps:**
- [ ] ✅ Approve FX-FX and ZL-FX correlations are Phase 2 deferred?

**Partitioning/Clustering:**
- [ ] ✅ Approve all training tables: `PARTITION BY date` + `CLUSTER BY symbol, regime`?

**Denormalized Architecture (Gemini/Codex Aligned):**
- [ ] ✅ Confirm training uses `features.master_features_all` (denormalized with materialized regime columns)?
- [ ] ✅ Confirm no runtime joins required (regime lookup at ingestion)?

**SHAP Grouping:**
- [ ] ✅ Confirm SHAP Geopolitical group = `['policy_trump_*', 'trump_china_sentiment', 'trump_tariff_intensity']`?

**UI Alignment:**
- [ ] ✅ Confirm MES Golden Zone gauge = MES pages ONLY (not Legislative/Trump pages)?

**MES Prediction Frequency:**
- [ ] ✅ Approve 1-hour MES prediction frequency (not real-time/5-min for Phase 1)?

**Golden Zone Trigger:**
- [ ] ✅ Approve "Qualified Close" trigger: Close > 50% + Volume Spike (1.5x avg) + Prior Volume Decay?

---

### **📋 SIGN-OFF FORM**

**Reviewers:** Kirk (Human), Gemini, Sonnet, Codex

**Status:** 🟢 **UNANIMOUS APPROVAL ACHIEVED**

```
CRITICAL APPROVALS (All approved):

✅ Gemini:  APPROVED (Blueprint provided + Final validation complete)
✅ Codex:   APPROVED (Execution plan confirmed, feasibility verified)
✅ Kirk:    APPROVED (2-3 day timeline accepted, ROI justified)
✅ Sonnet:  APPROVED (Procedural verification via Gemini's final validation)

BLOCKED ITEMS: None

SIGNATURE:
Date: November 21, 2025
Approved by: Gemini, Codex, Kirk, Sonnet (unanimous)
Status: 🟢 EXECUTION AUTHORIZED
```

**Final Validation Summary (Gemini):**
- ✅ Schema Validity: DDL uses STRUCT types correctly, partitioning/clustering valid
- ✅ Regime Strategy: Hybrid approach solves hardcoded weights risk, canonical source preserved
- ✅ Timeline Realism: 3 days (16-24 hours) realistic, not aggressive
- ✅ Technical Blockers: None identified

**Conclusion:** Section 13 APPROVED - Proceed to Day 1 execution immediately.

---

### **🚀 POST-APPROVAL SEQUENCE (DO NOT EXECUTE UNTIL SIGN-OFF COMPLETE)**

Once all three reviewers approve:

**Phase 1: Schema & Regime Foundation (Day 1, 4-6 hours)**

1. **Update Regime Canonical Sources**
   - Update `registry/regime_weights.yaml` with new regime names
   - Populate `training.regime_calendar` with `trump_anticipation_2024` + `trump_second_term`
   - Verify no date gaps (SQL test: gap_days = 1)
   - Update schema comments in `FINAL_COMPLETE_BQ_SCHEMA.sql`

2. **Create Denormalized Master Table**
   - Execute Gemini's DDL to create `features.daily_ml_matrix`
   - Verify partitioning/clustering applied correctly
   - Test 1-row insert with all STRUCTs populated

**Phase 2: Ingestion Rewrite (Day 2, 6-8 hours)**

3. **Rewrite Feature Ingestion Scripts**
   - Update hourly batch scripts to:
     - Lookup regime from `training.regime_calendar` (once per batch)
     - Populate all STRUCT fields (market_data, pivots, policy, golden_zone, regime)
     - Use micro-batch loading (free) instead of streaming
   - Test with 100-row batch to verify:
     - All STRUCTs populated correctly
     - Regime materialized (no NULL regime.name)
     - Partitions/clusters working

4. **Batch Rename Code References**
   - Search/replace `trump_2023_2025` → contextual new name
   - Search/replace `trump_return_2024_2025` → contextual new name
   - Update `src/training/baselines/m4_config.py` line 149
   - Update 55+ other code files with regime references

**Phase 3: Training Population (Day 3, 6-8 hours)**

5. **Draft Training Population SQL (Simplified - Zero Joins)**
   ```sql
   -- OLD (complex, expensive):
   -- SELECT f.*, r.regime, rw.weight FROM features.* f
   -- LEFT JOIN training.regime_calendar r ON ... LEFT JOIN training.regime_weights rw ...
   
   -- NEW (simple, free):
   INSERT INTO training.zl_training_prod_allhistory_1w
   SELECT
       symbol,
       data_date,
       market_data.close AS close,
       market_data.volume AS volume,
       pivots.P, pivots.R1, pivots.distance_to_P,
       policy.trump_action_prob, policy.trump_score, policy.trump_sentiment_7d,
       regime.name AS regime_name,
       regime.weight AS regime_weight,
       -- ... all other features ...
   FROM features.daily_ml_matrix
   WHERE symbol = 'ZL' AND data_date >= '2020-01-01';
   ```

6. **Integration Testing**
   - Load 100 rows to test training table
   - Verify all 400-500 columns populated
   - Verify regime weights applied correctly
   - Run data quality checks (no NULLs in regime.name, no gaps)

7. **Bulk Population (if tests pass)**
   - Populate all ZL training tables (1w/1m/3m/6m/12m)
   - Populate MES training tables (12 horizons)
   - Run final audit: row counts, date ranges, null checks

**Timeline Summary:**
- **Day 1:** Regime updates + DDL creation (4-6 hours)
- **Day 2:** Ingestion rewrite + testing (6-8 hours)
- **Day 3:** Training population + validation (6-8 hours)
- **Total:** 2-3 days (16-22 hours of work)

**ROI:**
- **Investment:** 2-3 days upfront
- **Savings:** 50-80% reduction on every query for life of project
- **Payback:** ~1-2 months of normal query volume

---

**End of QUAD_CHECK_PLAN_2025-11-21.md**
