---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Live Server Costs - Real Infrastructure Analysis
**Date:** November 19, 2025  
**Question:** What does it cost to run a live server for data feeds, cron jobs, and continuous collection?

---

## 🎯 QUICK ANSWER

**Live Server Cost: $0.00-6.11/month** (depending on setup)

**Options:**
1. **GCP e2-micro (Free Tier):** $0.00/month ✅ **RECOMMENDED**
2. **GCP e2-micro (Paid):** $6.11/month (if outside free tier regions)
3. **Cloud Run:** $0.00-5.00/month (pay-per-use, minimal for your workload)

---

## 💻 INFRASTRUCTURE OPTIONS

### Option 1: GCP e2-micro VM (Free Tier) ✅ **BEST**

**Requirements for Free Tier:**
- Region: `us-west1`, `us-central1`, or `us-east1`
- Instance: e2-micro (0.25-2 vCPU, 1 GB RAM)
- Non-preemptible
- One instance only
- 730 hours/month (always-on)

**Specs:**
- **vCPU:** 0.25-2 (shared)
- **RAM:** 1 GB
- **Disk:** 30 GB standard persistent disk (free)
- **Network:** 1 GB egress/month (free)

**Cost:** **$0.00/month** ✅

**What It Can Handle:**
- ✅ DataBento live feed (continuous connection)
- ✅ Cron jobs (every 5-15 minutes)
- ✅ Scrape collection scripts
- ✅ BigQuery uploads (batch loads)
- ✅ Lightweight Python scripts

**Limitations:**
- 1 GB RAM (may need optimization for heavy workloads)
- Shared CPU (may throttle under heavy load)
- Single instance (no redundancy)

---

### Option 2: GCP e2-micro VM (Paid)

**If you're outside free tier regions:**
- **Cost:** $6.11/month (us-central1)
- **Same specs** as free tier
- **Same capabilities**

**When to Use:**
- Need to run in non-US region
- Need multiple instances
- Need preemptible instances

---

### Option 3: Cloud Run (Serverless)

**How It Works:**
- Runs containers on-demand
- Scales to zero when idle
- Pay only for execution time

**Pricing:**
- **CPU:** $0.00002400 per vCPU-second
- **Memory:** $0.00000250 per GiB-second
- **Requests:** $0.40 per million requests
- **Free tier:** 2 million requests/month, 360,000 GiB-seconds, 180,000 vCPU-seconds

**Your Usage Estimate:**
- **Cron jobs:** 11,520 requests/month (every 5-15 min)
- **Execution time:** ~30 seconds per job
- **Memory:** 512 MB per container
- **CPU:** 1 vCPU per container

**Cost Calculation:**
```
Requests: 11,520 = $0.00 (under 2M free tier)
CPU time: 11,520 × 30s × 1 vCPU = 345,600 vCPU-seconds
  - Free tier: 180,000 vCPU-seconds
  - Excess: 165,600 vCPU-seconds
  - Cost: 165,600 × $0.00002400 = $3.97/month

Memory time: 11,520 × 30s × 0.5 GiB = 172,800 GiB-seconds
  - Free tier: 360,000 GiB-seconds
  - Cost: $0.00 (under free tier)

Total: $3.97/month
```

**Cost:** **$3.97/month** (with free tier)

**Pros:**
- Auto-scaling
- Pay only for execution
- No server management

**Cons:**
- Cold starts (1-2 second delay)
- More complex setup (containers)

---

### Option 4: Cloud Functions (Serverless)

**Similar to Cloud Run but simpler:**
- **Free tier:** 2 million invocations/month, 400,000 GB-seconds, 200,000 vCPU-seconds
- **Pricing:** $0.40 per million invocations, $0.0000025 per GB-second

**Your Usage:**
- **Invocations:** 11,520/month = $0.00 (under 2M free tier)
- **Execution:** Similar to Cloud Run
- **Cost:** **$0.00-4.00/month**

---

## 📊 COST COMPARISON

