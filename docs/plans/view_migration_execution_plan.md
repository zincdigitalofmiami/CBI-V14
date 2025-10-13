# View Migration Execution Plan (CBI-V14)
_Generated: 2025-10-11_

## Summary
Dashboard blueprint analysis complete. Found **4 Python scripts actively referencing legacy `soy_oil_features` view**. Cannot safely archive views until code migration is complete.

---

## Critical Findings

### Active Code Dependencies
| Script | Line | Legacy Reference | Migration Target |
|--------|------|------------------|------------------|
| `cbi-v14-ingestion/economic_intelligence.py` | 140 | `forecasting_data_warehouse.soy_oil_features` | `curated.vw_zl_features_daily` |
| `cbi-v14-ingestion/ice_trump_intelligence.py` | 350 | `forecasting_data_warehouse.soy_oil_features` | `curated.vw_zl_features_daily` |
| `forecast/main.py` | 165 | `forecasting_data_warehouse.soy_oil_features` | `curated.vw_zl_features_daily` |
| `cbi-v14-ingestion/intelligence_hunter.py` | 50 | `forecasting_data_warehouse.soy_oil_features` | `curated.vw_zl_features_daily` |

### View Audit Results
**Safe to archive immediately** (no code references):
- `vw_brazil_precip_daily` ✅
- `vw_brazil_weather_summary` ✅
- `vw_treasury_daily` ✅
- `vw_multi_source_intelligence_summary` ✅
- `vw_dashboard_brazil_weather` ✅

**Requires code migration first**:
- `soy_oil_features` ⚠️ (4 scripts depend on it)

**Keep temporarily for dashboard wiring**:
- `vw_dashboard_trump_intel` (Page 4)
- `vw_fed_rates_realtime` (Page 1)
- `vw_ice_trump_daily` (Page 4)
- `vw_news_intel_daily` (Page 2)
- `vw_trump_effect_breakdown` (Page 4)
- `vw_trump_effect_categories` (Page 4)
- `vw_trump_intelligence_dashboard` (Page 4)

---

## Execution Plan

### Step 1: Verify Curated View Schema Match
**Before any code changes**, confirm `curated.vw_zl_features_daily` contains all columns that `soy_oil_features` provides.

```bash
# Compare schemas
bq show --schema cbi-v14:forecasting_data_warehouse.soy_oil_features > /tmp/legacy_schema.json
bq show --schema cbi-v14:curated.vw_zl_features_daily > /tmp/curated_schema.json
diff /tmp/legacy_schema.json /tmp/curated_schema.json
```

**Expected columns in `soy_oil_features`:**
- `date`
- `value` (ZL price)
- `open`, `high`, `low`, `close`, `volume`
- `brazil_precip`, `argentina_precip`, `us_precip`
- `vix_value`, `volatility_30d`
- `dxy_value`, `10y_yield`
- Plus any other feature columns

**If schemas don't match**, we need to:
1. Update `curated.vw_zl_features_daily` SQL definition to match
2. Recreate the view
3. Then proceed with code migration

---

### Step 2: Update Python Scripts (4 files)

#### 2A: `cbi-v14-ingestion/economic_intelligence.py`
**Current (line 138-141):**
```python
query = f"""
    SELECT
        date,
        value as zl_price
    FROM `{PROJECT_ID}.{DATASET_ID}.soy_oil_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
"""
```

**Replace with:**
```python
query = f"""
    SELECT
        date,
        value as zl_price
    FROM `{PROJECT_ID}.curated.vw_zl_features_daily`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
"""
```

#### 2B: `cbi-v14-ingestion/ice_trump_intelligence.py`
**Current (line 348-352):**
```python
query = f"""
SELECT date, value as zl_price
FROM `{PROJECT_ID}.{DATASET_ID}.soy_oil_features`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
ORDER BY date
"""
```

**Replace with:**
```python
query = f"""
SELECT date, value as zl_price
FROM `{PROJECT_ID}.curated.vw_zl_features_daily`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY)
ORDER BY date
"""
```

#### 2C: `forecast/main.py`
**Current (line 163-167):**
```python
query = f"""
SELECT
    date,
    value,
    vix_value,
    dxy_value,
    brazil_precip,
    argentina_precip,
    us_precip
