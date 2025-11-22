# Current Billing Charges & Alerts Setup

**Date:** November 20, 2025  
**Project:** cbi-v14  
**Billing Account:** 015605-20A96F-2AD992 (Firebase Payment)

---

## 💰 CURRENT CHARGES (November 2025)

### Estimated Charges (Based on Your Bill)

**Current Date:** November 20, 2025  
**Days into month:** 20 days

### Scenario 1: Resources Ran for Full Month
**Total: $308.35**

| Service | Monthly Cost | Estimated (20 days) |
|---------|--------------|---------------------|
| Cloud SQL | $139.87 | ~$93.25 |
| Cloud Workstations | $91.40 | ~$60.93 |
| Compute Engine | $33.26 | ~$22.17 |
| Vertex AI | $24.80 | ~$16.53 |
| Networking | $17.38 | ~$11.59 |
| Dataplex | $1.31 | ~$0.87 |
| BigQuery | $0.28 | ~$0.19 |
| Artifact Registry | $0.05 | ~$0.03 |
| **TOTAL** | **$308.35** | **~$205.56** |

### Scenario 2: Resources Deleted Mid-Month (~10 days)
**Total: ~$102.78**

If resources were deleted around November 10:
- Cloud SQL: ~$46.62
- Cloud Workstations: ~$30.47
- Compute Engine: ~$11.09
- Vertex AI: ~$8.27
- Networking: ~$5.79
- Others: ~$1.54
- **Total: ~$102.78**

### Scenario 3: Resources Deleted Recently (~17 days)
**Total: ~$174.73**

If resources were deleted around November 3:
- Cloud SQL: ~$79.26
- Cloud Workstations: ~$51.79
- Compute Engine: ~$18.85
- Vertex AI: ~$14.05
- Networking: ~$9.85
- Others: ~$0.93
- **Total: ~$174.73**

---

## 📊 EXACT CHARGES

**To get EXACT charges, check GCP Console:**

1. Go to: https://console.cloud.google.com/billing/015605-20A96F-2AD992/reports
2. Filter by:
   - Project: `cbi-v14`
   - Date range: November 1-20, 2025
3. View breakdown by service

**Or use BigQuery billing export (if enabled):**
```sql
SELECT 
  service.description,
  sku.description,
  SUM(cost) as total_cost,
  COUNT(*) as usage_events
FROM `billing_export.gcp_billing_export_v1_XXXXX`
WHERE project.id = 'cbi-v14'
  AND usage_start_time >= '2025-11-01'
  AND usage_start_time < '2025-11-21'
GROUP BY service.description, sku.description
ORDER BY total_cost DESC
```

---

## 🛡️ BILLING ALERTS SETUP

### ✅ Alerts Created

I've created **3 budget alerts** for your project:

1. **CBI-V14 Critical Alert ($5)**
   - Alerts at: $2.50 (50%), $4.50 (90%), $5.00 (100%)
   - Purpose: Early warning for unexpected costs

2. **CBI-V14 Warning Alert ($10)**
   - Alerts at: $9.00 (90%), $10.00 (100%)
   - Purpose: Secondary warning if costs exceed $5

3. **CBI-V14 Emergency Alert ($20)**
   - Alerts at: $20.00 (100%)
   - Purpose: Emergency notification if costs spike

### 📧 Set Up Email Notifications

**To receive email alerts:**

1. Go to: https://console.cloud.google.com/billing/015605-20A96F-2AD992/budgets
2. Click on each budget:
   - "CBI-V14 Critical Alert ($5)"
   - "CBI-V14 Warning Alert ($10)"
   - "CBI-V14 Emergency Alert ($20)"
3. Click **"Edit notifications"**
4. Add your email address: `zinc@zincdigital.co`
5. Click **"Save"**

**You'll receive emails when:**
- Costs reach $2.50 (50% of $5 budget)
- Costs reach $4.50 (90% of $5 budget)
- Costs reach $5.00 (100% of $5 budget)
- Costs reach $9.00 (90% of $10 budget)
- Costs reach $10.00 (100% of $10 budget)
- Costs reach $20.00 (100% of $20 budget)

---

## 📈 EXPECTED FUTURE COSTS

### After Resources Deleted

**Expected monthly cost: ~$1.59/month**

| Service | Cost |
|---------|------|
| BigQuery Storage | $0.01/month |
| BigQuery Queries | $1.53/month |
| Artifact Registry | $0.05/month |
| **TOTAL** | **~$1.59/month** |

**Savings:** $306.76/month (99.5% reduction)

---

## ✅ VERIFICATION

### Check Budgets Are Active

```bash
# List budgets
gcloud billing budgets list \
  --billing-account=015605-20A96F-2AD992 \
  --format="table(displayName,budgetAmount.specifiedAmount.units,thresholdRules[].percent)"
```

### Check Current Costs

```bash
# Run billing analysis
python3 scripts/analysis/get_current_billing.py
```

### Monitor in Console

- Budgets: https://console.cloud.google.com/billing/015605-20A96F-2AD992/budgets
- Reports: https://console.cloud.google.com/billing/015605-20A96F-2AD992/reports

---

## 🎯 SUMMARY

### Current Charges (November 2025)
- **Estimated:** $102.78 - $205.56 (depending on when resources were deleted)
- **Check GCP Console for exact amount**

### Alerts Setup
- ✅ **3 budgets created** ($5, $10, $20)
- ⚠️ **Email notifications need to be configured** (see instructions above)

### Future Costs
- **Expected:** ~$1.59/month (BigQuery only)
- **Alerts will notify you** if costs exceed thresholds

---

**Next Steps:**
1. ✅ Check GCP Console for exact current charges
2. ✅ Set up email notifications for budgets
3. ✅ Monitor next billing cycle (should be ~$1.59/month)
4. ✅ Verify alerts work by checking budget status

---

**Last Updated:** November 20, 2025  
**Status:** ✅ Budgets created, email notifications pending









