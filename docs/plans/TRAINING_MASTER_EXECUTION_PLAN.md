# CBI-V14 Master Execution Plan
**Last Updated**: November 15, 2025  
**Status**: ⚠️ Data Verification Complete - Issues Found - Training Blocked  
**Architecture**: Local-First (Mac M4), No Vertex AI, No BQML Training  
**Data Status**: ⚠️ **VERIFICATION AUDIT FINDINGS** (See issues below)

---

## Current Mission

Train the most accurate ZL (soybean oil) forecasting models possible using **25 years of historical data** (2000-2025) with **regime-based weighting** on Apple M4 Mac mini. All training and inference is 100% local. BigQuery is used for storage only.

**Key Updates (November 2025)**:
- **Historical Data Integrated**: 6,057 rows of soybean oil prices (was 1,301)
- **11 Regime Tables Created**: From historical_pre2000 to trump_2023_2025
- **338K+ Pre-2020 Rows Available**: Full market cycle coverage
- **Migration Complete**: New naming convention (Option 3) implemented
- **Regime Weights Optimized**: Research-based, 50-5000 scale

**⚠️ CRITICAL FINDINGS (November 15, 2025 Verification Audit)**:
- **Training tables missing pre-2020 data**: All tables start from 2020, not 2000 (missing 20 years)
- **Regime assignments incomplete**: Only 1-3 unique regimes per table (expected 7+)
- **Critical issue**: `zl_training_prod_allhistory_1m` has 100% placeholder regimes ('allhistory', weight=1)
- **Missing join tables**: `raw_intelligence.commodity_soybean_oil_prices`, `forecasting_data_warehouse.vix_data`
- **✅ Verified**: No 0.5 placeholder pattern in production price data
- **✅ Verified**: Historical data in models_v4 is real (5,236 rows, no placeholders)
- **✅ Verified**: Yahoo Finance data is real (801K rows, 6,227 ZL rows)

**See:** `COMPREHENSIVE_DATA_VERIFICATION_REPORT.md` and `VERIFICATION_ISSUES_FOUND.md` for full details.

### Data Gap Remediation Plan (Pre-Training)
**Timeline**: Days 1-4 post-BigQuery deployment

**Day 1 - Historical Backfill**:
- Yahoo ZL 2000-2010 → `market_data.yahoo_zl_historical_2000_2010`
- DataBento 2010-present → `market_data.databento_futures_*` tables
- Script: `scripts/backfill/load_historical_data.py`
- Owner: Data Engineering

**Day 2 - Regime Assignment**:
- Load 11 regimes → `training.regime_calendar`
- Apply weights (50-5000 scale) → `training.regime_weights`
- Script: `scripts/regimes/populate_regime_tables.py`
- Owner: ML Engineering

**Day 3 - Feature Assembly**:
- Build continuous series from Yahoo + DataBento
- Populate `features.master_features` (400+ columns)
- Script: `scripts/features/build_master_features.py`
- Owner: Feature Engineering

**Day 4 - Validation**:
- Verify date coverage 2000-2025 (no gaps)
- Confirm 11 regime assignments
- Check join density >95%
- Script: `scripts/validation/pre_training_checks.py`
- Owner: QA

---

## Project Architecture (November 2025)

### Local-First Training Architecture

**Storage Layer: BigQuery**
- **Purpose**: Data warehouse, curated views, and dashboard serving
- **Read Access**: Vercel dashboard reads from BigQuery views
- **Write Access**: DataBento live pipeline writes to BigQuery
- **Training Data**: Exported from BigQuery to local Parquet for M4 training
- **Datasets**: 12 canonical datasets (market_data, raw_intelligence, features, training, predictions, monitoring, signals, regimes, drivers, neural, dim, ops)
- **Tables**: 55+ tables including 17 training tables (5 ZL + 12 MES horizons)
- **Status**: ✅ Schema ready, pending deployment

**Compute Layer: Mac M4**
- **Hardware**: Apple M4 Mac mini (16GB unified memory) + TensorFlow Metal GPU
- **Environment**: `vertex-metal-312` (Python 3.12.6)
- **Training**: 100% local (baselines, advanced, regime-specific, ensemble)
- **Inference**: 100% local prediction generation
- **Models**: 60-70 total (sequential training, memory-managed)
- **Cost**: $0 (no cloud compute)
- **Constraints**: Sequential training, FP16 mixed precision, external SSD

**Upload Layer: Python Scripts**
- **Export**: `scripts/export_training_data.py` (BigQuery → Parquet)
- **Upload**: `scripts/upload_predictions.py` (Local predictions → BigQuery)
- **Workflow**: Automated, no manual intervention

**UI Layer: Vercel Dashboard**
- **Purpose**: Read-only UI
- **Data Source**: BigQuery only (predictions.vw_zl_{h}_latest)
- **No Dependencies**: On local models or Vertex AI
- **Status**: Active

**Training**: 100% Local on M4 Mac (no BQML/Vertex AI)
**Data**: BigQuery serves as system of record
**Live Feed**: DataBento → BigQuery → Dashboard

---

## Security & API Key Management

### macOS Keychain Storage (MANDATORY)

**All API keys MUST be stored in macOS Keychain, never in code or environment variables.**

**Keychain Utility**: `src/utils/keychain_manager.py`

**Usage in Python scripts**:
```python
from src.utils.keychain_manager import get_api_key

# Retrieve API key from Keychain
fred_key = get_api_key('FRED_API_KEY')
if not fred_key:
    raise RuntimeError("FRED_API_KEY not found in Keychain. "
                     "Store it using: security add-generic-password -a default -s cbi-v14.FRED_API_KEY -w <key> -U")
```

**Storing keys in Keychain**:
```bash
# Store FRED API key
security add-generic-password -a default -s cbi-v14.FRED_API_KEY -w "your_key_here" -U

# Store NewsAPI key
security add-generic-password -a default -s cbi-v14.NEWSAPI_KEY -w "your_key_here" -U

# Store ScrapeCreators key
security add-generic-password -a default -s cbi-v14.SCRAPE_CREATORS_API_KEY -w "your_key_here" -U
```

**Key Naming Convention**:
- Service name: `cbi-v14.{KEY_NAME}`
- Account: `default` (unless specific account needed)
- Key names: `FRED_API_KEY`, `NEWSAPI_KEY`, `SCRAPE_CREATORS_API_KEY`, `ALPHA_VANTAGE_API_KEY`, etc.

**Migration from Environment Variables**:
- Scripts should use `get_api_key()` from `keychain_manager.py`
- Temporary fallback to `os.getenv()` is allowed during migration but will log warnings
- All new scripts MUST use Keychain only
- No hardcoded keys in source code (zero tolerance)

**Security Benefits**:
- Keys encrypted by macOS Keychain
- No keys in git history or environment variables
- Keys accessible only to user account
- Automatic keychain locking after inactivity

**Required Keys** (store in Keychain):
- `FRED_API_KEY` - Federal Reserve Economic Data
- `NEWSAPI_KEY` - News API for sentiment analysis
- `SCRAPE_CREATORS_API_KEY` - ScrapeCreators social media scraping
- `DATABENTO_API_KEY` - DataBento live CME/CBOT/NYMEX/COMEX futures feed
- Any other external API keys

