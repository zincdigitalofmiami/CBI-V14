# Quick Cost Summary - CBI-V14 Infrastructure

**Last Updated**: November 18, 2025  
**Source**: Real external drive data analysis

---

## The Bottom Line

### External Drive Data: **2.1 GB** (ready to upload)
### 24/7 Data Collection: **11,520 pulls/month** (every 5-15 min)
### Month 1 Cost: **$0.04/month**
### Month 12 Cost: **$0.09/month**
### With Optimizations: **$0.05/month** (flat, long-term)
### Total GCP Cost: **$0.04-0.09/month** 🎉

Yes, you read that right. **Four to nine pennies per month** - even with 24/7 automated data collection.

---

## What We Have (Real Data)

### Currently in BigQuery
```
BigQuery Storage: 0.70 GB
Tables: 479
Rows: 2.5 million
Monthly Cost: $0.01
```

### On External Drive (Ready to Upload)
```
TrainingData/raw: 1.8 GB (4,946 files)
  - DataBento (MES+ZL): 1.2 GB (historical JSON)
    → Keep on drive (backup/audit trail)
    → Use live DataBento API going forward
  - CFTC: 172 MB (Parquet - upload to BQ)
  - FRED: 7 MB (Parquet - upload to BQ)
  - Alpha Vantage: 30 MB (Parquet - upload to BQ)
  - NOAA, USDA, EIA: ~10 MB (upload to BQ)
  
GPT_Data: 265 MB (metadata)

Recommended Upload: ~220 MB (domain data only, NOT DataBento historical)
DataBento Strategy: Use live API (14 MB/month new data)
Total After Upload: 0.9 GB (Month 1) → 1.1 GB (Month 12)
Projected Cost: $0.02-0.03/month
```

---

## Vercel Dashboard (2-5 hrs/day)

### Query Volume
- **Low** (2 hrs/day): 7,200 requests/month → 0.069 GB scanned
- **High** (5 hrs/day): 18,000 requests/month → 0.17 GB scanned

### BigQuery Free Tier
- **1 TB/month FREE** (1000 GB)
- **Your usage: 0.17 GB** (0.017% of free tier)

### Result
**Query Cost: $0.00/month** ✅

---

## 24/7 Data Collection (NEW - Critical)

### Collection Pattern
- **Heavy pulls** (every 15 min): 96/day × 30 = 2,880/month
- **Light pulls** (every 5 min): 288/day × 30 = 8,640/month
- **Total pulls**: 11,520/month
- **Data volume**: ~6 GB/month (new data written)

### BigQuery Ingestion Costs

**Option A: Batch Loads** (Recommended)
- Load from Parquet/CSV files
- **Cost: FREE** (unlimited) ✅

**Option B: Streaming Inserts**
- INSERT via API
- Free tier: 2 TB/month
- Your usage: 6 GB/month
- **Cost: $0.00** (under free tier) ✅

### Storage Growth (With Smart Updates)

Using MERGE/UPSERT (update existing rows, not append):
- **Growth**: 225 MB/month (only new dates)
- **Month 1**: 1.8 GB → $0.04/month
- **Month 6**: 3.0 GB → $0.06/month
- **Month 12**: 4.3 GB → $0.09/month
- Still under 10 GB free tier ✅

### Collection Query Costs

If querying BigQuery before updating:
- **Volume**: ~23 GB/month scanned
- **Free tier**: 1 TB/month
- **Cost: $0.00** (2.3% of free tier) ✅

### Total With Data Collection
- **Ingestion**: $0.00 (batch loads FREE)
- **Storage** (Month 1): $0.04
- **Storage** (Month 12): $0.09
- **Queries**: $0.00 (under 1 TB)
- **TOTAL**: **$0.04-0.09/month** ✅

---

## Live Data (DataBento) - Optional

If you want live futures data:

### What You Need
- 1 e2-micro VM (us-central1, Iowa)
- ~40 MB/month storage (1-min bars, 10 symbols)
- <100 MB/month network egress

### GCP Free Tier
- ✅ 1 e2-micro: FREE (730 hrs/month)
- ✅ 30 GB disk: FREE
- ✅ 1 GB egress: FREE

### Result
**Live Data Cost: $0.00/month** ✅

---

## Total Costs

### After Uploading External Drive Data + 24/7 Data Collection

