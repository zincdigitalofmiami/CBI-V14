#!/usr/bin/env bash
set -euo pipefail

PROJECT="cbi-v14"
DATASET="forecasting_data_warehouse"
TABLE="soybean_prices"
BUCKET="forecasting-app-raw-data-bucket"
LOC="us-central1"

SRC_PREFIX="gs://${BUCKET}/historical/prices"
STAGE_PREFIX="${SRC_PREFIX}/_stage5"
QUAR_PREFIX="${SRC_PREFIX}/_quarantine"

echo "=== soybean_prices ($(date -u)) ==="

# [1] dataset
if ! bq --location="${LOC}" ls --project_id="${PROJECT}" | awk '{print $1}' | grep -qx "${DATASET}"; then
  bq --location="${LOC}" mk --dataset "${PROJECT}:${DATASET}"
fi

# [2] table with exact schema (DATE because files are YYYY-MM-DD)
bq --location="${LOC}" rm -f -t "${PROJECT}:${DATASET}.${TABLE}" >/dev/null 2>&1 || true
bq --location="${LOC}" mk --table "${PROJECT}:${DATASET}.${TABLE}" \
  time:DATE,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT

# [3] stage clean 5-col files; quarantine the rest
gsutil -m rm -f "${STAGE_PREFIX}/**" >/dev/null 2>&1 || true
gsutil -m rm -f "${QUAR_PREFIX}/**" >/dev/null 2>&1 || true
echo -n "" | gsutil cp - "${STAGE_PREFIX}/.keep" >/dev/null
echo -n "" | gsutil cp - "${QUAR_PREFIX}/.keep"  >/dev/null

mapfile -t FILES < <(gsutil ls "${SRC_PREFIX}/*.csv" 2>/dev/null || true)
[ ${#FILES[@]} -gt 0 ] || { echo "No CSVs under ${SRC_PREFIX}"; exit 2; }
good=0; bad=0
for f in "${FILES[@]}"; do
  header="$(gsutil cat "${f}" | head -n1 || echo "")"
  norm="$(echo "${header}" | tr -d ' \r' | tr '[:upper:]' '[:lower:]')"
  if [[ "${norm}" == "time,open,high,low,close" ]]; then
    gsutil cp "${f}" "${STAGE_PREFIX}/"; ((good++)) || true
  else
    gsutil cp "${f}" "${QUAR_PREFIX}/"; ((bad++)) || true
  fi
done
echo "Staged=${good} Quarantined=${bad}"
[ ${good} -gt 0 ] || { echo "Nothing staged. Abort."; exit 3; }

# [4] load staged
bq --location="${LOC}" load \
  --source_format=CSV --skip_leading_rows=1 \
  "${PROJECT}:${DATASET}.${TABLE}" \
  "${STAGE_PREFIX}/*.csv" \
  time:DATE,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT

# [5] sanity
bq --location="${LOC}" query --use_legacy_sql=false --format=csv --quiet \
  "SELECT COUNT(1) AS rows FROM \`${PROJECT}.${DATASET}.${TABLE}\`" | tail -n1
bq --location="${LOC}" query --use_legacy_sql=false --format=prettyjson --quiet \
  "SELECT * FROM \`${PROJECT}.${DATASET}.${TABLE}\` ORDER BY time DESC LIMIT 5"
