---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# External Drive → BigQuery Upload Plan
**Date**: November 18, 2025  
**Source**: Real data analysis from `/Volumes/Satechi Hub/Projects/CBI-V14`

---

## Executive Summary

You have **2.1 GB** of data on your external drive ready to upload to BigQuery.

**Recommendation**: Upload **~900 MB** of processed Parquet files, skip 1.2 GB of raw JSON.

**Cost**: **$0.03/month** (3 pennies) after upload.

---

## What's on the External Drive (Real Data)

### Total: 2.1 GB

```
TrainingData/raw/          1.8 GB  (4,946 files)
├── databento_mes/         749 MB  (2,000+ JSON files) ❌ DON'T UPLOAD
├── databento_zl/          470 MB  (2,000+ JSON files) ❌ DON'T UPLOAD
├── yahoo_finance/         177 MB  (Parquet) ✅ UPLOAD
├── cftc/                  172 MB  (Parquet) ✅ UPLOAD
├── yahoo_finance_comp/    127 MB  (Parquet) ✅ UPLOAD
├── alpha_vantage/          30 MB  (Parquet) ✅ UPLOAD
├── models_v4/              33 MB  (training tables) ✅ UPLOAD
├── market_data/            31 MB  (Parquet) ✅ UPLOAD
├── forecasting_dwh/        15 MB  (Parquet) ✅ UPLOAD
├── fred/                  7.3 MB  (Parquet) ✅ UPLOAD
├── noaa/                  2.5 MB  (Parquet) ✅ UPLOAD
├── signals/               2.8 MB  (Parquet) ✅ UPLOAD
├── usda/                  532 KB  (Parquet) ✅ UPLOAD
├── eia/                   248 KB  (Parquet) ✅ UPLOAD
└── other/                 ~10 MB  (various)

GPT_Data/                  265 MB  (metadata/exports)
```

### File Breakdown
- **JSON files**: 4,299 (mostly DataBento raw - inefficient format)
- **Parquet files**: 622 (processed data - efficient format)
- **CSV files**: 25 (small exports)

---

## Upload Strategy

### ✅ Recommended: Upload Parquet Only (~900 MB)

**What to upload**:
```
Yahoo Finance:            304 MB → yahoo_finance_comprehensive
CFTC:                     172 MB → raw_intelligence
Alpha Vantage:             30 MB → raw_intelligence
models_v4:                 33 MB → training
market_data:               31 MB → market_data
forecasting_dwh:           15 MB → forecasting_data_warehouse
FRED:                     7.3 MB → raw_intelligence
NOAA:                     2.5 MB → raw_intelligence
signals:                  2.8 MB → features
USDA:                     532 KB → raw_intelligence
EIA:                      248 KB → raw_intelligence
─────────────────────────────────
TOTAL:                   ~900 MB
```

**What NOT to upload**:
```
databento_mes/            749 MB ❌ Raw JSON - keep on drive
databento_zl/             470 MB ❌ Raw JSON - keep on drive
─────────────────────────────────
SKIP:                    1.2 GB (save 60% of storage cost)
```

**Why skip DataBento JSON?**
1. **Inefficient**: JSON is 5-10x larger than Parquet
2. **Redundant**: Likely already processed to Parquet
3. **Rarely queried**: Raw JSON not used in dashboard/training
4. **Better location**: External drive = free backup/audit trail

---

## Cost Projections

### Before Upload (Current)

| Component | Size | Cost |
|-----------|------|------|
| BigQuery storage | 0.70 GB | $0.01/month |

### After Upload (Recommended)

| Component | Size | Cost |
|-----------|------|------|
| Existing BigQuery | 0.70 GB | $0.01/month |
| New upload (Parquet) | 0.90 GB | $0.02/month |
| **TOTAL** | **1.60 GB** | **$0.03/month** |

### If You Upload Everything (Not Recommended)

| Component | Size | Cost |
|-----------|------|------|
| Existing BigQuery | 0.70 GB | $0.01/month |
| New upload (all) | 2.10 GB | $0.04/month |
| **TOTAL** | **2.80 GB** | **$0.05/month** |

### Free Tier Headroom

| Tier | Limit | Usage (after upload) | Headroom |
|------|-------|----------------------|----------|
| Storage | 10 GB | 1.6 GB (16%) | 8.4 GB ✅ |
| Queries | 1 TB/month | 0.17 GB (0.017%) | 999+ GB ✅ |

---

## Upload Commands

### Option A: Use Existing Upload Scripts

