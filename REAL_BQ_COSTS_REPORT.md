# Real BigQuery Costs - Direct from BigQuery
**Date:** November 19, 2025  
**Source:** Direct queries to `cbi-v14` BigQuery project  
**Location:** `us-central1`

---

## 🎯 CURRENT REAL COSTS

### **Total Monthly Cost: $1.54/month**

| Component | Current Usage | Cost |
|-----------|---------------|------|
| **Storage** | 0.672 GB | **$0.01/month** |
| **Queries** | 1,337 GB/month (1.31 TB) | **$1.53/month** ⚠️ |
| **Slots** | 551 hours/month | **$0.00/month** |
| **Streaming** | 0.374 GB/month | **$0.00/month** |
| **TOTAL** | — | **$1.54/month** |

**⚠️ CRITICAL:** You're already **exceeding the query free tier** (1 TB/month). You're scanning **1.31 TB/month**, which is **31% over the free tier**.

---

## 📊 DETAILED BREAKDOWN

### 1. Storage Costs

**Current Storage:**
- **Logical bytes:** 0.672 GB (what you see)
- **Physical bytes:** 0.500 GB (compressed on disk)
- **Tables:** 959 tables across 43 datasets
- **Cost:** $0.0134/month (active storage rate)

**Top Datasets by Size:**
| Dataset | Logical GB | Physical GB | Tables |
|---------|------------|-------------|--------|
| yahoo_finance_comprehensive | 0.182 | 0.094 | 12 |
| models_v4 | 0.114 | 0.042 | 121 |
| forecasting_data_warehouse | 0.100 | 0.067 | 111 |
| forecasting_data_warehouse_backup_20251117 | 0.064 | 0.023 | 87 |
| models_v4_backup_20251117 | 0.059 | 0.023 | 78 |

**Storage is minimal** - well under free tier (10 GB).

---

### 2. Query Costs ⚠️ **EXCEEDING FREE TIER**

**Last 30 Days:**
- **Total queries:** 33,866 jobs
- **Data scanned:** 1,336.991 GB (1.306 TB)
- **Slot hours:** 551.34 hours
- **Free tier:** 1 TB/month
- **Excess:** 0.306 TB
- **Cost:** **$1.53/month** ($5/TB × 0.306 TB)

**Daily Breakdown (Last 30 Days):**
- **Peak day:** Oct 22 - 364.8 GB scanned
- **Average day:** 44.6 GB scanned
- **Heavy usage days:** Oct 22-23, Nov 3-4, Nov 6-7

**Why You're Exceeding:**
- Large table scans (forecasting_data_warehouse, models_v4)
- Full table scans without filters
- Dashboard queries scanning entire datasets
- Data collection queries checking for updates

**Recommendations:**
1. Add WHERE clauses to limit date ranges
2. Use partitioned tables (scan only relevant partitions)
3. Cache dashboard queries (Vercel already doing this)
4. Use LIMIT clauses for exploratory queries

---

### 3. Streaming Insert Costs

**Last 30 Days:**
- **Load jobs:** 1,402 jobs
- **Data loaded:** 0.374 GB
- **Free tier:** 2 TB/month
- **Cost:** **$0.00/month** ✅

**All batch loads are FREE** - no streaming insert costs.

---

### 4. Slot Costs

**Last 30 Days:**
- **Slot hours:** 551.34 hours
- **Free tier:** 2,000 hours/month
- **Cost:** **$0.00/month** ✅

**Well under free tier** - no slot costs.

---

## 📈 COST PROJECTIONS (With Vast Data Growth)

### Storage Projections

| Scenario | Storage (GB) | Monthly Cost | Yearly Cost |
|----------|--------------|--------------|-------------|
| **Current** | 0.67 | $0.01 | $0.16 |
| **10x Growth** | 6.72 | $0.13 | $1.61 |
| **50x Growth** | 33.60 | $0.67 | $8.06 |
| **100x Growth** | 67.19 | $1.34 | $16.13 |
| **500x Growth** | 335.95 | $6.72 | $80.63 |
| **1000x Growth** | 671.90 | $13.44 | $161.25 |

