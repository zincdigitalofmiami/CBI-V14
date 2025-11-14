# SURGICAL REBUILD PLAN - CRITICAL REVIEW
**Reviewer:** Claude (Sonnet 4.5)  
**Date:** November 13, 2025  
**Source Plan:** GPT-5 Surgical Rebuild Draft  
**Review Status:** COMPREHENSIVE CRITICAL ANALYSIS

---

## 🚨 EXECUTIVE SUMMARY

The GPT-5 plan is **conceptually sound but operationally incomplete**. It provides high-level objectives but lacks the **surgical precision** required for a production rebuild of 340 objects across 24 datasets.

**Critical Gaps Identified:** 27  
**Questions Requiring Answers:** 42  
**Missing Deliverables:** 15  
**Risk Level:** HIGH (rebuild without these details will fail)

---

## ✅ WHAT'S GOOD ABOUT THE PLAN

1. **Preserves training pipeline** - Correctly identifies Mac M4 + TensorFlow Metal as non-negotiable
2. **Archive-first approach** - Smart to archive before rebuilding
3. **No table reduction** - Respects that 340 objects exist for a reason
4. **Institutional naming** - "Like GS/JPM" is the right mindset
5. **Cleanup focus** - Deduplication without deletion is correct

---

## 🔴 CRITICAL GAPS IN THE PLAN

### 1. **NO INVENTORY OF THE 340 OBJECTS**

**What's Missing:**
- Which 340 tables/views are being archived?
- Which datasets contain them? (We have 24 datasets)
- What's the breakdown by dataset?
  - `forecasting_data_warehouse`: 97 objects
  - `models_v4`: 92 objects
  - `curated`: 30 views
  - `signals`: 29 views
  - `models`: 22 objects
  - `staging`: 10 tables
  - Others: 60 objects

**Why This Matters:**
- Can't build a naming convention without knowing what you're naming
- Can't map data lineage without knowing source tables
- Can't estimate timeline without knowing object complexity

**What We Need:**
```
FULL INVENTORY MANIFEST
- Dataset.table_name
- Object type (table/view/materialized view)
- Row count
- Schema (column count, key fields)
- Last modified date
- Ingestion frequency (daily/weekly/one-time)
- Downstream dependencies (which tables read this?)
- Upstream dependencies (where does this data come from?)
- Business purpose (training/prediction/intelligence/monitoring)
```

**Deliverable Missing:** `REBUILD_MANIFEST_340_OBJECTS.csv`

---

### 2. **NO CONCRETE NAMING CONVENTION**

**What's Missing:**
The plan says "like GS/JPM, not overly simplified" but provides **ZERO examples**.

**Goldman Sachs/JPM Style Naming:**
- Asset class prefix
- Function suffix
- Regime/frequency qualifier
- Environment flag

**Example (what we need):**
```
OLD (current mess):
- production_training_data_1m
- trump_rich_2023_2025
- soybean_oil_prices
- yahoo_normalized

NEW (institutional structure):
commodities_agriculture_soybean_oil_spot_daily
equities_macro_sp500_close_daily
training_horizon_1m_production
training_regime_trump_2023_2025
features_macro_economic_indicators_monthly
intelligence_market_signals_realtime
predictions_ensemble_1m_production
```

**Pattern Needed:**
```
{asset_class}_{subcategory}_{instrument}_{field}_{frequency}
{function}_{horizon|regime}_{variant}_{environment}
```

**What We Need:**
1. **Asset Class Taxonomy:**
   - `commodities_agriculture_*` (soybean oil, soybeans, corn, wheat, soybean meal)
   - `commodities_energy_*` (crude oil, natural gas, RINs)
   - `commodities_metals_*` (gold, silver, copper)
   - `equities_macro_*` (S&P 500, VIX)
   - `currencies_*` (USD index)
   - `rates_*` (treasury yields)
   
