# CBI-V14 CURSOR RULES (MASTER)

**Last Updated:** October 7, 2025  
**Status:** ACTIVE AND ENFORCED

---

## 🎯 CORE PRINCIPLES

1. **Read plan.md as reference** - Don't edit automatically, user updates manually
2. **NO MOCK DATA - EVER** - All data from BigQuery or show "No data yet"
3. **NO NEW TABLES** without explicit permission
4. **BUDGET CONSCIOUS** - Keep costs <$1/month, max $275-300/month total
5. **EXISTING SCHEMA ONLY** - Route to existing tables, add columns (don't drop/rename)

---

## 🚨 CRITICAL RULES (ZERO TOLERANCE)

### RULE #1: NO MOCK DATA - EVER
- ❌ Placeholder values, hardcoded arrays, fake data
- ❌ mockData.js, fixtures.js, sampleData.js files
- ❌ faker.js or data generation libraries
- ✅ Query actual BigQuery tables
- ✅ Show empty states when no data
- ✅ Display real row counts and timestamps

### RULE #2: BIGQUERY AS SOURCE OF TRUTH
- ✅ Primary: `cbi-v14.forecasting_data_warehouse`
- ✅ All tables partitioned and clustered
- ✅ Never query production from frontend directly
- ✅ FastAPI → BigQuery → Vite dashboard

### RULE #3: NO HARDCODED CREDENTIALS
- ❌ API keys in code (use Secret Manager or env vars)
- ❌ Service account JSONs in repo
- ✅ Environment variables: PROJECT, DATASET, GOOGLE_APPLICATION_CREDENTIALS
- ✅ Store secrets in Google Secret Manager

### RULE #4: PROTECT EXISTING RESOURCES
**EXISTING BIGQUERY TABLES (38 total):**
```
Core Data:
- weather_data, economic_indicators, currency_data, fed_rates
- soybean_oil_prices, soybean_prices, soybean_meal_prices
- corn_prices, cotton_prices, commodity_prices_archive
- ice_trump_intelligence, news_intelligence, social_sentiment
- palm_oil_prices ✅ JUST CREATED
- palm_oil_fundamentals ✅ JUST CREATED

Models:
- zl_arima_baseline, zl_arima_xreg, zl_arima_backtest

Views (30+):
- vw_weather_daily, vw_economic_daily, vw_soy_palm_spread, etc.
```

**WHITELISTED FOLDERS:**
- `cbi-v14-ingestion/` (data pipelines)
- `forecast/` (ML and API)
- `bigquery_sql/` (SQL scripts)
- `dashboard/` (Vite frontend)

**BANNED:**
- ❌ Tables with: _test, _staging, _backup, _tmp (unless approved)
- ❌ Folders: tmp/, temp/, backup/, test/
- ❌ Files: *_test.py, *_backup.py, *.bak
- ❌ DROP TABLE (without explicit confirmation)
- ❌ Renaming existing tables (breaks Vite dashboards)

---

## ✅ VERIFICATION BEFORE ACTION

### Before Creating Resources:
```bash
# 1. Check if table exists
bq ls cbi-v14:forecasting_data_warehouse | grep table_name

# 2. Check whitelist - is it approved?

# 3. ASK USER if not on whitelist
```

### Before Modifying Files:
```bash
# 1. Check file exists
ls -la path/to/file

# 2. Show current state
cat existing_file.py | head -20

# 3. Never assume empty state
```

### Before BigQuery Operations:
```bash
# 1. Verify table exists
bq show cbi-v14:forecasting_data_warehouse.table_name

# 2. Check row count
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `cbi-v14.forecasting_data_warehouse.table_name`'

# 3. Confirm with user for DROP/RENAME
```

---

## 🔧 REQUIRED PATTERNS

### Environment Variables (Python)
```python
# CORRECT
import os
PROJECT = os.environ["PROJECT"]  # Fails if not set
DATASET = os.environ["DATASET"]

# WRONG
PROJECT = "cbi-v14"  # Hardcoded
PROJECT = os.environ.get("PROJECT", "cbi-v14")  # Has default
```

### BigQuery Queries
```python
# CORRECT
query = f"""
SELECT * FROM `{PROJECT}.{DATASET}.table_name`
WHERE date > @start_date
"""

# WRONG
query = "SELECT * FROM cbi-v14.forecasting_data_warehouse.table_name"  # Hardcoded
```

### Adding Columns (Not Dropping)
```sql
-- CORRECT
ALTER TABLE `cbi-v14.forecasting_data_warehouse.weather_data`
ADD COLUMN IF NOT EXISTS source_name STRING;

-- WRONG
ALTER TABLE `cbi-v14.forecasting_data_warehouse.weather_data`
DROP COLUMN old_field;  -- BREAKS DASHBOARDS
```

---

## 📋 DEVELOPMENT WORKFLOW

### Git Workflow
```bash
# 1. Create feature branch
git checkout -b feature/description

# 2. Make changes

# 3. Check rules BEFORE committing
make check-rules
make lint

# 4. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat(scope): description"

# 5. Push
git push origin feature/description
```

### Commit Message Format
```
<type>(<scope>): <subject>

Types: feat, fix, refactor, docs, test, chore
Scope: ingestion, forecast, dashboard, bigquery
```

---

## 🚫 BANNED BEHAVIORS

- ❌ Editing plan.md automatically (user updates manually)
- ❌ Mock/fake/placeholder data
- ❌ Creating tables not on whitelist without permission
- ❌ Creating temp/test/staging folders
- ❌ DROP TABLE without explicit user confirmation
- ❌ Renaming existing tables/columns (breaks Vite)
- ❌ Hardcoded credentials in code
- ❌ Docker/Docker Compose

---

## ✅ REQUIRED BEHAVIORS

- ✅ `ls` before create
- ✅ `cat` before overwrite
- ✅ `bq ls` before table operations
- ✅ Ask when uncertain
- ✅ Real data or explicit "no data" states
- ✅ Keep plan.md as single source of truth
- ✅ Route to existing tables (don't create new ones)
- ✅ Add columns (don't drop/rename)
- ✅ Test locally before committing
- ✅ Check budget impact before new services

---

## 💰 BUDGET RULES

- **Current BigQuery cost:** $0.71/month
- **Maximum budget:** $275-300/month total
- **New data sources:** Must be <$20/month (max 3 allowed)
- **Always ask** before adding paid services
- **Prefer free scraping** over paid APIs

---

## 📊 CURRENT PROJECT STATUS

**Tables:** 38 existing (2 palm oil tables just created)  
**Scrapers:** TradingEconomics (50+ URLs hourly, $0/month)  
**ML Models:** 3 ARIMA models operational  
**Vite Dashboard:** Operational, queries existing tables  
**Cost:** $0.71/month (well under budget)

---

**Version:** 2.0 (Consolidated from PROJECT_RULES.md, RULES_ACTIVE.md)  
**Enforcement:** Active (pre-commit hooks, CI/CD)  
**Next Review:** After 48-hour sprint completion



