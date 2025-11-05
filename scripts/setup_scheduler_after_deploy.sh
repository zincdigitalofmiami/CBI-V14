#!/bin/bash
#
# Setup Cloud Scheduler after function is deployed via Console
# Run this AFTER the function is deployed and you have the URL
#

set -e

PROJECT="cbi-v14"
REGION="us-central1"
SCHEDULER_JOB="generate-forecasts-daily"
FUNCTION_NAME="generate-daily-forecasts"
SCHEDULE="0 7 * * *"  # 2 AM ET = 7 AM UTC
TIMEZONE="America/New_York"

echo "================================================================================"
echo "SETTING UP CLOUD SCHEDULER"
echo "================================================================================"

# Get function URL
echo "Getting function URL..."
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --region=$REGION \
  --gen2 \
  --format="value(serviceConfig.uri)" \
  --project=$PROJECT 2>&1)

if [ -z "$FUNCTION_URL" ] || [[ "$FUNCTION_URL" == *"ERROR"* ]]; then
    echo "❌ Error: Could not get function URL"
    echo "   Make sure the function is deployed first"
    echo "   Function: $FUNCTION_NAME"
    echo "   Region: $REGION"
    exit 1
fi

echo "✅ Function URL: $FUNCTION_URL"
echo ""

# Check if scheduler job already exists
if gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION --project=$PROJECT &>/dev/null; then
    echo "⚠️  Scheduler job already exists. Updating..."
    gcloud scheduler jobs update http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="$TIMEZONE" \
        --project=$PROJECT
    echo "✅ Scheduler job updated"
else
    echo "Creating scheduler job..."
    gcloud scheduler jobs create http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="$TIMEZONE" \
        --project=$PROJECT
    echo "✅ Scheduler job created"
fi

echo ""
echo "================================================================================"
echo "SCHEDULER SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "Schedule: Daily at 2:00 AM ET (7:00 AM UTC)"
echo "Function URL: $FUNCTION_URL"
echo ""
echo "Next steps:"
echo "1. Test function: curl -X POST $FUNCTION_URL"
echo "2. Check scheduler: gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION"
echo "3. Verify forecasts in BigQuery"

