-- 01_pick_latest_date.sql
-- Get latest fully populated date from training dataset

CREATE OR REPLACE TABLE `cbi-v14.models_v4._latest_date` AS
SELECT MAX(date) AS latest_date
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE date <= CURRENT_DATE();



