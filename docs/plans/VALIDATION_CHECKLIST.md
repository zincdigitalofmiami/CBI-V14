# Validation Checklist

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document provides a comprehensive validation checklist to confirm the BigQuery warehouse rebuild is successful before final cutover. All checks must pass before switching the live pipeline to new tables.

## Table Completeness

### Check 1: All Objects Migrated or Archived

```sql
-- Verify all 340 original objects are accounted for
WITH original_objects AS (
  SELECT 
    dataset_name,
    table_name,
    'original' as status
  FROM `cbi-v14.archive.legacy_nov12_2025.BACKUP_MANIFEST`
),
migrated_objects AS (
  SELECT 
    'raw_intelligence' as dataset_name,
    table_name,
    'migrated' as status
  FROM `cbi-v14.raw_intelligence.__TABLES__`
  UNION ALL
  SELECT 
    'features' as dataset_name,
    table_name,
    'migrated' as status
  FROM `cbi-v14.features.__TABLES__`
  UNION ALL
  SELECT 
    'training' as dataset_name,
    table_name,
    'migrated' as status
  FROM `cbi-v14.training.__TABLES__`
  UNION ALL
  SELECT 
    'predictions' as dataset_name,
    table_name,
    'migrated' as status
  FROM `cbi-v14.predictions.__TABLES__`
  UNION ALL
  SELECT 
    'monitoring' as dataset_name,
    table_name,
    'migrated' as status
  FROM `cbi-v14.monitoring.__TABLES__`
),
archived_objects AS (
  SELECT 
    dataset_name,
    table_name,
    'archived' as status
  FROM `cbi-v14.archive.legacy_nov12_2025.__TABLES__`
  WHERE table_name NOT LIKE 'BACKUP_MANIFEST'
)
SELECT 
  o.dataset_name,
  o.table_name,
  COALESCE(m.status, a.status, 'missing') as migration_status
FROM original_objects o
LEFT JOIN migrated_objects m ON o.table_name = m.table_name
LEFT JOIN archived_objects a ON o.table_name = a.table_name
WHERE COALESCE(m.status, a.status) IS NULL;
```

**Requirement**: No rows returned (all objects accounted for)

**Status**: [ ] Pass [ ] Fail

### Check 2: Empty Tables Reviewed

```sql
-- Check empty tables from inventory
SELECT 
  dataset_name,
  table_name,
  row_count
FROM `cbi-v14.GPT_Data.empty_minimal_tables`
WHERE row_count = 0
  AND table_name NOT IN (
    SELECT table_name 
    FROM `cbi-v14.archive.legacy_nov12_2025.__TABLES__`
  );
```

**Requirement**: All empty tables either repopulated or archived

**Status**: [ ] Pass [ ] Fail

### Check 3: Duplicate Tables Resolved

```sql
-- Verify duplicate tables are consolidated
SELECT 
  table_name,
  dataset_count,
  datasets
FROM `cbi-v14.GPT_Data.duplicate_table_names`
WHERE table_name NOT IN (
  SELECT table_name 
  FROM `cbi-v14.archive.legacy_nov12_2025.__TABLES__`
);
```

**Requirement**: No duplicate tables remain (all consolidated or archived)

**Status**: [ ] Pass [ ] Fail

## Schema Consistency

### Check 4: Training Tables Have Identical Schemas

```sql
-- Compare schemas across training tables
WITH schemas AS (
  SELECT 
    'horizon_1w' as horizon,
    column_name,
    data_type,
    ordinal_position
  FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'horizon_1w_production'
  UNION ALL
  SELECT 
    'horizon_1m' as horizon,
    column_name,
    data_type,
    ordinal_position
  FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'horizon_1m_production'
  UNION ALL
  SELECT 
    'horizon_3m' as horizon,
    column_name,
    data_type,
    ordinal_position
  FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'horizon_3m_production'
  UNION ALL
  SELECT 
    'horizon_6m' as horizon,
    column_name,
    data_type,
    ordinal_position
  FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'horizon_6m_production'
  UNION ALL
  SELECT 
    'horizon_12m' as horizon,
    column_name,
    data_type,
    ordinal_position
  FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'horizon_12m_production'
)
SELECT 
  column_name,
  COUNT(DISTINCT data_type) as type_count,
  COUNT(DISTINCT ordinal_position) as position_count,
  COUNT(DISTINCT horizon) as horizon_count
FROM schemas
GROUP BY column_name
HAVING type_count > 1 OR position_count > 1 OR horizon_count < 5;
```

**Requirement**: No rows returned (all schemas identical)

**Status**: [ ] Pass [ ] Fail

### Check 5: Date Columns Standardized

