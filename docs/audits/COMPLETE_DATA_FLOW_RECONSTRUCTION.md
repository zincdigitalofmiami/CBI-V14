# 🧩 COMPLETE DATA FLOW RECONSTRUCTION - FOLLOWING YOUR ARCHITECTURE
**Date:** November 12, 2025 20:30 UTC  
**Purpose:** Reconstruct the ACTUAL data flow following documented architecture  
**Rule:** Find all pieces, organize per existing plan, NO recreation

---

## 📋 YOUR DOCUMENTED ARCHITECTURE (From Plans)

### The Correct Flow (Per ARCHITECTURE_VERIFICATION.md + VERTEX_AI_TRUMP_ERA_PLAN.md)

```
STAGE 1: DATA COLLECTION
─────────────────────────
Cron Jobs (Local Mac) → BigQuery Cloud
  ├── Daily: Weather, prices, volatility, RIN prices
  ├── Every 4-6 hours: Social intel, ScrapeCreators API  
  ├── Weekly: CFTC, USDA, EIA
  └── Monthly: China imports, ENSO climate

DESTINATION: forecasting_data_warehouse.* (RAW TABLES)


STAGE 2: FEATURE ENGINEERING & CONSOLIDATION
──────────────────────────────────────────────
BigQuery SQL Processing:
  forecasting_data_warehouse.* (50+ raw tables)
    ↓ JOIN + FEATURE ENGINEERING
  models_v4.production_training_data_* (290-444 features)
    ↓ ADD REGIME LABELS
  models_v4.*_historical (regime-specific tables)

CRITICAL: This is where intelligence data should be JOINed!


STAGE 3: EXPORT TO EXTERNAL DRIVE
──────────────────────────────────
BigQuery → Parquet on External Drive:
  Location: /Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
    ├── exports/ (raw BigQuery exports with Vertex naming)
    │   ├── CBI_V14_Vertex_1M_Dataset_YYYYMMDD.parquet
    │   ├── CBI_V14_Vertex_3M_Dataset_YYYYMMDD.parquet
    │   ├── CBI_V14_Vertex_6M_Dataset_YYYYMMDD.parquet
    │   └── CBI_V14_Vertex_12M_Dataset_YYYYMMDD.parquet
    │
    ├── raw/ (organized raw data copies)
    └── processed/ (feature-engineered, ready for training)


STAGE 4: LOCAL TRAINING (MAC M4)
─────────────────────────────────
External Drive → TensorFlow Metal Training:
  Input: TrainingData/exports/*.parquet
  Output: Models/local/* (H5, checkpoints)
  Output: Models/vertex-ai/* (SavedModel format)

Environment: vertex-metal-312 (Python 3.12.6 + TF Metal)


STAGE 5: VERTEX AI DEPLOYMENT (PREDICTION ONLY)
────────────────────────────────────────────────
Upload SavedModels → Vertex AI:
  Models: CBI V14 Vertex – AutoML {1M|3M|6M|12M}
  Endpoints: CBI V14 Vertex – {1M|3M|6M|12M} Endpoint

Purpose: Serve predictions to dashboard/API
NOT FOR TRAINING (all training is local)


STAGE 6: DASHBOARD/API
──────────────────────
Vertex AI Endpoints → Next.js Dashboard
```

---

## 🚨 CURRENT STATE vs DOCUMENTED ARCHITECTURE

### ✅ STAGE 1: Data Collection - WORKING
- 78 ingestion scripts exist
- Cron jobs configured  
- Data flowing to `forecasting_data_warehouse.*`
- 79,151 intelligence rows collected

### ❌ STAGE 2: Feature Engineering - **BROKEN HERE**
**Problem:** Intelligence data NOT joining into production_training_data_*

**Evidence:**
- Source tables: 79,151 rows exist ✅
- Training tables: 55 intelligence columns exist ✅
- **But columns are NULL for 2024-2025** ❌

**Root Cause:** The SQL that builds production_training_data_* is either:
1. Not running (tables are stale)
2. Has broken JOINs (date mismatches)
3. Missing JOINs to key tables (e.g., staging.comprehensive_social_intelligence)

