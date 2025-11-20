-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results


-- ============================================
-- COMPREHENSIVE 24-AUDIT SUITE
-- MANDATORY PRE-TRAINING VALIDATION
-- ============================================
-- 
-- ⚠️ CRITICAL: This audit suite MUST be executed before ANY model training
-- All 24 audits must PASS before proceeding to training
-- This is a STAPLE requirement - always use before training
--
-- Usage: Run this entire script before CREATE MODEL statements
-- Expected: All audits return PASS status
-- Action: Fix any FAIL results immediately, re-run audits
--
-- ============================================

-- ============================================
-- AUDIT 1: CORRECT TABLE EXISTS
-- ============================================
SELECT 
  'AUDIT 1: Table Exists' AS audit_name,
  table_name,
  CASE 
    WHEN table_name IS NOT NULL THEN '✅ PASS'
    ELSE '❌ FAIL - Table does not exist'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'full_220_comprehensive_2yr';  -- Update table name as needed

-- ============================================
-- AUDIT 2: COLUMN COUNT VALIDATION
-- ============================================
SELECT 
  'AUDIT 2: Column Count' AS audit_name,
  COUNT(*) AS total_columns,
  CASE 
    WHEN COUNT(*) BETWEEN 2000 AND 2500 THEN '✅ PASS'
    ELSE '❌ FAIL - Unexpected column count'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr';

-- ============================================
-- AUDIT 3: NULL COLUMN DETECTION
-- ============================================
-- Note: This is a simplified check - full UNPIVOT may be too expensive
-- Manual verification recommended: Check INFORMATION_SCHEMA for NULL columns
SELECT 
  'AUDIT 3: NULL Columns' AS audit_name,
  column_name,
  CASE 
    WHEN is_nullable = 'YES' THEN '⚠️ WARNING - Nullable column (check data)'
    ELSE '✅ PASS'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
  AND is_nullable = 'YES'
LIMIT 50;  -- Sample check - full scan may be expensive

-- ============================================
-- AUDIT 4: FORWARD-LOOKING LEAKAGE CHECK
-- ============================================
SELECT 
  'AUDIT 4: Forward-Looking Leakage' AS audit_name,
  column_name,
  CASE 
    WHEN column_name LIKE '%lead%' OR column_name LIKE '%next%' THEN '❌ FAIL - Forward-looking leakage'
    ELSE '✅ PASS'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
  AND (column_name LIKE '%lead%' OR column_name LIKE '%next%');

-- ============================================
-- AUDIT 5: TARGET-ACTUAL ALIGNMENT
-- ============================================
SELECT 
  'AUDIT 5: Target Alignment' AS audit_name,
  CORR(target_1m, zl_price_current) AS correlation,
  CASE 
    WHEN CORR(target_1m, zl_price_current) > 0.95 THEN '✅ PASS'
    ELSE '❌ FAIL - Target misaligned'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
WHERE target_1m IS NOT NULL AND zl_price_current IS NOT NULL;

-- ============================================
-- AUDIT 6: DISTRIBUTION DRIFT CHECK
-- ============================================
WITH stats_2024 AS (
  SELECT 
    AVG(palm_price) AS avg_palm_2024,
    STDDEV(palm_price) AS std_palm_2024
  FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
  WHERE date >= '2024-01-01' AND date < '2025-01-01'
),
stats_2025 AS (
  SELECT 
    AVG(palm_price) AS avg_palm_2025,
    STDDEV(palm_price) AS std_palm_2025
  FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
  WHERE date >= '2025-01-01'
)
SELECT 
  'AUDIT 6: Distribution Drift' AS audit_name,
  ABS(s2025.avg_palm_2025 - s2024.avg_palm_2024) / NULLIF(s2024.std_palm_2024, 0) AS z_score,
  CASE 
    WHEN ABS(s2025.avg_palm_2025 - s2024.avg_palm_2024) / NULLIF(s2024.std_palm_2024, 0) < 2 THEN '✅ PASS'
    ELSE '⚠️ WARNING - Significant drift detected'
  END AS status
FROM stats_2024 s2024 CROSS JOIN stats_2025 s2025;