```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14

# Upload Yahoo Finance data
python3 scripts/upload_yahoo_finance_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/yahoo_finance" \
  --dataset yahoo_finance_comprehensive

# Upload CFTC data
python3 scripts/upload_cftc_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/cftc" \
  --dataset raw_intelligence

# Upload FRED data
python3 scripts/upload_fred_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/fred" \
  --dataset raw_intelligence

# Upload Alpha Vantage data
python3 scripts/upload_alpha_vantage_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/alpha_vantage" \
  --dataset raw_intelligence

# Upload training tables
python3 scripts/upload_training_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/models_v4" \
  --dataset training

# Upload weather data
python3 scripts/upload_weather_data.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/noaa" \
  --dataset raw_intelligence
```

### Option B: Bulk Upload Script

Create a bulk upload script:

```python
#!/usr/bin/env python3
"""
Bulk upload from external drive to BigQuery
Skips raw JSON, uploads only Parquet files
"""

from google.cloud import bigquery
from pathlib import Path
import sys

PROJECT = "cbi-v14"
SOURCE_ROOT = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw")
SKIP_DIRS = ["databento_mes", "databento_zl"]  # Skip raw JSON

# Map source directories to BigQuery datasets
DATASET_MAP = {
    "yahoo_finance": "yahoo_finance_comprehensive",
    "yahoo_finance_comprehensive": "yahoo_finance_comprehensive",
    "cftc": "raw_intelligence",
    "alpha_vantage": "raw_intelligence",
    "fred": "raw_intelligence",
    "noaa": "raw_intelligence",
    "usda": "raw_intelligence",
    "eia": "raw_intelligence",
    "models_v4": "training",
    "market_data": "market_data",
    "forecasting_data_warehouse": "forecasting_data_warehouse",
    "signals": "features",
}

client = bigquery.Client(project=PROJECT)

for source_dir in SOURCE_ROOT.iterdir():
    if not source_dir.is_dir():
        continue
    
    dir_name = source_dir.name
    
    # Skip raw JSON directories
    if dir_name in SKIP_DIRS:
        print(f"⏭️  Skipping {dir_name} (raw JSON)")
        continue
    
    # Get target dataset
    if dir_name not in DATASET_MAP:
        print(f"⚠️  No mapping for {dir_name}, skipping")
        continue
    
    dataset_id = DATASET_MAP[dir_name]
    
    # Find all Parquet files
    parquet_files = list(source_dir.glob("**/*.parquet"))
    
    if not parquet_files:
        print(f"⏭️  No Parquet files in {dir_name}")
        continue
    
    print(f"\n📤 Uploading {dir_name} → {dataset_id}")
    print(f"   Files: {len(parquet_files)}")
    
    # Upload each file
    for file_path in parquet_files:
        table_name = file_path.stem  # filename without extension
        table_ref = f"{PROJECT}.{dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        
        try:
            with open(file_path, "rb") as f:
                job = client.load_table_from_file(f, table_ref, job_config=job_config)
                job.result()  # Wait for completion
            
            print(f"   ✅ {table_name}")
        except Exception as e:
            print(f"   ❌ {table_name}: {str(e)[:60]}")

print("\n✅ Upload complete!")
```

Save as `scripts/bulk_upload_from_external_drive.py` and run:

```bash
python3 scripts/bulk_upload_from_external_drive.py
```

---

## Verification After Upload

### Check BigQuery Storage

```bash
# List datasets
bq ls --project_id=cbi-v14

# Check storage size by dataset
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')
for dataset in client.list_datasets():
    query = f'''
    SELECT 
        SUM(size_bytes) / POW(1024, 3) as size_gb,
        COUNT(*) as tables
    FROM \`cbi-v14.{dataset.dataset_id}.__TABLES__\`
    '''
    result = list(client.query(query).result())[0]
    print(f'{dataset.dataset_id}: {result.size_gb:.2f} GB, {result.tables} tables')
"
```

### Check Table Counts

```bash
# Count tables per dataset
bq ls cbi-v14:yahoo_finance_comprehensive | wc -l
bq ls cbi-v14:raw_intelligence | wc -l
bq ls cbi-v14:training | wc -l
```

### Verify Data Integrity

```bash
# Check row counts
python3 scripts/verify_upload_integrity.py
```

---

## Dashboard Impact

### Query Costs (No Change)

Even with 2.3x more data (1.6 GB vs 0.7 GB):

