# FX Data Source Clarification
**Date:** November 24, 2025  
**Status:** ✅ Updated - FX comes from FRED, not Databento

---

## Primary FX Source: FRED

**All FX data comes from FRED, not Databento.**

### FRED FX Series (All Loaded - 2010-2025):

| Series | Purpose | Rows | Date Range | Status |
|--------|---------|------|------------|--------|
| **DEXJPUS** | USD/JPY (carry trade, risk sentiment) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXCHUS** | USD/CNY (China FX, trade impact) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXUSEU** | EUR/USD (Euro cross, dollar strength) | 3,975 | 2010-2025 | ✅ Loaded |
| **DEXBZUS** | USD/BRL (Brazil FX, soy producer currency) | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXBGS** | Dollar Index Broad (overall USD strength) | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXAFEGS** | Dollar Index AFE (Advanced Foreign Economies) | 3,975 | 2010-2025 | ✅ Loaded |
| **DTWEXEMEGS** | Dollar Index EME (Emerging Market Economies) | 3,975 | 2010-2025 | ✅ Loaded |

**Total:** 7 FX series from FRED, all with complete 15-year history.

---

## Optional: Databento FX Futures

**Databento FX futures are optional, not required:**

| Symbol | Purpose | Status |
|--------|---------|--------|
| **6E.FUT** | Euro FX Futures (EUR/USD) | Optional |
| **6J.FUT** | Japanese Yen Futures (USD/JPY) | Optional |
| **6B.FUT** | British Pound Futures (GBP/USD) | Optional |
| **6A.FUT** | Australian Dollar Futures (AUD/USD) | Optional |
| **6C.FUT** | Canadian Dollar Futures (USD/CAD) | Optional |
| **6N.FUT** | New Zealand Dollar Futures (NZD/USD) | Optional |

**Use Case:** Databento FX futures provide:
- Intraday granularity (1m, 1h bars)
- Options data (if needed for vol surface)
- Microstructure (BBO, depth)

**For ZL/MES modeling:** FRED FX series are sufficient for daily features.

---

## Feature Calculation

**All FX features are calculated from FRED data:**

```sql
-- Example: FX features from FRED
WITH fx_base AS (
    SELECT 
        date,
        series_id,
        value AS close,
        LN(value / LAG(value) OVER (PARTITION BY series_id ORDER BY date)) AS fx_ret_1d
    FROM raw_intelligence.fred_economic
    WHERE series_id IN ('DEXBZUS', 'DEXCHUS', 'DEXJPUS', 'DEXUSEU', 'DTWEXBGS')
)
SELECT
    date,
    MAX(CASE WHEN series_id = 'DEXBZUS' THEN fx_ret_1d END) AS usd_brl_ret_1d,
    MAX(CASE WHEN series_id = 'DEXCHUS' THEN fx_ret_1d END) AS usd_cny_ret_1d,
    MAX(CASE WHEN series_id = 'DEXJPUS' THEN fx_ret_1d END) AS usd_jpy_ret_1d,
    MAX(CASE WHEN series_id = 'DEXUSEU' THEN fx_ret_1d END) AS eur_usd_ret_1d,
    MAX(CASE WHEN series_id = 'DTWEXBGS' THEN fx_ret_1d END) AS dollar_index_ret_1d,
    -- Realized volatility
    STDDEV_SAMP(fx_ret_1d) OVER (PARTITION BY series_id ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) * SQRT(252) AS fx_realized_vol_10d
FROM fx_base
GROUP BY date
```

---

## Updated Plans

**All plans have been updated to reflect FRED as primary FX source:**

1. ✅ `PHASE2_DATA_PULL_PLAN.md` - Updated FX section
2. ✅ `MES_MASTER_PLAN.md` - Updated FX data requirements
3. ✅ `ZL_EXECUTION_PLAN.md` - Updated FX features section
4. ✅ `DATA_PULL_STATUS.md` - Added FX series table
5. ✅ `PHASE1_DATA_DOMAINS_TIPS_AND_GAPS.md` - Updated FX calculations

---

## Summary

**Primary Source:** FRED (7 FX series, 2010-2025)  
**Optional Source:** Databento FX futures (for intraday/microstructure, not required)  
**Status:** ✅ All FX data loaded and ready for feature calculation

---

**Status:** ✅ **FX SOURCE CLARIFIED - FRED IS PRIMARY SOURCE**