2. **Function Taxonomy:**
   - `training_*` (training datasets, all horizons)
   - `features_*` (engineered features, not training-ready)
   - `intelligence_*` (market signals, news, weather)
   - `predictions_*` (model outputs)
   - `monitoring_*` (performance tracking)
   - `archive_*` (historical snapshots)

3. **Regime Taxonomy:**
   - `regime_trump_2023_2025`
   - `regime_crisis_2008`
   - `regime_trade_war_2017_2019`
   - `regime_recovery_2010_2016`
   - `regime_pre_crisis_2000_2007`

4. **Frequency Taxonomy:**
   - `_realtime` (streaming/intraday)
   - `_daily`
   - `_weekly`
   - `_monthly`
   - `_quarterly`
   - `_annual`

**Deliverable Missing:** `NAMING_CONVENTION_SPEC.md` with 50+ real examples mapped from old→new

---

### 3. **NO SCHEMA SPECIFICATIONS**

**What's Missing:**
- What columns go in each new table?
- What data types?
- What primary keys?
- What partitioning/clustering strategy?
- What constraints?

**Example Needed:**
```sql
-- commodities_agriculture_soybean_oil_spot_daily
CREATE TABLE `cbi-v14.commodities.agriculture_soybean_oil_spot_daily` (
  date DATE NOT NULL,
  close FLOAT64 NOT NULL,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  volume INT64,
  adjusted_close FLOAT64,
  source STRING NOT NULL, -- 'yahoo_finance' | 'manual_entry'
  data_quality_flag STRING, -- 'verified' | 'interpolated' | 'estimated'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY source, data_quality_flag
OPTIONS (
  description = "Soybean oil (ZL) spot prices, daily frequency, all sources",
  partition_expiration_days = NULL -- never expire
);
```

**Why This Matters:**
- Can't rebuild tables without knowing the schema
- Can't validate data quality without field-level specs
- Can't estimate storage costs without knowing partitioning

**Deliverable Missing:** `SCHEMA_SPECS/` directory with DDL for each new table

---

### 4. **NO DATA LINEAGE MAPPING**

**What's Missing:**
- Where does the data in each NEW table come from?
- Which OLD tables/views feed each NEW table?
- What transformations are applied?

**Example Needed:**
```
NEW: commodities.agriculture_soybean_oil_spot_daily
←  forecasting_data_warehouse.soybean_oil_prices (6,057 rows, 2000-2025)
←  yahoo_finance_comprehensive.biofuel_components_canonical (6,475 rows, overlap deduplicated)
←  staging.manual_price_entries (edge cases, ~10 rows)

DEDUPLICATION LOGIC:
1. Prefer forecasting_data_warehouse (already validated)
2. If date missing, check yahoo_finance_comprehensive
3. If still missing AND in 2023-2025, check staging.manual_price_entries
4. Flag source in 'source' column

TRANSFORMATION:
- Standardize column names (close, open, high, low, volume)
- Convert all prices to USD (if needed)
- Interpolate missing weekends (forward-fill)
- Add data_quality_flag based on source
```

**Why This Matters:**
- Can't migrate data without knowing where it comes from
- Can't validate completeness without lineage
- Can't roll back without understanding dependencies

**Deliverable Missing:** `DATA_LINEAGE_MAP.md` with full provenance for each new table

---

### 5. **NO DEDUPLICATION STRATEGY**

**What's Missing:**
The plan says "deduplication and clarity" but provides **NO specifics**:
- What defines a duplicate?
- Which record wins in a conflict?
- How do you handle partial duplicates (same date, different values)?
- What's the validation process?