```sql
-- Verify date columns are standardized
SELECT 
  table_schema,
  table_name,
  column_name,
  data_type
FROM `cbi-v14.raw_intelligence.INFORMATION_SCHEMA.COLUMNS`
WHERE column_name IN ('date', 'time', 'timestamp', 'created_at', 'updated_at')
  AND data_type NOT IN ('DATE', 'TIMESTAMP')
UNION ALL
SELECT 
  table_schema,
  table_name,
  column_name,
  data_type
FROM `cbi-v14.features.INFORMATION_SCHEMA.COLUMNS`
WHERE column_name IN ('date', 'time', 'timestamp', 'created_at', 'updated_at')
  AND data_type != 'DATE'
UNION ALL
SELECT 
  table_schema,
  table_name,
  column_name,
  data_type
FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
WHERE column_name IN ('date', 'time', 'timestamp', 'created_at', 'updated_at')
  AND data_type != 'DATE';
```

**Requirement**: No rows returned (all date columns standardized)

**Status**: [ ] Pass [ ] Fail

### Check 6: No 100% NULL Columns

```sql
-- Check for columns with 100% nulls
SELECT 
  table_schema,
  table_name,
  column_name,
  null_count,
  total_rows,
  null_count / total_rows as null_rate
FROM (
  SELECT 
    table_schema,
    table_name,
    column_name,
    (SELECT COUNT(*) FROM `cbi-v14.{table_schema}.{table_name}`) as total_rows,
    (SELECT COUNT(*) FROM `cbi-v14.{table_schema}.{table_name}` WHERE {column_name} IS NULL) as null_count
  FROM `cbi-v14.{table_schema}.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_schema IN ('raw_intelligence', 'features', 'training', 'predictions')
)
WHERE null_rate = 1.0;
```

**Requirement**: No 100% NULL columns (or documented as expected)

**Status**: [ ] Pass [ ] Fail

## Row Counts & Ranges

### Check 7: Row Counts Match or Exceed Original

```sql
-- Compare row counts
SELECT 
  'old' as source,
  'models_v4.production_training_data_1m' as table_name,
  COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`
UNION ALL
SELECT 
  'new' as source,
  'training.horizon_1m_production' as table_name,
  COUNT(*) as row_count
FROM `cbi-v14.training.horizon_1m_production`;
```

**Requirement**: New table row count ≥ old table row count

**Status**: [ ] Pass [ ] Fail

### Check 8: Date Ranges Preserved

```sql
-- Verify date ranges
SELECT 
  'old' as source,
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(DISTINCT date) as date_count
FROM `cbi-v14.models_v4.production_training_data_1m`
UNION ALL
SELECT 
  'new' as source,
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(DISTINCT date) as date_count
FROM `cbi-v14.training.horizon_1m_production`;
```

**Requirement**: Date ranges match (2000-2025)

**Status**: [ ] Pass [ ] Fail

### Check 9: Random Sampling Validation

```sql
-- Random sample comparison
WITH old_sample AS (
  SELECT 
    date,
    target_1m,
    zl_price_current,
    vix_level
  FROM `cbi-v14.models_v4.production_training_data_1m`
  WHERE date IN (
    SELECT date 
    FROM `cbi-v14.models_v4.production_training_data_1m`
    ORDER BY RAND()
    LIMIT 100
  )
),
new_sample AS (
  SELECT 
    date,
    target_1m,
    zl_price_current,
    vix_level
  FROM `cbi-v14.training.horizon_1m_production`
  WHERE date IN (
    SELECT date 
    FROM `cbi-v14.training.horizon_1m_production`
    ORDER BY RAND()
    LIMIT 100
  )
)
SELECT 
  o.date,
  ABS(o.target_1m - n.target_1m) as target_diff,
  ABS(o.zl_price_current - n.zl_price_current) as price_diff,
  ABS(o.vix_level - n.vix_level) as vix_diff
FROM old_sample o
JOIN new_sample n ON o.date = n.date
WHERE ABS(o.target_1m - n.target_1m) > 0.01
   OR ABS(o.zl_price_current - n.zl_price_current) > 0.01
   OR ABS(o.vix_level - n.vix_level) > 0.01;
```

**Requirement**: No significant differences (within 0.01 tolerance)

**Status**: [ ] Pass [ ] Fail

## Model Performance

### Check 10: BQML Model Performance Parity

```sql
-- Compare BQML model performance
WITH old_performance AS (
  SELECT 
    AVG(mape) as avg_mape,
    AVG(mae) as avg_mae,
    AVG(r2) as avg_r2
  FROM `cbi-v14.monitoring.model_performance_daily`
  WHERE table_source = 'models_v4.production_training_data_1m'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
),
new_performance AS (
  SELECT 
    AVG(mape) as avg_mape,
    AVG(mae) as avg_mae,
    AVG(r2) as avg_r2
  FROM `cbi-v14.monitoring.model_performance_daily`
  WHERE table_source = 'training.horizon_1m_production'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
)
SELECT 
  ABS(o.avg_mape - n.avg_mape) as mape_diff,
  ABS(o.avg_mae - n.avg_mae) as mae_diff,
  ABS(o.avg_r2 - n.avg_r2) as r2_diff
FROM old_performance o
CROSS JOIN new_performance n
WHERE ABS(o.avg_mape - n.avg_mape) > 0.001  -- 0.1%
   OR ABS(o.avg_r2 - n.avg_r2) > 0.01;
```

**Requirement**: 
- ΔMAPE ≤ 0.1%
- ΔR² ≤ 0.01
- ΔMAE ≤ 0.1%

