---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Cost Analysis - With Automated Data Collection
**Date**: November 18, 2025  
**Scenario**: 24/7 automated data pulls every 5-15 minutes

---

## Data Collection Pattern

### Heavy Pulls (Every 15 Minutes)
- **Frequency**: 4 pulls/hour × 24 hours = **96 pulls/day**
- **Monthly**: 96 × 30 = **2,880 pulls/month**
- **Sources**: Yahoo Finance, FRED, CFTC, Alpha Vantage, NOAA, USDA, EIA
- **Data per pull**: ~2-5 MB (multiple sources combined)

### Light Pulls (Every 5 Minutes)
- **Frequency**: 12 pulls/hour × 24 hours = **288 pulls/day**
- **Monthly**: 288 × 30 = **8,640 pulls/month**
- **Sources**: Pricing updates only (Yahoo, Alpha Vantage)
- **Data per pull**: ~50-100 KB (just prices)

### Total Pull Volume
- **Daily pulls**: 384 pulls
- **Monthly pulls**: 11,520 pulls
- **Daily data**: ~200-300 MB
- **Monthly data**: ~6-9 GB

---

## BigQuery Cost Implications

### 1. Storage Growth

**Important**: Data collection doesn't multiply storage by number of pulls if you're updating existing rows.

**Smart Updates** (MERGE/UPSERT - Recommended):
```sql
-- Updates existing rows, inserts only new dates
MERGE INTO yahoo_finance_comprehensive.prices AS target
USING new_data AS source
ON target.symbol = source.symbol AND target.date = source.date
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...
```

**Storage Growth** (with smart updates):
- **New data per day**: ~5-10 MB (only new dates, updated prices)
- **Monthly growth**: 30 days × 7.5 MB = **225 MB/month**
- **Yearly growth**: 12 months × 225 MB = **2.7 GB/year**

**Storage Projection**:
| Month | Total Storage | Monthly Cost |
|-------|---------------|--------------|
| **Month 0** (initial upload) | 1.6 GB | $0.03 |
| **Month 1** | 1.8 GB | $0.04 |
| **Month 3** | 2.3 GB | $0.05 |
| **Month 6** | 3.0 GB | $0.06 |
| **Month 12** | 4.3 GB | $0.09 |
| **Month 24** | 7.0 GB | $0.14 |

**Still under 10 GB free tier for 2 years** ✅

**Bad Approach** (append-only, no deduplication):
- Would grow by 6-9 GB/month
- Would exceed 10 GB free tier in Month 2
- **Don't do this** - use MERGE/UPSERT instead

---

### 2. Data Ingestion Costs

BigQuery has THREE ways to load data:

#### Option A: Batch Loads (FREE) ✅ Recommended

**Method**: Load from files (Parquet, CSV, JSON)
```bash
# Load Yahoo data from file
bq load --source_format=PARQUET \
  cbi-v14:yahoo_finance_comprehensive.prices \
  /tmp/yahoo_latest.parquet
```

**Cost**: **FREE** (unlimited batch loads)
**Best for**: Every 15-minute heavy pulls

#### Option B: Streaming Inserts

**Method**: INSERT statements via API
```python
client.insert_rows_json(table, rows)
```

**Pricing**:
- First **2 TB/month**: FREE
- After 2 TB: $0.05 per 200 MB

**Your usage**: ~6 GB/month = **$0.00** (well under 2 TB)

#### Option C: DML Statements (UPDATE/MERGE)

**Method**: SQL UPDATE/MERGE statements
```sql
MERGE INTO table ...
```

**Cost**: Scans data, counts as query
- Your usage: ~100-200 GB/month scanned
- Free tier: 1 TB/month
- **Cost: $0.00** ✅

---

### 3. Query Costs

#### Data Collection Queries

If you're reading from BigQuery to decide what to update:

**Monthly query volume**:
- Heavy pulls: 2,880 × 5 MB = 14.4 GB
- Light pulls: 8,640 × 1 MB = 8.6 GB
- **Total**: ~23 GB/month scanned

**Cost**: $0.00 (under 1 TB free tier) ✅

#### Dashboard Queries (User-Facing)

- **Usage**: 0.17 GB/month (2-5 hrs/day)
- **Cost**: $0.00 ✅

#### Total Query Cost
- Data collection: 23 GB/month
- Dashboard: 0.17 GB/month
- **Total**: ~23 GB/month
- **Free tier**: 1,000 GB/month
- **Cost**: **$0.00** ✅

---

## Total Monthly Cost Breakdown

### Scenario A: Batch Loads (Recommended)

