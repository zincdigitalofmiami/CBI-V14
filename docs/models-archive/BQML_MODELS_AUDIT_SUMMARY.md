# BigQuery ML Models - Executive Summary

**Generated:** November 4, 2025  
**Total Models Audited:** 24  
**Dataset:** `cbi-v14.models_v4`

## Key Findings

### Model Performance Summary

| Category | Count | Status |
|----------|-------|--------|
| **Production Ready** (Excellent metrics, recent) | 6 | ✅ USE |
| **Good Performance** (Good metrics, minor issues) | 11 | ✅ USE |
| **Review Needed** (High errors, poor metrics, or missing evaluations) | 7 | ⚠️ REVIEW |

### Top Performing Models (Best Metrics)

1. **bqml_1w** - 1 Week horizon
   - MAE: 0.3769 | MAPE: 0.74% | R²: 0.9978
   - Training: 1,448 rows | Created: Today
   - ⚠️ 37 training errors (but final model works)

2. **bqml_3m_all_features** - 3 Month horizon
   - MAE: 0.3704 | MAPE: 0.70% | R²: 0.9977
   - Training: 1,329 rows | Created: Today

3. **bqml_1m** - 1 Month horizon
   - MAE: 0.3758 | MAPE: 0.72% | R²: 0.9973
   - Training: 1,347 rows | Created: Today

4. **bqml_1w_all_features** - 1 Week horizon
   - MAE: 0.6393 | MAPE: 1.21% | R²: 0.9956
   - Training: 1,448 rows | Created: Today

5. **bqml_6m_all_features** - 6 Month horizon
   - MAE: 0.6563 | MAPE: 1.21% | R²: 0.9943
   - Training: 1,198 rows | Created: Today

6. **bqml_1m_all_features** - 1 Month horizon
   - MAE: 0.6969 | MAPE: 1.29% | R²: 0.9943
   - Training: 1,347 rows | Created: Today

### Models by Type

#### BOOSTED_TREE_REGRESSOR (15 models)
- **Purpose:** Primary forecasting models
- **Status:** Most are production-ready with excellent metrics
- **Best:** bqml_1w, bqml_3m_all_features, bqml_1m

#### ARIMA_PLUS (8 models)
- **Purpose:** Time series baselines
- **Status:** Cannot use ML.EVALUATE/ML.PREDICT (must use ML.FORECAST)
- **Note:** Recent models, but evaluation requires different approach

#### DNN_REGRESSOR (2 models)
- **Purpose:** Neural network alternatives
- **Status:** Recent models, but no evaluation metrics available
- **Note:** Need to evaluate separately

### Critical Issues Found

#### 1. Training Errors (Common Patterns)

**NULL Column Errors:**
- `news_article_count` - All NULLs (multiple models)
- `social_sentiment_volatility` - All NULLs
- `treasury_10y_yield` - All NULLs (some models)
- `trump_*` columns - All NULLs (6M models)

**Impact:** These errors occurred during training attempts but final models were created successfully after excluding these columns.

**Recommendation:** Models that successfully trained are still credible. The errors show failed training attempts that were corrected.

#### 2. Baseline Models (Poor Performance)

**baseline_boosted_tree_*_v14_FINAL** models:
- MAE: 3.65-6.72 (high)
- MAPE: 8.42-16.61% (poor)
- R²: 0.30-0.71 (moderate to poor)
- **Verdict:** NOT recommended for production use

**Why they exist:** These are older baseline models. The newer `bqml_*` models far outperform them.

#### 3. Models Without Evaluation

**Models needing evaluation:**
- `bqml_1m_mean` - No evaluation metrics
- `bqml_3m_mean` - No evaluation metrics  
- `bqml_6m_mean` - No evaluation metrics
- `zl_baseline_clean_1w` - No evaluation metrics
- All ARIMA models - Need ML.FORECAST evaluation
- All DNN models - Need evaluation

### Models Currently in Use

**Actively referenced in codebase:**

1. **bqml_1w** - 62 file references
2. **bqml_1w_all_features** - 19 file references
3. **bqml_1m_all_features** - 9 file references
4. **bqml_3m_all_features** - 8 file references
5. **bqml_6m_all_features** - 8 file references

**Production endpoints (from VERTEX_AI_LIVE.txt):**
- Vertex AI models are used in dashboard (NOT these BQML models)
- BQML models appear to be for evaluation/backup

### Recommendations

#### ✅ USE THESE MODELS (Production Ready)

1. **bqml_1w** - Best 1W model (0.74% MAPE)
2. **bqml_1m** - Best 1M model (0.72% MAPE)
3. **bqml_3m_all_features** - Best 3M model (0.70% MAPE)
4. **bqml_6m_all_features** - Best 6M model (1.21% MAPE)
5. **bqml_1w_all_features** - Alternative 1W (1.21% MAPE)
6. **bqml_1m_all_features** - Alternative 1M (1.29% MAPE)

#### ⚠️ REVIEW BEFORE USE

1. **baseline_boosted_tree_*_v14_FINAL** - Poor metrics, high errors
2. **bqml_*_mean** models - No evaluation metrics available
3. **zl_baseline_clean_1w** - No evaluation metrics

#### 📊 EVALUATE SEPARATELY

1. **All ARIMA models** - Use ML.FORECAST instead of ML.PREDICT
2. **All DNN models** - Need proper evaluation

### Why Models Are/Are Not Used

#### Used Models
- **bqml_*_all_features**: High performance, recent training, actively referenced
- **bqml_1w, bqml_1m**: Excellent metrics, production-ready
- **ARIMA models**: Used in ensemble approaches (v4_model_predictions.py)

#### Not Used (Orphaned)
- **baseline_boosted_tree_*_v14_FINAL**: Poor performance, superseded by better models
- **bqml_*_mean**: Likely experimental, no evaluation metrics
- **zl_baseline_clean_1w**: No clear usage pattern

### Training Data Quality

**All production models have:**
- ✅ Sufficient training data (1,198-1,448 rows)
- ✅ Recent training (0-7 days old)
- ✅ Good date coverage (2020-2025)
- ⚠️ Some NULL column issues (handled by exclusion)

### Future Credibility Assessment

#### High Credibility (Can Use Now)
- All `bqml_*_all_features` models
- All `bqml_1w`, `bqml_1m`, `bqml_3m`, `bqml_6m` (without _all_features suffix)

#### Medium Credibility (Review First)
- ARIMA models (need ML.FORECAST evaluation)
- DNN models (need evaluation)
- `bqml_*_mean` models (experimental, no metrics)

#### Low Credibility (Avoid)
- `baseline_boosted_tree_*_v14_FINAL` (poor performance)
- Models with >10% MAPE or R² < 0.5

### Cost Implications

**Storage:** All models stored in BigQuery (minimal cost)  
**Inference:** ML.PREDICT calls are billed per query  
**Recommendation:** Use production models only to minimize costs

### Next Steps

1. ✅ **Evaluate ARIMA models** using ML.FORECAST
2. ✅ **Evaluate DNN models** using ML.EVALUATE
3. ✅ **Test bqml_*_mean models** for performance
4. ⚠️ **Archive or delete** baseline_boosted_tree_*_v14_FINAL models
5. 📊 **Compare** BQML models vs Vertex AI models for production

---

**Full Report:** See `docs/BQML_MODELS_COMPLETE_AUDIT.md`  
**Raw Data:** See `docs/BQML_MODELS_AUDIT_DATA.json`

