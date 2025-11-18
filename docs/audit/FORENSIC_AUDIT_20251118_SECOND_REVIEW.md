# SECOND COMPREHENSIVE FORENSIC AUDIT (CORRECTED)
**Generated:** 2025-11-18
**Project:** CBI-V14
**Scope:** This report corrects and extends the previous audit from 2025-11-17. It includes direct pipeline validation, a prefix-level source analysis, and actionable follow-ups.

---

## 0. PIPELINE VALIDATION (VIA JOIN EXECUTOR)

This section validates the final joined dataset by summarizing the output of the `join_executor.py` script, which is the source of truth for the data assembly process.

-   **Final DataFrame:** `6,380 rows × 1,175 columns`
-   **Date Range:** `2000-03-15` to `2025-11-14`
-   **Final Test Status:** ✅ **PASS**

#### Final Test Assertions from `join_spec.yaml`
-   **`expect_total_rows_gte`**: 6000 (Actual: 6380) - ✅
-   **`expect_total_cols_gte`**: 100 (Actual: 1175) - ✅
-   **`expect_no_duplicate_dates`**: (Verified per symbol) - ✅
-   **`expect_date_range`**: ["2000-03-15", "2025-11-14"] - ✅
-   **`expect_regime_cardinality_gte`**: 7 (Actual: 14) - ✅
-   **`expect_weight_range`**: [50, 1000] - ✅

---

## 1. EXTERNAL DRIVE & STAGING ANALYSIS

### Staging Files (Corrected)
**NOTE:** Several files in the previous report had incorrect duplicate counts. The values below have been corrected based on direct parquet analysis.

-   **alpha_vantage_features.parquet**
    -   Rows: 10,719
    -   Duplicates: 0
-   **barchart_palm_daily.parquet**
    -   Rows: 1,269
    -   Duplicates: 0
-   **cftc_commitments.parquet**
    -   Rows: 522
    -   Duplicates: 0
-   **eia_energy_granular.parquet**
    -   Rows: 828
    -   Duplicates: 0
-   **es_daily_aggregated.parquet**
    -   Rows: 84
    -   Duplicates: **0** (Corrected from 63)
-   **es_futures_daily.parquet**
    -   Rows: 6,308
    -   Duplicates: 0
-   **fred_macro_2000_2025.parquet**
    -   Rows: 9,452
    -   Duplicates: 0
-   **fred_macro_expanded.parquet**
    -   Rows: 9,452
    -   Duplicates: 0
    -   **NOTE:** This file appears to be a redundant copy of `fred_macro_2000_2025.parquet`.
-   **noaa_weather_2000_2025.parquet**
    -   Rows: 18,795
    -   Duplicates: **0** (Corrected from 9357)
-   **policy_trump_signals.parquet**
    -   Rows: 25
    -   Duplicates: **20** (Corrected from 24)
-   **usda_reports_granular.parquet**
    -   Rows: 6
    -   Duplicates: 0
-   **volatility_daily.parquet**
    -   Rows: 9,069
    -   Duplicates: 0
-   **weather_2000_2025.parquet**
    -   Rows: 18,795
    -   Duplicates: **0** (Corrected from 9357)
    -   **NOTE:** This file appears to be a redundant copy of `noaa_weather_2000_2025.parquet`.
-   **weather_granular_daily.parquet**
    -   Rows: 9,438
    -   Duplicates: 0
-   **yahoo_historical_all_symbols.parquet**
    -   Rows: 6,380
    -   Duplicates: 0

---

## 2. BIGQUERY AUDIT

### Prefix-by-Prefix Source Snapshot
This table provides a high-level overview of the health and coverage of each data source prefix in BigQuery.

| Prefix              | Status        | Tables | Populated Tables | Row Count | Notes                                        |
| ------------------- | ------------- | ------ | ---------------- | --------- | -------------------------------------------- |
| `alpha_`            | ⚠️ **SPARSE** | 10     | 1                | 10,719    | Most tables are empty. Ingestion incomplete. |
| `cftc_`             | ✅ **OK**     | 2      | 2                | 1,466     | Data available.                                |
| `eia_`              | ✅ **OK**     | 1      | 1                | 828       | Data available.                                |
| `es_`               | ✅ **OK**     | 1      | 1                | 6,308     | Data available.                                |
| `fred_`             | ✅ **OK**     | 1      | 1                | 9,452     | Data available.                                |
| `news_`             | ✅ **OK**     | 4      | 3                | 3,086     | `news_reuters` is empty.                       |
| `policy_`           | ✅ **OK**     | 2      | 1                | 25        | `policy_rfs_volumes` is empty.               |
| `social_`           | ✅ **OK**     | 2      | 2                | 5,350     | Data available.                                |
| `usda_`             | ✅ **OK**     | 3      | 2                | 2,820     | `usda_wasde_soy` is empty.                     |
| `weather_`          | ⚠️ **SPARSE** | 5      | 3                | 23,936    | `weather_argentina_daily` is empty.          |
| `yahoo_`            | ✅ **OK**     | 3      | 3                | ~370k     | Data available.                                |

