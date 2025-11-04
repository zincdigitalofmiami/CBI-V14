-- ============================================
-- FIX DUPLICATE DATES AND INVALID VALUES
-- Addresses issues found in comprehensive audit
-- ============================================

-- ============================================
-- PART 1: FIX DUPLICATE DATES
-- ============================================

-- Check duplicates first
SELECT 
  'DUPLICATE CHECK' as check_type,
  date,
  COUNT(*) as duplicate_count
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
GROUP BY date
HAVING COUNT(*) > 1
ORDER BY date DESC;

-- Remove duplicates by keeping the row with most non-NULL values
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched_deduped` AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY date 
      ORDER BY 
        -- Prefer rows with more non-NULL values
        (CASE WHEN zl_price_current IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN target_1w IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN treasury_10y_yield IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN unemployment_rate IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN usd_cny_rate IS NOT NULL THEN 1 ELSE 0 END) DESC,
        date DESC  -- If tie, prefer most recent insert
    ) as row_num
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
)
WHERE row_num = 1;

-- Replace original with deduplicated version
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_super_enriched` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched_deduped`;

-- Clean up temp table
DROP TABLE IF EXISTS `cbi-v14.models_v4.training_dataset_super_enriched_deduped`;

-- ============================================
-- PART 2: FIX INVALID USD/CNY RATES (0.0 values)
-- ============================================

-- Forward-fill invalid 0.0 values with nearest valid value using MERGE
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH invalid_dates AS (
    SELECT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE usd_cny_rate = 0.0 OR (usd_cny_rate IS NOT NULL AND usd_cny_rate <= 0)
  ),
  valid_values AS (
    SELECT 
      id.date,
      LAST_VALUE(t.usd_cny_rate IGNORE NULLS) OVER (
        ORDER BY t.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as replacement_rate
    FROM invalid_dates id
    LEFT JOIN `cbi-v14.models_v4.training_dataset_super_enriched` t
    ON t.date <= id.date
    WHERE t.usd_cny_rate IS NOT NULL AND t.usd_cny_rate > 0
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id.date ORDER BY t.date DESC) = 1
  )
  SELECT date, replacement_rate as usd_cny_rate
  FROM valid_values
  WHERE replacement_rate IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  usd_cny_rate = source.usd_cny_rate;

-- ============================================
-- PART 3: VERIFICATION
-- ============================================

SELECT 
  'POST-FIX VERIFICATION' as check_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT date) as unique_dates,
  COUNT(*) - COUNT(DISTINCT date) as duplicate_count,
  COUNTIF(usd_cny_rate IS NOT NULL AND usd_cny_rate <= 0) as invalid_usd_cny,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT date) = 0 AND COUNTIF(usd_cny_rate IS NOT NULL AND usd_cny_rate <= 0) = 0
    THEN 'PASS'
    ELSE 'FAIL'
  END as fix_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

