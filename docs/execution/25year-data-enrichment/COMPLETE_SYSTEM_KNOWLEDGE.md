---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🧠 COMPLETE SYSTEM KNOWLEDGE - CBI-V14

**Date**: November 16, 2025  
**Status**: Master Knowledge Document  
**Purpose**: Complete understanding of the entire CBI-V14 system

---

## 🎯 CORE MISSION

**PRIMARY OBJECTIVE**: Predict ZL (Soybean Oil Futures) for Procurement Optimization

**Key Understanding**:
- The ENTIRE application is one big ZL predictor
- Every feature, model, and page serves ONE purpose: Help Chris make better soybean oil procurement decisions
- Other pages (Legislative, Strategy, etc.) are "microscopes" to observe specific drivers of ZL
- Vegas Intel is completely separate (for Kevin, sales director)

---

## 👤 USER PERSONAS

### CHRIS - Procurement Manager
- **Role**: Buys soybean oil in bulk for company
- **Needs**: Know when to lock in contracts vs wait
- **Language**: Procurement terms, not trading jargon
- **Decisions**: "Lock now" vs "Wait for better price"
- **Key Metrics**: $/cwt, contract timing, risk levels
- **Pages Used**: Dashboard, Legislative, Strategy, Sentiment (future)

### KEVIN - Sales Director  
- **Role**: Sells oil to Las Vegas restaurants
- **Needs**: Upsell opportunities based on casino events
- **Tool**: Vegas Intel page (completely separate from ZL prediction)
- **Data**: Glide app customer data + event calendars
- **Decisions**: "Call MGM before F1 race" type actions
- **Pages Used**: Vegas Intel only

---

## 🏗️ SYSTEM ARCHITECTURE

### The Big Picture
```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZL PREDICTION SYSTEM (SOYBEAN OIL)               │
│                           Core Mission                              │
│                                                                      │
│  Every feature, model, and page serves ONE purpose:                 │
│  Help Chris make better soybean oil procurement decisions           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                                      │
        CHRIS'S SYSTEM                          KEVIN'S SYSTEM
     (Procurement Manager)                    (Sales Director)
                │                                      │
    ┌───────────┼───────────┐                   Vegas Intel
    │           │           │                  (Disconnected)
Dashboard   Legislative  Strategy
    │           │           │
All Horizons  Trump→ZL   Scenarios
VIX/SHAP    Correlations  If/Then
```

---

## 📊 DATA SOURCE ARCHITECTURE

### ⚠️ CRITICAL: Data Source is LOCAL DRIVE, NOT BigQuery

**Primary Data Source**: Local External Drive
- **Path**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/`
- **Structure**:
  ```
  TrainingData/
  ├── raw/           # Immutable source zone (API downloads, never edited)
  ├── staging/       # Validated, conformed (units/timezones/dtypes fixed)
  ├── features/      # Engineered signals (Big 8, tech, macro, weather)
  ├── labels/        # Forward targets by horizon (7d, 30d, 90d, etc.)
  ├── exports/       # Final training parquet per horizon
  └── quarantine/    # Failed validations (human triage)
  ```

**Data Flow**:
```
APIs → raw/ → staging/ → features/ → labels/ → exports/
```

**BigQuery Role**:
- **NOT** the source of truth
- **ONLY** thin dashboard read layer
- Data originates from local drive
- Used for dashboard display only

**Script Data Access Pattern**:
```python
# All scripts follow this pattern:
drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

# Try staging first (validated data)
staging_path = drive / "TrainingData/staging/data_name.parquet"
raw_path = drive / "TrainingData/raw/data_name.parquet"

if staging_path.exists():
    df = pd.read_parquet(staging_path)
elif raw_path.exists():
    df = pd.read_parquet(raw_path)
else:
    return None  # No fake data - return None if unavailable
```

---

## 🚫 ZERO TOLERANCE FOR FAKE DATA

### Policy
**ABSOLUTE ZERO TOLERANCE** - No exceptions

### Forbidden Patterns
- `np.random.*` - NO random data generation
- `random.rand*` - NO random numbers
- `mock_*` - NO mock functions
- `fake_*` - NO fake data
- `dummy_*` - NO dummy data
- `placeholder` - NO placeholders
- `synthetic` - NO synthetic data
- `random.seed` - NO random seeds

### Required Pattern
```python
# When data unavailable:
if data is None or data.empty:
    return None  # or pd.DataFrame() - NEVER fake data
    logger.warning("Data unavailable")
