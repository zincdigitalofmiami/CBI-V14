---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Databento Data Inventory - Complete Review

**Date:** 2025-11-18  
**Status:** Excellent MES data available! ZL 1-minute check needed.

---

## ✅ CONFIRMED DATA AVAILABLE

### MES (E-Mini S&P) - COMPLETE SET ⭐

| Timeframe | File | Size | Files | Status | Coverage |
|-----------|------|------|-------|--------|----------|
| **1-Minute** | `GLBX-20251118-R6DHL7G583.zip` | 722 MB | 98 | ✅ **Extracted** | 2019-04-14+ |
| 1-Hour | `GLBX-20251118-FEFDCP5HXU.zip` | 24 MB | 98 | ✅ Available | 2019-04-14+ |
| Daily | `GLBX-20251118-H3DTWEWHUN.zip` | 2.6 MB | 1 | ✅ **Extracted** | 2019-2025 |
| Statistics | `GLBX-20251118-NCPW3XBL8V.zip` | 598 MB | 31,524 | ✅ Available | Daily stats |

**Location:** `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_mes/`

**Processing Status:**
- ✅ All loaders fixed (spread filtering, contract calendar)
- ✅ Staging files generated (mes_daily_aggregated, mes_15min, etc.)
- ✅ Features generated (29,160 rows × 24 features)
- ✅ Training dataset ready (229,159 rows × 30 columns)
- ✅ **PRODUCTION READY**

---

### ZL (Soybean Oil) - NEED 1-MINUTE DATA

| Timeframe | File | Size | Files | Status | Coverage |
|-----------|------|------|-------|--------|----------|
| **1-Minute** | ❓ **CHECK PORTAL** | ❓ | ❓ | ⏳ **Queued/Processing?** | 2024-2025 (1 year) |
| 1-Hour | `GLBX-20251118-TAAH7VN45V.zip` | 413 MB | 3,999 | ✅ **Extracted** | 2010-2025 |
| Daily | `GLBX-20251118-FRGDM3B7UG/` | 48 MB | 1 | ✅ **Extracted** | 2010-2025 |

**Location:** `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/`

**Processing Status:**
- ✅ All loaders fixed (spread filtering, volume selection)
- ✅ Staging files generated using 1-hour data
- ⚠️ Microstructure features sub-optimal (1h instead of 1m)
- ⏳ **Need 1-minute download to complete**

---

## 🔍 CHECK DATABENTO PORTAL FOR ZL 1-MINUTE JOB

### Step 1: Check Job Status

1. Open portal: https://databento.com/portal/batch
2. Log in with your credentials
3. Look for recent jobs with:
   - Symbol: **ZL**
   - Schema: **ohlcv-1m** (1-minute)
   - Date range: Last 1 year (2024-11 to 2025-11)

### Step 2: If Job Status = "Done"

Download the file:
```bash
# Method 1: Portal download
1. Click "Download" button in portal
2. Save to ~/Downloads
3. Note the job ID (e.g., GLBX-20251118-XXXXXXXXX)

# Method 2: CLI download (if you have databento CLI)
databento batch download JOB_ID --output-dir ~/Downloads
```

### Step 3: Extract and Process

```bash
# Replace JOB_ID with actual ID from portal
cd ~/Downloads
JOB_ID="GLBX-20251118-XXXXXXXXX"

# Extract
unzip -o ${JOB_ID}.zip -d "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/${JOB_ID}/"

# Verify extraction
find "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/${JOB_ID}" -name "*ohlcv-1m*.json" | wc -l
# Should show ~365 files (one per day for last year)

# Rerun ZL aggregator with 1-minute data
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python3 scripts/ingest/aggregate_zl_intraday.py

# Verify microstructure features
python3 - <<'PY'
import pandas as pd
df = pd.read_parquet("TrainingData/staging/zl_daily_aggregated.parquet")
micro_cols = [c for c in df.columns if '60min' in c]
for col in micro_cols:
    null_pct = df[col].isna().sum() / len(df) * 100
    print(f"✅ {col}: {null_pct:.1f}% null, mean={df[col].mean():.4f}")
PY
```

### Step 4: If Job Status = "Queued" or "Processing"

Wait for it to complete (usually 10-30 minutes for 1 year of 1-minute data).

### Step 5: If Job NOT Found

Submit a new job:
```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"

# Set API key first
security add-generic-password -a databento -s databento_api_key -w "YOUR_KEY" -U

# Submit job
python3 scripts/ingest/download_zl_1min_databento.py
```

Or submit via portal:
- Dataset: GLBX.MDP3
- Symbol: ZL
- Schema: ohlcv-1m
- Date: 2024-11-18 to 2025-11-18 (last year)
- Encoding: JSON (pretty_ts, pretty_px)

---

## 📦 DATABENTO DOWNLOADS INVENTORY

### In ~/Downloads (as of Nov 18, 2025):

```
Downloaded and Available:
  ✅ GLBX-20251118-R6DHL7G583.zip ......... 722 MB (MES 1-minute) ⭐
  ✅ GLBX-20251118-TAAH7VN45V.zip ......... 413 MB (ZL 1-hour) ✅
  ✅ GLBX-20251118-H3DTWEWHUN.zip ......... 2.6 MB (MES daily) ✅
  ✅ GLBX-20251118-FEFDCP5HXU.zip ......... 24 MB (MES 1-hour) ✅
  ℹ️  GLBX-20251118-NCPW3XBL8V.zip ......... 598 MB (MES statistics)
  ℹ️  GLBX-20251118-5TS5D878NL.zip .......... 1.9 MB (MES daily contracts)

Missing:
  ❓ ZL 1-minute data ...................... CHECK PORTAL
```

### Already Extracted and Processed:

```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/
├── databento_mes/
│   ├── GLBX-20251118-R6DHL7G583/ .......... ✅ MES 1-minute (in use)
│   ├── GLBX-20251118-H3DTWEWHUN/ .......... ✅ MES daily (in use)
│   └── GLBX-20251118-FEFDCP5HXU/ .......... ✅ MES 1-hour (in use)
│
└── databento_zl/
    ├── GLBX-20251118-FRGDM3B7UG/ .......... ✅ ZL daily (in use)
    └── GLBX-20251118-TAAH7VN45V/ .......... ✅ ZL 1-hour (in use)
```

---

## 🎯 IMMEDIATE ACTION

**Check your Databento portal for the ZL 1-minute job:**

https://databento.com/portal/batch

**Look for a job with:**
- Symbol: ZL
- Schema: ohlcv-1m
- Status: "Done" (or "Queued" if still processing)

**If you can provide the job ID or tell me it's ready, I can help extract and process it immediately!**

---

## 💎 WHAT WE HAVE IS EXCELLENT

You already have **fantastic data** for MES:
- ✅ 722 MB of 1-minute bars
- ✅ 6.5 years of history
- ✅ Already processed and validated
- ✅ 229K training samples ready
- ✅ Real market data confirmed

The ZL 1-minute data will complete the set and give you accurate microstructure features for both instruments!





