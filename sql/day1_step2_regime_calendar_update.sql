-- ============================================================================
-- DAY 1 STEP 2: BigQuery Regime Calendar Update
-- Status: Ready for execution in BigQuery Console
-- Expected Runtime: ~10 seconds
-- ============================================================================

BEGIN
  -- 1. Clean up legacy keys
  DELETE FROM `training.regime_calendar`
  WHERE regime IN ('trump_return_2024_2025', 'trump_2023_2025');

  -- 2. Insert Canonical Split Regimes
  INSERT INTO `training.regime_calendar` (regime, weight, start_date, end_date, description)
  VALUES
    ('trump_anticipation_2024', 400, '2023-11-01', '2025-01-19', 'Trump 2.0 anticipation'),
    ('trump_second_term',       600, '2025-01-20', '2029-01-20', 'Trump second term');

  -- 3. CRITICAL VERIFICATION: Gap Check
  -- Expected: gap_days = 1 (continuous coverage)
  SELECT
      regime,
      start_date,
      end_date,
      LEAD(start_date) OVER (ORDER BY start_date) AS next_start,
      DATE_DIFF(LEAD(start_date) OVER (ORDER BY start_date), end_date, DAY) AS gap_days
  FROM `training.regime_calendar`
  WHERE regime LIKE 'trump_%'
  ORDER BY start_date;
END;

-- ============================================================================
-- EXPECTED OUTPUT:
-- regime                  | start_date  | end_date    | next_start  | gap_days
-- ------------------------|-------------|-------------|-------------|----------
-- trump_anticipation_2024 | 2023-11-01  | 2025-01-19  | 2025-01-20  | 1        ✅
-- trump_second_term       | 2025-01-20  | 2029-01-20  | NULL        | NULL     ✅
-- ============================================================================




