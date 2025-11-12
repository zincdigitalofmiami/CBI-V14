# Day 1 Data Export Manifest
**Complete inventory of all datasets being exported and MLflow experiments**

---

## 📊 8 MLFLOW EXPERIMENT CATEGORIES

### 1. **baselines_statistical**
- **Purpose**: Statistical baseline models
- **Models**: ARIMA, Auto-ARIMA, Prophet, Exponential Smoothing
- **Use Case**: Time series benchmarks, no ML dependencies
- **Training Script**: `src/training/baselines/statistical.py`

### 2. **baselines_tree**
- **Purpose**: Tree-based baseline models
- **Models**: LightGBM DART, XGBoost DART
- **Use Case**: Fast, interpretable, CPU-friendly baselines
- **Training Script**: `src/training/baselines/tree_models.py`

### 3. **baselines_neural**
- **Purpose**: Simple neural network baselines
- **Models**: 1-layer LSTM, 1-layer GRU, Feedforward Dense
- **Use Case**: GPU-accelerated neural benchmarks (FP16, batch≤64)
- **Training Script**: `src/training/baselines/neural_baseline.py`

### 4. **advanced_neural**
- **Purpose**: Advanced neural architectures
- **Models**: 2-layer LSTM/GRU, TCN (Temporal Convolutional Network), CNN-LSTM hybrid
- **Use Case**: Higher capacity models for complex patterns
- **Training Script**: To be created (Day 3)

### 5. **regime_models**
- **Purpose**: Regime-specific specialized models
- **Models**: Crisis model, Bull market model, Bear market model, Normal market model
- **Use Case**: Automatic model switching based on market conditions
- **Training Script**: To be created (Day 3)

### 6. **volatility**
- **Purpose**: Volatility forecasting models
- **Models**: Separate volatility prediction (not price prediction)
- **Use Case**: Uncertainty quantification, confidence intervals
- **Training Script**: To be created (Day 2-3)

### 7. **ensemble**
- **Purpose**: Ensemble meta-learners
- **Models**: Blends multiple models dynamically based on regime
- **Use Case**: Goldman/Citadel-style ensemble (50+ models blended)
- **Training Script**: To be created (Day 5)

### 8. **validation**
- **Purpose**: Walk-forward validation results
- **Models**: Out-of-sample performance tracking
- **Use Case**: True performance metrics (not overfitted)
- **Training Script**: To be created (Day 3)

---

## 📦 DATASETS BEING EXPORTED (12 Total)

### **Primary Training Tables** (6 tables)
**Source**: `cbi-v14.models_v4.*`

1. **production_training_data_1w.parquet**
   - **Table**: `models_v4.production_training_data_1w`
   - **Features**: 290+ features
   - **Target**: `target_1w`
   - **Purpose**: 1-week horizon training
   - **Export Location**: `TrainingData/exports/`

2. **production_training_data_1m.parquet**
   - **Table**: `models_v4.production_training_data_1m`
   - **Features**: 290+ features
   - **Target**: `target_1m`
   - **Purpose**: 1-month horizon training
   - **Export Location**: `TrainingData/exports/`

3. **production_training_data_3m.parquet**
   - **Table**: `models_v4.production_training_data_3m`
   - **Features**: 290+ features
   - **Target**: `target_3m`
   - **Purpose**: 3-month horizon training
   - **Export Location**: `TrainingData/exports/`

4. **production_training_data_6m.parquet**
   - **Table**: `models_v4.production_training_data_6m`
   - **Features**: 290+ features
   - **Target**: `target_6m`
   - **Purpose**: 6-month horizon training
   - **Export Location**: `TrainingData/exports/`

5. **production_training_data_12m.parquet**
   - **Table**: `models_v4.production_training_data_12m`
   - **Features**: 290+ features
   - **Target**: `target_12m`
   - **Purpose**: 12-month horizon training
   - **Export Location**: `TrainingData/exports/`

6. **trump_rich_2023_2025.parquet**
   - **Table**: `models_v4.trump_rich_2023_2025`
   - **Features**: 42 features
   - **Rows**: 782
   - **Purpose**: Trump-era specific training data
   - **Export Location**: `TrainingData/exports/`

### **Historical Full Dataset** (1 table)
**Source**: `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`

7. **historical_full.parquet**
   - **Table**: `forecasting_data_warehouse.soybean_oil_prices`
   - **Time Range**: 125+ years of historical data
   - **Columns**: `date`, `close_price`, `regime` (labeled)
   - **Regime Labels**:
     - `trump_2.0` (2023-01-01+)
     - `trade_war` (2017-2020)
     - `inflation` (2021-2023)
     - `crisis` (2008, 2020-2021)
     - `historical` (pre-2008)
   - **Export Location**: `TrainingData/raw/`

### **Regime-Specific Datasets** (5 tables)
**Source**: Filtered from `models_v4.production_training_data_1m` (has all features)

