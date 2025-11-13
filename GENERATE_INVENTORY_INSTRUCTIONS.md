# Generate BigQuery Inventory for GPT-5

**Date**: November 13, 2025  
**Purpose**: Produce a complete 340-object BigQuery inventory for the GPT-5 rebuild plan  

---

## 🎯 What This Is

A single Python command that hits the BigQuery metadata API (no SQL) and writes all required CSV files into `GPT_Data/`. These CSVs feed the GPT-5 architectural redesign.

---

## ⚡ Quick Start

### Step 1 – Install dependencies (one-time)
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
python3 -m pip install -r scripts/inventory_requirements.txt
```

### Step 2 – Generate the inventory package
```bash
python3 scripts/run_bq_inventory_export.py
```
This will fetch dataset/table metadata via the BigQuery Python client and write the 10 CSVs into `GPT_Data/`.

### Step 3 – (Optional) Inspect results
```bash
ls -lh GPT_Data/
```

---

## 📦 CSVs Produced (all in `GPT_Data/`)
1. `inventory_340_objects.csv`
2. `schema_all_columns.csv`
3. `production_tables_detail.csv`
4. `dataset_summary.csv`
5. `empty_minimal_tables.csv`
6. `duplicate_table_names.csv`
7. `column_name_frequency.csv`
8. `production_features_290.csv`
9. `historical_data_sources.csv`
10. `models_training_inventory.csv`

These came directly from the BigQuery metadata API on Nov 13, 2025 and reflect the exact warehouse state (no manual edits).

---

## ✉️ Updated GPT-5 Brief (Attach the 10 CSVs)
```
We operate the “CBI-V14” soybean oil (ZL) forecasting platform. Current state:

CONFIRMED FACTS
- 5 BQML DART models exist for 1w, 1m, 3m, 6m, 12m (tables are present; they can be renamed or rebuilt—dashboard is offline).
- 290 production features per horizon across `production_training_data_*` (1w/1m/3m/6m/12m) built on 25 years of history (2000-2025).
- Historical regime datasets (`models_v4.*historical`) and Yahoo Finance imports are intact.
- Mac M4 + TensorFlow Metal pipeline remains available for local training work.
- The attached BigQuery inventory (generated Nov 13, 2025 via metadata API) reflects current reality.

UNKNOWN / NEEDS VERIFICATION
- Cron/ingestion jobs exist but freshness and completeness have not been validated.
- Data quality varies; documentation, naming, and lineage are stale or missing across 340+ objects.

CHAOS TO CLEAN UP
- 340+ tables/views scattered across 24 datasets including archives and staging layers.
- Conflicting naming (identical table names in multiple datasets, ad-hoc suffixes, duplicated columns).
- No enforceable schema conventions; legacy artifacts mix with production tables.
- Dashboard is down; no downstream consumers depend on the current table names.

ATTACHED INVENTORY PACKAGE (Nov 13, 2025)
1. GPT_Data/inventory_340_objects.csv
2. GPT_Data/schema_all_columns.csv
3. GPT_Data/production_tables_detail.csv
4. GPT_Data/dataset_summary.csv
5. GPT_Data/empty_minimal_tables.csv
6. GPT_Data/duplicate_table_names.csv
7. GPT_Data/column_name_frequency.csv
8. GPT_Data/production_features_290.csv
9. GPT_Data/historical_data_sources.csv
10. GPT_Data/models_training_inventory.csv

YOUR TASK
Design a comprehensive, non-destructive rebuild plan that reorganizes this warehouse to institutional standards while keeping live data usable. Deliverables required:

1. NAMING_CONVENTION_SPEC.md
   - Institutional pattern (asset class / function / regime / horizon).
   - Map 50+ real tables/columns from the CSVs to new names.
   - You may rename or rebuild the current BQML tables.

2. DATASET_STRUCTURE_DESIGN.md
   - Proposed dataset layout (asset class, regime, function) with rationale.
   - Diagram/table explaining placement of current objects.

3. MIGRATION_SEQUENCE.md
   - Dependency-aware plan (phases, parallelizable steps, rollback points).
   - Identify prerequisites required before each phase (e.g., manifests, lineage docs).

4. SCHEMA_SPECS/ (directory with 50 DDL templates)
   - Column definitions, data types, partitioning/clustering, key constraints, data quality rules for the most critical tables.

5. DATA_LINEAGE_MAP.md
   - Current flow: ingestion → staging → feature layers → training tables → BQML outputs.
   - Highlight duplicated/conflicting sources exposed by the CSVs.

6. DEDUPLICATION_RULES.md
   - Conflict resolution for overlapping tables/columns (priority order, merge logic, audit logging).

7. ROLLBACK_PROCEDURE.md
   - How to revert during migration without breaking remaining live usage (training runs, exports, model refreshes).

8. VALIDATION_CHECKLIST.md
   - Acceptance criteria: row counts, schema parity, feature coverage, model QA, dashboard sanity checks.

CONSTRAINTS
- Dashboard is offline, so BQML tables can be renamed or rebuilt, but model continuity matters.
- Do NOT delete data during the design phase—mark tables for archive or migration.
- Preserve the Mac M4 training workflow and existing dataset exports.
- Keep live prediction and training pipelines operational throughout migration.

Please base your deliverables strictly on the attached CSVs; they reflect the warehouse as of Nov 13, 2025. We will validate against BigQuery and execute after your design.
```

---

## ✅ After GPT-5 Responds
1. Review deliverables.
2. Validate designs against actual BigQuery data (Claude task).
3. Execute migration (phased, with rollbacks).

---

**GPT_Data is ready. Send the brief + CSVs to GPT-5 now.**

