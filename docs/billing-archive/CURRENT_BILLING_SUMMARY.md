# Current Billing Summary - CBI-V14 Project

## Billing Account
- **Account ID**: 015605-20A96F-2AD992
- **Account Name**: Firebase Payment
- **Status**: Active (Open)

## Recent Spending (Last 30 Days)

### Model Training Costs
- **Total Jobs**: 559 CREATE_MODEL jobs
- **Total Data Processed**: 916.4 GB
- **Estimated Cost**: ~$229,097 USD
  - **Note**: This seems very high - may include:
    - Multiple training attempts
    - Failed/retried jobs
    - All CREATE_MODEL operations (including tests)

### Query Processing Costs
- **Total Jobs**: 13,629 jobs
- **Total Data Processed**: 23.6 GB
- **Estimated Cost**: ~$118 USD
  - First 1TB/month is free for queries
  - Most queries likely fall within free tier

## Daily Breakdown (Recent)

| Date       | Model Training Jobs | GB Processed | Estimated Cost |
|------------|---------------------|-------------|----------------|
| 2025-11-04 | 18                  | 69.0 GB     | ~$17,253       |
| 2025-11-03 | 38                  | 43.3 GB     | ~$10,823       |
| 2025-11-02 | 22                  | 130.9 GB    | ~$32,725       |

## Important Notes

1. **These are ESTIMATES** based on:
   - BigQuery ML Training: $250/TB
   - Actual billing may include:
     - Free tier allowances
     - Discounts
     - Different pricing tiers

2. **To Get ACTUAL Billing:**
   - Visit: https://console.cloud.google.com/billing
   - Or use: `gcloud billing accounts get-iam-policy`

3. **Cost Optimization:**
   - Many jobs may be failed/retried (explaining high job count)
   - Consider using smaller test datasets for development
   - Use dry_run to estimate costs before training

## Retraining Costs (Proposed)

To retrain 1W, 1M, 6M models with 100 iterations:
- **Estimated Cost**: <$0.001 (less than 1 cent)
- **Negligible compared to current spending**