---

## Training Strategy

### Phase 1: Local Baselines (Current Focus - Enhanced with Historical Data)
Run comprehensive baselines locally on **expanded 25-year dataset** (2000-2025):

**Statistical Baselines**:
- ARIMA/Prophet (now with 25-year patterns)
- Exponential smoothing (validated on 2008 crisis)

**Tree-Based Baselines**:
- LightGBM with DART dropout (trained on all regimes)
- XGBoost with regime weighting (using new regime tables)

**Regime-Specific Models** (NEW):
- Crisis model (253 rows from 2008)
- Trade War model (754 rows from 2017-2019)
- Recovery model (1,760 rows from 2010-2016)
- Pre-Crisis baseline (1,737 rows from 2000-2007)

**Neural Baselines**:
- Simple LSTM (1-2 layers)
- GRU with attention
- Feedforward dense networks

**Baseline Datasets**:
1. Full history (125 years) with regime weighting
2. Trump-era only (2023–2025)
3. Crisis periods (2008, 2020)
4. Trade war periods (2017–2019)

### Phase 2: Regime-Aware Training
- Train specialized models per regime
- Use weighting scheme from `MAC_TRAINING_EXPANDED_STRATEGY.md`:
  - Trump 2.0 (2023–2025): weight ×5000
  - Trade War (2017–2019): weight ×1500
  - Inflation (2021–2022): weight ×1200
  - Crisis (2008, 2020): weight ×500–800
  - Historical (<2000): weight ×50

### Phase 3: Horizon-Specific Optimization

**ZL Horizons** (5 total - Daily forecast horizons only):
- 1 week, 1 month, 3 months, 6 months, 12 months
- Features: Daily features, focus on fundamentals

**MES Horizons** (12 total - Intraday + multi-day horizons):
- **Intraday (minutes):** 1 min, 5 min, 15 min, 30 min (microstructure + orderflow)
- **Intraday (hours):** 1 hour, 4 hours (microstructure + orderflow)
- **Multi-day:** 1 day, 7 days, 30 days (macro + sentiment)
- **Multi-month:** 3 months, 6 months, 12 months (macro + sentiment)

For each horizon:
- Compare all baselines on holdout data
- Select top performer
- Add horizon-specific features
- Fine-tune architecture

### Phase 4: Prediction Upload
- Generate predictions locally for all trained models
- Upload to BigQuery via `scripts/upload_predictions.py`
- Create/update `predictions.vw_zl_{horizon}_latest` views
- Dashboard reads from BigQuery (no Vertex AI endpoints)

---

## Data Strategy (November 2025 Update)

### Table Mapping & Cutover Strategy
**Reference**: See `docs/plans/TABLE_MAPPING_MATRIX.md` for full mapping

**Compatibility During Migration**:
- Old table names → New tables via VIEWS
- Example: `models_v4.production_training_data_1w` → `training.zl_training_prod_allhistory_1w`
- Cutover grace period: 30 days with dual reads
- Script: `scripts/migration/create_compatibility_views.sql`

**Data Flow**:
1. DataBento → `market_data.databento_futures_*`
2. Yahoo Historical → `market_data.yahoo_zl_historical_2000_2010`
3. Feature Engineering → `features.master_features`
4. Training Export → `training.{zl|mes}_training_prod_*`
5. Local M4 reads Parquet exports for training
6. Predictions → `predictions.*` tables
7. Dashboard reads from BigQuery views

### Live Data Integration (DataBento Forward Feed)
- **Source:** DataBento GLBX.MDP3 subscription (CME/CBOT/NYMEX/COMEX)
- **Schemas:** `ohlcv-1m` (primary), aggregated to `ohlcv-1d`, plus forward continuous series
- **Ingestion Path (Local‑First):**
  - `scripts/live/databento_live_poller.py` writes forward-only 1-minute Parquet files to `TrainingData/live/{root}/1m/date=YYYY-MM-DD/`
  - `scripts/ingest/build_forward_continuous.py` produces front-by-volume series in `TrainingData/live_continuous/{root}/1m/date=YYYY-MM-DD/`
  - Optional (if needed later): mirror to BigQuery tables `market_data.databento_futures_ohlcv_1m_live` / `_1d_live`
- **Training Use:**
  - Daily job stitches historical Yahoo/DataBento aggregates with the new live Parquet to extend `features.master_features`
  - Latest daily training exports now include the continuous forward series so models have same-day coverage
  - Dashboard queries will read from BigQuery views powered by these tables (Vercel never hits DataBento directly)
- **Data Quality Gates:** spread-filter (no `symbol` with `-`), tick-size validation per root (`registry/universe/tick_sizes.yaml`), timestamp monotonicity, outlier guards. All enforced before Parquet is written.
- **Coverage:** Phase 1 roots = `ES`, `ZL`, `CL`; Phase 2 adds `ZS`, `ZM`, `NG`, `ZC`, `ZW`, `RB`, `HO`, `GC`, `SI`, `HG`, `MES`.

### New Naming Convention

**Pattern**: `{asset}_{function}_{scope}_{regime}_{horizon}`

**Components**:
- asset: `zl` (soybean oil)
- function: `training`, `feat`, `commodity`, etc.
- scope: `full` (1,948+ features) or `prod` (~290 features)
- regime: `allhistory`, `trump_2023_2025`, `tradewar_2017_2019`, etc.
- horizon: `1w`, `1m`, `3m`, `6m`, `12m`

### Primary Training Tables (NEW)

**Production Surface** (~290-450 features):
- Tables: `cbi-v14.training.zl_training_prod_allhistory_{1w|1m|3m|6m|12m}`
- Features: 275-449 features (varies by horizon)
- Rows: 1,404-1,475 per table
- Date Range: 2020-01-02 to 2025-11-06 (⚠️ **MISSING PRE-2020 DATA**)
- Regimes: Only 1-3 unique regimes (⚠️ **INCOMPLETE** - expected 7+)
- Exports: `TrainingData/exports/zl_training_prod_allhistory_{horizon}.parquet`
- Status: ⚠️ **ISSUES FOUND** - Regime assignments incomplete, missing pre-2020 data

**Full Surface** (1,948+ features):
- Tables: `cbi-v14.training.zl_training_full_allhistory_{1w|1m|3m|6m|12m}`
- Features: All available drivers
- Rows: Same as prod surface (1,404-1,475)
- Date Range: 2020-01-02 to 2025-11-06 (⚠️ **MISSING PRE-2020 DATA**)
- Regimes: Only 1-3 unique regimes (⚠️ **INCOMPLETE**)
- Status: ⚠️ **ISSUES FOUND** - Same issues as prod surface

### MES Training Surfaces (NEW, DataBento Feed)
- **Asset:** MES (Micro E-mini S&P 500, CME)
- **Horizon Set** (12 total - Intraday + multi-day horizons):  
  - **Intraday (minutes):** 1 min, 5 min, 15 min, 30 min  
  - **Intraday (hours):** 1 hour, 4 hours  
  - **Multi-day:** 1 day, 7 days, 30 days  
  - **Multi-month:** 3 months, 6 months, 12 months
