# Retraining Cost Analysis - 1W, 1M, 6M Models

## Current vs Proposed Configuration

### Model Specifications
| Model | Training Rows | Features | Current Iterations | Proposed Iterations | Data Size (MB) |
|-------|---------------|----------|-------------------|---------------------|----------------|
| 1W    | 1,448        | 275      | 50                | 100                 | ~2.71 MB       |
| 1M    | 1,347        | 274      | 48                | 100                 | ~2.51 MB       |
| 6M    | 1,198        | 257      | 48                | 100                 | ~2.23 MB       |

## BigQuery ML Pricing (2024)

### BOOSTED_TREE_REGRESSOR Pricing
- **Training**: $250 per TB of data processed
- **Model Storage**: $0.02 per GB per month (after first 10 GB free)
- **Prediction**: $5 per TB of data processed

### Data Processing Calculation
- Each iteration processes the full training dataset
- Total data processed = (rows × features × bytes per value × iterations)

### Cost Breakdown

#### 1W Model Retraining
- **Data per iteration**: ~2.71 MB
- **Current training**: 50 iterations = 135.5 MB processed
- **Proposed training**: 100 iterations = 271 MB processed
- **Additional cost**: ~135.5 MB = **~$0.000034** (0.0034 cents)

#### 1M Model Retraining
- **Data per iteration**: ~2.51 MB  
- **Current training**: 48 iterations = 120.5 MB processed
- **Proposed training**: 100 iterations = 251 MB processed
- **Additional cost**: ~130.5 MB = **~$0.000033** (0.0033 cents)

#### 6M Model Retraining
- **Data per iteration**: ~2.23 MB
- **Current training**: 48 iterations = 107 MB processed
- **Proposed training**: 100 iterations = 223 MB processed
- **Additional cost**: ~116 MB = **~$0.000029** (0.0029 cents)

### Total Retraining Costs

**Per Model Retraining:**
- 1W: **~$0.000034** (0.0034 cents)
- 1M: **~$0.000033** (0.0033 cents)
- 6M: **~$0.000029** (0.0029 cents)

**Total for All 3 Models:**
- **~$0.000096** (0.0096 cents) = **Less than $0.001**

### Model Storage Costs
- Current model size: ~1-5 MB per model
- Storage cost: $0.02/GB/month
- **3 models**: ~15 MB = **~$0.0003/month** (essentially free)

## Real Cost Summary

### One-Time Retraining Cost
- **Total cost to retrain all 3 models**: **~$0.0001** (less than 1 cent)
- **Cost per model**: **~$0.00003** (0.003 cents)

### Monthly Storage Cost
- **Model storage**: **~$0.0003/month** (essentially free)

## Cost Comparison: 3M Model (100 iterations)
- 3M model: 100 iterations, ~2.5 MB per iteration = 250 MB processed
- Cost: **~$0.000063** (0.0063 cents)
- **MAPE: 0.70%** (best performance)

## Recommendation

**Cost is negligible** - less than $0.001 total to retrain all 3 models.

**Benefits of retraining:**
- Potential MAPE improvement (3M has 0.70% vs 1.21-1.29% for others)
- Consistent 100 iterations across all models
- Better model performance for production

**Recommendation: Retrain all 3 models with 100 iterations**
- Cost: Essentially free (<$0.001)
- Time: ~10-15 minutes per model
- Potential: Significant MAPE improvement