| Option | Monthly Cost | Setup Complexity | Best For |
|--------|--------------|------------------|----------|
| **e2-micro (Free Tier)** | **$0.00** | Low | ✅ Always-on, continuous feeds |
| **e2-micro (Paid)** | $6.11 | Low | Non-US regions |
| **Cloud Run** | $0.00-4.00 | Medium | On-demand, auto-scaling |
| **Cloud Functions** | $0.00-4.00 | Low | Simple cron jobs |

**Recommendation:** **e2-micro (Free Tier)** for always-on continuous feeds.

---

## 🔧 WHAT THE LIVE SERVER DOES

### Continuous Tasks (Always Running)

1. **DataBento Live Feed**
   - Continuous connection to DataBento API
   - Streams 1-minute bars to BigQuery
   - Runs 24/7
   - **Resource:** Low CPU, ~100 MB RAM

2. **BigQuery Streaming**
   - Pushes data to BigQuery as it arrives
   - Uses streaming inserts or batch loads
   - **Resource:** Low CPU, ~50 MB RAM

### Scheduled Tasks (Cron Jobs)

1. **Heavy Pulls (Every 15 Minutes)**
   - FRED, USDA, EIA, CFTC, NOAA
   - 96 pulls/day = 2,880/month
   - **Resource:** Medium CPU, ~200 MB RAM per pull

2. **Light Pulls (Every 5 Minutes)**
   - Yahoo Finance, pricing updates
   - 288 pulls/day = 8,640/month
   - **Resource:** Low CPU, ~50 MB RAM per pull

3. **Scrapes (Various Intervals)**
   - News, sentiment, policy events
   - Variable frequency
   - **Resource:** Medium CPU, ~300 MB RAM per scrape

**Total Cron Jobs:** ~11,520/month

---

## 💰 TOTAL INFRASTRUCTURE COSTS

### Scenario A: e2-micro (Free Tier) ✅ **RECOMMENDED**

| Component | Cost |
|-----------|------|
| **VM (e2-micro, us-central1)** | $0.00 |
| **Persistent Disk (30 GB)** | $0.00 |
| **Network Egress (<1 GB)** | $0.00 |
| **BigQuery Storage** | $0.01 |
| **BigQuery Queries** | $1.53 |
| **BigQuery Streaming** | $0.00 |
| **TOTAL** | **$1.54/month** |

**Same as current BigQuery costs** - server is free!

---

### Scenario B: e2-micro (Paid Region)

| Component | Cost |
|-----------|------|
| **VM (e2-micro, paid region)** | $6.11 |
| **Persistent Disk (30 GB)** | $0.00 |
| **Network Egress (<1 GB)** | $0.00 |
| **BigQuery Storage** | $0.01 |
| **BigQuery Queries** | $1.53 |
| **BigQuery Streaming** | $0.00 |
| **TOTAL** | **$7.65/month** |

---

### Scenario C: Cloud Run

| Component | Cost |
|-----------|------|
| **Cloud Run (execution time)** | $3.97 |
| **Cloud Storage (if needed)** | $0.00-0.10 |
| **BigQuery Storage** | $0.01 |
| **BigQuery Queries** | $1.53 |
| **BigQuery Streaming** | $0.00 |
| **TOTAL** | **$5.51/month** |

---

## 🚀 SETUP INSTRUCTIONS

### Option 1: e2-micro VM (Free Tier)

```bash
# Create VM in us-central1 (free tier eligible)
gcloud compute instances create cbi-live-collector \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-standard

# SSH into VM
gcloud compute ssh cbi-live-collector --zone=us-central1-a

# Install dependencies
sudo apt update
sudo apt install -y python3-pip git
pip3 install databento pandas pyarrow google-cloud-bigquery

# Clone repo (or copy scripts)
git clone https://github.com/zincdigitalofmiami/CBI-V14.git
cd CBI-V14

# Set up cron jobs
crontab -e
# Add:
*/15 * * * * cd /home/user/CBI-V14 && python3 scripts/ingest/collect_fred_comprehensive.py
*/5 * * * * cd /home/user/CBI-V14 && python3 scripts/ingest/collect_yahoo_finance_comprehensive.py
# ... etc

# Start continuous DataBento feed (runs in background)
nohup python3 scripts/live/databento_live_poller.py \
  --roots ZL,MES,ES \
  --interval 60 \
  >> /var/log/databento_live.log 2>&1 &
```

