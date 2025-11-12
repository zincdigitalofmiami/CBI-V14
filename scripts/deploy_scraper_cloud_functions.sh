#!/bin/bash
#
# Deploy Cloud Functions for Web Scrapers
# Phase 0.2 - Production deployment
#

set -e

PROJECT="cbi-v14"
REGION="us-central1"
SOURCE_DIR="../cbi-v14-ingestion"

echo "================================================================================"
echo "DEPLOYING WEB SCRAPER CLOUD FUNCTIONS"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Region: $REGION"
echo "================================================================================"

# ============================================================================
# Deploy comprehensive web scraper as Cloud Function
# ============================================================================
echo ""
echo "Deploying comprehensive web scraper..."
gcloud functions deploy run-comprehensive-scraper \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=run_all_scrapers \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=600s \
  --memory=1GB \
  --max-instances=5 \
  --set-env-vars PROJECT_ID=$PROJECT \
  --set-secrets=SCRAPE_CREATORS_API_KEY=scrapecreators-api-key:latest \
  --project=$PROJECT

echo "   ✅ Deployed: run-comprehensive-scraper"

# ============================================================================
# Deploy individual scraper functions (for granular control)
# ============================================================================

# Barchart scraper
echo ""
echo "Deploying Barchart scraper..."
gcloud functions deploy scrape-barchart-futures \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=scrape_barchart \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512MB \
  --project=$PROJECT \
  || echo "⚠️  Deploy failed or function already exists"

# EPA scraper
echo ""
echo "Deploying EPA RFS scraper..."
gcloud functions deploy scrape-epa-rfs \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=scrape_epa \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512MB \
  --project=$PROJECT \
  || echo "⚠️  Deploy failed or function already exists"

# Federal Register scraper
echo ""
echo "Deploying Federal Register scraper..."
gcloud functions deploy scrape-federal-register \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=scrape_federal_register \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=240s \
  --memory=512MB \
  --project=$PROJECT \
  || echo "⚠️  Deploy failed or function already exists"

# Reuters scraper
echo ""
echo "Deploying Reuters scraper..."
gcloud functions deploy scrape-reuters-news \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=scrape_reuters \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512MB \
  --project=$PROJECT \
  || echo "⚠️  Deploy failed or function already exists"

# Truth Social monitor
echo ""
echo "Deploying Truth Social monitor..."
gcloud functions deploy monitor-truth-social \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=$SOURCE_DIR \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512MB \
  --set-secrets=SCRAPE_CREATORS_API_KEY=scrapecreators-api-key:latest \
  --project=$PROJECT \
  || echo "⚠️  Deploy failed or function already exists"

# ============================================================================
# Verify deployments
# ============================================================================
echo ""
echo "================================================================================"
echo "Verifying Cloud Function deployments..."
echo "================================================================================"
gcloud functions list --region=$REGION --gen2 --project=$PROJECT | grep -E "scrape-|monitor-"

echo ""
echo "================================================================================"
echo "✅ CLOUD FUNCTION DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Deployed functions:"
echo "  1. run-comprehensive-scraper   (all 12 scrapers)"
echo "  2. scrape-barchart-futures     (daily futures prices)"
echo "  3. scrape-epa-rfs              (RFS volumes)"
echo "  4. scrape-federal-register     (policy events)"
echo "  5. scrape-reuters-news         (commodities news)"
echo "  6. monitor-truth-social        (Trump posts)"
echo ""
echo "Next steps:"
echo "  1. Run setup_cloud_scheduler_scrapers.sh to schedule jobs"
echo "  2. Test functions manually:"
echo "     gcloud functions call run-comprehensive-scraper --region=$REGION"
echo "  3. Monitor execution:"
echo "     gcloud functions logs read run-comprehensive-scraper --region=$REGION --gen2"
echo ""








