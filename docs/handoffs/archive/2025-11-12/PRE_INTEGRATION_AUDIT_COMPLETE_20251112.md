---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Pre-Integration Audit Framework - Implementation Complete
**Date**: November 12, 2025  
**Status**: READY FOR EXECUTION  
**Priority**: CRITICAL - Run BEFORE integration

---

## 🎯 WHAT WAS CREATED

Comprehensive pre-integration audit framework with **5 risk categories** and **complete rollback plan**.

---

## 📁 FILES CREATED

### 1. Audit Framework Documentation
**File**: `docs/audits/PRE_INTEGRATION_AUDIT_FRAMEWORK_20251112.md`

**Contents**:
- 5 critical risks identified
- Validation queries for each risk
- Pass/fail criteria
- Complete checklist
- GO/NO-GO decision framework

### 2. Schema Validation Script
**File**: `scripts/validate_yahoo_schema.py`

**Checks**:
- Symbol standardization (ZL vs ZL=F vs ZL1!)
- Price range validation ($25-90 expected)
- Date type compatibility
- Overlap detection with production

**Usage**:
```bash
python3 scripts/validate_yahoo_schema.py
```

**Exit codes**:
- 0 = SAFE TO PROCEED
- 1 = STOP - Issues found

### 3. Data Quality Audit Script
**File**: `scripts/yahoo_quality_report.py`

**Checks**:
- Data gaps (missing trading days)
- Price volatility (detect bad data)
- Yahoo vs production comparison
- Extreme price movements

**Usage**:
```bash
python3 scripts/yahoo_quality_report.py
```

**Exit codes**:
- 0 = Quality acceptable
- 1 = Critical quality issues

### 4. Master Audit Script
**File**: `scripts/run_pre_integration_audit.sh`

**Features**:
- Guided interactive audit
- Prompts for BigQuery query results
- Generates audit summary
- GO/NO-GO decision
- Creates timestamped logs

**Usage**:
```bash
./scripts/run_pre_integration_audit.sh
```

### 5. Rollback Script
**File**: `scripts/rollback_integration.sh`

**Features**:
- Drops integration views
- Removes regime tables
- Restores from backups
- Verification checks
- Guided rollback process

**Usage**:
```bash
./scripts/rollback_integration.sh
```

---

## ⚠️ 5 CRITICAL RISKS ASSESSED

### Risk 1: Schema Mismatch ⚠️ HIGH
**Issue**: Yahoo uses `date DATE`, production uses `time TIMESTAMP`  
**Mitigation**: Views handle conversion  
**Validation**: Symbol check, date type check

### Risk 2: Duplicate Data ⚠️ HIGH
**Issue**: Backfill may create duplicates if overlap exists  
**Mitigation**: Exclude 2020+ dates in backfill  
**Validation**: Overlap detection query

### Risk 3: Data Quality ⚠️ MEDIUM
**Issue**: Gaps, bad prices, extreme volatility  
**Mitigation**: Quality validation before integration  
**Validation**: Gap analysis, volatility check

### Risk 4: Production Corruption ⚠️ HIGH
**Issue**: Integration could break existing tables  
**Mitigation**: Create backups BEFORE integration  
**Validation**: Rollback plan tested

### Risk 5: Cost Spike ⚠️ MEDIUM
**Issue**: Large scans = unexpected costs  
**Mitigation**: Dry run estimates, cost limits  
**Validation**: Table size check

---

## ✅ AUDIT CHECKLIST

### Phase 0: Backups (CRITICAL)
- [ ] Run: `bq cp cbi-v14:models_v4.production_training_data_1w cbi-v14:models_v4.production_training_data_1w_backup_20251112`
- [ ] Run: `bq cp cbi-v14:models_v4.production_training_data_1m cbi-v14:models_v4.production_training_data_1m_backup_20251112`
- [ ] Run: `bq cp cbi-v14:forecasting_data_warehouse.soybean_oil_prices cbi-v14:forecasting_data_warehouse.soybean_oil_prices_backup_20251112`
- [ ] Verify backups created

### Phase 1: Schema Validation
- [ ] Run symbol standardization query
- [ ] Check: Symbol is 'ZL' (not ZL=F or ZL1!)
- [ ] Run price range query
- [ ] Check: Prices in $25-90 range, no NULLs
- [ ] Run date overlap query
- [ ] Check: Overlap manageable (<100 days) OR prices match

### Phase 2: Data Quality
- [ ] Run data gaps query
- [ ] Check: Missing days < 500 (<10%)
- [ ] Run volatility query
- [ ] Check: Max daily move < 25%
- [ ] Run yahoo vs production comparison
- [ ] Check: Average difference < 5%

### Phase 3: Dry Run
- [ ] Create views (Step 1 of integration SQL)
- [ ] Query views to verify row counts
- [ ] Run backfill dry run (no INSERT)
- [ ] Verify expected row counts match

### Phase 4: Rollback Readiness
- [ ] Review rollback_integration.sh
- [ ] Document backup timestamps
- [ ] Test backup restoration (optional)
- [ ] Confirm rollback plan understood

---

## 🚨 GO/NO-GO CRITERIA

### ✅ SAFE TO PROCEED IF:

1. ✅ Symbol is 'ZL' (standard)
2. ✅ Prices in $10-$200 range (no corruption)
3. ✅ No NULL or negative prices
4. ✅ Overlap < 100 days OR prices match closely
5. ✅ Missing days < 500 (<10% of trading days)
6. ✅ Max daily move < 25%
7. ✅ Backups created successfully
8. ✅ Dry run row counts match expectations

### ❌ STOP INTEGRATION IF:

