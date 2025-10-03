#!/usr/bin/env bash
set -euo pipefail
PROJECT="cbi-v14"
DATASET="forecasting_data_warehouse"
RAW_BUCKET="forecasting-app-raw-data-bucket"
PROC_BUCKET="forecasting-app-processed-data-bucket"

echo "=== PURGE _p AND BEYOND ($(date -u)) ==="

# 1) Drop views created around the _p tables (quiet if missing)
for V in vw_soybean_prices vw_weather_data vw_fed_rates vw_economic_indicators; do
  if bq show --project_id="${PROJECT}" "${DATASET}.${V}" >/dev/null 2>&1; then
    echo "-> dropping view ${DATASET}.${V}"
    bq rm -f --project_id="${PROJECT}" -t "${DATASET}.${V}"
  fi
done

# 2) Drop any tables ending with _p (only the known ones, quiet if missing)
for T in soybean_prices_p weather_data_p fed_rates_p economic_indicators_p; do
  if bq show --project_id="${PROJECT}" "${DATASET}.${T}" >/dev/null 2>&1; then
    echo "-> dropping table ${DATASET}.${T}"
    bq rm -f --project_id="${PROJECT}" -t "${DATASET}.${T}"
  fi
done

# 3) Kill the processed bucket entirely if it exists (this was extra)
if gsutil ls -p "${PROJECT}" "gs://${PROC_BUCKET}" >/dev/null 2>&1; then
  echo "-> deleting processed bucket gs://${PROC_BUCKET}"
  gsutil -m rm -r "gs://${PROC_BUCKET}"
fi

# 4) Remove any .keep placeholders from RAW (don’t touch real files)
echo "-> removing .keep placeholders from RAW"
gsutil -m rm "gs://${RAW_BUCKET}/**/.keep" 2>/dev/null || true

# 5) Verify what remains
echo -e "\n# Buckets now:"
gsutil ls -p "${PROJECT}" || true

echo -e "\n# BigQuery tables now (dataset: ${DATASET}):"
bq ls --project_id="${PROJECT}" "${DATASET}" || true

echo "=== DONE PURGE ==="