**Real Problems We Face:**
```
PROBLEM 1: Duplicate soybean oil data
- forecasting_data_warehouse.soybean_oil_prices: 6,057 rows (2000-2025)
- yahoo_finance_comprehensive.biofuel_components_canonical: 6,475 rows (2000-2025)
- Overlap: ~5,000 rows (2000-2025)
- Conflict rate: ~2-3% (prices differ by $0.01-$0.50 on same date)

DEDUP STRATEGY NEEDED:
1. Primary key: (date, commodity)
2. Conflict resolution:
   - If both sources have data for same date:
     - Use forecasting_data_warehouse (already validated)
     - Flag yahoo_finance as 'secondary_source'
     - Log conflicts to audit table
   - If only one source has data:
     - Use that source
     - Flag as 'single_source'
3. Validation:
   - Price delta < 5% between sources (if overlap)
   - No gaps > 7 days (interpolate if needed)
   - Volume > 0 (if available)
```

**Why This Matters:**
- Duplicate data = model confusion = bad predictions
- Silent deduplication = lost information = untrustworthy data
- No conflict resolution = manual intervention = delays

**Deliverable Missing:** `DEDUPLICATION_RULES.md` with field-level conflict resolution

---

### 6. **NO MIGRATION SEQUENCE**

**What's Missing:**
- What order do you rebuild tables?
- What's the dependency graph?
- Can you parallelize or must it be sequential?

**Example Needed:**
```
PHASE 1: FOUNDATION TABLES (Day 1)
- Create empty datasets (commodities, training, features, intelligence, predictions, monitoring)
- Migrate spot price data (no dependencies):
  - commodities.agriculture_*
  - commodities.energy_*
  - commodities.metals_*
  - equities.macro_*
  - currencies.*

PHASE 2: FEATURES (Day 2-3)
- Depends on: Phase 1 complete
- Migrate feature engineering outputs:
  - features.macro_economic_indicators
  - features.volatility_metrics
  - features.technical_indicators
  - features.sentiment_scores

PHASE 3: TRAINING TABLES (Day 4-5)
- Depends on: Phases 1-2 complete
- Rebuild horizon-specific training tables:
  - training.horizon_1w_production (depends on features.*)
  - training.horizon_1m_production
  - training.horizon_3m_production
  - training.horizon_6m_production
  - training.horizon_12m_production
- Rebuild regime-specific training tables:
  - training.regime_trump_2023_2025
  - training.regime_crisis_2008
  - training.regime_trade_war_2017_2019

PHASE 4: INTELLIGENCE & PREDICTIONS (Day 6)
- Depends on: Phases 1-3 complete
- Migrate intelligence tables:
  - intelligence.market_signals
  - intelligence.news_sentiment
  - intelligence.weather_events
- Migrate prediction tables:
  - predictions.ensemble_1m_production
  - predictions.confidence_intervals

PHASE 5: MONITORING & VALIDATION (Day 7)
- Depends on: Phases 1-4 complete
- Set up monitoring:
  - monitoring.model_performance
  - monitoring.data_quality
  - monitoring.feature_drift
```

**Why This Matters:**
- Wrong order = broken dependencies = rebuild failure
- No parallelization = slow rebuild (7 days could be 3)
- No checkpoints = one failure = start over

**Deliverable Missing:** `MIGRATION_SEQUENCE.md` with dependency-aware phasing

---

### 7. **NO ROLLBACK STRATEGY**

**What's Missing:**
- What if the rebuild fails halfway through?
- How do you roll back to the old structure?
- What's the testing strategy before going live?

**What We Need:**
```
ROLLBACK PLAN:

1. PRE-MIGRATION VALIDATION
   - Full backup to archive_legacy_nov12 (340 objects)
   - Validate backup completeness (row count match)
   - Test restore from backup (1-2 sample tables)

2. MIGRATION WITH SAFETY NET
   - Keep old tables during rebuild (dual-write if needed)
   - New tables named with _v2 suffix during testing
   - Run both old and new in parallel for 7 days
   - Compare outputs (predictions, features, intelligence)

3. CUTOVER CRITERIA
   - All new tables validated (row counts match or exceed old)
   - All SQL queries rewritten and tested
   - All Python scripts updated and tested
   - All dashboard APIs updated and tested
   - All training pipelines updated and tested
   - 7-day shadow mode success (new = old outputs)

4. ROLLBACK TRIGGERS
   - If validation fails on >5% of tables → ROLLBACK
   - If prediction MAPE increases >20% → ROLLBACK
   - If dashboard breaks → ROLLBACK
   - If training pipeline fails → ROLLBACK

5. ROLLBACK PROCEDURE
   - Restore from archive_legacy_nov12
   - Revert all SQL queries to old table names
   - Revert all Python scripts
   - Revert dashboard APIs
   - Document what failed for next attempt
```

