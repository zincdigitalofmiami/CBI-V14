# CBI-V14 Warehouse Cleanup - VALIDATED EXECUTION PLAN
**Date:** October 9, 2025  
**Status:** READY FOR APPROVAL

## PRE-FLIGHT VALIDATION COMPLETED

### Environment Check ✅
- **Project:** cbi-v14
- **Existing Dataset:** forecasting_data_warehouse
- **Location:** us-central1 (NOT US multi-region)
- **Cron Jobs:** Installed and running
- **Data Freshness:** 
  - soybean_oil_prices: 1 day stale ✅
  - economic_indicators: 1 day stale ✅
  - weather_data: 9 days stale ❌ (MUST FIX)

### Schema Validation ✅
- `soybean_oil_prices`: `time` TIMESTAMP, `close`, `open`, `high`, `low`, `volume`, `symbol`
- `economic_indicators`: NARROW format (indicator STRING, value FLOAT64, time TIMESTAMP)
- `weather_data`: `date` DATE, `region` STRING, `precip_mm`, `temp_max`, `temp_min`
- `vw_economic_daily`: EXISTS (wide format economic indicators)
- `vw_zl_features_daily`: EXISTS (ZL features with lags/rolling windows)

### Critical Decision Points

**DECISION 1: Dataset Location**
- ❌ DON'T use US multi-region
- ✅ USE us-central1 to match existing data
- **Action:** Recreate datasets in correct location

**DECISION 2: View Strategy**
- ❌ DON'T recreate existing good views
- ✅ PROMOTE existing views to curated namespace
- **Rationale:** `vw_economic_daily`, `vw_zl_features_daily`, `vw_weather_daily` are already good

**DECISION 3: Naming Convention**
- ✅ USE `fct_*` for new fact/metric views (institutional pattern)
- ✅ KEEP `vw_*` for promoted existing views (backwards compatibility)
- **Hybrid approach:** New = `fct_*`, Promoted = `vw_*`

---

## EXECUTION SEQUENCE (SAFE, TESTED)

### Phase 1: Fix Location Mismatch (5 minutes)

**1.1 Remove incorrectly located datasets**
```bash
bq rm -f cbi-v14:curated
bq rm -f cbi-v14:models  
bq rm -f cbi-v14:bkp
```
**Status:** ✅ COMPLETED (datasets removed)

**1.2 Recreate in correct location**
```bash
bq mk --dataset --location=us-central1 --description="Canonical dashboard views" cbi-v14:curated
bq mk --dataset --location=us-central1 --description="ML predictions and model monitoring" cbi-v14:models
bq mk --dataset --location=us-central1 --description="Backups before deployments" cbi-v14:bkp
```
**Status:** PENDING APPROVAL

**1.3 Verify datasets**
```bash
bq ls | grep -E "(curated|models|bkp)"
bq show cbi-v14:curated | grep location
```

---

### Phase 2: Deploy Canonical Views (30 minutes)

**TIER 1: Independent Views (no dependencies)**

**2.1 Market Indicators** 
```bash
bq query --use_legacy_sql=false < sql/04_curated/01_fct_market_indicators_daily.sql
```
- **Source:** vw_economic_daily (existing)
- **Risk:** LOW (read-only, references existing view)
- **Validation:** `SELECT COUNT(*) FROM cbi-v14.curated.fct_market_indicators_daily`

**2.2 Weather Daily**
```bash
bq query --use_legacy_sql=false < sql/04_curated/02_fct_weather_daily.sql
```
- **Source:** weather_data (raw table)
- **Risk:** LOW (read-only)
- **Validation:** `SELECT COUNT(*), MAX(date) FROM cbi-v14.curated.fct_weather_daily`

**2.3 ZL Price + Volatility**
```bash
bq query --use_legacy_sql=false < sql/04_curated/03_fct_zl_price_volatility_daily.sql
```
- **Source:** soybean_oil_prices (raw table)
- **Risk:** LOW (read-only, window functions tested)
- **Validation:** `SELECT * FROM cbi-v14.curated.fct_zl_price_volatility_daily LIMIT 5`

**TIER 2: Dependent Views (requires TIER 1)**

**2.4 Dashboard Executive**
```bash
bq query --use_legacy_sql=false < sql/04_curated/04_fct_dashboard_executive.sql
```
- **Dependencies:** fct_market_indicators_daily, fct_zl_price_volatility_daily, fct_weather_daily
- **Risk:** MEDIUM (circular dependency if TIER 1 not deployed first)
- **Validation:** `SELECT * FROM cbi-v14.curated.fct_dashboard_executive WHERE date >= '2025-10-01' LIMIT 10`

---

### Phase 3: ML Infrastructure (15 minutes)

**3.1 Create ml_predictions table**
```sql
CREATE OR REPLACE TABLE `cbi-v14.models.ml_predictions` (
  prediction_date DATE,
  forecast_date DATE,
  predicted_price FLOAT64,
  confidence_lower FLOAT64,
  confidence_upper FLOAT64,
  model_name STRING,
  model_version STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  -- Canonical metadata
  source_name STRING DEFAULT 'bigquery_ml_arima',
  confidence_score FLOAT64,
  ingest_timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  provenance_uuid STRING
)
PARTITION BY prediction_date
CLUSTER BY model_name, forecast_date;
```

