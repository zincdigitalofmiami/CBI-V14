---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Costs Only (Storage + Queries)
**Date:** November 19, 2025  
**Source:** Direct queries to `cbi-v14` BigQuery project  
**Location:** `us-central1`

---

## 🎯 CURRENT REAL COSTS

### **Total BigQuery Cost: $1.54/month**

| Component | Current Usage | Cost |
|-----------|---------------|------|
| **Storage** | 0.672 GB | **$0.01/month** |
| **Queries** | 1,337 GB/month (1.31 TB) | **$1.53/month** ⚠️ |
| **TOTAL** | — | **$1.54/month** |

---

## 📊 STORAGE COSTS

### Current Storage

- **Logical bytes:** 0.672 GB
- **Physical bytes:** 0.500 GB (compressed)
- **Tables:** 959 tables across 43 datasets
- **Cost:** **$0.0134/month**

**Pricing:**
- Active storage: $0.020/GB/month
- Long-term storage (90+ days): $0.010/GB/month
- Free tier: 10 GB

**Current usage:** 6.7% of free tier ✅

---

## 📊 QUERY COSTS ⚠️ **EXCEEDING FREE TIER**

### Last 30 Days Usage

- **Total queries:** 33,866 jobs
- **Data scanned:** 1,336.991 GB (1.306 TB)
- **Free tier:** 1 TB/month
- **Excess:** 0.306 TB
- **Cost:** **$1.5283/month** ($5/TB × 0.306 TB)

**Pricing:**
- First 1 TB/month: FREE
- After 1 TB: $5/TB
- Your usage: 1.31 TB/month = **$1.53/month**

**⚠️ CRITICAL:** You're scanning **31% over the free tier**.

---

## 📈 COST PROJECTIONS (With Vast Data Growth)

### Storage Projections

| Growth | Storage (GB) | Monthly Cost |
|--------|--------------|--------------|
| **Current** | 0.67 | $0.01 |
| **10x** | 6.72 | $0.13 |
| **50x** | 33.60 | $0.67 |
| **100x** | 67.19 | $1.34 |
| **500x** | 335.95 | $6.72 |
| **1000x** | 671.90 | $13.44 |

**Storage stays cheap** - even 1000x growth = $13.44/month.

---

### Query Cost Projections ⚠️ **EXPENSIVE**

| Growth | GB Scanned/Month | TB Scanned/Month | Monthly Cost |
|--------|------------------|------------------|--------------|
| **Current** | 1,337 | 1.31 | **$1.53** |
| **10x** | 13,370 | 13.06 | **$60.28** |
| **50x** | 66,850 | 65.28 | **$321.41** |
| **100x** | 133,699 | 130.57 | **$647.83** |
| **500x** | 668,496 | 652.83 | **$3,259.14** |
| **1000x** | 1,336,991 | 1,305.66 | **$6,523.28** |

**⚠️ CRITICAL:** Query costs scale **linearly** and become **very expensive**.

---

## 💰 TOTAL BIGQUERY COSTS

### Current (Month 1)

| Component | Cost |
|-----------|------|
| Storage | $0.01 |
| Queries | $1.53 |
| **TOTAL** | **$1.54/month** |

### With Vast Data Growth (100x)

**Without Optimizations:**
| Component | Cost |
|-----------|------|
| Storage | $1.34 |
| Queries | $647.83 |
| **TOTAL** | **$649.17/month** |

**With Optimizations (partitioning + filters + caching):**
| Component | Cost |
|-----------|------|
| Storage | $1.34 |
| Queries | $32.39 (90% reduction) |
| **TOTAL** | **$33.73/month** |

**Savings:** $615.44/month (95% reduction)

---

## 🚨 IMMEDIATE ACTIONS TO REDUCE COSTS

### 1. Add Date Filters (Save 50-70%)

**Problem:** Full table scans without filters

**Solution:**
```sql
-- BAD: Scans entire table
SELECT * FROM forecasting_data_warehouse.prices;

-- GOOD: Scan only recent data
SELECT * FROM forecasting_data_warehouse.prices
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
```

**Expected savings:** 50-70% reduction in query costs

---

### 2. Partition Large Tables (Save 70-90%)

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

### 3. Cache Dashboard Queries (Save 80-90%)

**Current:** Dashboard queries BigQuery directly

**Recommendation:** 
- Increase Vercel cache to 5-10 minutes
- Use stale-while-revalidate pattern

**Expected savings:** 80-90% reduction in dashboard query costs

---

## ✅ SUMMARY

### Current BigQuery Costs

- **Storage:** $0.01/month ✅
- **Queries:** $1.53/month ⚠️ (exceeding free tier)
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

**Storage stays cheap** ($13/month even at 1000x growth), but **queries become expensive** ($6,523/month at 1000x without optimizations).

---

**Reference:** Run `python3 scripts/analysis/get_real_bq_costs.py` to get latest costs.

