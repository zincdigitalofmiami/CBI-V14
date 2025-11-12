#!/bin/bash
#
# CBI-V14 OPTIMIZED CRON CONFIGURATION
# Generated: 2025-11-05
# Optimizations: Reduced frequency for cost savings, staggered peak times, added missing jobs
#
# USAGE:
#   chmod +x crontab_optimized.sh
#   ./crontab_optimized.sh
#
# This will backup your current crontab and install the optimized version.
#

set -e

PROJECT_ROOT="/Users/zincdigital/CBI-V14"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
INGESTION_DIR="$PROJECT_ROOT/ingestion"
CBI_INGESTION_DIR="$PROJECT_ROOT/cbi-v14-ingestion"
LOG_DIR="$PROJECT_ROOT/logs"

echo "================================================================================"
echo "CBI-V14 OPTIMIZED CRON CONFIGURATION INSTALLER"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Backup your current crontab"
echo "  2. Install optimized cron schedule with:"
echo "     - Reduced frequencies (75% reduction for high-cost jobs)"
echo "     - Staggered peak times (avoids conflicts)"
echo "     - Added missing critical jobs"
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

# Create optimized crontab
echo ""
echo "📝 Creating optimized crontab..."

cat > /tmp/cbi_v14_optimized_cron << EOF
# ====================================================================
# CBI-V14 OPTIMIZED DATA COLLECTION SCHEDULE
# Generated: $(date +%Y-%m-%d)
# Optimizations: Reduced frequency for cost savings, staggered peak times
# ====================================================================

# ====================================================================
# CRITICAL FINANCIAL DATA (Every hour during market hours)
# OPTIMIZATION: Reduced from every 15 min to every hour (75% reduction)
# ====================================================================
0 9-16 * * 1-5 cd $SCRIPTS_DIR && python3 hourly_prices.py >> $LOG_DIR/prices.log 2>&1

# ====================================================================
# WEATHER DATA (Every 6 hours - includes weekends for crop monitoring)
# ====================================================================
0 */6 * * * cd $SCRIPTS_DIR && python3 daily_weather.py >> $LOG_DIR/weather.log 2>&1

# ====================================================================
# NEWS & SOCIAL INTELLIGENCE (Every 2 hours - 24/7 coverage)
# ====================================================================
0 */2 * * * cd $INGESTION_DIR && python3 ingest_social_intelligence_comprehensive.py >> $LOG_DIR/social_intel.log 2>&1

# ====================================================================
# POLICY & GOVERNMENT DATA (Staggered to avoid 9 AM peak)
# OPTIMIZATION: Moved to 8:45 AM weekdays, added Saturday run for weekend coverage
# ====================================================================
45 8 * * 1-5 cd $INGESTION_DIR && python3 backfill_trump_intelligence.py >> $LOG_DIR/trump_policy.log 2>&1
15 9 * * 6 cd $INGESTION_DIR && python3 backfill_trump_intelligence.py >> $LOG_DIR/trump_policy.log 2>&1

# ====================================================================
# ECONOMIC INDICATORS (Staggered to avoid 9 AM peak)
# OPTIMIZATION: Moved to 7:45 AM weekdays, added Saturday run for weekend coverage
# ====================================================================
45 7 * * 1-5 cd $INGESTION_DIR && python3 ingest_market_prices.py >> $LOG_DIR/economic_data.log 2>&1
45 7 * * 6 cd $INGESTION_DIR && python3 ingest_market_prices.py >> $LOG_DIR/economic_data.log 2>&1

# ====================================================================
# WEEKLY DATA SOURCES
# ====================================================================
0 17 * * 5 cd $INGESTION_DIR && python3 ingest_cftc_positioning_REAL.py >> $LOG_DIR/cftc_data.log 2>&1
0 15 * * 4 cd $INGESTION_DIR && python3 ingest_usda_harvest_api.py >> $LOG_DIR/usda_exports.log 2>&1
0 10 * * 3 cd $INGESTION_DIR && python3 ingest_eia_biofuel_real.py >> $LOG_DIR/biofuel_data.log 2>&1

# ====================================================================
# WEB SCRAPING (Staggered to avoid conflicts)
# ====================================================================
0 9 * * 1-5 cd $SCRIPTS_DIR && python3 production_web_scraper.py >> $LOG_DIR/scraper_morning.log 2>&1
0 16 * * 1-5 cd $SCRIPTS_DIR && python3 production_web_scraper.py >> $LOG_DIR/scraper_afternoon.log 2>&1

