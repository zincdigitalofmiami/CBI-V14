-- 03_contract_check.sql
-- Verify predict_frame_209 matches 209-column contract

WITH model_cols AS (
  SELECT column_name, data_type
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'training_dataset_backup_20251028'  -- 207 baseline
  UNION ALL SELECT 'fx_usd_ars_30d_z','FLOAT64'
  UNION ALL SELECT 'fx_usd_myr_30d_z','FLOAT64'
  UNION ALL SELECT 'market_regime','STRING'
),
frame_cols AS (
  SELECT column_name, data_type
  FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'predict_frame_209'
)
SELECT
  (SELECT COUNT(*) FROM model_cols) AS contract_cols,
  (SELECT COUNT(*) FROM frame_cols) AS frame_cols,
  (SELECT COUNT(*) FROM frame_cols f LEFT JOIN model_cols m USING(column_name,data_type) WHERE m.column_name IS NULL) AS mismatches,
  (SELECT STRING_AGG(f.column_name, ', ') FROM frame_cols f LEFT JOIN model_cols m USING(column_name,data_type) WHERE m.column_name IS NULL LIMIT 10) AS mismatch_names;