| Component | Volume | Cost |
|-----------|--------|------|
| **Storage** (Month 1) | 1.8 GB | $0.04 |
| **Storage** (Month 6) | 3.0 GB | $0.06 |
| **Storage** (Month 12) | 4.3 GB | $0.09 |
| **Batch Loads** | 6 GB/month | $0.00 (FREE) |
| **Queries** | 23 GB/month | $0.00 (under 1 TB) |
| **Streaming** | 0 GB | $0.00 |
| **TOTAL (Month 1)** | — | **$0.04** |
| **TOTAL (Month 6)** | — | **$0.06** |
| **TOTAL (Month 12)** | — | **$0.09** |

### Scenario B: Streaming Inserts

| Component | Volume | Cost |
|-----------|--------|------|
| **Storage** (Month 1) | 1.8 GB | $0.04 |
| **Storage** (Month 12) | 4.3 GB | $0.09 |
| **Streaming Inserts** | 6 GB/month | $0.00 (under 2 TB) |
| **Queries** | 23 GB/month | $0.00 (under 1 TB) |
| **TOTAL (Month 1)** | — | **$0.04** |
| **TOTAL (Month 12)** | — | **$0.09** |

---

## Data Collection Architecture

### Recommended: Batch Load Pattern

```python
#!/usr/bin/env python3
"""
Data collection script (runs every 15 minutes)
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime

def collect_and_upload():
    # 1. Collect data from external APIs
    yahoo_data = fetch_yahoo_finance()  # External API call
    fred_data = fetch_fred()
    alpha_data = fetch_alpha_vantage()
    
    # 2. Save to local Parquet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    yahoo_data.to_parquet(f"/tmp/yahoo_{timestamp}.parquet")
    
    # 3. Load to BigQuery (FREE batch load)
    client = bigquery.Client(project='cbi-v14')
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # Or WRITE_TRUNCATE
    )
    
    with open(f"/tmp/yahoo_{timestamp}.parquet", "rb") as f:
        job = client.load_table_from_file(
            f, 
            "cbi-v14.yahoo_finance_comprehensive.prices",
            job_config=job_config
        )
        job.result()  # Wait for completion
    
    # 4. Cleanup temp file
    os.remove(f"/tmp/yahoo_{timestamp}.parquet")

# Run via cron every 15 minutes
# */15 * * * * python3 /path/to/collect_and_upload.py
```

**Cost**: $0.00 (batch loads are free)

### Alternative: Streaming Insert Pattern

```python
def collect_and_stream():
    # 1. Collect data
    yahoo_data = fetch_yahoo_finance()
    
    # 2. Convert to JSON rows
    rows = yahoo_data.to_dict('records')
    
    # 3. Stream to BigQuery
    client = bigquery.Client(project='cbi-v14')
    errors = client.insert_rows_json(
        "cbi-v14.yahoo_finance_comprehensive.prices",
        rows
    )
    
    if errors:
        print(f"Errors: {errors}")
```

**Cost**: $0.00 (under 2 TB/month free tier)

---

## Storage Management Strategy

### After 90 Days: Long-Term Storage (50% Cheaper)

BigQuery automatically moves tables to long-term storage if:
- Table partition not modified in 90 days
- Cost drops from $0.020 → $0.010/GB/month

**With Partitioning** (Recommended):
```sql
CREATE TABLE yahoo_finance_comprehensive.prices_partitioned (
  symbol STRING,
  date DATE,
  close FLOAT64,
  ...
)
PARTITION BY date
OPTIONS (
  partition_expiration_days=365  -- Auto-delete partitions older than 1 year
);
```

**Benefits**:
- Old partitions (90+ days) = long-term pricing ($0.010/GB)
- Auto-expiration prevents unlimited growth
- Queries scan only relevant partitions

**Storage Cost with Partitioning** (after 1 year):
- Active partitions (0-90 days): 0.7 GB × $0.020 = $0.014
- Long-term (90+ days): 3.6 GB × $0.010 = $0.036
- **Total: $0.05/month** (vs $0.09 without partitioning)

---

## Network Costs (Data Collection)

### Data Downloaded from External APIs

**Not a BigQuery cost** - these are separate vendor charges:
- Yahoo Finance: FREE API
- FRED: FREE API
- Alpha Vantage: $75/month (Plan75)
- NOAA: FREE API
- USDA: FREE API
- EIA: FREE API

**Network Egress from BigQuery**: Minimal
- Dashboard queries return small result sets (<1 MB)
- Well under free tier

---

## Optimization Recommendations

### 1. Use Batch Loads (Not Streaming)

**Why**: Batch loads are FREE, streaming has limits
```python
# Good: FREE batch load
bq load --source_format=PARQUET table.json data.parquet

# Also Good: FREE (under 2 TB)
client.insert_rows_json(table, rows)
```

### 2. Implement Deduplication