**Storage stays cheap** - even 1000x growth = $13.44/month.

---

### Query Cost Projections ⚠️ **EXPENSIVE**

| Scenario | GB Scanned/Month | TB Scanned/Month | Monthly Cost | Yearly Cost |
|----------|------------------|------------------|--------------|-------------|
| **Current** | 1,337 | 1.31 | **$1.53** | $18.36 |
| **10x Growth** | 13,370 | 13.06 | **$60.28** | $723.36 |
| **50x Growth** | 66,850 | 65.28 | **$321.41** | $3,856.92 |
| **100x Growth** | 133,699 | 130.57 | **$647.83** | $7,773.96 |
| **500x Growth** | 668,496 | 652.83 | **$3,259.14** | $39,109.68 |
| **1000x Growth** | 1,336,991 | 1,305.66 | **$6,523.28** | $78,279.36 |

**⚠️ CRITICAL:** Query costs scale **linearly** and become **very expensive** with vast data growth.

**Current problem:** You're already scanning 1.31 TB/month. With 10x growth, you'd scan 13 TB/month = **$60/month just for queries**.

---

## 🚨 COST OPTIMIZATION STRATEGIES

### 1. Optimize Queries (CRITICAL)

**Problem:** Full table scans without filters

**Solutions:**
```sql
-- BAD: Scans entire table
SELECT * FROM forecasting_data_warehouse.prices;

-- GOOD: Scan only recent data
SELECT * FROM forecasting_data_warehouse.prices
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- BETTER: Use partitioned table
SELECT * FROM forecasting_data_warehouse.prices_partitioned
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
-- Only scans partitions for last 30 days
```

**Expected savings:** 50-90% reduction in query costs

---

### 2. Partition All Large Tables

**Current large tables:**
- `forecasting_data_warehouse.*` (0.100 GB)
- `models_v4.*` (0.114 GB)
- `yahoo_finance_comprehensive.*` (0.182 GB)

**Action:** Partition by `date` column

```sql
CREATE TABLE forecasting_data_warehouse.prices_partitioned
PARTITION BY date
CLUSTER BY symbol
AS SELECT * FROM forecasting_data_warehouse.prices;
```

**Expected savings:** 70-95% reduction in query scans

---

### 3. Cache Dashboard Queries

**Current:** Dashboard queries BigQuery directly (some cached)