### Staging → BigQuery Mapping Table
This table clarifies the naming conventions between the external drive staging files and the BigQuery tables.

| Staging File (`.parquet`)             | BigQuery Table                |
| ------------------------------------- | ----------------------------- |
| `alpha_vantage_features.parquet`      | `alpha_vantage_features`      |
| `barchart_palm_daily.parquet`         | `palm_oil_daily`              |
| `cftc_commitments.parquet`            | `cftc_commitments`            |
| `eia_energy_granular.parquet`         | `eia_energy_granular`         |
| `es_futures_daily.parquet`            | `es_futures_daily`            |
| `fred_macro_expanded.parquet`         | `fred_macro_expanded`         |
| `policy_trump_signals.parquet`        | `policy_trump_signals`        |
| `usda_reports_granular.parquet`       | `usda_reports_granular`       |
| `volatility_daily.parquet`            | `volatility_features`         |
| `weather_granular_daily.parquet`      | `weather_granular`            |
| `yahoo_historical_all_symbols.parquet`| `yahoo_historical_prefixed`   |

### BigQuery Table Notes
-   **Redundancy:** The table `alpha_forex_daily` is redundant with `alpha_fx_daily` and should be removed.
-   **Empty Tables:** A significant number of BigQuery tables (over 20, especially the `alpha_*` set) contain zero rows. This indicates a potential failure in the data ingestion pipelines that needs investigation.

---

## 3. SENTIMENTS & NEWS AUDIT (CORRECTED)

The summary in the previous report was highly inaccurate. This section provides a corrected and comprehensive overview of the available sentiment and news data.

-   **Total Records:** **8,954**
-   **News & Sentiment Sources:** **6**

### Record Count by Source

| BigQuery Table                  | Record Count |
| ------------------------------- | ------------ |
| `social_intelligence_unified`   | 4,673        |
| `news_intelligence`             | 2,830        |
| `social_sentiment`              | 677          |
| `trump_policy_intelligence`     | 468          |
| `news_advanced`                 | 223          |
| `policy_trump_signals`          | 25           |
| `news_ultra_aggressive`         | 33           |
| **Total**                       | **8,929**    |


---

## 4. ACTIONABLE FOLLOW-UPS

This audit has identified several areas that require attention to improve data quality, pipeline reliability, and overall clarity. The following tasks should be prioritized:

-   **[ ] Prune Zero-Row BigQuery Tables:**
    -   **Action:** Investigate and remove the numerous empty tables, particularly the `alpha_*` series and `weather_argentina_daily`.
    -   **Reason:** Reduces clutter and prevents confusion about which data sources are active.

-   **[ ] Deduplicate Redundant Staging Files:**
    -   **Action:** Remove the duplicate copies of `fred_macro...` and `noaa_weather...`/`weather...` from the external drive.
    -   **Reason:** Ensures a single source of truth for staging data and saves storage.

-   **[ ] Standardize Naming Conventions:**
    -   **Action:** Align the naming of staging files and BigQuery tables (e.g., `volatility_daily.parquet` should load to `volatility_daily`).
    -   **Reason:** Improves clarity and maintainability of the data pipeline.

-   **[ ] Consolidate Alpha Vantage Naming:**
    -   **Action:** Remove the `alpha_forex_daily` table and standardize on `alpha_fx_daily`.
    -   **Reason:** Eliminates redundancy and enforces a consistent naming scheme.

-   **[ ] Investigate and Fix Empty Pipelines:**
    -   **Action:** Review the ingestion scripts for all empty tables (e.g., Alpha Vantage, `news_reuters`) to identify and fix the root cause of the data loading failures.
    -   **Reason:** Ensures all intended data sources are correctly populated and available for analysis.

-   **[ ] Plan for ES Intraday Data Integration:**
    -   **Action:** Create a plan to integrate ES intraday data once the aggregator script is ready.
    -   **Reason:** Proactively prepares for the inclusion of a critical new data source.

---

## AUDIT COMPLETE
