#!/usr/bin/env bash
set -euo pipefail
PROJECT="cbi-v14"
OUT="${HOME}/inventory_step3_output.txt"

echo "=== START STEP 3 INVENTORY $(date -u) ===" > "${OUT}"

# ===== BigQuery Inventory =====
echo -e "\n# BigQuery datasets in project ${PROJECT}" | tee -a "${OUT}"
gcloud bigquery datasets list --project="${PROJECT}" --format="table(datasetReference.datasetId,location)" | tee -a "${OUT}"

DATASET="forecasting_data_warehouse"
echo -e "\n# Tables in dataset ${DATASET}" | tee -a "${OUT}"
bq ls --project_id="${PROJECT}" "${DATASET}" | tee -a "${OUT}" || echo "Dataset ${DATASET} not found" | tee -a "${OUT}"

# Expected core tables
EXPECTED_TABLES=(economic_indicators fed_rates soybean_prices weather_data)
for T in "${EXPECTED_TABLES[@]}"; do
  if bq show --project_id="${PROJECT}" "${DATASET}.${T}" >/dev/null 2>&1; then
    echo "✓ Table exists: ${T}" | tee -a "${OUT}"
  else
    echo "MISSING: ${T} — would create with:" | tee -a "${OUT}"
    echo "bq mk --table ${PROJECT}:${DATASET}.${T} schema.json" | tee -a "${OUT}"
  fi
done

# ===== Storage Inventory =====
echo -e "\n# Storage buckets (gsutil)" | tee -a "${OUT}"
gsutil ls -p "${PROJECT}" | tee -a "${OUT}"

# Expected buckets
EXPECTED_BUCKETS=("forecasting-app-raw-data-bucket" "forecasting-app-processed-data-bucket")
for B in "${EXPECTED_BUCKETS[@]}"; do
  if gsutil ls -p "${PROJECT}" "gs://${B}" >/dev/null 2>&1; then
    echo "✓ Bucket exists: ${B}" | tee -a "${OUT}"
  else
    echo "MISSING: ${B} — would create with:" | tee -a "${OUT}"
    echo "gsutil mb -p ${PROJECT} -c STANDARD -l us-central1 gs://${B}" | tee -a "${OUT}"
  fi
done

echo -e "\n=== END STEP 3 INVENTORY $(date -u) ===" | tee -a "${OUT}"
echo "Results saved to: ${OUT}"
