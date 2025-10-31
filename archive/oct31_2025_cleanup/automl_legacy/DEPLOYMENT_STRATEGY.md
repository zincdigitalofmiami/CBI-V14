# 🎯 VERTEX AI DEPLOYMENT STRATEGY

## ✅ CONFIRMED: All Models are Vertex AI AutoML (NOT ARIMA)

| Horizon | Model ID | Endpoint Status |
|---------|----------|-----------------|
| **1W** | 575258986094264320 | ✅ Has Endpoint (3891152959001591808) |
| **1M** | 274643710967283712 | ❌ No Endpoint |
| **3M** | 3157158578716934144 | ❌ No Endpoint |
| **6M** | 3788577320223113216 | ❌ No Endpoint |

---

## 🚀 RECOMMENDED SERVERLESS APPROACH

### Option A: Hybrid (Best of Both Worlds)

**For 1W (Real-time for dashboard):**
- Use existing endpoint (already deployed)
- Cost: ~$144/month for 1 endpoint
- Benefit: Instant predictions when users load dashboard

**For 1M, 3M, 6M (Batch predictions):**
- Use batch predictions (TRUE serverless)
- Run daily at 6 AM via Cloud Scheduler
- Cost: ~$0.003/day = $1/month
- Benefit: No idle costs

**Total Cost: ~$145/month** (vs $576/month for all endpoints)

### Option B: All Batch (Most Cost-Effective)

**All 4 horizons use batch predictions:**
- Run once daily via Cloud Scheduler
- Dashboard shows predictions from latest batch run
- Cost: ~$0.004/day = $1.50/month total
- Predictions are 0-24 hours old (acceptable for most use cases)

**Total Cost: ~$1.50/month** (99.7% savings)

### Option C: All Endpoints (Real-time but Expensive)

**Deploy all 4 models to endpoints:**
- Instant predictions anytime
- Cost: 4 × $144/month = **$576/month**
- Only needed if dashboard requires real-time updates

---

## 📊 Current Status

### What's Working NOW:
```python
# 1W model can be called via endpoint
from google.cloud import aiplatform

aiplatform.init(project="cbi-v14", location="us-central1")
endpoint = aiplatform.Endpoint("3891152959001591808")

# Make prediction
prediction = endpoint.predict(instances=[features])
```

### What's Running:
- Batch prediction job for 1W (ID: 6515374901661007872)
- Status: Running (ETA: 5-30 minutes)
- Will save to BigQuery when complete

---

## 🎯 RECOMMENDED NEXT STEPS

### Immediate (Use what's working):

1. **Update FastAPI to use 1W endpoint:**
```python
# In forecast/main.py - /api/vertex-predict endpoint
endpoint = aiplatform.Endpoint("3891152959001591808")
prediction = endpoint.predict(instances=[features])
```

2. **Wait for batch job to complete** (check with `python3 check_batch_status.py`)

3. **Deploy other models to endpoints if needed:**
```bash
# Only if you want real-time predictions for 1M, 3M, 6M
# Cost: +$432/month
python3 deploy_serverless_endpoints.py
```

### Long-term (Cost-effective):

1. **Set up Cloud Scheduler for daily batch predictions:**
```bash
gcloud scheduler jobs create http vertex-daily-predictions \
  --schedule="0 6 * * *" \
  --uri="https://YOUR_CLOUD_FUNCTION_URL" \
  --time-zone="America/New_York"
```

2. **Dashboard reads from BigQuery:**
```sql
SELECT * FROM `cbi-v14.predictions.daily_forecasts`
WHERE prediction_date = CURRENT_DATE()
```

---

## 💰 Cost Summary

| Approach | Monthly Cost | Latency | Update Frequency |
|----------|--------------|---------|------------------|
| **All Batch** | $1.50 | N/A | Daily at 6 AM |
| **Hybrid (1W endpoint + 3 batch)** | $145 | <100ms for 1W | 1W real-time, others daily |
| **All Endpoints** | $576 | <100ms all | Real-time all |

**Recommendation:** Hybrid approach - keep 1W endpoint for quick dashboard loads, use batch for longer horizons.

---

## ✅ Serverless Confirmed

- **Batch Predictions = TRUE Serverless** ✅ (pay only when running)
- **Online Endpoints = NOT Serverless** ❌ (min 1 replica always on)
- **All 4 models are Vertex AI AutoML** ✅ (NOT ARIMA)

---

## 📝 Next Action

**Choose your approach:**

1. **I want lowest cost ($1.50/month):** Wait for batch jobs to finish, use all batch predictions
2. **I want fast dashboard ($145/month):** Use 1W endpoint + batch for others
3. **I want everything real-time ($576/month):** Deploy all 4 to endpoints

Let me know which approach you prefer!

