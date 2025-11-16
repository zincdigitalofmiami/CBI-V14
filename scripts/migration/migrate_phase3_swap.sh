#!/bin/bash
# Phase 3: Atomic dataset swap
set -e

PROJECT="cbi-v14"
DATASETS=("raw_intelligence" "training" "features" "predictions" "monitoring" "archive")
BACKUP_DATE=$(date +%Y%m%d)

echo "========================================================================"
echo "PHASE 3: Atomic Dataset Swap"
echo "========================================================================"
echo "Backup suffix: _backup_${BACKUP_DATE}"
echo ""

# Step 1: Rename old datasets (US) to backups
echo "Step 1: Renaming old datasets to backups..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo "Renaming ${ds} -> ${ds}_backup_${BACKUP_DATE}..."
    
    # Copy dataset to backup name
    bq mk --dataset --location=US ${PROJECT}:${ds}_backup_${BACKUP_DATE}
    
    # Copy all tables
    tables=$(bq ls --location=US --max_results=9999 ${PROJECT}:${ds} | awk 'NR>2 {print $1}')
    for table in $tables; do
        bq cp -f ${PROJECT}:${ds}.${table} ${PROJECT}:${ds}_backup_${BACKUP_DATE}.${table}
    done
    
    echo "  ✅ ${ds} backed up"
done

echo ""
echo "Step 2: Deleting old datasets..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo "Deleting ${ds}..."
    bq rm -r -f -d ${PROJECT}:${ds}
    echo "  ✅ ${ds} deleted"
done

echo ""
echo "Step 3: Renaming _tmp datasets to canonical names..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo "Renaming ${ds}_tmp -> ${ds}..."
    
    # Create new dataset with canonical name in us-central1
    bq mk --dataset --location=us-central1 ${PROJECT}:${ds}
    
    # Copy all tables
    tables=$(bq ls --location=us-central1 --max_results=9999 ${PROJECT}:${ds}_tmp | awk 'NR>2 {print $1}')
    for table in $tables; do
        bq cp -f ${PROJECT}:${ds}_tmp.${table} ${PROJECT}:${ds}.${table}
    done
    
    echo "  ✅ ${ds} in us-central1"
done

echo ""
echo "Step 4: Cleaning up _tmp datasets..."
echo "------------------------------------------------------------------------"

for ds in "${DATASETS[@]}"; do
    echo "Deleting ${ds}_tmp..."
    bq rm -r -f -d ${PROJECT}:${ds}_tmp
    echo "  ✅ ${ds}_tmp deleted"
done

echo ""
echo "========================================================================"
echo "✅ PHASE 3 COMPLETE: All datasets now in us-central1"
echo "========================================================================"
echo ""
echo "📊 Verify locations:"
for ds in "${DATASETS[@]}"; do
    loc=$(bq show --format=prettyjson ${PROJECT}:${ds} | grep -o '"location": "[^"]*"' | cut -d'"' -f4)
    echo "  ${ds}: ${loc}"
done

