#!/bin/bash
#
# Deploy Cloud Function via REST API (workaround for gcloud CLI bug)
#

set -e

PROJECT="cbi-v14"
FUNCTION_NAME="generate-daily-forecasts"
REGION="us-central1"
SOURCE_BUCKET="cbi-v14-function-source"
SOURCE_OBJECT="function-source.zip"

echo "================================================================================"
echo "DEPLOYING VIA CLOUD FUNCTIONS API"
echo "================================================================================"

# Get access token
echo "Getting access token..."
TOKEN=$(gcloud auth print-access-token)

# Get upload URL
echo "Getting upload URL..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  "https://cloudfunctions.googleapis.com/v2/projects/$PROJECT/locations/$REGION/functions:generateUploadUrl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | grep -o '"uploadUrl":"[^"]*' | cut -d'"' -f4)

if [ -z "$UPLOAD_URL" ]; then
    echo "❌ Failed to get upload URL"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Got upload URL"

# Upload source
echo "Uploading source code..."
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: application/zip" \
  --data-binary "@function-source.zip" \
  -o /dev/null -s

echo "✅ Source uploaded"

# Create function
echo "Creating function..."
CREATE_RESPONSE=$(curl -s -X POST \
  "https://cloudfunctions.googleapis.com/v2/projects/$PROJECT/locations/$REGION/functions?functionId=$FUNCTION_NAME" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "name": "projects/$PROJECT/locations/$REGION/functions/$FUNCTION_NAME",
  "buildConfig": {
    "runtime": "python311",
    "entryPoint": "generate_daily_forecasts",
    "source": {
      "storageSource": {
        "bucket": "$SOURCE_BUCKET",
        "object": "$SOURCE_OBJECT"
      }
    }
  },
  "serviceConfig": {
    "maxInstanceCount": 1,
    "availableMemory": "512M",
    "timeoutSeconds": 540,
    "ingressSettings": "ALLOW_ALL",
    "allTrafficOnLatestRevision": true
  },
  "eventTrigger": {
    "eventType": "google.cloud.pubsub.topic.v1.messagePublished",
    "pubsubTopic": "projects/$PROJECT/topics/$FUNCTION_NAME-topic"
  }
}
EOF
)

echo "Response: $CREATE_RESPONSE"

# For HTTP trigger, we need to use httpsTrigger instead
echo ""
echo "Note: This creates a Pub/Sub trigger. For HTTP trigger, use Cloud Console."
echo "See: scripts/DEPLOY_CONSOLE_GUIDE.md"

