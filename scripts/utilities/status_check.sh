#!/bin/bash
# CBI-V14 Quick Status Check
# Verifies data freshness and system health
# Created: November 6, 2025

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 CBI-V14 QUICK STATUS CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 1. PRODUCTION TRAINING DATA STATUS"
echo "----------------------------------------"
echo "Expected: Nov 5-6, 2025 | Last Known Stale: Sep 10, 2025"
bq query --use_legacy_sql=false \
"SELECT 
  'production_training_data_1w' as dataset,
  MAX(date) as latest_date,
  COUNT(*) as total_rows,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM \`cbi-v14.models_v4.production_training_data_1w\`
UNION ALL
SELECT 
  'production_training_data_1m' as dataset,
  MAX(date) as latest_date,
  COUNT(*) as total_rows,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM \`cbi-v14.models_v4.production_training_data_1m\`
UNION ALL
SELECT 
  'production_training_data_3m' as dataset,
  MAX(date) as latest_date,
  COUNT(*) as total_rows,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM \`cbi-v14.models_v4.production_training_data_3m\`
UNION ALL
SELECT 
  'production_training_data_6m' as dataset,
  MAX(date) as latest_date,
  COUNT(*) as total_rows,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM \`cbi-v14.models_v4.production_training_data_6m\`
ORDER BY dataset"
echo ""

echo "🧠 2. BIG 8 NEURAL SIGNALS STATUS"
echo "----------------------------------------"
bq query --use_legacy_sql=false \
"SELECT 
  MAX(date) as latest_date,
  COUNT(*) as total_rows,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_behind
FROM \`cbi-v14.neural.vw_big_eight_signals\`"
echo ""

echo "💰 3. CORE PRICE DATA STATUS"
echo "----------------------------------------"
bq query --use_legacy_sql=false \
"SELECT 
  'soybean_oil_prices' as source,
  MAX(DATE(time)) as latest_date,
  COUNT(*) as total_rows
FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`
UNION ALL
SELECT 
  'vix_daily' as source,
  MAX(date) as latest_date,
  COUNT(*) as total_rows
FROM \`cbi-v14.forecasting_data_warehouse.vix_daily\`
UNION ALL
SELECT 
  'cftc_cot' as source,
  MAX(report_date) as latest_date,
  COUNT(*) as total_rows
FROM \`cbi-v14.forecasting_data_warehouse.cftc_cot\`"
echo ""

echo "🤖 4. BQML MODELS STATUS"
echo "----------------------------------------"
bq query --use_legacy_sql=false \
"SELECT 
  table_id as model_name,
  TIMESTAMP_MILLIS(creation_time) as created_date,
  TIMESTAMP_MILLIS(last_modified_time) as last_modified
FROM \`cbi-v14.models_v4.__TABLES__\`
WHERE table_id LIKE 'bqml_%'
ORDER BY table_id"
echo ""

echo "🎯 5. CRITICAL FEATURES CHECK"
echo "----------------------------------------"
echo "Checking for CRUSH MARGIN (0.961 correlation - #1 predictor)"
bq query --use_legacy_sql=false \
"SELECT 
  COUNT(*) as rows_with_crush_margin,
  AVG(crush_margin) as avg_crush_margin,
  MIN(crush_margin) as min_crush_margin,
  MAX(crush_margin) as max_crush_margin
FROM \`cbi-v14.models_v4.production_training_data_1w\`
WHERE crush_margin IS NOT NULL"
echo ""

echo "📈 6. VERTEX AI EXPORT DATA"
echo "----------------------------------------"
bq query --use_legacy_sql=false \
"SELECT 
  COUNT(*) as total_rows,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM \`cbi-v14.export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z.evaluated_data_items\`
WHERE date IS NOT NULL"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ STATUS CHECK COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚨 EXPECTED RESULTS:"
echo "  • Production data: Should be Nov 5-6, 2025 (0-1 days behind)"
echo "  • Big 8 Signals: Should be Nov 6, 2025 (0 days behind)"
echo "  • Price data: Should be Nov 5-6, 2025"
echo "  • Crush margin: Should have non-null values"
echo ""
echo "⚠️  IF DATA IS STALE (>7 days behind):"
echo "  Run: ./scripts/run_ultimate_consolidation.sh"
echo ""