```

### Verification
- ✅ All scripts verified: 0 fake data instances
- ✅ All prediction scripts use real data only
- ✅ All sentiment scripts use real data only
- ✅ Verification script: `verify_no_fake_data.sh`

---

## 🖥️ PAGE STRUCTURE

### 1. DASHBOARD (Home) ✅ Complete
**Purpose**: Main ZL prediction center
- All time horizons (1w, 1m, 3m, 6m, 12m)
- VIX overlay for risk assessment
- SHAP values explaining predictions
- Current price and targets
- Confidence levels
- **NOT trading signals - procurement guidance**

### 2. LEGISLATIVE ✅ Complete
**Purpose**: Policy/Trump impact microscope on ZL
- Trump action predictions
- How each action impacts ZL specifically
- Historical correlations (tariffs → ZL movement)
- ICE/labor regulations impact
- Lobbying activity effects
- Laws and trade relations
- **ZL-specific impact section with procurement alerts for Chris**

### 3. STRATEGY ✅ Complete
**Purpose**: Scenario planning for procurement
- What-if scenarios
- Upcoming laws to watch
- If/then decision trees
- Timing optimization
- Risk/reward for different contract timings
- **Chris's language: "If X happens, lock contracts by Y date"**

### 4. VEGAS INTEL (Kevin Only) ✅ Complete
**Purpose**: Sales intelligence for restaurant upsells
- Glide app integration (customer data)
- Casino event calendar
- Volume multipliers for events
- Upsell opportunities
- Sales strategies
- **Completely disconnected from ZL prediction**

### 5. SENTIMENT 🚧 Planned (Future Buildout)
**Purpose**: Comprehensive sentiment analysis and breaking news
- Unified sentiment scoring (all sources)
- Breaking news feed
- Social media sentiment trends
- Market analyst sentiment
- Policy document sentiment
- Weather/supply sentiment indicators
- Neural network sentiment analysis
- Sentiment component breakdown
- Historical sentiment patterns
- **Status**: Planned for future buildout

### 6. ES PREDICTION (Private) ✅ Complete
**Purpose**: S&P 500 futures prediction (private page, not in sidebar)
- Technical indicators
- Market microstructure
- Cross-asset correlations
- Sentiment indicators
- Machine learning ensemble
- **Note**: Private page, not shown in sidebar menu

---

## 🔄 DATA FLOW

### For Chris (ZL Prediction)
```
1. INPUTS (2000+ features)
   ├── Weather data (local drive)
   ├── Trump/social sentiment (local drive)
   ├── Market microstructure (local drive)
   ├── Supply/demand (local drive)
   ├── Technical indicators (calculated)
   ├── Cross-asset correlations (calculated)
   └── Policy/regulatory (local drive)

2. PROCESSING
   ├── Neural network (512-256-128-64-32)
   ├── Regime detection
   ├── Crisis intensity scoring
   └── Ensemble predictions

3. OUTPUT
   └── ZL price predictions with:
       ├── Procurement recommendations
       ├── Risk levels
       ├── Confidence scores
       └── Timing guidance
```

### For Kevin (Vegas Intel)
```
1. INPUTS
   ├── Glide app JSON (customers) → local drive
   ├── Casino event calendars → local drive
   ├── Historical volumes → local drive
   └── Demographics → local drive

2. PROCESSING
   ├── Event matching
   ├── Volume multipliers
   └── Opportunity scoring

3. OUTPUT
   └── Sales intelligence:
       ├── Upsell opportunities
       ├── Event-driven volume forecasts
       └── Restaurant contact recommendations
```

---

## 📁 KEY DIRECTORY STRUCTURE

### External Drive (Primary Data Source)
```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/           # API downloads (immutable)
│   ├── staging/       # Validated data
│   ├── features/      # Engineered signals
│   ├── labels/        # Forward targets
│   ├── exports/       # Final training data
│   └── quarantine/    # Failed validations
├── registry/
│   ├── feature_registry.json
│   ├── join_spec.yaml
│   ├── regime_calendar.parquet
│   └── regime_weights.parquet
└── scripts/
    ├── ingest/        # API pulls → raw/
    ├── conform/       # raw/ → staging/
    ├── features/       # staging/ → features/
    ├── labels/        # Date offsets → labels/
    ├── assemble/      # features + labels → exports/
    ├── predictions/   # Prediction models
    ├── sentiment/     # Sentiment analysis
    └── qa/            # QA gates
