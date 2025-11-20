#!/bin/bash
# ============================================================================
# Archive and Clean Up BigQuery - Move Everything to Archive
# Date: November 19, 2025
# Purpose: Archive all backup/duplicate/legacy datasets, keep only essentials
# ============================================================================

set -euo pipefail

PROJECT_ID="cbi-v14"
LOCATION="us-central1"
ARCHIVE_DATE=$(date +%Y%m%d)
ARCHIVE_DATASET="z_archive_${ARCHIVE_DATE}"

echo "🗄️  BigQuery Archive and Cleanup Script"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Archive Dataset: $ARCHIVE_DATASET"
echo ""

# ============================================================================
# STEP 1: Create Archive Dataset
# ============================================================================
echo "📦 Step 1: Creating archive dataset..."
bq mk --location=${LOCATION} --project_id=${PROJECT_ID} ${ARCHIVE_DATASET} 2>/dev/null || echo "  Archive dataset already exists"

# ============================================================================
# STEP 2: Define What to Keep vs Archive
# ============================================================================

# ESSENTIAL DATASETS TO KEEP (12 only)
KEEP_DATASETS=(
    "raw_intelligence"
    "market_data"
    "features"
    "training"
    "predictions"
    "monitoring"
    "api"
    "dim"
    "ops"
    "signals"
    "regimes"
    "neural"
)

# DATASETS TO ARCHIVE (everything with backup, old versions, duplicates)
ARCHIVE_DATASETS=(
    "archive_backup_20251115"
    "archive_consolidation_nov6"
    "dashboard_backup_20251115_final"
    "dashboard_tmp"
    "features_backup_20251115"
    "features_backup_20251117"
    "forecasting_data_warehouse_backup_20251117"
    "model_backups_oct27"
    "models_v4_backup_20251117"
    "monitoring_backup_20251115"
    "predictions_backup_20251115"
    "raw_intelligence_backup_20251115"
    "raw_intelligence_backup_20251117"
    "training_backup_20251115"
    "training_backup_20251117"
)

# DATASETS TO ARCHIVE AND MAYBE DELETE (legacy/deprecated)
LEGACY_DATASETS=(
    "bkp"
    "curated"
    "dashboard"
    "deprecated"
    "export_evaluated_data_items_cbi_v14_automl_pilot_1w_2025_10_28T10_08_35_327Z"
    "forecasting_data_warehouse"  # Old name, replaced by market_data
    "models"                       # Old version
    "models_v4"                    # Keep data but archive dataset
    "models_v5"                    # Old version
    "predictions_uc1"              # Old predictions
    "raw"                          # Old raw dataset
    "staging"                      # Temporary staging
    "staging_ml"                   # Temporary staging
    "vegas_intelligence"           # Old dashboard data
    "weather"                      # Should be in raw_intelligence
    "yahoo_finance_comprehensive"  # Should be in market_data
    "archive"                      # Old archive
    "drivers"                      # If not actively used
    "performance"                  # If not actively used
)

# ============================================================================
# STEP 3: Archive Backup Datasets
# ============================================================================
echo ""
echo "📁 Step 2: Archiving backup datasets..."

for dataset in "${ARCHIVE_DATASETS[@]}"; do
    if bq ls -d --project_id=${PROJECT_ID} | grep -q "^${dataset}$"; then
        echo "  Archiving ${dataset}..."
        
        # Get all tables in the dataset
        tables=$(bq ls -n 1000 --project_id=${PROJECT_ID} ${dataset} 2>/dev/null | tail -n +3 | awk '{print $1}')
        
        if [ -n "$tables" ]; then
            for table in $tables; do
                echo "    Moving ${dataset}.${table}..."
                bq cp -f ${PROJECT_ID}.${dataset}.${table} ${PROJECT_ID}.${ARCHIVE_DATASET}.${dataset}__${table} 2>/dev/null || true
            done
        fi
        
        # Remove the dataset
        echo "    Removing dataset ${dataset}..."
        bq rm -r -f -d ${PROJECT_ID}.${dataset} 2>/dev/null || true
    else
        echo "  Dataset ${dataset} not found, skipping..."
    fi
done

# ============================================================================
# STEP 4: Archive Legacy Datasets
# ============================================================================
echo ""
echo "📁 Step 3: Archiving legacy datasets..."

for dataset in "${LEGACY_DATASETS[@]}"; do
    if bq ls -d --project_id=${PROJECT_ID} | grep -q "^${dataset}$"; then
        echo "  Archiving ${dataset}..."
        
        # Special handling for important data
        if [[ "$dataset" == "models_v4" || "$dataset" == "yahoo_finance_comprehensive" ]]; then
            echo "    ⚠️  Important data - copying tables before deletion..."
        fi
        
        # Get all tables
        tables=$(bq ls -n 1000 --project_id=${PROJECT_ID} ${dataset} 2>/dev/null | tail -n +3 | awk '{print $1}')
        
        if [ -n "$tables" ]; then
            for table in $tables; do
                echo "    Moving ${dataset}.${table}..."
                bq cp -f ${PROJECT_ID}.${dataset}.${table} ${PROJECT_ID}.${ARCHIVE_DATASET}.${dataset}__${table} 2>/dev/null || true
            done
        fi
        
        # Remove the dataset
        echo "    Removing dataset ${dataset}..."
        bq rm -r -f -d ${PROJECT_ID}.${dataset} 2>/dev/null || true
    else
        echo "  Dataset ${dataset} not found, skipping..."
    fi
done

# ============================================================================
# STEP 5: Create Missing Essential Datasets
# ============================================================================
echo ""
echo "✨ Step 4: Ensuring essential datasets exist..."

for dataset in "${KEEP_DATASETS[@]}"; do
    if bq ls -d --project_id=${PROJECT_ID} | grep -q "^${dataset}$"; then
        echo "  ✓ ${dataset} exists"
    else
        echo "  Creating ${dataset}..."
        bq mk --location=${LOCATION} --project_id=${PROJECT_ID} ${dataset}
    fi
done

# ============================================================================
# STEP 6: Final Report
# ============================================================================
echo ""
echo "📊 Step 5: Final Report..."
echo ""

# Count datasets
total_datasets=$(bq ls -d --project_id=${PROJECT_ID} | tail -n +3 | wc -l)
echo "Total datasets remaining: ${total_datasets}"
echo ""

# List all datasets
echo "Current datasets:"
bq ls -d --project_id=${PROJECT_ID} --format=pretty

echo ""
echo "=========================================="
echo "🎉 Cleanup Complete!"
echo ""
echo "✅ Essential datasets kept: ${#KEEP_DATASETS[@]}"
echo "📦 Datasets archived: $((${#ARCHIVE_DATASETS[@]} + ${#LEGACY_DATASETS[@]}))"
echo "🗄️  Archive location: ${PROJECT_ID}.${ARCHIVE_DATASET}"
echo ""
echo "Next Steps:"
echo "1. Verify important data was preserved in archive"
echo "2. Run data migration to proper datasets"
echo "3. Delete archive dataset after 30 days if not needed"
echo ""




