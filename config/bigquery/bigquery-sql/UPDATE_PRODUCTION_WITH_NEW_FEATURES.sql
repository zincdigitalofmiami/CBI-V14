-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- UPDATE PRODUCTION TRAINING DATA WITH NEW FEATURES
-- Created: November 5, 2025
-- Purpose: Update production_training_data_* tables with new scraped features
-- ============================================

-- Update zl_training_prod_allhistory_1m
MERGE `cbi-v14.training.zl_training_prod_allhistory_1m` AS target
USING (
  WITH 
  -- RIN prices data
  rin AS (
    SELECT 
      date,
      rin_d4_price,
      rin_d5_price,
      rin_d6_price
    FROM `cbi-v14.models_v4.rin_prices_daily`
  ),
  
  -- RFS mandates data
  rfs AS (
    SELECT 
      date,
      rfs_mandate_biodiesel,
      rfs_mandate_advanced,
      rfs_mandate_total
    FROM `cbi-v14.models_v4.rfs_mandates_daily`
  ),
  
  -- Freight logistics data
  freight AS (
    SELECT 
      date,
      baltic_dry_index
    FROM `cbi-v14.models_v4.freight_logistics_daily`
  ),
  
  -- Argentina port logistics data
  argentina_port AS (
    SELECT 
      date,
      argentina_vessel_queue_count,
      argentina_port_throughput_teu
    FROM `cbi-v14.models_v4.argentina_port_logistics_daily`
  ),
  
  -- USDA export data (with weekly cancellations)
  usda AS (
    SELECT 
      date,
      china_weekly_cancellations_mt
    FROM `cbi-v14.models_v4.usda_export_daily`
    WHERE china_weekly_cancellations_mt IS NOT NULL
  )
  
  SELECT 
    COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) as date,
    rin.rin_d4_price,
    rin.rin_d5_price,
    rin.rin_d6_price,
    rfs.rfs_mandate_biodiesel,
    rfs.rfs_mandate_advanced,
    rfs.rfs_mandate_total,
    freight.baltic_dry_index,
    argentina_port.argentina_vessel_queue_count,
    argentina_port.argentina_port_throughput_teu,
    usda.china_weekly_cancellations_mt
  FROM rin
  FULL OUTER JOIN rfs USING(date)
  FULL OUTER JOIN freight USING(date)
  FULL OUTER JOIN argentina_port USING(date)
  FULL OUTER JOIN usda USING(date)
  WHERE COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) IS NOT NULL
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  rin_d4_price = COALESCE(target.rin_d4_price, source.rin_d4_price),
  rin_d5_price = COALESCE(target.rin_d5_price, source.rin_d5_price),
  rin_d6_price = COALESCE(target.rin_d6_price, source.rin_d6_price),
  rfs_mandate_biodiesel = COALESCE(target.rfs_mandate_biodiesel, source.rfs_mandate_biodiesel),
  rfs_mandate_advanced = COALESCE(target.rfs_mandate_advanced, source.rfs_mandate_advanced),
  rfs_mandate_total = COALESCE(target.rfs_mandate_total, source.rfs_mandate_total),
  baltic_dry_index = COALESCE(target.baltic_dry_index, source.baltic_dry_index),
  argentina_vessel_queue_count = COALESCE(target.argentina_vessel_queue_count, source.argentina_vessel_queue_count),
  argentina_port_throughput_teu = COALESCE(target.argentina_port_throughput_teu, source.argentina_port_throughput_teu),
  china_weekly_cancellations_mt = COALESCE(target.china_weekly_cancellations_mt, source.china_weekly_cancellations_mt);