```

### Repository Structure
```
CBI-V14/
├── docs/
│   ├── execution/25year-data-enrichment/
│   │   ├── architecture-lock.plan.md  # MASTER PLAN
│   │   └── COMPLETE_SYSTEM_KNOWLEDGE.md  # This file
│   ├── PAGE_BUILDOUT_ROADMAP.md
│   └── SYSTEM_UNDERSTANDING_COMPLETE.md
├── scripts/
│   ├── predictions/
│   │   ├── es_futures_predictor.py      # ES prediction (local drive)
│   │   ├── zl_impact_predictor.py        # ZL impact from Trump
│   │   ├── trump_action_predictor.py     # Trump predictions
│   │   └── generate_vegas_intel.py       # Vegas Intel
│   ├── sentiment/
│   │   └── unified_sentiment_neural.py   # Sentiment analysis
│   └── features/
│       └── feature_calculations.py       # All feature engineering
└── dashboard-nextjs/
    └── src/app/
        ├── page.tsx                      # Dashboard
        ├── legislation/page.tsx          # Legislative
        ├── strategy/page.tsx             # Strategy
        ├── vegas-intel/page.tsx          # Vegas Intel
        ├── sentiment/page.tsx            # Sentiment (basic, needs buildout)
        └── private/
            └── es-prediction/page.tsx    # ES (private)
```

---

## 🔧 KEY SCRIPTS AND THEIR PURPOSES

### Prediction Scripts
1. **`scripts/predictions/es_futures_predictor.py`**
   - Predicts S&P 500 futures (ES)
   - Reads from: `TrainingData/staging/es_futures.parquet`
   - Uses technical indicators, market microstructure, cross-asset correlations
   - Output: `dashboard-nextjs/public/api/es_prediction.json`

2. **`scripts/predictions/zl_impact_predictor.py`**
   - Predicts ZL impact from Trump actions
   - Uses real Trump predictions from `trump_action_predictor.py`
   - Reads ZL price from: `TrainingData/staging/zl_futures.parquet`
   - Generates procurement alerts for Chris
   - Output: `dashboard-nextjs/public/api/zl_impact.json`

3. **`scripts/predictions/trump_action_predictor.py`**
   - Predicts Trump policy actions
   - Fetches real Truth Social data (BigQuery or ScrapeCreators API)
   - Analyzes posting patterns, threat levels, action signals
   - Output: `dashboard-nextjs/public/api/trump_prediction.json`

4. **`scripts/predictions/generate_vegas_intel.py`**
   - Generates Vegas sales intelligence for Kevin
   - Reads from: `TrainingData/staging/glide_restaurants.parquet`
   - Reads from: `TrainingData/staging/casino_events.parquet`
   - Output: `dashboard-nextjs/public/api/vegas_intel.json`

### Sentiment Scripts
5. **`scripts/sentiment/unified_sentiment_neural.py`**
   - Comprehensive sentiment analysis
   - Combines: social, news, analyst, policy, weather, technical, supply/demand
   - Uses neural network for pattern recognition
   - Reads from: `TrainingData/staging/sentiment_*.parquet`
   - Output: `TrainingData/sentiment/unified_sentiment_neural.parquet`

### Feature Engineering Scripts
6. **`scripts/features/feature_calculations.py`**
   - All 8 feature engineering functions:
     - `calculate_technical_indicators()` - RSI, MACD, Bollinger Bands, etc.
     - `calculate_cross_asset_features()` - Correlations, spreads, ratios
     - `calculate_volatility_features()` - Realized vol, VIX, GARCH
     - `calculate_seasonal_features()` - Month/quarter, harvest indicators
     - `calculate_macro_regime_features()` - Fed regime, yield curve
     - `calculate_weather_aggregations()` - Regional temp/precip, drought
     - `add_regime_columns()` - Merges regime calendar and weights
     - `add_override_flags()` - Data quality flags

7. **`scripts/features/build_all_features.py`**
   - Orchestrates all feature engineering
   - Calls all 8 functions from `feature_calculations.py`
   - Output: `TrainingData/features/all_features.parquet`

### QA Scripts
8. **`scripts/qa/pre_flight_harness.py`**
   - Pre-flight checks before training
   - `verify_no_leakage()` - Data leakage detection
   - `pre_flight_check()` - Includes Sharpe ratio parity validation
   - `run_all_checks()` - Comprehensive validation

9. **`scripts/qa/data_validation.py`**
   - Data quality validation
   - `validate_jumps_bps()` - Fed Funds rate jump validation (basis points)
   - `validate_vix_floor()` - VIX non-negative validation
   - `validate_all_columns()` - Comprehensive column validation

### Ingestion Scripts
10. **`scripts/ingest/collect_with_resilience.py`**
    - Resilient data collection framework
    - Multi-level caching
    - Fallback API sources
    - "Last good" cache recovery
    - China demand proxy builder

11. **`scripts/ingest/collect_google_public_datasets.py`**
    - Google Public Datasets integration
    - NOAA GSOD, FRED, UN Comtrade, COVID-19, Google Trends

12. **`scripts/ingest/collect_comprehensive_sentiment.py`**
    - ScrapeCreators API (Truth Social, Facebook)
    - Reddit API (retail trader sentiment)

13. **`scripts/ingest/collect_sentiment_with_fallbacks.py`**
    - Multiple fallback sources for sentiment
    - Market analysts, financial news APIs
    - Backup if ScrapeCreators fails

### Regime Scripts
14. **`scripts/regime/create_regime_definitions.py`**
    - Creates fresh regime definitions from scratch
    - 14 distinct regimes with weights (50-500)
    - Based on 25-year market analysis
    - Output: `registry/regime_calendar.parquet` and `registry/regime_weights.parquet`

---

## 📋 CHRIS'S PROCUREMENT RULES (Examples)

These are the types of rules Chris uses for decisions:

```python
# VIX stress
if VIX > 30:
    "HIGH RISK - Lock in contracts NOW"