**Recommendation:** 
- Increase Vercel cache to 5-10 minutes (from 10-30s)
- Use stale-while-revalidate pattern
- Cache prediction views (they don't change frequently)

**Expected savings:** 80-90% reduction in dashboard query costs

---

### 4. Limit Data Collection Queries

**Current:** Collection scripts may be scanning full tables to check for updates

**Recommendation:**
```python
# BAD: Scans entire table
latest_date = client.query("""
    SELECT MAX(date) FROM forecasting_data_warehouse.prices
""").result()

# GOOD: Use metadata table or last update timestamp
latest_date = get_last_update_timestamp()  # From ops.ingestion_runs
```

**Expected savings:** 50-70% reduction in collection query costs

---

### 5. Use Materialized Views

**For frequently queried aggregations:**
```sql
CREATE MATERIALIZED VIEW forecasting_data_warehouse.daily_summary
PARTITION BY date
AS
SELECT 
  date,
  symbol,
  AVG(close) as avg_close,
  SUM(volume) as total_volume
FROM forecasting_data_warehouse.prices
GROUP BY date, symbol;
```

**Expected savings:** 90%+ reduction (pre-aggregated data)

---

## 💰 PROJECTED COSTS (With Optimizations)

### Scenario: 100x Data Growth + Optimizations

**Without Optimizations:**
- Storage: $1.34/month
- Queries: $647.83/month
- **Total: $649.17/month**

**With Optimizations (partitioning + caching + query limits):**
- Storage: $1.34/month
- Queries: $32.39/month (90% reduction)
- **Total: $33.73/month**

**Savings: $615.44/month (95% reduction)**

---

## 📊 REAL USAGE PATTERNS

### Query Volume by Day (Last 30 Days)

**Heavy Usage Days:**
- Oct 22: 364.8 GB (migration/backfill?)
- Oct 23: 162.6 GB
- Nov 3: 80.4 GB
- Nov 4: 345.3 GB (migration?)
- Nov 6: 76.7 GB

**Normal Usage Days:**
- Average: 44.6 GB/day
- Light days: 0.1-5 GB/day

**Pattern:** Heavy usage during migrations/backfills, normal usage otherwise.

---

### Storage Growth Pattern

**Current:** 0.672 GB (959 tables)

**Growth Rate:** Minimal (most data is historical, not growing)

**Projected Growth:**
- With live feeds: +225 MB/month (with MERGE/dedup)
- Without dedup: +6 GB/month (would be expensive)

**Recommendation:** Always use MERGE/UPSERT, never append-only.

---

## ✅ ACTION ITEMS

### Immediate (Reduce Current $1.53/month Query Cost)

1. **Add date filters to all queries**
   - Dashboard: Only query last 30-90 days
   - Collection scripts: Only check recent dates
   - **Expected savings:** 50-70%

2. **Partition large tables**
   - `forecasting_data_warehouse.prices`
   - `models_v4.*` tables
   - `yahoo_finance_comprehensive.*`
   - **Expected savings:** 70-90%

3. **Increase dashboard cache**
   - Vercel: 5-10 minutes (from 10-30s)
   - **Expected savings:** 80-90% of dashboard queries

### Before Vast Data Growth

4. **Set up materialized views** for common aggregations
5. **Use clustering** on frequently filtered columns
6. **Monitor query costs** weekly (set up alerts)

---

## 💻 LIVE SERVER COSTS

### Current Setup
**You're running:**
- Live data feeds (DataBento continuous connection)
- Cron pulls for scrapes (every 5-15 minutes)
- Dashboard on Vercel (reads from BigQuery)

### Server Options

**Option 1: GCP e2-micro VM (Free Tier)** ✅ **RECOMMENDED**
- **Cost:** $0.00/month
- **Requirements:** us-central1, us-west1, or us-east1
- **Specs:** 0.25-2 vCPU, 1 GB RAM, 30 GB disk
- **Can handle:** Continuous feeds + 11,520 cron jobs/month

**Option 2: GCP e2-micro VM (Paid)**
- **Cost:** $6.11/month (if outside free tier regions)

**Option 3: Cloud Run (Serverless)**
- **Cost:** $3.97/month (pay-per-use)

### Live Server Cost: **$0.00/month** (with free tier VM)

---

## 📋 SUMMARY

### Current Real Costs (BigQuery + Live Server)
- **BigQuery Storage:** $0.01/month ✅
- **BigQuery Queries:** $1.53/month ⚠️ (exceeding free tier)
- **BigQuery Streaming:** $0.00/month ✅
- **Live Server (e2-micro free tier):** $0.00/month ✅
- **TOTAL:** **$1.54/month**

### With Vast Data Growth (100x)
- **Without optimizations:** $649/month
- **With optimizations:** $34/month
- **Savings:** $615/month (95% reduction)

### Key Takeaway
**Query costs are the problem**, not storage. With vast data growth, query costs will explode unless you:
1. Partition tables
2. Add date filters
3. Cache aggressively
4. Use materialized views

**Storage stays cheap** ($13/month even at 1000x growth), but **queries become expensive** ($6,523/month at 1000x without optimizations).

---

**Next Steps:**
1. Review `REAL_BQ_COSTS.json` for detailed breakdown
2. Implement query optimizations (partitioning, filters)
3. Set up cost monitoring alerts
4. Re-run cost analysis after optimizations