- **Data Source:** DataBento GLBX.MDP3 `ohlcv-1m` stream aggregated to required intervals via local Parquet → `features.mes_intraday_*` matrices.
- **Status:** Live capture in progress; historical backfill via DataBento Historical API. Training exports saved alongside ZL under `TrainingData/exports/mes_training_*`.

### Regime Support Tables

**Regime Calendar**:
- Table: `cbi-v14.training.regime_calendar`
- Rows: 13,102 (maps every date 1990-2025 to regime)
- Regimes: 11 total (historical_pre2000 → trump_2023_2025)

**Regime Weights** (Research-Optimized):
- Table: `cbi-v14.training.regime_weights`
- Rows: 11 (one per regime)
- Scale: 50-5000 (100x differential)
- Trump era: 5000 (maximum recency bias)
- Historical: 50 (pattern learning only)
- Research: `scripts/migration/REGIME_WEIGHTS_RESEARCH.md`

### Legacy Tables (Archived, Read-Only)

**Archived to** `archive.legacy_20251114__models_v4__*`:
- `production_training_data_{1w|1m|3m|6m|12m}` (5 tables)
- `trump_rich_2023_2025`
- Crisis and regime tables (4 tables)

**Shim views** (temporary, 30-day grace period):
- `models_v4.production_training_data_{horizon}` → points to new tables

---

## Success Metrics

### Baseline Requirements (Realistic for M4 16GB)
| Metric | Target | Hardware Constraint | Notes |
|--------|--------|---------------------|-------|
| ZL Ensemble MAPE | < 1.5% | Sequential training | Walk-forward validated, 30-35 models |
| MES MAPE (intraday) | < 0.8% | FP16 mixed precision | 1min-4hr horizons (6 horizons), neural nets |
| MES MAPE (multi-day+) | < 1.2% | Sequential training | 1d-12m horizons (6 horizons), tree models |
| Regime detection | > 95% accuracy | LightGBM CPU | Crisis/bull/bear/normal classifier |
| Volatility forecast | < 0.5% MAE | Small models | GARCH + 1 neural model |
| SHAP coverage | > 80% variance | Batch inference | Factor attribution |
| Model count (total) | 65-75 | FP16 sequential | ZL: 30-35, MES: 35-40 models |
| NLP | Inference-only | Pre-trained FinBERT | Fine-tuning requires cloud |
| Memory management | Mandatory | 16GB unified | FP16, session cleanup, external SSD |
| Training strategy | Sequential | One GPU job at a time | Prevent thermal throttling |
| Batch sizes | Optimized | LSTM ≤32, TCN ≤32, Attention ≤16 | Memory-constrained |

### Production Promotion Criteria (Dashboard Integration)
A model qualifies for dashboard production use if:
1. Beats reference BQML MAPE by ≥10% on holdout data (BQML: 0.7-1.3%)
2. R² > 0.95 consistently across validation windows
3. SHAP explanations align with known market dynamics
4. No data leakage (verified via time-based splits)
5. Passes monotonic constraint validation
 6. Passes walk-forward validation (60+ iterations)
7. Regime detection accuracy > 95%

## Idea Generation

Purpose: capture rigorous modeling ideas for ZL forecasting (and scale to the full futures universe) before implementation. These are research proposals, not commitments, and must pass out‑of‑sample gates.

- Model Stack (enterprise)
  - Baselines: LightGBM, CatBoost, ElasticNet (calibrated quantiles for MAPE).
  - Deep TS: Temporal Fusion Transformer (TFT), N‑HiTS/N‑BEATS, TCN (dilated CNNs) for multi‑horizon forecasting.
  - Ensembles: regime‑routed stacking/blending; meta‑learner chooses expert per regime/horizon.
  - Driver cascades: submodels for crude/palm/soy complex (drivers) → feed ZL models with proper lags.

- Research harness (MAs and indicators)
  - Families: SMA/EMA/WMA/KAMA/T3 across {20, 30, 50, 100, 150, 200, 250}.
  - Signals: price vs MA, MA vs MA, distance‑to‑MA (ATR‑normalized), MA slope/ribbon width.
  - TS‑CV: expanding or purged K‑Fold with 10‑day embargo; per‑regime and all‑history.
  - Acceptance gates: OOS IC ≥ 0.03 (p < 0.05) in ≥ 70% folds; conditioned returns > 0 after transaction costs; stable sign by year/regime.
  - Default to SMA(50/100/200) only if research shows no materially better alternative after costs and stability checks.

- Hidden intelligence (primary drivers) — feature family
  - New primary drivers to engineer (lagged and decayed): BRICS/CIPS settlement rails; crush/HVO‑RD margin stress; fertilizer/chemical constraints; river draft/hydrology; port/crane outages; trade finance/insurer repricing; statistical revision patterns (USDA/EPA); satellite NDVI/EVI drift; refinery turnarounds/outages; export lineup anomalies.
  - Engineering: daily event counts/intensity, EWMA decays (30–90d half‑life), 30/60/90‑day lags, regime‑conditional variants, cross‑effects with crude/palm and USD.
  - Staging: prefix `hidden_`; one row per date; tests for continuity, duplicates, and provenance.

- Alpha NEWS_SENTIMENT integration (drivers, not proxies)
  - Aggregate daily by symbol: mean/median sentiment, article count, pos/neg skew, topic‑conditioned scores (economy_monetary, energy_transportation, etc.), 3/7/30‑day trends/z‑scores.
  - Map `ticker_sentiment` to driver symbols and ZL via driver graph; apply ≥ 1‑day lag; prefix `alpha_news_`.

- Dataset builders and trainers (governed)
  - Build per‑horizon/per‑regime matrices with strict lagging and embargo.
  - Trainers: LightGBM/CatBoost with Optuna (pinball/MAE) and TFT/N‑HiTS (quantiles, early stopping).
  - Stackers: blending/stacking with purged validation; regime routing for meta‑learner.

- Evaluation and gating
  - OOS: MAPE, sMAPE, MASE; IC for features vs forward returns; conditioned returns after realistic costs (ticks).
  - Robustness: structural break diagnostics; block‑bootstrap Monte Carlo (10–20‑day blocks, 10k samples) for Sharpe/DD distributions; require stability for promotion.

- Explainability and monitoring
  - SHAP (global + temporal), permutation importance stability, feature drift monitoring.
  - Quarterly re‑validation; demotion path for features/models failing stability gates.

- Implementation notes (when approved)
  - Single source per instrument; no proxies; strict prefix policy; one row per date preserved in joins.
  - ZL is primary; extend methods to the broader futures universe only after ZL passes acceptance gates.

### Hidden Relationship Intelligence Module (HRI) — Spec (Idea Generation)

Scope and role
- Goal: convert cross‑domain, primary drivers into formal, testable daily signals that lead ZL by 1–9 months, feed the hidden correlation dimension of the Big 7 stack, and remain explainable (cause→effect), not black‑box.
- Position in stack: new Tier 5 above existing TIER 1–4 (fundamentals/geo/substitution/technical).