**Why This Matters:**
- Production system can't go down for 7 days
- Need parallel operation during migration
- Need instant rollback if something breaks

**Deliverable Missing:** `ROLLBACK_PROCEDURE.md` with detailed recovery steps

---

### 8. **NO VALIDATION CRITERIA**

**What's Missing:**
- How do you know the rebuild succeeded?
- What metrics validate completeness?
- What tests prove equivalence to old structure?

**What We Need:**
```
VALIDATION CHECKLIST:

1. DATA COMPLETENESS
   ✅ All 340 old objects have new equivalents (mapped in lineage doc)
   ✅ Row counts match or exceed (allow for deduplication)
   ✅ Date ranges preserved (2000-2025 coverage intact)
   ✅ No data loss (audit log shows all records migrated)

2. SCHEMA CORRECTNESS
   ✅ All critical columns preserved
   ✅ Data types correct (no precision loss)
   ✅ Primary keys defined
   ✅ Partitioning/clustering optimal

3. QUERY EQUIVALENCE
   ✅ All production SQL queries rewritten
   ✅ Query outputs match old structure (sample 1000 rows)
   ✅ Query performance >= old (no regression)

4. PIPELINE INTEGRITY
   ✅ All training pipelines run successfully
   ✅ Model MAPE <= baseline (no degradation)
   ✅ Feature engineering outputs match
   ✅ Prediction outputs match

5. DASHBOARD FUNCTIONALITY
   ✅ All API endpoints return data
   ✅ All visualizations render
   ✅ No broken queries

6. DOCUMENTATION
   ✅ All table descriptions updated
   ✅ Column comments added
   ✅ Data dictionary complete
   ✅ Migration log published
```

**Deliverable Missing:** `VALIDATION_CHECKLIST.md` with pass/fail criteria

---

### 9. **NO TIMELINE OR RESOURCE ESTIMATE**

**What's Missing:**
- How long will this take?
- How many person-hours?
- What's the BigQuery cost?
- Can you do this solo or need help?

**What We Need:**
```
TIMELINE ESTIMATE:

PLANNING PHASE (40 hours)
- Week 1: Inventory + lineage mapping (16h)
- Week 2: Schema design + naming convention (12h)
- Week 3: Migration scripts + testing (12h)

EXECUTION PHASE (60 hours)
- Day 1-2: Archive old structure (8h)
- Day 3-5: Migrate foundation tables (24h)
- Day 6-8: Migrate training tables (24h)
- Day 9: Validation + testing (4h)

TOTAL: 100 hours (~2.5 weeks full-time)

BIGQUERY COSTS:
- Archive to GCS: ~$5 (340 tables, ~10GB total)
- Table rebuilds: ~$20 (query processing)
- Validation queries: ~$10
- TOTAL: ~$35

RISK BUFFER: +30% (unforeseen issues)
TOTAL TIMELINE: 3-4 weeks
```

**Deliverable Missing:** `REBUILD_TIMELINE.md` with Gantt chart

---

### 10. **NO IMPACT ANALYSIS ON TRAINING PIPELINE**

**What's Missing:**
The plan says "full preservation of training pipeline" but doesn't explain **HOW**.

