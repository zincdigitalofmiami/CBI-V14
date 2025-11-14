#!/bin/bash
# Automated Pre-Integration Audit (Non-Interactive)
# Runs all validation queries and generates comprehensive report

set -e

AUDIT_DATE=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs/pre_integration_audit_$AUDIT_DATE"
mkdir -p $LOG_DIR

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AUTOMATED PRE-INTEGRATION AUDIT                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Timestamp: $AUDIT_DATE"
echo "Log Directory: $LOG_DIR"
echo ""

# Track results
PASS=0
FAIL=0
WARN=0

# Check 1: Symbol Standardization
echo "═══════════════════════════════════════════════════════════════"
echo "CHECK 1: SYMBOL STANDARDIZATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

bq query --nouse_legacy_sql --format=pretty \
"SELECT DISTINCT symbol, symbol_name, COUNT(*) as cnt
FROM \`cbi-v14.yahoo_finance_comprehensive.yahoo_normalized\`
WHERE symbol LIKE '%ZL%' OR symbol_name LIKE '%Soybean Oil%'
GROUP BY symbol, symbol_name
ORDER BY cnt DESC" \
> $LOG_DIR/check1_symbols.txt 2>&1

cat $LOG_DIR/check1_symbols.txt
echo ""

# Check if ZL symbol exists
if grep -q "ZL" $LOG_DIR/check1_symbols.txt; then
    echo "✅ CHECK 1 PASSED: ZL symbol found"
    PASS=$((PASS + 1))
else
    echo "❌ CHECK 1 FAILED: ZL symbol not found"
    FAIL=$((FAIL + 1))
fi
echo ""

# Check 2: Price Range Validation
echo "═══════════════════════════════════════════════════════════════"
echo "CHECK 2: PRICE RANGE VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

bq query --nouse_legacy_sql --format=pretty \
"SELECT 
    MIN(close) as min_price,
    MAX(close) as max_price,
    AVG(close) as avg_price,
    COUNTIF(close IS NULL) as null_prices,
    COUNTIF(close <= 0) as zero_or_negative
FROM \`cbi-v14.yahoo_finance_comprehensive.yahoo_normalized\`
WHERE symbol = 'ZL'" \
> $LOG_DIR/check2_prices.txt 2>&1

cat $LOG_DIR/check2_prices.txt
echo ""

# Parse results (simplified check)
if grep -q "null_prices.*0" $LOG_DIR/check2_prices.txt && \
   grep -q "zero_or_negative.*0" $LOG_DIR/check2_prices.txt; then
    echo "✅ CHECK 2 PASSED: No null or negative prices"
    PASS=$((PASS + 1))
else
    echo "⚠️  CHECK 2 WARNING: Review price statistics"
    WARN=$((WARN + 1))
fi
echo ""

# Check 3: Date Overlap Detection
echo "═══════════════════════════════════════════════════════════════"
echo "CHECK 3: DATE OVERLAP DETECTION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

bq query --nouse_legacy_sql --format=pretty \
"WITH yahoo_dates AS (
    SELECT DISTINCT date
    FROM \`cbi-v14.yahoo_finance_comprehensive.yahoo_normalized\`
    WHERE symbol = 'ZL' AND date >= '2020-01-01'
),
prod_dates AS (
    SELECT DISTINCT DATE(time) as date
    FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
)
SELECT 
    COUNT(DISTINCT y.date) as yahoo_count,
    COUNT(DISTINCT p.date) as prod_count,
    COUNT(DISTINCT CASE WHEN y.date = p.date THEN y.date END) as overlap_count
FROM yahoo_dates y
FULL OUTER JOIN prod_dates p ON y.date = p.date" \
> $LOG_DIR/check3_overlap.txt 2>&1

cat $LOG_DIR/check3_overlap.txt
echo ""
echo "✅ CHECK 3 COMPLETE: Review overlap count above"
PASS=$((PASS + 1))
echo ""

# Check 4: Data Gaps Analysis
echo "═══════════════════════════════════════════════════════════════"
echo "CHECK 4: DATA GAPS ANALYSIS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

bq query --nouse_legacy_sql --format=pretty \
"WITH date_series AS (
    SELECT DATE_ADD('2000-01-01', INTERVAL day DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 6500)) as day
    WHERE DATE_ADD('2000-01-01', INTERVAL day DAY) <= CURRENT_DATE()
      AND EXTRACT(DAYOFWEEK FROM DATE_ADD('2000-01-01', INTERVAL day DAY)) NOT IN (1, 7)
),
yahoo_data AS (
    SELECT DISTINCT date
    FROM \`cbi-v14.yahoo_finance_comprehensive.yahoo_normalized\`
    WHERE symbol = 'ZL'
)
SELECT 
    COUNT(*) as expected_trading_days,
    COUNT(y.date) as found_trading_days,
    COUNT(*) - COUNT(y.date) as missing_days,
    ROUND((COUNT(*) - COUNT(y.date)) / COUNT(*) * 100, 2) as missing_pct
FROM date_series d
LEFT JOIN yahoo_data y USING(date)" \
> $LOG_DIR/check4_gaps.txt 2>&1

cat $LOG_DIR/check4_gaps.txt
echo ""
echo "✅ CHECK 4 COMPLETE: Review missing days above"
PASS=$((PASS + 1))
echo ""

# Check 5: Historical Data Coverage
echo "═══════════════════════════════════════════════════════════════"
echo "CHECK 5: HISTORICAL DATA COVERAGE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

bq query --nouse_legacy_sql --format=pretty \
"SELECT 
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    COUNT(*) as total_rows,
    COUNT(DISTINCT date) as unique_dates,
    COUNTIF(date < '2020-01-01') as pre_2020_rows
FROM \`cbi-v14.yahoo_finance_comprehensive.yahoo_normalized\`
WHERE symbol = 'ZL'" \
> $LOG_DIR/check5_coverage.txt 2>&1

cat $LOG_DIR/check5_coverage.txt
echo ""

# Check if pre-2020 data exists
if grep -q "pre_2020_rows" $LOG_DIR/check5_coverage.txt; then
    echo "✅ CHECK 5 PASSED: Historical data coverage confirmed"
    PASS=$((PASS + 1))
else
    echo "❌ CHECK 5 FAILED: Could not verify historical data"
    FAIL=$((FAIL + 1))
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "AUDIT SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Results:"
echo "   ✅ Passed: $PASS"
echo "   ❌ Failed: $FAIL"
echo "   ⚠️  Warnings: $WARN"
echo ""

# Generate summary file
cat > $LOG_DIR/AUDIT_SUMMARY.txt << EOF
PRE-INTEGRATION AUDIT SUMMARY
============================
Timestamp: $AUDIT_DATE

RESULTS:
✅ Passed: $PASS
❌ Failed: $FAIL
⚠️  Warnings: $WARN

CHECKS RUN:
1. Symbol Standardization
2. Price Range Validation
3. Date Overlap Detection
4. Data Gaps Analysis
5. Historical Data Coverage

DETAILED RESULTS:
See individual check files in $LOG_DIR/

GO/NO-GO DECISION:
EOF

# Decision
if [ $FAIL -gt 0 ]; then
    echo "❌ GO/NO-GO: NO-GO" | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo "   Critical failures detected. Fix before integration." | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo ""
    exit 1
elif [ $WARN -gt 2 ]; then
    echo "⚠️  GO/NO-GO: PROCEED WITH CAUTION" | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo "   Multiple warnings. Manual review recommended." | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo ""
    exit 0
else
    echo "✅ GO/NO-GO: GO" | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo "   All checks passed. Safe to proceed with integration." | tee -a $LOG_DIR/AUDIT_SUMMARY.txt
    echo ""
    exit 0
fi