-- Repeat for other horizons (1w, 3m, 6m) - same pattern
-- zl_training_prod_allhistory_1w
MERGE `cbi-v14.training.zl_training_prod_allhistory_1w` AS target
USING (
  WITH 
  rin AS (SELECT date, rin_d4_price, rin_d5_price, rin_d6_price FROM `cbi-v14.models_v4.rin_prices_daily`),
  rfs AS (SELECT date, rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total FROM `cbi-v14.models_v4.rfs_mandates_daily`),
  freight AS (SELECT date, baltic_dry_index FROM `cbi-v14.models_v4.freight_logistics_daily`),
  argentina_port AS (SELECT date, argentina_vessel_queue_count, argentina_port_throughput_teu FROM `cbi-v14.models_v4.argentina_port_logistics_daily`),
  usda AS (SELECT date, china_weekly_cancellations_mt FROM `cbi-v14.models_v4.usda_export_daily` WHERE china_weekly_cancellations_mt IS NOT NULL)
  SELECT 
    COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) as date,
    rin.rin_d4_price, rin.rin_d5_price, rin.rin_d6_price,
    rfs.rfs_mandate_biodiesel, rfs.rfs_mandate_advanced, rfs.rfs_mandate_total,
    freight.baltic_dry_index,
    argentina_port.argentina_vessel_queue_count, argentina_port.argentina_port_throughput_teu,
    usda.china_weekly_cancellations_mt
  FROM rin
  FULL OUTER JOIN rfs USING(date)
  FULL OUTER JOIN freight USING(date)
  FULL OUTER JOIN argentina_port USING(date)
  FULL OUTER JOIN usda USING(date)
  WHERE COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) IS NOT NULL
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  rin_d4_price = COALESCE(target.rin_d4_price, source.rin_d4_price),
  rin_d5_price = COALESCE(target.rin_d5_price, source.rin_d5_price),
  rin_d6_price = COALESCE(target.rin_d6_price, source.rin_d6_price),
  rfs_mandate_biodiesel = COALESCE(target.rfs_mandate_biodiesel, source.rfs_mandate_biodiesel),
  rfs_mandate_advanced = COALESCE(target.rfs_mandate_advanced, source.rfs_mandate_advanced),
  rfs_mandate_total = COALESCE(target.rfs_mandate_total, source.rfs_mandate_total),
  baltic_dry_index = COALESCE(target.baltic_dry_index, source.baltic_dry_index),
  argentina_vessel_queue_count = COALESCE(target.argentina_vessel_queue_count, source.argentina_vessel_queue_count),
  argentina_port_throughput_teu = COALESCE(target.argentina_port_throughput_teu, source.argentina_port_throughput_teu),
  china_weekly_cancellations_mt = COALESCE(target.china_weekly_cancellations_mt, source.china_weekly_cancellations_mt);

-- zl_training_prod_allhistory_3m
MERGE `cbi-v14.training.zl_training_prod_allhistory_3m` AS target
USING (
  WITH 
  rin AS (SELECT date, rin_d4_price, rin_d5_price, rin_d6_price FROM `cbi-v14.models_v4.rin_prices_daily`),
  rfs AS (SELECT date, rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total FROM `cbi-v14.models_v4.rfs_mandates_daily`),
  freight AS (SELECT date, baltic_dry_index FROM `cbi-v14.models_v4.freight_logistics_daily`),
  argentina_port AS (SELECT date, argentina_vessel_queue_count, argentina_port_throughput_teu FROM `cbi-v14.models_v4.argentina_port_logistics_daily`),
  usda AS (SELECT date, china_weekly_cancellations_mt FROM `cbi-v14.models_v4.usda_export_daily` WHERE china_weekly_cancellations_mt IS NOT NULL)
  SELECT 
    COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) as date,
    rin.rin_d4_price, rin.rin_d5_price, rin.rin_d6_price,
    rfs.rfs_mandate_biodiesel, rfs.rfs_mandate_advanced, rfs.rfs_mandate_total,
    freight.baltic_dry_index,
    argentina_port.argentina_vessel_queue_count, argentina_port.argentina_port_throughput_teu,
    usda.china_weekly_cancellations_mt
  FROM rin
  FULL OUTER JOIN rfs USING(date)
  FULL OUTER JOIN freight USING(date)
  FULL OUTER JOIN argentina_port USING(date)
  FULL OUTER JOIN usda USING(date)
  WHERE COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) IS NOT NULL
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  rin_d4_price = COALESCE(target.rin_d4_price, source.rin_d4_price),
  rin_d5_price = COALESCE(target.rin_d5_price, source.rin_d5_price),
  rin_d6_price = COALESCE(target.rin_d6_price, source.rin_d6_price),
  rfs_mandate_biodiesel = COALESCE(target.rfs_mandate_biodiesel, source.rfs_mandate_biodiesel),
  rfs_mandate_advanced = COALESCE(target.rfs_mandate_advanced, source.rfs_mandate_advanced),
  rfs_mandate_total = COALESCE(target.rfs_mandate_total, source.rfs_mandate_total),
  baltic_dry_index = COALESCE(target.baltic_dry_index, source.baltic_dry_index),
  argentina_vessel_queue_count = COALESCE(target.argentina_vessel_queue_count, source.argentina_vessel_queue_count),
  argentina_port_throughput_teu = COALESCE(target.argentina_port_throughput_teu, source.argentina_port_throughput_teu),
  china_weekly_cancellations_mt = COALESCE(target.china_weekly_cancellations_mt, source.china_weekly_cancellations_mt);