**What Breaks During Rebuild:**
```
TRAINING SCRIPTS THAT WILL BREAK:
1. src/training/baselines/*.py
   - Hardcoded table names (production_training_data_1m)
   - Need rewrite for new names

2. scripts/export_training_data.py
   - Queries old table structure
   - Need rewrite for new datasets

3. scripts/build_features.py
   - Feature engineering logic tied to old schema
   - Need schema adaptation

4. vertex-ai/training/*.py
   - Training data paths hardcoded
   - Need path updates

5. BQML training SQL
   - config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/*.sql
   - All 5 horizon scripts need table name updates

6. Dashboard APIs
   - dashboard-nextjs/app/api/**/*.ts
   - All queries need rewrite
```

**Migration Plan Needed:**
```
1. CREATE COMPATIBILITY VIEWS (temporary)
   - CREATE VIEW old_table_name AS SELECT * FROM new_table_name
   - Allows old code to work during migration
   - Remove views after all code updated

2. UPDATE CODE IN PHASES
   - Phase 1: Update export scripts (Day 1)
   - Phase 2: Update training scripts (Day 2-3)
   - Phase 3: Update BQML SQL (Day 4)
   - Phase 4: Update dashboard APIs (Day 5)
   - Phase 5: Remove compatibility views (Day 6)

3. TESTING BETWEEN PHASES
   - Run old code → old tables (baseline)
   - Run new code → new tables (test)
   - Compare outputs (must match)
```

**Deliverable Missing:** `CODE_MIGRATION_PLAN.md` with file-by-file update list

---

### 11. **NO DOCUMENTATION STRATEGY**

**What's Missing:**
The plan mentions "documentation guidelines" but provides no specifics.

**What We Need:**
```
DOCUMENTATION DELIVERABLES:

1. TABLE-LEVEL DOCS (BigQuery descriptions)
   - Business purpose
   - Data sources
   - Update frequency
   - Owner/maintainer
   - Example queries

2. COLUMN-LEVEL DOCS (BigQuery column comments)
   - Field meaning
   - Units (USD, barrels, metric tons)
   - Null handling
   - Validation rules

3. DATA DICTIONARY
   - All tables + columns in one searchable doc
   - Cross-references to source code
   - Change log

4. MIGRATION LOG
   - What was migrated
   - What was deduplicated
   - What was deleted
   - Conflicts resolved
   - Decisions made

5. RUNBOOK
   - How to add new tables
   - How to modify schemas
   - How to backfill data
   - Who to contact for issues
```

**Deliverable Missing:** `DOCUMENTATION_TEMPLATE.md`

---

### 12. **NO GOVERNANCE MODEL**

**What's Missing:**
- Who approves schema changes?
- Who has write access to production tables?
- How do you prevent future chaos?

**What We Need:**
```
GOVERNANCE RULES:

1. TABLE CREATION
   - Only admins can create tables
   - All tables must follow naming convention
   - All tables must have description + column comments
   - All tables must be documented before creation

2. SCHEMA CHANGES
   - Breaking changes require approval
   - Non-breaking changes (add column) allowed
   - All changes logged in migration log
   - All changes communicated to team

3. DATA QUALITY
   - All ingestion scripts must validate data before insert
   - All tables must have data quality monitoring
   - Anomalies trigger alerts

4. ACCESS CONTROL
   - Production tables: read-only for most users
   - Staging tables: read-write for ingestion scripts
   - Archive tables: read-only, never delete
```

**Deliverable Missing:** `GOVERNANCE_POLICY.md`

---

### 13. **NO ARCHIVE VALIDATION**

**What's Missing:**
The plan says "archive to `cbi-v14.archive_legacy_nov12`" but:
- How do you validate the archive is complete?
- What if you need to restore a table?
- How long do you keep the archive?