Data architecture (aligned to naming conventions)
- Datasets (existing): `raw_intelligence`, `signals`, `neural`, `api`.
- Raw layer (new tables under `raw_intelligence`):
  - `raw_intelligence.hidden_defense_contracts`
  - `raw_intelligence.hidden_tech_export_controls`
  - `raw_intelligence.hidden_pharma_licensing`
  - `raw_intelligence.hidden_swf_positions`
  - `raw_intelligence.hidden_carbon_markets`
  - `raw_intelligence.hidden_cbdc_corridors`
  - `raw_intelligence.hidden_port_projects`
  - `raw_intelligence.hidden_agri_academic_links`
- Curated cross‑domain views (views, same dataset as appropriate):
  - `vw_hidden_defense_agri_links`, `vw_hidden_tech_agri_links`, `vw_hidden_pharma_agri_links`,
    `vw_hidden_swf_agri_links`, `vw_hidden_carbon_arbitrage`, `vw_hidden_cbdc_trade_corridors`,
    `vw_hidden_port_infrastructure_signals`, `vw_hidden_academic_agri_influence`
- Hidden feature table (daily grain, prefixed):
  - Dataset: `signals`
  - Table: `signals.hidden_relationship_signals`
  - Columns (all prefixed `hidden_` except `date`):
    - `date`
    - `hidden_defense_agri_score`, `hidden_tech_agri_score`, `hidden_pharma_agri_score`
    - `hidden_swf_lead_flow_score`, `hidden_carbon_arbitrage_score`, `hidden_cbdc_corridor_score`
    - `hidden_port_capacity_lead_index`, `hidden_academic_exchange_score`
    - `hidden_trump_argentina_backchannel_score`, `hidden_china_alt_bloc_score`, `hidden_biofuel_lobbying_pressure`
    - `hidden_relationship_composite_score`

Feature engineering (repeatable formulas; examples)
- Defense–agri nexus:
  - Input: defense events (country, date, value/type), ag trade volumes.
  - Score example: sum over countries of intensity_{t−90→t−30} × Δ soy_oil_imports_{t→t+90}.
- Tech export controls:
  - Input: export license events by country; subsequent import shifts.
  - Score example: rolling 6–12m corr_zscore(tech_event_intensity_t, soy_imports_{t+30→t+180}).
- Pharma–agri link:
  - Input: licensing/approvals; FX/trade; GDP scaling.
  - Score example: Σ (pharma_value_{t−60→t}/GDP_c) × Δ soy_exports_{t→t+90}.
- SWF effect:
  - Input: SWF positions in ag/logistics.
  - Score example: ΔSWF_positions_{t−180→t} × future_flow_change_{t→t+180} (validate with Granger tests).
- Carbon arbitrage:
  - Input: carbon prices by region; policy step‑changes.
  - Score example: carbon_spread(EU,Asia)_t × elasticity_for_crush_migration.
- CBDC corridors:
  - Input: corridor announcements/activations.
  - Score example: Σ active_corridor_{t} × Δ soy_flows_{t→t+180} (normalized).
- Ports/dredging capacity:
  - Input: infra contracts, dredging awards, loading equipment orders.
  - Score example: Σ normalized_invest_{t−365→t−180} × %traffic_change_{t→t+365}.
- Academic exchanges:
  - Input: ag MoUs, grants, exchanges.
  - Score example: count_active_MoUs_{t−365→t} × Δ soy_oil_imports_{t→t+365}.
- Trump–Argentina backchannel:
  - Input: US↔AR policy intensity; AR export mix shifts.
  - Score example: composite f(trump_event_intensity_{t−90→t}, shift_AR_exports_{t→t+90}).
- China alternative bloc diplomacy:
  - Input: partnership intensity; import share changes.
  - Score example: Σ partnership_intensity_{t−180→t} × Δ import_share_from_US_{t→t+180} × (−1).
- Biofuel lobbying cascade:
  - Input: PAC spend, pre‑rule dockets, hearings.
  - Score example: scaled_sum(PAC_{t−180→t}, pre_rule_{t−90→t}, hearings_{t−60→t}).

Detection engine and composite
- Lagged correlations: ρ(H_i(t), ZL(t+Δ)) for Δ∈{30,60,90,180}; store `corr_max_i`, `lag_at_corr_max_i`, `p_value_i`.
- Granger layer: monthly frequency on selected pairs; store `granger_predictive_i`, `best_lag_i`.
- Anomalies: rolling z‑scores; flag `hidden_i_zscore_t > 2.0`.
- Composite: `hidden_relationship_composite_score` = weighted sum of hidden z‑scores using `policy_impact_score` and `source_reliability_score` from the enhanced metadata layer.

UI/visualization hooks
- Graph: nodes (ZL, palm, soy, regions), hidden domains; edges weighted by corr×sign(lag) with Granger flags.
- Views: “current hidden regime” (top 3 active); composite vs ZL trend chart.

Governance & tests
- Prefix policy: all columns `hidden_`; joins preserve one row/day; strict lagging (no leakage).
- Tests: continuity (≤0.5% missing weekdays), no duplicate dates, schema stability; audit trail raw→feature.

### Integration Into Ultimate Signal Architecture (Idea Generation)

Extend comprehensive signal universe (Tier 5)
- Add a CTE sourcing from `signals.hidden_relationship_signals`, then left join by `date` in `vw_comprehensive_signal_universe` to expose:
  - `hidden_relationship_composite_score`, key domain scores (e.g., `hidden_trump_argentina_backchannel_score`, `hidden_china_alt_bloc_score`, `hidden_biofuel_lobbying_pressure`).

Upgrade Big 7 / hidden correlation dimension
- In `vw_big_seven_signals`, define:
  - `feature_hidden_correlation = SAFE_DIVIDE(hidden_relationship_composite_score, NULLIF(stddev_hidden_relationship_composite_score_rolling_1yr, 0))`.
  - `correlation_override_flag = (feature_hidden_correlation > 1.5)`.

Neural training inputs
- In `neural.comprehensive_weight_training`, include hidden features:
  - `hidden_relationship_composite_score` and component scores listed above.
  - Interactions (examples):
    - `hidden_china_alt_bloc_score * china_trade_tension_index AS china_bloc_tension_interaction`
    - `hidden_biofuel_lobbying_pressure * us_rfs_mandate_change_expected AS biofuel_policy_interaction`
    - `hidden_cbdc_corridor_score * usd_index_level AS fx_cbdc_interaction`

Ultimate adaptive predictor
- Pass hidden features and interactions into `neural.ultimate_adaptive_predictor` alongside existing Tier 1–4 composites and Big 4 features.

API layer & explainability
- In `api.vw_ultimate_adaptive_signal`, extend `primary_signal_driver`:
  - If `correlation_override_flag` then 'Hidden relationships driving signal'.
- Add `hidden_primary_domain` for dashboard clarity using domain thresholds (e.g., >1.5 z‑score → biofuel_lobbying/defense_agri/china_alt_bloc/etc.).

Metadata & governance
- Register each hidden feature in the enhanced metadata table with:
  - `policy_impact_score`, `source_reliability_score`, `related_futures_contract`, and key countries.
- Quarterly re‑validation; demotion path for unstable features; documentation of acceptance gates and drift.

### GPT-Based News Classification System for ZL Intelligence (Idea Generation)

