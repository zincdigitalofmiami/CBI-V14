#!/bin/bash
#
# Verify Phase 3.5 Deployment
# Checks function status, tests execution, verifies forecasts
#

set -e

PROJECT="cbi-v14"
FUNCTION_NAME="generate-daily-forecasts"
REGION="us-central1"
DATASET="predictions_uc1"
TABLE="production_forecasts"

echo "================================================================================"
echo "VERIFYING PHASE 3.5 DEPLOYMENT"
echo "================================================================================"

# Check function exists
echo ""
echo "1. Checking Cloud Function status..."
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --region=$REGION --gen2 \
  --format="value(serviceConfig.uri)" \
  --project=$PROJECT 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Function not found!"
    echo "   Deploy function first via Cloud Console"
    exit 1
fi

echo "✅ Function found: $FUNCTION_URL"

# Check scheduler
echo ""
echo "2. Checking Cloud Scheduler..."
if gcloud scheduler jobs describe generate-forecasts-daily --location=$REGION --project=$PROJECT &>/dev/null; then
    echo "✅ Scheduler job exists"
    gcloud scheduler jobs describe generate-forecasts-daily \
        --location=$REGION \
        --project=$PROJECT \
        --format="value(schedule)" | head -1
else
    echo "⚠️  Scheduler job not found"
    echo "   Run: ./scripts/setup_scheduler.sh"
fi

# Test function
echo ""
echo "3. Testing function execution..."
echo "   Triggering function..."
RESPONSE=$(curl -s -X POST "$FUNCTION_URL" -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Function executed successfully"
    echo "   Response: $BODY" | head -5
else
    echo "❌ Function returned error (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi

# Check forecasts
echo ""
echo "4. Verifying forecasts in BigQuery..."
FORECAST_QUERY="SELECT COUNT(*) as count FROM \`$PROJECT.$DATASET.$TABLE\` WHERE forecast_date = CURRENT_DATE()"
FORECAST_COUNT=$(bq query --use_legacy_sql=false --format=csv "$FORECAST_QUERY" | tail -1)

if [ "$FORECAST_COUNT" -ge 4 ]; then
    echo "✅ Found $FORECAST_COUNT forecasts for today"
else
    echo "⚠️  Found $FORECAST_COUNT forecasts (expected 4+)"
fi

# Show forecast details
echo ""
echo "5. Forecast details:"
bq query --use_legacy_sql=false --format=prettyjson "
SELECT 
  horizon,
  forecast_date,
  target_date,
  predicted_value,
  confidence,
  model_name
FROM \`$PROJECT.$DATASET.$TABLE\`
WHERE forecast_date = CURRENT_DATE()
ORDER BY 
  CASE horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END
" | head -30

# Check logs
echo ""
echo "6. Recent function logs:"
gcloud functions logs read $FUNCTION_NAME \
  --region=$REGION --gen2 \
  --limit=10 \
  --project=$PROJECT 2>/dev/null | head -20 || echo "   No logs available yet"

echo ""
echo "================================================================================"
echo "VERIFICATION COMPLETE"
echo "================================================================================"