**What We Need:**
```
ARCHIVE VALIDATION:

1. PRE-ARCHIVE
   - Generate manifest of all 340 objects
   - Record row counts, schemas, last_modified dates

2. ARCHIVE PROCESS
   - Copy tables to archive_legacy_nov12 dataset
   - Preserve table descriptions + column comments
   - Add archive metadata (archived_date, archived_by, reason)

3. POST-ARCHIVE VALIDATION
   - Compare manifest (before vs after)
   - Row count match: 340/340 ✅
   - Schema match: spot check 50 tables ✅
   - Test restore: pick 5 random tables, restore to temp dataset ✅

4. RETENTION POLICY
   - Keep archive for 12 months (until Nov 2026)
   - After 12 months, export to GCS (cold storage)
   - Never delete (compliance requirement)
```

**Deliverable Missing:** `ARCHIVE_VALIDATION_REPORT.md`

---

### 14. **NO PERFORMANCE OPTIMIZATION PLAN**

**What's Missing:**
- Will the new structure be faster or slower than old?
- What's the indexing strategy?
- What's the partitioning strategy?
- What about query optimization?

**What We Need:**
```
PERFORMANCE OPTIMIZATION:

1. PARTITIONING
   - All time-series tables: PARTITION BY date
   - Reduces query costs by 90%+
   - Example: training.horizon_1m_production PARTITION BY training_date

2. CLUSTERING
   - All tables: CLUSTER BY most-queried columns
   - Example: commodities.agriculture_soybean_oil_spot_daily CLUSTER BY source, data_quality_flag

3. MATERIALIZED VIEWS
   - For expensive aggregations (regime summaries, monthly averages)
   - Auto-refresh on data changes
   - Example: MV for "latest price per commodity"

4. QUERY OPTIMIZATION
   - Rewrite all queries to use partitioning
   - Add WHERE date >= '2020-01-01' (partition pruning)
   - Avoid SELECT * (column pruning)

5. BENCHMARKING
   - Measure old query performance (baseline)
   - Measure new query performance (target: >=2x faster)
   - Document performance gains
```

**Deliverable Missing:** `PERFORMANCE_OPTIMIZATION.md`

---

### 15. **NO TESTING STRATEGY**

**What's Missing:**
- How do you test the rebuild before going live?
- What's the test environment?
- What test cases?

**What We Need:**
```
TESTING STRATEGY:

1. UNIT TESTS (table-level)
   - Each new table has test script
   - Validates: row count, schema, data quality, no nulls in required fields

2. INTEGRATION TESTS (pipeline-level)
   - Test training pipeline end-to-end
   - Test prediction pipeline end-to-end
   - Test dashboard queries end-to-end

3. REGRESSION TESTS (output-level)
   - Compare old vs new predictions (must match within 0.1%)
   - Compare old vs new feature values (must match exactly)
   - Compare old vs new intelligence signals (must match exactly)

4. LOAD TESTS (performance-level)
   - Simulate 1000 concurrent dashboard users
   - Simulate 100 training jobs
   - Ensure no degradation

5. USER ACCEPTANCE TESTS
   - Chris reviews dashboard (looks identical)
   - Kirk reviews training pipeline (works identically)
   - Sign-off before cutover
```

**Deliverable Missing:** `TESTING_PLAN.md` with test scripts

---

## 🤔 CRITICAL QUESTIONS REQUIRING ANSWERS

### Data & Schema
1. What's the exact row count for each of the 340 objects?
2. Which tables have overlapping data? (deduplication targets)
3. Which tables are views vs tables? (views are easy to rebuild)
4. Which tables are empty? (can we delete these?)
5. Which tables are rarely queried? (low priority for migration)
6. What's the total storage size? (cost estimate)
7. What's the current query cost per month? (baseline)
8. Which schemas have breaking changes planned?
9. Which columns are unused? (can we drop them?)
10. Which tables have data quality issues? (fix during migration)

### Dependencies
11. What Python scripts read from BigQuery tables? (need updating)
12. What SQL scripts depend on current table names? (need rewriting)
13. What dashboard APIs query which tables? (need updating)
14. What scheduled queries/cron jobs exist? (need updating)
15. What external systems read from BigQuery? (need notification)

