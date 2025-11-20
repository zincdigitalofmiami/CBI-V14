---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Complete Architecture Audit - November 17, 2025
**Purpose**: Deep review of ACTUAL existing architecture before answering GPT integration questions  
**Scope**: BigQuery structure, external drives, current pipelines, feature calculations

---

## ACTUAL CURRENT ARCHITECTURE

### 1. BigQuery Datasets (us-central1)

**Production Datasets (Active)**:
- `forecasting_data_warehouse` (99 tables) - Primary raw data storage
- `models_v4` (93 tables) - Training tables and BQML models
- `training` (18 tables) - New November 2025 training tables
- `raw_intelligence` (7 tables) - Intelligence data
- `staging` (11 tables) - Staging data
- `curated` (30 tables) - Curated views
- `signals` (34 tables) - Signal views
- `yahoo_finance_comprehensive` (10 tables) - 801K rows historical data
- `predictions` - Model outputs
- `monitoring` - Performance tracking

**Key Production Tables**:
```
training.zl_training_prod_allhistory_1w  (1,472 rows, 305 cols)
training.zl_training_prod_allhistory_1m  (1,404 rows, 449 cols)
training.zl_training_prod_allhistory_3m  (1,475 rows, 305 cols)
training.zl_training_prod_allhistory_6m  (1,473 rows, 305 cols)
training.zl_training_prod_allhistory_12m (1,473 rows, 306 cols)

models_v4.production_training_data_1w  (1,448 rows, 290 features)
models_v4.production_training_data_1m  (1,347 rows, 290 features)
models_v4.production_training_data_3m  (1,329 rows, 290 features)
models_v4.production_training_data_6m  (1,198 rows, 290 features)
```

### 2. External Drive Structure (/Volumes/Satechi Hub)

**Size Breakdown**:
- raw/: 620 MB (primary data storage)
- staging/: 572 KB
- quarantine/: 23 MB
- All other dirs: Empty (0B)

**Raw Data Subdirectories**:
```
forecasting_data_warehouse/ (mirroring BQ structure)
models_v4/ (mirroring BQ structure)
yahoo_finance/ (price data)
yahoo_finance_comprehensive/ (historical data)
fred/ (economic data)
noaa/ (weather data)
cftc/ (COT data)
eia/ (biofuel data)
usda/ (agricultural data)
inmet/ (Brazil weather)
brazil_weather/
csv/ (legacy CSV backups)
```

### 3. Current Data Collection Pattern

**Collection Scripts (Python → External Drive → Manual BQ Upload)**:
- `scripts/ingest/collect_fred_comprehensive.py` → `/Volumes/.../raw/fred/`
- `scripts/ingest/collect_yahoo_finance_comprehensive.py` → `/Volumes/.../raw/yahoo_finance/`
- `scripts/ingest/collect_cftc_comprehensive.py` → `/Volumes/.../raw/cftc/`
- `scripts/ingest/collect_eia_comprehensive.py` → `/Volumes/.../raw/eia/`
- `scripts/ingest/collect_noaa_comprehensive.py` → `/Volumes/.../raw/noaa/`
- `scripts/ingest/daily_data_updates.py` → Orchestrator

**Current Flow**:
```
Python script → External drive (Parquet/CSV) → Manual BigQuery upload
```

**NOT CURRENTLY**:
```
Cloud Run → BigQuery (no Cloud Run jobs exist)
```

### 4. Feature Calculation Approach

**Current Method: Python (NOT BigQuery SQL)**:
- `scripts/features/feature_calculations.py` - ALL feature engineering
- `scripts/features/build_all_features.py` - Orchestrator
- `scripts/features/calculate_amplified_features.py` - 850+ features

**Functions in feature_calculations.py**:
1. `calculate_technical_indicators()` - RSI, MACD, Bollinger Bands, MAs
2. `calculate_cross_asset_features()` - Correlations (30d, 90d)
3. `calculate_volatility_features()` - Realized vol, VIX regimes
4. `calculate_seasonal_features()` - Seasonality, calendar effects
5. `calculate_macro_regime_features()` - Fed regimes, yield curve
6. `calculate_weather_aggregations()` - Weather features
7. `add_regime_columns()` - Regime classification
8. `add_override_flags()` - Override flags

**ALL done in Pandas/NumPy, NOT BigQuery SQL**

### 5. BigQuery SQL Usage (Limited)

**BigQuery SQL Currently Used For**:
- Table creation (`CREATE TABLE`)
- Data insertion (`INSERT INTO`)
- Simple joins for training tables
- Model training (`CREATE MODEL`)
- Predictions (`ML.PREDICT`)

**NOT Currently Used For**:
- Feature calculation (correlations, moving averages, volatility)
- Complex window functions
- Advanced analytics

**Evidence**: 206+ SQL files in `config/bigquery/bigquery-sql/` are mostly:
- Table creation
- Data integration
- Model training
- NOT feature engineering

### 6. Training Pipeline (ACTUAL)

**Current Production Flow**:
```
1. Python scripts collect data → External drive (Parquet)
2. Manual/scripted upload → BigQuery raw tables
3. Python feature engineering → External drive (Parquet)
4. Manual/scripted upload → BigQuery training tables
5. BQML training in BigQuery → Models
6. Predictions via ML.PREDICT() → BigQuery predictions tables
7. Dashboard queries BigQuery predictions
```

**NOT Cloud Run orchestrated**
**NOT BigQuery SQL feature engineering**
**Local Python-first, BQ as storage**

### 7. Current ZL Feature Set

**290-450 features across training tables**:
- Price data (ZL, corn, wheat, palm, crude)
- Big 8 signals (8 features)
- Correlations (manual calculation in Python)
- Weather (Brazil, Argentina, US)
- Economic (FRED: 30+ series)
- China data
- Argentina data
- CFTC positioning
- News sentiment
- Trump intelligence
- Social sentiment

