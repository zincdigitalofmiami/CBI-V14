---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# REAL BigQuery Cost Analysis - External Drive Data
**Date**: November 18, 2025  
**Source**: Actual data on `/Volumes/Satechi Hub/Projects/CBI-V14`

---

## Executive Summary

**Current BigQuery**: 0.70 GB ($0.01/month)  
**External Drive Data**: **2.1 GB** (ready to upload)  
**Projected BigQuery Cost**: **$0.04/month**  
**Dashboard Query Cost**: **$0.00/month** (under 1 TB free tier)  
**Total Infrastructure**: **$0.04/month** (essentially free)

---

## Part 1: What's Actually on the External Drive

### Storage Breakdown

| Directory | Size | Description |
|-----------|------|-------------|
| **TrainingData/raw** | **1.8 GB** | All collected data sources |
| **GPT_Data** | **265 MB** | Schema exports and metadata |
| **Other** | ~100 MB | Scripts, docs, configs |
| **TOTAL** | **~2.1 GB** | Ready for BigQuery upload |

### TrainingData/raw Breakdown (Top Data Sources)

| Data Source | Size | Files | Description |
|-------------|------|-------|-------------|
| **databento_mes** | 749 MB | ~2,000 JSON | MES futures data |
| **databento_zl** | 470 MB | ~2,000 JSON | ZL futures data |
| **yahoo_finance** | 177 MB | Parquet | Historical Yahoo data |
| **cftc** | 172 MB | Parquet | CFTC positioning reports |
| **yahoo_finance_comprehensive** | 127 MB | Parquet | Comprehensive Yahoo dataset |
| **alpha_vantage** | 30 MB | Parquet | Alpha Vantage indicators |
| **models_v4** | 33 MB | Parquet | Training tables |
| **market_data** | 31 MB | Parquet | Market data |
| **forecasting_data_warehouse** | 15 MB | Parquet | Warehouse data |
| **models** | 9 MB | Parquet | Model artifacts |
| **fred** | 7.3 MB | Parquet | FRED economic data |
| **noaa** | 2.5 MB | Parquet | Weather data |
| **signals** | 2.8 MB | Parquet | Trading signals |
| **usda** | 532 KB | Parquet | USDA agricultural data |
| **eia** | 248 KB | Parquet | Energy data |
| **Other** | ~10 MB | Various | Misc data sources |

### File Statistics

| Metric | Count |
|--------|-------|
| **Total files** | 4,946 |
| **JSON files** | 4,299 (DataBento raw) |
| **Parquet files** | 622 (processed data) |
| **CSV files** | 25 (exports) |

---

## Part 2: BigQuery Storage Cost Projection

### Storage After Upload

| Component | Size |
|-----------|------|
| Current BigQuery data | 0.70 GB |
| External drive data | 2.10 GB |
| **TOTAL AFTER UPLOAD** | **2.80 GB** |

### Monthly Storage Cost Calculation

**BigQuery Storage Pricing** (November 2024):
- **Active storage**: $0.020/GB/month (first 90 days)
- **Long-term storage**: $0.010/GB/month (after 90 days, unused)

**Assuming 50/50 split** (conservative):
- Active: 1.4 GB × $0.020 = **$0.028**
- Long-term: 1.4 GB × $0.010 = **$0.014**
- **TOTAL: $0.042/month** (rounds to **$0.04**)

**Assuming 100% active** (worst case):
- Active: 2.8 GB × $0.020 = **$0.056/month**

**Assuming 75% long-term** (optimistic, after a few months):
- Active: 0.7 GB × $0.020 = $0.014
- Long-term: 2.1 GB × $0.010 = $0.021
- **TOTAL: $0.035/month**

**Realistic Range**: **$0.04 - $0.06/month**

---

## Part 3: BigQuery Free Tier Analysis

### Storage Free Tier: **10 GB**

| Scenario | Usage | % of Free Tier | Cost |
|----------|-------|----------------|------|
| Current (0.70 GB) | 0.70 GB | 7% | $0.01 |
| After upload (2.80 GB) | 2.80 GB | 28% | $0.04 |
| **Headroom** | **7.2 GB** | **72% free** | — |

**Analysis**: You're using less than 1/3 of the free 10 GB storage tier ✅

### Query Free Tier: **1 TB/month**

Dashboard usage (2-5 hrs/day):
- Data scanned: 0.17 GB/month
- Free tier: 1,000 GB/month
- **Usage: 0.017%** ✅
- **Cost: $0.00**

---

## Part 4: Data Upload Strategy

### Option A: Upload All Data (Recommended)

**What to upload**:
- ✅ All Parquet files (622 files, ~900 MB)
- ✅ Processed CFTC data (172 MB)
- ✅ Yahoo Finance (304 MB combined)
- ✅ Alpha Vantage (30 MB)
- ✅ FRED, NOAA, USDA, EIA (~10 MB)
- ❌ Raw DataBento JSON (1.2 GB) - keep on drive, already in Parquet

