#!/bin/bash
# Phase 2: Create datasets in us-central1 and load data
set -e

PROJECT="cbi-v14"
BUCKET="gs://cbi-v14-migration-us-central1"
DATASETS=("raw_intelligence" "training" "features" "predictions" "monitoring" "archive")

echo "========================================================================"
echo "PHASE 2: Creating datasets in us-central1 and loading data"
echo "========================================================================"

# Step 1: Create temporary datasets in us-central1
echo ""
echo "Step 1: Creating temporary datasets in us-central1..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo "Creating ${ds}_tmp..."
    bq mk --dataset --location=us-central1 --description="Temp migration dataset" ${PROJECT}:${ds}_tmp 2>/dev/null || echo "  (already exists)"
done

echo "✅ All temporary datasets created"

# Step 2: Load data from GCS
echo ""
echo "Step 2: Loading data from GCS into us-central1..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo ""
    echo "📥 Loading $ds..."
    
    # Get list of tables from GCS
    tables=$(gsutil ls ${BUCKET}/${ds}/ | sed 's|.*/||' | sed 's/-[0-9]*\.parquet$//' | sort -u)
    
    if [ -z "$tables" ]; then
        echo "   ⚠️  No files found for $ds"
        continue
    fi
    
    table_count=$(echo "$tables" | wc -l | xargs)
    echo "   Found $table_count tables to load"
    
    # Load each table
    for table in $tables; do
        echo "   → Loading $table..."
        bq load --location=us-central1 \
            --source_format=PARQUET \
            --replace \
            ${PROJECT}:${ds}_tmp.${table} \
            ${BUCKET}/${ds}/${table}-*.parquet &
    done
    
    # Wait for this dataset's loads to complete
    wait
    echo "   ✅ $ds loaded"
done

echo ""
echo "========================================================================"
echo "✅ PHASE 2 COMPLETE: All data loaded into us-central1"
echo "========================================================================"







