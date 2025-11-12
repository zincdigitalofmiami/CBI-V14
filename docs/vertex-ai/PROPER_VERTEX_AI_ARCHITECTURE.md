# Proper Vertex AI Architecture for CBI-V14

**Date:** November 7, 2025  
**Status:** ARCHITECTURAL DESIGN  
**Purpose:** Proper data consolidation strategy leveraging ALL available data

---

## THE REAL DATA SITUATION

### What We Actually Have
- **157 tables** with data across 4 datasets
- **431,740 total rows** of historical data
- **9,213 total columns** (features)
- **45 time series tables** 
- **125 years** of historical data (1900-2025)

### Critical Pre-Computed Assets

**Derived Features Tables (models_v4):**
| Table | Rows | Date Range | Purpose |
|-------|------|------------|---------|
| fundamentals_derived_features | 16,824 | 1900-2025 | Economic fundamentals |
| fx_derived_features | 16,824 | 1900-2025 | FX/currency features |
| monetary_derived_features | 16,824 | 1900-2025 | Monetary policy features |
| volatility_derived_features | 16,824 | 1900-2025 | Volatility indicators |

These tables are **DAILY** and **PRE-COMPUTED**. This is our foundation.

### The Vertex AI Constraint
- **Maximum columns:** 1,000
- **Current features:** 9,213
- **Selection ratio:** 9.2:1 (need to select top 11% of features)

---

## ARCHITECTURAL STRATEGY

### Phase 1: Master Time Series Spine

**Create a single time series spine from 1900-2025 (daily granularity):**

```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.master_time_series_spine` AS
WITH date_spine AS (
  SELECT date
  FROM fundamentals_derived_features
  WHERE date >= '1900-01-01'
  ORDER BY date
)
SELECT 
  date,
  EXTRACT(YEAR FROM date) as year,
  EXTRACT(MONTH FROM date) as month,
  EXTRACT(DAY FROM date) as day,
  EXTRACT(DAYOFWEEK FROM date) as day_of_week,
  -- Trump era flag
  CASE 
    WHEN date >= '2023-01-01' THEN TRUE
    ELSE FALSE
  END as is_trump_era
FROM date_spine
```

**Result:** Single table with 16,824 rows (1900-2025) as the backbone for ALL joins.

---

### Phase 2: Core Feature Integration

**Join pre-computed derived features (already at daily granularity):**

```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.core_features_consolidated` AS
SELECT 
  s.date,
  s.is_trump_era,
  -- Fundamentals (all columns)
  f.*  EXCEPT(date),
  -- FX features (all columns)
  fx.* EXCEPT(date),
  -- Monetary features (all columns)
  m.*  EXCEPT(date),
  -- Volatility features (all columns)
  v.*  EXCEPT(date)
FROM `cbi-v14.models_v4.master_time_series_spine` s
LEFT JOIN `cbi-v14.models_v4.fundamentals_derived_features` f USING(date)
LEFT JOIN `cbi-v14.models_v4.fx_derived_features` fx USING(date)
LEFT JOIN `cbi-v14.models_v4.monetary_derived_features` m USING(date)
LEFT JOIN `cbi-v14.models_v4.volatility_derived_features` v USING(date)
```

**Estimated columns:** ~200-400 (derived features are already computed)

---

### Phase 3: Yahoo Finance Integration

**Add Yahoo Finance data (224 symbols with 30+ indicators each):**

```sql
-- Create pivot of Yahoo data to wide format
CREATE OR REPLACE TABLE `cbi-v14.models_v4.yahoo_features_wide` AS
SELECT 
  date,
  -- Pivot each symbol's indicators into columns
  -- This could be 224 symbols × 7 key indicators = 1,568 columns
  MAX(IF(symbol = 'ZL' AND metric = 'close', value, NULL)) as zl_close,
  MAX(IF(symbol = 'ZL' AND metric = 'volume', value, NULL)) as zl_volume,
  MAX(IF(symbol = 'ZL' AND metric = 'rsi_14', value, NULL)) as zl_rsi_14,
  -- ... repeat for all 224 symbols ...
FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
GROUP BY date
```

**Problem:** This creates 1,568 columns just from Yahoo (224 × 7). Too many.

