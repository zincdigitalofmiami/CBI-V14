---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Missing Features Report
**Date:** November 19, 2025  
**Status:** ⚠️ **CRITICAL FEATURES NOT CREATED**

---

## EXECUTIVE SUMMARY

While **52,794 rows of raw data** have been loaded to BigQuery, **several critical derived features** that depend on this data have NOT been created yet.

### ✅ What's Done
- ✅ Raw data loaded (Yahoo, ES, FRED, Weather, CFTC, USDA, EIA, Volatility, Palm, Policy)
- ✅ Master features view created (440 columns × 6,380 rows)
- ✅ Regime calendar loaded (9,497 rows)

### ❌ What's Missing
- ❌ **Sentiment daily** - 9-layer sentiment architecture NOT created
- ❌ **Signals tables** - Big 8 signals, crush calculations NOT created
- ⏳ **Master features table** - Materialized version (optional)

---

## MISSING FEATURES DETAIL

### 1. ❌ SENTIMENT DAILY (CRITICAL)

**Status:** NOT CREATED  
**Required For:** Sentiment dashboard page, procurement decisions, pinball triggers

**What Should Exist:**
- `staging/sentiment_daily.parquet` - Staging file
- `raw_intelligence.sentiment_daily` - BigQuery table

**What It Contains:**
- 9 sentiment layers (core_zl_price, biofuel_policy, geopolitical_tariff, etc.)
- `procurement_sentiment_index` (composite score)
- 5 pinball triggers (tariff_pinball, rin_moon_pinball, drought_pinball, etc.)

**Dependencies (All Loaded ✅):**
- ✅ `policy_trump_signals.parquet` → `raw_intelligence.policy_events`
- ✅ `eia_energy_granular.parquet` → `raw_intelligence.eia_biofuels`
- ✅ `weather_granular.parquet` → `raw_intelligence.weather_segmented`
- ✅ `usda_reports_granular.parquet` → `raw_intelligence.usda_granular`
- ✅ `cftc_commitments.parquet` → `raw_intelligence.cftc_positioning`
- ✅ `fred_macro_expanded.parquet` → `raw_intelligence.fred_economic`
- ⚠️ `news_articles` - May not exist (uses policy_trump_signals as proxy)
- ⚠️ `databento_futures_ohlcv_1d` - May need ES/Yahoo data

**How to Create:**
```bash
python3 scripts/features/sentiment_layers.py
```

**Then Load to BigQuery:**
- Create `raw_intelligence.sentiment_daily` table
- Load from `staging/sentiment_daily.parquet`

---

### 2. ❌ SIGNALS TABLES (CRITICAL)

**Status:** NOT CREATED  
**Required For:** Big 8 signals, crush calculations, dashboard signals

**Missing Tables:**
- `signals.big_eight_live` - Composite Big 8 signals
- `signals.crush_oilshare_daily` - Crush spread calculations
- `signals.energy_proxies_daily` - Energy proxy signals
- `signals.hidden_relationship_signals` - Hidden relationship signals

**Dependencies:**
- ✅ All raw intelligence data loaded
- ✅ Market data loaded
- ⚠️ Need calculation scripts/logic

**How to Create:**
- Need to create calculation scripts or SQL views
- Reference: `docs/plans/MASTER_PLAN.md` (Big 8 section)

---

### 3. ⏳ MASTER FEATURES TABLE (OPTIONAL)

**Status:** View exists, table optional  
**Current:** `features.master_features_all` (VIEW - 6,380 rows)

**Optional Materialized Table:**
- `features.master_features` - Materialized version for faster queries
- Would be a copy of the view as a table

**Not Critical:** View works fine for now

---

## IMPACT ANALYSIS

### What Works Now
- ✅ Raw data queries work
- ✅ Master features view works (440 columns)
- ✅ Can join data manually
- ✅ Regime calendar available

### What's Broken
- ❌ Sentiment dashboard page - No data source
- ❌ Pinball triggers - Not calculated
- ❌ Procurement sentiment index - Missing
- ❌ Big 8 signals - Not available
- ❌ Crush calculations - Not available

---

## ACTION REQUIRED

### Priority 1: Create Sentiment Daily (CRITICAL)
1. Run `scripts/features/sentiment_layers.py`
2. Verify `staging/sentiment_daily.parquet` created
3. Create `raw_intelligence.sentiment_daily` table in BigQuery
4. Load sentiment data to BigQuery
5. Update master features view to include sentiment

### Priority 2: Create Signals Tables
1. Create `signals` dataset if not exists
2. Build calculation logic for Big 8 signals
3. Create `signals.big_eight_live` table
4. Create `signals.crush_oilshare_daily` table
5. Load calculated signals

### Priority 3: Materialize Master Features (Optional)
1. Create `features.master_features` table
2. Populate from `features.master_features_all` view
3. Set up refresh schedule

---

## NEXT STEPS

**Immediate:**
1. ✅ Verify all raw data loaded (DONE)
2. ❌ Create sentiment daily features (TODO)
3. ❌ Create signals tables (TODO)
4. ⏳ Update master features view to include sentiment (TODO)

**Short Term:**
5. Create training tables from master features
6. Set up prediction tables
7. Fix API views

---

## SUMMARY

**Status:** ⚠️ **INCOMPLETE**

While raw data is loaded, **critical derived features are missing**:
- Sentiment daily (9-layer architecture)
- Signals tables (Big 8, crush, etc.)

**These features are required for:**
- Dashboard functionality
- Model training
- Procurement decisions
- Pinball triggers

**Action:** Run feature calculation scripts to create missing features.




