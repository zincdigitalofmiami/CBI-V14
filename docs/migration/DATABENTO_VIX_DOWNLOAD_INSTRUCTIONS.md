---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Databento VIX Download Instructions
**Request ID:** OPRA-20251120-U3F99GTFES  
**Purpose:** VIX data for CVOL calculations  
**Status:** Ready for download

---

## DOWNLOAD STEPS

### 1. Access Databento Portal

Open the download page:
```
https://databento.com/portal/batch/jobs/OPRA-20251120-U3F99GTFES
```

Or navigate manually:
1. Go to https://databento.com/portal/batch
2. Log in with your credentials
3. Find job: `OPRA-20251120-U3F99GTFES`
4. Click "Download" button

### 2. Download and Extract

```bash
# Download will save to ~/Downloads (or your browser's download location)
cd ~/Downloads

# Extract to project directory
unzip -o OPRA-20251120-U3F99GTFES.zip -d "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_vix/OPRA-20251120-U3F99GTFES/"
```

### 3. Process VIX Data

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
python3 scripts/ingest/process_databento_vix.py
```

This will:
- Process all VIX records from OPRA files
- Create daily aggregated VIX data
- Integrate into volatility staging
- Prepare for CVOL calculations

---

## WHAT THIS DATA CONTAINS

**Source:** OPRA (Options Price Reporting Authority)  
**Content:** VIX options data  
**Format:** Databento JSON files  
**Use:** CVOL (CBOE Volatility Index) calculations

---

## INTEGRATION

After processing, VIX data will be:
1. Saved to: `TrainingData/raw/databento_vix/vix_daily_opra.parquet`
2. Integrated into: `staging/volatility_features.parquet`
3. Available for: CVOL calculations and volatility features

---

## VERIFICATION

After download and processing, verify:
```bash
python3 -c "
import pandas as pd
from pathlib import Path

vix_file = Path('/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/databento_vix/vix_daily_opra.parquet')
if vix_file.exists():
    df = pd.read_parquet(vix_file)
    print(f'✅ VIX data: {len(df)} rows')
    print(f'   Date range: {df[\"date\"].min()} to {df[\"date\"].max()}')
    print(f'   Columns: {list(df.columns)}')
else:
    print('❌ VIX file not found - run process_databento_vix.py')
"
```

---

**Status:** ⏳ Waiting for manual download from Databento portal




