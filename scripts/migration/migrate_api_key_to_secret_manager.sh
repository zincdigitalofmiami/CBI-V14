#!/bin/bash
#
# Migrate Scrape Creators API Key to Google Secret Manager
# Security enhancement per memory 9658867
#

set -e

PROJECT="cbi-v14"
SECRET_NAME="scrapecreators-api-key"
API_KEY="B1TOgQvMVSV6TDglqB8lJ2cirqi2"

echo "================================================================================"
echo "MIGRATING SCRAPE CREATORS API KEY TO SECRET MANAGER"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Secret: $SECRET_NAME"
echo "================================================================================"

# Enable Secret Manager API
echo ""
echo "Step 1: Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT

# Create secret
echo ""
echo "Step 2: Creating secret..."
echo -n "$API_KEY" | gcloud secrets create $SECRET_NAME \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT \
  || echo "⚠️  Secret may already exist, attempting to add version..."

# Add new version if secret exists
echo -n "$API_KEY" | gcloud secrets versions add $SECRET_NAME \
  --data-file=- \
  --project=$PROJECT \
  2>/dev/null || echo "Using existing secret"

# Grant access to compute service account
echo ""
echo "Step 3: Granting access to service accounts..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding $SECRET_NAME \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT

# Also grant to Cloud Functions service account
CLOUD_FUNCTIONS_SA="${PROJECT}@appspot.gserviceaccount.com"
gcloud secrets add-iam-policy-binding $SECRET_NAME \
  --member="serviceAccount:${CLOUD_FUNCTIONS_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT \
  2>/dev/null || echo "Cloud Functions SA may not exist yet"

# Verify secret exists
echo ""
echo "Step 4: Verifying secret..."
gcloud secrets describe $SECRET_NAME --project=$PROJECT

echo ""
echo "================================================================================"
echo "✅ SECRET MIGRATION COMPLETE"
echo "================================================================================"
echo ""
echo "Secret name: $SECRET_NAME"
echo "Project: $PROJECT"
echo "Access granted to:"
echo "  - Compute Engine SA: $COMPUTE_SA"
echo "  - Cloud Functions SA: $CLOUD_FUNCTIONS_SA"
echo ""
echo "Usage in Python:"
echo ""
echo "from google.cloud import secretmanager"
echo "client = secretmanager.SecretManagerServiceClient()"
echo "name = f\"projects/$PROJECT/secrets/$SECRET_NAME/versions/latest\""
echo "response = client.access_secret_version(request={\"name\": name})"
echo "api_key = response.payload.data.decode(\"UTF-8\")"
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Update social_intelligence.py to use Secret Manager"
echo "  2. Update trump_truth_social_monitor.py (already configured)"
echo "  3. Remove hardcoded API key from source files"
echo "  4. Rotate API key at Scrape Creators"
echo ""








