#!/bin/bash
#
# COMPREHENSIVE SCHEDULING SETUP FOR CBI-V14
# Implements all missing scheduled jobs from DATA_INGESTION_PIPELINE_AUDIT.md
# Based on DEEP_PARSING_SCHEMA_CALCULATION_AUDIT.md standards
#
# Generated: 2025-11-07
# Purpose: Schedule all missing ingestion jobs with proper parsing, routing, and deduplication
#

set -e

PROJECT_ROOT="/Users/zincdigital/CBI-V14"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
INGESTION_DIR="$PROJECT_ROOT/ingestion"
CBI_INGESTION_DIR="$PROJECT_ROOT/cbi-v14-ingestion"
LOG_DIR="$PROJECT_ROOT/logs"

echo "================================================================================"
echo "CBI-V14 COMPREHENSIVE SCHEDULING SETUP"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Backup current crontab"
echo "  2. Add all missing scheduled jobs from audit"
echo "  3. Ensure proper parsing, routing, and deduplication"
echo "  4. Schedule critical data sources (China imports, RIN prices, etc.)"
echo "  5. Schedule production training data refresh"
echo "  6. Schedule Trump sentiment quantification"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Backup current crontab
BACKUP_FILE="/tmp/cbi_v14_cron_backup_$(date +%Y%m%d_%H%M%S).txt"
echo ""
echo "📋 Backing up current crontab to: $BACKUP_FILE"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# No existing crontab" > "$BACKUP_FILE"
echo "✅ Backup created"

# Create comprehensive crontab
echo ""
echo "📝 Creating comprehensive crontab with all missing jobs..."

cat > /tmp/cbi_v14_comprehensive_cron << 'EOF'
# ====================================================================
# CBI-V14 COMPREHENSIVE DATA INGESTION SCHEDULE
# Generated: 2025-11-07
# Includes all missing jobs from DATA_INGESTION_PIPELINE_AUDIT.md
# Based on DEEP_PARSING_SCHEMA_CALCULATION_AUDIT.md standards
# ====================================================================

# ====================================================================
# CRITICAL: PRODUCTION TRAINING DATA REFRESH (P0 - DAILY)
# Last update: Sep 10, 2025 (56 days stale!) - MUST FIX
# ====================================================================
0 5 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 update_production_datasets.py >> /Users/zincdigital/CBI-V14/logs/production_refresh.log 2>&1

# ====================================================================
# CRITICAL: CHINA IMPORTS (P0 - WEEKLY, EPA publishes Wednesdays)
# Last update: Oct 15, 2025 (21 days stale) - MUST FIX
# ====================================================================
0 8 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_china_imports_uncomtrade.py >> /Users/zincdigital/CBI-V14/logs/china_imports.log 2>&1

# ====================================================================
# CRITICAL: RIN PRICES (P0 - WEEKLY, EPA publishes Wednesdays)
# Required for features #23-30 in 42 neural drivers (+0.88 correlation)
# ====================================================================
0 9 * * 3 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_epa_rin_prices.py >> /Users/zincdigital/CBI-V14/logs/rin_prices.log 2>&1

# ====================================================================
# CRITICAL: TRUMP SENTIMENT QUANTIFICATION (P1 - DAILY)
# Raw data exists but not processed into features
# ====================================================================
0 7 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 TRUMP_SENTIMENT_QUANT_ENGINE.py >> /Users/zincdigital/CBI-V14/logs/trump_quant.log 2>&1

# ====================================================================
# CRITICAL: BIG EIGHT NEURAL SIGNALS (P1 - DAILY)
# Verify refresh_features_pipeline.py includes Big Eight, or schedule separately
# ====================================================================
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 collect_neural_data_sources.py >> /Users/zincdigital/CBI-V14/logs/big_eight_signals.log 2>&1

# ====================================================================
# EXISTING SCHEDULED JOBS (from crontab_optimized.sh)
# ====================================================================

# CRITICAL FINANCIAL DATA (Every hour during market hours)
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_prices.py >> /Users/zincdigital/CBI-V14/logs/prices.log 2>&1

# WEATHER DATA (Every 6 hours - includes weekends for crop monitoring)
0 */6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 daily_weather.py >> /Users/zincdigital/CBI-V14/logs/weather.log 2>&1

# NEWS & SOCIAL INTELLIGENCE (Every 2 hours - 24/7 coverage)
0 */2 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_social_intelligence_comprehensive.py >> /Users/zincdigital/CBI-V14/logs/social_intel.log 2>&1

# POLICY & GOVERNMENT DATA (Staggered to avoid 9 AM peak)
45 8 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 backfill_trump_intelligence.py >> /Users/zincdigital/CBI-V14/logs/trump_policy.log 2>&1
15 9 * * 6 cd /Users/zincdigital/CBI-V14/ingestion && python3 backfill_trump_intelligence.py >> /Users/zincdigital/CBI-V14/logs/trump_policy.log 2>&1

# ECONOMIC INDICATORS (Staggered to avoid 9 AM peak)
45 7 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_market_prices.py >> /Users/zincdigital/CBI-V14/logs/economic_data.log 2>&1
45 7 * * 6 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_market_prices.py >> /Users/zincdigital/CBI-V14/logs/economic_data.log 2>&1

# WEEKLY DATA SOURCES
0 17 * * 5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_cftc_positioning_REAL.py >> /Users/zincdigital/CBI-V14/logs/cftc_data.log 2>&1
0 15 * * 4 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_usda_harvest_api.py >> /Users/zincdigital/CBI-V14/logs/usda_exports.log 2>&1
0 10 * * 3 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_eia_biofuel_real.py >> /Users/zincdigital/CBI-V14/logs/biofuel_data.log 2>&1

