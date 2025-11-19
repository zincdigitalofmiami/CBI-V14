#!/bin/bash
# ============================================================================
# SQL Pre-Flight Validation Script
# Date: November 18, 2025
# Purpose: Validate PRODUCTION_READY_BQ_SCHEMA.sql before deployment
# ============================================================================

set -uo pipefail

PROJECT_ID="cbi-v14"
LOCATION="us-central1"
SCHEMA_FILE="PRODUCTION_READY_BQ_SCHEMA.sql"

echo "🔍 SQL Pre-Flight Validation"
echo "============================================"
echo "Schema file: $SCHEMA_FILE"
echo "Project: $PROJECT_ID"
echo "Location: $LOCATION"
echo ""

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
  echo "❌ ERROR: Schema file not found: $SCHEMA_FILE"
  exit 1
fi

echo "✅ Schema file exists"
echo ""

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# ============================================================================
# Check 1: BigQuery dry-run validation
# ============================================================================
echo "📋 Check 1: BigQuery SQL Syntax (dry-run)"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if bq query --use_legacy_sql=false --project_id=$PROJECT_ID --location=$LOCATION --dry_run < "$SCHEMA_FILE" >/dev/null 2>&1; then
  echo "✅ PASS: SQL syntax is valid"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "❌ FAIL: SQL syntax errors detected"
  echo ""
  echo "Error details:"
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID --location=$LOCATION --dry_run < "$SCHEMA_FILE" 2>&1 | head -10
  FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Check 2: DEFAULT clause detection (BigQuery doesn't support)
# ============================================================================
echo "📋 Check 2: DEFAULT Clause Detection"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

DEFAULT_COUNT=$(grep -c "DEFAULT '" "$SCHEMA_FILE" || true)
if [ "$DEFAULT_COUNT" -eq 0 ]; then
  echo "✅ PASS: No DEFAULT clauses found"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "❌ FAIL: Found $DEFAULT_COUNT DEFAULT clause(s)"
  echo ""
  echo "Lines with DEFAULT:"
  grep -n "DEFAULT '" "$SCHEMA_FILE" | head -5
  FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Check 3: CREATE OR REPLACE usage
# ============================================================================
echo "📋 Check 3: Idempotency (CREATE OR REPLACE)"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

CREATE_COUNT=$(grep -c "^CREATE TABLE" "$SCHEMA_FILE" || true)
CREATE_OR_REPLACE_COUNT=$(grep -c "^CREATE OR REPLACE TABLE" "$SCHEMA_FILE" || true)

if [ "$CREATE_COUNT" -eq 0 ]; then
  echo "✅ PASS: All tables use CREATE OR REPLACE"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "⚠️  WARNING: Found $CREATE_COUNT CREATE TABLE without OR REPLACE"
  echo "   (This may be intentional for some tables)"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Check 4: Required datasets referenced
# ============================================================================
echo "📋 Check 4: Required Datasets Referenced"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

REQUIRED_DATASETS=(
  "market_data"
  "raw_intelligence"
  "signals"
  "features"
  "training"
  "regimes"
  "drivers"
  "neural"
  "predictions"
  "monitoring"
  "dim"
  "ops"
)

MISSING_DATASETS=()
for dataset in "${REQUIRED_DATASETS[@]}"; do
  if ! grep -q "$dataset\." "$SCHEMA_FILE"; then
    MISSING_DATASETS+=("$dataset")
  fi
done

if [ ${#MISSING_DATASETS[@]} -eq 0 ]; then
  echo "✅ PASS: All required datasets referenced"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "❌ FAIL: Missing dataset references:"
  for dataset in "${MISSING_DATASETS[@]}"; do
    echo "   - $dataset"
  done
  FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Check 5: Table count validation
# ============================================================================
echo "📋 Check 5: Expected Table Count"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

TABLE_COUNT=$(grep -c "^CREATE OR REPLACE TABLE" "$SCHEMA_FILE" || true)
EXPECTED_MIN=50

if [ "$TABLE_COUNT" -ge "$EXPECTED_MIN" ]; then
  echo "✅ PASS: Found $TABLE_COUNT tables (expected >= $EXPECTED_MIN)"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "❌ FAIL: Only found $TABLE_COUNT tables (expected >= $EXPECTED_MIN)"
  FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Check 6: Critical tables present
# ============================================================================
echo "📋 Check 6: Critical Tables Present"
echo "--------------------------------------------"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

CRITICAL_TABLES=(
  "features.master_features"
  "signals.big_eight_live"
  "training.regime_calendar"
  "training.zl_training_prod_allhistory_1w"
  "training.mes_training_prod_allhistory_1min"
)

MISSING_TABLES=()
for table in "${CRITICAL_TABLES[@]}"; do
  if ! grep -q "CREATE OR REPLACE TABLE $table" "$SCHEMA_FILE"; then
    MISSING_TABLES+=("$table")
  fi
done

if [ ${#MISSING_TABLES[@]} -eq 0 ]; then
  echo "✅ PASS: All critical tables present"
  PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
  echo "❌ FAIL: Missing critical tables:"
  for table in "${MISSING_TABLES[@]}"; do
    echo "   - $table"
  done
  FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "============================================"
echo "VALIDATION SUMMARY"
echo "============================================"
echo "Total checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS"
echo "Failed: $FAILED_CHECKS"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
  echo "✅ ALL CHECKS PASSED - SQL is ready for deployment"
  exit 0
else
  echo "❌ VALIDATION FAILED - Fix errors before deployment"
  exit 1
fi

