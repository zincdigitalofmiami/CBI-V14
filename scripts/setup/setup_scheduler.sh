#!/bin/bash
#
# Post-Deployment: Setup Cloud Scheduler for Daily Forecasts
# Run this AFTER the Cloud Function is deployed via Console
#

set -e

PROJECT="cbi-v14"
FUNCTION_NAME="generate-daily-forecasts"
SCHEDULER_JOB="generate-forecasts-daily"
REGION="us-central1"
SCHEDULE="0 7 * * *"  # 2 AM ET = 7 AM UTC
TIMEZONE="America/New_York"

echo "================================================================================"
echo "SETTING UP CLOUD SCHEDULER FOR DAILY FORECASTS"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Function: $FUNCTION_NAME"
echo "Scheduler: $SCHEDULER_JOB"
echo "Schedule: $SCHEDULE ($TIMEZONE)"
echo "================================================================================"

# Get function URL
echo ""
echo "Getting function URL..."
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --region=$REGION --gen2 \
  --format="value(serviceConfig.uri)" \
  --project=$PROJECT 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Error: Could not get function URL"
    echo "   Make sure the function is deployed first!"
    echo "   Check: gcloud functions list --region=$REGION --gen2"
    exit 1
fi

echo "✅ Function URL: $FUNCTION_URL"

# Check if scheduler job already exists
if gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION --project=$PROJECT &>/dev/null; then
    echo ""
    echo "⚠️  Scheduler job already exists. Updating..."
    gcloud scheduler jobs update http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="$TIMEZONE" \
        --project=$PROJECT
    
    echo "✅ Scheduler job updated!"
else
    echo ""
    echo "Creating Cloud Scheduler job..."
    gcloud scheduler jobs create http $SCHEDULER_JOB \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="$TIMEZONE" \
        --project=$PROJECT
    
    echo "✅ Scheduler job created!"
fi

# Verify scheduler
echo ""
echo "Verifying scheduler configuration..."
gcloud scheduler jobs describe $SCHEDULER_JOB \
    --location=$REGION \
    --project=$PROJECT \
    --format="yaml"

echo ""
echo "================================================================================"
echo "✅ SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Test function: curl -X POST $FUNCTION_URL"
echo "2. Check logs: gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=50"
echo "3. Manually trigger: gcloud scheduler jobs run $SCHEDULER_JOB --location=$REGION"
echo ""
echo "Function URL: $FUNCTION_URL"
echo "Scheduler will run daily at 2:00 AM ET (7:00 AM UTC)"
echo ""

