#!/usr/bin/env bash
set -euo pipefail
OUT="${HOME}/inventory_restart_step1.txt"
PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

echo "=== INVENTORY RESTART ($(date -u)) ===" > "${OUT}"
echo "# Project: ${PROJECT}" | tee -a "${OUT}"

echo -e "\n# Buckets" | tee -a "${OUT}"
gsutil ls -p "${PROJECT}" | tee -a "${OUT}" || true

echo -e "\n# BigQuery datasets" | tee -a "${OUT}"
bq ls --project_id="${PROJECT}" | tee -a "${OUT}" || true

echo -e "\n# BigQuery tables in forecasting_data_warehouse" | tee -a "${OUT}"
bq ls --project_id="${PROJECT}" forecasting_data_warehouse | tee -a "${OUT}" || true

echo "=== END INVENTORY ===" | tee -a "${OUT}"
echo "Results saved to: ${OUT}"
