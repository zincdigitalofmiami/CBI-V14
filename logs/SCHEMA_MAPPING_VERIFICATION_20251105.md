# Schema Mapping Verification - New Scrapers
**Date:** November 5, 2025  
**Status:** DRY RUN - Schema Verification Only

---

## 📊 EXISTING SCHEMAS

### 1. `forecasting_data_warehouse.biofuel_prices`
```sql
date: DATETIME
symbol: STRING
close: FLOAT
open: FLOAT
high: FLOAT
low: FLOAT
volume: FLOAT
source_name: STRING
confidence_score: FLOAT
ingest_timestamp_utc: TIMESTAMP
provenance_uuid: STRING
```

**Analysis:**
- ✅ Schema exists for price data
- ⚠️ **NO RIN-specific columns** (D4, D5, D6, D3, D7)
- **Action:** Need to ADD columns OR create new table `forecasting_data_warehouse.rin_prices`

### 2. `forecasting_data_warehouse.biofuel_policy`
```sql
date: DATE
policy_type: STRING
mandate_volume: FLOAT
compliance_status: STRING
region: STRING
source_name: STRING
confidence_score: FLOAT
ingest_timestamp_utc: TIMESTAMP
provenance_uuid: STRING
policy_text: STRING
```

**Analysis:**
- ✅ Schema exists for policy data
- ✅ Has `mandate_volume` column (can store RFS mandates)
- ⚠️ **NO specific RFS columns** (biodiesel, advanced, total)
- **Action:** Can ADD columns OR use existing `mandate_volume` with `policy_type='RFS'`

### 3. `forecasting_data_warehouse.china_soybean_imports`
- ✅ Table exists
- ✅ Has `china_soybean_sales` column in production
- ⚠️ **Need to verify schema** - check for weekly/cancellation columns

### 4. `forecasting_data_warehouse.argentina_crisis_tracker`
- ✅ Table exists
- ✅ Has `argentina_export_tax`, `argentina_china_sales_mt`
- ⚠️ **Need to verify schema** - check for port/vessel columns

---

## 🎯 PRODUCTION TABLE MAPPING (290 Features)

### Existing Features (CONFIRMED in production_training_data_1m)
- ✅ `argentina_export_tax` (FLOAT64)
- ✅ `argentina_china_sales_mt` (FLOAT64)
- ✅ `argentina_competitive_threat` (INT64)
- ✅ `export_capacity_index` (FLOAT64)
- ✅ `export_seasonality_factor` (FLOAT64)
- ✅ `china_soybean_sales` (FLOAT64)
- ✅ `cn_imports` (FLOAT64)
- ✅ `cn_imports_fixed` (FLOAT64)
- ✅ `feature_biofuel_cascade` (FLOAT64)
- ✅ `feature_biofuel_ethanol` (FLOAT64)
- ✅ `biofuel_news_count` (INT64)

### Missing Features (NEW - Need Approval)
- ❌ `rin_d4_price` (RIN D4 biodiesel credit price)
- ❌ `rin_d5_price` (RIN D5 advanced biofuel credit price)
- ❌ `rin_d6_price` (RIN D6 renewable fuel credit price)
- ❌ `rin_d3_price` (RIN D3 cellulosic biofuel credit price)
- ❌ `rin_d7_price` (RIN D7 cellulosic diesel credit price)
- ❌ `rfs_mandate_biodiesel` (EPA RFS biodiesel mandate volume)
- ❌ `rfs_mandate_advanced` (EPA RFS advanced biofuel mandate volume)
- ❌ `rfs_mandate_total` (EPA RFS total renewable fuel mandate volume)
- ❌ `china_weekly_cancellations_mt` (China weekly purchase cancellations)
- ❌ `argentina_vessel_queue_count` (Argentina port vessel queue)
- ❌ `argentina_port_throughput_teu` (Argentina port throughput)
- ❌ `baltic_dry_index` (Baltic Exchange dry bulk freight index)

---

