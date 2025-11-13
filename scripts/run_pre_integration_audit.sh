#!/bin/bash
# Pre-Integration Audit - Master Script
# Run this BEFORE yahoo_finance_comprehensive integration

set -e

AUDIT_DATE=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs/pre_integration_audit_$AUDIT_DATE"
mkdir -p $LOG_DIR

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   PRE-INTEGRATION AUDIT - Yahoo Finance Comprehensive          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Audit Timestamp: $AUDIT_DATE"
echo "Log Directory: $LOG_DIR"
echo ""

# Track results
PASS=0
FAIL=0
WARN=0

# Phase 0: Backups
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 0: Creating Backups"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "⏳ Backing up critical tables..."

# Backup commands (run manually or uncomment to execute)
echo "📋 Manual backup required:"
echo "   bq cp cbi-v14:models_v4.production_training_data_1w cbi-v14:models_v4.production_training_data_1w_backup_$AUDIT_DATE"
echo "   bq cp cbi-v14:forecasting_data_warehouse.soybean_oil_prices cbi-v14:forecasting_data_warehouse.soybean_oil_prices_backup_$AUDIT_DATE"
echo ""

read -p "Have you created backups? (yes/no): " backup_response
if [ "$backup_response" != "yes" ]; then
    echo "❌ Backups not created - ABORTING AUDIT"
    exit 1
fi

echo "✅ Backups confirmed"
echo ""

# Phase 1: Quick Manual Checks
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 1: Manual BigQuery Checks"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📋 Please run these queries in BigQuery Console:"
echo ""

echo "1. Symbol Check:"
cat << 'EOF'
SELECT DISTINCT symbol, symbol_name, COUNT(*) as cnt
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol LIKE '%ZL%' OR symbol_name LIKE '%Soybean Oil%'
GROUP BY symbol, symbol_name
ORDER BY cnt DESC;
EOF

echo ""
echo "Expected: Should see 'ZL' symbol with high row count"
echo ""

read -p "Symbol check passed? (yes/no/skip): " symbol_check
if [ "$symbol_check" = "yes" ]; then
    PASS=$((PASS + 1))
    echo "✅ Symbol check passed" | tee -a $LOG_DIR/audit_summary.txt
elif [ "$symbol_check" = "no" ]; then
    FAIL=$((FAIL + 1))
    echo "❌ Symbol check failed" | tee -a $LOG_DIR/audit_summary.txt
else
    WARN=$((WARN + 1))
    echo "⚠️  Symbol check skipped" | tee -a $LOG_DIR/audit_summary.txt
fi
echo ""

echo "2. Price Range Check:"
cat << 'EOF'
SELECT 
    MIN(close) as min_price,
    MAX(close) as max_price,
    AVG(close) as avg_price,
    COUNTIF(close IS NULL) as nulls,
    COUNTIF(close <= 0) as zeros
FROM `cbi-v14.yahoo_finance_comprehensive.yahoo_normalized`
WHERE symbol = 'ZL';
EOF

echo ""
echo "Expected: min ~$25, max ~$90, no nulls, no zeros"
echo ""

read -p "Price range check passed? (yes/no/skip): " price_check
if [ "$price_check" = "yes" ]; then
    PASS=$((PASS + 1))
    echo "✅ Price range check passed" | tee -a $LOG_DIR/audit_summary.txt
elif [ "$price_check" = "no" ]; then
    FAIL=$((FAIL + 1))
    echo "❌ Price range check failed" | tee -a $LOG_DIR/audit_summary.txt
else
    WARN=$((WARN + 1))
    echo "⚠️  Price range check skipped" | tee -a $LOG_DIR/audit_summary.txt
fi
echo ""

echo "3. Date Overlap Check:"
cat << 'EOF'
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
    COUNT(DISTINCT CASE WHEN y.date = p.date THEN y.date END) as overlap_count
FROM yahoo_dates y
FULL OUTER JOIN prod_dates p ON y.date = p.date;
EOF