**Correlations calculated in Python**:
```python
df[f'cross_corr_{asset}_{period}d'] = df[base_price].rolling(
    window=period, min_periods=period//2
).corr(df[col])
```

**NOT using BigQuery CORR() function**

### 8. Missing from Current Architecture

**What Doesn't Exist Yet**:
- ❌ Cloud Run data collection jobs
- ❌ Cloud Scheduler orchestration
- ❌ BigQuery SQL feature engineering
- ❌ Dataform for feature pipelines
- ❌ Alpha Vantage integration (any)
- ❌ Options data collection
- ❌ Extended FX pairs
- ❌ Real-time/intraday data
- ❌ ES futures data
- ❌ Automated BQ feature calculations

**What Exists But Is Incomplete**:
- ⚠️ Feature engineering (done in Python, could move to BQ SQL)
- ⚠️ Data ingestion (Python scripts, could move to Cloud Run)
- ⚠️ FRED data (collected but not formalized)
- ⚠️ Sentiment data (collected but not enhanced)

---

## ANSWERS TO GPT'S QUESTIONS (Based on ACTUAL Architecture)

### Question 1: BigQuery-Centric Ingestion Strategy

**ACTUAL CURRENT STATE**:
- Python-first collection → External drive → Manual BQ upload
- NO Cloud Run jobs
- NO atomic ingestion
- NO BigQuery-first pattern

**ANSWER FOR GPT**:
**REPLACE (not augment)** - Move from Python-first to BigQuery-first:

```
NEW FLOW:
Python script (local/Cloud Run) → BigQuery raw.* → DONE
Then: BigQuery SQL → staging.* → features.* → training.*
```

**Key Changes**:
1. Direct BQ insert (no external drive intermediate)
2. Use BigQuery SQL for simple features (correlations, MAs, regimes)
3. Keep Python ONLY for complex NLP/sentiment
4. Remove dependency on external drive for primary flow

### Question 2: ZL vs ES in Phase 1

**ACTUAL CURRENT STATE**:
- ZL feature engineering INCOMPLETE
- Correlations calculated but in Python
- Sentiment exists but not formalized
- Regimes calculated but in Python
- NO ES data at all

**ANSWER FOR GPT**:
**DEFER ES to Phase 2** - ZL must be completed first:

**Phase 1 Must Complete**:
1. Formalize FRED data (already collected, needs documentation)
2. Formalize Yahoo Finance (already collected, needs documentation)
3. Integrate Alpha Vantage (NEW - doesn't exist yet)
4. Move correlations to BigQuery SQL (currently Python)
5. Formalize sentiment pipeline (exists but ad-hoc)
6. Formalize regime detection (currently Python)

**Then Phase 2**: ES reuses completed ZL infrastructure

### Question 3: Live File Mappings

**ACTUAL CURRENT STATE**:
- Most proposed files DON'T exist
- No Dataform
- No Cloud Run jobs
- Feature engineering in `scripts/features/feature_calculations.py`

**ANSWER FOR GPT**:
**YES - Provide actual file structure**, but recognize most are NEW:

```
EXISTING FILES (to modify/integrate):
├── scripts/ingest/
│   ├── collect_fred_comprehensive.py (EXISTS - needs BQ direct)
│   ├── collect_yahoo_finance_comprehensive.py (EXISTS - needs BQ direct)
│   └── daily_data_updates.py (EXISTS - needs BQ direct)
├── scripts/features/
│   ├── feature_calculations.py (EXISTS - some move to BQ SQL)
│   └── build_all_features.py (EXISTS - orchestrator)

NEW FILES (to create):
├── scripts/ingest/
│   ├── collect_alpha_vantage_master.py (NEW)
│   └── upload_to_bigquery_direct.py (NEW)
├── config/bigquery/features/ (NEW directory)
│   ├── zl_correlations.sql (NEW - move from Python)
│   ├── fed_regimes.sql (NEW - move from Python)
│   └── macro_features.sql (NEW)
```

---

## CRITICAL FINDINGS

### What's Working:
1. ✅ Data collection (FRED, Yahoo, CFTC, EIA, NOAA)
2. ✅ External drive storage working
3. ✅ Feature engineering working (in Python)
4. ✅ BQML training working
5. ✅ Predictions working

### What Needs Change:
1. ⚠️ Move simple features from Python to BigQuery SQL
2. ⚠️ Direct BigQuery insertion (skip external drive)
3. ⚠️ Add Alpha Vantage integration (completely new)
4. ⚠️ Formalize data source documentation
5. ⚠️ Consider Cloud Run for production (optional)

### Reality Check:
- Current architecture is **Python-first, BQ-storage**
- Proposed architecture is **BQ-first, Python-for-complex**
- This is a SIGNIFICANT shift, not a minor enhancement
- Most "deliverables" in plans DON'T exist yet

---

## RECOMMENDED INTEGRATION STRATEGY

### Phase 1A: Keep Working System (Week 1-2)
1. Continue Python feature engineering
2. Add Alpha Vantage collection (Python script)
3. Keep external drive flow
4. Focus on ADDING Alpha Vantage data

### Phase 1B: Gradual Migration (Week 3-4)
1. Move simple correlations to BigQuery SQL
2. Test BQ SQL performance vs Python
3. Create hybrid pipeline

### Phase 2: Full BigQuery-First (Later)
1. Cloud Run jobs (if needed)
2. Complete BQ SQL feature engineering
3. Dataform (if desired)

### Pragmatic Approach:
**Don't rebuild what works - enhance it**

---

**Report Generated**: November 17, 2025  
**Next**: Answer GPT questions based on ACTUAL architecture

