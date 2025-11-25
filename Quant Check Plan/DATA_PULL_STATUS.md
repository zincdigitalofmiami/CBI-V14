# Data Pull Status
**Updated:** 2025-11-25

---

## ✅ COMPLETED TODAY

### Databento CSV Jobs Submitted (Processing)
| Symbol | Job ID | Schema | Status |
|--------|--------|--------|--------|
| ZL.FUT | GLBX-20251125-PBF5APJPGQ | ohlcv-1d CSV | Processing |
| ZS.FUT | GLBX-20251125-RBE5N8KYEP | ohlcv-1d CSV | Processing |
| ZM.FUT | GLBX-20251125-XQNFPDW9G4 | ohlcv-1d CSV | Processing |
| CL.FUT | GLBX-20251125-E3ADT7UYEW | ohlcv-1d CSV | Processing |
| HO.FUT | GLBX-20251125-EVELES7FL7 | ohlcv-1d CSV | Processing |
| MES.FUT | GLBX-20251125-Q5YGRMQMKL | ohlcv-1d CSV | Processing |
| ES.FUT | GLBX-20251125-P6EGKXHCBF | ohlcv-1d CSV | Processing |

**Date Range:** 2010-06-06 → 2025-11-25  
**Encoding:** CSV (BigQuery compatible)  
**Compression:** None  

### BigQuery Data Audit ✅
- `market_data.databento_futures_ohlcv_1d`: 6,034 rows, **0 duplicates**
- `features.zl_daily_v1`: 3,936 rows, **0 duplicates**
- Math verified: return_1d, ma_5 calculations correct
- Training view: **NO JOINS** - only SELECT from feature table

### Scripts Created/Updated
1. `scripts/ingest/submit_databento_csv_jobs.py` - CSV batch job submission
2. `scripts/ingest/load_databento_to_bigquery.py` - Loader with correct schema

---

## 📊 CURRENT BIGQUERY STATE

| Table | Rows | Symbols | Date Range |
|-------|------|---------|------------|
| market_data.databento_futures_ohlcv_1d | 6,034 | ZL, MES | 2010-2025 |
| features.zl_daily_v1 | 3,936 | ZL | 2010-2025 |
| training.vw_zl_1m_v1 | 3,921 | ZL | View (no joins) |

**Missing (awaiting CSV jobs):** ZS, ZM, CL, HO, ES

---

## 🔄 ARCHITECTURE CONFIRMED (NO JOINS)

```
1. CSV from Databento
   ↓
2. LOAD → market_data.* (partitioned, MERGE dedupe)
   ↓
3. PYTHON CALCULATOR → features.zl_daily_v1 (DENORMALIZED)
   - All TA indicators baked in
   - Regime stamped in Python
   - NO external joins
   ↓
4. TRAINING VIEW → SELECT from feature table only
   - Adds LEAD() targets
   - Date-based split
   - NO JOINS
   ↓
5. MAC TRAINING → SELECT * → DataFrame → LightGBM
```

---

## ⏳ NEXT STEPS

1. **Wait for CSV jobs to complete** (~20-30 min remaining)
2. **Download completed jobs** to external drive
3. **Load to BigQuery** using `load_databento_to_bigquery.py`
4. **Run Python calculator** to create features for ZS, ZM, CL, HO
5. **Build crush margin features** (requires ZL + ZS + ZM)
6. **Retrain ZL model** with expanded features

---

## 📁 External Drive Data

| Directory | Files | Size |
|-----------|-------|------|
| databento_zl | 4,002 | 488M |
| databento_zs | 8,004 | 37M |
| databento_zm | 8,002 | 37M |
| databento_cl | 9,596 | 63M |
| databento_ho | 9,596 | 47M |
| databento_mes | JSON | 749M |
| databento_es | 4,794 | 22M |

---

**Monitor jobs:** https://databento.com/portal/batch/jobs
