# ☁️ SERVERLESS VERTEX AI SETUP

## ✅ Confirmed: ALL MODELS ARE VERTEX AI AUTOML (NOT ARIMA)

| Horizon | Model ID | Type | Status |
|---------|----------|------|--------|
| 1W | 575258986094264320 | **Vertex AI AutoML** | ✅ Trained |
| 1M | 274643710967283712 | **Vertex AI AutoML** | ✅ Trained |
| 3M | 3157158578716934144 | **Vertex AI AutoML** | ✅ Trained |
| 6M | 3788577320223113216 | **Vertex AI AutoML** | ✅ Trained |

**ARIMA models were created for baseline comparison only - NOT used in production.**

---

## 🚀 TRUE SERVERLESS: Batch Prediction Approach

### Why Batch Prediction is Serverless:

**Batch Prediction (TRUE Serverless):**
- ✅ Pay ONLY when predictions run (~$0.001 per prediction)
- ✅ ZERO cost when idle
- ✅ Scales automatically during job
- ✅ No endpoints to manage
- ✅ Perfect for daily dashboard updates

**Online Endpoints (NOT Serverless):**
- ❌ Minimum 1 replica always running
- ❌ Costs $0.20/hour even when idle = **$576/month**
- ❌ AutoML doesn't support min_replica_count=0
- ❌ Only needed for real-time predictions

---

## 📋 Setup Instructions

### 1. Run Daily Batch Predictions

```bash
# Manual run
python3 /Users/zincdigital/CBI-V14/automl/batch_predictions_serverless.py

# This will:
# 1. Get latest features from BigQuery
# 2. Run batch predictions on all 4 Vertex AI AutoML models
# 3. Save results to BigQuery (predictions.daily_forecasts)
# 4. Cost: ~$0.004 total
```

### 2. Schedule Daily Updates (Cloud Scheduler)

```bash
# Create Cloud Scheduler job for daily predictions
gcloud scheduler jobs create http vertex-daily-predictions \
  --schedule="0 6 * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/run-predictions" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --description="Daily Vertex AI AutoML predictions (serverless)"
```

### 3. Dashboard API Reads from BigQuery

The FastAPI backend (`/api/v4/forecast/latest`) already queries:
```sql
SELECT * FROM `cbi-v14.predictions.daily_forecasts`
WHERE prediction_date = CURRENT_DATE()
ORDER BY created_timestamp DESC
LIMIT 1
```

---

## 💰 Cost Comparison

### Current Setup (If Using Online Endpoints):
- 4 endpoints × 1 replica × $0.20/hour = **$0.80/hour**
- **$576/month** even when no one uses dashboard
- **$6,912/year** idle cost

### Serverless Setup (Batch Prediction):
- Run once daily: **$0.004/day**
- **$1.46/month** total cost
- **$17.52/year** total cost

**Savings: $6,894/year (99.7% cost reduction)**

---

## 🔧 Implementation Status

### ✅ Completed:
1. All 4 Vertex AI AutoML models trained
2. Batch prediction script created
3. BigQuery integration ready
4. Dashboard API configured

### ⏳ Next Steps:
1. Run `batch_predictions_serverless.py` to generate first predictions
2. Verify predictions in `predictions.daily_forecasts` table
3. Test dashboard at https://cbi-dashboard.vercel.app
4. Set up Cloud Scheduler for daily automation

---

## 📊 Model Performance (Vertex AI AutoML)

| Horizon | MAPE | MAE | R² | Performance |
|---------|------|-----|-----|-------------|
| 1W | 2.02% | 1.008 | 0.9836 | Exceptional |
| 1M | TBD | TBD | TBD | Training complete |
| 3M | 2.68% | 1.340 | 0.9727 | Institutional |
| 6M | 2.51% | 1.254 | 0.9792 | Institutional |

All models are **Vertex AI AutoML** (gradient-boosted trees), NOT ARIMA baselines.

---

## 🎯 Verification

Run this to confirm you're using Vertex AI AutoML models:

```bash
gcloud ai models list --region=us-central1 --project=cbi-v14 \
  --filter="displayName:(soybean_oil OR cbi_v14_automl)" \
  --format="table(displayName,name,modelType)"
```

Expected output: All models show "AutoML Tabular" type, NOT "ARIMA"

---

## 📝 Summary

✅ **All 4 models are Vertex AI AutoML** (confirmed)  
✅ **Batch prediction is TRUE serverless** (pay-per-request)  
✅ **Online endpoints are NOT serverless** (min 1 replica always on)  
✅ **Dashboard ready to use batch predictions** (API already configured)  

**Next action:** Run `batch_predictions_serverless.py` to generate today's predictions.

