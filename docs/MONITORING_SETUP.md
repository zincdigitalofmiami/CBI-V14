# Monitoring & Alerts Setup Guide

**Last Updated:** 2025-10-31  
**Purpose:** Configure Cloud Scheduler, Cloud Monitoring, and budget alerts for production operations

---

## 🎯 Monitoring Requirements

### Critical Alerts
1. **Job Failure Alerts** - Predictor/aggregation jobs fail
2. **Zero-Row Alerts** - No predictions in 25 hours
3. **Endpoint Error Alerts** - Vertex AI predict failures
4. **Budget Alerts** - Vertex AI spending > $100/month

### Scheduled Jobs
1. **Predictor Job** - Hourly (after market open)
2. **Aggregation Job** - Hourly (after predictor)
3. **1W Signal Computation** - Hourly
4. **Cache Invalidation Heartbeat** - After predictor/aggregation

---

## ⏰ Cloud Scheduler Setup

### 1. Predictor Job (Hourly)
```bash
gcloud scheduler jobs create http predictor-job-1m \
  --location=us-central1 \
  --schedule="0 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/api/run-predictor" \
  --http-method=POST \
  --headers="Authorization=Bearer $(gcloud auth print-identity-token)" \
  --time-zone="America/New_York"
```

**Alternative:** Run as Cloud Run Job
```bash
gcloud run jobs create predictor-job-1m \
  --image=gcr.io/cbi-v14/predictor-job:latest \
  --region=us-central1 \
  --command="python" \
  --args="scripts/1m_predictor_job.py" \
  --set-env-vars="PROJECT_ID=cbi-v14"
```

### 2. Aggregation Job (Hourly, after predictor)
```bash
gcloud scheduler jobs create http aggregation-job-1m \
  --location=us-central1 \
  --schedule="5 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/api/run-aggregation" \
  --http-method=POST \
  --time-zone="America/New_York"
```

### 3. 1W Signal Computation (Hourly)
```bash
gcloud scheduler jobs create http signal-computation-1w \
  --location=us-central1 \
  --schedule="10 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/api/run-1w-signals" \
  --http-method=POST \
  --time-zone="America/New_York"
```

### 4. Cache Invalidation Heartbeat (After jobs complete)
```bash
gcloud scheduler jobs create http cache-invalidation-heartbeat \
  --location=us-central1 \
  --schedule="15 * * * *" \
  --uri="https://YOUR_VERCEL_URL/api/revalidate" \
  --http-method=POST \
  --headers="Authorization=Bearer ${ADMIN_SECRET}" \
  --time-zone="America/New_York"
```

---

## 📊 Cloud Monitoring Alerts

### 1. Job Failure Alert
```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Predictor Job Failure" \
  --condition-display-name="Cloud Scheduler job failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_scheduler_job" AND metric.type="run.googleapis.com/job/run_count"'
```

### 2. Zero-Row Alert (No predictions in 25h)
```bash
# Create log-based metric first
gcloud logging metrics create zero_predictions_alert \
  --description="Alert when no predictions in 25 hours" \
  --log-filter='resource.type="bigquery_table" AND protoPayload.methodName="google.cloud.bigquery.v2.JobService.InsertJob" AND jsonPayload.job.jobConfiguration.query.query:"predictions_1m"'

# Then create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Zero Predictions Alert" \
  --condition-display-name="No predictions in 25 hours"
```

### 3. Endpoint Error Alert
```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Vertex AI Endpoint Error" \
  --condition-display-name="Endpoint predict error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-filter='resource.type="aiplatform.googleapis.com/Endpoint" AND metric.type="aiplatform.googleapis.com/prediction/error_count"'
```

### 4. Budget Alert ($100 Vertex threshold)
```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Vertex AI Budget Alert" \
  --budget-amount=100USD \
  --threshold-rule=percent=100 \
  --notification-rule=pubsub-topic=projects/cbi-v14/topics/budget-alerts \
  --filter-projects=projects/cbi-v14 \
  --filter-credits=EXCLUDE_CREDITS \
  --filter-services=services/aiplatform.googleapis.com
```

---

## 🔔 Notification Channels

### Create Email Channel
```bash
gcloud alpha monitoring channels create \
  --display-name="On-Call Email" \
  --type=email \
  --channel-labels=email_address=team@example.com
```

### Create Slack Channel (via Webhook)
```bash
gcloud alpha monitoring channels create \
  --display-name="Slack Alerts" \
  --type=webhook \
  --channel-labels=url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📈 Key Metrics to Monitor

### Operational Metrics
- **Prediction Latency**: p95 < 2s (Vertex AI predict)
- **API Response Time**: Cached < 300ms, Uncached < 2s
- **Job Success Rate**: > 99%
- **Endpoint Availability**: > 99.9%
- **Cache Hit Rate**: > 80%

### Business Metrics
- **Prediction Freshness**: Max 1 hour old
- **Data Completeness**: 30 rows per prediction run
- **Schema Validation Pass Rate**: 100% (non-negotiable)

### Cost Metrics
- **Vertex AI Cost**: < $130/mo (3 endpoints)
- **BigQuery Cost**: < $20/mo (with ISR caching)
- **Total Monthly Cost**: < $150/mo

---

## 🚨 Alert Response Procedures

### Job Failure
1. Check Cloud Scheduler logs for error
2. Verify BigQuery table exists and is accessible
3. Check Vertex AI endpoint status
4. Verify schema validation passed
5. Manual retry if transient error

### Zero Predictions
1. Check predictor job logs
2. Verify feature assembler ran successfully
3. Check schema validation (may have aborted)
4. Verify endpoints are accessible
5. Check for quota/exceeding limits

### Endpoint Errors
1. Check Vertex AI endpoint health
2. Verify traffic split configuration
3. Check for model version mismatch
4. Review prediction request format
5. Check endpoint logs for details

### Budget Alert
1. Review Vertex AI usage dashboard
2. Check for unexpected endpoint scaling
3. Review BigQuery query costs
4. Verify caching is working (ISR hit rate)
5. Consider custom container optimization (reduce to $40/mo)

---

## 📋 Daily Operations Checklist

### Morning (Market Open)
- [ ] Verify predictor job ran successfully
- [ ] Check predictions_1m has latest timestamp
- [ ] Verify agg_1m_latest refreshed
- [ ] Check endpoint health status
- [ ] Review any overnight alerts

### Afternoon (Mid-Day)
- [ ] Verify cache invalidation working
- [ ] Check API response times
- [ ] Review error rates
- [ ] Verify budget on track

### End of Day
- [ ] Review all alerts from day
- [ ] Verify 24-hour prediction coverage
- [ ] Check cost trends
- [ ] Document any issues

---

## 🔧 Troubleshooting

### Jobs Not Running
- Check Cloud Scheduler job status: `gcloud scheduler jobs describe JOB_NAME`
- Verify service account permissions
- Check job execution logs
- Verify target URL/command is correct

### High Costs
- Review Vertex AI endpoint machine types (should be n1-standard-2)
- Check min_replica_count (should be 1)
- Verify ISR caching hit rate (should be > 80%)
- Review BigQuery query patterns

### Stale Cache
- Verify cache invalidation endpoint is being called
- Check Cloud Scheduler heartbeat job
- Verify revalidate endpoint is accessible
- Check Next.js cache configuration

---

**This monitoring setup ensures operational visibility and rapid response to issues.**

