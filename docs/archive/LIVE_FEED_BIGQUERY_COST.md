---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Live Feed BigQuery Cost Analysis
**Date:** November 18, 2025  
**Question:** What does it cost to push all data live to BigQuery?

---

## 🎯 QUICK ANSWER

**Total Cost: $0.04-0.09/month** (4-9 pennies)

Even with **24/7 live data collection** (every 5-15 minutes, 11,520 pulls/month), your BigQuery costs are:

- **Data Ingestion:** $0.00 (FREE - batch loads or streaming under 2 TB)
- **Storage:** $0.04-0.09/month (grows slowly with smart updates)
- **Queries:** $0.00 (under 1 TB free tier)
- **TOTAL:** **$0.04-0.09/month**

---

## 📊 DETAILED BREAKDOWN

### 1. Data Ingestion Costs (Pushing Data to BigQuery)

**Option A: Batch Loads** ✅ **RECOMMENDED - FREE**
```python
# Load from Parquet/CSV files
bq load --source_format=PARQUET \
  cbi-v14:market_data.databento_futures_ohlcv_1m \
  /tmp/latest_data.parquet
```
- **Cost:** **FREE** (unlimited batch loads)
- **Best for:** Every 15-minute heavy pulls
- **Your usage:** ~6 GB/month → **$0.00**

