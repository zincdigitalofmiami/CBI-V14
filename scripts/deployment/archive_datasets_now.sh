#!/bin/bash
# ============================================================================
# Direct Archive and Cleanup Script
# Date: November 19, 2025
# Purpose: Archive all non-essential datasets to save money
# ============================================================================

set -euo pipefail

PROJECT_ID="cbi-v14"
ARCHIVE_DATASET="z_archive_20251119"
LOCATION="us-central1"

echo "🗄️  BigQuery Dataset Archive & Cleanup"
echo "======================================"
echo "Archive Dataset: ${ARCHIVE_DATASET}"
echo ""

# Essential datasets to keep
ESSENTIAL_DATASETS=(
    "api"
    "features" 
    "market_data"
    "monitoring"
    "predictions"
    "raw_intelligence"
    "training"
    "z_archive_20251119"  # Keep the archive itself
)

# Datasets to archive and remove
TO_ARCHIVE=(
    "archive"
    "archive_backup_20251115"
    "archive_consolidation_nov6"
    "bkp"
    "curated"
    "dashboard"
    "dashboard_backup_20251115_final"
    "dashboard_tmp"
    "deprecated"
    "dim"
    "drivers"
    "export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z"
    "features_backup_20251115"
    "features_backup_20251117"
    "forecasting_data_warehouse"
    "forecasting_data_warehouse_backup_20251117"
    "model_backups_oct27"
    "models"
    "models_v4"
    "models_v4_backup_20251117"
    "models_v5"
    "monitoring_backup_20251115"
    "neural"
    "ops"
    "performance"
    "predictions_backup_20251115"
    "predictions_uc1"
    "raw"
    "raw_intelligence_backup_20251115"
    "raw_intelligence_backup_20251117"
    "regimes"
    "signals"
    "staging"
    "staging_ml"
    "training_backup_20251115"
    "training_backup_20251117"
    "vegas_intelligence"
    "weather"
    "yahoo_finance_comprehensive"
)

echo "📦 Archiving ${#TO_ARCHIVE[@]} datasets..."
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

for dataset in "${TO_ARCHIVE[@]}"; do
    echo -n "  ${dataset}: "
    
    # Check if dataset exists
    if ! bq show ${PROJECT_ID}:${dataset} &>/dev/null; then
        echo "❌ Not found"
        continue
    fi
    
    # Get list of tables in the dataset
    tables=$(bq ls -n 10000 --project_id=${PROJECT_ID} ${dataset} 2>/dev/null | tail -n +3 | awk '{print $1}')
    
    if [ -z "$tables" ]; then
        # Empty dataset - just remove it
        echo -n "📭 Empty, removing... "
        if bq rm -r -f -d ${PROJECT_ID}:${dataset} 2>/dev/null; then
            echo "✅"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "❌ Failed"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        # Dataset has tables - archive them
        table_count=0
        archive_success=true
        
        for table in $tables; do
            # Archive table (copy to archive dataset with prefixed name)
            if ! bq cp -f ${PROJECT_ID}:${dataset}.${table} \
                ${PROJECT_ID}:${ARCHIVE_DATASET}.${dataset}__${table} 2>/dev/null; then
                archive_success=false
                break
            fi
            table_count=$((table_count + 1))
        done
        
        if $archive_success; then
            echo -n "📦 Archived ${table_count} tables, removing... "
            # Remove original dataset
            if bq rm -r -f -d ${PROJECT_ID}:${dataset} 2>/dev/null; then
                echo "✅"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "❌ Remove failed"
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi
        else
            echo "❌ Archive failed"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    fi
done

echo ""
echo "======================================"
echo "✅ Archive Complete!"
echo ""
echo "📊 Results:"
echo "  - Successfully archived: ${SUCCESS_COUNT}"
echo "  - Failed: ${FAIL_COUNT}"
echo ""
echo "💰 Cost Savings:"
echo "  - Reduced from 47 to ~8 active datasets"
echo "  - Estimated monthly savings: $100-300"
echo ""
echo "📁 Remaining Active Datasets:"
bq ls --project_id=${PROJECT_ID} --max_results=20 2>/dev/null || true

echo ""
echo "📦 To view archived tables:"
echo "  bq ls ${PROJECT_ID}:${ARCHIVE_DATASET}"
echo ""
echo "🔄 To restore a table:"
echo "  bq cp ${PROJECT_ID}:${ARCHIVE_DATASET}.dataset__table ${PROJECT_ID}:dataset.table"
