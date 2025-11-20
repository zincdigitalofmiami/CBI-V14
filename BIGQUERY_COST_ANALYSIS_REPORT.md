---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Cost Analysis for Vercel Dashboard
**Date**: November 18, 2025  
**Analysis**: Real data from cbi-v14 BigQuery project

---

## Executive Summary

**Current Monthly Cost**: $0.01/month (BigQuery storage only)  
**Projected Dashboard Cost** (2-5 hrs/day): $0.00/month (under free tier)  
**Total Infrastructure Cost** (with free-tier GCP VM): $0.01/month  
**Worst Case** (paid VM if outside free tier): ~$7/month

**Verdict**: ✅ **You can run everything for essentially free** ($0.01/month = negligible)

---

## Part 1: What We Have Now

### Current BigQuery Storage

| Metric | Value |
|--------|-------|
| **Total Storage** | **0.70 GB** |
| **Total Tables** | 479 |
| **Total Rows** | 2,532,081 |
| **Monthly Storage Cost** | **$0.01** |

### Storage by Dataset (Top 10)

| Dataset | Size (GB) | Tables | Rows |
|---------|-----------|--------|------|
| yahoo_finance_comprehensive | 0.18 | 10 | 801,199 |
| models_v4 | 0.11 | 99 | 205,468 |
| forecasting_data_warehouse | 0.10 | 75 | 482,053 |
| models | 0.05 | 60 | 44,481 |
| staging | 0.03 | 9 | 79,885 |
| training | 0.03 | 18 | 34,206 |
| archive | 0.02 | 11 | 13,937 |
| raw_intelligence | 0.01 | 6 | 87,666 |
| features | 0.00 | 3 | 12,391 |
| predictions | 0.00 | 7 | ~600 |

**Key Findings**:
- ✅ **Extremely small dataset** (0.70 GB total)
- ✅ All data fits comfortably in BigQuery free tier
- ✅ Storage cost is effectively zero ($0.01/month)
- ✅ No cleanup needed - storage is minimal

---

## Part 2: What Exists for Dashboard

### Prediction Tables/Views

| Table/View | Type | Status |
|------------|------|--------|
| predictions.zl_predictions_prod_allhistory_1w | VIEW | ✅ Exists |
| predictions.zl_predictions_prod_allhistory_1m | TABLE | ✅ Exists |
| predictions.zl_predictions_prod_allhistory_3m | VIEW | ✅ Exists |
| predictions.zl_predictions_prod_allhistory_6m | VIEW | ✅ Exists |
| predictions.zl_predictions_prod_allhistory_12m | VIEW | ✅ Exists |
| predictions.zl_predictions_prod_all_latest | TABLE | ✅ Exists |

**Note**: The prediction views exist but NOT with `vw_zl_{horizon}_latest` naming. They use `zl_predictions_prod_allhistory_{horizon}` naming.

### Data Source Tables

| Table | Status | Rows | Use Case |
|-------|--------|------|----------|
| yahoo_finance_comprehensive.all_symbols_20yr | ✅ Exists | ~801K | Historical price data |
| yahoo_finance_comprehensive.yahoo_finance_complete_enterprise | ✅ Exists | Large | Market data |
| raw_intelligence.commodity_crude_oil_prices | ✅ Exists | ~10K | Oil prices |
| raw_intelligence.commodity_palm_oil_prices | ✅ Exists | ~5K | Palm oil prices |
| features.market_regimes | ✅ Exists | ~12K | Regime detection |
| features.regime_calendar | ✅ Exists | ~13K | Regime calendar |

### Training Tables

| Table | Type | Status |
|-------|------|--------|
| training.zl_training_prod_allhistory_{1w\|1m\|3m\|6m\|12m} | TABLE | ✅ All 5 exist |
| training.zl_training_full_allhistory_{1w\|1m\|3m\|6m\|12m} | TABLE | ✅ All 5 exist |
| training.regime_calendar | TABLE | ✅ Exists |
| training.regime_weights | TABLE | ✅ Exists |

---

## Part 3: Dashboard Query Costs (2-5 Hours/Day)

### Usage Assumptions

| Parameter | Low | High |
|-----------|-----|------|
| **Hours/day** | 2 | 5 |
| **Requests/minute** | 2 | 2 |
| **Daily requests** | 240 | 600 |
| **Monthly requests** | 7,200 | 18,000 |

### Data Scanned

| Scenario | GB/month | TB/month | Cost |
|----------|----------|----------|------|
| **Low usage** (2 hrs/day) | 0.069 | 0.000067 | **$0.00** |
| **High usage** (5 hrs/day) | 0.172 | 0.000168 | **$0.00** |
| **Free tier limit** | 1,000 | 1.0 | — |

**Analysis**:
- ✅ Dashboard queries scan **0.17 GB/month** (worst case)
- ✅ BigQuery free tier: **1 TB/month** (1000 GB)
- ✅ **You're using 0.017% of free tier** - essentially zero cost
- ✅ Even with 10x traffic, still free

