-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FIX PALM PRICE COVERAGE
-- Forward-fill existing palm_price data to 100%
-- ============================================

-- Step 1: Check current palm price coverage and gaps
SELECT 
  'Current Palm Price Status' as check_type,
  COUNT(*) as total_rows,
  COUNTIF(palm_price IS NOT NULL) as filled_rows,
  COUNTIF(palm_price IS NULL) as null_rows,
  ROUND(COUNTIF(palm_price IS NOT NULL) / COUNT(*) * 100, 1) as coverage_pct,
  MIN(date) as earliest_date,
  MAX(date) as latest_date
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- Step 2: Create palm price daily complete table with forward-fill
CREATE OR REPLACE TABLE `cbi-v14.models_v4.palm_price_daily_complete` AS
WITH 
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),

-- Get existing palm price data from training dataset
existing_palm AS (
  SELECT 
    date,
    palm_price,
    'training_dataset' as source
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE palm_price IS NOT NULL
  AND palm_price > 0  -- Sanity check
),

-- Get first palm price value for back-filling early dates
first_palm AS (
  SELECT 
    date as first_date,
    palm_price as first_price
  FROM existing_palm
  WHERE date = (SELECT MIN(date) FROM existing_palm)
  LIMIT 1
),

-- Forward-fill palm price to daily frequency (and back-fill early dates)
palm_daily_filled AS (
  SELECT 
    td.date,
    fp.first_date,
    fp.first_price,
    -- Forward fill: carry last known value forward
    -- Back-fill: use first known value for all dates before first data point
    COALESCE(
      ep.palm_price,  -- Actual data
      -- Forward fill (last known value)
      LAST_VALUE(ep.palm_price IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      -- Back-fill: use first known value for early dates
      CASE WHEN td.date < fp.first_date THEN fp.first_price ELSE NULL END
    ) as palm_price,
    -- Track data freshness
    COALESCE(
      -- Days since last update (forward fill)
      DATE_DIFF(
        td.date,
        LAST_VALUE(ep.date IGNORE NULLS) OVER (
          ORDER BY td.date 
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ),
        DAY
      ),
      -- Days before first update (back-fill)
      DATE_DIFF(
        FIRST_VALUE(ep.date IGNORE NULLS) OVER (
          ORDER BY td.date 
          ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
        ),
        td.date,
        DAY
      )
    ) as days_since_update,
    -- Track data source
    COALESCE(
      LAST_VALUE(ep.source IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      FIRST_VALUE(ep.source IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
      )
    ) as data_source
  FROM training_dates td
  CROSS JOIN first_palm fp
  LEFT JOIN existing_palm ep ON td.date = ep.date
)

SELECT 
  date,
  palm_price,
  days_since_update,
  data_source,
  -- Quality flags
  CASE 
    WHEN days_since_update <= 7 THEN 'fresh'
    WHEN days_since_update <= 30 THEN 'acceptable'
    WHEN days_since_update <= 90 THEN 'stale'
    ELSE 'very_stale'
  END as data_quality
FROM palm_daily_filled
WHERE palm_price IS NOT NULL
ORDER BY date;

-- Step 3: Apply palm price fix to training dataset
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  SELECT 
    date,
    palm_price
  FROM `cbi-v14.models_v4.palm_price_daily_complete`
  WHERE data_quality IN ('fresh', 'acceptable', 'stale')  -- Exclude very_stale (>90 days)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY days_since_update ASC) = 1  -- One row per date
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  palm_price = COALESCE(target.palm_price, source.palm_price);

-- Step 4: Final verification of palm price coverage
WITH final_coverage AS (
  SELECT 
    COUNT(*) as total_rows,
    COUNTIF(palm_price IS NOT NULL) as filled_rows,
    COUNTIF(palm_price IS NULL) as null_rows,
    ROUND((1 - COUNTIF(palm_price IS NULL) / COUNT(*)) * 100, 1) as palm_coverage,
    
    -- Check data quality
    COUNTIF(
      DATE_DIFF(
        CURRENT_DATE(),
        (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched` WHERE palm_price IS NOT NULL),
        DAY
      ) <= 90
    ) as recent_data_available
    
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)

SELECT 
  'PALM PRICE COVERAGE FIX RESULTS' as status,
  total_rows,
  filled_rows,
  null_rows,
  CONCAT('Palm Price: ', palm_coverage, '%') as palm_result,
  
  CASE 
    WHEN palm_coverage >= 95 THEN 'EXCELLENT - READY FOR TRAINING'
    WHEN palm_coverage >= 90 THEN 'GOOD - ACCEPTABLE COVERAGE'
    WHEN palm_coverage >= 80 THEN 'ACCEPTABLE - CAN PROCEED'
    ELSE 'NEEDS MORE WORK'
  END as assessment,
  
  CASE 
    WHEN null_rows = 0 THEN 'SUCCESS - 100% COVERAGE ACHIEVED'
    WHEN null_rows <= 50 THEN 'SUCCESS - NEARLY COMPLETE'
    ELSE 'PARTIAL SUCCESS - SOME GAPS REMAIN'
  END as fix_status

FROM final_coverage;

-- Step 5: Show which dates still have NULLs (if any)
SELECT 
  'REMAINING NULL DATES' as check_type,
  date,
  DATE_DIFF(CURRENT_DATE(), date, DAY) as days_ago
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE palm_price IS NULL
ORDER BY date DESC
LIMIT 20;

