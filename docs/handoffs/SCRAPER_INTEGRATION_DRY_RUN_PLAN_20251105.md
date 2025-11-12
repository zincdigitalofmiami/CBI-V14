# Scraper Integration Dry Run Plan
**Date:** November 5, 2025  
**Status:** DRY RUN - NO EXECUTION  
**Purpose:** Integrate new data sources into existing system following naming/schema conventions

---

## 🎯 INTEGRATION PRINCIPLES

1. **NO SCHEMA CHANGES** - Use existing tables/columns where possible
2. **Follow Existing Patterns** - Match `ingest_*.py` and `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql` patterns
3. **Naming Convention:**
   - Source tables: `forecasting_data_warehouse.*_raw` or `forecasting_data_warehouse.*`
   - Intermediate: `models_v4.*_daily` (if needed)
   - Final: `production_training_data_*` (290 features - DO NOT MODIFY)
4. **Integration Path:** Source → Daily Aggregation → Production (via existing SQL)

---

## 📊 DATA SOURCE MAPPING

### 1. ✅ RIN Prices (Biofuel Credits)

**URLs:**
- EPA RIN Trades: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rin-trades-and-price-information
- EPA RIN Generation: https://www.epa.gov/fuels-registration-reporting-and-compliance-help/spreadsheet-rin-generation-data-renewable-fuel

**Existing System:**
- ✅ Table: `forecasting_data_warehouse.biofuel_prices` (exists)
- ✅ Columns in production: `feature_biofuel_cascade`, `feature_biofuel_ethanol`, `biofuel_news_count`
- ✅ Script: `ingestion/ingest_eia_biofuel_real.py` (exists)