1. ❌ Symbol mismatch (ZL vs ZL1!)
2. ❌ Prices outside $5-$300 range
3. ❌ NULL or negative prices found
4. ❌ Overlap > 500 days with >5% price divergence
5. ❌ Missing days > 1000 (>20% gaps)
6. ❌ Max daily move > 50% (data corruption)
7. ❌ Backup creation failed
8. ❌ Dry run row counts don't match

---

## 📋 EXECUTION SEQUENCE

### Recommended Order:

1. **Today** (30 min):
   ```bash
   # Create backups (manual BigQuery commands)
   # See Phase 0 checklist above
   ```

2. **Today** (1-2 hours):
   ```bash
   # Run master audit script
   ./scripts/run_pre_integration_audit.sh
   
   # Review audit summary
   cat logs/pre_integration_audit_*/audit_summary.txt
   ```

3. **Decision Point**:
   - If GO: Proceed to integration
   - If NO-GO: Fix issues, re-audit

4. **If GO** (Tomorrow):
   ```bash
   # Run integration SQL
   bq query --nouse_legacy_sql < config/bigquery/bigquery-sql/INTEGRATE_YAHOO_FINANCE_HISTORICAL.sql
   ```

5. **If Issues** (Anytime):
   ```bash
   # Rollback
   ./scripts/rollback_integration.sh
   ```

---

## 📊 VALIDATION QUERIES (Quick Reference)

### Query 1: Symbol Check
```sql
SELECT DISTINCT symbol, symbol_name, COUNT(*) as cnt
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol LIKE '%ZL%' OR symbol_name LIKE '%Soybean Oil%'
GROUP BY symbol, symbol_name
ORDER BY cnt DESC;
```
**Expected**: 'ZL' with high row count

### Query 2: Price Range
```sql
SELECT 
    MIN(close) as min_price,
    MAX(close) as max_price,
    AVG(close) as avg_price,
    COUNTIF(close IS NULL) as nulls,
    COUNTIF(close <= 0) as zeros
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL';
```
**Expected**: min ~$25, max ~$90, no nulls/zeros

### Query 3: Overlap Detection
```sql
WITH yahoo_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL' AND date >= '2020-01-01'
),
prod_dates AS (
    SELECT DISTINCT DATE(time) as date
    FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
)
SELECT 
    COUNT(DISTINCT y.date) as yahoo_count,
    COUNT(DISTINCT p.date) as prod_count,
    COUNT(DISTINCT CASE WHEN y.date = p.date THEN y.date END) as overlap
FROM yahoo_dates y
FULL OUTER JOIN prod_dates p ON y.date = p.date;
```
**Expected**: overlap < 100 days

### Query 4: Data Gaps
```sql
WITH date_series AS (
    SELECT DATE_ADD('2000-01-01', INTERVAL day DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 6500)) as day
    WHERE DATE_ADD('2000-01-01', INTERVAL day DAY) <= CURRENT_DATE()
      AND EXTRACT(DAYOFWEEK FROM DATE_ADD('2000-01-01', INTERVAL day DAY)) NOT IN (1, 7)
),
yahoo_data AS (
    SELECT DISTINCT date
    FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
    WHERE symbol = 'ZL'
)
SELECT 
    COUNT(*) as expected,
    COUNT(y.date) as found,
    COUNT(*) - COUNT(y.date) as missing
FROM date_series d
LEFT JOIN yahoo_data y USING(date);
```
**Expected**: missing < 500 days

---

## ⚠️ KNOWN ISSUES & MITIGATIONS

### Issue 1: Python Scripts Crash
**Symptom**: validate_yahoo_schema.py exits with code 139  
**Cause**: Large result sets, memory issues  
**Mitigation**: Use manual BigQuery queries instead  
**Status**: Manual queries provided in audit script

### Issue 2: Overlap with Production
**Symptom**: 2020-2025 dates exist in both sources  
**Cause**: Yahoo has recent data too  
**Mitigation**: Backfill excludes dates >= 2020-01-01  
**Status**: Handled in integration SQL

### Issue 3: Symbol Variants
**Symptom**: Multiple symbols (ZL, ZL=F, ZL1!)  
**Cause**: Different Yahoo Finance naming conventions  
**Mitigation**: Symbol check identifies primary symbol  
**Status**: Validation query catches this

---

## 📞 SUPPORT

### If Audit Fails:
1. Review `logs/pre_integration_audit_*/audit_summary.txt`
2. Check specific failed queries
3. Investigate data quality in BigQuery Console
4. Fix issues in source data or integration plan
5. Re-run audit

### If Integration Fails:
1. Run `./scripts/rollback_integration.sh`
2. Review error logs
3. Check integration SQL for issues
4. Fix and retry

### If Rollback Needed:
1. Have backup timestamp ready
2. Run rollback script
3. Verify restoration complete
4. Fix root cause
5. Re-run audit before retry

---

## 🎯 SUCCESS METRICS

- [ ] All Phase 0 backups created
- [ ] All validation queries pass
- [ ] GO decision from audit script
- [ ] Integration SQL executes successfully
- [ ] Views created and queryable
- [ ] Backfill completes (if executed)
- [ ] No data corruption
- [ ] Rollback plan tested and ready

---

## 📝 NOTES

- **Estimated Time**: 2-3 hours for complete audit
- **Risk Level**: LOW (if all checks pass)
- **Rollback Time**: 15-30 minutes
- **Impact**: Enables 25+ years of historical data for training

---

**Last Updated**: November 12, 2025  
**Framework Version**: 1.0  
**Status**: COMPLETE - Ready for execution  
**Next Step**: Run `./scripts/run_pre_integration_audit.sh`

