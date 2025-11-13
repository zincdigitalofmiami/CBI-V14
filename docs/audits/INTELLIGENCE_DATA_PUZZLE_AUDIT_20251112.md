# 🧩 INTELLIGENCE DATA PUZZLE AUDIT
**Date:** November 12, 2025  
**Purpose:** Find all intelligence data pieces, understand current state, fix JOINs only  
**Rule:** NO table recreation, NO data movement, ONLY connect what exists

---

## PHASE 1: INVENTORY - WHERE IS EVERYTHING?

### Step 1.1: News Intelligence Data
**Question:** Where is all the news/sentiment data and what's its schema?

**Datasets to check:**
- `forecasting_data_warehouse.news_intelligence`
- `forecasting_data_warehouse.news_advanced`
- `forecasting_data_warehouse.news_ultra_aggressive`
- `forecasting_data_warehouse.breaking_news_hourly`
- `staging.comprehensive_social_intelligence`
- Any other news-related tables

**For each, document:**
- Row count
- Date range
- Date column name and type
- Key columns (sentiment, source, etc.)
- Sample of 2024-2025 data

### Step 1.2: Trump/Policy Intelligence
**Question:** Where is Trump policy data?

**Tables to check:**
- `forecasting_data_warehouse.trump_policy_intelligence`
- `staging.trump_policy_intelligence`
- `deprecated.ice_trump_intelligence`
- Any trump_* tables in models_v4

**Document:** Same as above

### Step 1.3: Social Intelligence
**Question:** Where is social media/sentiment data?

**Tables to check:**
- `forecasting_data_warehouse.social_intelligence_unified`
- `forecasting_data_warehouse.social_sentiment`
- `staging.comprehensive_social_intelligence`

### Step 1.4: Tariff/Trade Data
**Question:** Where is tariff threat data?

**Tables to check:**
- `models_v4.trade_war_2017_2019_historical`
- Any cftc_* tables
- Any trade_* tables

### Step 1.5: Derived Intelligence Features
**Question:** Where are pre-computed intelligence features?

**Tables to check:**
- `models.tariff_features_materialized`
- `models.enhanced_policy_features`
- `models.news_features_materialized`
- `models.sentiment_features_*`

---

## PHASE 2: UNDERSTAND CURRENT JOINS

### Step 2.1: Find Training Table Build SQL
**Files to locate:**
- `config/bigquery/bigquery-sql/BUILD_PRODUCTION_TRAINING_*.sql`
- Any SQL that creates `production_training_data_*` tables

### Step 2.2: Trace Intelligence JOINs
**For each training table SQL, document:**
- Which intelligence tables are being JOINed?
- What JOIN keys are used (date columns)?
- Are there date type mismatches (DATE vs TIMESTAMP)?
- Are there LEFT JOINs that should be working but return NULL?

### Step 2.3: Identify Broken JOINs
**Common issues to check:**
- Date column name mismatches (published vs created_at vs time)
- Date type mismatches (DATE vs DATETIME vs TIMESTAMP)
- Missing CAST/CONVERT operations
- Wrong JOIN conditions

---

## PHASE 3: MAP THE COMPLETE DATA FLOW

### Step 3.1: Source → Warehouse Flow
```
Daily Ingestion (cron)
  ↓
forecasting_data_warehouse (raw intelligence)
  ↓
Feature Engineering (signals views?)
  ↓
models_v4.production_training_data_* (final training tables)
  ↓
Parquet Export (external drive)
  ↓
Local Training (Mac M4)
```

### Step 3.2: Document Each Stage
**For each stage, verify:**
- Data exists at this stage
- Schema is consistent
- JOINs are functioning
- No data loss between stages

---

## PHASE 4: VERIFY SIGNAL VIEWS

### Step 4.1: Check Signal Views
**Tables to verify:**
- `signals.vw_tariff_threat_signal`
- `signals.vw_china_relations_signal`
- `signals.vw_master_signal_processor`
- All 29 signal views

**Questions:**
- Do they reference the correct source tables?
- Do they actually return data?
- Are they being used in training table builds?

---

## PHASE 5: ROOT CAUSE ANALYSIS

### Step 5.1: Why Are 2024-2025 Intelligence Features NULL?

**Hypothesis 1:** Source data doesn't exist for 2024-2025
- **Test:** Query source tables for 2024-2025 data
- **Result:** TBD

**Hypothesis 2:** JOINs are broken (date mismatches)
- **Test:** Check JOIN conditions in build SQL
- **Result:** TBD

**Hypothesis 3:** Build SQL isn't being run/is outdated
- **Test:** Check when training tables were last rebuilt
- **Result:** TBD

**Hypothesis 4:** Data is in staging but not promoted
- **Test:** Check if staging has 2024-2025 data
- **Result:** TBD

---

## PHASE 6: FIX PLAN (ONLY AFTER FULL AUDIT)

### Step 6.1: Document Current State
- Create complete data lineage diagram
- List all broken JOINs
- Identify missing transformations

### Step 6.2: Minimal Fix Approach
**ONLY fix JOINs, do not:**
- Recreate tables
- Move data
- Change schemas
- Rename columns

**DO:**
- Update JOIN conditions in build SQL
- Add missing CAST operations
- Correct date column references
- Test JOINs return data

### Step 6.3: Incremental Validation
**For each fix:**
- Test JOIN returns data
- Verify no data loss
- Check for duplicates
- Confirm date ranges

---

## EXECUTION CHECKLIST

- [ ] Phase 1: Complete inventory of all intelligence tables
- [ ] Phase 2: Map all current JOIN logic in build SQL
- [ ] Phase 3: Trace complete data flow source → training
- [ ] Phase 4: Test all signal views
- [ ] Phase 5: Root cause analysis - why NULLs?
- [ ] Phase 6: Document fix plan (for approval before execution)

---

**Status:** AUDIT IN PROGRESS  
**Next Step:** Execute Phase 1 - Complete inventory  
**Estimated Time:** 3-4 hours for full audit before any fixes

