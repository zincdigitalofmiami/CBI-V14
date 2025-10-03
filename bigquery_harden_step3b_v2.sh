#!/usr/bin/env bash
set -euo pipefail
PROJECT="cbi-v14"
DATASET="forecasting_data_warehouse"

echo "=== BIGQUERY HARDEN (prod) $(date -u) ==="

exists_table () { bq show --project_id="${PROJECT}" "${DATASET}.$1" >/dev/null 2>&1; }

# 1) soybean_prices_p  (partition: time; cluster: ticker, volume)
echo -e "\n[1/4] soybean_prices_p"
if ! exists_table soybean_prices_p; then
  bq mk --project_id="${PROJECT}" \
        --table \
        --time_partitioning_field time \
        --time_partitioning_type DAY \
        --clustering_fields ticker,volume \
        "${DATASET}.soybean_prices_p" \
        time:TIMESTAMP,open:FLOAT,high:FLOAT,low:FLOAT,close:FLOAT,volume:INTEGER,ticker:STRING
  echo "✓ Created ${DATASET}.soybean_prices_p"
else
  echo "✓ Exists ${DATASET}.soybean_prices_p"
fi

echo "-> Migrating soybean_prices -> soybean_prices_p (idempotent)"
bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
INSERT INTO \`${PROJECT}.${DATASET}.soybean_prices_p\` (time,open,high,low,close,volume,ticker)
SELECT time,open,high,low,close,volume,CAST(NULL AS STRING)
FROM \`${PROJECT}.${DATASET}.soybean_prices\`
WHERE time IS NOT NULL
EXCEPT DISTINCT
SELECT time,open,high,low,close,volume,ticker
FROM \`${PROJECT}.${DATASET}.soybean_prices_p\`;"

bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
CREATE OR REPLACE VIEW \`${PROJECT}.${DATASET}.vw_soybean_prices\` AS
SELECT * FROM \`${PROJECT}.${DATASET}.soybean_prices_p\`;"

# 2) weather_data_p  (partition: date; cluster: location)
echo -e "\n[2/4] weather_data_p"
if ! exists_table weather_data_p; then
  bq mk --project_id="${PROJECT}" \
        --table \
        --time_partitioning_field date \
        --time_partitioning_type DAY \
        --clustering_fields location \
        "${DATASET}.weather_data_p" \
        date:DATE,location:STRING,temp_high:FLOAT,temp_low:FLOAT,precipitation:FLOAT
  echo "✓ Created ${DATASET}.weather_data_p"
else
  echo "✓ Exists ${DATASET}.weather_data_p"
fi

echo "-> Migrating weather_data -> weather_data_p (idempotent)"
bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
INSERT INTO \`${PROJECT}.${DATASET}.weather_data_p\` (date,location,temp_high,temp_low,precipitation)
SELECT date,location,temp_high,temp_low,precipitation
FROM \`${PROJECT}.${DATASET}.weather_data\`
WHERE date IS NOT NULL
EXCEPT DISTINCT
SELECT date,location,temp_high,temp_low,precipitation
FROM \`${PROJECT}.${DATASET}.weather_data_p\`;"

bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
CREATE OR REPLACE VIEW \`${PROJECT}.${DATASET}.vw_weather_data\` AS
SELECT * FROM \`${PROJECT}.${DATASET}.weather_data_p\`;"

# 3) fed_rates_p  (partition: time; cluster: time)
echo -e "\n[3/4] fed_rates_p"
if ! exists_table fed_rates_p; then
  bq mk --project_id="${PROJECT}" \
        --table \
        --time_partitioning_field time \
        --time_partitioning_type DAY \
        --clustering_fields time \
        "${DATASET}.fed_rates_p" \
        time:TIMESTAMP,close:FLOAT,EMA:FLOAT,MACD:FLOAT,Signal_Line:FLOAT,Histogram:FLOAT,Cross:FLOAT
  echo "✓ Created ${DATASET}.fed_rates_p"
else
  echo "✓ Exists ${DATASET}.fed_rates_p"
fi

echo "-> Migrating fed_rates -> fed_rates_p (idempotent)"
bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
INSERT INTO \`${PROJECT}.${DATASET}.fed_rates_p\` (time,close,EMA,MACD,Signal_Line,Histogram,Cross)
SELECT time,close,EMA,MACD,Signal_Line,Histogram,Cross
FROM \`${PROJECT}.${DATASET}.fed_rates\`
WHERE time IS NOT NULL
EXCEPT DISTINCT
SELECT time,close,EMA,MACD,Signal_Line,Histogram,Cross
FROM \`${PROJECT}.${DATASET}.fed_rates_p\`;"

bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
CREATE OR REPLACE VIEW \`${PROJECT}.${DATASET}.vw_fed_rates\` AS
SELECT * FROM \`${PROJECT}.${DATASET}.fed_rates_p\`;"

# 4) economic_indicators_p  (partition: time; cluster: indicator)
echo -e "\n[4/4] economic_indicators_p"
if ! exists_table economic_indicators_p; then
  bq mk --project_id="${PROJECT}" \
        --table \
        --time_partitioning_field time \
        --time_partitioning_type DAY \
        --clustering_fields indicator \
        "${DATASET}.economic_indicators_p" \
        time:TIMESTAMP,indicator:STRING,value:FLOAT
  echo "✓ Created ${DATASET}.economic_indicators_p"
else
  echo "✓ Exists ${DATASET}.economic_indicators_p"
fi

echo "-> Migrating economic_indicators -> economic_indicators_p (idempotent)"
bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
INSERT INTO \`${PROJECT}.${DATASET}.economic_indicators_p\` (time,indicator,value)
SELECT time,indicator,value
FROM \`${PROJECT}.${DATASET}.economic_indicators\`
WHERE time IS NOT NULL
EXCEPT DISTINCT
SELECT time,indicator,value
FROM \`${PROJECT}.${DATASET}.economic_indicators_p\`;"

bq query --project_id="${PROJECT}" --use_legacy_sql=false --quiet "
CREATE OR REPLACE VIEW \`${PROJECT}.${DATASET}.vw_economic_indicators\` AS
SELECT * FROM \`${PROJECT}.${DATASET}.economic_indicators_p\`;"

# Row counts (source vs partitioned)
echo -e "\n# Row counts (source vs partitioned)"
for T in soybean_prices weather_data fed_rates economic_indicators; do
  SRC=$(bq query --project_id="${PROJECT}" --use_legacy_sql=false --format=csv --quiet "SELECT COUNT(1) FROM \`${PROJECT}.${DATASET}.${T}\`" | tail -n1)
  DST=$(bq query --project_id="${PROJECT}" --use_legacy_sql=false --format=csv --quiet "SELECT COUNT(1) FROM \`${PROJECT}.${DATASET}.${T}_p\`" | tail -n1)
  echo "${T}: src=${SRC}, dst=${DST}"
done

echo -e "\n=== DONE BIGQUERY HARDEN ==="