**Status**: [ ] Pass [ ] Fail

## Downstream Integration

### Check 11: Mac M4 Training Scripts

```bash
# Test Mac M4 export
python scripts/export_training_data.py \
  --table training.horizon_1m_production \
  --output TrainingData/exports/test_export.parquet \
  --verify
```

**Requirement**: Export succeeds and produces valid Parquet file

**Status**: [ ] Pass [ ] Fail

### Check 12: Dashboard API Endpoints

```bash
# Test API endpoints
curl -X GET "https://api.cbi-v14.com/api/v4/procurement-timing?horizon=1m" \
  -H "X-Test-Mode: validation" \
  -H "X-Table-Source: new"
```

**Requirement**: API returns identical data structure and values

**Status**: [ ] Pass [ ] Fail

## Data Quality Metrics

### Check 13: Freshness Checks

```sql
-- Check data freshness
SELECT 
  table_schema,
  table_name,
  MAX(date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_old
FROM `cbi-v14.raw_intelligence.*`
WHERE date IS NOT NULL
GROUP BY table_schema, table_name
HAVING days_old > 2
UNION ALL
SELECT 
  table_schema,
  table_name,
  MAX(date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_old
FROM `cbi-v14.features.*`
WHERE date IS NOT NULL
GROUP BY table_schema, table_name
HAVING days_old > 2;
```

**Requirement**: No tables older than 2 days

**Status**: [ ] Pass [ ] Fail

### Check 14: Null Rate Checks

```sql
-- Check null rates for critical features
SELECT 
  table_schema,
  table_name,
  column_name,
  null_count,
  total_rows,
  null_count / total_rows as null_rate
FROM `cbi-v14.monitoring.data_quality_daily`
WHERE column_name IN (
  'zl_price_current',
  'target_1m',
  'vix_level',
  'dxy_level'
)
  AND null_rate > 0.05;  -- 5%
```

**Requirement**: No critical features with >5% nulls

**Status**: [ ] Pass [ ] Fail

### Check 15: Duplicate Check

```sql
-- Check for duplicate dates
SELECT 
  table_schema,
  table_name,
  date,
  COUNT(*) as duplicate_count
FROM `cbi-v14.training.horizon_1m_production`
GROUP BY table_schema, table_name, date
HAVING duplicate_count > 1;
```

**Requirement**: No duplicate dates after deduplication

**Status**: [ ] Pass [ ] Fail

## Documentation

### Check 16: Documentation Complete

**Files to Verify**:
- [ ] `NAMING_CONVENTION_SPEC.md` – Complete
- [ ] `DATASET_STRUCTURE_DESIGN.md` – Complete
- [ ] `DATA_LINEAGE_MAP.md` – Complete
- [ ] `DEDUPLICATION_RULES.md` – Complete
- [ ] `ROLLBACK_PROCEDURE.md` – Complete
- [ ] `VALIDATION_CHECKLIST.md` – Complete (this file)
- [ ] `MASTER_EXECUTION_PLAN.md` – Complete

**Status**: [ ] Pass [ ] Fail

### Check 17: Table Descriptions

```sql
-- Verify table descriptions
SELECT 
  table_schema,
  table_name,
  description
FROM `cbi-v14.raw_intelligence.INFORMATION_SCHEMA.TABLES`
WHERE description IS NULL
UNION ALL
SELECT 
  table_schema,
  table_name,
  description
FROM `cbi-v14.features.INFORMATION_SCHEMA.TABLES`
WHERE description IS NULL
UNION ALL
SELECT 
  table_schema,
  table_name,
  description
FROM `cbi-v14.training.INFORMATION_SCHEMA.TABLES`
WHERE description IS NULL;
```

**Requirement**: All tables have descriptions

**Status**: [ ] Pass [ ] Fail

### Check 18: Column Comments

```sql
-- Verify column comments for critical tables
SELECT 
  table_schema,
  table_name,
  column_name,
  comment
FROM `cbi-v14.training.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN (
  'horizon_1m_production',
  'horizon_1w_production',
  'horizon_3m_production'
)
  AND comment IS NULL
  AND column_name NOT IN ('date', 'target_1m', 'target_1w', 'target_3m');
```

**Requirement**: Critical columns have comments

**Status**: [ ] Pass [ ] Fail

## Validation Summary

### Overall Status

- **Total Checks**: 18
- **Passed**: [ ] / 18
- **Failed**: [ ] / 18
- **Blocking Issues**: [ ] (list below)

### Blocking Issues

List any failed checks that block cutover:

1. [ ] Issue description
2. [ ] Issue description
3. [ ] Issue description

### Non-Blocking Issues

List any failed checks that don't block cutover:

1. [ ] Issue description
2. [ ] Issue description

## Sign-Off

- **Data Team Lead**: [ ] Approved
- **Platform Engineer**: [ ] Approved
- **Model Team Lead**: [ ] Approved
- **Date**: _______________

## References

- See `ROLLBACK_PROCEDURE.md` for rollback instructions
- See `MASTER_EXECUTION_PLAN.md` for migration steps

