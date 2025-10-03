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

echo "=== Stage 5-col files & quarantine the rest ($(date -u)) ==="

# ensure prefixes
gsutil -m rm -f "${STAGE_PREFIX}/**" 2>/dev/null || true
gsutil -m rm -f "${QUAR_PREFIX}/**"  2>/dev/null || true
echo -n "" | gsutil cp - "${STAGE_PREFIX}/.keep" >/dev/null
echo -n "" | gsutil cp - "${QUAR_PREFIX}/.keep"  >/dev/null

# list candidate CSVs
mapfile -t FILES < <(gsutil ls "${SRC_PREFIX}/*.csv" 2>/dev/null || true)
if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No CSVs found in ${SRC_PREFIX}/"
  exit 2
fi

good=0; bad=0
for f in "${FILES[@]}"; do
  # read first line (header)
  header="$(gsutil cat "${f}" | head -n1 || echo "")"
  if [[ -z "${header}" ]]; then
    echo "!! empty or unreadable: ${f} -> quarantine"
    gsutil mv "${f}" "${QUAR_PREFIX}/" && ((bad++)) || true
    continue
  fi

  # normalize header for matching
  hdr_lc="$(echo "${header}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"

  # count comma-delimited fields
  # (number of commas + 1)
  comma_fields=$(( $(printf "%s" "${header}" | awk -F',' '{print NF}') ))

  # accept exactly 5 columns AND a recognizable naming
  if [[ ${comma_fields} -eq 5 && ( "${hdr_lc}" == "time,open,high,low,close" \
         || "${hdr_lc}" == "datetime,open,high,low,close" ) ]]; then
    echo "-> stage OK (5 cols): ${f}"
    gsutil cp "${f}" "${STAGE_PREFIX}/" >/dev/null && ((good++)) || true
  else
    echo "-> quarantine (not 5 cols or weird header): ${f}"
    echo "   header='${header}' (fields=${comma_fields})"
    gsutil mv "${f}" "${QUAR_PREFIX}/" >/dev/null && ((bad++)) || true
  fi
done

echo "Staged: ${good}  |  Quarantined: ${bad}"

# fix table schema to EXACT 5 columns (drop volume if still present)
bq --location="${LOC}" query --use_legacy_sql=false --quiet \
"ALTER TABLE \`${PROJECT}.${DATASET}.${TABLE}\` DROP COLUMN IF EXISTS volume"

# load only staged CSVs
echo "Loading staged files into ${DATASET}.${TABLE}…"
bq --location="${LOC}" load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  "${DATASET}.${TABLE}" \
  "${STAGE_PREFIX}/*.csv" \
  time:TIMESTAMP,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT

# sanity checks
echo "Row count:"
bq --location="${LOC}" query --use_legacy_sql=false --format=csv --quiet \
"SELECT COUNT(1) FROM \`${PROJECT}.${DATASET}.${TABLE}\`" | tail -n1

echo -e "\nNewest 5 rows:"
bq --location="${LOC}" query --use_legacy_sql=false --format=prettyjson --quiet \
"SELECT * FROM \`${PROJECT}.${DATASET}.${TABLE}\` ORDER BY time DESC LIMIT 5"