**Solution:** Select only high-value symbols (top 50 most correlated with ZL)

---

### Phase 4: Feature Selection Strategy

**We have 9,213 potential features but Vertex AI allows only 1,000.**

**Tier 1: Core Features (MUST INCLUDE - ~200 columns)**
- Target variables (ZL prices, targets)
- Date/time features
- All derived features (fundamentals, FX, monetary, volatility)
- VIX, DXY, Fed funds rate
- Soybean-specific fundamentals

**Tier 2: High-Value Correlates (~400 columns)**
- Top 50 correlated symbols from Yahoo Finance (50 × 7 indicators = 350)
- Economic indicators with |correlation| > 0.3
- Weather data (Brazil, Argentina, US)
- China imports, Argentina exports
- RIN prices, biofuel data

**Tier 3: Interaction & Lag Features (~400 columns)**
- VIX × Trump sentiment
- China imports × Tariff rates
- RIN prices × Crush margins
- Lag features: 7d, 14d, 30d, 60d for key variables

**Total:** ~1,000 columns (Vertex AI limit)

---

### Phase 5: Horizon-Specific Targets

**Create 4 horizon-specific datasets:**

```sql
-- 1M Horizon
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_1m` AS
SELECT 
  *,
  LEAD(zl_close, 22) OVER (ORDER BY date) as target_1m  -- 22 trading days
FROM `cbi-v14.models_v4.master_consolidated_features`
WHERE is_trump_era = TRUE  -- Trump era filter
  AND target_1m IS NOT NULL;

-- 3M Horizon  
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_3m` AS
SELECT 
  *,
  LEAD(zl_close, 66) OVER (ORDER BY date) as target_3m  -- 66 trading days
FROM `cbi-v14.models_v4.master_consolidated_features`
WHERE is_trump_era = TRUE
  AND target_3m IS NOT NULL;

-- 6M Horizon
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_6m` AS
SELECT 
  *,
  LEAD(zl_close, 132) OVER (ORDER BY date) as target_6m  -- 132 trading days
FROM `cbi-v14.models_v4.master_consolidated_features`
WHERE is_trump_era = TRUE
  AND target_6m IS NOT NULL;

-- 12M Horizon
CREATE OR REPLACE TABLE `cbi-v14.models_v4.vertex_ai_training_12m` AS
SELECT 
  *,
  LEAD(zl_close, 264) OVER (ORDER BY date) as target_12m  -- 264 trading days
FROM `cbi-v14.models_v4.master_consolidated_features`
WHERE is_trump_era = TRUE
  AND target_12m IS NOT NULL;
```

**Trump era filtering:** 2023-01-01 to 2025-11-06 = ~700 training rows per horizon

---

### Phase 6: Vertex AI Feature Transform Engine

**Let Vertex AI handle final feature selection:**

```python
from google.cloud import aiplatform

# Create Vertex AI dataset from BigQuery
dataset = aiplatform.TabularDataset.create(
    display_name="CBI V14 Vertex – 1M Dataset",
    bq_source='bq://cbi-v14.models_v4.vertex_ai_training_1m',
)

# AutoML with Feature Transform Engine
training_job = aiplatform.AutoMLTabularTrainingJob(
    display_name="CBI V14 Vertex – AutoML 1M",
    optimization_objective="minimize-rmse",
)

