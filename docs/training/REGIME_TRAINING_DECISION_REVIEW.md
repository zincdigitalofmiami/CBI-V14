---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Regime-Based Training Decision Review
**Date**: November 7, 2025  
**Purpose**: Clarify regime weighting decisions, implementation status, and applicability

---

## Key Questions Answered

### 1. Are We Doing Regime-Based Training?

**Status**: ✅ **PLANNED but NOT YET IMPLEMENTED**

**Evidence**:
- **Documentation**: `docs/vertex-ai/REGIME_BASED_TRAINING_STRATEGY.md` exists (comprehensive strategy)
- **SQL Script**: `bigquery-sql/vertex-ai/03_add_regime_weights_to_production.sql` exists (implementation ready)
- **Current Tables**: `production_training_data_1m` does NOT have `training_weight` or `market_regime` columns
- **Vertex AI Plan**: VERTEX_AI_TRUMP_ERA_PLAN.md includes regime weighting in Phase 2.3.3

**Decision**: Regime-based training is **planned for Vertex AI AutoML**, not yet implemented in production tables.

---

### 2. Did We Decide on Final Regimes and Weighting?

**YES - Final Regimes Defined** (from `REGIME_BASED_TRAINING_STRATEGY.md`):

| Regime | Date Range | Weight | Rationale |
|--------|-----------|--------|-----------|
| **Trump 2.0 Era** | 2023-01-01 to 2025-11-06 | **5,000** | Current regime - MAXIMUM emphasis |
| **Trade War Era** | 2017-01-01 to 2019-12-31 | **1,500** | Most similar to current - critical for learning tariff impacts |
| **Inflation Era** | 2021-01-01 to 2022-12-31 | **1,200** | Recent inflation dynamics - relevant for substitution effects |
| **COVID Crisis** | 2020-01-01 to 2020-12-31 | **800** | Supply chain disruption patterns |
| **Financial Crisis** | 2008-01-01 to 2009-12-31 | **500** | Extreme volatility learning |
| **Commodity Crash** | 2014-01-01 to 2016-12-31 | **400** | Dollar surge patterns |
| **QE/Supercycle** | 2010-01-01 to 2013-12-31 | **300** | Commodity boom dynamics |
| **Pre-Crisis** | 2000-01-01 to 2007-12-31 | **100** | Baseline patterns |
| **Historical** | Pre-2000 | **50** | Pattern learning only |

**Topic-Based Multipliers** (in addition to date-based weights):
- **Trump Effects**: ×2.0 (when `trump_sentiment_score > 0.7`)
- **Tariffs**: ×1.5 (when `tariff_rate > 0.25`)
- **Inflation Effects**: ×1.4 (when `cpi_yoy > 0.05`)
- **Trade Wars**: ×1.3 (when `china_relations_score < -0.5`)
- **Trade Developments**: ×1.2 (when `new_trade_deals = TRUE`)

**Final Weight Calculation**:
```sql
final_weight = base_weight * topic_multiplier
```

**Example**: Trump 2.0 era (base 5,000) with active tariffs (×1.5) = 7,500 final weight

---

### 3. Was This Created to Meet 1,000 Column Limit?

**YES - Partially Correct**

**The 1,000 Column Limit**:
- **Source**: Vertex AI AutoML requirement (NOT a general ML requirement)
- **Documentation**: "Columns: 3 to 1,000" per VERTEX_AI_TRUMP_ERA_PLAN.md
- **Discovery**: Found when planning Vertex AI training (had 9,213 potential features)

**Why Regime Weighting Was Created**:
1. **Initial Problem**: Had 9,213 features but Vertex AI allows only 1,000
2. **First Solution**: Feature selection (reduce to top 1,000)
3. **Second Problem**: Only 700 rows in Trump era (2023-2025) - too small for robust training
4. **Regime Solution**: Use ALL 125 years (16,824 rows) with intelligent weighting
   - Trump 2.0 gets 5,000 weight (50-100x emphasis)
   - Historical data gets 50-500 weight (pattern learning)
   - Result: Large dataset (16,824 rows) with Trump era emphasis

**Key Insight**: Regime weighting solves TWO problems:
- ✅ Uses all historical data (not just 700 Trump-era rows)
- ✅ Emphasizes relevant periods (Trump 2.0 gets 50x weight)
- ✅ Still respects 1,000 column limit (feature selection still needed)

---

### 4. Does This Apply to Mac Training?

**NO - Regime Weighting is Vertex AI Specific**