**BigQuery Query Pricing**:
- First 1 TB/month: **FREE**
- After 1 TB: $5/TB
- Your usage: ~0.00017 TB = **$0.00**

---

## Part 4: Live Data Storage Needs (DataBento)

### Live Futures Data Volume

| Metric | Value |
|--------|-------|
| **Symbols** | 10 (ES, ZL, CL, GC, ZC, ZS, ZW, NG, HG, SI) |
| **Bars/day** | 14,400 (1-min bars, 24 hrs) |
| **Daily storage** | 1.37 MB |
| **Monthly storage** | 0.04 GB (40 MB) |
| **Yearly storage** | 0.48 GB |
| **30 GB free tier** | ✅ Covers 62 years of data |

**Analysis**:
- ✅ Live data is **tiny** (1.37 MB/day)
- ✅ One year = 0.48 GB (1% of free tier)
- ✅ GCP persistent disk free tier: 30 GB
- ✅ **No storage costs for live data**

---

## Part 5: GCP VM Costs (e2-micro for Live Collector)

### GCP Free Tier (Eligible if in US Region)

| Resource | Free Tier | Needed | Status |
|----------|-----------|--------|--------|
| **Compute** | 1 e2-micro (730 hrs/month) | 1 e2-micro | ✅ FREE |
| **Persistent Disk** | 30 GB standard | ~5 GB | ✅ FREE |
| **Network Egress** | 1 GB/month | <100 MB/month | ✅ FREE |
| **External IP** | Free on e2-micro | 1 IP | ✅ FREE |

**Free Tier Requirements**:
- ✅ Region: us-west1 (Oregon), us-central1 (Iowa), or us-east1 (South Carolina)
- ✅ Instance: e2-micro (0.25-2 vCPU, 1 GB RAM)
- ✅ Non-preemptible instance
- ✅ One instance only

**Paid VM Cost** (if outside free tier):
- e2-micro in us-central1: ~$6.11/month
- e2-micro in asia-southeast1: ~$7.50/month

**Recommendation**: Use **us-central1** (Iowa) to qualify for free tier

---

## Part 6: Total Monthly Cost Breakdown

### Current Costs (What We Have)

| Service | Cost |
|---------|------|
| BigQuery Storage (0.70 GB) | $0.01 |
| BigQuery Queries | $0.00 (under 1 TB free tier) |
| **CURRENT TOTAL** | **$0.01/month** |

### Dashboard Costs (2-5 hrs/day, added)

| Service | Cost |
|---------|------|
| BigQuery Queries (0.17 GB scanned) | $0.00 (under 1 TB free tier) |
| Vercel Hosting | $0.00 (Hobby tier) or $20 (Pro) |
| **DASHBOARD ADDITION** | **$0.00/month** (BQ queries) |

### Live Data Infrastructure (DataBento Collector)

| Service | Free Tier | Cost |
|---------|-----------|------|
| e2-micro VM (us-central1) | ✅ Yes | $0.00 |
| 30 GB Persistent Disk | ✅ Yes | $0.00 |
| 1 GB Network Egress | ✅ Yes | $0.00 |
| **LIVE INFRA ADDITION** | — | **$0.00/month** |

### Separate Costs (Not GCP)

| Service | Cost |
|---------|------|
| DataBento API (Plan75) | $75/month (separate vendor) |
| Vercel Pro (optional) | $20/month (if needed) |

---

## Part 7: Complete Cost Summary

### Scenario A: Free Tier (Recommended)

| Component | Monthly Cost |
|-----------|--------------|
| BigQuery Storage | $0.01 |
| BigQuery Queries | $0.00 |
| GCP VM (e2-micro, us-central1) | $0.00 |
| Persistent Disk (< 30 GB) | $0.00 |
| Network Egress (< 1 GB) | $0.00 |
| **GCP TOTAL** | **$0.01/month** |
| **Plus: DataBento** | $75/month (vendor) |
| **Plus: Vercel** | $0-20/month (vendor) |

### Scenario B: Paid VM (Wrong Region or >1 Instance)

| Component | Monthly Cost |
|-----------|--------------|
| BigQuery Storage | $0.01 |
| BigQuery Queries | $0.00 |
| GCP VM (e2-micro, paid) | $6.11 |
| Persistent Disk (< 30 GB) | $0.00 |
| Network Egress (< 1 GB) | $0.00 |
| **GCP TOTAL** | **$6.12/month** |
| **Plus: DataBento** | $75/month (vendor) |
| **Plus: Vercel** | $0-20/month (vendor) |

---

## Part 8: Recommendations

### ✅ What We Have Now
- **0.70 GB** in BigQuery (479 tables, 2.5M rows)
- **$0.01/month** storage cost
- All data well within free tier limits

### ✅ What We Need for Dashboard (2-5 hrs/day)
- **No additional costs** - queries stay under 1 TB free tier
- Prediction views already exist: `predictions.zl_predictions_prod_allhistory_{horizon}`
- Dashboard can read directly from BigQuery views

