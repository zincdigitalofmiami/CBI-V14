# Pre-Integration Risk Assessment & Audit Framework
**Date**: November 12, 2025  
**Purpose**: Validate yahoo_finance_comprehensive data before integration  
**Status**: COMPREHENSIVE AUDIT FRAMEWORK - RUN BEFORE INTEGRATION

---

## 🎯 AUDIT OVERVIEW

This framework validates 25+ years of historical data before integrating it into production systems. Failure to run these checks could result in:
- Data corruption
- Production system breakage
- Wasted training time on bad data
- Unexpected BigQuery costs

---

## ⚠️ CRITICAL RISKS IDENTIFIED

### Risk 1: Schema Mismatch ⚠️ HIGH

**Problem**:
```sql
-- Production soybean_oil_prices:
time TIMESTAMP,
close FLOAT64,
symbol STRING

-- Yahoo yahoo_normalized:
date DATE,           -- ❌ Different type
close FLOAT64,       -- ✅ Same
symbol STRING        -- ❌ Different values?
```

**Validation Queries**:

```sql
-- Check 1.1: Symbol standardization
SELECT DISTINCT 
    symbol,
    symbol_name,
    COUNT(*) as row_count
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol LIKE '%ZL%' 
   OR symbol_name LIKE '%Soybean Oil%'
GROUP BY symbol, symbol_name
ORDER BY row_count DESC;

-- Expected: Should return 'ZL' or 'ZL=F' as primary symbol
-- Flag if: Multiple conflicting symbols found

-- Check 1.2: Date type compatibility
SELECT 
    'yahoo' as source,
    MIN(date) as earliest,
    MAX(date) as latest,
    COUNT(DISTINCT date) as unique_dates
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL'

UNION ALL

SELECT 
    'production' as source,
    MIN(DATE(time)) as earliest,
    MAX(DATE(time)) as latest,
    COUNT(DISTINCT DATE(time)) as unique_dates
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;

-- Expected: Yahoo earliest < 2000-01-01, Production earliest >= 2020
-- Flag if: Yahoo doesn't have pre-2020 data
```

**✅ PASS Criteria**:
- Symbol 'ZL' or 'ZL=F' found (not ZL1! or other variants)
- Yahoo has pre-2020 data (earliest < 2000-01-01)
- Date ranges don't conflict

**❌ FAIL Criteria**:
- Multiple conflicting symbols
- No pre-2020 data in yahoo
- Date type incompatibility

---

### Risk 2: Duplicate Data Corruption ⚠️ HIGH

**Problem**: Backfill may create duplicates if overlap exists

**Validation Queries**:

```sql
-- Check 2.1: Date overlap detection
WITH yahoo_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL'
      AND date >= '2020-01-01'
),
prod_dates AS (
    SELECT DISTINCT DATE(time) as date
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE DATE(time) >= '2020-01-01'
)
SELECT 
    COUNT(DISTINCT y.date) as yahoo_2020_plus,
    COUNT(DISTINCT p.date) as prod_2020_plus,
    COUNT(DISTINCT CASE WHEN y.date = p.date THEN y.date END) as overlapping
FROM yahoo_dates y
FULL OUTER JOIN prod_dates p ON y.date = p.date;

-- Expected: overlapping should be manageable (<100 days)
-- Flag if: overlapping > 500 days (major conflict)

-- Check 2.2: Price comparison in overlap
WITH yahoo_overlap AS (
    SELECT date, close as yahoo_close
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL' AND date >= '2020-01-01'
),
prod_overlap AS (
    SELECT DATE(time) as date, close as prod_close
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
    WHERE DATE(time) >= '2020-01-01'
)
SELECT 
    AVG(ABS(y.yahoo_close - p.prod_close)) as avg_diff,
    MAX(ABS(y.yahoo_close - p.prod_close)) as max_diff,
    AVG(ABS(y.yahoo_close - p.prod_close) / p.prod_close * 100) as avg_pct_diff,
    COUNT(*) as overlap_days
FROM yahoo_overlap y
JOIN prod_overlap p USING(date);

-- Expected: avg_pct_diff < 2%
-- Flag if: avg_pct_diff > 5% (sources diverge significantly)
```

