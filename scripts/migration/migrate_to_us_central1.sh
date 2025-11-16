#!/bin/bash
# Region Migration: US -> us-central1
# Date: November 15, 2025
set -e

PROJECT="cbi-v14"
BUCKET="gs://cbi-v14-migration-us-central1"
DATASETS=("raw_intelligence" "training" "features" "predictions" "monitoring" "archive")

echo "========================================================================"
echo "DATASET REGION MIGRATION: US -> us-central1"
echo "========================================================================"
echo "Project: $PROJECT"
echo "Bucket: $BUCKET"
echo "Datasets: ${DATASETS[@]}"
echo ""

# Phase 1: Export tables from US to GCS
echo "PHASE 1: Exporting tables to GCS..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo ""
    echo "📦 Exporting $ds..."
    
    # Get all tables in the dataset
    tables=$(bq ls --location=US --max_results=9999 ${PROJECT}:${ds} | awk 'NR>2 {print $1}')
    
    if [ -z "$tables" ]; then
        echo "   ⚠️  No tables found in $ds"
        continue
    fi
    
    table_count=$(echo "$tables" | wc -l | xargs)
    echo "   Found $table_count tables"
    
    # Export each table
    for table in $tables; do
        echo "   → Exporting $table..."
        bq extract --location=US \
            --destination_format=PARQUET \
            --compression=SNAPPY \
            ${PROJECT}:${ds}.${table} \
            ${BUCKET}/${ds}/${table}-*.parquet &
    done
    
    # Wait for this dataset's exports to complete
    wait
    echo "   ✅ $ds exported"
done

echo ""
echo "========================================================================"
echo "✅ PHASE 1 COMPLETE: All tables exported to GCS"
echo "========================================================================"

