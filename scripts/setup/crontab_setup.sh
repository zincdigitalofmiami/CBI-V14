#!/bin/bash
#
# CBI-V14 CRON CONFIGURATION (2025-11 REFRESH)
# Installs the production ingestion and monitoring schedule using the current
# repository layout on macOS (Apple Silicon) hosts.
#
# Usage:
#   ./crontab_setup.sh
# Optional:
#   PYTHON_BIN=/opt/homebrew/bin/python3 ./crontab_setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
INGESTION_DIR="$REPO_ROOT/src/ingestion"
SCRIPTS_DIR="$REPO_ROOT/scripts"
LOG_DIR="$REPO_ROOT/Logs/cron"
ENV_FILE="$REPO_ROOT/.env.cron"

mkdir -p "$LOG_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "❌ PYTHON_BIN does not point to an executable (PYTHON_BIN=$PYTHON_BIN)" >&2
  exit 1
fi

if [[ ! -d "$INGESTION_DIR" ]]; then
  echo "❌ Could not locate ingestion directory at $INGESTION_DIR" >&2
  exit 1
fi

# Create .env.cron template if it doesn't exist (BEFORE checking for it)
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<ENV_TEMPLATE
# CBI-V14 Environment Variables for Cron Jobs
# This file is automatically sourced by cron jobs
# Created: $(date '+%Y-%m-%d %H:%M:%S')

# Google Cloud Credentials (REQUIRED for BigQuery)
# Uncomment and set path to your service account key file:
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# API Keys (do not commit secrets; set via Keychain or environment)
# export FRED_API_KEY="<set-via-keychain-or-env>"
# export NOAA_API_TOKEN="<set-via-keychain-or-env>"
# export SCRAPECREATORS_API_KEY="<set-via-keychain-or-env>"

# Project Configuration
export PROJECT_ID="cbi-v14"
export DATASET_ID="forecasting_data_warehouse"

# Repository Paths
export CBI_REPO_ROOT="$REPO_ROOT"
export CBI_INGESTION_DIR="$INGESTION_DIR"
export CBI_SCRIPTS_DIR="$SCRIPTS_DIR"
export CBI_LOG_DIR="$LOG_DIR"

# Timezone
export TZ="America/New_York"

# Python Environment (if using conda/venv)
# export CONDA_ENV="cbi-v14"
# export VIRTUAL_ENV="/path/to/venv"

ENV_TEMPLATE
  echo "✅ Created $ENV_FILE with template configuration"
  echo "⚠️  Please edit $ENV_FILE to add your Google Cloud credentials"
fi

ENV_SOURCE=""
if [[ -f "$ENV_FILE" ]]; then
  ENV_SOURCE=". \"$ENV_FILE\" && "
fi

TEMP_CRON="$(mktemp /tmp/cbi_v14_cron.XXXXXX)"

cat > "$TEMP_CRON" <<EOF
# ====================================================================
# CBI-V14 PRODUCTION INGESTION SCHEDULE
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
# Repository: $REPO_ROOT
# ====================================================================
SHELL=/bin/zsh
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin

# --------------------------------------------------------------------
# DAILY CORE INGESTION (UTC-5, local time)
# --------------------------------------------------------------------
# Weather Data (NOAA API)
30 5 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_weather_noaa.py >> $LOG_DIR/weather_noaa.log 2>&1
45 5 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_brazil_weather_inmet.py >> $LOG_DIR/weather_brazil.log 2>&1

# Market & Price Data
0 6 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_epa_rin_prices.py >> $LOG_DIR/biofuel_prices.log 2>&1
15 6 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_volatility.py >> $LOG_DIR/volatility.log 2>&1
30 6 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_market_prices.py >> $LOG_DIR/market_prices.log 2>&1
0 7 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_baltic_dry_index.py >> $LOG_DIR/baltic_dry_index.log 2>&1

# FRED Economic Data
15 7 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} fred_economic_deployment.py >> $LOG_DIR/fred_economic.log 2>&1

# Social Intelligence & Scrape Creators
0 */4 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_social_intelligence_comprehensive.py >> $LOG_DIR/social_intel.log 2>&1
30 */6 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_scrapecreators_institutional.py >> $LOG_DIR/scrapecreators_institutional.log 2>&1
0 8 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} scrape_creators_full_blast.py >> $LOG_DIR/scrapecreators_full.log 2>&1
0 */4 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} trump_truth_social_monitor.py >> $LOG_DIR/trump_social.log 2>&1

# Multi-source collector during market hours (Mon-Fri)
0 9,12,15 * * 1-5 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} multi_source_collector.py >> $LOG_DIR/multi_source.log 2>&1

# --------------------------------------------------------------------
# QUALITY & MONITORING
# --------------------------------------------------------------------
30 8 * * * cd $SCRIPTS_DIR && ${ENV_SOURCE}${PYTHON_BIN} data_quality_checks.py >> $LOG_DIR/data_quality.log 2>&1
0 9 * * * cd $SCRIPTS_DIR && ${ENV_SOURCE}${PYTHON_BIN} check_stale_data.py >> $LOG_DIR/stale_check.log 2>&1
30 9 * * * cd $SCRIPTS_DIR && ${ENV_SOURCE}${PYTHON_BIN} find_missing_data.py >> $LOG_DIR/missing_data.log 2>&1