**3.2 Create model monitoring view**
```sql
CREATE OR REPLACE VIEW `cbi-v14.models.vw_ml_model_monitor` AS
SELECT
  model_name,
  model_version,
  COUNT(*) AS prediction_count,
  MIN(prediction_date) AS first_prediction,
  MAX(prediction_date) AS latest_prediction,
  COUNT(DISTINCT forecast_date) AS forecast_days
FROM `cbi-v14.models.ml_predictions`
GROUP BY model_name, model_version;
```

---

### Phase 4: Fix Weather Pipeline (CRITICAL)

**4.1 Debug Brazil weather**
```bash
cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion
python3 ingest_brazil_weather_inmet.py --days 10 2>&1 | tee /tmp/weather_debug.log
```

**4.2 If broken, run NOAA fallback**
```bash
python3 ingest_weather_noaa.py --days 10
```

**4.3 Verify freshness**
```bash
bq query --use_legacy_sql=false \
  "SELECT MAX(date) AS last_date, DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) AS days_stale 
   FROM \`cbi-v14.forecasting_data_warehouse.weather_data\`"
```
**Target:** days_stale <= 2

---

### Phase 5: Validation (10 minutes)

**5.1 Data Quality Checks**
```bash
# Check all views return data
for view in fct_market_indicators_daily fct_weather_daily fct_zl_price_volatility_daily fct_dashboard_executive; do
  echo "Testing $view..."
  bq query --use_legacy_sql=false "SELECT COUNT(*) as row_count FROM \`cbi-v14.curated.$view\`"
done
```

**5.2 Freshness Check**
```sql
SELECT 
  'fct_dashboard_executive' AS view_name,
  MAX(date) AS latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) AS days_behind
FROM `cbi-v14.curated.fct_dashboard_executive`;
```
**Expected:** days_behind <= 2

**5.3 Schema Validation**
```bash
# Verify all expected columns exist
bq show --schema cbi-v14:curated.fct_dashboard_executive | jq -r '.[].name'
```

---

## ROLLBACK PLAN

**If ANY view fails:**
```bash
# Drop failed view
bq rm -f cbi-v14:curated.FAILED_VIEW_NAME

# Check dependencies
bq ls -j cbi-v14:curated | grep FAILED_VIEW_NAME

# Restore from backup (if needed)
# Views don't have data, just recreate
```

**If weather pipeline can't be fixed:**
- Proceed with views anyway (weather is optional for dashboard)
- Dashboard will show weather_risk_index = 50 (default)
- Add TODO: Fix weather pipeline as separate task

---

## SUCCESS CRITERIA

**Phase 1 Success:**
- [ ] 3 datasets exist in us-central1
- [ ] `bq ls` shows curated, models, bkp
- [ ] No location mismatch errors

**Phase 2 Success:**
- [ ] All 4 canonical views created
- [ ] Each view returns >0 rows
- [ ] fct_dashboard_executive returns last 90 days
- [ ] No BigQuery errors

**Phase 3 Success:**
- [ ] ml_predictions table exists (0 rows OK for now)
- [ ] vw_ml_model_monitor view exists
- [ ] Table is partitioned and clustered

**Phase 4 Success:**
- [ ] weather_data is <3 days stale
- [ ] Brazil weather logs show success
- [ ] No Python errors in weather scripts

**Phase 5 Success:**
- [ ] All DQ checks pass
- [ ] No views with 0 rows (except ml_predictions)
- [ ] fct_dashboard_executive has data for today or yesterday

---

## ESTIMATED TIME

- Phase 1: 5 minutes
- Phase 2: 30 minutes (includes validation)
- Phase 3: 15 minutes
- Phase 4: 15 minutes (if weather works) or 30 minutes (if needs debugging)
- Phase 5: 10 minutes

**Total: 75-90 minutes**

---

## FILES CREATED SO FAR

✅ `sql/04_curated/01_fct_market_indicators_daily.sql`
✅ `sql/04_curated/02_fct_weather_daily.sql`
✅ `sql/04_curated/03_fct_zl_price_volatility_daily.sql`
✅ `sql/04_curated/04_fct_dashboard_executive.sql`

**Still Need:**
- [ ] `sql/05_models/ml_predictions_table.sql`
- [ ] `sql/05_models/vw_ml_model_monitor.sql`
- [ ] `scripts/validate_views.sh` (DQ automation)

---

## APPROVAL REQUIRED

**Question 1:** Proceed with Phase 1.2 (recreate datasets in us-central1)?
**Question 2:** Deploy TIER 1 views (market indicators, weather, ZL price)?
**Question 3:** Deploy TIER 2 view (dashboard executive)?
**Question 4:** Create ML infrastructure (predictions table + monitor)?
**Question 5:** Debug and fix weather pipeline?

**OR: Approve entire plan for execution?**

---

**Next Action:** Awaiting your approval to proceed.