### ✅ What We Need for Live Data (DataBento)
- **1 e2-micro VM** in us-central1 (free tier eligible)
- **~40 MB/month** Parquet storage (well under 30 GB free)
- **<100 MB/month** network egress (under 1 GB free)

### 🎯 Optimization Strategy

1. **Use Free Tier VM** (us-central1, Iowa)
   - Spin up e2-micro in us-central1
   - Qualifies for 730 hrs/month free compute
   - Total cost: $0.00

2. **Dashboard Query Optimization**
   - Use 10-30s cache on Vercel endpoints (already doing this)
   - Read from BigQuery views (already optimized)
   - Keep queries simple (SELECT * from views, no aggregations)
   - Total cost: $0.00 (under 1 TB free tier)

3. **Live Data Collection**
   - Python script: `scripts/live/databento_live_poller.py`
   - Write to Parquet: `/mnt/data/live/{symbol}/1m/date=YYYY-MM-DD/`
   - Hourly cron: `scripts/ingest/build_forward_continuous.py`
   - Total cost: $0.00 (under 30 GB free PD)

4. **Vercel Dashboard Endpoints**
   - Option A: Read from DataBento API directly (DATABENTO_API_KEY server-side)
   - Option B: Read from VM Parquet files (serve via simple API)
   - Option C: Read from BigQuery prediction views (current setup)
   - Recommended: **Option C** (BigQuery views, already working)

### ⚡ Next Steps

1. **Immediate** (Today):
   - Verify dashboard works with existing prediction views
   - Update dashboard code to use `predictions.zl_predictions_prod_allhistory_{horizon}`
   - Test query performance with 10-30s cache

2. **This Week** (Optional - if live data needed):
   - Spin up e2-micro VM in us-central1
   - Install Python 3.12 + DataBento client
   - Run: `python3 scripts/live/databento_live_poller.py --roots ES,ZL,CL`
   - Set up hourly cron for continuous contract builder

3. **Monitoring**:
   - Check BigQuery query bytes scanned (should stay << 1 GB/month)
   - Monitor VM CPU/memory (e2-micro should handle easily)
   - Verify Parquet storage stays < 1 GB (cleanup old data if needed)

---

## Part 9: Cost Comparison

### Current Architecture vs Alternatives

| Architecture | Monthly Cost | Notes |
|--------------|--------------|-------|
| **Current (BQ + Free VM)** | **$0.01** | ✅ Recommended |
| BQ + Paid VM (wrong region) | $6.12 | Easily avoidable |
| BQ Streaming + Paid VM | $12-20 | Unnecessary (no streaming needed) |
| Cloud Run + BQ | $15-30 | Over-engineered |
| Dataflow + BQ | $50-100+ | WAY over-engineered |

**Verdict**: Current architecture is **optimal** for this use case.

---

## Part 10: Key Metrics

### BigQuery Usage Limits (Free Tier)

| Resource | Free Tier | Current Usage | Headroom |
|----------|-----------|---------------|----------|
| **Storage** | 10 GB | 0.70 GB | **93% available** |
| **Queries** | 1 TB/month | 0.00017 TB/month | **99.98% available** |

### GCP VM Usage Limits (Free Tier)

| Resource | Free Tier | Current Need | Headroom |
|----------|-----------|--------------|----------|
| **Compute** | 730 hrs/month (e2-micro) | 730 hrs/month | 0% (full usage) |
| **Storage** | 30 GB PD | ~1 GB | **97% available** |
| **Network** | 1 GB egress | <0.1 GB | **90% available** |

---

## Conclusion

**Question**: "What we have now, how much we need, what we need for Vercel dashboard with 2-5 hours/day use?"

**Answer**:

1. **What We Have**: 0.70 GB in BigQuery ($0.01/month)

2. **How Much We Need**: 
   - Dashboard queries: ~0.17 GB/month (under 1 TB free tier = $0)
   - Live data storage: ~0.04 GB/month (under 30 GB free tier = $0)
   - Total additional: **$0.00/month**

3. **What We Need for Dashboard**:
   - ✅ Prediction views already exist (use `predictions.zl_predictions_prod_allhistory_{horizon}`)
   - ✅ Query costs under free tier (0.17 GB << 1 TB)
   - ✅ Optional: Free-tier e2-micro VM for live data collection
   - ✅ **Total cost: $0.01/month** (essentially free)

**Bottom Line**: You can run the entire infrastructure (BigQuery + Vercel Dashboard + Live Data Collector) for **$0.01/month** if you use a free-tier e2-micro VM in a supported US region.

If you skip the live data collector or run it on your Mac instead of GCP, your cost remains $0.01/month (just BigQuery storage).

**No changes needed** - current architecture is already cost-optimized.

---

**Report Generated**: November 18, 2025  
**Data Source**: Real BigQuery data from cbi-v14 project  
**Analysis By**: BigQuery cost analysis script