**Why**: Prevents storage explosion
```sql
-- Daily deduplication job
CREATE OR REPLACE TABLE yahoo_finance_comprehensive.prices AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY symbol, date ORDER BY updated_at DESC) as row_num
  FROM yahoo_finance_comprehensive.prices
)
WHERE row_num = 1;
```

### 3. Use Partitioning

**Why**: Reduces query costs and enables long-term storage pricing
```sql
PARTITION BY DATE(timestamp)
OPTIONS (partition_expiration_days=365)
```

### 4. Set Up Scheduled Queries (FREE)

**Why**: Automated cleanup/aggregation at no cost
```sql
-- Scheduled daily at 2 AM
-- Deduplicate and compact data
CREATE OR REPLACE TABLE dataset.table_clean AS
SELECT * FROM dataset.table_raw
QUALIFY ROW_NUMBER() OVER (PARTITION BY id, date ORDER BY timestamp DESC) = 1;
```

### 5. Archive Old Data to Cloud Storage

**Why**: Cloud Storage is cheaper for rarely-accessed data
- BigQuery: $0.020/GB/month (active) or $0.010/GB/month (long-term)
- Cloud Storage: $0.004/GB/month (Nearline) or $0.0012/GB/month (Coldline)

```bash
# Export data older than 1 year to Cloud Storage
bq extract --destination_format=PARQUET \
  'cbi-v14:yahoo_finance_comprehensive.prices$20230101' \
  gs://cbi-v14-archive/yahoo/2023/*.parquet
```

---

## Cost Projections (3 Scenarios)

### Scenario 1: No Optimization (Append-Only)

**Storage growth**: 6 GB/month
| Month | Storage | Cost |
|-------|---------|------|
| 1 | 7.6 GB | $0.15 |
| 2 | 13.6 GB | $0.27 |
| 3 | 19.6 GB | $0.39 |
| 6 | 37.6 GB | $0.75 |
| 12 | 73.6 GB | $1.47 |

**NOT RECOMMENDED** ❌

### Scenario 2: Smart Updates (MERGE/Dedup)

**Storage growth**: 225 MB/month
| Month | Storage | Cost |
|-------|---------|------|
| 1 | 1.8 GB | $0.04 |
| 3 | 2.3 GB | $0.05 |
| 6 | 3.0 GB | $0.06 |
| 12 | 4.3 GB | $0.09 |
| 24 | 7.0 GB | $0.14 |

**RECOMMENDED** ✅

### Scenario 3: Partitioning + Long-Term Storage + Expiration

**Storage growth**: 225 MB/month, but with optimizations
| Month | Active | Long-term | Total Cost |
|-------|--------|-----------|------------|
| 1 | 1.8 GB | 0 GB | $0.04 |
| 6 | 0.7 GB | 2.3 GB | $0.04 |
| 12 | 0.7 GB | 3.6 GB | $0.05 |
| 24 | 0.7 GB | 3.6 GB | $0.05 |

**BEST** ⭐

---

## Summary

### With 24/7 Data Collection (Every 5-15 Minutes)

| Component | Volume | Cost |
|-----------|--------|------|
| **Data ingestion** | 6 GB/month | $0.00 (FREE batch loads) |
| **Storage** (smart updates) | 1.8-4.3 GB (grows slowly) | $0.04-0.09/month |
| **Collection queries** | 23 GB/month | $0.00 (under 1 TB) |
| **Dashboard queries** | 0.17 GB/month | $0.00 (under 1 TB) |
| **GCP VM** (e2-micro) | — | $0.00 (free tier) |
| **TOTAL (Year 1 avg)** | — | **$0.06/month** |

### Key Findings

✅ **Data collection is FREE** (batch loads)  
✅ **Queries stay FREE** (23 GB << 1 TB free tier)  
✅ **Storage grows slowly** with smart updates (225 MB/month)  
✅ **Total cost: $0.04-0.09/month** (4-9 pennies)  
✅ **With optimizations: $0.05/month** flat (after partitioning + expiration)

### Bottom Line

Even with **11,520 data pulls per month** (24/7 collection every 5-15 minutes), your BigQuery costs remain:

**$0.06/month average** (6 pennies)

As long as you:
1. Use batch loads (FREE) or streaming (under 2 TB free)
2. Use MERGE/dedup to prevent storage explosion
3. Set up table partitioning with auto-expiration

---

**Next Steps**:
1. Review current data collection scripts
2. Ensure using batch loads or MERGE statements (not append-only)
3. Set up partitioning on high-volume tables
4. Enable auto-expiration (365 days)
5. Monitor with `bq ls` and Cloud Console

See `EXTERNAL_DRIVE_TO_BIGQUERY_PLAN.md` for upload strategy.

