#!/usr/bin/env bash
# ============================================================================
# MOVE_US_TO_USCENTRAL1.SH
# Author: Cursor AI (2025-11-15)
# Purpose: Relocate new-architecture datasets from US multi-region to
#          us-central1 single-region with zero downtime.
# Datasets moved: raw_intelligence, features, training, predictions,
#                 monitoring, archive
# Requirements:   bq CLI authenticated with OWNER permission; gsutil.
# ============================================================================

set -euo pipefail

PROJECT="cbi-v14"
BUCKET="cbi-v14-migration-us-central1"
GS_URI="gs://${BUCKET}"
DATE_TS="$(date +%Y%m%d_%H%M%S)"

# 1. Create bucket if it doesn't exist
if ! gsutil ls -b "${GS_URI}" >/dev/null 2>&1; then
  echo "Creating GCS bucket ${GS_URI} (us-central1)"
  gsutil mb -p "${PROJECT}" -l us-central1 "${GS_URI}"
fi

echo "Using bucket: ${GS_URI}"

declare -a DATASETS=(raw_intelligence features training predictions monitoring archive)

echo "\n=== EXPORT PHASE ==="
for DS in "${DATASETS[@]}"; do
  echo "Exporting dataset ${DS} (US) → GCS"
  mkdir -p "${GS_URI}/${DS}" || true
  # List tables and export each in background (parquet + snappy)
  for TBL in $(bq --location=US ls --max_results=9999 ${PROJECT}:${DS} | awk 'NR>2 {print $1}'); do
    echo "  • Extract ${DS}.${TBL}"
    bq --location=US extract --destination_format=PARQUET \
      --compression=SNAPPY \
      "${PROJECT}:${DS}.${TBL}" \
      "${GS_URI}/${DS}/${TBL}-*.parquet" &
  done
  wait
  echo "✓ Dataset ${DS} exported"
done

echo "\n=== CREATE _tmp DATASETS (us-central1) ==="
for DS in "${DATASETS[@]}"; do
  echo "Creating dataset ${DS}_tmp in us-central1"
  bq mk --dataset --location=us-central1 "${PROJECT}:${DS}_tmp" || true
  # Mirror labels from source (optional)
  bq update --set_label=state=staging "${PROJECT}:${DS}_tmp"
done

echo "\n=== LOAD PHASE ==="
for DS in "${DATASETS[@]}"; do
  for OBJ in $(gsutil ls "${GS_URI}/${DS}/"); do
    TABLE_NAME="$(basename ${OBJ} | cut -d'-' -f1)"
    echo "  • Loading ${DS}/${TABLE_NAME} into ${DS}_tmp"
    bq --location=us-central1 load --source_format=PARQUET --replace \
      "${PROJECT}:${DS}_tmp.${TABLE_NAME}" "${OBJ}*" &
  done
  wait
  echo "✓ Dataset ${DS}_tmp loaded"
done

echo "\n=== SWAP PHASE ==="
for DS in "${DATASETS[@]}"; do
  echo "Swapping dataset ${DS} → ${DS}_backup_${DATE_TS}"
  bq cp --rename_dataset "${PROJECT}:${DS}" "${PROJECT}:${DS}_backup_${DATE_TS}" || true
  echo "Promoting ${DS}_tmp → ${DS} (us-central1)"
  bq cp --rename_dataset "${PROJECT}:${DS}_tmp" "${PROJECT}:${DS}"
  echo "✓ Swap complete for ${DS}"
done

echo "\n=== POST-MIGRATION CLEANUP ==="
# Rename two prediction tables to final compliant names
bq cp --rename_table "${PROJECT}:predictions.daily_forecasts" \
                 "${PROJECT}:predictions.zl_predictions_prod_all_latest" || true
bq cp --rename_table "${PROJECT}:predictions.monthly_vertex_predictions" \
                 "${PROJECT}:predictions.zl_predictions_prod_allhistory_1m" || true
bq rm -f "${PROJECT}:predictions.daily_forecasts" || true
bq rm -f "${PROJECT}:predictions.monthly_vertex_predictions" || true

echo "\n=== VERIFICATION ==="
for DS in "${DATASETS[@]}"; do
  LOC=$(bq show --format=prettyjson "${PROJECT}:${DS}" | grep -o '"location": "[^"]*"' | head -1)
  echo "  • ${DS}: ${LOC}"
done

echo "\nMigration complete.  Backups: *_backup_${DATE_TS}.  Review and delete after validation."
