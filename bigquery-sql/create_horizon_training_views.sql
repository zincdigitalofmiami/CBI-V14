-- Horizon-filtered training views (targets excluded from features)
-- Fixes: "Null values not allowed in transformations" error

-- Base reference (create if doesn't exist, or replace if exists)
CREATE OR REPLACE VIEW `cbi-v14.models_v4._v_train_core` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- 1W Training View (only target_1w as label, exclude other targets)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1w` AS
SELECT
  * EXCEPT(target_1m, target_3m, target_6m)  -- strip other targets entirely
FROM `cbi-v14.models_v4._v_train_core`
WHERE target_1w IS NOT NULL;

-- 1M Training View (only target_1m as label, exclude other targets)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_1m` AS
SELECT
  * EXCEPT(target_1w, target_3m, target_6m)
FROM `cbi-v14.models_v4._v_train_core`
WHERE target_1m IS NOT NULL;

-- 3M Training View (only target_3m as label, exclude other targets)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_3m` AS
SELECT
  * EXCEPT(target_1w, target_1m, target_6m)
FROM `cbi-v14.models_v4._v_train_core`
WHERE target_3m IS NOT NULL;

-- 6M Training View (only target_6m as label, exclude other targets)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.train_6m` AS
SELECT
  * EXCEPT(target_1w, target_1m, target_3m)
FROM `cbi-v14.models_v4._v_train_core`
WHERE target_6m IS NOT NULL;

-- Prediction frame (all targets excluded - used at inference time)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.predict_frame` AS
WITH latest AS (
  SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
)
SELECT
  -- drop ALL target_* so no label-ish columns leak into features
  latest.* EXCEPT(target_1w, target_1m, target_3m, target_6m)
FROM latest;