**Option B: Streaming Inserts**
```python
# INSERT via API
client.insert_rows_json(table, rows)
```
- **Free tier:** First 2 TB/month FREE
- **Your usage:** ~6 GB/month → **$0.00**
- **After 2 TB:** $0.05 per 200 MB (you won't hit this)

**Option C: DML (MERGE/UPDATE)**
```sql
MERGE INTO table AS target
USING new_data AS source
ON target.symbol = source.symbol AND target.date = source.date
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```
- **Cost:** Counts as query (scans data)
- **Your usage:** ~100-200 GB/month scanned
- **Free tier:** 1 TB/month → **$0.00**

**VERDICT:** All three methods are **FREE** for your usage volume.

---

### 2. Storage Costs (Storing Data in BigQuery)

**Critical:** Use **MERGE/UPSERT** (not append-only) to prevent storage explosion.

**Smart Updates (MERGE/UPSERT):** ✅ **RECOMMENDED**
- **Growth:** 225 MB/month (only new unique dates)
- **Month 1:** 1.8 GB → **$0.04/month**
- **Month 6:** 3.0 GB → **$0.06/month**
- **Month 12:** 4.3 GB → **$0.09/month**
- **Still under 10 GB free tier** ✅

**Bad Approach (Append-Only):** ❌ **DON'T DO THIS**
- **Growth:** 6 GB/month (duplicates every pull)
- **Month 2:** 13.6 GB → **$0.27/month**
- **Month 12:** 73.6 GB → **$1.47/month**
- **Exceeds free tier quickly**

**Storage Pricing:**
- Active storage: $0.020/GB/month
- Long-term storage (90+ days): $0.010/GB/month (50% cheaper)
- Free tier: 10 GB (you'll use 1.8-4.3 GB)

**With Partitioning + Auto-Expiration:**
- After 6 months: **$0.04-0.05/month** (flat cost)
- Old partitions auto-delete after 365 days
- Long-term pricing kicks in for 90+ day partitions

---

### 3. Query Costs (Reading Data from BigQuery)

**Collection Queries** (if querying before updating):
- **Volume:** ~23 GB/month scanned
- **Free tier:** 1 TB/month
- **Cost:** **$0.00** (2.3% of free tier)

**Dashboard Queries** (user-facing):
- **Volume:** ~0.17 GB/month scanned
- **Free tier:** 1 TB/month
- **Cost:** **$0.00** (0.017% of free tier)

**Total Query Cost:** **$0.00** ✅

---

## 💰 TOTAL MONTHLY COST BREAKDOWN

### Scenario: 24/7 Live Data Collection (Every 5-15 Minutes)

| Component | Volume | Cost |
|-----------|--------|------|
| **Data Ingestion** | 6 GB/month | **$0.00** (FREE batch loads) |
| **Storage** (Month 1) | 1.8 GB | **$0.04** |
| **Storage** (Month 12) | 4.3 GB | **$0.09** |
| **Collection Queries** | 23 GB/month | **$0.00** (under 1 TB) |
| **Dashboard Queries** | 0.17 GB/month | **$0.00** (under 1 TB) |
| **TOTAL (Month 1)** | — | **$0.04/month** |
| **TOTAL (Month 12)** | — | **$0.09/month** |

### With Optimizations (Partitioning + Auto-Expiration)

| Month | Storage Cost | Notes |
|-------|--------------|-------|
| 1-5 | $0.04 | Active storage only |
| 6+ | $0.04-0.05 | Long-term pricing kicks in |
| 12+ | $0.05 | Flat cost with auto-expiration |

**Best Case:** **$0.05/month** (flat, long-term)

---

## 📈 DATA VOLUME PROJECTIONS

### Live Data Collection Pattern

**Heavy Pulls (Every 15 Minutes):**
- 96 pulls/day × 30 = 2,880 pulls/month
- Data per pull: ~2-5 MB
- Total: ~6 GB/month (new data written)

**Light Pulls (Every 5 Minutes):**
- 288 pulls/day × 30 = 8,640 pulls/month
- Data per pull: ~50-100 KB
- Total: ~0.5 GB/month

**Total Pulls:** 11,520/month  
**Total Data Written:** ~6.5 GB/month

**But with MERGE/UPSERT:**
- Only new unique dates stored
- Storage growth: **225 MB/month** (not 6.5 GB)

---

## 🎯 KEY FINDINGS

### ✅ What's FREE

1. **Data Ingestion:** Batch loads are FREE (unlimited)
2. **Streaming Inserts:** FREE (under 2 TB/month)
3. **Queries:** FREE (under 1 TB/month)
4. **Network Egress:** FREE (under 1 GB/month)

### 💰 What Costs Money

1. **Storage:** $0.020/GB/month (active) or $0.010/GB/month (long-term)
2. **Your usage:** 1.8-4.3 GB → **$0.04-0.09/month**

### ⚠️ Critical: Use MERGE/UPSERT

**Bad Approach (Append-Only):**
```sql
-- DON'T DO THIS - Creates duplicates
INSERT INTO table VALUES (...);
```
- Storage: 6 GB/month growth
- Cost: $1.47/month (Year 1)

**Good Approach (MERGE/UPSERT):**
```sql
-- DO THIS - Updates existing rows
MERGE INTO table AS target
USING new_data AS source
ON target.symbol = source.symbol AND target.date = source.date
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;
```
- Storage: 225 MB/month growth
- Cost: $0.09/month (Year 1)
- **Savings: 94%** ($1.47 → $0.09)

---

## 🚀 RECOMMENDED ARCHITECTURE

### Data Collection Script Pattern

```python
#!/usr/bin/env python3
"""
Live data collection (runs every 15 minutes)
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

def collect_and_upload():
    # 1. Collect data from DataBento API
    databento_data = fetch_databento_live()  # External API call
    
    # 2. Save to local Parquet (temporary)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    databento_data.to_parquet(f"/tmp/databento_{timestamp}.parquet")
    
    # 3. Load to BigQuery (FREE batch load)
    client = bigquery.Client(project='cbi-v14')
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    with open(f"/tmp/databento_{timestamp}.parquet", "rb") as f:
        job = client.load_table_from_file(
            f, 
            "cbi-v14.market_data.databento_futures_ohlcv_1m",
            job_config=job_config
        )
        job.result()  # Wait for completion
    
    # 4. Deduplicate (daily job, not every pull)
    # Run this once per day, not every 15 minutes
    deduplicate_table()
    
    # 5. Cleanup temp file
    os.remove(f"/tmp/databento_{timestamp}.parquet")

# Run via cron every 15 minutes
# */15 * * * * python3 /path/to/collect_and_upload.py
```

**Cost:** $0.00 (batch loads are free)

---

### Daily Deduplication Job

```sql
-- Run once per day at 2 AM
-- Deduplicate and compact data
CREATE OR REPLACE TABLE market_data.databento_futures_ohlcv_1m_clean AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *, 
    ROW_NUMBER() OVER (
      PARTITION BY symbol, date, timestamp 
      ORDER BY collection_timestamp DESC
    ) as row_num
  FROM market_data.databento_futures_ohlcv_1m
)
WHERE row_num = 1;
```

**Cost:** $0.00 (counts as query, under 1 TB free tier)

---

## 📊 COST COMPARISON

### Your Usage vs. Free Tier Limits

| Resource | Free Tier | Your Usage | % Used | Cost |
|----------|-----------|------------|--------|------|
| **Storage** | 10 GB | 1.8-4.3 GB | 18-43% | $0.04-0.09 |
| **Queries** | 1 TB/month | 23 GB/month | 2.3% | $0.00 |
| **Streaming** | 2 TB/month | 6 GB/month | 0.3% | $0.00 |
| **Network** | 1 GB/month | <0.1 GB/month | <10% | $0.00 |

**Verdict:** You're using **<50% of free tier** for storage, **<3% for queries**. Costs are minimal.

---

## ✅ SUMMARY

### To Push All Data Live to BigQuery:

**Cost Breakdown:**
- **Data Ingestion:** $0.00 (FREE - batch loads)
- **Storage:** $0.04-0.09/month (1.8-4.3 GB)
- **Queries:** $0.00 (under 1 TB free tier)
- **TOTAL:** **$0.04-0.09/month** (4-9 pennies)

**Key Requirements:**
1. ✅ Use batch loads (FREE) or streaming (under 2 TB)
2. ✅ Use MERGE/UPSERT (not append-only) to prevent storage explosion
3. ✅ Set up partitioning with auto-expiration (365 days)
4. ✅ Run daily deduplication job

**Bottom Line:**
Even with **11,520 data pulls per month** (24/7 collection every 5-15 minutes), your BigQuery costs are **$0.04-0.09/month** - essentially free.

**No cost concerns. Push all the data you need.**

---

**Reference Documents:**
- `COST_WITH_DATA_COLLECTION.md` - Full 24/7 collection analysis
- `BIGQUERY_COST_ANALYSIS_REPORT.md` - Current state analysis
- `COST_SUMMARY_QUICK_REFERENCE.md` - Quick reference