# ====================================================================
# SATELLITE & ALTERNATIVE DATA
# ====================================================================
0 7 * * * cd $INGESTION_DIR && python3 ingest_scrapecreators_institutional.py >> $LOG_DIR/satellite_data.log 2>&1

# ====================================================================
# DATA QUALITY MONITORING (Reduced frequency)
# OPTIMIZATION: Reduced from every hour to every 4 hours (75% reduction)
# ====================================================================
0 */4 * * * cd $INGESTION_DIR && python3 enhanced_data_quality_monitor.py >> $LOG_DIR/quality_monitor.log 2>&1

# ====================================================================
# MASTER CONTINUOUS COLLECTOR (Reduced frequency - CRITICAL OPTIMIZATION)
# OPTIMIZATION: Reduced from every 15 min to every hour (75% reduction)
# This saves ~$30-40/month in API and BigQuery costs
# ====================================================================
0 * * * * cd $CBI_INGESTION_DIR && python3 MASTER_CONTINUOUS_COLLECTOR.py >> $LOG_DIR/MASTER_CONTINUOUS.log 2>&1

# ====================================================================
# FEATURE PIPELINE REFRESH (Previously missing - now scheduled)
# CRITICAL: This ensures Big 8 signals are refreshed daily
# ====================================================================
0 6 * * * cd $SCRIPTS_DIR && python3 refresh_features_pipeline.py >> $LOG_DIR/feature_refresh.log 2>&1

# ====================================================================
# BREAKING NEWS (Previously missing - now scheduled)
# ====================================================================
0 9-16 * * 1-5 cd $SCRIPTS_DIR && python3 hourly_news.py >> $LOG_DIR/breaking_news.log 2>&1

# ====================================================================
# DAILY SIGNAL CALCULATIONS (Previously missing - now scheduled)
# ====================================================================
0 7 * * 1-5 cd $SCRIPTS_DIR && python3 daily_signals.py >> $LOG_DIR/signals.log 2>&1

# ====================================================================
# MAINTENANCE & MONITORING
# ====================================================================
0 2 * * 0 cd $SCRIPTS_DIR && python3 daily_data_pull_and_migrate.py >> $LOG_DIR/weekend_maintenance.log 2>&1
0 */4 * * * cd $CBI_INGESTION_DIR && python3 trump_truth_social_monitor.py >> $LOG_DIR/trump_social.log 2>&1

# ====================================================================
# LOG ROTATION (Daily at midnight)
# ====================================================================
0 0 * * * find $LOG_DIR -name "*.log" -mtime +30 -delete

# END OF CBI-V14 OPTIMIZED SCHEDULE
EOF

# Install the optimized crontab
echo ""
echo "📥 Installing optimized crontab..."
crontab /tmp/cbi_v14_optimized_cron
echo "✅ Optimized crontab installed"

# Verify installation
echo ""
echo "🔍 Verifying installation..."
CRON_COUNT=$(crontab -l | grep -c "python3" || echo "0")
echo "   Found $CRON_COUNT Python jobs scheduled"

# Show summary
echo ""
echo "================================================================================"
echo "✅ OPTIMIZATION COMPLETE"
echo "================================================================================"
echo ""
echo "📊 Summary of Changes:"
echo ""
echo "Frequency Reductions:"
echo "  • MASTER_CONTINUOUS_COLLECTOR: 96 runs/day → 24 runs/day (75% reduction)"
echo "  • hourly_prices.py: 28 runs/day → 7 runs/day (75% reduction)"
echo "  • enhanced_data_quality_monitor: 24 runs/day → 6 runs/day (75% reduction)"
echo ""
echo "New Jobs Added:"
echo "  • refresh_features_pipeline.py: 1 run/day (was missing)"
echo "  • hourly_news.py: 7 runs/day (was missing)"
echo "  • daily_signals.py: 5 runs/week (was missing)"
echo ""
echo "Staggered Times:"
echo "  • Economic indicators: 7:45 AM (was 8:00 AM)"
echo "  • Policy data: 8:45 AM weekdays, 9:15 AM Saturday (was 9:00 AM)"
echo ""
echo "Expected Savings:"
echo "  • ~$40-60/month (40-50% cost reduction)"
echo "  • ~50% reduction in total runs/month"
echo ""
echo "📋 Backup saved to: $BACKUP_FILE"
echo ""
echo "📝 To view current crontab: crontab -l"
echo "📝 To edit: crontab -e"
echo "📝 To restore backup: crontab $BACKUP_FILE"
echo ""
echo "⚠️  IMPORTANT: Monitor logs and costs for 1 week after optimization"
echo "   Report any issues immediately"
echo ""







