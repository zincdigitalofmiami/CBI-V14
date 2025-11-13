# 📋 REBUILD PRODUCTION TABLES - ASSESSMENT
**Date**: November 12, 2025  
**Status**: ⏳ READY TO EXECUTE

---

## 🎯 OBJECTIVE

Rebuild all `production_training_data_*` tables to incorporate the newly backfilled historical data (2000-2025).

---

## 📊 CURRENT STATE

### Production Training Tables
All currently limited to 2020-2025:
- `production_training_data_1w`: 1,404 rows
- `production_training_data_1m`: 1,404 rows
- `production_training_data_3m`: 1,404 rows
- `production_training_data_6m`: 1,404 rows
- `production_training_data_12m`: 1,404 rows

### Source Data Now Available
After today's backfill (2000-2025):
- Soybean Oil: 6,057 rows ✅
- Soybeans: 15,708 rows ✅
- Corn: 15,623 rows ✅
- Wheat: 15,631 rows ✅
- Crude Oil: 10,859 rows ✅
- Gold: 11,555 rows ✅
- And 7 more commodities...

---

## ⚠️ CONSIDERATIONS

### 1. Feature Engineering
The production tables have 290+ engineered features including:
- Moving averages (7d, 30d, 90d, etc.)
- Volatility measures
- Correlation matrices
- Technical indicators
- Seasonal adjustments

**Issue**: Some features require historical context (e.g., 200-day MA needs 200 days of history).

### 2. Missing Data Handling
Not all features have 2000-2025 coverage:
- ✅ Commodities: Now complete
- ⚠️ Economic indicators: Partial
- ❌ CFTC COT: Only 86 rows
- ❌ China imports: Only 22 rows
- ❌ News/sentiment: Only recent

**Strategy**: Use forward-fill or exclude features with <50% coverage.

### 3. Target Variable Creation
Each horizon needs different target calculations:
- 1w: 7-day ahead price
- 1m: 30-day ahead price
- 3m: 90-day ahead price
- 6m: 180-day ahead price
- 12m: 365-day ahead price

**Note**: Will lose last N days of data for each horizon.

---

## 📝 REBUILD STRATEGY

### Option 1: Full Historical Rebuild (Recommended)
**Pros**:
- Maximum training data
- Complete regime coverage
- Best for regime detection

**Cons**:
- Some features will be NULL pre-2020
- Computational cost higher
- May need feature selection

**SQL Approach**:
```sql
-- Start from 2000-01-01
-- Use COALESCE for missing features
-- Forward-fill where appropriate
```

### Option 2: Balanced Rebuild (2010-2025)
**Pros**:
- Better feature completeness
- Still covers major regimes
- Cleaner dataset

**Cons**:
- Misses 2008 crisis
- Less historical validation

### Option 3: Incremental (Keep 2020+, Add Historical)
**Pros**:
- Preserves existing
- Adds historical for backtesting
- Two-tier approach

**Cons**:
- Complex implementation
- Inconsistent coverage

---

## 🔧 IMPLEMENTATION PLAN

### Step 1: Analyze Feature Coverage
```sql
-- Check which features have data back to 2000
-- Identify gaps and missing periods
-- Decide on minimum coverage threshold
```

### Step 2: Update Base SQL
Location: `config/bigquery/bigquery-sql/PRODUCTION_HORIZON_SPECIFIC/`
- Modify date range to 2000-01-01
- Add NULL handling for sparse features
- Update joins to handle missing data

### Step 3: Test One Horizon First
Start with `production_training_data_1m`:
1. Backup existing table
2. Run rebuild with historical data
3. Validate feature quality
4. Check for NULL proliferation

### Step 4: Deploy All Horizons
If test succeeds:
1. Rebuild all 5 horizons
2. Validate row counts
3. Check feature distributions
4. Update documentation

---

## 📊 EXPECTED OUTCOMES

### Row Count Estimates
Based on soybean oil (core target):
- Current: ~1,404 rows per table
- Expected: ~6,000 rows per table
- Increase: ~327%

### Feature Quality
- **Good** (>80% complete): Prices, volumes, technical indicators
- **Moderate** (50-80%): Economic indicators, weather
- **Poor** (<50%): CFTC, China imports, news

### Training Impact
- **BQML**: Can retrain immediately with more data
- **Neural**: Need to handle NULLs carefully
- **Ensemble**: May need feature selection
- **SHAP**: Better importance with full history

---

## ⚡ QUICK WINS

Before full rebuild, these would help immediately:
1. Create historical-only tables for backtesting
2. Add date range parameters to training scripts
3. Create regime-filtered views
4. Build feature completeness report

---

## 🚨 RISKS

1. **NULL Explosion**: Too many missing values in early years
   - Mitigation: Feature selection, forward-fill

2. **Computation Cost**: 4x more data to process
   - Mitigation: Incremental updates, partitioning

3. **Model Degradation**: If features are too sparse
   - Mitigation: Test thoroughly, A/B comparison

4. **Breaking Changes**: Existing pipelines expect certain row counts
   - Mitigation: Version tables, update gradually

---

## ✅ RECOMMENDATION

**Proceed with Option 1: Full Historical Rebuild**

Reasons:
1. Maximizes value of backfilled data
2. Enables regime detection and crisis modeling
3. Provides full backtesting capability
4. One-time effort with lasting benefits

**Next Action**: Create and test rebuild SQL for `production_training_data_1m` first.

---

**Assessment Complete**: November 12, 2025 17:35 UTC  
**Recommendation**: Full rebuild with 2000-2025 data  
**Priority**: HIGH - Enables all advanced modeling  
**Estimated Time**: 2-3 hours for all tables