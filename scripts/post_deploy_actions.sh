#!/bin/bash
#
# Post-deployment actions: Setup scheduler, test, verify
# Run after function is deployed via Console
#

set -e

PROJECT="cbi-v14"
REGION="us-central1"
FUNCTION_NAME="generate-daily-forecasts"
SCHEDULER_JOB="generate-forecasts-daily"

echo "================================================================================"
echo "POST-DEPLOYMENT SETUP"
echo "================================================================================"

# Step 1: Get function URL
echo ""
echo "Step 1: Getting function URL..."
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --region=$REGION \
  --gen2 \
  --format="value(serviceConfig.uri)" \
  --project=$PROJECT 2>&1)

if [ -z "$FUNCTION_URL" ] || [[ "$FUNCTION_URL" == *"ERROR"* ]] || [[ "$FUNCTION_URL" == *"not found"* ]]; then
    echo "❌ Error: Function not found or not accessible"
    echo "   Make sure the function is fully deployed"
    exit 1
fi

echo "✅ Function URL: $FUNCTION_URL"
echo ""

# Step 2: Setup Scheduler
echo "Step 2: Setting up Cloud Scheduler..."
if gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION --project=$PROJECT &>/dev/null; then
    echo "⚠️  Scheduler job already exists. Updating..."
    gcloud scheduler jobs update http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="0 7 * * *" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="America/New_York" \
        --project=$PROJECT
    echo "✅ Scheduler updated"
else
    gcloud scheduler jobs create http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="0 7 * * *" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="America/New_York" \
        --project=$PROJECT
    echo "✅ Scheduler created"
fi
echo ""

# Step 3: Test Function
echo "Step 3: Testing function..."
echo "Calling: $FUNCTION_URL"
TEST_RESPONSE=$(curl -s -X POST "$FUNCTION_URL" 2>&1)
TEST_STATUS=$?

if [ $TEST_STATUS -eq 0 ]; then
    echo "✅ Function responded"
    echo "Response:"
    echo "$TEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TEST_RESPONSE"
else
    echo "⚠️  Function test failed (status: $TEST_STATUS)"
    echo "Response: $TEST_RESPONSE"
fi
echo ""

# Step 4: Verify Forecasts
echo "Step 4: Verifying forecasts in BigQuery..."
bq query --use_legacy_sql=false --format=prettyjson "
SELECT 
  forecast_date,
  horizon,
  predicted_value,
  confidence,
  model_name,
  created_at
FROM \`cbi-v14.predictions_uc1.production_forecasts\`
ORDER BY created_at DESC
LIMIT 10
" 2>&1 | head -30

echo ""
echo "================================================================================"
echo "POST-DEPLOYMENT SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "✅ Scheduler: Daily at 2:00 AM ET (7:00 AM UTC)"
echo "✅ Function URL: $FUNCTION_URL"
echo ""
echo "Next steps:"
echo "  - Function will run daily at 2 AM ET"
echo "  - Forecasts will be in: cbi-v14.predictions_uc1.production_forecasts"
echo "  - Monitor logs: gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2"