## 📋 RECOMMENDED INTEGRATION APPROACH

### Option A: Extend Existing Tables (RECOMMENDED)
1. **Add RIN columns to `biofuel_prices`**
   - Add: `rin_d4_price`, `rin_d5_price`, `rin_d6_price`, `rin_d3_price`, `rin_d7_price`
   - Keep existing schema, just add columns

2. **Add RFS columns to `biofuel_policy`**
   - Add: `rfs_mandate_biodiesel`, `rfs_mandate_advanced`, `rfs_mandate_total`
   - Use `policy_type='RFS'` to distinguish

3. **Add weekly columns to `china_soybean_imports`**
   - Add: `china_weekly_cancellations_mt`
   - Enhance existing `china_soybean_sales` with weekly granularity

4. **Add logistics columns to `argentina_crisis_tracker`**
   - Add: `argentina_vessel_queue_count`, `argentina_port_throughput_teu`
   - Enhance existing export capacity features

### Option B: Create New Tables (If Schema Conflicts)
1. **New Table:** `forecasting_data_warehouse.rin_prices_raw`
2. **New Table:** `forecasting_data_warehouse.argentina_port_logistics_raw`
3. **New Table:** `forecasting_data_warehouse.freight_logistics_raw`

**Decision:** Use Option A (extend existing) unless schema conflicts arise

---

## ⚠️ CRITICAL: PRODUCTION TABLE INTEGRATION

### Production Tables (290 Features - DO NOT MODIFY)
- `production_training_data_1w/1m/3m/6m` have FIXED 290-column schema
- **NEW features require:**
  1. Approval
  2. Schema expansion (add columns)
  3. Model retraining (if adding features)

### Integration Path (Existing Pattern)
```sql
-- Follow COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql pattern:

-- Step 1: Create daily aggregation
CREATE OR REPLACE TABLE `models_v4.rin_prices_daily` AS
SELECT 
  DATE(date) as date,
  AVG(rin_d4_price) as rin_d4_price_avg,
  AVG(rin_d5_price) as rin_d5_price_avg,
  ...
FROM `forecasting_data_warehouse.biofuel_prices`
GROUP BY DATE(date);

-- Step 2: Join to production (via MERGE or UPDATE)
-- Add to COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql
```

---

## 🎯 DRY RUN CHECKLIST

### Schema Verification
- [ ] ✅ `biofuel_prices` schema verified (needs RIN columns added)
- [ ] ✅ `biofuel_policy` schema verified (needs RFS columns added)
- [ ] ⏳ `china_soybean_imports` schema needs verification
- [ ] ⏳ `argentina_crisis_tracker` schema needs verification

### New Features Identification
- [ ] ⏳ Verify NEW features list (11 potential new columns)
- [ ] ⏳ Get approval for NEW features before adding to production
- [ ] ⏳ Document NEW features in separate file

### Script Development Pattern
- [ ] ✅ Follow `ingest_*.py` naming convention
- [ ] ✅ Use existing table schemas (extend with new columns)
- [ ] ✅ Include standard metadata: `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`

### Integration SQL
- [ ] ⏳ Create daily aggregations (`models_v4.*_daily`)
- [ ] ⏳ Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`
- [ ] ⏳ Test joins (DRY RUN first)

---

## 📝 NEXT ACTIONS (After Approval)

1. **Verify Remaining Schemas:**
   - Check `china_soybean_imports` full schema
   - Check `argentina_crisis_tracker` full schema

2. **Get Approval for NEW Features:**
   - Present 11 new feature list
   - Get approval before schema expansion

3. **Create Scripts:**
   - `ingest_epa_rin_prices.py`
   - `ingest_epa_rfs_mandates.py`
   - `ingest_usda_export_sales_weekly.py`
   - `ingest_argentina_port_logistics.py`
   - Enhance existing weather/news scripts

4. **Update Integration SQL:**
   - Add daily aggregations
   - Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`

**Status:** DRY RUN SCHEMA VERIFICATION IN PROGRESS







