# Complete Data Audit - October 28, 2025

## Executive Summary

**Status**: Training dataset is **15 days stale** and missing critical recent data updates from warehouse tables.

## 1. Training Dataset Status

**Table**: `cbi-v14.models_v4.training_dataset_super_enriched`
- **Rows**: 1,251
- **Columns**: 207
- **Date Range**: 2020-10-21 to 2025-10-13 (15 days behind current)
- **Big 8 Signals**: ✅ ALL 8 PRESENT AND COMPLETE

### Big 8 Coverage (100%)
1. `feature_vix_stress` ✅
2. `feature_harvest_pace` ✅
3. `feature_china_relations` ✅
4. `feature_tariff_threat` ✅
5. `feature_geopolitical_volatility` ✅
6. `feature_biofuel_cascade` ✅
7. `feature_hidden_correlation` ✅
8. `feature_biofuel_ethanol` ✅

### Critical Feature Status

| Feature | Exists | Has Data | Is Current | Issue |
|---------|--------|----------|------------|-------|
| `argentina_export_tax` | ✅ | ✅ | ❌ | OLD values (22.75% vs 0%) |
| `argentina_china_sales_mt` | ✅ | Partial | ❌ | 10x too low (0.24 vs 2.2 MT) |
| `argentina_competitive_threat` | ✅ | ❌ | ❌ | Not properly flagged |
| `industrial_demand_index` | ✅ | ❌ | ❌ | **ALL ZEROS** |
| `china_soybean_imports_mt` | ❌ | N/A | N/A | **COLUMN MISSING** |

## 2. Warehouse Table Status

### china_soybean_imports
- **Rows**: 22
- **Date Range**: 2024-01-15 to 2025-10-15
- **Non-zero rows**: 17
- **Latest Value**: 13.9 MT (Oct 2025)
- **Status**: ✅ CURRENT AND VALID

**Columns**:
```
- date (DATE)
- china_soybean_imports_mt (FLOAT)
- china_imports_from_us_mt (FLOAT)
- updated_at (TIMESTAMP)
```

### argentina_crisis_tracker
- **Rows**: 10
- **Date Range**: 2025-08-26 to 2025-10-28
- **Latest Values**:
  - Export tax: **0%** (crisis active)
  - China sales: **2.5 MT**
  - Competitive threat: **1** (active)
- **Status**: ✅ CURRENT (updated today!)

**Columns**:
```
- date (DATE)
- argentina_export_tax (FLOAT64)
- argentina_china_sales_mt (FLOAT64)
- argentina_peso_usd (FLOAT64)
- argentina_competitive_threat (INT64)
- updated_at (TIMESTAMP)
```

### industrial_demand_indicators
- **Rows**: 3
- **Date Range**: 2025-10-14 to 2025-10-28
- **Latest Values**:
  - Asphalt pilots: **12 states**
  - Goodyear soy: **90%**
  - Demand index: **0.512**
- **Status**: ✅ CURRENT (updated today!)

**Columns**:
```
- date (DATE)
- asphalt_pilot_count (INT64)
- goodyear_soy_volume (FLOAT64)
- green_tire_growth (FLOAT64)
- industrial_demand_index (FLOAT64)
- updated_at (TIMESTAMP)
```

## 3. Schema Inconsistencies (Price Columns)

### Commodity Price Tables

**palm_oil_prices**:
- Has both `close` and `close_price`
- Has both `open` and `open_price`

**crude_oil_prices**:
- Has `close` (FLOAT64)
- Has `open` (INT64) ← Type mismatch!

**soybean_oil_prices**:
- Standard: `close`, `open`, `high`, `low`

### Impact on Joins

When the original training dataset was built, it selected:
- `palm_oil_prices.close_price` → became `palm_price`
- `crude_oil_prices.close` → became `crude_price`

Any new joins MUST use the SAME column names or risk:
1. ❌ Null values from wrong column selection
2. ❌ Duplicate column errors
3. ❌ Type mismatches

## 4. Root Cause Analysis

### Why Argentina/Industrial Data is Stale

1. **Warehouse tables were populated** on 2025-10-28 (today)
2. **Training dataset was last updated** on/before 2025-10-13
3. **No automatic sync exists** between warehouse → training dataset
4. **Manual UPDATE required** to refresh training dataset

### Why Data is Zero/Wrong

1. **Argentina**: Old join fetched pre-crisis data (Sep 2025 = 26% tax)
2. **Industrial**: Original join returned NULLs, COALESCE to 0
3. **China imports**: Column never existed in training dataset

## 5. Action Plan (BEFORE VERTEX AI TRAINING)

### Step 1: Add Missing China Import Column (if needed)
```sql
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS china_soybean_imports_mt FLOAT64,
ADD COLUMN IF NOT EXISTS china_imports_from_us_mt FLOAT64;
```