**Integration Plan:**
1. **New Script:** `ingestion/ingest_epa_rin_prices.py`
   - Scrape EPA weekly RIN price table (D4, D5, D6, D3, D7)
   - Load to: `forecasting_data_warehouse.biofuel_prices` (APPEND - check schema match)
   - Columns: `date`, `rin_d4_price`, `rin_d5_price`, `rin_d6_price`, `rin_d3_price`, `rin_d7_price`, `source_name='EPA_SCRAPED'`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`

2. **Daily Aggregation:** Add to `models_v4.biofuel_daily` (if exists) or create
   - Aggregate weekly RIN prices to daily (forward-fill)
   - Calculate rolling averages

3. **Production Integration:** Add to `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`
   - Join `biofuel_daily` → `production_training_data_*`
   - New columns: `rin_d4_price`, `rin_d5_price`, `rin_d6_price` (if not in 290 features)

**DRY RUN CHECK:**
- [ ] Verify `biofuel_prices` schema matches proposed columns
- [ ] Check if RIN columns exist in production_training_data_* (290 features)
- [ ] If columns don't exist, document as "NEW FEATURE" (requires approval)

---

### 2. ✅ EPA RFS Mandates

**URLs:**
- Final Rule 2023-2025: https://www.epa.gov/renewable-fuel-standard/final-renewable-fuels-standards-rule-2023-2024-and-2025
- Annual Standards: https://www.epa.gov/renewable-fuel-standard/renewable-fuel-annual-standards

**Existing System:**
- ✅ Table: `forecasting_data_warehouse.biofuel_policy` (exists)
- ✅ Script: `ingestion/comprehensive_policy_collector.py` (exists)

**Integration Plan:**
1. **New Script:** `ingestion/ingest_epa_rfs_mandates.py`
   - Scrape EPA annual RFS mandate tables
   - Parse: Year, Biomass-based diesel, Advanced biofuel, Total renewable fuel
   - Load to: `forecasting_data_warehouse.biofuel_policy` (APPEND)
   - Columns: `date`, `rfs_mandate_biodiesel`, `rfs_mandate_advanced`, `rfs_mandate_total`, `source_name='EPA_RFS_SCRAPED'`, etc.

2. **Production Integration:** 
   - Map to existing `feature_biofuel_cascade` or add new column if needed

**DRY RUN CHECK:**
- [ ] Verify `biofuel_policy` schema
- [ ] Check if RFS mandate columns exist in production

---

### 3. ✅ USDA / China Soybean Imports

**URLs:**
- USDA FAS Weekly Export Sales: https://apps.fas.usda.gov/export-sales/h801.htm
- Complete Weekly Report: https://apps.fas.usda.gov/export-sales/complete.htm

**Existing System:**
- ✅ Table: `forecasting_data_warehouse.china_soybean_imports` (exists)
- ✅ Columns: `china_soybean_sales`, `cn_imports`, `cn_imports_fixed`, `china_soybean_sales` (in production)
- ✅ Script: `ingestion/ingest_china_imports_uncomtrade.py` (exists)

**Integration Plan:**
1. **New Script:** `ingestion/ingest_usda_export_sales_weekly.py`
   - Scrape USDA FAS weekly export sales table
   - Extract: Week Ending, Country (China), Commodity (Soybeans), Net Sales, Cancellations
   - Load to: `forecasting_data_warehouse.china_soybean_imports` (APPEND)
   - Columns: `date`, `china_weekly_sales_mt`, `china_weekly_cancellations_mt`, `source_name='USDA_FAS_SCRAPED'`

2. **Production Integration:**
   - Join to existing `china_soybean_sales` column or enhance it

**DRY RUN CHECK:**
- [ ] Verify `china_soybean_imports` schema
- [ ] Check if weekly cancellations column needed (new feature?)

---

### 4. ✅ Argentina Export Logistics

**URLs:**
- Port of Rosario: https://www.bcr.com.ar/en/markets/grain-market
- TradingEconomics: https://tradingeconomics.com/argentina/container-port-traffic-teu-20-foot-equivalent-units-wb-data.html

**Existing System:**
- ✅ Table: `forecasting_data_warehouse.argentina_crisis_tracker` (exists)
- ✅ Columns: `argentina_export_tax`, `argentina_china_sales_mt`, `argentina_competitive_threat`, `export_capacity_index`, `export_seasonality_factor`

**Integration Plan:**
1. **New Script:** `ingestion/ingest_argentina_port_logistics.py`
   - Scrape Port of Rosario vessel line-up / shipments
   - Scrape TradingEconomics port throughput
   - Load to: `forecasting_data_warehouse.argentina_crisis_tracker` (APPEND) OR new table `forecasting_data_warehouse.argentina_port_logistics`
   - Columns: `date`, `vessel_count`, `port_throughput_teu`, `cargo_soy_mt`, `cargo_meal_mt`, `cargo_oil_mt`, `source_name='ARGENTINA_PORT_SCRAPED'`

2. **Production Integration:**
   - Enhance `export_capacity_index` or add new column: `argentina_vessel_queue_count`

**DRY RUN CHECK:**
- [ ] Check `argentina_crisis_tracker` schema
- [ ] Decide: Append to existing table or create `argentina_port_logistics`?
- [ ] Verify if vessel/port columns exist in production (290 features)

---

### 5. ✅ Weather / Climate Backfill

**URLs:**
- NOAA Midwest: https://mrcc.purdue.edu/climate/
- Iowa Mesonet: https://mesonet.agron.iastate.edu/ASOS/
- Brazil INMET: https://portal.inmet.gov.br/dadoshistoricos

**Existing System:**
- ✅ Tables: Weather tables exist (check schema)
- ✅ Columns: `argentina_temp_c`, `argentina_precip_mm`, `brazil_temp_c`, `brazil_precip_mm`, `us_midwest_temp_c`, `us_midwest_precip_mm`
- ✅ Scripts: `ingestion/ingest_weather_noaa.py`, `ingestion/ingest_brazil_weather_inmet.py` (exist)

**Integration Plan:**
1. **Enhance Existing Scripts:**
   - Add NOAA Midwest scraping to `ingest_weather_noaa.py`
   - Add Iowa Mesonet to `ingest_midwest_weather_iem.py` (exists)
   - Enhance Brazil INMET in `ingest_brazil_weather_inmet.py`

2. **Production Integration:**
   - Data already flows to production via existing weather integration

**DRY RUN CHECK:**
- [ ] Verify existing weather scripts work
- [ ] Check if backfill needed (historical data gaps)

---

### 6. ✅ Trade / Policy News Sentiment

**URLs:**
- GDELT: https://www.gdeltproject.org/data.html
- Reuters: https://www.reuters.com/markets/commodities/
- Bloomberg: https://www.bloomberg.com/energy

**Existing System:**
- ✅ Table: `forecasting_data_warehouse.news_intelligence` (exists)
- ✅ Columns: `news_article_count`, `news_avg_score`, `news_sentiment_avg`, `china_news_count`, `biofuel_news_count`, `tariff_news_count`
- ✅ Script: `ingestion/multi_source_news.py` (exists)

**Integration Plan:**
1. **Enhance Existing Script:**
   - Add GDELT daily CSV scraping to `multi_source_news.py`
   - Add Reuters headlines scraping
   - Add Bloomberg headlines scraping
   - Filter for: soybean, biodiesel, tariff, China, EPA, Argentina keywords

2. **Production Integration:**
   - Data already flows via `news_intelligence_daily` → production

**DRY RUN CHECK:**
- [ ] Verify `news_intelligence` schema
- [ ] Check if GDELT integration already exists

---

### 7. ✅ Freight & Logistics

**URLs:**
- Baltic Exchange: https://www.tradingeconomics.com/commodity/baltic
- FreightWaves: https://www.freightwaves.com/news

**Existing System:**
- ✅ Script: `ingestion/ingest_baltic_dry_index.py` (exists)
- ⚠️ No explicit freight columns in production (check 290 features)

**Integration Plan:**
1. **Enhance Existing Script:**
   - Enhance `ingest_baltic_dry_index.py` with TradingEconomics scraping
   - Add FreightWaves headline scraping

2. **New Table:** `forecasting_data_warehouse.freight_logistics` (if needed)
   - Columns: `date`, `baltic_dry_index`, `freight_soybean_mentions`, `source_name`

3. **Production Integration:**
   - Add `baltic_dry_index` column if not in 290 features (NEW FEATURE)

**DRY RUN CHECK:**
- [ ] Check if `baltic_dry_index` exists in production (290 features)
- [ ] Verify `ingest_baltic_dry_index.py` works

---

## 📋 IMPLEMENTATION CHECKLIST (DRY RUN)

### Phase 1: Schema Verification
- [ ] Verify all existing table schemas match proposed columns
- [ ] Identify which features are NEW (not in 290 features)
- [ ] Document NEW features requiring approval

### Phase 2: Script Creation Pattern
- [ ] Follow `ingest_*.py` naming convention
- [ ] Use `advanced_scraper_base.py` pattern (if applicable)
- [ ] Include: `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`
- [ ] Load to `forecasting_data_warehouse.*` tables

### Phase 3: Integration SQL
- [ ] Add daily aggregations to `models_v4.*_daily` tables
- [ ] Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql` with new joins
- [ ] Map to existing production columns OR document NEW columns

