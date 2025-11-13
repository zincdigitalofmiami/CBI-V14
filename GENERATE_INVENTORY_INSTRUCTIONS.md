# Generate BigQuery Inventory for GPT-5

**Date**: November 13, 2025  
**Purpose**: Create complete 340-object inventory for surgical rebuild  

---

## 🎯 WHAT THIS IS

10 SQL queries that generate the complete BigQuery inventory GPT-5 needs to design the rebuild architecture.

---

## ⚡ QUICK START

### **Step 1: Run Queries**

```bash
# Open BigQuery console
open https://console.cloud.google.com/bigquery?project=cbi-v14

# Or run via bq command line
bq query --nouse_legacy_sql --format=csv < scripts/generate_bigquery_inventory.sql > inventory_results.csv
```

### **Step 2: Download Each Query Result**

Run each query in `scripts/generate_bigquery_inventory.sql` and save as CSV:

1. **inventory_340_objects.csv** - Complete table inventory
2. **schema_all_columns.csv** - All column definitions
3. **production_tables_detail.csv** - Critical production assets
4. **dataset_summary.csv** - 24 dataset rollup
5. **empty_minimal_tables.csv** - Deletion candidates
6. **duplicate_table_names.csv** - Same name, different datasets
7. **column_name_frequency.csv** - Common column patterns
8. **production_features_290.csv** - 290 production features
9. **historical_data_sources.csv** - 25-year historical data
10. **models_training_inventory.csv** - All models & training tables

### **Step 3: Create Inventory Package**

```bash
# Create directory
mkdir -p /Users/kirkmusick/Documents/GitHub/CBI-V14/inventory_for_gpt5

# Move all CSVs there
mv *.csv inventory_for_gpt5/

# Create manifest
ls -lh inventory_for_gpt5/ > inventory_for_gpt5/MANIFEST.txt
```

---

## 📤 SEND TO GPT-5

### **Brief for GPT-5**

```
I have a production soybean oil forecasting system with organizational chaos:

WHAT WORKS:
- 5 BQML models (live, serving predictions)
- 290 features in production_training_data_* tables (1w, 1m, 3m, 6m, 12m)
- 25 years of historical data (2000-2025)
- Mac M4 + TensorFlow Metal training pipeline
- Automated cron ingestion (32 jobs)

THE PROBLEM:
- 340 BigQuery objects across 24 datasets
- Same data in multiple places with different names
- 97 duplicate sentiment columns
- 20+ columns 100% NULL
- No clear naming convention
- Schema drift
- Organizational chaos growing daily

ATTACHED INVENTORY:
- inventory_340_objects.csv (complete manifest)
- schema_all_columns.csv (all column definitions)
- production_tables_detail.csv (critical assets)
- dataset_summary.csv (24 datasets)
- [7 more CSV files with detailed analysis]

YOUR TASK:
Design the surgical rebuild architecture with:

1. NAMING CONVENTION
   - Institutional-grade (like Goldman Sachs/JPMorgan)
   - 50+ real examples mapped from my actual data
   - Pattern: {asset_class}_{function}_{instrument}_{frequency}
   - Clear, unambiguous, self-documenting

2. DATASET STRUCTURE
   - Organized by: asset class, function, regime
   - NOT oversimplified (this is institutional-grade)
   - Clear separation of concerns
   - Scalable for future growth

3. MIGRATION SEQUENCE
   - Dependency-aware order
   - Which tables to migrate first
   - Parallel vs sequential execution
   - Rollback checkpoints

4. SCHEMA SPECIFICATIONS
   - DDL for top 50 most critical tables
   - Partitioning/clustering strategy
   - Primary keys, constraints
   - Data quality rules

CRITICAL CONSTRAINTS:
- Training pipeline CANNOT break (production models serving predictions)
- BQML models CANNOT be renamed (dashboard depends on them)
- NO table reduction (this is cleanup, not deletion)
- Must preserve 25 years of historical data
- Mac M4 training pipeline must continue working

DELIVERABLES NEEDED:
1. NAMING_CONVENTION_SPEC.md (50+ examples)
2. DATASET_STRUCTURE_DESIGN.md (architecture diagram)
3. MIGRATION_SEQUENCE.md (dependency graph + order)
4. SCHEMA_SPECS/ (DDL for 50 tables)
5. DATA_LINEAGE_MAP.md (where data flows)
6. DEDUPLICATION_RULES.md (conflict resolution)
7. ROLLBACK_PROCEDURE.md (disaster recovery)
8. VALIDATION_CHECKLIST.md (success criteria)

Please provide TACTICAL deliverables (not conceptual). I have engineers ready to validate against real data and execute.
```

---

## 📋 EXPECTED FILES

After running all queries, you should have:

```
inventory_for_gpt5/
├── inventory_340_objects.csv           (~340 rows)
├── schema_all_columns.csv              (~3,000+ rows)
├── production_tables_detail.csv        (~20 rows)
├── dataset_summary.csv                 (~24 rows)
├── empty_minimal_tables.csv            (~50+ rows)
├── duplicate_table_names.csv           (~20+ rows)
├── column_name_frequency.csv           (~100 rows)
├── production_features_290.csv         (~290 rows)
├── historical_data_sources.csv         (~30 rows)
├── models_training_inventory.csv       (~50 rows)
└── MANIFEST.txt                        (file list)
```

---

## ✅ VERIFICATION

Before sending to GPT-5, verify:

- [ ] All 10 CSV files generated
- [ ] Row counts look reasonable
- [ ] No query errors
- [ ] Files contain actual data (not empty)
- [ ] Manifest created

---

## 🚀 NEXT STEPS

1. **Generate inventory** (run queries above)
2. **Send to GPT-5** (use brief above + CSV files)
3. **Receive designs** (8 deliverables)
4. **Validate with Claude** (against real BigQuery data)
5. **Execute migration** (after validation)

---

**DO IT NOW. GPT-5 is waiting.**

