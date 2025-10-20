#!/bin/bash
# CI Schema Lint: Enforce Canonical Metadata on All New Base Tables
# Run this in GitHub Actions pre-merge to catch schema violations

set -e

PROJECT_ID="cbi-v14"
DATASET_ID="forecasting_data_warehouse"

echo "🔍 Checking for base tables missing canonical metadata..."

# Query for non-compliant tables
QUERY="
WITH t AS (
  SELECT table_name 
  FROM \`${PROJECT_ID}.${DATASET_ID}.INFORMATION_SCHEMA.TABLES\`
  WHERE table_type='BASE TABLE'
    AND table_name NOT LIKE '%_bkp_%'
    AND table_name NOT IN ('feature_metadata', 'extraction_labels', 'raw_ingest', 'backtest_forecast', 'soybean_oil_forecast')
), c AS (
  SELECT table_name, ARRAY_AGG(column_name) AS cols
  FROM \`${PROJECT_ID}.${DATASET_ID}.INFORMATION_SCHEMA.COLUMNS\`
  WHERE column_name IN ('source_name','confidence_score','ingest_timestamp_utc','provenance_uuid')
  GROUP BY table_name
)
SELECT t.table_name, ARRAY_LENGTH(c.cols) AS col_count
FROM t LEFT JOIN c USING(table_name)
WHERE (c.cols IS NULL OR ARRAY_LENGTH(c.cols) < 4)
"

# Run query
RESULT=$(bq query --nouse_legacy_sql --format=csv "$QUERY")

# Check if any non-compliant tables found
if [ "$(echo "$RESULT" | wc -l)" -gt 1 ]; then
  echo "❌ SCHEMA LINT FAILED: Base tables missing canonical metadata:"
  echo "$RESULT"
  echo ""
  echo "Required columns: source_name, confidence_score, ingest_timestamp_utc, provenance_uuid"
  exit 1
else
  echo "✅ SCHEMA LINT PASSED: All base tables have canonical metadata"
  exit 0
fi












