-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FIX NULLS USING MERGE SYNTAX (DUPLICATE-SAFE VERSION)
-- Ensures one row per date to avoid MERGE constraint violations
-- ============================================

-- Create a backup first
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched_backup` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- SINGLE COMPREHENSIVE MERGE (DUPLICATE-SAFE)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH 
  -- Yahoo Finance data (DEDUPLICATED - one row per date)
  yahoo_data AS (
    SELECT 
      date,
      MAX(CASE WHEN symbol = 'ZL=F' THEN Close END) as zl_close,
      MAX(CASE WHEN symbol = 'ZL=F' THEN Volume END) as zl_volume_new,
      MAX(CASE WHEN symbol = 'ZC=F' THEN Close END) as corn_close,
      MAX(CASE WHEN symbol = 'ZW=F' THEN Close END) as wheat_close,
      MAX(CASE WHEN symbol = 'CL=F' THEN Close END) as crude_close,
      MAX(CASE WHEN symbol = 'ZM=F' THEN Close END) as meal_close,
      MAX(CASE WHEN symbol = 'FCPO=F' THEN Close END) as palm_close,
      MAX(CASE WHEN symbol = '^VIX' THEN Close END) as vix_close,
      MAX(CASE WHEN symbol = 'DX-Y.NYB' THEN Close END) as dxy_close
    FROM (
      SELECT date, symbol, Close, Volume, pulled_at
      FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
      WHERE symbol IN ('ZL=F', 'ZC=F', 'ZW=F', 'CL=F', 'ZM=F', 'FCPO=F', '^VIX', 'DX-Y.NYB')
      QUALIFY ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY pulled_at DESC) = 1
    )
    GROUP BY date
  ),
  
  -- Economic indicators (DEDUPLICATED - one row per date)
  econ_data AS (
    SELECT 
      CAST(time AS DATE) as date,
      MAX(CASE WHEN indicator = 'ten_year_treasury' THEN value END) as treasury_yield,
      MAX(CASE WHEN indicator = 'usd_cny_rate_fred' THEN value END) as usd_cny,
      MAX(CASE WHEN indicator = 'usd_brl_rate_fred' THEN value END) as usd_brl,
      MAX(CASE WHEN indicator = 'dollar_index_fred' THEN value END) as dollar_idx,
      MAX(CASE WHEN indicator = 'fed_funds_rate' THEN value END) as fed_funds,
      MAX(CASE WHEN indicator = 'unemployment_rate' THEN value END) as unemployment
    FROM (
      SELECT time, indicator, value
      FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
      WHERE indicator IN (
        'ten_year_treasury', 'usd_cny_rate_fred', 'usd_brl_rate_fred',
        'dollar_index_fred', 'fed_funds_rate', 'unemployment_rate'
      )
      QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE), indicator ORDER BY time DESC) = 1
    )
    GROUP BY CAST(time AS DATE)
  ),
  
  -- Combine data sources (GUARANTEED one row per date)
  source_data AS (
    SELECT 
      COALESCE(y.date, e.date) as date,
      y.zl_close,
      y.zl_volume_new,
      y.corn_close,
      y.wheat_close,
      y.crude_close,
      y.meal_close,
      y.palm_close,
      y.vix_close,
      y.dxy_close,
      e.treasury_yield,
      e.usd_cny,
      e.usd_brl,
      e.dollar_idx,
      e.fed_funds,
      e.unemployment
    FROM yahoo_data y
    FULL OUTER JOIN econ_data e ON y.date = e.date
    WHERE COALESCE(y.date, e.date) IS NOT NULL
  )
  
  -- Final source: one row per date, only dates that exist in training dataset
  SELECT 
    s.*
  FROM source_data s
  WHERE EXISTS (
    SELECT 1 
    FROM `cbi-v14.models_v4.training_dataset_super_enriched` t 
    WHERE t.date = s.date
    AND (
      -- Only include dates where we can actually fill NULLs
      (t.zl_price_current IS NULL AND s.zl_close IS NOT NULL) OR
      (t.zl_volume IS NULL AND s.zl_volume_new IS NOT NULL) OR
      (t.corn_price IS NULL AND s.corn_close IS NOT NULL) OR
      (t.wheat_price IS NULL AND s.wheat_close IS NOT NULL) OR
      (t.crude_oil_wti_new IS NULL AND s.crude_close IS NOT NULL) OR
      (t.crude_price IS NULL AND s.crude_close IS NOT NULL) OR
      (t.soybean_meal_price IS NULL AND s.meal_close IS NOT NULL) OR
      (t.palm_price IS NULL AND s.palm_close IS NOT NULL) OR
      (t.vix_level IS NULL AND s.vix_close IS NOT NULL) OR
      (t.vix_index_new IS NULL AND s.vix_close IS NOT NULL) OR
      (t.dxy_level IS NULL AND s.dxy_close IS NOT NULL) OR
      (t.dollar_index IS NULL AND s.dxy_close IS NOT NULL) OR
      (t.usd_index IS NULL AND s.dxy_close IS NOT NULL) OR
      (t.treasury_10y_yield IS NULL AND s.treasury_yield IS NOT NULL) OR
      (t.usd_cny_rate IS NULL AND s.usd_cny IS NOT NULL) OR
      (t.usd_brl_rate IS NULL AND s.usd_brl IS NOT NULL) OR
      (t.fed_funds_rate IS NULL AND s.fed_funds IS NOT NULL) OR
      (t.unemployment_rate IS NULL AND s.unemployment IS NOT NULL) OR
      (t.econ_unemployment_rate IS NULL AND s.unemployment IS NOT NULL)
    )
  )
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  -- Yahoo Finance updates (only fill NULLs)
  zl_price_current = COALESCE(target.zl_price_current, source.zl_close),
  zl_volume = COALESCE(target.zl_volume, source.zl_volume_new),
  corn_price = COALESCE(target.corn_price, source.corn_close),
  wheat_price = COALESCE(target.wheat_price, source.wheat_close),
  crude_oil_wti_new = COALESCE(target.crude_oil_wti_new, source.crude_close),
  crude_price = COALESCE(target.crude_price, source.crude_close),
  soybean_meal_price = COALESCE(target.soybean_meal_price, source.meal_close),
  palm_price = COALESCE(target.palm_price, source.palm_close),
  vix_level = COALESCE(target.vix_level, source.vix_close),
  vix_index_new = COALESCE(target.vix_index_new, source.vix_close),
  dxy_level = COALESCE(target.dxy_level, source.dxy_close),
  dollar_index = COALESCE(target.dollar_index, source.dxy_close),
  usd_index = COALESCE(target.usd_index, source.dxy_close),
  
  -- Economic indicator updates (only fill NULLs)
  treasury_10y_yield = COALESCE(target.treasury_10y_yield, source.treasury_yield),
  usd_cny_rate = COALESCE(target.usd_cny_rate, source.usd_cny),
  usd_brl_rate = COALESCE(target.usd_brl_rate, source.usd_brl),
  fed_funds_rate = COALESCE(target.fed_funds_rate, source.fed_funds),
  unemployment_rate = COALESCE(target.unemployment_rate, source.unemployment),
  econ_unemployment_rate = COALESCE(target.econ_unemployment_rate, source.unemployment);

-- ============================================
-- VERIFICATION: Show improvement results
-- ============================================

WITH improvement_check AS (
  SELECT 
    'SUCCESS' as status,
    COUNT(*) as total_rows,
    
    -- Count remaining NULLs after fix
    COUNTIF(zl_price_current IS NULL) as zl_price_nulls_after,
    COUNTIF(zl_volume IS NULL) as zl_volume_nulls_after,
    COUNTIF(corn_price IS NULL) as corn_nulls_after,
    COUNTIF(wheat_price IS NULL) as wheat_nulls_after,
    COUNTIF(crude_oil_wti_new IS NULL) as crude_nulls_after,
    COUNTIF(soybean_meal_price IS NULL) as meal_nulls_after,
    COUNTIF(palm_price IS NULL) as palm_nulls_after,
    COUNTIF(vix_level IS NULL) as vix_nulls_after,
    COUNTIF(dollar_index IS NULL) as dollar_nulls_after,
    COUNTIF(treasury_10y_yield IS NULL) as treasury_nulls_after,
    COUNTIF(usd_cny_rate IS NULL) as usd_cny_nulls_after,
    COUNTIF(usd_brl_rate IS NULL) as usd_brl_nulls_after,
    COUNTIF(fed_funds_rate IS NULL) as fed_funds_nulls_after,
    COUNTIF(unemployment_rate IS NULL) as unemployment_nulls_after,
    
    -- Calculate success percentages
    ROUND((1 - COUNTIF(zl_price_current IS NULL) / COUNT(*)) * 100, 1) as zl_price_fill_pct,
    ROUND((1 - COUNTIF(soybean_meal_price IS NULL) / COUNT(*)) * 100, 1) as meal_fill_pct,
    ROUND((1 - COUNTIF(treasury_10y_yield IS NULL) / COUNT(*)) * 100, 1) as treasury_fill_pct,
    ROUND((1 - COUNTIF(unemployment_rate IS NULL) / COUNT(*)) * 100, 1) as unemployment_fill_pct
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  status,
  total_rows,
  
  -- Show key improvements
  CONCAT('ZL Price: ', zl_price_fill_pct, '% filled') as zl_improvement,
  CONCAT('Meal Price: ', meal_fill_pct, '% filled') as meal_improvement,
  CONCAT('Treasury: ', treasury_fill_pct, '% filled') as treasury_improvement,
  CONCAT('Unemployment: ', unemployment_fill_pct, '% filled') as unemployment_improvement,
  
  -- Remaining NULLs
  zl_price_nulls_after,
  meal_nulls_after,
  treasury_nulls_after,
  unemployment_nulls_after
  
FROM improvement_check;

-- ============================================
-- TRAINING READINESS CHECK
-- ============================================

SELECT 
  'TRAINING_READINESS' as check_type,
  COUNT(*) as total_rows,
  COUNT(*) - COUNTIF(target_1w IS NULL) as valid_1w_targets,
  
  -- Count how many features are now usable (>80% non-NULL)
  COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) as zl_price_coverage,
  COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) as meal_coverage,
  COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) as treasury_coverage,
  COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) as unemployment_coverage,
  
  -- Features ready for training (>80% coverage)
  CASE WHEN COUNTIF(zl_price_current IS NOT NULL) / COUNT(*) > 0.8 THEN 'READY' ELSE 'NOT_READY' END as zl_price_status,
  CASE WHEN COUNTIF(soybean_meal_price IS NOT NULL) / COUNT(*) > 0.8 THEN 'READY' ELSE 'NOT_READY' END as meal_status,
  CASE WHEN COUNTIF(treasury_10y_yield IS NOT NULL) / COUNT(*) > 0.8 THEN 'READY' ELSE 'NOT_READY' END as treasury_status,
  CASE WHEN COUNTIF(unemployment_rate IS NOT NULL) / COUNT(*) > 0.8 THEN 'READY' ELSE 'NOT_READY' END as unemployment_status

FROM `cbi-v14.models_v4.training_dataset_super_enriched`;