**✅ PASS Criteria**:
- Overlap < 100 days OR prices match closely (<2% avg difference)
- Backfill plan handles overlap (excludes 2020+ dates)

**❌ FAIL Criteria**:
- Overlap > 500 days with no conflict resolution plan
- Prices diverge >5% on average

---

### Risk 3: Data Quality Issues ⚠️ MEDIUM

**Problem**: Yahoo data may have gaps, errors, or bad prices

**Validation Queries**:

```sql
-- Check 3.1: Data gaps (missing trading days)
WITH date_series AS (
    SELECT DATE_ADD('2000-01-01', INTERVAL day DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 9500)) as day
    WHERE DATE_ADD('2000-01-01', INTERVAL day DAY) <= CURRENT_DATE()
      AND EXTRACT(DAYOFWEEK FROM DATE_ADD('2000-01-01', INTERVAL day DAY)) NOT IN (1, 7)
),
yahoo_data AS (
    SELECT DISTINCT date
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL'
)
SELECT 
    COUNT(*) as trading_days_expected,
    COUNT(y.date) as trading_days_found,
    COUNT(*) - COUNT(y.date) as missing_days,
    ROUND((COUNT(*) - COUNT(y.date)) / COUNT(*) * 100, 2) as missing_pct
FROM date_series d
LEFT JOIN yahoo_data y USING(date);

-- Expected: missing_days < 500 (< ~10%)
-- Flag if: missing_days > 1000 (major gaps)

-- Check 3.2: Price range validation
SELECT 
    MIN(close) as min_price,
    MAX(close) as max_price,
    AVG(close) as avg_price,
    STDDEV(close) as std_price,
    COUNTIF(close IS NULL) as null_prices,
    COUNTIF(close <= 0) as zero_or_negative
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL';

-- Expected: min_price ~$25, max_price ~$90 (historical ZL range)
-- Flag if: min_price < $10 OR max_price > $200 (data corruption)
-- Flag if: null_prices > 0 OR zero_or_negative > 0

-- Check 3.3: Price volatility (detect bad data)
WITH price_changes AS (
    SELECT 
        date,
        close,
        LAG(close) OVER (ORDER BY date) as prev_close,
        ABS(close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) as pct_change
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL'
    ORDER BY date
)
SELECT 
    MAX(pct_change) as max_daily_move,
    AVG(pct_change) as avg_daily_move,
    COUNTIF(pct_change > 0.10) as days_with_10pct_moves,
    COUNTIF(pct_change > 0.20) as days_with_20pct_moves
FROM price_changes
WHERE pct_change IS NOT NULL;

-- Expected: max_daily_move < 0.15 (15%)
-- Flag if: max_daily_move > 0.25 (25% - likely bad data)
-- Flag if: days_with_20pct_moves > 10 (too many extreme moves)
```

**✅ PASS Criteria**:
- Missing days < 500 (<10% of trading days)
- Prices in range $10-$200
- Max daily move < 25%
- No NULL or negative prices

**❌ FAIL Criteria**:
- Missing days > 1000 (>20% gaps)
- Prices outside $5-$300 range
- Max daily move > 50%
- NULL or negative prices found

---

### Risk 4: Production Table Corruption ⚠️ HIGH

**Problem**: Integration could break existing production tables

**Mitigation**: CREATE BACKUPS FIRST

```sql
-- Backup 4.1: Production training tables
CREATE TABLE `cbi-v14.models_v4.production_training_data_1w_backup_20251112` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1w`;

CREATE TABLE `cbi-v14.models_v4.production_training_data_1m_backup_20251112` AS
SELECT * FROM `cbi-v14.models_v4.production_training_data_1m`;

-- Backup 4.2: Soybean oil prices
CREATE TABLE `cbi-v14.forecasting_data_warehouse.soybean_oil_prices_backup_20251112` AS
SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;

-- Rollback 4.3: If integration fails
-- DROP TABLE `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;
-- CREATE TABLE `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` AS
-- SELECT * FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices_backup_20251112`;
```

**✅ PASS Criteria**:
- All backups created successfully
- Backup table sizes match originals
- Rollback plan documented

**❌ FAIL Criteria**:
- Backup creation fails
- No rollback plan

---

### Risk 5: BigQuery Cost Spike ⚠️ MEDIUM

**Problem**: Large scans could cause unexpected costs

**Mitigation**: Estimate costs BEFORE running

```sql
-- Cost 5.1: Check table sizes
SELECT 
    table_name,
    ROUND(size_bytes / POW(10, 9), 2) as size_gb,
    ROUND(size_bytes / POW(10, 12) * 5, 2) as scan_cost_usd