### ⚠️ STAGE 3: Export - PARTIALLY WORKING
**Current exports:**
- Files going to: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/exports/`
- **But NOT using Vertex naming convention!**

**Current file names:**
- `historical_full.parquet`
- `regime_*.parquet`

**Should be:**
- `CBI_V14_Vertex_1M_Dataset_YYYYMMDD.parquet`
- `CBI_V14_Vertex_3M_Dataset_YYYYMMDD.parquet`
- etc.

### ⏳ STAGE 4-6: Training/Deployment - READY BUT WAITING
- Environment configured ✅
- Scripts exist ✅
- Waiting for proper data from Stage 2-3

---

## 🔍 WHAT'S MISSING: THE COMPLETE PICTURE

### Intelligence Data Scattered Across Multiple Locations

#### NEWS DATA (5 locations)
1. `forecasting_data_warehouse.news_intelligence` - 2,830 rows (Oct-Nov 2025)
2. `forecasting_data_warehouse.news_advanced` - 223 rows (Sep-Oct 2025)
3. `forecasting_data_warehouse.news_ultra_aggressive` - 33 rows
4. `forecasting_data_warehouse.breaking_news_hourly` - 440 rows
5. `models.news_features_materialized` - 13 rows (processed)

**Total: ~3,539 rows across 5 tables**

#### SOCIAL INTELLIGENCE (3+ locations)
1. `staging.comprehensive_social_intelligence` - **63,431 rows** (Oct-Nov 2025) ← HUGE
2. `forecasting_data_warehouse.social_intelligence_unified` - 4,673 rows
3. `forecasting_data_warehouse.social_sentiment` - 677 rows (mixed dates)
4. `models.sentiment_features_materialized` - 581 rows (processed)
5. `models.sentiment_features_precomputed` - 604 rows (processed)

**Total: ~70,000 rows across 5+ tables**

#### TRUMP/POLICY (8 locations)
1. `forecasting_data_warehouse.trump_policy_intelligence` - 450 rows (active)
2. `staging.trump_policy_intelligence` - 215 rows (staging)
3. `deprecated.ice_trump_intelligence` - 186 rows (legacy)
4. `deprecated.ice_trump_intelligence_legacy_20251013` - 190 rows (legacy)
5. `staging.ice_enforcement_intelligence` - 4 rows
6. `models.enhanced_policy_features` - 653 rows (processed)
7. `models.tariff_features_materialized` - 46 rows (processed)
8. `models_v4.trump_policy_daily` - 53 rows (processed daily)

**Total: ~1,797 rows across 8 tables**

#### SIGNAL VIEWS (29 views in signals dataset)
- `vw_master_signal_processor`
- `vw_tariff_threat_signal`
- `vw_china_relations_signal`
- Plus 26 more...

**Status:** Unknown if these are being used in training table builds

---

## 🎯 THE RECONSTRUCTION PLAN

### PHASE 1: AUDIT EXISTING SQL (Find the Builder)
**Files to read (in order):**
1. `config/bigquery/bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql` (296 lines)
2. `config/bigquery/bigquery-sql/CREATE_EXPLOSIVE_PRODUCTION_TABLE_FAST.sql` (113 lines)
3. Search for any SQL that has `CREATE OR REPLACE TABLE production_training_data_`

**Goal:** Understand current JOIN logic and identify what's missing

### PHASE 2: MAP SIGNAL VIEWS
**Query all 29 signal views:**
- Get view definitions
- Check if they reference intelligence tables
- Verify they return data for 2024-2025
- Document if they're used in training table builds

### PHASE 3: DOCUMENT MISSING JOINS
**Create a map showing:**
- Which intelligence tables are NOT joined into production_training_data_*
- Which date column mismatches exist
- Which signal views are NOT being used

### PHASE 4: FIX JOINS (Minimal Changes)
**Only fix broken connections:**
- Add missing JOINs to intelligence tables
- Fix date column conversions (DATE vs TIMESTAMP)
- Ensure signal views are included

### PHASE 5: ORGANIZE EXTERNAL DRIVE PER VERTEX NAMING
**Update export_training_data.py to use proper names:**
```python
# Current (wrong):
output_file = f"historical_full.parquet"

# Should be (per Vertex plan):
output_file = f"CBI_V14_Vertex_1M_Dataset_{timestamp}.parquet"
```

**Organize external drive:**
```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
├── raw/ (clearly labeled raw intelligence data copies)
│   ├── news_intelligence_raw.parquet
│   ├── social_intelligence_raw.parquet
│   ├── trump_policy_raw.parquet
│   └── ... (all other raw sources)
│
├── exports/ (Vertex-named, BQ-prepped data)
│   ├── CBI_V14_Vertex_1M_Dataset_20251112.parquet
│   ├── CBI_V14_Vertex_3M_Dataset_20251112.parquet
│   ├── CBI_V14_Vertex_6M_Dataset_20251112.parquet
│   └── CBI_V14_Vertex_12M_Dataset_20251112.parquet
│
└── processed/ (feature-engineered, all layers)
    ├── layer_1_base_features/
    ├── layer_2_derived_features/
    └── layer_3_ensemble_ready/
```

---

## 🚦 STATUS: READY TO EXECUTE PHASES 1-2

**Next Actions:**
1. Read the 3 SQL files to understand current build logic
2. Map all 29 signal views to see what they provide
3. Create comprehensive JOIN audit showing what's missing
4. Document fix plan for approval

**Estimated Time:** 4-6 hours for complete audit before any fixes

**NO changes will be made until full audit is complete and approved.**

---

**Status:** AUDIT PHASE - Finding all puzzle pieces  
**Rule:** NO table recreation, NO data movement until we understand current state  
**Goal:** Minimal JOIN fixes to connect existing data per documented architecture