### Phase 4: Testing
- [ ] Test each scraper individually (DRY RUN)
- [ ] Verify data loads to BigQuery
- [ ] Check daily aggregations work
- [ ] Verify production integration (no schema errors)

---

## ⚠️ CRITICAL WARNINGS

1. **Production Tables (290 features):**
   - DO NOT MODIFY SCHEMA
   - NEW features require approval and retraining
   - Document all NEW features separately

2. **Naming Convention:**
   - Source: `forecasting_data_warehouse.*`
   - Intermediate: `models_v4.*_daily`
   - Final: `models_v4.production_training_data_*`

3. **Rate Limiting:**
   - 1-3 second delays between requests
   - Rotate user agents
   - Handle 429 errors

4. **Data Quality:**
   - Log: `source_url`, `scrape_date`, `row_count`, `null_count`
   - Store raw HTML snapshots for re-parsing
   - Handle missing data gracefully

---

## 🎯 NEXT STEPS (AFTER DRY RUN APPROVAL)

1. **Schema Verification:** Check all existing tables match proposed columns
2. **Script Development:** Create scrapers following existing patterns
3. **Integration SQL:** Update `COMPREHENSIVE_DATA_INTEGRATION_FIXED.sql`
4. **Testing:** Dry run each scraper individually
5. **Production Update:** Run integration SQL to update production tables

**Status:** DRY RUN PLAN COMPLETE - AWAITING APPROVAL