echo ""
echo "Expected: overlap_count < 100 days OR close to yahoo_count (full overlap acceptable if prices match)"
echo ""

read -p "Date overlap check passed? (yes/no/skip): " overlap_check
if [ "$overlap_check" = "yes" ]; then
    PASS=$((PASS + 1))
    echo "✅ Date overlap check passed" | tee -a $LOG_DIR/audit_summary.txt
elif [ "$overlap_check" = "no" ]; then
    FAIL=$((FAIL + 1))
    echo "❌ Date overlap check failed" | tee -a $LOG_DIR/audit_summary.txt
else
    WARN=$((WARN + 1))
    echo "⚠️  Date overlap check skipped" | tee -a $LOG_DIR/audit_summary.txt
fi
echo ""

echo "4. Data Gaps Check:"
cat << 'EOF'
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
    COUNT(*) as expected_days,
    COUNT(y.date) as found_days,
    COUNT(*) - COUNT(y.date) as missing_days
FROM date_series d
LEFT JOIN yahoo_data y USING(date);
EOF

echo ""
echo "Expected: missing_days < 500 (<10% of trading days)"
echo ""

read -p "Data gaps check passed? (yes/no/skip): " gaps_check
if [ "$gaps_check" = "yes" ]; then
    PASS=$((PASS + 1))
    echo "✅ Data gaps check passed" | tee -a $LOG_DIR/audit_summary.txt
elif [ "$gaps_check" = "no" ]; then
    FAIL=$((FAIL + 1))
    echo "❌ Data gaps check failed" | tee -a $LOG_DIR/audit_summary.txt
else
    WARN=$((WARN + 1))
    echo "⚠️  Data gaps check skipped" | tee -a $LOG_DIR/audit_summary.txt
fi
echo ""

# Phase 2: Summary and Decision
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 2: Audit Summary & GO/NO-GO Decision"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📊 Audit Results:" | tee -a $LOG_DIR/audit_summary.txt
echo "   ✅ Passed: $PASS" | tee -a $LOG_DIR/audit_summary.txt
echo "   ❌ Failed: $FAIL" | tee -a $LOG_DIR/audit_summary.txt
echo "   ⚠️  Skipped: $WARN" | tee -a $LOG_DIR/audit_summary.txt
echo ""

# Decision logic
if [ $FAIL -gt 0 ]; then
    echo "❌ GO/NO-GO DECISION: NO-GO" | tee -a $LOG_DIR/audit_summary.txt
    echo "   Critical issues found. Fix before integration." | tee -a $LOG_DIR/audit_summary.txt
    echo ""
    echo "📋 Recommended actions:"
    echo "   1. Review failed checks above"
    echo "   2. Investigate data quality issues"
    echo "   3. Fix issues in source data"
    echo "   4. Re-run audit after fixes"
    echo ""
    exit 1
elif [ $WARN -gt 2 ]; then
    echo "⚠️  GO/NO-GO DECISION: PROCEED WITH CAUTION" | tee -a $LOG_DIR/audit_summary.txt
    echo "   Multiple checks skipped. Manual review recommended." | tee -a $LOG_DIR/audit_summary.txt
    echo ""
    read -p "Proceed despite warnings? (yes/no): " proceed_response
    if [ "$proceed_response" != "yes" ]; then
        echo "❌ Integration aborted by user"
        exit 1
    fi
else
    echo "✅ GO/NO-GO DECISION: GO" | tee -a $LOG_DIR/audit_summary.txt
    echo "   All checks passed. Safe to proceed with integration." | tee -a $LOG_DIR/audit_summary.txt
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AUDIT COMPLETE - See $LOG_DIR/audit_summary.txt              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📋 Next Steps:"
echo "   1. Review audit summary: cat $LOG_DIR/audit_summary.txt"
echo "   2. If GO: Run integration SQL"
echo "   3. If NO-GO: Review and fix issues"
echo ""