8. **trump_2.0_2023_2025.parquet**
   - **Date Range**: 2023-01-01 to 2025-12-31
   - **Weight**: ×5000 (highest priority)
   - **Purpose**: Current regime training
   - **Export Location**: `TrainingData/exports/`

9. **trade_war_2017_2019.parquet**
   - **Date Range**: 2017-01-01 to 2020-01-01
   - **Weight**: ×1500
   - **Purpose**: Trade war regime training
   - **Export Location**: `TrainingData/exports/`

10. **inflation_2021_2022.parquet**
    - **Date Range**: 2021-01-01 to 2023-01-01
    - **Weight**: ×1200
    - **Purpose**: Inflation regime training
    - **Export Location**: `TrainingData/exports/`

11. **crisis_2008_2020.parquet**
    - **Date Range**: 2008-2009 OR 2020-2021
    - **Weight**: ×500
    - **Purpose**: Crisis regime training (financial crisis + COVID)
    - **Export Location**: `TrainingData/exports/`

12. **historical_pre2000.parquet**
    - **Date Range**: Before 2000-01-01
    - **Weight**: ×50 (lowest priority)
    - **Purpose**: Long-term historical patterns
    - **Export Location**: `TrainingData/exports/`

---

## ⚠️ POTENTIALLY MISSING DATASETS

### **Additional Tables in `forecasting_data_warehouse`** (Not Currently Exported)

These tables exist in BigQuery but are **NOT** being exported in Day 1:

1. **Commodity Prices** (Related markets):
   - `palm_oil_prices` - Palm oil prices
   - `canola_oil_prices` - Canola oil prices
   - `corn_prices` - Corn prices
   - `crude_oil_prices` - Crude oil prices
   - `gold_prices` - Gold prices
   - `natural_gas_prices` - Natural gas prices

2. **Market Indicators**:
   - `vix_daily` - VIX volatility index
   - `cftc_cot` - CFTC Commitments of Traders
   - `yahoo_finance_enhanced` - Enhanced Yahoo Finance data

3. **News & Sentiment**:
   - `news_intelligence` - News intelligence data
   - `news_advanced` - Advanced news data
   - `social_sentiment` - Social media sentiment
   - `trump_policy_intelligence` - Trump policy tracking

4. **Economic Data**:
   - `economic_indicators` - Economic indicators
   - `currency_data` - FX/currency data
   - `biofuel_prices` - Biofuel/RIN prices

5. **Supply Chain**:
   - `china_soybean_imports` - China import data
   - `argentina_crisis_tracker` - Argentina tracking
   - `industrial_demand_indicators` - Demand indicators

6. **Weather**:
   - `weather_data` - Weather data

### **Why These Aren't Exported**

The current export strategy focuses on:
- ✅ **Training-ready tables** (already feature-engineered)
- ✅ **Complete feature sets** (290+ features already calculated)
- ✅ **Regime-labeled data** (for specialized training)

The `forecasting_data_warehouse` tables are **raw source data** that would need:
- Feature engineering
- Joins with other tables
- Target variable calculation

**These are already incorporated into `production_training_data_*` tables** via the BigQuery feature engineering pipeline.

---

## ✅ VERIFICATION CHECKLIST

Before running Day 1, verify these tables exist in BigQuery:

```sql
-- Check all production training tables
SELECT table_name, row_count
FROM `cbi-v14.models_v4.__TABLES__`
WHERE table_name LIKE 'production_training_data%'
   OR table_name = 'trump_rich_2023_2025'
ORDER BY table_name;

-- Check historical data
SELECT COUNT(*) as row_count
FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`;

-- Verify regime date ranges
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date,
  COUNT(*) as row_count
FROM `cbi-v14.models_v4.production_training_data_1m`
WHERE date >= '2023-01-01' AND date < '2026-01-01';
```

---

## 📋 EXPORT SUMMARY

**Total Files to Export**: 12 Parquet files

**Storage Locations**:
- `TrainingData/exports/` - 11 files (training tables + regime datasets)
- `TrainingData/raw/` - 1 file (historical full)

**Expected Total Size**: ~500MB - 2GB (depending on data volume)

**Export Time**: ~30-45 minutes (depends on BigQuery query performance)

---

## 🎯 RECOMMENDATION

**Current export is COMPLETE** for Day 1-2 baseline training:
- ✅ All 5 horizons covered (1w, 1m, 3m, 6m, 12m)
- ✅ All regime-specific datasets included
- ✅ Full historical data for context
- ✅ Trump-era specific data included

**Additional exports** (from `forecasting_data_warehouse`) can be added later if needed for:
- Custom feature engineering experiments
- Multi-commodity analysis
- News/sentiment integration
- Weather impact modeling

But for **baseline training**, the current 12 exports are sufficient.

---

**Last Updated**: November 12, 2025  
**Export Script**: `scripts/export_training_data.py`  
**Execution**: `./EXECUTE_DAY_1.sh`

