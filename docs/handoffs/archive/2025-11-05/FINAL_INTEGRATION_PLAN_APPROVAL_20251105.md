---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Final Integration Plan - New Scrapers
**Date:** November 5, 2025  
**Status:** DRY RUN COMPLETE - AWAITING APPROVAL  
**Principle:** Follow existing system/naming/setup - NO SCHEMA CHANGES without approval

---

## ✅ EXECUTIVE SUMMARY

### What We Have
- ✅ Existing ingestion scripts following `ingest_*.py` pattern
- ✅ Source tables: `forecasting_data_warehouse.*`
- ✅ Intermediate tables: `models_v4.*_daily`
- ✅ Production tables: `production_training_data_*` (290 features - DO NOT MODIFY)
- ✅ Integration SQL: `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`

### What We Need
- ⏳ RIN price scrapers (EPA)
- ⏳ RFS mandate scrapers (EPA)
- ⏳ USDA weekly export sales scraper
- ⏳ Argentina port logistics scraper
- ⏳ Enhanced weather/news scrapers

### Critical Finding
- **11 NEW features identified** that don't exist in 290-feature production tables
- **Requires approval** before adding to production schema
- **Will require model retraining** if new features added

---

## 📊 DATA SOURCE MAPPING

### 1. EPA RIN Prices → `forecasting_data_warehouse.biofuel_prices`

**URLs:**
- Weekly RIN Trades: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rin-trades-and-price-information
- RIN Generation: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/spreadsheet-rin-generation-data-renewable-fuel

**Existing:**
- ✅ Table: `forecasting_data_warehouse.biofuel_prices` (schema: date, symbol, close, open, high, low, volume, metadata)
- ❌ **NO RIN-specific columns** (D4, D5, D6, D3, D7)

**Action:**
1. **Extend Schema:** Add columns to `biofuel_prices`:
   - `rin_d4_price` (FLOAT)
   - `rin_d5_price` (FLOAT)
   - `rin_d6_price` (FLOAT)
   - `rin_d3_price` (FLOAT)
   - `rin_d7_price` (FLOAT)
2. **Create Script:** `ingestion/ingest_epa_rin_prices.py`
3. **Daily Aggregation:** `models_v4.rin_prices_daily`
4. **Production:** NEW feature `rin_d4_price`, `rin_d5_price`, `rin_d6_price` (requires approval)

---

### 2. EPA RFS Mandates → `forecasting_data_warehouse.biofuel_policy`

**URLs:**
- Final Rule 2023-2025: https://www.epa.gov/renewable-fuel-standard/final-renewable-fuels-standards-rule-2023-2024-and-2025
- Annual Standards: https://www.epa.gov/renewable-fuel-standard/renewable-fuel-annual-standards

**Existing:**
- ✅ Table: `forecasting_data_warehouse.biofuel_policy` (schema: date, policy_type, mandate_volume, compliance_status, region, metadata)
- ✅ Has `mandate_volume` column (can use with `policy_type='RFS'`)

**Action:**
1. **Extend Schema:** Add columns to `biofuel_policy`:
   - `rfs_mandate_biodiesel` (FLOAT)
   - `rfs_mandate_advanced` (FLOAT)
   - `rfs_mandate_total` (FLOAT)
2. **Create Script:** `ingestion/ingest_epa_rfs_mandates.py`
3. **Daily Aggregation:** `models_v4.rfs_mandates_daily`
4. **Production:** NEW features `rfs_mandate_biodiesel`, `rfs_mandate_advanced`, `rfs_mandate_total` (requires approval)

---

### 3. USDA Weekly Export Sales → `forecasting_data_warehouse.china_soybean_imports`

**URLs:**
- Weekly Export Sales: https://apps.fas.usda.gov/export-sales/h801.htm
- Complete Report: https://apps.fas.usda.gov/export-sales/complete.htm

**Existing:**
- ✅ Table: `forecasting_data_warehouse.china_soybean_imports` (exists)
- ✅ Production: `china_soybean_sales` (FLOAT64)

**Action:**
1. **Extend Schema:** Add column to `china_soybean_imports`:
   - `china_weekly_cancellations_mt` (FLOAT)
