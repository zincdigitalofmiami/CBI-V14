# Deployment Validation Report
**Date:** 2025-11-18 18:26:31  
**Project:** CBI-V14  
**Status:** In Progress

---

## Validation Results

🔍 SQL Pre-Flight Validation
============================================
Schema file: PRODUCTION_READY_BQ_SCHEMA.sql
Project: cbi-v14
Location: us-central1

✅ Schema file exists

📋 Check 1: BigQuery SQL Syntax (dry-run)
--------------------------------------------
✅ PASS: SQL syntax is valid

📋 Check 2: DEFAULT Clause Detection
--------------------------------------------
✅ PASS: No DEFAULT clauses found

📋 Check 3: Idempotency (CREATE OR REPLACE)
--------------------------------------------
✅ PASS: All tables use CREATE OR REPLACE

📋 Check 4: Required Datasets Referenced
--------------------------------------------
❌ FAIL: Missing dataset references:
   - predictions

📋 Check 5: Expected Table Count
--------------------------------------------
✅ PASS: Found 55 tables (expected >= 50)

📋 Check 6: Critical Tables Present
--------------------------------------------
✅ PASS: All critical tables present

============================================
VALIDATION SUMMARY
============================================
Total checks: 6
Passed: 5
Failed: 1

❌ VALIDATION FAILED - Fix errors before deployment

### 1. SQL Validation: ❌ FAIL

🔍 Shell Script Linting Validation
============================================

⚠️  WARNING: shellcheck not installed

Install with:
  macOS: brew install shellcheck
  Linux: apt-get install shellcheck

Skipping shell linting...

### 2. Shell Script Linting: ✅ PASS

test_alpha_to_databento_mapping (__main__.TestMigrateMasterFeatures.test_alpha_to_databento_mapping)
Test that Alpha Vantage columns map to DataBento ... ok
test_column_mapping_exists (__main__.TestMigrateMasterFeatures.test_column_mapping_exists)
Test that COLUMN_MAPPING dictionary exists ... ok
test_yahoo_column_mapping (__main__.TestMigrateMasterFeatures.test_yahoo_column_mapping)
Test that Yahoo columns are mapped correctly ... ok
test_client_initialization (__main__.TestBigQueryClient.test_client_initialization)
Test that BigQuery client can be initialized ... ok
test_project_id_constant (__main__.TestBigQueryClient.test_project_id_constant)
Test that PROJECT_ID constant is set correctly ... ok
test_no_duplicate_target_columns (__main__.TestColumnMappingLogic.test_no_duplicate_target_columns)
Test that no two source columns map to the same target ... ok
test_technical_indicator_mapping (__main__.TestColumnMappingLogic.test_technical_indicator_mapping)
Test that technical indicators are mapped with yahoo_ prefix ... ok
test_schema_validation (__main__.TestErrorHandling.test_schema_validation)
Test that schema validation exists ... ok
test_table_exists_check (__main__.TestErrorHandling.test_table_exists_check)
Test that table existence is checked ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.684s

OK
============================================================
Running Unit Tests for Migration Scripts
============================================================


============================================================
TEST SUMMARY
============================================================
Tests run: 9
Passed: 9
Failed: 0
Errors: 0
Skipped: 0

✅ ALL TESTS PASSED

### 3. Python Unit Tests: ✅ PASS

============================================================
BigQuery Current State Scanner
============================================================

📊 Parsing schema file: PRODUCTION_READY_BQ_SCHEMA.sql
   Found 11 expected datasets
   Found 55 expected tables

🔍 Scanning BigQuery project: cbi-v14
   Found 43 current datasets
   Found 654 current tables

📝 Generating report: BQ_CURRENT_STATE_REPORT.md
✅ Report saved to: BQ_CURRENT_STATE_REPORT.md

❌ Missing datasets detected - deployment required

### 4. Environment State Scan: ❌ FAIL


### 5. Required Files: ✅ PASS


### 6. BigQuery Credentials: ✅ PASS


---

## Summary

- **Total Checks:** 6
- **Passed:** 4
- **Failed:** 2

**Status:** ❌ NOT READY

Fix the failed checks above before proceeding with deployment.
