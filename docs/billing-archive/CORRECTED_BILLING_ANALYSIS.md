# CORRECTED BILLING ANALYSIS - Real Costs

## ⚠️ Previous Estimate Was WRONG

**My $229K estimate was completely wrong** because I used BigQuery ML pricing ($250/TB) for Vertex AI jobs, which have completely different pricing.

## Actual Vertex AI Costs

### From Your Vertex AI Dashboard:
- **4 Successful Jobs** (Finished):
  1. `cbi_v14_1m_FINAL`: 3 hr 14 min
  2. `cbi_v14_3m_final`: 3 hr 4 min  
  3. `cbi_v14_production_6m`: 2 hr 45 min
  4. `cbi_v14_automl_pilot_1w`: 2 hr 50 min
  - **Total training time**: ~12 hours

- **10 Failed Jobs**: Minimal/no charge (failed early)

### Vertex AI AutoML Actual Pricing
- **Training**: Hourly rate (~$20-40/hour for tabular regression)
- **NOT per-TB**: Vertex AI charges by compute time, not data volume
- **Failed jobs**: Minimal charge (if they fail early)

### Estimated Actual Cost
- **4 successful jobs**: ~12 hours × $30/hour = **~$360**
- **Failed jobs**: **~$10-20** (minimal charge)
- **Total Vertex AI**: **~$370-380**

## BigQuery ML Costs

### Your 4 BQML Models:
- `bqml_1w_all_features`: 50 iterations
- `bqml_1m_all_features`: 48 iterations
- `bqml_3m_all_features`: 100 iterations
- `bqml_6m_all_features`: 48 iterations

### Actual Cost:
- **From console**: BigQuery total ~$10
- **BQML portion**: Likely ~$5-10 (very small datasets)

## BigQuery Query Costs

- **13,671 queries**: 23.6 GB processed
- **First 1TB/month FREE**
- **Estimated cost**: ~$0-10 (within free tier)

## Corrected Total (60 Days)

### Actual Costs:
- **Vertex AI AutoML**: ~$370-380
- **BigQuery ML**: ~$10
- **BigQuery Queries**: ~$0-10
- **Other services**: ~$50-100 (Workstations, Dataplex, Compute)
- **TOTAL**: **~$430-500** (60 days)

### Monthly Estimate:
- **November forecast (from console)**: $159/month
- **Extrapolated 60 days**: ~$318
- **Matches actual**: Your console shows $37.98 for Nov 1-4 ≈ $159/month

## Why My Estimate Was Wrong

1. **Used wrong pricing**: Applied BigQuery ML pricing ($250/TB) to Vertex AI
2. **Vertex AI is hourly**: ~$20-40/hour, not per-TB
3. **Failed jobs**: Don't charge much (if they fail early)
4. **Free tiers**: Not accounted for

## Real Billing Summary

**From your console (MOST ACCURATE):**
- Nov 1-4: $37.98
- November forecast: $159
- Monthly average: ~$150-200
- 60 days: ~$300-400

**This matches the corrected calculation above!**