| Usage | Data Scanned | Cost |
|-------|--------------|------|
| Low (2 hrs/day) | 0.069 GB/month | $0.00 |
| High (5 hrs/day) | 0.17 GB/month | $0.00 |
| Free tier | 1,000 GB/month | — |

**Why no increase?**
- Dashboard reads from views (small, optimized)
- Views scan 1-10 MB per query (not entire tables)
- Cache (10-30s) reduces query frequency
- Total scanned: 0.17 GB << 1 TB free tier

---

## Long-Term Cost Projection

### Month 1-3 (All Active Storage)

```
Storage: 1.6 GB × $0.020/GB = $0.032/month
Queries: $0.00 (under 1 TB free tier)
VM: $0.00 (free tier e2-micro)
─────────────────────────────────────
TOTAL: $0.03/month
```

### Month 4+ (After Long-Term Kicks In)

BigQuery automatically moves tables to long-term storage (50% cheaper) if:
- Table not modified in 90 days
- Reduces cost: $0.020 → $0.010/GB/month

Assuming 75% goes long-term:
```
Active: 0.4 GB × $0.020 = $0.008
Long-term: 1.2 GB × $0.010 = $0.012
─────────────────────────────────
TOTAL: $0.020/month (~$0.02)
```

### 5-Year Projection

```
Year 1: $0.03/month × 12 = $0.36
Year 2-5: $0.02/month × 12 × 4 = $0.96
────────────────────────────────────
5-year total: $1.32 (cost of a coffee)
```

---

## What NOT to Upload (Keep on External Drive)

### DataBento Raw JSON (1.2 GB)

```
databento_mes/    749 MB (2,000+ JSON files)
databento_zl/     470 MB (2,000+ JSON files)
```

**Why keep on external drive?**
1. **Backup/Audit**: Raw data for compliance/verification
2. **Inefficient**: JSON is 5-10x larger than Parquet
3. **Rarely used**: Not queried in dashboard or training
4. **Free storage**: External drive costs $0

**If you need this data later**:
- Process JSON → Parquet (scripts/process_databento.py)
- Upload processed Parquet (~100-200 MB vs 1.2 GB raw)
- Save 80-90% of storage cost

---

## Migration Checklist

### Pre-Upload

- [ ] Verify external drive accessible: `/Volumes/Satechi Hub/`
- [ ] Check BigQuery authentication: `gcloud auth list`
- [ ] Confirm project: `cbi-v14`
- [ ] Test upload with one small file

### Upload

- [ ] Upload Yahoo Finance data (304 MB)
- [ ] Upload CFTC data (172 MB)
- [ ] Upload Alpha Vantage data (30 MB)
- [ ] Upload models_v4 training tables (33 MB)
- [ ] Upload FRED, NOAA, USDA, EIA (~10 MB)
- [ ] Upload signals/features (3 MB)

### Post-Upload Verification

- [ ] Check BigQuery storage (should be ~1.6 GB)
- [ ] Verify table counts (30-50 tables added)
- [ ] Test dashboard queries (should still be fast)
- [ ] Check monthly cost estimate (should be $0.03-0.04)
- [ ] Verify data integrity (row counts, date ranges)

### Cleanup

- [ ] Keep raw JSON on external drive (backup)
- [ ] Delete temp files (if any)
- [ ] Update documentation
- [ ] Create backup of external drive

---

## Troubleshooting

### Upload Fails: "Table already exists"

```bash
# Add --replace flag or use WRITE_TRUNCATE
job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)
```

### Upload Fails: "Schema mismatch"

```bash
# Use autodetect
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    autodetect=True,
)
```

### Upload Slow

- Check network speed (external drive → Mac → BigQuery)
- Upload during off-peak hours
- Consider multiprocessing for large uploads

### Cost Higher Than Expected

- Check for duplicate tables (temp/test tables)
- Verify long-term storage kicking in (after 90 days)
- Use `bq ls --format=pretty` to see all tables

---

## Summary

### What You Have
- **2.1 GB** on external drive (4,946 files)
- **0.7 GB** currently in BigQuery

### What to Upload
- **~900 MB** of Parquet files (skip 1.2 GB raw JSON)

### What It Will Cost
- **$0.03/month** after upload (3 pennies)
- **$0.02/month** after long-term storage kicks in (month 4+)

### Dashboard Impact
- **$0.00** - queries stay under 1 TB free tier

### Bottom Line
Upload all your processed data. Cost is negligible. No concerns about exceeding limits.

---

**Next Step**: Run upload scripts or create bulk upload script above.

**Questions?** See `REAL_DATA_COST_ANALYSIS.md` for full details.

