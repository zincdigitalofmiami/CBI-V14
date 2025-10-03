#!/usr/bin/env bash
set -euo pipefail

PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
DATASET="forecasting_data_warehouse"
TABLE="soybean_prices"
BUCKET="forecasting-app-raw-data-bucket"
LOCATION="US"

echo "=== VERIFY & LOAD ($(date -u)) ==="
echo "# Project: ${PROJECT}"

echo -e "\n[1/6] BigQuery dataset existence"
if bq --location=${LOCATION} ls --project_id="${PROJECT}" | awk '{print $1}' | grep -qx "${DATASET}"; then
  echo "✓ dataset exists: ${PROJECT}.${DATASET}"
else
  echo "-> creating dataset ${PROJECT}:${DATASET} in ${LOCATION}"
  bq --location=${LOCATION} mk --dataset "${PROJECT}:${DATASET}"
fi

echo -e "\n[2/6] Table existence"
if bq show --project_id="${PROJECT}" "${DATASET}.${TABLE}" >/dev/null 2>&1; then
  echo "✓ table exists: ${DATASET}.${TABLE}"
else
  echo "-> creating table schema for ${DATASET}.${TABLE}"
  bq mk --project_id="${PROJECT}" --table "${DATASET}.${TABLE}" \
    time:TIMESTAMP,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT,volume:INTEGER
fi

echo -e "\n[3/6] Make sure files are in the expected prefix"
# move only if such files exist at the root historical/ (quiet if none)
gsutil -m mv "gs://${BUCKET}/historical/CBOT_ZL1*csv" "gs://${BUCKET}/historical/prices/" 2>/dev/null || true

echo -e "\n[4/6] Find candidate CSVs to load"
URIS=$(gsutil ls "gs://${BUCKET}/historical/prices/*.csv" 2>/dev/null || true)
if [[ -z "${URIS}" ]]; then
  echo "ERROR: no CSVs found at gs://${BUCKET}/historical/prices/*.csv"
  exit 2
fi
echo "${URIS}" | nl

# pick first file to inspect header
FIRST_URI="$(echo "${URIS}" | head -n1)"
echo -e "\nInspecting header of: ${FIRST_URI}"
HEADER="$(gsutil cat "${FIRST_URI}" | head -n1 || true)"
echo "Header line: ${HEADER}"

SKIP=0
# crude check: if header contains 'time,open,high,low,close' we skip 1
echo "${HEADER}" | grep -qiE '^ *time *, *open *, *high *, *low *, *close' && SKIP=1
echo "Calculated --skip_leading_rows=${SKIP}"

echo -e "\n[5/6] Load into ${DATASET}.${TABLE} (location=${LOCATION})"
bq --location=${LOCATION} load \
  --project_id="${PROJECT}" \
  --source_format=CSV \
  --skip_leading_rows="${SKIP}" \
  "${DATASET}.${TABLE}" \
  "gs://${BUCKET}/historical/prices/*.csv" \
  time:TIMESTAMP,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT,volume:INTEGER

echo -e "\n[6/6] Sanity row count"
bq query --use_legacy_sql=false --format=csv --quiet \
  "SELECT COUNT(1) AS rows_loaded FROM \`${PROJECT}.${DATASET}.${TABLE}\`" | tail -n1

echo "=== DONE ==="
