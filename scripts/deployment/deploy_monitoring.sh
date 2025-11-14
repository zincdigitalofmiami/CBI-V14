#!/bin/bash
#
# Deploy Prediction Monitoring Cloud Function
# This script deploys the monitoring function and sets up Cloud Scheduler
#

set -e  # Exit on error

PROJECT="cbi-v14"
FUNCTION_NAME="monitor-predictions"
SCHEDULER_JOB="monitor-predictions-daily"
REGION="us-central1"
SCHEDULE="15 7 * * *"  # 15 minutes after forecast generation (2:15 AM ET = 7:15 AM UTC)
TIMEZONE="America/New_York"

echo "================================================================================"
echo "DEPLOYING PREDICTION MONITORING CLOUD FUNCTION"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Schedule: $SCHEDULE ($TIMEZONE)"
echo "================================================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if authenticated
echo "Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated. Run: gcloud auth login"
    exit 1
fi

# Set project
echo "Setting project to $PROJECT..."
gcloud config set project $PROJECT

# Create temporary directory for Cloud Function deployment
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Copy function file
cp scripts/monitor_predictions.py "$TEMP_DIR/main.py"

# Create requirements.txt for Cloud Function
cat > "$TEMP_DIR/requirements.txt" << EOF
google-cloud-bigquery>=3.11.0
google-cloud-functions>=1.12.0
flask>=2.3.0
EOF

# Deploy Cloud Function
echo ""
echo "Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source="$TEMP_DIR" \
    --entry-point=monitor_predictions \
    --trigger-http \
    --allow-unauthenticated \
    --timeout=300s \
    --memory=256MB \
    --max-instances=1 \
    --project=$PROJECT

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --gen2 --format="value(serviceConfig.uri)")

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Error: Could not get function URL"
    exit 1
fi

echo ""
echo "✅ Cloud Function deployed successfully!"
echo "   URL: $FUNCTION_URL"

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
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Test the function: curl -X POST $FUNCTION_URL"
echo "2. Check scheduler: gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION"
echo "3. View logs: gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=50"
echo ""
echo "To manually trigger:"
echo "  gcloud scheduler jobs run $SCHEDULER_JOB --location=$REGION"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "================================================================================"
echo "DEPLOYMENT COMPLETE"
echo "================================================================================"

