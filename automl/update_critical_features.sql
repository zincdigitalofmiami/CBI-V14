-- Update existing training dataset with current Argentina and Industrial data
-- This uses UPDATE instead of CREATE to preserve all existing columns

-- Step 1: Update Argentina data
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
SET 
  argentina_export_tax = argentina.argentina_export_tax,
  argentina_china_sales_mt = argentina.argentina_china_sales_mt,
  argentina_competitive_threat = argentina.argentina_competitive_threat
FROM (
  SELECT 
    date,
    argentina_export_tax,
    argentina_china_sales_mt,
    argentina_competitive_threat
  FROM `cbi-v14.forecasting_data_warehouse.argentina_crisis_tracker`
) argentina
WHERE DATE_TRUNC(base.date, WEEK) = DATE_TRUNC(argentina.date, WEEK);

-- Step 2: Update Industrial data
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
SET 
  industrial_demand_index = industrial.industrial_demand_index
FROM (
  SELECT 
    date,
    industrial_demand_index
  FROM `cbi-v14.forecasting_data_warehouse.industrial_demand_indicators`
) industrial
WHERE DATE_TRUNC(base.date, WEEK) = DATE_TRUNC(industrial.date, WEEK);


