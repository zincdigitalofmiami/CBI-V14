# Fetch ZL 1-Minute Data - Quick Instructions

## Status: Ready to Download from Databento

Since the ZL 1-minute data is queued in Databento, follow these steps to fetch and process it:

---

## Option 1: Manual Download (Quickest)

### Step 1: Download from Databento Portal

1. Go to https://databento.com/portal/batch
2. Find your ZL 1-minute job (look for most recent job with ZL symbol)
3. Click "Download" when status shows "Done"
4. Save the zip file (should be named like `GLBX-XXXXXXXX-XXXXXXXX.zip`)

### Step 2: Extract to Raw Directory

```bash
# Assuming download is in ~/Downloads
cd ~/Downloads

# Find the ZL 1-minute zip (check which one has ZL ohlcv-1m files)
unzip -l GLBX-*.zip | grep "ZL.*ohlcv-1m"

# Once identified, extract it
JOB_ID="GLBX-20251118-XXXXXXXXX"  # Replace with actual job ID
unzip -o ${JOB_ID}.zip -d "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl/${JOB_ID}/"
```

### Step 3: Verify 1-Minute Files

```bash
# Check for 1-minute OHLCV files
find "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_zl" -name "*ohlcv-1m*" | wc -l

# Should show hundreds/thousands of files
# Sample file should look like: glbx-mdp3-20241118.ohlcv-1m.json
```

### Step 4: Rerun ZL Aggregator

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python3 scripts/ingest/aggregate_zl_intraday.py
```

**Expected Output:**
```
Loaded glbx-mdp3-YYYYMMDD.ohlcv-1m.json: XXXX rows (1min)
Resampled 1min -> 5min: YYYY rows  
Resampled 1min -> 15min: YYYY rows
Resampled 1min -> 30min: YYYY rows
Resampled 1min -> 60min: YYYY rows  # ← This is the key one for microstructure
Saved 3998 rows × 14 cols to staging/zl_daily_aggregated.parquet
```

### Step 5: Validate Features

```bash
python3 - <<'PY'
import pandas as df
df = pd.read_parquet("TrainingData/staging/zl_daily_aggregated.parquet")

# Check microstructure features
micro_cols = [c for c in df.columns if '60min' in c]
print("ZL Microstructure Features (now from 1-minute data):")
for col in micro_cols:
    null_pct = df[col].isna().sum() / len(df) * 100
    mean_val = df[col].mean()
    print(f"  ✅ {col}: {null_pct:.1f}% null, mean={mean_val:.4f}")
PY
```

---

## Option 2: Automated with API Key

### Step 1: Set Up Databento API Key

Get your key from: https://databento.com/portal/keys

```bash
# Store in keychain
security add-generic-password -a databento -s databento_api_key -w "YOUR_API_KEY_HERE" -U
```

### Step 2: Run Auto-Fetch Script

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python3 scripts/ingest/check_and_fetch_zl_1min.py
```

This will:
- ✅ Check for ZL batch jobs
- ✅ Download when ready
- ✅ Extract to proper directory
- ✅ Count 1-minute files
- ✅ Provide next steps

---

## What to Expect

### Before (Current State):
```
TrainingData/raw/databento_zl/
├── GLBX-...-FRGDM3B7UG/
│   └── glbx-mdp3-20100606-20251117.ohlcv-1d.json  (daily only)
└── GLBX-...-TAAH7VN45V/
    └── glbx-mdp3-*.ohlcv-1h.json  (hourly only - 4000+ files)
```

### After (With 1-Minute Data):
```
TrainingData/raw/databento_zl/
├── GLBX-...-FRGDM3B7UG/  (existing - daily)
├── GLBX-...-TAAH7VN45V/  (existing - hourly)
└── GLBX-...-XXXXXXXXX/   (NEW - 1-minute)
    ├── glbx-mdp3-20241101.ohlcv-1m.json
    ├── glbx-mdp3-20241102.ohlcv-1m.json
    ├── glbx-mdp3-20241103.ohlcv-1m.json
    └── ... (one file per day for last year = ~365 files)
```

### Feature Impact:

**Current (1-hour data):**
- `zl_60min_realized_vol`: ⚠️ Wrong (computed from 60min bars)
- `zl_60min_hl_vol`: ⚠️ Wrong (hourly candles)
- `zl_60min_vwap`: ⚠️ Wrong (no intraday ticks)

**After (1-minute data):**
- `zl_60min_realized_vol`: ✅ Correct (computed from 1min bars resampled to 60min)
- `zl_60min_hl_vol`: ✅ Correct (true intraday high-low)
- `zl_60min_vwap`: ✅ Correct (volume-weighted from 1min)

---

## Quick Check: Is Data Already Downloaded?

```bash
# Check most recent Downloads
ls -lht ~/Downloads/*.zip | head -5

# Look for files from today (Nov 18) that might be ZL
# Check their contents:
cd ~/Downloads
for f in GLBX-20251118-*.zip; do
    echo "=== $f ==="
    unzip -l "$f" | grep -E "ZL|ohlcv-1m" | head -3
done
```

If you find a zip with `ZL` and `ohlcv-1m` files, extract it per Step 2 above.

---

## Troubleshooting

### "Job still queued/processing"
- Wait for Databento to finish processing
- Check https://databento.com/portal/batch for status
- Usually takes 10-30 minutes for 1 year of 1-minute data

### "Job done but can't find download"
- Check your Databento portal downloads page
- Files might be under different name
- Try databento CLI: `databento batch download JOB_ID`

### "Downloaded but still getting 1h data errors"
- Make sure you extracted to correct directory
- Verify files are `*ohlcv-1m*.json` not `*ohlcv-1h*.json`
- Rerun aggregator script

---

## Status Check After Processing

```bash
# Verify 1-minute files loaded
cd "/Volumes/Satechi Hub/Projects/CBI-V14"

python3 - <<'PY'
import pandas as pd
from pathlib import Path

# Check file sizes as proxy for data completeness
zl_staging = Path("TrainingData/staging/zl_daily_aggregated.parquet")
print(f"ZL staging file: {zl_staging.stat().st_size / 1024:.1f} KB")

# Load and inspect
df = pd.read_parquet(zl_staging)
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"\nFeatures:")
for col in sorted(df.columns):
    print(f"  {col}")
PY
```

**Expected:** File should be larger (more features from 1-minute resampling), and `zl_60min_*` columns should have realistic values.

---

**Once complete, the entire MES+ZL pipeline will be 100% production-ready!** 🎉