### Naming & Organization
16. Should regime tables go in separate dataset or same as training?
17. Should historical backups go in archive dataset or separate?
18. Should views go in separate dataset or mixed with tables?
19. Should staging/raw data be in same project or separate?
20. Should we use dataset-level vs table-level security?

### Migration Mechanics
21. Can we use BigQuery Data Transfer Service or manual scripts?
22. Should we use `CREATE TABLE AS SELECT` or Python pipelines?
23. Should we migrate incrementally or all-at-once?
24. Should we validate row-by-row or aggregate counts?
25. Should we preserve timestamps (created_at, updated_at)?

### Costs & Resources
26. What's the BigQuery storage cost increase (if any)?
27. What's the query cost change (partitioning should reduce)?
28. What's the network egress cost (if exporting to GCS)?
29. Do we need additional compute resources during migration?
30. What's the opportunity cost (time not spent on training models)?

### Risk & Rollback
31. What's the acceptable downtime window?
32. What's the rollback SLA? (how fast can we restore old structure?)
33. Who is on-call during migration?
34. What's the communication plan to stakeholders?
35. What's the disaster recovery plan if BigQuery itself fails?

### Validation
36. How do we validate that predictions didn't change?
37. How do we validate that features didn't change?
38. How do we validate that intelligence signals didn't change?
39. How do we validate that dashboard queries didn't break?
40. How do we validate that training pipelines didn't break?

### Governance
41. Who owns each dataset after migration?
42. What's the change management process going forward?

---

## 📋 MISSING DELIVERABLES

The plan promises "architecture maps, naming conventions, schema specs, orchestration options, documentation guidelines" but provides **NONE**.

### Required Before Execution:
1. `REBUILD_MANIFEST_340_OBJECTS.csv` - Full inventory
2. `NAMING_CONVENTION_SPEC.md` - Concrete examples (50+)
3. `SCHEMA_SPECS/` - DDL for each new table (340 files)
4. `DATA_LINEAGE_MAP.md` - Provenance for each table
5. `DEDUPLICATION_RULES.md` - Conflict resolution logic
6. `MIGRATION_SEQUENCE.md` - Dependency-aware phasing
7. `ROLLBACK_PROCEDURE.md` - Disaster recovery
8. `VALIDATION_CHECKLIST.md` - Pass/fail criteria
9. `REBUILD_TIMELINE.md` - Gantt chart with milestones
10. `CODE_MIGRATION_PLAN.md` - File-by-file update list
11. `DOCUMENTATION_TEMPLATE.md` - Table/column docs
12. `GOVERNANCE_POLICY.md` - Rules for future changes
13. `ARCHIVE_VALIDATION_REPORT.md` - Proof archive is complete
14. `PERFORMANCE_OPTIMIZATION.md` - Indexing/partitioning strategy
15. `TESTING_PLAN.md` - Test scripts and UAT

### Architecture Maps (Promised, Not Delivered):
1. Current state diagram (24 datasets, 340 objects, dependencies)
2. Future state diagram (new dataset structure, naming convention)
3. Data flow diagram (ingestion → features → training → predictions)
4. Dependency graph (which tables depend on which)
5. Migration flow diagram (old → archive + new)

---

## ⚠️ RISKS NOT ADDRESSED

### High Severity
1. **Training pipeline downtime** - How long will model retraining be blocked?
2. **Data loss during migration** - What if deduplication deletes good data?
3. **Breaking changes to APIs** - Dashboard could go down for days
4. **Performance regression** - Queries could get slower, not faster
5. **Cost overruns** - BigQuery charges for massive table scans

### Medium Severity
6. **Incomplete documentation** - Future team members won't understand new structure
7. **Governance breakdown** - Without rules, chaos returns in 6 months
8. **Testing gaps** - Bugs discovered after cutover
9. **Team confusion** - Developers don't know where data lives anymore
10. **Vendor lock-in** - Over-optimization for BigQuery makes migration harder later