# --------------------------------------------------------------------
# WEEKLY SOURCES
# --------------------------------------------------------------------
# EIA Biofuel Production (Wednesday)
0 10 * * 3 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_eia_biofuel_real.py >> $LOG_DIR/eia_biofuel.log 2>&1

# USDA Data (Thursday)
0 15 * * 4 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_usda_harvest_api.py >> $LOG_DIR/usda_exports.log 2>&1
30 15 * * 4 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_usda_export_sales_weekly.py >> $LOG_DIR/usda_export_sales.log 2>&1

# CFTC Positioning Data (Friday)
0 17 * * 5 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_cftc_positioning_REAL.py >> $LOG_DIR/cftc.log 2>&1

# --------------------------------------------------------------------
# ADDITIONAL API-BASED INGESTION
# --------------------------------------------------------------------
# China Trade Data (UN Comtrade API - monthly, runs on 1st of month)
0 14 1 * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_china_imports_uncomtrade.py >> $LOG_DIR/china_imports.log 2>&1

# Argentina Port Logistics (daily)
45 7 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_argentina_port_logistics.py >> $LOG_DIR/argentina_logistics.log 2>&1

# EPA RFS Mandates (weekly, Monday)
0 11 * * 1 cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_epa_rfs_mandates.py >> $LOG_DIR/epa_rfs.log 2>&1

# ENSO Climate Data (monthly, 1st of month)
0 13 1 * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_enso_climate.py >> $LOG_DIR/enso_climate.log 2>&1

# White House RSS Feed (daily)
30 8 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_whitehouse_rss.py >> $LOG_DIR/whitehouse_rss.log 2>&1

# Policy RSS Feeds (daily)
45 8 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} ingest_rss_feeds_policy.py >> $LOG_DIR/policy_rss.log 2>&1

# GDELT China Intelligence (every 6 hours)
0 */6 * * * cd $INGESTION_DIR && ${ENV_SOURCE}${PYTHON_BIN} gdelt_china_intelligence.py >> $LOG_DIR/gdelt_china.log 2>&1

# --------------------------------------------------------------------
# DAILY TRAINING & PREDICTION PIPELINE
# --------------------------------------------------------------------
# Build Features (Daily 3:30 AM)
30 3 * * * cd $SCRIPTS_DIR && ${ENV_SOURCE}${PYTHON_BIN} build_features.py --horizon=all >> $LOG_DIR/build_features.log 2>&1

# Daily Model Retraining (Daily 4 AM)
0 4 * * * cd $REPO_ROOT && ${ENV_SOURCE}${PYTHON_BIN} vertex-ai/deployment/train_local_deploy_vertex.py --horizon=1m --skip-deploy >> $LOG_DIR/daily_training.log 2>&1

# Daily Prediction Generation (Daily 5 AM)
0 5 * * * cd $REPO_ROOT && ${ENV_SOURCE}${PYTHON_BIN} src/prediction/generate_forecasts.py --horizon=all >> $LOG_DIR/daily_forecasts.log 2>&1

# --------------------------------------------------------------------
# DAILY TRAINING DATA REFRESH
# --------------------------------------------------------------------
# Export fresh training data to external drive (Daily 3 AM - keeps training data current)
0 3 * * * cd $REPO_ROOT && ${ENV_SOURCE}${PYTHON_BIN} scripts/export_training_data.py >> $LOG_DIR/training_export.log 2>&1

# --------------------------------------------------------------------
# MONTHLY / MAINTENANCE
# --------------------------------------------------------------------
0 2 1 * * cd $SCRIPTS_DIR && ${ENV_SOURCE}bash monthly_vertex_predictions.sh >> $LOG_DIR/monthly_vertex.log 2>&1
0 2 * * 0 cd $SCRIPTS_DIR && ${ENV_SOURCE}${PYTHON_BIN} daily_data_pull_and_migrate.py >> $LOG_DIR/weekend_maintenance.log 2>&1

# --------------------------------------------------------------------
# HOUSEKEEPING
# --------------------------------------------------------------------
0 0 * * * find $LOG_DIR -name "*.log" -mtime +30 -delete
# END OF CBI-V14 SCHEDULE
EOF

echo "================================================================================"
echo "CBI-V14 CRONTAB PREVIEW"
echo "================================================================================"
cat "$TEMP_CRON"

echo ""
echo "Installing crontab..."
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"

echo "✅ Cron schedule installed for $REPO_ROOT"
echo ""
echo "Current entries:"
crontab -l

# Environment file already created above if it didn't exist
if [[ -f "$ENV_FILE" ]]; then
  echo "✅ Environment file exists at $ENV_FILE"
else
  echo "❌ Environment file was not created properly at $ENV_FILE"
fi
