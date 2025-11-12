#!/bin/bash
#
# Archive old tables to avoid confusion
# This prefixes old tables with _ARCHIVED_ so they're hidden but not deleted
# Date: November 5, 2025
#

set -e

PROJECT="cbi-v14"
DATASET="models_v4"

echo "==============================================="
echo "ARCHIVING OLD TABLES TO CLEAN UP WORKSPACE"
echo "==============================================="
echo ""
echo "This will rename old tables with _ARCHIVED_ prefix"
echo "Production tables will NOT be touched"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# List of tables to archive (that aren't already archived)
TABLES_TO_ARCHIVE=(
    "training_dataset_super_enriched"
    "training_dataset_automl"
    "training_dataset_current"
    "training_dataset_baseline_clean"
    "training_dataset_baseline_complete"
    "training_dataset_clean"
    "training_dataset"
    "training_data"
    "enhanced_features"
    "features_complete"
    "features_enriched"
    "_contract_207"
    "_contract_209"
)

echo ""
echo "📦 Archiving old tables..."
echo ""

for TABLE in "${TABLES_TO_ARCHIVE[@]}"; do
    # Check if table exists
    if bq ls -n 1000 "$PROJECT:$DATASET" | grep -q "^  $TABLE "; then
        # Check if archived version already exists
        if bq ls -n 1000 "$PROJECT:$DATASET" | grep -q "^  _ARCHIVED_$TABLE "; then
            echo "⏭️  Skipping $TABLE (archived version already exists)"
        else
            echo "📦 Archiving: $TABLE → _ARCHIVED_$TABLE"
            bq cp -f "$PROJECT:$DATASET.$TABLE" "$PROJECT:$DATASET._ARCHIVED_$TABLE"
            bq rm -f -t "$PROJECT:$DATASET.$TABLE"
            echo "✅ Archived: $TABLE"
        fi
    else
        echo "⏭️  Skipping $TABLE (doesn't exist)"
    fi
done

echo ""
echo "==============================================="
echo "✅ ARCHIVAL COMPLETE"
echo "==============================================="
echo ""
echo "📋 PRODUCTION TABLES (KEPT):"
echo "  • production_training_data_1w"
echo "  • production_training_data_1m"
echo "  • production_training_data_3m"
echo "  • production_training_data_6m"
echo "  • bqml_1w"
echo "  • bqml_1m"
echo "  • bqml_3m"
echo "  • bqml_6m"
echo ""
echo "📦 ARCHIVED TABLES:"
echo "  All old training_dataset_* tables now prefixed with _ARCHIVED_"
echo ""
echo "🗄️ DAILY AGGREGATIONS (KEPT for ingestion):"
echo "  • cftc_daily_filled"
echo "  • news_intelligence_daily"
echo "  • palm_oil_complete"
echo "  • social_sentiment_daily"
echo "  • trump_policy_daily"
echo "  • usda_export_daily"
echo "  • currency_complete"
echo "  • rin_prices_daily"
echo "  • rfs_mandates_daily"
echo "  • freight_logistics_daily"
echo "  • argentina_port_logistics_daily"
echo ""
echo "Next step: Run MEGA_CONSOLIDATION_ALL_DATA.sql to merge all data"
echo ""