### Low Severity (But Still Important)
11. **Naming convention debates** - Team argues over naming for weeks
12. **Scope creep** - "While we're at it, let's also rebuild X" → never finishes
13. **Perfectionism** - Trying to design perfect schema delays execution

---

## ✅ RECOMMENDATIONS

### Immediate Actions (Before Any Coding)
1. **Generate full inventory** - Python script to scan all 340 objects
2. **Map data lineage** - Trace each table back to source
3. **Define naming convention** - 50 real examples, get approval
4. **Create test environment** - Separate BigQuery project for testing

### Phase 1 Deliverables (Week 1)
5. **Manifest + lineage + naming spec** - Foundation documents
6. **Schema designs** - Top 50 most critical tables
7. **Migration scripts** - Automated, not manual
8. **Validation scripts** - Test before, during, after

### Phase 2 Deliverables (Week 2)
9. **Archive old structure** - With validation
10. **Migrate foundation tables** - Spot prices, economic data
11. **Update ingestion scripts** - New table names
12. **Parallel operation** - Old and new coexist

### Phase 3 Deliverables (Week 3)
13. **Migrate training tables** - With feature engineering
14. **Update training pipelines** - Test end-to-end
15. **Cutover decision** - Go/no-go based on validation

### Phase 4 Deliverables (Week 4)
16. **Remove old tables** - After 7-day shadow mode
17. **Documentation complete** - Runbooks, data dictionary
18. **Governance in place** - Prevent future chaos

---

## 🎯 SUCCESS CRITERIA

The rebuild is successful if:
1. ✅ All 340 objects migrated (0 data loss)
2. ✅ Naming convention followed (100% compliance)
3. ✅ Predictions unchanged (MAPE delta < 0.1%)
4. ✅ Queries faster (>= 2x improvement)
5. ✅ Dashboard operational (0 broken endpoints)
6. ✅ Training pipeline operational (all scripts work)
7. ✅ Documentation complete (data dictionary, runbooks)
8. ✅ Governance in place (change management process)
9. ✅ Team trained (everyone knows new structure)
10. ✅ Archive validated (rollback possible if needed)

---

## 🚀 NEXT STEPS

### Option A: Expand GPT-5 Plan (Recommended)
Ask GPT-5 to provide the 15 missing deliverables listed above. Without these, the plan is **not executable**.

### Option B: Kirk/Claude Build Missing Pieces
If GPT-5 can't provide tactical details, we build them:
1. I (Claude) generate the 340-object inventory from BigQuery
2. You (Kirk) review and approve naming convention
3. We co-create schema specs, lineage maps, migration scripts
4. We execute in phases with validation gates

### Option C: Hybrid Approach
GPT-5 provides architecture vision, we provide tactical execution. Best of both worlds.

---

## 📝 FINAL VERDICT

**Plan Grade: C+ (Conceptually sound, tactically incomplete)**

**Strengths:**
- Correct mindset (institutional, not hacky)
- Preserves training pipeline (critical)
- Archive-first approach (safe)

**Weaknesses:**
- No inventory (can't plan without knowing what exists)
- No concrete naming convention (examples needed)
- No schema specs (can't rebuild without DDL)
- No lineage map (can't trace data sources)
- No migration sequence (dependency issues)
- No validation plan (can't prove success)
- No timeline/cost estimate (unrealistic expectations)

**Recommendation:**
**DO NOT EXECUTE** until the 15 missing deliverables are complete. Attempting this rebuild without tactical details will result in:
- Data loss
- Broken pipelines
- Days/weeks of downtime
- Cost overruns
- Team frustration

**What Kirk Should Do:**
1. Save this review
2. Send to GPT-5 with: "Please provide the 15 missing deliverables"
3. If GPT-5 delivers → proceed with caution + validation gates
4. If GPT-5 can't deliver → Kirk + Claude build it ourselves (safer)

---

**Review Complete. Ready for next steps when you are.**