| Component | Current | Month 1 | Month 6 | Month 12 |
|-----------|---------|---------|---------|----------|
| **BigQuery Storage** | $0.01 (0.7 GB) | **$0.04** (1.8 GB) | **$0.06** (3.0 GB) | **$0.09** (4.3 GB) |
| **Data Ingestion** | $0.00 | $0.00 (FREE) | $0.00 (FREE) | $0.00 (FREE) |
| **BigQuery Queries** | $0.00 | $0.00 (23 GB) | $0.00 (23 GB) | $0.00 (23 GB) |
| **GCP VM (e2-micro)** | $0.00 | $0.00 | $0.00 | $0.00 |
| **Persistent Disk** | $0.00 | $0.00 | $0.00 | $0.00 |
| **Network** | $0.00 | $0.00 | $0.00 | $0.00 |
| **TOTAL** | **$0.01** | **$0.04** | **$0.06** | **$0.09** |

**Note**: Storage grows ~225 MB/month with smart MERGE/UPSERT updates (not append-only).

### With Optimizations (Partitioning + Auto-Expiration)

| Month | Storage Cost | Notes |
|-------|--------------|-------|
| 6+ | **$0.04-0.05** | Long-term storage pricing kicks in |
| 12+ | **$0.05** | Flat cost with auto-expiration |

### Separate Vendors (Not GCP)
- DataBento API: $75/month (if using live data)
- Alpha Vantage: $75/month (Plan75 for data collection)
- Vercel Pro: $0-20/month (optional)

---

## What Tables Exist for Dashboard

### Prediction Views (Use These)
```
predictions.zl_predictions_prod_allhistory_1w  (VIEW)
predictions.zl_predictions_prod_allhistory_1m  (TABLE)
predictions.zl_predictions_prod_allhistory_3m  (VIEW)
predictions.zl_predictions_prod_allhistory_6m  (VIEW)
predictions.zl_predictions_prod_allhistory_12m (VIEW)
predictions.zl_predictions_prod_all_latest     (TABLE)
```

### Data Sources
```
yahoo_finance_comprehensive.all_symbols_20yr
yahoo_finance_comprehensive.yahoo_finance_complete_enterprise
raw_intelligence.commodity_crude_oil_prices
raw_intelligence.commodity_palm_oil_prices
features.market_regimes
features.regime_calendar
```

---

## Architecture Recommendation

### For Dashboard Only (No Live Data)
```
Current Setup ✅
- Dashboard reads from BigQuery prediction views
- 10-30s cache on Vercel endpoints
- Cost: $0.01/month
```

### For Dashboard + Live Data
```
Recommended Setup:
1. e2-micro VM in us-central1 (FREE)
2. Python collector: scripts/live/databento_live_poller.py
3. Store Parquet locally on VM (~40 MB/month)
4. Optional: Hourly cron for continuous contracts
5. Dashboard reads from BigQuery (or DataBento API directly)
Cost: $0.01/month (GCP)
```

---

## How to Stay Free

