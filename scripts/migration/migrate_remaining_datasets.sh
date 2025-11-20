#!/bin/bash
# Migrate remaining US datasets to us-central1
# Date: November 15, 2025
set -e

PROJECT="cbi-v14"
BUCKET="gs://cbi-v14-migration-us-central1"
DATASETS=("dashboard" "market_data" "weather")

echo "========================================================================"
echo "MIGRATING REMAINING DATASETS: US → us-central1"
echo "========================================================================"

# Export, Load, Swap (same process as before)
for ds in "${DATASETS[@]}"; do
    echo ""
    echo "📦 Migrating $ds..."
    
    # Check if dataset has tables
    table_count=$(bq ls --location=us-central1 ${PROJECT}:${ds} 2>/dev/null | tail -n +3 | wc -l | xargs)
    
    if [ "$table_count" -eq "0" ]; then
        echo "   ⚠️  $ds is empty, skipping"
        continue
    fi
    
    # Export
    echo "   → Exporting..."
    tables=$(bq ls --location=us-central1 --max_results=9999 ${PROJECT}:${ds} | awk 'NR>2 {print $1}')
    for table in $tables; do
        bq extract --location=us-central1 \
            --destination_format=PARQUET \
            --compression=SNAPPY \
            ${PROJECT}:${ds}.${table} \
            ${BUCKET}/${ds}/${table}-*.parquet &
    done
    wait
    
    # Create tmp dataset
    echo "   → Creating tmp dataset in us-central1..."
    bq mk --dataset --location=us-central1 ${PROJECT}:${ds}_tmp 2>/dev/null || echo "     (exists)"
    
    # Load
    echo "   → Loading into us-central1..."
    for table in $tables; do
        bq load --location=us-central1 \
            --source_format=PARQUET \
            --replace \
            ${PROJECT}:${ds}_tmp.${table} \
            ${BUCKET}/${ds}/${table}-*.parquet &
    done
    wait
    
    # Backup old
    echo "   → Creating backup..."
    bq mk --dataset --location=us-central1 ${PROJECT}:${ds}_backup_20251115_final 2>/dev/null || echo "     (exists)"
    for table in $tables; do
        bq cp -f ${PROJECT}:${ds}.${table} ${PROJECT}:${ds}_backup_20251115_final.${table}
    done
    
    # Swap
    echo "   → Swapping datasets..."
    bq rm -r -f -d ${PROJECT}:${ds}
    bq mk --dataset --location=us-central1 ${PROJECT}:${ds}
    for table in $tables; do
        bq cp -f ${PROJECT}:${ds}_tmp.${table} ${PROJECT}:${ds}.${table}
    done
    bq rm -r -f -d ${PROJECT}:${ds}_tmp
    
    echo "   ✅ $ds migrated to us-central1"
done

echo ""
echo "========================================================================"
echo "✅ ALL REMAINING DATASETS MIGRATED"
echo "========================================================================"