**Status**: Ready-to-implement spec (not yet executed)  
**Purpose**: Feed headlines/articles into GPT to extract structured, ZL-focused intelligence for Hidden Relationship Intelligence Module

**Integration Path**: ScrapeCreators → BigQuery → `news_intelligence` → `hidden_relationship_signals`

**System Architecture**:

1. **Classification Model** (GPT-based)
   - **System Prompt**: Agricultural geopolitics and commodities intelligence analyst focused on ZL (soybean oil), soybeans, and competing vegetable oils
   - **Input**: Single news item (headline + snippet/short article)
   - **Output**: Structured JSON analysis with 12 fields (see schema below)
   - **Classification Axes**:
     - Primary topic (40 categories matching institutional keyword matrix)
     - Hidden relationships (17 cross-domain drivers-of-drivers)
     - Region focus (12 geographies)
     - Relevance, direction, strength, timing, mechanism

2. **User Prompt Template**
   ```
   HEADLINE: {{headline_text}}
   SOURCE: {{source_name}}
   DATE: {{iso_date_if_known_or_null}}
   BODY: {{short_snippet_or_article_text}}
   ```

3. **Output JSON Schema** (12 fields)
   - `primary_topic`: One of 40 categories (biofuel_policy, palm_policy, china_demand, us_policy_trump, brazil_argentina_crop_logistics, weather_agriculture, biofuel_lobbying, sovereign_wealth_funds, carbon_markets_eudr, shipping_chokepoints, defense_agri_nexus, pharma_agri_link, cbdc_trade_corridor, port_infrastructure, academic_agri_links, farm_bill_usdomestic, crush_margins_processing, fx_macro, food_security, freight_rates, fertilizer_energy_inputs, us_china_tension, gmo_agrochemical_policy, black_sea_war, labor_strikes_logistics, renewable_diesel_capacity, tanker_dynamics, inflation_rates_liquidity, spec_positioning, risk_off_vix, shipping_insurance, port_throughput, lgfv_china_finance, soybean_disease_pests, energy_markets, infra_failures, credit_crunch, elections_political_instability, digital_traceability, other)
   - `hidden_relationships`: Array of drivers-of-drivers (defense_agri_nexus, tech_export_agri_link, pharma_agri_link, sovereign_wealth_fund_effect, carbon_market_arbitrage, cbdc_corridor_effect, deep_water_port_intel, educational_exchange_trade_nexus, trump_argentina_backchannel, china_alt_bloc_diplomacy, biofuel_lobbying_chain, offshore_finance_shells, telecom_infrastructure_loyalty, agri_mercenary_corridor, water_rights_shift, esg_rating_drift, none)
   - `region_focus`: Array of geographies (us, brazil, argentina, china, eu, southeast_asia, india, black_sea, middle_east, africa, latin_america_other, global, other)
   - `relevance_to_soy_complex`: Integer 0-100 (0-20: almost irrelevant, 21-40: weak, 41-60: moderate, 61-80: high, 81-100: very high)
   - `directional_impact_zl`: One of (bullish, bearish, neutral, mixed, unknown)
   - `impact_strength`: Integer 0-100 (how big the impact if it plays out)
   - `impact_time_horizon_days`: Approximate days until main price effect (e.g., 7, 30, 90, 180)
   - `half_life_days`: How long effect persists before decaying ~50% (e.g., chokepoint disruptions = 7-21, policy shifts = 90-365)
   - `mechanism_summary`: 1-3 sentences explaining causal chain from news → ZL (explicit about palm vs soy, China vs US origin, biofuel vs food)
   - `direct_vs_indirect`: One of (direct, indirect, hidden)
   - `subtopics`: Array of finer-grained labels (rfs_saf_lcfs, palm_export_tax, dalian_futures, china_state_reserves, argentina_export_tax, port_strike, truck_blockade, mississippi_draft, el_nino, heatwave, flooding, gmo_ban, glyphosate, carbon_credit, deforestation_compliance, sanctions, naval_protection, cbdc_settlement, digital_yuan, swf_equity_stake, academic_mou, 5g_infrastructure, pharma_license, vaccine_deal, credit_tightening, refinery_conversion, renewable_diesel, fertilizer_sanctions, black_sea_corridor, soydollar, exchange_rate_shock, lgfv_default, esg_downgrade, election_result, farm_bill, food_security_law, none)
   - `confidence`: Integer 0-100 (confidence in classification)

4. **Domain Knowledge Rules** (embedded in system prompt)
   - Biofuel mandates, SAF credits, LCFS tightening → BULLISH ZL (higher feedstock demand)
   - Palm oil export taxes/bans, Indonesia/Malaysia supply issues → BULLISH ZL via substitution
   - Chinese demand (state reserves, crush margins, Dalian futures) → major drivers
   - Brazil/Argentina weather, logistics, strikes, policy → supply drivers → ZL responds
   - Hidden channels (defense deals, tech controls, pharma licensing, SWF investments, CBDC corridors, port projects, academic MoUs, biofuel lobbying) → trade flow changes by 3-9 months
   - FX shocks, credit constraints, geopolitical risk, sanctions, ESG restrictions → affect soy/palm movement

5. **BigQuery Integration**
   - **Storage**: `raw_intelligence.news_intelligence` / `news_advanced`
   - **Schema**: Map JSON fields 1:1 to BigQuery columns or JSON field
   - **Aggregation** (daily):
     - Bullish/bearish sentiment by topic
     - Hidden driver intensity per day (e.g., `biofuel_lobbying_chain`)
     - Time series: `hidden_biofuel_lobbying_pressure`, `hidden_china_alt_bloc_score`, etc. from counts/weights
   - **Feeds Into**:
     - `hidden_relationship_signals` table
     - `feature_hidden_correlation` and `correlation_override_flag` in Big 7 / Ultimate Signal

6. **Implementation Options** (when approved)
   - **Option A**: BigQuery UDF (accepts headline, body, returns JSON)
   - **Option B**: Python script (processes articles, writes to BigQuery)
   - **Option C**: Hybrid (Python for complex logic, BigQuery for aggregation)

7. **Test Cases** (ready-to-use examples)
   - **Example 1 - Biofuel Lobbying**: "U.S. biofuel lobby pushes for aggressive SAF tax credit expansion" → Expected: `primary_topic: "biofuel_lobbying"`, `hidden_relationships: ["biofuel_lobbying_chain"]`, `directional_impact_zl: "bullish"`, `impact_time_horizon_days: 60`
   - **Example 2 - CBDC Corridor**: "China and Brazil launch direct digital yuan–real settlement corridor" → Expected: `primary_topic: "cbdc_trade_corridor"`, `hidden_relationships: ["cbdc_corridor_effect", "china_alt_bloc_diplomacy"]`, `directional_impact_zl: "bearish"`, `impact_time_horizon_days: 90`

**Next Steps** (when ready to implement):
1. Convert to BigQuery UDF spec OR design Python processing script
2. Design aggregation logic (dozens of JSON records per day → `hidden_relationship_composite_score` and per-domain hidden scores)
3. Integrate with existing ScrapeCreators → BigQuery pipeline
4. Wire into `hidden_relationship_signals` table and Big 7 / Ultimate Signal architecture