2. **Create Script:** `ingestion/ingest_usda_export_sales_weekly.py`
3. **Daily Aggregation:** Enhance existing `models_v4.usda_export_daily`
4. **Production:** NEW feature `china_weekly_cancellations_mt` (requires approval)

---

### 4. Argentina Port Logistics → `forecasting_data_warehouse.argentina_crisis_tracker`

**URLs:**
- Port of Rosario: https://www.bcr.com.ar/en/markets/grain-market
- TradingEconomics: https://tradingeconomics.com/argentina/container-port-traffic-teu-20-foot-equivalent-units-wb-data.html

**Existing:**
- ✅ Table: `forecasting_data_warehouse.argentina_crisis_tracker` (exists)
- ✅ Production: `argentina_export_tax`, `argentina_china_sales_mt`, `export_capacity_index`

**Action:**
1. **Extend Schema:** Add columns to `argentina_crisis_tracker`:
   - `argentina_vessel_queue_count` (INT64)
   - `argentina_port_throughput_teu` (FLOAT)
2. **Create Script:** `ingestion/ingest_argentina_port_logistics.py`
3. **Daily Aggregation:** Enhance existing export capacity features
4. **Production:** NEW features `argentina_vessel_queue_count`, `argentina_port_throughput_teu` (requires approval)

---

### 5. Freight & Logistics → NEW TABLE

**URLs:**
- Baltic Exchange: https://www.tradingeconomics.com/commodity/baltic
- FreightWaves: https://www.freightwaves.com/news

**Existing:**
- ✅ Script: `ingestion/ingest_baltic_dry_index.py` (exists)
- ❌ No explicit freight table or production columns

**Action:**
1. **Create Table:** `forecasting_data_warehouse.freight_logistics` (NEW)
   - Schema: `date`, `baltic_dry_index`, `freight_soybean_mentions`, metadata
2. **Enhance Script:** Update `ingest_baltic_dry_index.py`
3. **Daily Aggregation:** `models_v4.freight_logistics_daily`
4. **Production:** NEW feature `baltic_dry_index` (requires approval)

---

### 6. Weather/News Enhancement → EXISTING TABLES

**URLs:**
- NOAA Midwest: https://mrcc.purdue.edu/climate/
- GDELT: https://www.gdeltproject.org/data.html
- Reuters: https://www.reuters.com/markets/commodities/

**Existing:**
- ✅ Weather scripts exist
- ✅ News scripts exist (`multi_source_news.py`)
- ✅ Tables: `forecasting_data_warehouse.news_intelligence`, weather tables

**Action:**
1. **Enhance Existing Scripts:**
   - Add NOAA Midwest to `ingest_weather_noaa.py`
   - Add GDELT to `multi_source_news.py`
   - Add Reuters/Bloomberg to `multi_source_news.py`
2. **No Schema Changes:** Use existing tables/columns

---

## ⚠️ NEW FEATURES REQUIRING APPROVAL

### List of 11 New Features (NOT in 290-feature production tables)

1. `rin_d4_price` (FLOAT64) - RIN D4 biodiesel credit price
2. `rin_d5_price` (FLOAT64) - RIN D5 advanced biofuel credit price
3. `rin_d6_price` (FLOAT64) - RIN D6 renewable fuel credit price
4. `rfs_mandate_biodiesel` (FLOAT64) - EPA RFS biodiesel mandate volume
5. `rfs_mandate_advanced` (FLOAT64) - EPA RFS advanced biofuel mandate volume
6. `rfs_mandate_total` (FLOAT64) - EPA RFS total renewable fuel mandate volume
7. `china_weekly_cancellations_mt` (FLOAT64) - China weekly purchase cancellations
8. `argentina_vessel_queue_count` (INT64) - Argentina port vessel queue count
9. `argentina_port_throughput_teu` (FLOAT64) - Argentina port throughput (TEU)
10. `baltic_dry_index` (FLOAT64) - Baltic Exchange dry bulk freight index
11. `rin_d3_price`, `rin_d7_price` (optional - D4, D5, D6 are priority)