# Argentina competition
if argentina_tax == 0:
    "Wait - Argentina undercutting market"

# China demand
if china_imports > 12_000_000:  # MT
    "BUY - demand spike incoming"

# Harvest pace
if harvest_pace > 70 and month == "Brazil harvest":
    "Supply glut - WAIT for bottom"

# Industrial demand
if industrial_demand > 0.5:
    "Floor support at $50/cwt"

# Palm oil substitution
if palm_spread < 10:
    "Risk of demand destruction - substitution threat"
```

---

## 🎯 TRUMP → ZL CORRELATION MAPPING

### Historical Patterns (from `zl_impact_predictor.py`)

| Trump Action | ZL Impact | Confidence | Time to Impact | Procurement Action |
|--------------|-----------|------------|----------------|-------------------|
| Tariff Announcement | -2.5% avg | 85% | 48 hours | LOCK CONTRACTS IMMEDIATELY |
| Trade Negotiation | +1.5% avg | 70% | 72 hours | WAIT - Positive momentum likely |
| Social Media Storm | -0.8% avg | 60% | 24 hours | MONITOR - Small impact expected |
| Policy Reversal | +2.0% avg | 75% | 48 hours | WAIT FOR REVERSAL - Better prices coming |
| China Threat | -3.0% avg | 80% | 24 hours | URGENT - Lock before major drop |
| Deal Making | +2.2% avg | 72% | 96 hours | WAIT - Deal optimism will lift prices |

### Market Condition Modifiers
- High VIX (>30): Amplifies moves by 1.5x
- Harvest Season (>70%): Dampens policy impact by 0.7x
- Low Inventory: Amplifies bullish moves by 1.3x
- High Inventory: Dampens moves by 0.8x
- Argentina Competition: Amplifies bearish moves by 1.2x

---

## 🔒 DATA INTEGRITY RULES

### Data Validation
1. **VIX Range**: 0-150 (quarantine if outside)
2. **Fed Funds Jumps**: >20% change flagged (quarantine)
3. **Date Duplicates**: Keep first, quarantine rest
4. **Missing Critical Columns**: Quarantine entire row
5. **Outlier Detection**: 3-sigma rule, quarantine outliers

### QA Gates
- **Phase 1 → Phase 2**: Block if >10% data quarantined
- **Pre-flight Check**: Verify no data leakage
- **Sharpe Ratio Parity**: Local model must match BigQuery metrics
- **Feature Completeness**: All required features must exist

### Quarantine Process
```
Bad Data → TrainingData/quarantine/ → Human Triage → Fix or Archive
```

---

## 📊 FEATURE CATEGORIES

### Technical Indicators
- RSI (9, 14, 25)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- Moving Averages (5, 10, 20, 50, 200)
- Momentum indicators
- Volume indicators (OBV, AD, ADOSC)
- Volatility (ATR, NATR)
- Pattern recognition (Doji, Hammer, Engulfing)

### Cross-Asset Features
- Correlations with: VIX, Dollar Index, Crude Oil, Gold, Bonds
- Spreads: Palm-Soy, Canola-Soy, Sunflower-Soy
- Ratios: Gold/ES, Oil/ES, etc.
- Sector rotation indicators

### Volatility Features
- Realized volatility (20-day rolling)
- VIX level, change, term structure
- GARCH estimates
- Volatility of volatility

### Seasonal Features
- Month/quarter encoding
- Harvest indicators (US, Brazil, Argentina)
- Cyclical patterns
- Day-of-week effects

### Macro Regime Features
- Fed regime (easing/tightening/neutral)
- Yield curve (steep/flat/inverted)
- Economic cycle indicators
- Inflation regime

### Weather Aggregations
- Regional temperature/precipitation
- Drought indicators (SPI, PDSI)
- Growing Degree Days (GDD)
- Extreme weather events

### Regime Columns
- Regime assignment (from `regime_calendar.parquet`)
- Regime weights (from `regime_weights.parquet`)
- Weighted training signals

### Override Flags
- Data quality flags
- Outlier flags
- Missing data flags
- Validation failure flags

---

## 🚀 EXECUTION PLAN STATUS

### Master Plan
**File**: `docs/execution/25year-data-enrichment/architecture-lock.plan.md`
- **Status**: LOCKED - Ready for execution
- **Phases**: 7 phases, 34 hours total
- **Current Phase**: Phase 0 complete ✅

### Phase 0: Setup + Forensic Inventory ✅
- Directory structure created
- Forensic audit complete
- All critical fixes applied

### Phase 1: Data Collection with Validation (Next)
- Tier 1 critical gaps
- FRED data collection
- Conformance & validation
- QA gates

### Remaining Phases
- Phase 2: Feature Engineering
- Phase 3: Label Generation
- Phase 4: Assembly
- Phase 5: QA Gates
- Phase 6: Upload to BigQuery
- Phase 7: Training & Automation

---

## 🔗 RELATED DOCUMENTATION

### Core Plans
- **`architecture-lock.plan.md`** - MASTER EXECUTION PLAN (authoritative)
- **`PAGE_BUILDOUT_ROADMAP.md`** - Dashboard page specifications
- **`SYSTEM_UNDERSTANDING_COMPLETE.md`** - System architecture details

### Execution Guides
- **`START_HERE_TOMORROW.md`** - Quick start guide
- **`MORNING_START_GUIDE.md`** - Detailed morning sequence
- **`READY_FOR_EXECUTION_20251116.md`** - Phase 0 completion status

### Status Reports
- **`EXECUTION_STATUS_20251116.md`** - Current execution status
- **`SYSTEM_STATUS_20251116_NIGHT.md`** - Comprehensive system status
- **`TONIGHT_COMPLETION_SUMMARY.md`** - What was done tonight

### Strategy Documents
- **`PRAGMATIC_DATA_STRATEGY.md`** - Data collection strategy
- **`CRITICAL_FIXES_APPLIED.md`** - Technical fixes applied

---

## ⚠️ CRITICAL DECISIONS & RATIONALE

### 1. Local Drive as Primary Data Source
**Decision**: All data stored on external drive, not BigQuery  
**Rationale**: 
- Mac M4 = compute engine (free, fast, deterministic)
- BigQuery = thin dashboard read layer only
- Data originates from APIs → local drive
- Training happens locally

### 2. Zero Tolerance for Fake Data
**Decision**: Absolute ban on any fake/mock/random data  
**Rationale**:
- Production system must use real data only
- Fake data leads to false confidence
- Better to return None/empty than fake data
- Verification script enforces policy

### 3. Fresh Regime Definitions
**Decision**: Create new regime definitions from scratch, don't pull from BigQuery  
**Rationale**:
- Starting fresh training from scratch
- Legacy models from BigQuery are being replaced
- New intelligence-based regime definitions
- Better alignment with current market understanding

### 4. ZL as Core Mission
**Decision**: Everything serves ZL prediction  
**Rationale**:
- Clear focus on procurement optimization
- All features and models optimized for ZL
- Other pages are "microscopes" for specific drivers
- Prevents scope creep

### 5. Separate Vegas Intel
**Decision**: Vegas Intel completely separate from ZL prediction  
**Rationale**:
- Different user (Kevin vs Chris)
- Different purpose (sales vs procurement)
- Different data sources (Glide app vs market data)
- Prevents confusion and maintains focus

---

## 🎯 NEXT STEPS

### Immediate (Phase 1)
1. Collect Tier 1 critical data gaps
2. FRED data collection with retry logic
3. Conformance & validation (raw → staging)
4. QA gates (block if >10% quarantined)

### Short Term
1. Complete feature engineering (Phase 2)
2. Generate labels (Phase 3)
3. Assemble training datasets (Phase 4)
4. Run QA gates (Phase 5)

### Medium Term
1. Upload to BigQuery (Phase 6)
2. Train models (Phase 7)
3. Deploy predictions
4. Build out Sentiment page

---

## 📝 IMPORTANT NOTES

### Data Availability
- Scripts return `None` or empty DataFrame if data unavailable
- No fake fallback data
- Logs data availability status
- Dashboard handles missing data gracefully

### Script Execution Order
1. Ingest scripts → `TrainingData/raw/`
2. Conform scripts → `TrainingData/staging/`
3. Feature scripts → `TrainingData/features/`
4. Label scripts → `TrainingData/labels/`
5. Assemble scripts → `TrainingData/exports/`
6. QA gates between each phase

### Error Handling
- All scripts use try/except blocks
- Log errors with context
- Quarantine bad data (don't delete)
- Continue processing if non-critical errors

### Testing
- No test files with fake data
- All tests use real data or skip if unavailable
- Verification script: `verify_no_fake_data.sh`

---

## 🔍 VERIFICATION CHECKLIST

Before starting any work, verify:
- [ ] Data source is local drive (not BigQuery)
- [ ] No fake data in scripts
- [ ] Scripts handle missing data gracefully
- [ ] All imports are correct
- [ ] File paths use external drive path
- [ ] Error handling is in place
- [ ] Logging is configured

---

## 📚 QUICK REFERENCE

### Historical Data Locations
**See**: `HISTORICAL_DATA_LOCATIONS.md` for complete inventory

**Summary**:
- **BigQuery (Legacy)**: 
  - `yahoo_finance_comprehensive`: 20+ years, 57,397+ rows
  - `forecasting_data_warehouse`: 108,487+ rows across 99 tables
- **External Drive (Primary)**: 
  - `TrainingData/raw/`: 332 files (267MB)
  - `TrainingData/exports/`: 19 files (23MB)
  - **Status**: Partially populated, needs 25-year backfill

### Data Paths
- **Raw Data**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/`
- **Staging Data**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging/`
- **Features**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/features/`
- **Exports**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/`

### Key Files
- **Master Plan**: `docs/execution/25year-data-enrichment/architecture-lock.plan.md`
- **System Understanding**: `docs/SYSTEM_UNDERSTANDING_COMPLETE.md`
- **Page Roadmap**: `docs/PAGE_BUILDOUT_ROADMAP.md`
- **This Knowledge Doc**: `docs/execution/25year-data-enrichment/COMPLETE_SYSTEM_KNOWLEDGE.md`

### Verification
- **Fake Data Check**: `./verify_no_fake_data.sh`
- **No Fake Data**: ✅ Verified (0 instances)

---

**Last Updated**: November 16, 2025  
**Maintained By**: AI Assistant  
**Status**: Complete and Current

---

## 🎓 KNOWLEDGE SUMMARY

1. **Core Mission**: ZL prediction for procurement optimization
2. **Data Source**: Local external drive (NOT BigQuery)
3. **Zero Tolerance**: No fake data, ever
4. **User Focus**: Chris (procurement) and Kevin (sales, separate)
5. **Page Structure**: Dashboard, Legislative, Strategy, Vegas Intel, Sentiment (planned)
6. **Architecture**: Local training → BigQuery dashboard read layer
7. **Current Status**: Phase 0 complete, ready for Phase 1
8. **Key Scripts**: All in `scripts/` directory, read from local drive
9. **Regime Definitions**: Fresh, created from scratch
10. **Next Phase**: Data collection with validation

**This document contains everything needed to understand and work with the CBI-V14 system.**
