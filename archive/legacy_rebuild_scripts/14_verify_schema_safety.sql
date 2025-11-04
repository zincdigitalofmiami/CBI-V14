-- Region safety lives in the bq CLI flag; this file is pure SQL.

-- === Configuration ===
DECLARE ref_table STRING  DEFAULT 'cbi-v14.models_v4.training_dataset_backup_20251028';
DECLARE cur_dataset STRING DEFAULT 'cbi-v14.models_v4';
DECLARE cur_table  STRING  DEFAULT 'training_dataset_super_enriched';

-- Columns the models expect you to explicitly populate (business logic columns)
DECLARE explicit ARRAY<STRING> DEFAULT [
  'date','zl_price_current','zl_price_lag1','zl_price_lag7','zl_price_lag30',
  'return_1d','return_7d','ma_7d','ma_30d','volatility_30d','zl_volume',
  'feature_vix_stress','feature_harvest_pace','feature_china_relations',
  'feature_tariff_threat','feature_geopolitical_volatility','feature_biofuel_cascade',
  'feature_hidden_correlation','feature_biofuel_ethanol','big8_composite_score',
  'market_regime','fx_usd_ars_30d_z','fx_usd_myr_30d_z'
];

-- Target columns (exist in ref/filtered views for training; excluded at predict-time)
DECLARE targets ARRAY<STRING>  DEFAULT ['target_1w','target_1m','target_3m','target_6m'];

-- === Current & reference schemas ===
WITH cur_cols AS (
  SELECT column_name, data_type, ordinal_position
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_super_enriched'
),
ref_cols AS (
  SELECT column_name, data_type, ordinal_position
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_backup_20251028'
),

-- === Set math ===
name_misses AS (
  SELECT
    ARRAY(
      SELECT column_name FROM ref_cols
      EXCEPT DISTINCT
      SELECT column_name FROM cur_cols
      ORDER BY column_name
    ) AS missing_from_current,
    ARRAY(
      SELECT column_name FROM cur_cols
      EXCEPT DISTINCT
      SELECT column_name FROM ref_cols
      ORDER BY column_name
    ) AS extra_in_current
),
type_misses AS (
  SELECT ARRAY_AGG(STRUCT(r.column_name, r.data_type AS ref_type, c.data_type AS cur_type)
                   ORDER BY r.column_name) AS type_mismatch
  FROM ref_cols r
  JOIN cur_cols c USING (column_name)
  WHERE r.data_type != c.data_type
),
duty_checks AS (
  SELECT
    ARRAY(
      SELECT col FROM UNNEST(explicit) col
      WHERE col NOT IN (SELECT column_name FROM cur_cols)
      ORDER BY col
    ) AS explicit_missing,
    ARRAY(
      SELECT col FROM UNNEST(targets) col
      WHERE col NOT IN (SELECT column_name FROM cur_cols)
      ORDER BY col
    ) AS targets_missing
),
counts AS (
  SELECT
    (SELECT COUNT(*) FROM cur_cols) AS cur_count,
    (SELECT COUNT(*) FROM ref_cols) AS ref_count,
    (SELECT COUNT(*) FROM cur_cols WHERE column_name IN UNNEST(explicit)) AS explicit_present,
    (SELECT COUNT(*) FROM cur_cols WHERE column_name IN UNNEST(targets))  AS targets_present,
    (SELECT COUNT(*) FROM cur_cols
      WHERE column_name NOT IN UNNEST(explicit)
        AND column_name NOT IN UNNEST(targets)) AS null_cast_needed
)

-- === OUTPUTS (explicitly named, JSON-safe) ===
SELECT 'SCHEMA_SUMMARY' AS section,
       TO_JSON_STRING((
         SELECT AS STRUCT
           (SELECT cur_count       FROM counts)          AS cur_count,
           (SELECT ref_count       FROM counts)          AS ref_count,
           (SELECT explicit_present FROM counts)         AS explicit_present,
           (SELECT targets_present FROM counts)          AS targets_present,
           (SELECT null_cast_needed FROM counts)         AS null_cast_needed
       )) AS payload

UNION ALL
SELECT 'NAME_MISMATCH',
       TO_JSON_STRING((
         SELECT AS STRUCT
           (SELECT missing_from_current FROM name_misses) AS missing_from_current,
           (SELECT extra_in_current     FROM name_misses) AS extra_in_current
       )) AS payload

UNION ALL
SELECT 'TYPE_MISMATCH',
       TO_JSON_STRING((
         SELECT AS STRUCT
           (SELECT type_mismatch FROM type_misses) AS type_mismatch
       )) AS payload

UNION ALL
SELECT 'DUTY_CHECKS',
       TO_JSON_STRING((
         SELECT AS STRUCT
           (SELECT explicit_missing FROM duty_checks) AS explicit_missing,
           (SELECT targets_missing  FROM duty_checks) AS targets_missing
       )) AS payload

UNION ALL
SELECT 'STATUS',
       TO_JSON_STRING((
         SELECT AS STRUCT
           (
             (SELECT ARRAY_LENGTH(missing_from_current) FROM name_misses) = 0
             AND (SELECT ARRAY_LENGTH(type_mismatch)    FROM type_misses) = 0
             AND (SELECT ARRAY_LENGTH(explicit_missing) FROM duty_checks) = 0
             AND (SELECT ARRAY_LENGTH(targets_missing)  FROM duty_checks) = 0
           ) AS ok,
           CONCAT(
             'cur=',        (SELECT CAST(cur_count AS STRING) FROM counts),
             ' ref=',       (SELECT CAST(ref_count AS STRING) FROM counts),
             ' miss=',      (SELECT CAST(ARRAY_LENGTH(missing_from_current) AS STRING) FROM name_misses),
             ' extra=',     (SELECT CAST(ARRAY_LENGTH(extra_in_current)     AS STRING) FROM name_misses),
             ' type=',      (SELECT CAST(ARRAY_LENGTH(type_mismatch)        AS STRING) FROM type_misses),
             ' explicit_miss=', (SELECT CAST(ARRAY_LENGTH(explicit_missing) AS STRING) FROM duty_checks),
             ' targets_miss=',  (SELECT CAST(ARRAY_LENGTH(targets_missing)  AS STRING) FROM duty_checks)
           ) AS message
       )) AS payload;