**Why**:
1. **1,000 Column Limit**: This is a **Vertex AI AutoML requirement**, NOT a general ML requirement
2. **TensorFlow/Keras**: No hard column limit (can use all features)
3. **Mac Training**: Can use all 9,213 features if desired (limited by memory, not hard limit)
4. **Weight Column**: Vertex AI has built-in `weight_column` parameter - TensorFlow doesn't have this

**Mac Training Approach**:
- **No Column Limit**: Can use all features (or select top features based on correlation/importance)
- **No Weight Column**: TensorFlow doesn't have built-in weight column
- **Alternative Approaches**:
  - **Sample Weighting**: Use `sample_weight` parameter in Keras (similar concept)
  - **Data Filtering**: Filter to relevant periods (Trump era only)
  - **Class Weights**: Not applicable (regression, not classification)
  - **Custom Loss**: Weighted loss function that emphasizes recent/Trump-era data

**Recommendation for Mac Training**:
- **Option A**: Train on Trump era only (2023-2025, ~700 rows) - simpler, focused
- **Option B**: Train on all data with custom weighted loss function - more complex, uses all history
- **Option C**: Train on all data, no weighting - simplest, let model learn naturally

---

## Implementation Status

### Vertex AI Regime Weighting

**Status**: ✅ **PLANNED, NOT IMPLEMENTED**

**Files**:
- ✅ `docs/vertex-ai/REGIME_BASED_TRAINING_STRATEGY.md` - Strategy document
- ✅ `bigquery-sql/vertex-ai/03_add_regime_weights_to_production.sql` - Implementation script
- ❌ `vertex_ai_training_1m` table - Does NOT exist yet (would have `training_weight` column)
- ❌ `production_training_data_1m` - Does NOT have `training_weight` column

**What Needs to Happen**:
1. Create `vertex_ai_training_*_base` tables (cleaned, 1,000 features, no weights)
2. Run `03_add_regime_weights_to_production.sql` to add weights
3. Create final `vertex_ai_training_*` tables (WITH weights, ready for Vertex AI)

### BQML DART Model (Trump-Era)

**Status**: ❌ **NO REGIME WEIGHTING**

**Current Approach**: 
- Uses `trump_rich_2023_2025` table (2023-2025 only, 732 rows)
- No regime weighting (only Trump era data)
- No `training_weight` column
- BQML doesn't support weight columns (only Vertex AI AutoML does)

**Why No Regime Weighting**:
- BQML (BigQuery ML) doesn't have `weight_column` parameter
- Only Vertex AI AutoML supports this feature
- Trump-era model is focused on 2023-2025 data only (no historical data)

---

## Summary Table

| Approach | Regime Weighting? | Column Limit | Weight Column Support |
|----------|------------------|--------------|---------------------|
| **Vertex AI AutoML** | ✅ YES (planned) | 1,000 (hard limit) | ✅ Built-in `weight_column` |
| **BQML DART** | ❌ NO | No hard limit | ❌ Not supported |
| **Mac Training (TensorFlow)** | ⚠️ Optional | No hard limit | ⚠️ Custom (sample_weight) |

---

## Recommendations

### For Vertex AI Training
1. **Implement Regime Weighting**: Use the defined regimes and weights
2. **Create Weighted Tables**: Run `03_add_regime_weights_to_production.sql`
3. **Use All Historical Data**: 16,824 rows with intelligent weighting
4. **Respect 1,000 Column Limit**: Feature selection still required

### For BQML DART Model (Trump-Era)
1. **No Regime Weighting**: BQML doesn't support it
2. **Focus on Trump Era**: 2023-2025 data only (732 rows)
3. **No Column Limit**: Can use all 58 features (well within BQML limits)

### For Mac Training (Neural Pipeline)
1. **No Regime Weighting Required**: No 1,000 column limit
2. **Options**:
   - **Simple**: Train on Trump era only (2023-2025)
   - **Advanced**: Custom weighted loss function for historical emphasis
   - **Natural**: Train on all data, let model learn patterns
3. **Recommendation**: Start simple (Trump era only), add weighting later if needed

---

## Key Takeaways

1. **Regime Weighting**: ✅ Planned for Vertex AI, NOT implemented yet
2. **Final Regimes**: ✅ Defined (9 regimes, weights 50-5,000)
3. **1,000 Column Limit**: ✅ Vertex AI requirement (NOT general ML)
4. **Mac Training**: ❌ No regime weighting needed (no column limit, optional custom weighting)

**Bottom Line**: Regime weighting is a Vertex AI-specific solution to use all historical data while emphasizing Trump 2.0 era. Mac training doesn't need this - can use all features and all data without weighting (or add custom weighting if desired).

