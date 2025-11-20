---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# PLAN CONSOLIDATION REVIEW
**Date:** November 19, 2025  
**Purpose:** Review all plans and consolidate to 5-6 essential active plans

---

## CURRENT PLANS AUDIT

### Core Plans (docs/plans/) - 27 files

#### ACTIVE - KEEP (6 Plans)
1. ✅ **FRESH_START_MASTER_PLAN.md** - Overall master plan
2. ✅ **TRAINING_MASTER_EXECUTION_PLAN.md** - Training strategy and execution
3. ✅ **BIGQUERY_CENTRIC_MIGRATION_PLAN.md** - BQ migration strategy
4. ✅ **TABLE_MAPPING_MATRIX.md** - Reference: BQ table structure
5. ✅ **DATA_SOURCES_REFERENCE.md** - Reference: All data sources
6. ✅ **ARCHITECTURE_WIREFRAME.md** - System architecture

#### DUPLICATE/SUPERSEDED - ARCHIVE (8 Plans)
7. 📦 COMPLETE_ALPHA_INTEGRATION_PLAN.md → Superseded by FRESH_START_MASTER_PLAN
8. 📦 COMPLETE_DATA_INTEGRATION_PLAN.md → Superseded by FRESH_START_MASTER_PLAN
9. 📦 IMMEDIATE_DATA_LOADING_PLAN.md → Superseded by BIGQUERY_CENTRIC_MIGRATION_PLAN
10. 📦 TRAINING_SURFACE_FIX_THEN_ALPHA.plan.md → Superseded by TRAINING_MASTER_EXECUTION_PLAN
11. 📦 REGIME_BASED_TRAINING_STRATEGY.md → Integrated into TRAINING_MASTER_EXECUTION_PLAN
12. 📦 NAMING_ARCHITECTURE_PLAN.md → Superseded by TABLE_MAPPING_MATRIX
13. 📦 IMPLEMENTATION_PLAN_BIG8_UPDATE.md → Obsolete (Big8 already implemented)
14. 📦 EXECUTION_PLAN_LOCATION.md → Just a pointer file, obsolete

#### REFERENCE/CONTEXT - ARCHIVE (13 Files)
15. 📦 ACTUAL_ARCHITECTURE_AUDIT.md → Old audit, superseded by recent work
16. 📦 ALPHA_VANTAGE_FIXED_VS_SLIDING_WINDOW.md → Reference doc, not a plan
17. 📦 ARCHITECTURE_EVALUATION_AND_RECOMMENDATIONS.md → Old recommendations
18. 📦 ARCHITECTURE_REVIEW_REPORT.md → Old review
19. 📦 BEST_HARDWARE_RECOMMENDATION.md → Reference only
20. 📦 CRYSTAL_BALL_ENHANCEMENT_IDEAS.md → Ideas file, not a plan
21. 📦 DATA_LINEAGE_MAP.md → Reference, integrated into TABLE_MAPPING_MATRIX
22. 📦 DATASET_STRUCTURE_DESIGN.md → Superseded by TABLE_MAPPING_MATRIX
23. 📦 EXECUTIVE_SUMMARY_FOR_GPT.md → Old summary
24. 📦 FINAL_GPT_INTEGRATION_DIRECTIVE.md → Obsolete
25. 📦 GPT_INTEGRATION_ANSWERS.md → Q&A file, not a plan
26. 📦 HARDWARE_CORE_COMPARISON.md → Reference only
27. 📦 README.md → Keep as is (directory readme)

### Other Plan Files

#### Migration Plans (docs/migration/)
28. 📦 BQ_MIGRATION_ACTION_PLAN.md → Superseded by BIGQUERY_CENTRIC_MIGRATION_PLAN

#### Training Strategy
29. 📦 docs/training/HORIZON_TRAINING_STRATEGY.md → Integrated into TRAINING_MASTER_EXECUTION_PLAN

#### Execution Plans
30. 📦 docs/execution/25year-data-enrichment/architecture-lock.plan.md → Old
31. 📦 docs/execution/25year-data-enrichment/DATA_FORMAT_ISSUE_EXPLANATION.md → Issue doc
32. 📦 docs/execution/25year-data-enrichment/PLAN_REVIEW_AND_RECOMMENDATIONS.md → Old
33. 📦 docs/execution/25year-data-enrichment/PRAGMATIC_DATA_STRATEGY.md → Superseded

