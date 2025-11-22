# Loader Planning Report

**Date:** November 21, 2025
**Status:** Planning Phase

---

## 1. Source Data Analysis

We have identified two primary data sources in `TrainingData/staging/` that match our needs for bootstrapping the `market_data.databento_futures_ohlcv_1d` table.

### A. ZL (Soybean Oil)
*   **Source File:** `zl_daily_aggregated.parquet`
*   **Key Columns Found:**
    *   `date` (Timestamp)
    *   `zl_open`, `zl_high`, `zl_low`, `zl_close`
    *   `zl_volume`
    *   `zl_60min_vwap` (Valuable proxy for daily VWAP)

### B. MES (Micro E-mini S&P 500)
*   **Source File:** `mes_daily_aggregated.parquet`
*   **Key Columns Found:**
    *   `date` (Timestamp)
    *   `mes_open`, `mes_high`, `mes_low`, `mes_close`
    *   `mes_volume`
    *   `mes_60min_vwap`

---

## 2. Proposed Schema Mapping

The BigQuery table `market_data.databento_futures_ohlcv_1d` expects specific column names. We will apply the following transformations:

| BigQuery Column | ZL Source Column | MES Source Column | Logic / Default |
| :--- | :--- | :--- | :--- |
| **data_date** | `date` | `date` | Cast to DATE |
| **symbol** | *Static* | *Static* | 'ZL' / 'MES' |
| **open** | `zl_open` | `mes_open` | Float |
| **high** | `zl_high` | `mes_high` | Float |
| **low** | `zl_low` | `mes_low` | Float |
| **close** | `zl_close` | `mes_close` | Float |
| **settle** | `zl_close` | `mes_close` | Proxy using Close (Settle not in staging) |
| **volume** | `zl_volume` | `mes_volume` | Integer |
| **vwap** | `zl_60min_vwap` | `mes_60min_vwap` | Float |
| **open_interest** | *None* | *None* | NULL |
| **instrument_id** | *None* | *None* | NULL |
| **exchange** | *None* | *None* | 'CBOT' (ZL) / 'CME' (MES) |
| **currency** | *None* | *None* | 'USD' |
| **dataset** | *None* | *None* | 'history_bootstrap' |

---

## 3. Loader Script Strategy (`scripts/ingestion/load_databento_raw.py`)

The script will perform the following operations:

1.  **Initialize BigQuery Client:** Connect to project `cbi-v14`.
2.  **Load ZL Data:**
    *   Read `zl_daily_aggregated.parquet`.
    *   Rename columns based on the mapping above.
    *   Add static metadata columns (`symbol`, `exchange`, etc.).
    *   Ensure `data_date` is properly formatted.
3.  **Load MES Data:**
    *   Read `mes_daily_aggregated.parquet`.
    *   Apply similar transformations.
4.  **Union & Upload:**
    *   Concatenate ZL and MES dataframes.
    *   Use `client.load_table_from_dataframe` to upload to `market_data.databento_futures_ohlcv_1d`.
    *   **Write Disposition:** `WRITE_TRUNCATE` (initially) or `WRITE_APPEND` (if we want to add to existing). given this is a bootstrap, `WRITE_TRUNCATE` might be safer to ensure a clean slate, or we can append if we want to preserve manual inserts. *Recommendation: WRITE_APPEND since table is currently empty.*

## 4. Verification Plan

After execution, we will run:
1.  **Row Count Check:** Verify total rows matches source files (~4000 for ZL).
2.  **View Validation:** Query `views.precomputed_features_daily` to ensure technical indicators (RSI, MACD) are calculating correctly on the newly loaded data.

---

**Ready to implement?**



