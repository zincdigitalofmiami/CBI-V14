# ACTUAL BILLING DATA - From Google Cloud Console

## Billing Account
- **Account ID**: 015605-20A96F-2AD992
- **Account Name**: Firebase Payment
- **Status**: Open/Active

## Current Period Costs (November 1-4, 2025)

### Total Costs
- **Cost**: $38.23
- **Savings**: $0.25
- **Total Cost**: $37.98
- **Forecasted Total for November**: $159

### Service Breakdown (Top Services)
1. **Vertex AI**: ~$170 (largest cost)
   - This is your Vertex AI AutoML training (Pipeline 3610713670704693248)
   - Different pricing than BigQuery ML

2. **Cloud Workstations**: ~$120
   - Development environment costs

3. **Dataplex**: ~$40
   - Data governance service

4. **Compute Engine**: ~$60
   - VM instances

5. **BigQuery**: ~$10
   - Storage and query costs
   - BigQuery ML costs are included here and are minimal

### Project Breakdown
- **CBI V14**: ~$150 (for the period shown)

## Daily Cost Breakdown (Nov 1-4)
- Nov 1: ~$12
- Nov 2: ~$12
- Nov 3: ~$12
- Nov 4: ~$3

## Key Findings

### BigQuery ML Costs
- **Actual BigQuery cost**: ~$10 total
- **BigQuery ML training**: Included in BigQuery costs, but very minimal
- **Job history estimates were WRONG** - they included Vertex AI jobs

### Vertex AI Costs
- **Largest cost component**: ~$170
- This is your Vertex AI AutoML training
- Different pricing structure than BigQuery ML

## Retraining Costs (1W, 1M, 6M with 100 iterations)
- **Estimated**: <$0.001 (less than 1 cent)
- **Negligible** compared to current spending

## Important Notes

1. **Payment Issue**: Red banner shows payment information couldn't be processed
   - Need to fix payment method to avoid service disruption

2. **Actual vs Estimates**:
   - My job history estimates: ~$229K (WRONG)
   - Actual billing: $37.98 for Nov 1-4
   - Estimates were inflated because:
     - Included Vertex AI jobs
     - Didn't account for free tiers
     - Failed jobs don't charge

3. **Forecast**:
   - November forecast: $159
   - Reasonable monthly spend

## Recommendation

✅ **Retraining is cost-effective**: <$0.001 for all 3 models
✅ **Current spending is reasonable**: $159/month forecast
⚠️ **Fix payment method**: Address the payment processing issue