8. Predictions upload successfully to BigQuery
9. Dashboard can read from `predictions.vw_zl_{horizon}_latest`

**Note**: All models run locally. "Production" = uploaded to BigQuery for dashboard consumption.

---

## File Organization

### Training Scripts
- `src/training/baselines/` - Statistical/tree/simple neural baselines
- `src/training/regime_classifier.py` - Automatic regime detection
- `src/training/regime_models.py` - Crisis/bull/bear/normal specialists
- `src/training/walk_forward_validation.py` - True out-of-sample testing
- `vertex-ai/training/` - Advanced neural architectures

### Prediction & Monitoring
- `src/prediction/shap_explanations.py` - Factor attribution per prediction
- `src/prediction/ensemble_predictor.py` - Regime-aware ensemble
- `src/prediction/uncertainty_quantification.py` - Conformal prediction
- `src/prediction/news_impact_model.py` - FinBERT NLP integration
- `src/prediction/feature_drift_tracker.py` - Importance drift detection
- `scripts/daily_model_validation.py` - Predictions vs actuals
- `scripts/performance_alerts.py` - Email alerts on degradation
- `scripts/correlation_monitoring.py` - Correlation breakdown detection

### Analysis & Backtesting
- `src/analysis/backtesting_engine.py` - Strategy validation
- `src/api/explain.py` - SHAP explanations (dev tool)
- `src/api/backtest.py` - Strategy backtesting (dev tool)
- `src/api/validate.py` - Daily model validation (dev tool)
- `src/api/monitoring.py` - Performance tracking (dev tool)
- `src/deployment/ab_testing.py` - Shadow mode deployment

### Production Dashboard APIs
- `dashboard-nextjs/app/api/forecast/[horizon]/route.ts` - Production predictions
- `dashboard-nextjs/app/api/market/intelligence/route.ts` - Real-time signals
- `dashboard-nextjs/app/api/predictions/route.ts` - All horizons
- `dashboard-nextjs/app/api/regime/current/route.ts` - Regime detection

### Trained Models
- `Models/local/baselines/` - Local baseline artifacts
- `Models/local/{horizon}/` - Horizon-specific models
- `Models/vertex-ai/` - SavedModels for Vertex deployment
- `Models/mlflow/` - MLflow experiment tracking

### Training Data
- `TrainingData/raw/` - Raw exports from BigQuery
- `TrainingData/processed/` - Preprocessed/engineered features
- `TrainingData/exports/` - Ready-to-train Parquet files
- `TrainingData/precalc/` - Mac-side precalc bundle (`surfaces/`, `metrics/`, `regimes/`, `logs/`, `qc/`)

### Documentation
- `active-plans/` - This file + related execution plans
- `docs/training/` - Training reports, analysis
- `docs/data/` - Data manifests, schemas

---

## Current Execution Plans (Reference)

1. **VERTEX_AI_TRUMP_ERA_PLAN.md** - Vertex AI AutoML + neural pipeline architecture
2. **TRUMP_ERA_EXECUTION_PLAN.md** - BQML DART production training
3. **MAC_TRAINING_SETUP_PLAN.md** - M4 Mac setup and environment
4. **MAC_TRAINING_EXPANDED_STRATEGY.md** - Multi-model ensemble strategy
5. **MASTER_EXECUTION_PLAN.md** - This file (overview)

---

## Migration Status (November 14, 2025)

### ✅ Completed: Naming Architecture Migration

**Achievement**: Migrated entire system to institutional naming convention (Option 3)

**Phases Complete**:
- Phase 1: Archive (10 tables preserved)
- Phase 2: Datasets (7/7 verified)
- Phase 3: Training Tables (12/12 created with new naming)
- Phase 4: Python Scripts (15/15 updated)
- Phase 6: Shim Views (5/5 backward compatibility)

**Key Deliverables**:
- ✅ New naming: `{asset}_{function}_{scope}_{regime}_{horizon}`
- ✅ Regime weights: 50-5000 (research-optimized)
- ✅ Upload pipeline: `scripts/upload_predictions.py`
- ✅ Documentation: 4 institutional framework documents
- ✅ Architecture: 100% local-first verified

**Documentation**: `docs/migrations/20251114_NAMING_ARCHITECTURE_MIGRATION.md`

### ✅ Completed: Institutional Quant Framework

**Achievement**: Established professional methodology for signal interpretation and forecasting

**Documents Created**:
1. `CONVICTION_VS_CONFIDENCE.md` - Separates directional certainty from forecast precision
2. `SIGNAL_TREATMENT_RULES.md` - 12 institutional guidelines for market signals
3. `CURSOR_MASTER_INSTRUCTION_SET.md` - Mandatory post-move audit protocol
4. `INSTITUTIONAL_FRAMEWORK_INDEX.md` - Central navigation

**Key Insights**:
- Crisis = high conviction (direction) + low confidence (precision)
- Signals must be paired, validated, contextualized
- Post-move audits mandatory (VIX >25, USD/BRL >3%, etc.)

**Documentation**: `docs/reference/` + `INSTITUTIONAL_FRAMEWORK_COMPLETE.md`

---

## 7-Day Institutional Production System Execution Plan

**Timeline**: 65 hours over 7 days (9-10 hours/day)  
**Goal**: Complete institutional-grade forecasting system with zero deferrals  
**Current Status**: Migration complete (Day 0), ready to start Day 1

---

### Day 1: Foundation & Data Quality (6 hours)

**Morning (3h)**: Reorganization & Data Exports
- ✅ Commit repository reorganization (622 files)
- **Data quality validation BEFORE exports** - catch bad data early
- Export `trump_rich_2023_2025.parquet` (42 features, 782 rows)
- Export all 5 `production_training_data_{1w|1m|3m|6m|12m}.parquet` (290 features)
- Export full historical dataset (125 years) with regime labels
- Export 5 regime-specific datasets (trump_2.0, trade_war, inflation, crisis, historical)

**Afternoon (3h)**: Infrastructure Setup
- Configure MLflow tracking → `Models/mlflow/`
- **Set up Metal GPU acceleration** (enables all training)
- Create experiment structure (baselines_statistical, baselines_tree, baselines_neural, regime_models)
- Test GPU + logging with dummy run

**Scripts Created**:
- `scripts/data_quality_checks.py` - validate before training
- `scripts/export_training_data.py` - automated exports

**Deliverable**: Clean repo committed, all data exported, GPU + MLflow operational

---

### Day 2: Baselines + Volatility (7 hours)

**Setup (15min)**: GPU Optimization + Memory Management
- Enable Metal GPU with FP16 mixed precision (MANDATORY for 16GB RAM)
- Configure gradient checkpointing and memory cleanup
- Set batch sizes: Trees unlimited, LSTM ≤64, attention ≤16
- External SSD for all checkpoints/logs

**Track A (2h)**: Statistical Baselines (CPU, sequential)
- ARIMA/Prophet on 1w, 1m, 3m (Day 2)
- Complete 6m, 12m on Day 4 (stagger to avoid heat)
- Log to MLflow: MAPE, R², residuals
- Count: 10-12 statistical models