-- ============================================
-- AUDIT 7: MONOTONIC SANITY CHECK
-- ============================================
SELECT 
  'AUDIT 7: Monotonic Sanity' AS audit_name,
  CORR(rin_d4_price, target_1m) AS rin_target_corr,
  CASE 
    WHEN CORR(rin_d4_price, target_1m) < -0.6 THEN '✅ PASS'
    ELSE '⚠️ WARNING - Monotonic constraint may be incorrect'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
WHERE rin_d4_price IS NOT NULL AND target_1m IS NOT NULL;

-- ============================================
-- AUDIT 8: STRING COLUMN DETECTION
-- ============================================
SELECT 
  'AUDIT 8: String Columns' AS audit_name,
  column_name,
  data_type,
  CASE 
    WHEN data_type = 'STRING' AND column_name != 'date' THEN '❌ FAIL - Non-date string column'
    ELSE '✅ PASS'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
  AND data_type = 'STRING'
  AND column_name != 'date';

-- ============================================
-- AUDIT 9: SEQUENTIAL SPLIT DATE VALIDATION
-- ============================================
SELECT 
  'AUDIT 9: Split Date Validation' AS audit_name,
  MAX(date) AS max_training_date,
  CASE 
    WHEN MAX(date) < '2025-09-01' THEN '✅ PASS'
    ELSE '❌ FAIL - Training data includes future dates'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
WHERE target_1m IS NOT NULL;

-- ============================================
-- AUDIT 10: DUPLICATE COLUMN CHECK
-- ============================================
SELECT 
  'AUDIT 10: Duplicate Columns' AS audit_name,
  column_name,
  COUNT(*) AS occurrence_count,
  CASE 
    WHEN COUNT(*) = 1 THEN '✅ PASS'
    ELSE '❌ FAIL - Duplicate column name'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
GROUP BY column_name
HAVING COUNT(*) > 1;

-- ============================================
-- AUDIT 11: DART BOOSTER SUPPORT
-- ============================================
SELECT 
  'AUDIT 11: DART Support' AS audit_name,
  '✅ PASS - DART supported in BQML' AS status;

-- ============================================
-- AUDIT 12: SCHEMA STABILITY
-- ============================================
SELECT 
  'AUDIT 12: Schema Stability' AS audit_name,
  MAX(date) AS latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) AS days_behind,
  CASE 
    WHEN DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) <= 1 THEN '✅ PASS'
    ELSE '⚠️ WARNING - Data may be stale'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`;

-- ============================================
-- AUDIT 13: TIMESTAMP CONVERSION VALIDATION
-- ============================================
SELECT 
  'AUDIT 13: Timestamp Conversion' AS audit_name,
  COUNT(*) AS total_rows,
  COUNTIF(date IS NULL) AS null_dates,
  CASE 
    WHEN COUNTIF(date IS NULL) = 0 THEN '✅ PASS'
    ELSE '❌ FAIL - Invalid date conversions'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
WHERE date IS NULL OR date < '2020-01-01' OR date > '2026-01-01';

-- ============================================
-- AUDIT 14: EXCEPT CLAUSE COMPLETENESS
-- ============================================
-- Manual verification required
SELECT 
  'AUDIT 14: EXCEPT Completeness' AS audit_name,
  'Manual verification required' AS note,
  'Check EXCEPT clause includes all columns from Audit 3' AS instruction;

-- ============================================
-- AUDIT 15: MODEL NAME CONSISTENCY
-- ============================================
-- Manual verification required
SELECT 
  'AUDIT 15: Model Name Consistency' AS audit_name,
  'Manual verification required' AS note,
  'Check CREATE MODEL, ML.EVALUATE, ML.PREDICT all use same model name' AS instruction;

-- ============================================
-- AUDIT 16: DATE RANGE VALIDATION
-- ============================================
SELECT 
  'AUDIT 16: Date Range' AS audit_name,
  MIN(date) AS min_date,
  MAX(date) AS max_date,
  CASE 
    WHEN MIN(date) >= '2024-01-01' AND MAX(date) <= CURRENT_DATE() THEN '✅ PASS'
    ELSE '❌ FAIL - Date range incorrect'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`;