**Upload size**: ~900 MB  
**Total after upload**: 0.7 GB (current) + 0.9 GB (new) = **1.6 GB**  
**Monthly cost**: **$0.03/month**

### Option B: Upload Only Training Tables

**What to upload**:
- ✅ models_v4 (33 MB) - training tables
- ✅ yahoo_finance_comprehensive (127 MB)
- ✅ FRED, CFTC, Alpha Vantage (~210 MB)
- ❌ Raw DataBento JSON (keep on external drive)

**Upload size**: ~370 MB  
**Total after upload**: 0.7 GB + 0.37 GB = **1.07 GB**  
**Monthly cost**: **$0.02/month**

### Option C: Upload Only Latest/Essential

**What to upload**:
- ✅ Training tables (33 MB)
- ✅ Latest Yahoo Finance (50 MB)
- ✅ FRED (7 MB)
- ✅ Alpha Vantage (30 MB)

**Upload size**: ~120 MB  
**Total after upload**: 0.7 GB + 0.12 GB = **0.82 GB**  
**Monthly cost**: **$0.01/month** (no change)

---

## Part 5: DataBento Data Strategy

### Current DataBento Data on Drive

| Symbol | Size | Files | Description |
|--------|------|-------|-------------|
| databento_mes | 749 MB | ~2,000 | MES micro E-mini futures |
| databento_zl | 470 MB | ~2,000 | ZL soybean oil futures |
| **TOTAL** | **1.2 GB** | **~4,000** | Historical intraday data |

### Recommendation: DON'T Upload to BigQuery

**Why not upload DataBento JSON?**
1. **Size**: 1.2 GB of raw JSON adds significant cost
2. **Format**: JSON is inefficient (5-10x larger than Parquet)
3. **Usage**: Likely won't query directly (use processed Parquet instead)
4. **Alternative**: Keep on external drive as backup/audit trail

**Better approach**:
1. Keep raw JSON on external drive (backup/compliance)
2. Process to Parquet format (already done - see processed/)
3. Upload only processed Parquet (~100-200 MB vs 1.2 GB)
4. Save 80-90% of storage cost

**If you need intraday DataBento data**:
- Use live collection (scripts/live/databento_live_poller.py)
- Store on free-tier VM (~40 MB/month)
- Keep only last 30-90 days in BigQuery
- Archive older data to external drive

---

## Part 6: Updated Total Cost Breakdown

### Scenario A: Upload All Parquet Files (~900 MB)

| Component | Cost |
|-----------|------|
| BigQuery Storage (1.6 GB) | $0.03/month |
| BigQuery Queries | $0.00 (under 1 TB free) |
| GCP VM (e2-micro, us-central1) | $0.00 (free tier) |
| Persistent Disk (<30 GB) | $0.00 (free tier) |
| Network Egress | $0.00 (under 1 GB free) |
| **TOTAL GCP** | **$0.03/month** |

### Scenario B: Upload Only Training Data (~370 MB)

| Component | Cost |
|-----------|------|
| BigQuery Storage (1.07 GB) | $0.02/month |
| BigQuery Queries | $0.00 (under 1 TB free) |
| GCP VM (e2-micro) | $0.00 (free tier) |
| **TOTAL GCP** | **$0.02/month** |

### Scenario C: Minimal Upload (~120 MB)

| Component | Cost |
|-----------|------|
| BigQuery Storage (0.82 GB) | $0.01/month |
| BigQuery Queries | $0.00 (under 1 TB free) |
| GCP VM (e2-micro) | $0.00 (free tier) |
| **TOTAL GCP** | **$0.01/month** |

---

## Part 7: Recommendations

### ✅ Recommended Strategy (Scenario A)

**Upload**: All processed Parquet files (~900 MB)  
**Skip**: Raw DataBento JSON (1.2 GB)  
**Total Cost**: **$0.03/month**

**Why this is optimal**:
1. All data sources available in BigQuery for queries
2. Excludes inefficient raw JSON
3. Still well under free tier limits (1.6 GB vs 10 GB free)
4. Costs essentially zero ($0.03 = 3 pennies)
5. Can query all data sources for dashboard/training

### 📊 What to Upload

```bash
# Upload these directories to BigQuery:
TrainingData/raw/yahoo_finance_comprehensive/  → yahoo_finance_comprehensive dataset
TrainingData/raw/cftc/                        → raw_intelligence dataset
TrainingData/raw/yahoo_finance/               → yahoo_finance_comprehensive dataset  
TrainingData/raw/alpha_vantage/               → raw_intelligence dataset
TrainingData/raw/fred/                        → raw_intelligence dataset
TrainingData/raw/models_v4/                   → training dataset
TrainingData/raw/noaa/                        → raw_intelligence dataset
TrainingData/raw/usda/                        → raw_intelligence dataset
TrainingData/raw/eia/                         → raw_intelligence dataset
TrainingData/raw/forecasting_data_warehouse/  → forecasting_data_warehouse dataset
TrainingData/raw/signals/                     → features dataset

# SKIP (keep on external drive):
TrainingData/raw/databento_mes/               → 749 MB of raw JSON (inefficient)
TrainingData/raw/databento_zl/                → 470 MB of raw JSON (inefficient)
```