**Track B (2h)**: Tree-Based Baselines (CPU, 8-10 threads)
- LightGBM DART: 3-4 configs per horizon, 1w/1m/3m first
- XGBoost DART: 2 configs per horizon
- Complete 6m/12m on Day 4
- Count: 8-10 tree models (Day 2), 4-6 more (Day 4)

**Track C (1.5h)**: Simple Neural Baselines (GPU, sequential)
- 1-layer LSTM, 1-layer GRU, Feedforward Dense
- Train 1w, 1m only on Day 2 (test Metal performance)
- Complete 3m/6m/12m on Day 3-4
- Clear Keras session after each model (memory management)
- Count: 6 simple neural (Day 2), 9 more (Days 3-4)

**Track D (1h)**: Volatility Forecasting
- GARCH (statsmodels, fast)
- 1 neural volatility model (lightweight)
- Count: 2 volatility models

**Scripts Created** (✅ COMPLETE - November 12, 2025):
- `src/training/baselines/train_statistical.py` (ARIMA/Prophet with caching)
- `src/training/baselines/train_tree.py` (LightGBM/XGBoost with memory limits)
- `src/training/baselines/train_simple_neural.py` (LSTM/GRU with FP16, Metal GPU, session cleanup)
- `scripts/build_features.py` (feature engineering pipeline)
- `src/prediction/generate_forecasts.py` (daily forecast generation)
- `src/prediction/shap_explanations.py` (SHAP feature importance)
- `src/analysis/backtesting_engine.py` (procurement strategy validation)
- `scripts/crontab_setup.sh` (updated with ML pipeline automation)

**Deliverable**: ✅ Day 2 baseline training infrastructure complete. Ready to execute 20 baseline models (complete remainder Days 3-4), volatility forecasts available

**Memory Management**: Clear sessions, one GPU job at a time, monitor Activity Monitor

---

### Day 3: Advanced Models + Regime Detection + Backtesting (11 hours)

**Morning (5h)**: Advanced Neural Architectures (REALISTIC for 16GB)
- **Core architectures** (train 10-15 total, not 20-30):
  - 2-layer LSTM (2-3 variants, units 64-128)
  - 2-layer GRU (2-3 variants)
  - TCN (1-2 variants, kernel_size 3-5)
  - CNN-LSTM hybrid (1-2 variants)
  - Optional: 1-2 TINY attention (heads ≤4, d_model ≤256, seq_len ≤256)
- **Cut:** Heavy Transformers, multi-head attention >4, bidirectional LSTM
- **Strategy:** Train SEQUENTIALLY, clear Keras sessions, FP16 mixed precision
- **Batch sizes:** LSTM ≤32, TCN ≤32, attention ≤16
- **Focus:** 1w, 1m, 3m horizons (complete 6m/12m Day 4)
- Use Keras Tuner with RandomSearch (not Bayesian - too slow)
- Count: 10-12 advanced models

**Afternoon (6h)**: Critical Infrastructure
- **Regime classifier** (1h) - LightGBM, detect crisis/bull/bear/normal
- **Regime-specific models** (3h) - TOP 2-3 architectures per regime (not all)
  - Crisis regime: 2-layer LSTM + GRU (most important for risk)
  - Bull/Bear/Normal: 1 architecture each
  - Count: 8-10 regime models (not 20)
- **Walk-forward validation** (2h) - 60-iteration out-of-sample test
- **Backtesting engine** (2h) - procurement strategy validation
- Document winners

**Scripts Created**:
- `src/training/baselines/neural_advanced.py` (FP16, memory cleanup)
- `src/training/regime_classifier.py` - LightGBM classifier
- `src/training/regime_models.py` - selective regime specialists
- `src/training/walk_forward_validation.py`
- `src/analysis/backtesting_engine.py`

**Deliverable**: 20-25 models trained (realistic for 16GB), regime detection working, true MAPE known, strategies validated

**Overnight**: Let best models train overnight (2-layer LSTM for 6m/12m)

---

### Day 4: Production Monitoring & Decomposition (9 hours)

**Morning (4h)**: Daily Validation Framework
- `scripts/daily_model_validation.py` - predictions vs actuals
- **Performance decomposition** - MAPE by regime, by move size, by driver
- `scripts/performance_alerts.py` - email if MAPE > 3% or regime-specific failure
- Set up cron for daily runs

**Afternoon (5h)**: Explainability & Monitoring
- `src/prediction/shap_explanations.py` - factor attribution per prediction
- **Feature importance drift tracking** - detect when drivers change
- **Correlation breakdown monitoring** - alert on soy-palm/crude correlation failures
- Integrate with prediction API
- Dashboard endpoints: `/api/explain/{horizon}`, `/api/monitoring/performance`

**Scripts Created**:
- `scripts/daily_model_validation.py`
- `scripts/performance_alerts.py`
- `scripts/correlation_monitoring.py`
- `src/prediction/shap_explanations.py`
- `src/prediction/feature_drift_tracker.py`

**Deliverable**: Production monitoring operational, SHAP + drift tracking live, correlation alerts configured

---

### Day 5: Ensemble + Uncertainty + NLP (9 hours - REVISED)

**Morning (5h)**: Regime-Aware Ensemble
- `config/bigquery/bigquery-sql/ensemble_meta_learner.sql` - dynamic model blending
- **Regime-aware weighting** - crisis = weight 1W more, calm = weight 6M more
- Train LightGBM meta-learner on OOF predictions + regime context
- **Integrate regime classifier** - automatic model switching
- Count: 5 ensemble models (1 per horizon)

**Afternoon (4h)**: Uncertainty + NLP (INFERENCE-ONLY)
- **Uncertainty quantification** (2h) - MAPIE conformal prediction for 90% confidence bands
- **Volatility integration** (1h) - combine volatility forecasts with price forecasts
- **News impact NLP** (1h) - PRE-TRAINED FinBERT inference only (NOT fine-tuned)
  - Use ProsusAI/finbert out-of-box
  - Inference on 551 articles (batch 16, seq_len 128)
  - Generate sentiment features for predictions
  - **Skip:** Fine-tuning (too heavy for 16GB RAM)
  - **Optional:** Fine-tune on Colab Pro (2-hour session, $10)

**Scripts Created**:
- `src/prediction/ensemble_predictor.py` - LightGBM meta-learner
- `src/prediction/uncertainty_quantification.py` - MAPIE
- `src/prediction/news_impact_model.py` - FinBERT inference wrapper
- `config/bigquery/bigquery-sql/ensemble_meta_learner.sql`
- `scripts/correlation_monitoring.py`

**Deliverable**: Ensemble beating individuals, confidence intervals shown, NLP sentiment features (inference-only), correlation monitoring live

**Memory Management**: Keep FinBERT in inference mode only, batch size ≤16

---

### Day 6: Integration + A/B Testing + Backtesting Display (10 hours)

**Morning (5h)**: Complete Dashboard Integration
- Ensemble predictions → main forecast display
- SHAP explanations → "WHY prices moving" section with % contributions
- Confidence intervals → risk bands  
- Volatility forecasts → uncertainty display
- Regime detection → current regime + model selection display
- Daily validation → performance monitoring page
- **A/B testing framework** (30min) - shadow mode deployment for safe model swaps

