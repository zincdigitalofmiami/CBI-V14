-- ============================================
-- DAILY AGGREGATIONS FOR NEW FEATURES
-- Created: November 5, 2025
-- Purpose: Create daily aggregation tables for new scraped features
-- ============================================

-- ============================================
-- RIN PRICES DAILY
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rin_prices_daily` AS
WITH rin_weekly AS (
  SELECT 
    DATE(date) as date,
    rin_d4_price,
    rin_d5_price,
    rin_d6_price,
    rin_d3_price,
    rin_d7_price
  FROM `cbi-v14.forecasting_data_warehouse.biofuel_prices`
  WHERE rin_d4_price IS NOT NULL OR rin_d5_price IS NOT NULL OR rin_d6_price IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(date) ORDER BY date DESC) = 1
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  ORDER BY date
),
-- Forward-fill RIN weekly data to daily
rin_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(rw.rin_d4_price IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rin_d4_price,
    LAST_VALUE(rw.rin_d5_price IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rin_d5_price,
    LAST_VALUE(rw.rin_d6_price IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rin_d6_price,
    LAST_VALUE(rw.rin_d3_price IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rin_d3_price,
    LAST_VALUE(rw.rin_d7_price IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rin_d7_price
  FROM training_dates td
  LEFT JOIN rin_weekly rw ON td.date = rw.date
)
SELECT * FROM rin_daily_filled WHERE date IS NOT NULL ORDER BY date;

-- ============================================
-- RFS MANDATES DAILY
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rfs_mandates_daily` AS
WITH rfs_yearly AS (
  SELECT 
    date,
    rfs_mandate_biodiesel,
    rfs_mandate_advanced,
    rfs_mandate_total
  FROM `cbi-v14.forecasting_data_warehouse.biofuel_policy`
  WHERE (policy_type = 'RFS_MANDATE' OR rfs_mandate_biodiesel IS NOT NULL OR rfs_mandate_advanced IS NOT NULL OR rfs_mandate_total IS NOT NULL)
    AND (rfs_mandate_biodiesel IS NOT NULL OR rfs_mandate_advanced IS NOT NULL OR rfs_mandate_total IS NOT NULL)
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  ORDER BY date
),
-- Forward-fill RFS yearly data to daily
rfs_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(rf.rfs_mandate_biodiesel IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rfs_mandate_biodiesel,
    LAST_VALUE(rf.rfs_mandate_advanced IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rfs_mandate_advanced,
    LAST_VALUE(rf.rfs_mandate_total IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as rfs_mandate_total
  FROM training_dates td
  LEFT JOIN rfs_yearly rf ON td.date = rf.date
)
SELECT * FROM rfs_daily_filled WHERE date IS NOT NULL ORDER BY date;

-- ============================================
-- FREIGHT LOGISTICS DAILY
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.freight_logistics_daily` AS
WITH freight_raw AS (
  SELECT 
    date,
    baltic_dry_index,
    freight_soybean_mentions
  FROM `cbi-v14.forecasting_data_warehouse.freight_logistics`
  WHERE baltic_dry_index IS NOT NULL
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  ORDER BY date
),
-- Forward-fill freight data to daily
freight_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(fr.baltic_dry_index IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as baltic_dry_index,
    LAST_VALUE(fr.freight_soybean_mentions IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as freight_soybean_mentions
  FROM training_dates td
  LEFT JOIN freight_raw fr ON td.date = fr.date
)
SELECT * FROM freight_daily_filled WHERE date IS NOT NULL ORDER BY date;

-- ============================================
-- ARGENTINA PORT LOGISTICS DAILY
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.argentina_port_logistics_daily` AS
WITH port_raw AS (
  SELECT 
    date,
    argentina_vessel_queue_count,
    argentina_port_throughput_teu
  FROM `cbi-v14.forecasting_data_warehouse.argentina_crisis_tracker`
  WHERE argentina_vessel_queue_count IS NOT NULL OR argentina_port_throughput_teu IS NOT NULL
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  ORDER BY date
),
-- Forward-fill port data to daily
port_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(pr.argentina_vessel_queue_count IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as argentina_vessel_queue_count,
    LAST_VALUE(pr.argentina_port_throughput_teu IGNORE NULLS) OVER (ORDER BY td.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as argentina_port_throughput_teu
  FROM training_dates td
  LEFT JOIN port_raw pr ON td.date = pr.date
)
SELECT * FROM port_daily_filled WHERE date IS NOT NULL ORDER BY date;

-- ============================================
-- CHINA WEEKLY CANCELLATIONS DAILY
-- ============================================
-- Enhance existing usda_export_daily table - preserve existing structure
CREATE OR REPLACE TABLE `cbi-v14.models_v4.usda_export_daily` AS
WITH existing_usda AS (
  SELECT 
    date,
    soybean_weekly_sales,
    soybean_oil_weekly_sales,
    soybean_meal_weekly_sales,
    china_soybean_sales
  FROM `cbi-v14.models_v4.usda_export_daily`
),
china_weekly AS (
  SELECT 
    date,
    china_weekly_cancellations_mt
  FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
  WHERE china_weekly_cancellations_mt IS NOT NULL
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  ORDER BY date
),
-- Combine existing and new data
combined AS (
  SELECT 
    COALESCE(eu.date, cw.date) as date,
    eu.soybean_weekly_sales,
    eu.soybean_oil_weekly_sales,
    eu.soybean_meal_weekly_sales,
    eu.china_soybean_sales,
    cw.china_weekly_cancellations_mt
  FROM training_dates td
  LEFT JOIN existing_usda eu ON td.date = eu.date
  LEFT JOIN china_weekly cw ON td.date = cw.date
)
-- Forward-fill weekly cancellations
SELECT 
  date,
  soybean_weekly_sales,
  soybean_oil_weekly_sales,
  soybean_meal_weekly_sales,
  china_soybean_sales,
  LAST_VALUE(china_weekly_cancellations_mt IGNORE NULLS) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as china_weekly_cancellations_mt
FROM combined
WHERE date IS NOT NULL
ORDER BY date;

