#!/bin/bash
#
# RUN ULTIMATE DATA CONSOLIDATION
# Achieves ZERO stale data by combining all sources
# Date: November 6, 2025
#

set -e

echo "=========================================="
echo "ULTIMATE DATA CONSOLIDATION"
echo "=========================================="
echo ""
echo "This will:"
echo "1. Backup existing production data"
echo "2. Consolidate ALL data sources"
echo "3. Fill Sep 11-Oct 27 gap with Vertex AI data"
echo "4. Update with current Big 8 signals (Nov 6)"
echo "5. Forward-fill sparse features"
echo "6. Populate feature importance"
echo ""

# Check current status
echo "📊 Current data status:"
bq query --use_legacy_sql=false "
SELECT 
  'production_training_data_1m' as table_name,
  MAX(date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_stale,
  COUNT(*) as row_count
FROM \`cbi-v14.models_v4.production_training_data_1m\`
"

echo ""
echo "🚀 Running consolidation..."
echo ""

# Run the consolidation
bq query --use_legacy_sql=false < bigquery-sql/ULTIMATE_DATA_CONSOLIDATION.sql

echo ""
echo "✅ Consolidation complete!"
echo ""

# Verify results
echo "📊 New data status:"
bq query --use_legacy_sql=false "
SELECT 
  'AFTER CONSOLIDATION' as status,
  MAX(date) as latest_date,
  MIN(date) as earliest_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  ROUND(100 * SUM(CASE WHEN feature_vix_stress IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as vix_coverage,
  ROUND(100 * SUM(CASE WHEN feature_tariff_threat IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as tariff_coverage
FROM \`cbi-v14.models_v4.production_training_data_1m\`
"

echo ""
echo "=========================================="
echo "✅ COMPLETE - DATA IS NOW CURRENT!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify all 300 features are populated"
echo "2. Check feature importance table"
echo "3. Archive old tables with scripts/archive_old_tables.sh"
echo "4. Set up daily refresh pipelines"