**Afternoon (5h)**: Testing & Backtesting
- End-to-end testing: data refresh → prediction → explanation → alert
- **Backtest historical strategies** - show Chris what he would have saved
- **Load testing with A/B split** - verify shadow mode works
- Verify all 5 horizons operational
- Test correlation/regime alerts trigger correctly

**Scripts Created**:
- `src/deployment/ab_testing.py` - shadow mode deployment
- `dashboard-nextjs/app/api/monitoring/route.ts` - monitoring endpoints
- `dashboard-nextjs/app/api/backtesting/route.ts` - strategy validation display

**Deliverable**: Fully integrated dashboard, A/B testing ready, backtesting shows strategy ROI

---

### Day 7: Production Deployment & Documentation (6 hours)

**Morning (3h)**: Production Deployment
- Deploy ensemble to production endpoint (with shadow mode)
- Verify automatic retraining triggers work
- Test email alerts for all failure modes
- Verify regime switching operational
- Confirm correlation monitoring alerts

**Afternoon (3h)**: Documentation & Handoff
- Create `docs/training/PHASE_1_RESULTS.md` - metrics, model performance decomposition
- Create `docs/reference/PRODUCTION_PLAYBOOK.md` - operations guide
- Update this file with final results
- Handoff to Chris with capabilities overview

**Deliverable**: Production system live, documented, operational playbook complete

---

## Complete Feature Set (End of Day 7)

| Feature | Implementation | Hardware Realistic | Status |
|---------|---------------|-------------------|--------|
| **Baseline models** | 60-70 models (statistical, tree, neural, regime) | ✅ 16GB capable | ✅ |
| **Ensemble meta-learner** | LightGBM regime-aware blending | ✅ Lightweight | ✅ |
| **Regime detection** | LightGBM crisis/bull/bear/normal classifier | ✅ CPU-friendly | ✅ |
| **Daily validation** | Predictions vs actuals with decomposition | ✅ No GPU needed | ✅ |
| **Performance alerts** | Email if MAPE > 3% or regime failure | ✅ Scripts only | ✅ |
| **SHAP explainability** | Factor attribution per prediction | ✅ Batch inference | ✅ |
| **Feature drift tracking** | Detect importance changes over time | ✅ Lightweight | ✅ |
| **Volatility forecasting** | GARCH + 1 neural model | ✅ Small models | ✅ |
| **Uncertainty quantification** | MAPIE conformal prediction, 90% bands | ✅ Post-processing | ✅ |
| **Correlation monitoring** | Real-time soy-palm/crude breakdown alerts | ✅ Scripts only | ✅ |
| **News impact NLP** | FinBERT inference (pre-trained, NOT fine-tuned) | ✅ Inference-only | ✅ |
| **Backtesting engine** | Validate procurement strategies | ✅ Python only | ✅ |
| **A/B testing** | Shadow mode for safe model deployments | ✅ Logging only | ✅ |
| **Walk-forward validation** | 60-iteration out-of-sample testing | ✅ Sequential | ✅ |

**Optional (Cloud): FinBERT fine-tuning** - 2-hour Colab Pro session ($10), download weights for local inference

---

## API Architecture

### Production Dashboard (Chris-facing)
**Location**: `dashboard-nextjs/app/api/` (TypeScript, deployed on Vercel)

- `forecast/[horizon]/route.ts` - Production predictions from BigQuery
- `market/intelligence/route.ts` - Real-time signals
- `predictions/route.ts` - All horizons
- `regime/current/route.ts` - Regime detection display
- `monitoring/route.ts` - Performance tracking
- `backtesting/route.ts` - Strategy validation display

### Development Tools (Kirk-facing)
**Location**: `src/api/` (Python FastAPI, local server)

- `explain.py` - SHAP factor attribution (dev tool)
- `backtest.py` - Strategy backtesting (dev tool)
- `validate.py` - Daily model validation (dev tool)
- `monitoring.py` - Performance tracking (dev tool)
- `shadow.py` - A/B testing logs

**Communication**: Python scripts write results to BigQuery → Next.js reads them (no runtime dependency)

---

## Key Decisions Documented

**Baseline Approach**: Use full 125-year dataset with regime weighting, NOT just 2023–2025.

**Training Location**: Local M4 Mac mini for all development and baseline work.

**Cloud Usage**: Vertex AI for deployment only, after local validation.

**Model Selection**: Data-driven - promote models that beat benchmarks, not pre-selected architectures.

**Feature Strategy**: Start with 42 neural drivers, expand to 200–500 if baselines warrant it.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Regime overfitting | Test on multiple regime holdouts |
| Data leakage | Strict time-based splits, no future data |
| Local compute limits | Start with simple models, scale complexity based on results |
| Vertex AI costs | Only deploy validated winners |
| Documentation drift | This file is source of truth, update after each phase |

---

## Project Health Indicators

**Green Flags**:
- ✅ Repository reorganized and clean
- ✅ External drive configured
- ✅ Environment ready (`vertex-metal-312`)
- ✅ BQML production models running
- ✅ Deployment scripts created

**Yellow Flags**:
- ⚠️ Training data exports pending
- ⚠️ Baseline scripts not yet created
- ⚠️ MLflow not configured
- ⚠️ No baseline results yet

**Red Flags** (Production Readiness Gaps - Being Addressed in 7-Day Plan):
- 🚨 No daily validation (predictions vs actuals) → **Day 4**
- 🚨 No performance degradation alerts → **Day 4**
- 🚨 No SHAP explainability for predictions → **Day 4**
- 🚨 No ensemble meta-learner (models don't communicate) → **Day 5**
- 🚨 No automatic retraining triggers → **Day 4**
- 🚨 No prediction uncertainty quantification → **Day 5**
- 🚨 No regime detection → **Day 3**
- 🚨 No volatility forecasting → **Day 2**
- 🚨 No correlation monitoring → **Day 4**
- 🚨 No news impact NLP → **Day 5**
- 🚨 No backtesting engine → **Day 3**
- 🚨 No A/B testing framework → **Day 6**

---

**Review Cadence**: Update this file weekly or after major milestones.

---

## Future Enhancement Ideas (Reference)

**Strategic Concepts Document**: `docs/plans/CRYSTAL_BALL_ENHANCEMENT_IDEAS.md`

This document captures enhancement ideas from the "Crystal Ball" AI strategic proposal, including:
- Proactive intelligence ("reverse Google search")
- Standardized market pulse indicators (red/yellow/green)
- Advanced correlation analysis
- Conversational interface concepts
- Cost avoidance tracking & ROI
- Enterprise scalability considerations

**Note**: These are reference ideas for future consideration, not blocking dependencies for current training work. Review when planning app refinements.

**Data Sources Catalog**: `docs/plans/DATA_SOURCES_REFERENCE.md`

Comprehensive catalog of data sources, APIs, and scraping endpoints including:
- Weather and climate APIs (INMET, NOAA, Argentina SMN)
- Economic data sources (FRED, Treasury, Central Banks)
- Market data APIs (TradingEconomics, Polygon.io)
- Social media and sentiment sources
- Trade policy and news sources
- Security notes on API key management

**Note**: Review security section for hardcoded API keys that need migration to Keychain.
