# DATASET REBUILD - ISSUES FOUND
**Date:** October 27, 2025 18:28 UTC

## CRITICAL ISSUES DISCOVERED

### Issue #1: DUPLICATES ❌
```
Total rows: 1,263
Unique dates: 1,251
Duplicates: 12 rows

Duplicate dates:
- 2025-09-09: 5 rows (4 duplicates)
- 2025-09-16: 5 rows (4 duplicates)
- 2025-09-23: 5 rows (4 duplicates)
```

### Issue #2: STALE DATA ❌
```
Latest date: 2025-10-13
Current date: 2025-10-27
Gap: 14 days missing
```

### Issue #3: MISSING SOURCE VIEWS ❌
```
Required views not found (8):
- models.vw_correlation_features
- models.vw_seasonality_features
- models.vw_crush_margins
- models.vw_china_import_tracker
- models.vw_brazil_export_lineup
- models.vw_trump_xi_volatility
- models.vw_event_driven_features
- models.vw_cross_asset_lead_lag
```

### Issue #4: BROKEN VIEW FIXED ✅
```
signals.vw_hidden_correlation_signal - REPAIRED
```

## WHAT NEEDS TO HAPPEN

### Step 1: Archive Broken Dataset
```sql
-- Archive the duplicate-ridden dataset
CREATE TABLE models_v4.archive_training_dataset_super_enriched_DUPLICATES_20251027
AS SELECT * FROM models_v4.training_dataset_super_enriched
```

### Step 2: Find OR Rebuild Missing Views
Check if views exist elsewhere OR recreate them from warehouse

### Step 3: Rebuild Dataset
- Source directly from warehouse tables
- Proper deduplication (ROW_NUMBER() or GROUP BY)
- Current through Oct 27
- All 202 features

### Step 4: Validate
- Zero duplicates
- Current dates
- All features present
- No fake data (verify COALESCE only fills real gaps)

## RECOMMENDATION

Need to either:
- **A)** Find where the 8 missing views are (different dataset?)
- **B)** Rebuild them from warehouse
- **C)** Find the original script that built this dataset and fix it

**Currently checking...**