#### Data Source Plans
34. 📦 docs/data-sources/vegas-intel/REAL_DATA_INTEGRATION_PLAN.md → Vegas specific
35. 📦 docs/data-sources/vegas-intel/VEGAS_DATA_SYNTHESIS_PLAN.md → Vegas specific
36. 📦 docs/data-sources/google-marketplace/DATA_SOURCE_STRATEGY.md → Reference

#### Archived Handoffs (already archived)
37. ✅ docs/handoffs/archive/2025-11-05/* → Already in archive

---

## PROPOSED STRUCTURE

### 📁 docs/plans/ (ACTIVE - 6 FILES)

**Core Plans (5)**
1. `MASTER_PLAN.md` (rename from FRESH_START_MASTER_PLAN.md)
2. `TRAINING_PLAN.md` (rename from TRAINING_MASTER_EXECUTION_PLAN.md)
3. `BIGQUERY_MIGRATION_PLAN.md` (rename from BIGQUERY_CENTRIC_MIGRATION_PLAN.md)
4. `ARCHITECTURE.md` (rename from ARCHITECTURE_WIREFRAME.md)
5. `DASHBOARD_PAGES_PLAN.md` (NEW - consolidate dashboard/pages planning)

**Reference (1)**
6. `REFERENCE.md` (NEW - consolidate TABLE_MAPPING_MATRIX + DATA_SOURCES_REFERENCE)

Note on data authority and indicators:
- Technical indicators are computed in‑house from DataBento OHLCV (BigQuery/Dataform), not from Alpha Vantage/Yahoo pre‑calculated feeds.
- Alpha Vantage is not used for indicators. If retained at all, it is for news sentiment only (optional), with neutral table naming (e.g., `raw_intelligence.news_articles`).

### 📁 docs/plans/archive/ (ARCHIVED - 27 FILES)

Move all superseded, duplicate, and old plans here with timestamp.

---

## CONSOLIDATION ACTIONS

### Step 1: Create Archive Directory
```bash
mkdir -p docs/plans/archive/2025-11-19-consolidation
```

### Step 2: Archive Old Plans (27 files)
Move all superseded/duplicate plans to archive

### Step 3: Rename Active Plans (5 files)
- FRESH_START_MASTER_PLAN.md → MASTER_PLAN.md
- TRAINING_MASTER_EXECUTION_PLAN.md → TRAINING_PLAN.md
- BIGQUERY_CENTRIC_MIGRATION_PLAN.md → BIGQUERY_MIGRATION_PLAN.md
- ARCHITECTURE_WIREFRAME.md → ARCHITECTURE.md

### Step 4: Create New Plans (2 files)
- DASHBOARD_PAGES_PLAN.md (new)
- REFERENCE.md (consolidate existing references)

### Step 5: Update Links
Update any cross-references between plans

Policy alignment changes to apply during link updates:
- Replace any references to “Alpha Vantage technical indicators” with “in‑house indicators computed from DataBento OHLCV in BigQuery”.
- Remove cron examples invoking `collect_alpha_vantage_*` for indicators; keep only provider‑agnostic news collection if needed.
- Ensure the BigQuery‑centric migration is the canonical reference for data authority and orchestration.

---

## FINAL STRUCTURE

```
docs/plans/
├── MASTER_PLAN.md                    # Overall strategy & roadmap
├── TRAINING_PLAN.md                   # Training execution & strategy
├── BIGQUERY_MIGRATION_PLAN.md         # BQ migration & data flow
├── ARCHITECTURE.md                    # System architecture
├── DASHBOARD_PAGES_PLAN.md            # Dashboard & UI planning
├── REFERENCE.md                       # Quick reference (tables, sources)
├── README.md                          # Directory overview
└── archive/
    └── 2025-11-19-consolidation/
        └── [27 archived plans]
```

---

## BENEFITS

✅ **Reduced from 27 to 6 active plans** (78% reduction)  
✅ **Clear purpose** for each plan  
✅ **No duplication** or confusion  
✅ **Easy to maintain**  
✅ **Archived history** preserved  

---

**Status:** Ready to execute consolidation