FROM `{PROJECT}.{DATASET}.soy_oil_features`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
ORDER BY date DESC
"""
```

**Replace with:**
```python
query = f"""
SELECT
    date,
    value,
    vix_value,
    dxy_value,
    brazil_precip,
    argentina_precip,
    us_precip
FROM `{PROJECT}.curated.vw_zl_features_daily`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
ORDER BY date DESC
"""
```

#### 2D: `cbi-v14-ingestion/intelligence_hunter.py`
**Current (line 46-52):**
```python
query = f"""
    SELECT
        date,
        value,
        brazil_precip,
        argentina_precip,
        us_precip,
        volume
    FROM `{PROJECT_ID}.{DATASET_ID}.soy_oil_features`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    ORDER BY date
"""
```

**Replace with:**
```python
query = f"""
    SELECT
        date,
        value,
        brazil_precip,
        argentina_precip,
        us_precip,
        volume
    FROM `{PROJECT_ID}.curated.vw_zl_features_daily`
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    ORDER BY date
"""
```

---

### Step 3: Test Scripts (Dry-Run Mode)
```bash
cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion

# Test each script in read-only mode
python economic_intelligence.py --dry-run  # (if flag exists)
python ice_trump_intelligence.py --dry-run
python intelligence_hunter.py --dry-run

# Test forecast script
cd /Users/zincdigital/CBI-V14/forecast
python main.py --test  # Or whatever test flag it has
```

**Verify:**
- No SQL errors
- Query results match expected shape
- All feature columns present

---

### Step 4: Archive Safe Views to Deprecated Dataset

```bash
# Create timestamped archives in deprecated dataset
bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.vw_brazil_precip_daily_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_brazil_precip_daily;
"

bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.vw_brazil_weather_summary_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_brazil_weather_summary;
"

bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.vw_treasury_daily_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_treasury_daily;
"

bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.vw_multi_source_intelligence_summary_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_multi_source_intelligence_summary;
"

bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.vw_dashboard_brazil_weather_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.vw_dashboard_brazil_weather;
"
```

---

### Step 5: Drop Legacy Views from forecasting_data_warehouse

**ONLY after Step 4 archive is complete:**

```bash
bq rm -f cbi-v14:forecasting_data_warehouse.vw_brazil_precip_daily
bq rm -f cbi-v14:forecasting_data_warehouse.vw_brazil_weather_summary
bq rm -f cbi-v14:forecasting_data_warehouse.vw_treasury_daily
bq rm -f cbi-v14:forecasting_data_warehouse.vw_multi_source_intelligence_summary
bq rm -f cbi-v14:forecasting_data_warehouse.vw_dashboard_brazil_weather
```

---

### Step 6: Handle soy_oil_features (After Script Updates)

**After Python scripts are updated and tested:**

```bash
# Archive to deprecated
bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW deprecated.soy_oil_features_legacy_20251011 AS 
SELECT * FROM forecasting_data_warehouse.soy_oil_features;
"

# Drop from warehouse
bq rm -f cbi-v14:forecasting_data_warehouse.soy_oil_features
```

---

### Step 7: Consolidate Trump Views (Next Phase)

**Create unified Trump intelligence view in curated:**

```sql
CREATE OR REPLACE VIEW curated.vw_trump_trade_intelligence AS
SELECT
  t.post_date as date,
  t.post_content,
  t.post_type,
  t.post_url,
  t.event_category,
  t.severity_score,
  t.aggression_score,
  t.market_relevance,
  
  -- Correlations (if ice_trump_intelligence has them)
  i.zl_price,
  i.price_change_pct,
  i.correlation_1d,
  i.correlation_7d,
  
  -- Categorization
  c.category_name,
  c.category_weight,
  
  -- Impact breakdown
  b.impact_type,
  b.impact_magnitude,
  b.confidence_score
  
FROM forecasting_data_warehouse.ice_trump_intelligence t
LEFT JOIN forecasting_data_warehouse.vw_ice_trump_daily i
  ON t.post_date = i.date
LEFT JOIN forecasting_data_warehouse.vw_trump_effect_categories c
  ON t.event_category = c.category_id
LEFT JOIN forecasting_data_warehouse.vw_trump_effect_breakdown b
  ON t.post_date = b.date AND t.event_category = b.category
  
WHERE t.post_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
ORDER BY t.post_date DESC;
```

**Save SQL:**
```bash
cat > /Users/zincdigital/CBI-V14/bigquery_sql/curated_facade/vw_trump_trade_intelligence.sql << 'EOF'
[paste SQL above]
EOF
```

**Deploy:**
```bash
bq query --use_legacy_sql=false < /Users/zincdigital/CBI-V14/bigquery_sql/curated_facade/vw_trump_trade_intelligence.sql
```

**After validation, archive 5 Trump views:**
```bash
# Archive each Trump view to deprecated with timestamp
# Then drop from forecasting_data_warehouse
```

---

## Dashboard Wiring Priority (Parallel Track)

While cleaning up views, implement **high-priority missing data sources**:

### Client Priority (Must Have)
1. ✅ **China Export Sales** — `export_sales_weekly` (Client #1)
2. ✅ **USDA Crop Progress** — `crop_progress_reports` (Client #2)
3. ✅ **CONAB Brazil Harvest** — `conab_harvest_forecasts` (Client #2)
4. ✅ **EPA RFS Biofuel Mandates** — `rfs_mandates` (Client #3)

### Core Infrastructure (Required for Dashboard)
5. ✅ **ZL Price Rebuild** — CME/TradingEconomics → `staging.market_prices`
6. ✅ **CFTC COT Reports** — Fund positioning (Pages 1, 2)
7. ✅ **USDA WASDE** — Monthly S&D balance (Page 3)
8. ✅ **Crush Margins** — Derived feature (Page 1)
9. ✅ **Palm Oil Complete** — MPOB + FCPO (substitute tracking)

### Enhanced Intelligence
10. ⏸️ **Google Trends** — Page 2 sentiment (lower priority)
11. ⏸️ **Congressional Votes** — Page 4 (nice-to-have)
12. ⏸️ **Storage Capacity** — USDA grain stocks (useful but not critical)

---

## Rollback Plan

If any step fails:

### Rollback Step 1 (Python Scripts)
```bash
git checkout HEAD -- cbi-v14-ingestion/economic_intelligence.py
git checkout HEAD -- cbi-v14-ingestion/ice_trump_intelligence.py
git checkout HEAD -- forecast/main.py
git checkout HEAD -- cbi-v14-ingestion/intelligence_hunter.py
```

### Rollback Step 2 (Views)
Views are archived in `deprecated` dataset, so we can recreate from archive:

```bash
# Restore any accidentally dropped view
bq query --use_legacy_sql=false "
CREATE OR REPLACE VIEW forecasting_data_warehouse.vw_brazil_precip_daily AS 
SELECT * FROM deprecated.vw_brazil_precip_daily_legacy_20251011;
"
```

---

## Validation Checklist

After each step:
- [ ] No BigQuery SQL errors
- [ ] Python scripts run without exceptions
- [ ] Query result schemas match expected
- [ ] Dashboard pages load without errors
- [ ] Git commit with clear message
- [ ] Log results to `/Users/zincdigital/CBI-V14/logs/view_migration_YYYYMMDD.log`

---

## Timeline Estimate

| Step | Time | Blocking? |
|------|------|-----------|
| 1. Verify schema match | 15 min | Yes |
| 2. Update Python scripts | 30 min | Yes |
| 3. Test scripts | 30 min | Yes |
| 4. Archive safe views | 10 min | No |
| 5. Drop legacy views | 5 min | Yes (after 4) |
| 6. Handle soy_oil_features | 10 min | Yes (after 2, 3) |
| 7. Consolidate Trump views | 60 min | No (can defer) |
| **Total critical path** | **~2 hours** | |

---

## Decision Required

**Should I proceed with Step 1 (schema verification) now?**

Options:
- **A)** Yes, proceed with full migration (Steps 1-6)
- **B)** Yes, but only do safe views first (Steps 4-5), defer soy_oil_features until later
- **C)** No, focus on high-priority data sources first (China exports, USDA, etc.)
- **D)** No, review dashboard wiring plan in detail before any changes

Your call.