**Cost:** $0.00/month ✅

---

### Option 2: Cloud Run (Serverless)

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: cbi-data-collector
spec:
  template:
    spec:
      containers:
      - image: gcr.io/cbi-v14/data-collector:latest
        resources:
          limits:
            cpu: "1"
            memory: 512Mi
        env:
        - name: DATABENTO_API_KEY
          valueFrom:
            secretKeyRef:
              name: databento-key
              key: api-key
```

**Cost:** $3.97/month

---

## 📊 RESOURCE USAGE ESTIMATES

### e2-micro VM (1 GB RAM, 0.25-2 vCPU)

**Continuous Tasks:**
- DataBento feed: ~100 MB RAM, 5% CPU
- BigQuery streaming: ~50 MB RAM, 2% CPU
- **Total continuous:** ~150 MB RAM, 7% CPU ✅

**Cron Jobs (Peak):**
- Heavy pull: ~200 MB RAM, 30% CPU (15 min)
- Light pull: ~50 MB RAM, 10% CPU (5 min)
- **Peak:** ~250 MB RAM, 40% CPU ✅

**Headroom:** 750 MB RAM, 60% CPU available ✅

**Verdict:** e2-micro can handle your workload easily.

---

## ⚠️ CONSIDERATIONS

### Free Tier Limitations

1. **730 hours/month** - Must be exactly 730 (always-on)
2. **One instance only** - Can't run multiple VMs
3. **US regions only** - Must use us-west1, us-central1, or us-east1
4. **Non-preemptible** - Can't use preemptible instances

### If You Exceed Free Tier

**Options:**
1. Use paid e2-micro: $6.11/month
2. Use Cloud Run: $3.97/month
3. Optimize to stay within free tier

---

## ✅ RECOMMENDATION

### For Your Use Case (Live Feeds + Cron Jobs)

**Best Option:** **e2-micro VM (Free Tier)**

**Why:**
- ✅ $0.00/month
- ✅ Always-on (perfect for continuous feeds)
- ✅ Enough resources for your workload
- ✅ Simple setup (just SSH and run scripts)
- ✅ No cold starts (unlike Cloud Run)

**Setup:**
1. Create e2-micro in `us-central1-a`
2. Install Python + dependencies
3. Set up cron jobs
4. Start DataBento continuous feed
5. **Total cost: $0.00/month**

**Total Infrastructure Cost:**
- **VM:** $0.00/month
- **BigQuery:** $1.54/month
- **TOTAL:** **$1.54/month**

---

## 📋 SUMMARY

### Live Server Costs

| Option | Monthly Cost | Best For |
|--------|--------------|----------|
| **e2-micro (Free Tier)** | **$0.00** | ✅ Always-on continuous feeds |
| **e2-micro (Paid)** | $6.11 | Non-US regions |
| **Cloud Run** | $3.97 | On-demand, auto-scaling |

### Total Infrastructure (VM + BigQuery)

| Scenario | VM Cost | BigQuery Cost | Total |
|----------|---------|---------------|-------|
| **Free Tier VM** | $0.00 | $1.54 | **$1.54/month** |
| **Paid VM** | $6.11 | $1.54 | $7.65/month |
| **Cloud Run** | $3.97 | $1.54 | $5.51/month |

**Recommendation:** Use **e2-micro (Free Tier)** in `us-central1` = **$0.00/month for the server**.

**Your total infrastructure cost stays at $1.54/month** (just BigQuery queries).

---

**Next Steps:**
1. Create e2-micro VM in us-central1
2. Set up continuous DataBento feed
3. Configure cron jobs for scrapes
4. Monitor resource usage (should be well under limits)