FROM `cbi-v14.yahoo_finance_comprehensive.__TABLES__`
ORDER BY size_bytes DESC;

-- Expected: Total cost < $1 for full scan
-- Flag if: Any single table > $5 to scan
```

**✅ PASS Criteria**:
- Total estimated cost < $5
- Individual queries estimated < $1

**❌ FAIL Criteria**:
- Total cost > $20
- Single query > $5

---

## ✅ PRE-INTEGRATION CHECKLIST

### Phase 0: Backups (30 min)
- [ ] Backup production_training_data_1w
- [ ] Backup production_training_data_1m  
- [ ] Backup soybean_oil_prices
- [ ] Export current training data (for rollback)
- [ ] Document current schema

### Phase 1: Schema Validation (1 hour)
- [ ] Run symbol standardization check
- [ ] Validate price ranges
- [ ] Check date type compatibility
- [ ] Verify no overlapping dates (or overlap acceptable)

### Phase 2: Data Quality Audit (1 hour)
- [ ] Check for data gaps
- [ ] Validate price volatility
- [ ] Compare yahoo vs production in overlap period
- [ ] Manual spot check (5 random dates)

### Phase 3: Dry Run (30 min)
- [ ] Create views (non-destructive)
- [ ] Test view queries
- [ ] Run dry run backfill (no actual INSERT)
- [ ] Validate expected row counts

### Phase 4: Rollback Plan (15 min)
- [ ] Document rollback commands
- [ ] Test backup restoration (on test table)
- [ ] Create rollback script

---

## 🚨 GO/NO-GO DECISION CRITERIA

### ✅ SAFE TO PROCEED IF:

1. **Schema**: Symbol matches ('ZL'), date types compatible
2. **Overlap**: < 100 overlapping days OR prices match closely
3. **Quality**: < 500 missing days, prices in range, no extreme volatility
4. **Backups**: All backups created successfully
5. **Cost**: Estimated cost < $5
6. **Dry Run**: Expected row counts match

### ❌ STOP INTEGRATION IF:

1. **Schema**: Symbol mismatch (ZL vs ZL1!), incompatible types
2. **Overlap**: > 500 overlapping days with >5% price divergence
3. **Quality**: > 1000 missing days, prices out of range, suspicious moves
4. **Backups**: Backup creation failed
5. **Cost**: Estimated cost > $20
6. **Dry Run**: Row counts don't match expectations

---

## 📋 AUDIT RESULTS TEMPLATE

```markdown
# Yahoo Finance Integration - Audit Results
Date: [DATE]
Auditor: [NAME]

## Schema Validation
- [✅/❌] Symbol standardization: [RESULT]
- [✅/❌] Price range validation: [RESULT]
- [✅/❌] Date overlap check: [RESULT]

## Data Quality
- [✅/❌] Data gaps: [X missing days / Y%]
- [✅/❌] Price volatility: [Max move: X%]
- [✅/❌] Source comparison: [Avg diff: X%]

## Safety Checks
- [✅/❌] Backups created: [List]
- [✅/❌] Rollback plan: [Status]
- [✅/❌] Cost estimate: [$X]

## Decision
- [✅ GO / ❌ NO-GO]
- Justification: [EXPLANATION]
```

---

## 🔧 RECOMMENDED NEXT STEPS

### If GO Decision:
1. Execute integration SQL (Step 1: Views)
2. Validate views created correctly
3. Run backfill (with overlap exclusion)
4. Verify backfill results
5. Rebuild production training tables
6. Validate training data quality

### If NO-GO Decision:
1. Document specific issues found
2. Create remediation plan
3. Fix data quality issues
4. Re-run audit
5. Get approval before retry

---

**Last Updated**: November 12, 2025  
**Framework Version**: 1.0  
**Estimated Audit Time**: 2-3 hours  
**Risk Mitigation**: HIGH - Critical for data integrity