-- zl_training_prod_allhistory_6m
MERGE `cbi-v14.training.zl_training_prod_allhistory_6m` AS target
USING (
  WITH 
  rin AS (SELECT date, rin_d4_price, rin_d5_price, rin_d6_price FROM `cbi-v14.models_v4.rin_prices_daily`),
  rfs AS (SELECT date, rfs_mandate_biodiesel, rfs_mandate_advanced, rfs_mandate_total FROM `cbi-v14.models_v4.rfs_mandates_daily`),
  freight AS (SELECT date, baltic_dry_index FROM `cbi-v14.models_v4.freight_logistics_daily`),
  argentina_port AS (SELECT date, argentina_vessel_queue_count, argentina_port_throughput_teu FROM `cbi-v14.models_v4.argentina_port_logistics_daily`),
  usda AS (SELECT date, china_weekly_cancellations_mt FROM `cbi-v14.models_v4.usda_export_daily` WHERE china_weekly_cancellations_mt IS NOT NULL)
  SELECT 
    COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) as date,
    rin.rin_d4_price, rin.rin_d5_price, rin.rin_d6_price,
    rfs.rfs_mandate_biodiesel, rfs.rfs_mandate_advanced, rfs.rfs_mandate_total,
    freight.baltic_dry_index,
    argentina_port.argentina_vessel_queue_count, argentina_port.argentina_port_throughput_teu,
    usda.china_weekly_cancellations_mt
  FROM rin
  FULL OUTER JOIN rfs USING(date)
  FULL OUTER JOIN freight USING(date)
  FULL OUTER JOIN argentina_port USING(date)
  FULL OUTER JOIN usda USING(date)
  WHERE COALESCE(rin.date, rfs.date, freight.date, argentina_port.date, usda.date) IS NOT NULL
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  rin_d4_price = COALESCE(target.rin_d4_price, source.rin_d4_price),
  rin_d5_price = COALESCE(target.rin_d5_price, source.rin_d5_price),
  rin_d6_price = COALESCE(target.rin_d6_price, source.rin_d6_price),
  rfs_mandate_biodiesel = COALESCE(target.rfs_mandate_biodiesel, source.rfs_mandate_biodiesel),
  rfs_mandate_advanced = COALESCE(target.rfs_mandate_advanced, source.rfs_mandate_advanced),
  rfs_mandate_total = COALESCE(target.rfs_mandate_total, source.rfs_mandate_total),
  baltic_dry_index = COALESCE(target.baltic_dry_index, source.baltic_dry_index),
  argentina_vessel_queue_count = COALESCE(target.argentina_vessel_queue_count, source.argentina_vessel_queue_count),
  argentina_port_throughput_teu = COALESCE(target.argentina_port_throughput_teu, source.argentina_port_throughput_teu),
  china_weekly_cancellations_mt = COALESCE(target.china_weekly_cancellations_mt, source.china_weekly_cancellations_mt);








