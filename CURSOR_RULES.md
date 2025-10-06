# Cursor AI Rules for CBI-V14

## Core Principle
**Read plan.md as reference. Don't try to edit it automatically.**

The plan.md file is documentation, not a live tracking system. Reference it to understand project goals, but user updates it manually.

## CRITICAL: Protect the Working Forecast

- Do not modify, rename, or drop `forecasting_data_warehouse.soybean_oil_forecast`.
- FastAPI endpoints must continue reading from `soybean_oil_forecast` unless the user explicitly approves a change.
- Any new modeling or data joins happen in new resources suffixed `_v2` and require approval before cutover.

## CRITICAL: No Mock Data

**Every component must use real data from BigQuery or show "No data yet"**

- ❌ Placeholder values
- ❌ Hardcoded sample data
- ❌ Mock API responses
- ✅ Query actual BigQuery tables
- ✅ Show empty states when tables have no data
- ✅ Display real row counts and timestamps

## CRITICAL: No Temporary Resources

**WHITELISTED TABLES ONLY:**
soybean_prices_clean, soybean_oil_forecast, weather_data, volatility_data, news_intelligence, economic_indicators, technical_signals, fed_rates, commodity_prices

**WHITELISTED FOLDERS ONLY:**
cbi-v14-ingestion/, forecast/, bigquery_sql/

**BANNED:**
- ❌ Any table not in whitelist
- ❌ Tables with: _test, _staging, _backup, _tmp, _v2 (unless explicitly approved)
- ❌ Folders: tmp/, temp/, backup/, test/, staging/
- ❌ Files: *_test.py, *_backup.py, *.bak

## No Docker

- We do not use Docker or Docker Compose for local work. Do not introduce images, compose files, or container-only steps.

## Environment Variables

- Always read `PROJECT_ID` and `DATASET_ID` environment variables. Do not concatenate project and dataset into a single ID. Example: `bigquery.Client(project=PROJECT_ID)`.

## Before Creating ANY Resource
1. Check whitelist: Is this table/folder explicitly allowed?
2. If NO: STOP and ask user
3. If YES: Verify it doesn't already exist

## Verification Before Action

### 1. Check if files exist
```
ls -la path/to/file
```

### 2. Show current state first
```
cat existing_file.py | head -20
```

### 3. Never assume empty state

- Check BigQuery tables:
```
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM `project.dataset.table`'
```
- Check packages: `pip3 list | grep package`
- Check git: `git status`

## Before Major Work: Architecture Review

- Run `bq ls cbi-v14:forecasting_data_warehouse`
- Verify against whitelists
- Confirm approach with user

## Banned Behaviors

- ❌ Editing plan.md automatically
- ❌ Mock/fake/placeholder data
- ❌ Creating tables not on whitelist
- ❌ Creating temp/test/staging folders
- ❌ Running DROP TABLE without explicit confirmation

## Required Behaviors

- ✅ `ls` before create
- ✅ `cat` before overwrite
- ✅ `bq ls`/`INFORMATION_SCHEMA` before table operations
- ✅ Architecture audit before new phases
- ✅ Real data or explicit "no data" states
- ✅ Ask when uncertain
- ✅ Keep `plan.md` as the single source of truth for status and scope


