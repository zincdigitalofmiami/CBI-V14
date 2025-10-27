#!/bin/bash
# Monitor training status

echo "=================================================="
echo "🔍 MONITORING ENRICHED MODEL TRAINING STATUS"
echo "=================================================="
echo ""

echo "📊 Checking for new models..."
bq ls --models --max_results=20 cbi-v14:models | grep enriched

echo ""
echo "📈 Training dataset status:"
bq query --use_legacy_sql=false "SELECT COUNT(*) as row_count, COUNT(DISTINCT CAST(date AS STRING)) as unique_dates FROM \`cbi-v14.models.training_dataset\` LIMIT 1"

echo ""
echo "✅ V3 Models (should still exist):"
bq ls --models cbi-v14:models | grep "zl_boosted_tree.*v3" | grep -v enriched

echo ""
echo "🆕 Enriched Models (being trained):"
bq ls --models cbi-v14:models | grep enriched

echo ""
echo "=================================================="
echo "To check specific model status:"
echo "bq show cbi-v14:models.zl_boosted_tree_1w_v3_enriched"
echo "=================================================="