### Approval Required
- ✅ **Schema Expansion:** Add 11 columns to `production_training_data_*` tables
- ✅ **Model Retraining:** All 4 models (bqml_1w, bqml_1m, bqml_3m, bqml_6m) need retraining
- ✅ **Impact Assessment:** Evaluate feature importance before retraining

---

## 📋 IMPLEMENTATION PLAN (After Approval)

### Phase 1: Schema Extension (Approval Required)
1. Add columns to source tables:
   - `biofuel_prices`: Add RIN columns
   - `biofuel_policy`: Add RFS columns
   - `china_soybean_imports`: Add weekly cancellations
   - `argentina_crisis_tracker`: Add port/vessel columns
   - Create `freight_logistics` table
2. Add columns to production tables:
   - `production_training_data_1w/1m/3m/6m`: Add 11 new features
   - **WARNING:** This changes the 290-feature schema

### Phase 2: Script Development
1. Create new scrapers:
   - `ingest_epa_rin_prices.py`
   - `ingest_epa_rfs_mandates.py`
   - `ingest_usda_export_sales_weekly.py`
   - `ingest_argentina_port_logistics.py`
2. Enhance existing scripts:
   - `ingest_weather_noaa.py` (add NOAA Midwest)
   - `multi_source_news.py` (add GDELT, Reuters, Bloomberg)
   - `ingest_baltic_dry_index.py` (enhance with FreightWaves)

### Phase 3: Daily Aggregations
1. Create/update `models_v4.*_daily` tables:
   - `rin_prices_daily`
   - `rfs_mandates_daily`
   - `freight_logistics_daily`
   - Enhance existing daily tables

### Phase 4: Production Integration
1. Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`:
   - Add joins for new daily tables
   - Map new features to production columns
2. Test integration:
   - Dry run SQL queries
   - Verify data flows correctly
   - Check for NULLs/errors

### Phase 5: Model Retraining (After New Features Added)
1. Retrain all 4 models with new features
2. Evaluate performance improvements
3. Deploy updated models

---

## 🎯 DRY RUN CHECKLIST

### Pre-Implementation
- [x] ✅ Review existing schemas
- [x] ✅ Identify new features
- [x] ✅ Map to existing tables
- [x] ✅ Document integration approach
- [ ] ⏳ **GET APPROVAL** for 11 new features
- [ ] ⏳ **GET APPROVAL** for schema expansion

### Script Development (After Approval)
- [ ] Create scrapers following `ingest_*.py` pattern
- [ ] Test scrapers individually (DRY RUN)
- [ ] Verify data loads to BigQuery
- [ ] Check for schema errors

### Integration (After Approval)
- [ ] Create daily aggregations
- [ ] Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`
- [ ] Test joins (DRY RUN)
- [ ] Verify production updates

---

## ⚠️ CRITICAL WARNINGS

1. **Production Schema (290 features):**
   - DO NOT MODIFY without approval
   - New features require model retraining
   - Document all changes

2. **Naming Convention:**
   - Source: `forecasting_data_warehouse.*`
   - Intermediate: `models_v4.*_daily`
   - Final: `models_v4.production_training_data_*`

3. **Rate Limiting:**
   - 1-3 second delays between requests
   - Rotate user agents
   - Handle 429 errors gracefully

4. **Data Quality:**
   - Log: `source_url`, `scrape_date`, `row_count`, `null_count`
   - Store raw HTML snapshots
   - Handle missing data gracefully

---

## ✅ SUMMARY

**Status:** DRY RUN COMPLETE  
**Ready For:** Approval and implementation  
**Blockers:** 11 new features need approval before schema expansion  
**Risk:** Medium (schema changes require model retraining)

**Next Step:** Get approval for 11 new features and schema expansion plan

---

**Documents Created:**
- `logs/SCRAPER_INTEGRATION_DRY_RUN_PLAN_20251105.md` - Detailed integration plan
- `logs/SCHEMA_MAPPING_VERIFICATION_20251105.md` - Schema verification
- `logs/FINAL_INTEGRATION_PLAN_APPROVAL_20251105.md` - This document (executive summary)