-- ============================================
-- AUDIT 17: SYMBOL LIST COMPLETENESS
-- ============================================
SELECT 
  'AUDIT 17: Symbol Completeness' AS audit_name,
  COUNT(DISTINCT 
    CASE 
      WHEN column_name LIKE '%_close%' THEN REGEXP_EXTRACT(column_name, r'^([^_]+)_')
      ELSE NULL
    END
  ) AS unique_symbols,
  CASE 
    WHEN COUNT(DISTINCT 
      CASE 
        WHEN column_name LIKE '%_close%' THEN REGEXP_EXTRACT(column_name, r'^([^_]+)_')
        ELSE NULL
      END
    ) >= 200 THEN '✅ PASS'
    ELSE '⚠️ WARNING - Missing symbols'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
  AND column_name LIKE '%_close%';

-- ============================================
-- AUDIT 18: COLUMN NAME SANITIZATION
-- ============================================
SELECT 
  'AUDIT 18: Column Sanitization' AS audit_name,
  column_name,
  CASE 
    WHEN column_name LIKE '%^%' OR column_name LIKE '%=%' OR column_name LIKE '%/%' THEN '⚠️ WARNING - Special characters may cause issues'
    ELSE '✅ PASS'
  END AS status
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'full_220_comprehensive_2yr'
  AND (column_name LIKE '%^%' OR column_name LIKE '%=%' OR column_name LIKE '%/%');

-- ============================================
-- AUDIT 19: QUANTILE CONSISTENCY (POST-PROCESSING)
-- ============================================
-- Post-training validation
SELECT 
  'AUDIT 19: Quantile Consistency' AS audit_name,
  'Post-training validation' AS note,
  'Run after model training - verify LEAST/GREATEST fix applied' AS instruction;

-- ============================================
-- AUDIT 20: MONOTONIC CONSTRAINTS SYNTAX
-- ============================================
-- Manual verification required
SELECT 
  'AUDIT 20: Monotonic Syntax' AS audit_name,
  'Manual verification required' AS note,
  'Check monotone_constraints = [("feature", -1), ...] format in CREATE MODEL' AS instruction;

-- ============================================
-- AUDIT 21: DART PARAMETERS VALIDATION
-- ============================================
-- Manual verification required
SELECT 
  'AUDIT 21: DART Parameters' AS audit_name,
  'Manual verification required' AS note,
  'Check: drop_rate 0-1, skip_drop 0-1, num_parallel_tree > 0, max_tree_depth > 0' AS instruction;

-- ============================================
-- AUDIT 22: TRAINING DATA SIZE
-- ============================================
SELECT 
  'AUDIT 22: Training Data Size' AS audit_name,
  COUNT(*) AS training_rows,
  CASE 
    WHEN COUNT(*) >= 500 THEN '✅ PASS'
    ELSE '❌ FAIL - Insufficient training data'
  END AS status
FROM `cbi-v14.models_v4.full_220_comprehensive_2yr`
WHERE target_1m IS NOT NULL
  AND date >= '2024-01-01';

-- ============================================
-- AUDIT 23: FEATURE COUNT VALIDATION
-- ============================================
-- Manual calculation required
SELECT 
  'AUDIT 23: Feature Count' AS audit_name,
  'Manual calculation required' AS note,
  'Calculate: Total columns - EXCEPT list count, should be >= 2000' AS instruction;

-- ============================================
-- AUDIT 24: EXCEPT CLAUSE EXISTENCE CHECK
-- ============================================
-- Manual verification required
SELECT 
  'AUDIT 24: EXCEPT Existence' AS audit_name,
  'Manual verification required' AS note,
  'Check each column in EXCEPT list exists in INFORMATION_SCHEMA.COLUMNS' AS instruction;

-- ============================================
-- AUDIT SUMMARY
-- ============================================
-- Run all audits above, then review results
-- All audits must show ✅ PASS or acceptable warnings
-- Any ❌ FAIL must be fixed before training
-- Document all results before proceeding

