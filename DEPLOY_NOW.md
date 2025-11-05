# Deploy Phase 3.5 Cloud Function - NOW

## Quick Deploy Link
https://console.cloud.google.com/functions/create?project=cbi-v14&region=us-central1

## Deployment Package
- Location: `/tmp/forecasts-deploy.zip`
- Size: 5.8K
- Contains: main.py, GENERATE_PRODUCTION_FORECASTS_V3.sql, requirements.txt

## Configuration
- Name: `generate-daily-forecasts`
- Region: `us-central1`
- Environment: `2nd gen`
- Runtime: `Python 3.11`
- Entry Point: `generate_daily_forecasts`
- Trigger: HTTP (Allow unauthenticated)
- Timeout: 540s
- Memory: 512MB

## Steps
1. Open the link above
2. Upload `/tmp/forecasts-deploy.zip`
3. Click Deploy
4. Wait 2-3 minutes

## After Deployment
We'll verify and test the function.