model = training_job.run(
    dataset=dataset,
    target_column="target_1m",
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    model_display_name="CBI V14 Vertex – AutoML 1M",
    # Feature Transform Engine will automatically select best features
    budget_milli_node_hours=20000,  # $100 budget
)
```

---

## IMPLEMENTATION PHASES

### Phase 1: Data Consolidation (Week 1)
1. ✅ Create master time series spine
2. ✅ Join derived features tables
3. ✅ Add economic indicators
4. ✅ Add currency data

**Output:** Single table with ~500 columns, 16,824 rows

### Phase 2: Yahoo Finance Integration (Week 1)
1. ✅ Calculate correlations with ZL
2. ✅ Select top 50 most correlated symbols
3. ✅ Pivot to wide format (50 symbols × 7 indicators = 350 columns)
4. ✅ Join to master table

**Output:** Single table with ~850 columns, 16,824 rows

### Phase 3: Additional Features (Week 2)
1. ✅ Add weather data (Brazil, Argentina, US)
2. ✅ Add China imports, Argentina exports
3. ✅ Add RIN prices, biofuel data
4. ✅ Add Trump policy intelligence
5. ✅ Add CFTC positioning

**Output:** Single table with ~950 columns, 16,824 rows

### Phase 4: Interaction & Lag Features (Week 2)
1. ✅ Create interaction terms (VIX × Trump, China × Tariffs, etc.)
2. ✅ Create lag features (7d, 14d, 30d, 60d)
3. ✅ Final feature count: ~1,000 columns

**Output:** Master table with 1,000 columns, 16,824 rows (1900-2025)

### Phase 5: Horizon-Specific Datasets (Week 2)
1. ✅ Create 4 tables with horizon-specific targets
2. ✅ Apply Trump era filter (2023-2025)
3. ✅ Drop rows with NULL targets

**Output:** 4 training tables, ~700 rows each, 1,000 columns

### Phase 6: Vertex AI Training (Week 3)
1. ✅ Register datasets in Vertex AI
2. ✅ Launch AutoML training (4 models, $100 each = $400)
3. ✅ Monitor training progress
4. ✅ Export feature importance
5. ✅ Deploy endpoints

**Output:** 4 production models with endpoints

---

## WHY THIS APPROACH WORKS

### 1. Leverages Pre-Computed Features
- Derived features tables are ALREADY computed (fundamentals, FX, monetary, volatility)
- Don't need to re-compute from scratch
- Saves weeks of feature engineering

### 2. Uses Full Historical Context
- 125 years of data for feature engineering
- Trump era filtering for training (2023-2025)
- Best of both: rich features + regime-specific training

### 3. Respects Vertex AI Constraints
- 1,000 column limit enforced through feature selection
- Feature Transform Engine does final optimization
- Each model gets exactly what it needs

### 4. Scalable & Maintainable
- Master consolidation script can be re-run
- Easy to add new features
- Easy to retrain with new data

### 5. Follows GS Quant / JPMorgan DNA Principles
- Signal packaging (derived features)
- Cross-asset features (FX, commodities, currencies)
- Regime indicators (Trump era, VIX stress)
- Causal features (economic fundamentals)

---

## CRITICAL DIFFERENCES FROM BQML APPROACH

| Aspect | BQML Approach | Vertex AI Approach |
|--------|--------------|-------------------|
| Data Volume | 1,400 rows (2020-2025) | 16,824 rows (1900-2025) for features<br>~700 rows (2023-2025) for training |
| Features | 300-444 columns (random) | 1,000 columns (selected) |
| Feature Engineering | Manual | Automated Feature Transform Engine |
| Training Time | Minutes | Hours (20 hour budget = $100) |
| Feature Selection | None | Automatic top-feature selection |
| Regime Awareness | None | Trump-era filtering |
| Historical Context | 5 years | 125 years |

---

## NEXT IMMEDIATE STEPS

1. **Create master time series spine** (16,824 daily rows from 1900-2025)
2. **Join derived features** (fundamentals, FX, monetary, volatility)
3. **Calculate Yahoo correlations** (identify top 50 symbols)
4. **Build consolidation SQL** (create master table)
5. **Apply Trump era filter** (create training datasets)
6. **Register in Vertex AI** (create TabularDatasets)
7. **Launch training** (4 models × $100 = $400)

---

## ESTIMATED TIMELINE

- **Week 1:** Data consolidation & feature engineering
- **Week 2:** Horizon-specific datasets & validation
- **Week 3:** Vertex AI training & deployment
- **Week 4:** Evaluation, tuning, production deployment

**Total:** 4 weeks to production

---

## SUCCESS CRITERIA

1. ✅ Single master table with 1,000 well-selected features
2. ✅ 4 horizon-specific training tables (1M, 3M, 6M, 12M)
3. ✅ Trump-era filtered datasets (~700 rows each)
4. ✅ All targets non-NULL
5. ✅ All schema validations pass
6. ✅ 4 production models trained and deployed
7. ✅ Performance beats 7.8% MAPE baseline

---

**This is the PROPER Vertex AI architecture that leverages ALL available data.**

