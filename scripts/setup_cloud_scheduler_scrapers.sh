#!/bin/bash
#
# PHASE 0.2: Setup Cloud Scheduler for Web Scraping Jobs
# Deploys 4 Cloud Scheduler jobs to automate scraping
#

set -e

PROJECT="cbi-v14"
REGION="us-central1"

echo "================================================================================"
echo "SETTING UP CLOUD SCHEDULER FOR WEB SCRAPING"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Region: $REGION"
echo "================================================================================"

# Ensure Cloud Scheduler API is enabled
echo ""
echo "Enabling Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT

# ============================================================================
# JOB 1: Barchart Daily Scraper (Weekdays @ 4 PM UTC)
# ============================================================================
echo ""
echo "Creating Barchart daily scraper job..."
gcloud scheduler jobs create http scrape-barchart-daily \
  --location=$REGION \
  --schedule="0 16 * * 1-5" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/scrape-barchart-futures" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Daily Barchart futures scraping (weekdays 4 PM UTC)" \
  --project=$PROJECT \
  --attempt-deadline=540s \
  || echo "⚠️  Job may already exist"

# ============================================================================
# JOB 2: EPA RFS Daily Scraper (Daily @ Noon UTC)
# ============================================================================
echo ""
echo "Creating EPA RFS daily scraper job..."
gcloud scheduler jobs create http scrape-epa-daily \
  --location=$REGION \
  --schedule="0 12 * * *" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/scrape-epa-rfs" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Daily EPA RFS volume scraping (noon UTC)" \
  --project=$PROJECT \
  --attempt-deadline=300s \
  || echo "⚠️  Job may already exist"

# ============================================================================
# JOB 3: Federal Register 15-Minute Scraper
# ============================================================================
echo ""
echo "Creating Federal Register 15-minute scraper job..."
gcloud scheduler jobs create http scrape-federalregister-15min \
  --location=$REGION \
  --schedule="*/15 * * * *" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/scrape-federal-register" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Federal Register policy events (every 15 minutes)" \
  --project=$PROJECT \
  --attempt-deadline=240s \
  || echo "⚠️  Job may already exist"

# ============================================================================
# JOB 4: Reuters 30-Minute Scraper
# ============================================================================
echo ""
echo "Creating Reuters 30-minute scraper job..."
gcloud scheduler jobs create http scrape-reuters-30min \
  --location=$REGION \
  --schedule="*/30 * * * *" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/scrape-reuters-news" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Reuters commodities news (every 30 minutes)" \
  --project=$PROJECT \
  --attempt-deadline=300s \
  || echo "⚠️  Job may already exist"

# ============================================================================
# JOB 5: Comprehensive Web Scraper (Daily @ 9 AM & 4 PM UTC)
# ============================================================================
echo ""
echo "Creating comprehensive web scraper jobs..."
gcloud scheduler jobs create http scrape-comprehensive-morning \
  --location=$REGION \
  --schedule="0 9 * * 1-5" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/run-comprehensive-scraper" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Comprehensive web scraper - morning run (9 AM UTC weekdays)" \
  --project=$PROJECT \
  --attempt-deadline=600s \
  || echo "⚠️  Job may already exist"

gcloud scheduler jobs create http scrape-comprehensive-afternoon \
  --location=$REGION \
  --schedule="0 16 * * 1-5" \
  --uri="https://${REGION}-${PROJECT}.cloudfunctions.net/run-comprehensive-scraper" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Comprehensive web scraper - afternoon run (4 PM UTC weekdays)" \
  --project=$PROJECT \
  --attempt-deadline=600s \
  || echo "⚠️  Job may already exist"

# ============================================================================
# Verify all jobs created
# ============================================================================
echo ""
echo "================================================================================"
echo "Verifying Cloud Scheduler jobs..."
echo "================================================================================"
gcloud scheduler jobs list --location=$REGION --project=$PROJECT

echo ""
echo "================================================================================"
echo "✅ CLOUD SCHEDULER SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "Created jobs:"
echo "  1. scrape-barchart-daily        (weekdays 4 PM UTC)"
echo "  2. scrape-epa-daily             (daily noon UTC)"
echo "  3. scrape-federalregister-15min (every 15 minutes)"
echo "  4. scrape-reuters-30min         (every 30 minutes)"
echo "  5. scrape-comprehensive-morning (weekdays 9 AM UTC)"
echo "  6. scrape-comprehensive-afternoon (weekdays 4 PM UTC)"
echo ""
echo "Next steps:"
echo "  1. Deploy Cloud Functions for each scraper"
echo "  2. Test jobs: gcloud scheduler jobs run JOB_NAME --location=$REGION"
echo "  3. Monitor logs: gcloud scheduler jobs describe JOB_NAME --location=$REGION"
echo ""