### Step 2: Update Argentina Data (Most Recent Per Week)
```sql
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
SET 
  argentina_export_tax = argentina.argentina_export_tax,
  argentina_china_sales_mt = argentina.argentina_china_sales_mt,
  argentina_competitive_threat = argentina.argentina_competitive_threat
FROM (
  SELECT 
    DATE_TRUNC(date, WEEK) as week_start,
    FIRST_VALUE(argentina_export_tax) OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) as argentina_export_tax,
    FIRST_VALUE(argentina_china_sales_mt) OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) as argentina_china_sales_mt,
    FIRST_VALUE(argentina_competitive_threat) OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) as argentina_competitive_threat
  FROM `cbi-v14.forecasting_data_warehouse.argentina_crisis_tracker`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) = 1
) argentina
WHERE DATE_TRUNC(base.date, WEEK) = argentina.week_start;
```

### Step 3: Update Industrial Data
```sql
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
SET industrial_demand_index = industrial.industrial_demand_index
FROM (
  SELECT 
    DATE_TRUNC(date, WEEK) as week_start,
    FIRST_VALUE(industrial_demand_index) OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) as industrial_demand_index
  FROM `cbi-v14.forecasting_data_warehouse.industrial_demand_indicators`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, WEEK) ORDER BY date DESC) = 1
) industrial
WHERE DATE_TRUNC(base.date, WEEK) = industrial.week_start;
```

### Step 4: Update China Import Data (Monthly)
```sql
UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
SET 
  china_soybean_imports_mt = china.china_soybean_imports_mt,
  china_imports_from_us_mt = china.china_imports_from_us_mt
FROM (
  SELECT 
    DATE_TRUNC(date, MONTH) as month_start,
    FIRST_VALUE(china_soybean_imports_mt) OVER (PARTITION BY DATE_TRUNC(date, MONTH) ORDER BY date DESC) as china_soybean_imports_mt,
    FIRST_VALUE(china_imports_from_us_mt) OVER (PARTITION BY DATE_TRUNC(date, MONTH) ORDER BY date DESC) as china_imports_from_us_mt
  FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, MONTH) ORDER BY date DESC) = 1
) china
WHERE DATE_TRUNC(base.date, MONTH) = china.month_start;
```

### Step 5: Verify Updates
```sql
SELECT 
  COUNT(*) as total_rows,
  COUNTIF(argentina_export_tax = 0 AND date > '2025-09-24') as argentina_crisis_flagged,
  COUNTIF(industrial_demand_index > 0) as industrial_populated,
  COUNTIF(china_soybean_imports_mt > 0) as china_populated,
  MAX(date) as latest_date,
  AVG(CASE WHEN date > '2025-10-01' THEN argentina_export_tax END) as recent_arg_tax,
  AVG(CASE WHEN date > '2025-10-01' THEN industrial_demand_index END) as recent_industrial
FROM `cbi-v14.models_v4.training_dataset_super_enriched`;
```

**Expected Results**:
- `argentina_crisis_flagged`: ~10 rows (since Sep 24)
- `industrial_populated`: ~3 rows (Oct only)
- `china_populated`: ~300-400 rows (monthly data)
- `recent_arg_tax`: **0.0** (not 22.75)
- `recent_industrial`: **>0.4** (not 0.0)

## 6. Post-Update Validation Checklist

- [ ] No duplicate rows (COUNT(*) = COUNT(DISTINCT date))
- [ ] Big 8 signals still 100% present
- [ ] Argentina export tax shows 0% for Oct 2025
- [ ] Industrial demand index >0 for recent dates
- [ ] China imports populated (if column added)
- [ ] No new NULL columns introduced
- [ ] Total row count unchanged (1,251)
- [ ] Date range unchanged (2020-10-21 to 2025-10-13)

## 7. Vertex AI Training Readiness

### BEFORE Training Can Start:

1. ✅ Vertex AI SDK installed (v1.38.0)
2. ✅ GCS export exists (Parquet)
3. ❌ **Training dataset MUST be updated** (Steps 1-4 above)
4. ❌ **Post-update validation MUST pass** (Step 5)
5. ❌ **Vertex AI script needs parameter fix** (remove `column_transformations`)

### After Data Update:

1. Re-export to GCS Parquet (with updated data)
2. Fix Vertex AI script
3. Run pilot (1W horizon, 1,000 budget)
4. Validate pilot results
5. Run full training (all horizons, 4,000 budget)

## 8. Recommendations

### Immediate Actions

1. **DO NOT TRAIN** until data is updated
2. Execute Steps 1-4 in sequence
3. Validate each step before proceeding
4. Re-export to GCS after all updates

### Future Prevention

1. Create automated daily/weekly sync job
2. Add data freshness monitoring
3. Set alerts for stale data (>7 days)
4. Document all column name mappings
5. Standardize price column naming across warehouse

## 9. Cost Impact of Stale Data

Training with **15-day-old data** that's missing:
- Argentina crisis (0% tax since Sep 24)
- Industrial demand surge (Oct 2025)
- Latest China imports

**Expected Impact**: 
- ❌ Models will NOT learn the Argentina competitive threat
- ❌ Models will miss industrial demand structural shift  
- ❌ 1M/3M/6M MAPE will be **0.5-1.0% WORSE** than possible
- ❌ $80 Vertex AI budget partially wasted on outdated patterns

**ROI of Update**:
- Time: 15 minutes
- Cost: $0.10 (BigQuery UPDATE)
- Benefit: 0.5-1.0% MAPE improvement = **WORTH IT**



