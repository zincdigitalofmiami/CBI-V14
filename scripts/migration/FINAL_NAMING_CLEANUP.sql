-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- FINAL NAMING CLEANUP - LOCK DOWN ARCHITECTURE
-- Date: November 14, 2025
-- Purpose: Remove inconsistencies, enforce Option 3 naming
-- Status: FINAL - After this, NO MORE NAMING CHANGES
-- ============================================

-- ============================================
-- SECTION 1: VERIFY DUPLICATE TABLES
-- ============================================
-- These should be identical to the _allhistory_ variants
-- If row counts match, they are duplicates and should be dropped

SELECT 
  'DUPLICATE VERIFICATION' AS check_type,
  a.table_name AS variant_all,
  a.row_count AS all_rows,
  b.table_name AS variant_allhistory,
  b.row_count AS allhistory_rows,
  CASE WHEN a.row_count = b.row_count THEN 'DUPLICATE' ELSE 'DIFFERENT' END AS status
FROM (
  SELECT table_name, row_count 
  FROM `cbi-v14.training`.__TABLES__
  WHERE table_name LIKE 'zl_training_prod_all_%'
    AND table_name NOT LIKE '%allhistory%'
) a
JOIN (
  SELECT table_name, row_count
  FROM `cbi-v14.training`.__TABLES__
  WHERE table_name LIKE 'zl_training_prod_allhistory_%'
) b
ON REPLACE(a.table_name, '_all_', '_allhistory_') = b.table_name
ORDER BY a.table_name;

-- Expected output: 5 rows, all status = 'DUPLICATE'

-- ============================================
-- SECTION 2: DROP DUPLICATE TABLES
-- ============================================
-- ONLY execute after verifying Section 1 shows DUPLICATE status

-- SAFETY CHECK: Backup first (optional)
/*
CREATE TABLE `cbi-v14.archive.backup_20251114__training__zl_training_prod_all_1w` AS
SELECT *, CURRENT_TIMESTAMP() AS archived_at FROM `cbi-v14.training.zl_training_prod_all_1w`;

CREATE TABLE `cbi-v14.archive.backup_20251114__training__zl_training_prod_all_1m` AS
SELECT *, CURRENT_TIMESTAMP() AS archived_at FROM `cbi-v14.training.zl_training_prod_all_1m`;

CREATE TABLE `cbi-v14.archive.backup_20251114__training__zl_training_prod_all_3m` AS
SELECT *, CURRENT_TIMESTAMP() AS archived_at FROM `cbi-v14.training.zl_training_prod_all_3m`;

CREATE TABLE `cbi-v14.archive.backup_20251114__training__zl_training_prod_all_6m` AS
SELECT *, CURRENT_TIMESTAMP() AS archived_at FROM `cbi-v14.training.zl_training_prod_all_6m`;

CREATE TABLE `cbi-v14.archive.backup_20251114__training__zl_training_prod_all_12m` AS
SELECT *, CURRENT_TIMESTAMP() AS archived_at FROM `cbi-v14.training.zl_training_prod_all_12m`;
*/

-- DROP DUPLICATES
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_1w`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_1m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_3m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_6m`;
DROP TABLE IF EXISTS `cbi-v14.training.zl_training_prod_all_12m`;

-- ============================================
-- SECTION 3: VERIFY ONLY CORRECT NAMES REMAIN
-- ============================================

SELECT 
  'POST-CLEANUP VERIFICATION' AS check_type,
  table_name,
  row_count,
  CASE 
    WHEN table_name LIKE 'zl_training_%_allhistory_%' THEN 'CORRECT'
    WHEN table_name LIKE 'zl_training_%_crisis_%' THEN 'CORRECT'
    WHEN table_name LIKE 'zl_training_%_trump_%' THEN 'CORRECT'
    WHEN table_name LIKE 'zl_training_%_precrisis_%' THEN 'CORRECT'
    WHEN table_name LIKE 'zl_training_%_recovery_%' THEN 'CORRECT'
    WHEN table_name LIKE 'zl_training_%_tradewar_%' THEN 'CORRECT'
    WHEN table_name IN ('regime_calendar', 'regime_weights') THEN 'SUPPORT'
    ELSE 'UNEXPECTED'
  END AS naming_status
FROM `cbi-v14.training`.__TABLES__
WHERE table_name NOT LIKE 'legacy_%'
ORDER BY naming_status, table_name;

-- Expected: All rows show 'CORRECT' or 'SUPPORT'
-- If any 'UNEXPECTED', investigate and fix

-- ============================================
-- SECTION 4: FINAL TABLE INVENTORY
-- ============================================

SELECT 
  'FINAL TRAINING DATASET INVENTORY' AS report_type,
  COUNT(*) AS total_tables,
  COUNTIF(table_name LIKE 'zl_training_prod_allhistory_%') AS prod_allhistory_tables,
  COUNTIF(table_name LIKE 'zl_training_full_allhistory_%') AS full_allhistory_tables,
  COUNTIF(table_name LIKE 'zl_training_%_crisis_%') AS regime_specific_tables,
  COUNTIF(table_name IN ('regime_calendar', 'regime_weights')) AS support_tables
FROM `cbi-v14.training`.__TABLES__
WHERE table_name NOT LIKE 'legacy_%';

-- Expected output:
-- total_tables: 23 (or 18 after dropping 5 duplicates)
-- prod_allhistory_tables: 5
-- full_allhistory_tables: 5
-- regime_specific_tables: 6
-- support_tables: 2

-- ============================================
-- EXECUTION LOG
-- ============================================
/*
Date: 2025-11-14
Executed by: [Your Name]
Result: [PASS/FAIL]
Notes: [Any issues encountered]

Verification:
- Section 1: [5 duplicates confirmed]
- Section 2: [5 tables dropped]
- Section 3: [0 unexpected names remaining]
- Section 4: [18 tables total, all compliant]

FINAL STATUS: Naming architecture LOCKED as Option 3
Next allowed change: NEVER (without executive approval)
*/







