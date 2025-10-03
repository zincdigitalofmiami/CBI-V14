#!/usr/bin/env bash
set -euo pipefail
PROJECT="cbi-v14"
RAW_BUCKET="forecasting-app-raw-data-bucket"
PROC_BUCKET="forecasting-app-processed-data-bucket"
REGION="us-central1"

echo "=== STORAGE BOOTSTRAP $(date -u) ==="

echo -e "\n# 1) Create processed bucket if missing"
if gsutil ls -p "${PROJECT}" "gs://${PROC_BUCKET}" >/dev/null 2>&1; then
  echo "✓ Exists: gs://${PROC_BUCKET}"
else
  echo "-> Creating: gs://${PROC_BUCKET} in ${REGION}"
  gsutil mb -p "${PROJECT}" -c STANDARD -l "${REGION}" "gs://${PROC_BUCKET}"
fi

echo -e "\n# 2) Ensure standard prefixes exist in RAW bucket"
RAW_PREFIXES=(
  "historical/prices/"
  "historical/economic/"
  "historical/weather/"
  "historical/sentiment/"
  "manual-uploads/"
  "processed/"
)
for p in "${RAW_PREFIXES[@]}"; do
  echo "-> ensuring gs://${RAW_BUCKET}/${p}"
  echo -n "" | gsutil cp - "gs://${RAW_BUCKET}/${p}.keep" >/dev/null
done

echo -e "\n# 3) Ensure standard prefixes exist in PROCESSED bucket"
PROC_PREFIXES=(
  "feature_store/"
  "ml/exports/"
  "analytics/"
  "dashboards/"
  "checks/"
)
for p in "${PROC_PREFIXES[@]}"; do
  echo "-> ensuring gs://${PROC_BUCKET}/${p}"
  echo -n "" | gsutil cp - "gs://${PROC_BUCKET}/${p}.keep" >/dev/null
done

echo -e "\n# 4) Quick verify"
gsutil ls -r "gs://${RAW_BUCKET}/" | sed -n '1,200p'
gsutil ls -r "gs://${PROC_BUCKET}/" | sed -n '1,200p'

echo -e "\n=== DONE STORAGE BOOTSTRAP ==="