### 🚀 Upload Command

Use existing upload scripts:
```bash
# Upload Yahoo Finance
python3 scripts/upload_yahoo_finance_data.py

# Upload FRED
python3 scripts/upload_fred_data.py

# Upload CFTC
python3 scripts/upload_cftc_data.py

# Upload Alpha Vantage
python3 scripts/upload_alpha_vantage_data.py

# Upload training tables
python3 scripts/upload_training_data.py

# Or use bulk upload:
python3 scripts/bulk_upload_external_drive.py \
  --source "/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw" \
  --exclude "databento_*" \
  --target cbi-v14
```

---

## Part 8: Long-Term Storage Strategy

### After 90 Days (Automatic Long-Term Storage)

BigQuery automatically moves tables to long-term storage if:
- Table hasn't been modified in 90 days
- Reduces cost by 50% ($0.020 → $0.010/GB/month)

**Your cost after 90 days**:
- Active tables (updated regularly): 0.3 GB × $0.020 = $0.006
- Long-term (historical): 1.3 GB × $0.010 = $0.013
- **New total: $0.019/month** (~$0.02)

**5-year projection**:
- Year 1: $0.03/month × 12 = $0.36/year
- Year 2-5: $0.02/month × 12 = $0.24/year
- **5-year total: ~$1.32** (cost of a coffee)

---

## Part 9: Dashboard Query Cost (No Change)

### With 2.8 GB in BigQuery

Even with 3x more data, dashboard costs remain **$0.00** because:

1. **Queries read from views** (small, optimized)
2. **Views typically scan 1-10 MB per query** (not entire tables)
3. **Monthly scanned**: 0.17 GB (with cache)
4. **Free tier**: 1,000 GB/month
5. **Usage**: 0.017% of free tier ✅

**Projection**:
- Even with 10x traffic: 1.7 GB scanned/month = still FREE
- Even with 100x traffic: 17 GB scanned/month = still FREE

---

## Part 10: File Count & Table Structure

### Current File Distribution

| File Type | Count | Avg Size | Total Size |
|-----------|-------|----------|------------|
| JSON (DataBento raw) | 4,299 | 280 KB | 1.2 GB |
| Parquet (processed) | 622 | 1.5 MB | 900 MB |
| CSV (exports) | 25 | 40 KB | 1 MB |

### Projected BigQuery Tables

**After upload** (~30-40 tables):
- yahoo_finance_comprehensive: 5-10 tables
- raw_intelligence: 15-20 tables (fred, cftc, alpha, noaa, usda, eia)
- training: 5-10 tables (models_v4 tables)
- features: 3-5 tables (signals, regimes)
- predictions: 5-7 tables (existing)

**Total tables**: ~40-50 (vs 479 current - likely duplicates/temp tables)

---

## Conclusion

### Question: What do we have and what will it cost?

**Answer**:

1. **What we have on external drive**:
   - Total: **2.1 GB** (1.8 GB training data + 265 MB metadata)
   - Files: 4,946 (4,299 JSON + 622 Parquet + 25 CSV)
   - Key sources: DataBento (1.2 GB), Yahoo (304 MB), CFTC (172 MB), Alpha (30 MB)

2. **What to upload**:
   - Recommended: **~900 MB** (all Parquet, skip raw JSON)
   - Total in BigQuery: 0.7 GB (current) + 0.9 GB (new) = **1.6 GB**

3. **What it will cost**:
   - Storage: **$0.03/month** (1.6 GB)
   - Queries: **$0.00/month** (under 1 TB free tier)
   - VM: **$0.00/month** (free tier e2-micro)
   - **TOTAL: $0.03/month** (3 pennies)

4. **For Vercel dashboard (2-5 hrs/day)**:
   - No additional costs
   - Query volume stays under free tier
   - Dashboard reads from optimized views
   - **Still $0.00/month for queries**

### Bottom Line

Upload all your Parquet data to BigQuery (skip raw JSON) and you'll pay **$0.03/month** - essentially free.

Your infrastructure (BigQuery + Dashboard + Live Data VM) will cost **$0.03-0.04/month** total.

**No cost concerns. Upload everything you need.**

---

**Report Generated**: November 18, 2025  
**Data Source**: Actual external drive at `/Volumes/Satechi Hub/Projects/CBI-V14`  
**Next Step**: Run upload scripts to move Parquet files to BigQuery