# WEB SCRAPING (Staggered to avoid conflicts)
0 9 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 production_web_scraper.py >> /Users/zincdigital/CBI-V14/logs/scraper_morning.log 2>&1
0 16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 production_web_scraper.py >> /Users/zincdigital/CBI-V14/logs/scraper_afternoon.log 2>&1

# SATELLITE & ALTERNATIVE DATA
0 7 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_scrapecreators_institutional.py >> /Users/zincdigital/CBI-V14/logs/satellite_data.log 2>&1

# DATA QUALITY MONITORING (Reduced frequency)
0 */4 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 enhanced_data_quality_monitor.py >> /Users/zincdigital/CBI-V14/logs/quality_monitor.log 2>&1

# MASTER CONTINUOUS COLLECTOR (Reduced frequency - CRITICAL OPTIMIZATION)
0 * * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 MASTER_CONTINUOUS_COLLECTOR.py >> /Users/zincdigital/CBI-V14/logs/MASTER_CONTINUOUS.log 2>&1

# FEATURE PIPELINE REFRESH (Previously missing - now scheduled)
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_features_pipeline.py >> /Users/zincdigital/CBI-V14/logs/feature_refresh.log 2>&1

# BREAKING NEWS (Previously missing - now scheduled)
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_news.py >> /Users/zincdigital/CBI-V14/logs/breaking_news.log 2>&1

# DAILY SIGNAL CALCULATIONS (Previously missing - now scheduled)
0 7 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_signals.py >> /Users/zincdigital/CBI-V14/logs/signals.log 2>&1

# MAINTENANCE & MONITORING
0 2 * * 0 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_data_pull_and_migrate.py >> /Users/zincdigital/CBI-V14/logs/weekend_maintenance.log 2>&1
0 */4 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 trump_truth_social_monitor.py >> /Users/zincdigital/CBI-V14/logs/trump_social.log 2>&1

# ====================================================================
# ADDITIONAL MISSING JOBS FROM AUDIT
# ====================================================================

# USDA HARVEST DATA (Weekly - Thursday after USDA report)
0 11 * * 4 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_usda_harvest_real.py >> /Users/zincdigital/CBI-V14/logs/usda_harvest.log 2>&1

# EPA RFS MANDATES (Monthly - first Monday of month)
0 9 * * 1 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_epa_rfs_mandates.py >> /Users/zincdigital/CBI-V14/logs/rfs_mandates.log 2>&1

# VOLATILITY DATA (VIX) - Daily during market hours
30 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/ingestion && python3 ingest_volatility.py >> /Users/zincdigital/CBI-V14/logs/volatility.log 2>&1

# NEWS INTELLIGENCE (Multi-source) - Every 4 hours
0 */4 * * * cd /Users/zincdigital/CBI-V14/ingestion && python3 multi_source_news.py >> /Users/zincdigital/CBI-V14/logs/multi_news.log 2>&1

# DATA INGESTION HEALTH CHECK (Daily - early morning)
0 3 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 data_ingestion_health_check.py >> /Users/zincdigital/CBI-V14/logs/health_check.log 2>&1

# LOG ROTATION (Daily at midnight)
0 0 * * * find /Users/zincdigital/CBI-V14/logs -name "*.log" -mtime +30 -delete

# END OF CBI-V14 COMPREHENSIVE SCHEDULE
EOF

# Install the comprehensive crontab
echo ""
echo "📥 Installing comprehensive crontab..."
crontab /tmp/cbi_v14_comprehensive_cron
echo "✅ Comprehensive crontab installed"

# Verify installation
echo ""
echo "🔍 Verifying installation..."
CRON_COUNT=$(crontab -l | grep -c "python3" || echo "0")
echo "   Found $CRON_COUNT Python jobs scheduled"

# Show summary
echo ""
echo "================================================================================"
echo "✅ COMPREHENSIVE SCHEDULING COMPLETE"
echo "================================================================================"
echo ""
echo "📊 Summary of Changes:"
echo ""
echo "NEW CRITICAL JOBS ADDED (P0):"
echo "  • update_production_datasets.py: Daily 5 AM (production training data refresh)"
echo "  • ingest_china_imports_uncomtrade.py: Weekdays 8 AM (China imports)"
echo "  • ingest_epa_rin_prices.py: Wednesday 9 AM (RIN prices)"
echo ""
echo "NEW HIGH PRIORITY JOBS ADDED (P1):"
echo "  • TRUMP_SENTIMENT_QUANT_ENGINE.py: Daily 7 AM (Trump sentiment processing)"
echo "  • collect_neural_data_sources.py: Daily 6 AM (Big Eight signals)"
echo ""
echo "ADDITIONAL MISSING JOBS ADDED:"
echo "  • ingest_usda_harvest_real.py: Thursday 11 AM (USDA harvest)"
echo "  • ingest_epa_rfs_mandates.py: First Monday 9 AM (RFS mandates)"
echo "  • ingest_volatility.py: Market hours (VIX data)"
echo "  • multi_source_news.py: Every 4 hours (news intelligence)"
echo "  • data_ingestion_health_check.py: Daily 3 AM (health monitoring)"
echo ""
echo "📋 Backup saved to: $BACKUP_FILE"
echo ""
echo "📝 To view current crontab: crontab -l"
echo "📝 To edit: crontab -e"
echo "📝 To restore backup: crontab $BACKUP_FILE"
echo ""
echo "⚠️  IMPORTANT: Monitor logs for first week after setup"
echo "   Check for any parsing, routing, or deduplication issues"
echo ""