### ✅ Do This
1. Use e2-micro in **us-central1** (Iowa) or us-west1 (Oregon)
2. Keep only 1 VM running
3. Use non-preemptible instance
4. Keep disk under 30 GB (you're using 1 GB)
5. Keep network egress under 1 GB (you're using 0.1 GB)
6. Cache dashboard queries (10-30s)

### ❌ Avoid This
- Running VM in non-free-tier regions (asia, europe)
- Running multiple VMs
- Using preemptible instances (not eligible for free tier)
- Streaming inserts to BigQuery (unnecessary)
- Heavy aggregation queries (keep queries simple)

---

## Next Steps

### Option A: Dashboard Only (Existing Data)
```bash
# No changes needed - current setup works
# Cost: $0.01/month
```

### Option B: Add Live Data Collection
```bash
# 1. Spin up VM in us-central1
gcloud compute instances create cbi-live-collector \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud

# 2. Install Python + DataBento
sudo apt update && sudo apt install -y python3-pip
pip3 install databento pandas pyarrow

# 3. Run collector
python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL

# 4. Set up cron for continuous contracts
crontab -e
# Add: 0 * * * * python3 /path/to/scripts/ingest/build_forward_continuous.py
```

---

## ⚠️ CRITICAL: Data Collection Strategy

### Use MERGE/UPSERT - NOT Append-Only!

**Bad Approach** (Append-Only): ❌
```sql
-- DON'T DO THIS - Creates duplicates
INSERT INTO table VALUES (...);
```
- Storage growth: **6 GB/month** (11,520 duplicate rows/month)
- Exceeds 10 GB free tier in Month 2
- Cost: $0.27/month (Month 2), $1.47/month (Year 1)

**Good Approach** (MERGE/UPSERT): ✅
```sql
-- DO THIS - Updates existing rows
MERGE INTO table AS target
USING new_data AS source
ON target.symbol = source.symbol AND target.date = source.date
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```
- Storage growth: **225 MB/month** (only new unique dates)
- Stays under 10 GB free tier for 2+ years
- Cost: $0.04-0.09/month

**Savings**: 96% reduction in storage costs ($1.47 → $0.09/month)

---

## FAQs

**Q: Is this really $0.04-0.09/month?**  
A: Yes. Real data with 24/7 collection (11,520 pulls/month). Storage grows slowly with MERGE/UPSERT.

**Q: Should I upload all the data?**  
A: Yes - upload all Parquet files (~900 MB). Skip raw DataBento JSON (1.2 GB) - keep on external drive.

**Q: What about the 1.2 GB of DataBento JSON?**  
A: Keep on external drive as backup. It's raw/inefficient format. Use processed Parquet instead.

**Q: What if I exceed the free tier?**  
A: Very unlikely. After upload you'll use 16% of storage free tier (1.6 GB / 10 GB) and 0.017% of query free tier.

**Q: What if I need live data?**  
A: Use e2-micro in us-central1 = still $0.00 (free tier).

**Q: What if I run the VM outside free-tier regions?**  
A: Cost goes to $6.12/month (e2-micro in paid region).

**Q: Can I avoid BigQuery entirely?**  
A: Yes, but you'd need to serve predictions another way (S3, Cloud Storage, etc.). Current setup is already nearly free.

**Q: What about DataBento costs?**  
A: DataBento is separate vendor ($75/month for Plan75). GCP costs are independent.

---

## Data Upload Strategy

### Recommended Upload (Scenario A: ~900 MB)

```bash
# Upload these to BigQuery:
✅ Yahoo Finance: 304 MB → yahoo_finance_comprehensive
✅ CFTC: 172 MB → raw_intelligence  
✅ Alpha Vantage: 30 MB → raw_intelligence
✅ FRED: 7 MB → raw_intelligence
✅ NOAA, USDA, EIA: ~10 MB → raw_intelligence
✅ Training tables: 33 MB → training
✅ Signals: 3 MB → features

❌ DataBento JSON: 1.2 GB → Keep on external drive (backup only)

Total upload: ~900 MB
BigQuery after: 1.6 GB
Cost: $0.03/month
```

### Upload Commands

```bash
# Use existing scripts
cd /Users/kirkmusick/Documents/GitHub/CBI-V14

python3 scripts/upload_yahoo_finance_data.py
python3 scripts/upload_fred_data.py
python3 scripts/upload_cftc_data.py
python3 scripts/upload_alpha_vantage_data.py
python3 scripts/upload_training_data.py

# Or bulk upload (if script exists)
python3 scripts/bulk_upload_external_drive.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw" \
  --exclude "databento_*" \
  --project cbi-v14
```

---

## Monitoring Commands

### Check BigQuery Usage
```bash
# Storage by dataset
bq ls --project_id=cbi-v14 --format=pretty

# Check storage size
python3 scripts/check_bq_storage.py

# Query costs (via GCP Console)
# Console > BigQuery > More > Query History > View Usage
```

### Check External Drive Data
```bash
# See what's ready to upload
du -sh "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw"/*

# Count files
find "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw" -type f | wc -l
```

### Check VM Usage
```bash
# If you create a VM
gcloud compute instances list
gcloud compute disks list
```

---

**tl;dr**: You have **2.1 GB** on external drive. Upload **~900 MB** (Parquet only, skip JSON) to BigQuery. With **24/7 data collection** (every 5-15 min, 11,520 pulls/month), cost will be **$0.04-0.09/month** (4-9 pennies). Data ingestion is **FREE** (batch loads). Queries stay free (under 1 TB). No cost concerns - run everything you need.

**Key**: Use MERGE/UPSERT (not append-only) to keep storage growth at 225 MB/month instead of 6 GB/month.


