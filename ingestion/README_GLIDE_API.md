# Glide API Integration - Setup Instructions

## Current Status
- ✅ BigQuery tables created: `vegas_customers`, `vegas_fryers`, `vegas_events`
- ✅ Ingestion script created: `ingest_glide_vegas_data.py`
- ⚠️ Glide API authentication needs fixing

## Glide API Issue
The Glide API is returning "400 Bad Request". Possible causes:
1. API endpoint format changed
2. Authentication token expired or format incorrect
3. Table IDs changed
4. API requires different request structure

## Alternative Approaches

### Option 1: Fix Glide API (Recommended)
1. Check Glide App settings for API credentials
2. Verify table IDs are correct
3. Check Glide API documentation for current endpoint format
4. Update `GLIDE_BEARER_TOKEN` and `GLIDE_APP_ID` if needed

### Option 2: Use Glide's BigQuery Integration
If Glide is already syncing to BigQuery:
1. Check if tables exist in BigQuery (query INFORMATION_SCHEMA)
2. If data exists, update ingestion script to read from existing tables
3. No API calls needed - data already in BigQuery

### Option 3: Manual Data Export
1. Export data from Glide App manually
2. Load CSV files to BigQuery using `bq load` command
3. Schedule regular exports

## Running the Script
Once API is fixed:
```bash
cd /Users/zincdigital/CBI-V14
python3 cbi-v14-ingestion/ingest_glide_vegas_data.py
```

## Expected BigQuery Tables
- `cbi-v14.forecasting_data_warehouse.vegas_customers`
- `cbi-v14.forecasting_data_warehouse.vegas_fryers`  
- `cbi-v14.forecasting_data_warehouse.vegas_events`

## Next Steps
1. Verify Glide API credentials with Glide support
2. Test API endpoint with correct format
3. Run ingestion script
4. Verify data appears in BigQuery
5. Dashboard will automatically display real data

## NO FAKE DATA POLICY
- Script returns empty arrays if API fails
- Dashboard shows "No data" messages if tables are empty
- No placeholders, no mock data, no defaults


