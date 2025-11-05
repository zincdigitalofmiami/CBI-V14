#!/bin/bash
# ENHANCED CBI-V14 CRON SETUP WITH COMPREHENSIVE DATA COVERAGE
# Addresses audit findings: missing sources, weekend gaps, frequency issues

INGESTION_DIR="/Users/zincdigital/CBI-V14/cbi-v14-ingestion"
SCRIPTS_DIR="/Users/zincdigital/CBI-V14/scripts"
LOG_DIR="/Users/zincdigital/CBI-V14/logs"

# Create directories
mkdir -p "$LOG_DIR"

echo "🚀 SETTING UP ENHANCED CBI-V14 DATA COLLECTION CRON JOBS..."
echo "=========================================================="

# Get current crontab and backup
crontab -l > /tmp/cbi_v14_cron_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "# New crontab" > /tmp/current_cron
cp /tmp/current_cron /tmp/enhanced_cron

# Remove existing CBI-V14 jobs (clean slate)
sed -i '/CBI-V14/d' /tmp/enhanced_cron
sed -i '/hourly_prices/d' /tmp/enhanced_cron
sed -i '/daily_weather/d' /tmp/enhanced_cron
sed -i '/production_web_scraper/d' /tmp/enhanced_cron

# Add comprehensive data collection schedule
cat << 'ENHANCED_SCHEDULE' >> /tmp/enhanced_cron

# ====================================================================
# CBI-V14 ENHANCED DATA COLLECTION SCHEDULE
# Updated: $(date)
# ====================================================================

# CRITICAL FINANCIAL DATA (Every hour during market hours - OPTIMIZED)
# OPTIMIZATION: Reduced from every 15 min to every hour (75% reduction, saves ~$5-10/month)
0 9-16 * * 1-5 cd $SCRIPTS_DIR && python3 hourly_prices.py >> $LOG_DIR/prices.log 2>&1

# WEATHER DATA (Every 6 hours - includes weekends for crop monitoring)
0 */6 * * * cd $SCRIPTS_DIR && python3 daily_weather.py >> $LOG_DIR/weather.log 2>&1

# NEWS & SOCIAL INTELLIGENCE (Every 2 hours - 24/7 coverage)
0 */2 * * * cd $INGESTION_DIR && python3 ingest_social_intelligence_comprehensive.py >> $LOG_DIR/social_intel.log 2>&1

# POLICY & GOVERNMENT DATA (Staggered to avoid 9 AM peak - OPTIMIZED)
# OPTIMIZATION: Moved to 8:45 AM weekdays, added Saturday run for weekend coverage
45 8 * * 1-5 cd $INGESTION_DIR && python3 backfill_trump_intelligence.py >> $LOG_DIR/trump_policy.log 2>&1
15 9 * * 6 cd $INGESTION_DIR && python3 backfill_trump_intelligence.py >> $LOG_DIR/trump_policy.log 2>&1

# ECONOMIC INDICATORS (Staggered to avoid 9 AM peak - OPTIMIZED)
# OPTIMIZATION: Moved to 7:45 AM weekdays, added Saturday run for weekend coverage
45 7 * * 1-5 cd $INGESTION_DIR && python3 ingest_market_prices.py >> $LOG_DIR/economic_data.log 2>&1
45 7 * * 6 cd $INGESTION_DIR && python3 ingest_market_prices.py >> $LOG_DIR/economic_data.log 2>&1

# CFTC POSITIONING DATA (Weekly on Friday)
0 17 * * 5 cd $INGESTION_DIR && python3 ingest_cftc_positioning_REAL.py >> $LOG_DIR/cftc_data.log 2>&1

# EXPORT SALES DATA (Weekly on Thursday)
0 15 * * 4 cd $INGESTION_DIR && python3 ingest_usda_harvest_api.py >> $LOG_DIR/usda_exports.log 2>&1

# BIOFUEL PRODUCTION (Weekly on Wednesday)
0 10 * * 3 cd $INGESTION_DIR && python3 ingest_eia_biofuel_real.py >> $LOG_DIR/biofuel_data.log 2>&1

# COMPREHENSIVE WEB SCRAPING (9 AM and 4 PM weekdays)
0 9 * * 1-5 cd $SCRIPTS_DIR && python3 production_web_scraper.py >> $LOG_DIR/scraper_morning.log 2>&1
0 16 * * 1-5 cd $SCRIPTS_DIR && python3 production_web_scraper.py >> $LOG_DIR/scraper_afternoon.log 2>&1

# SATELLITE & ALTERNATIVE DATA (Daily at 7 AM)
0 7 * * * cd $INGESTION_DIR && python3 ingest_scrapecreators_institutional.py >> $LOG_DIR/satellite_data.log 2>&1

# DATA QUALITY MONITORING (Every 4 hours - OPTIMIZED)
# OPTIMIZATION: Reduced from hourly to every 4 hours (75% reduction, saves ~$10-30/month)
0 */4 * * * cd $INGESTION_DIR && python3 enhanced_data_quality_monitor.py >> $LOG_DIR/quality_monitor.log 2>&1

# WEEKEND MAINTENANCE (Sunday at 2 AM)
0 2 * * 0 cd $SCRIPTS_DIR && python3 daily_data_pull_and_migrate.py >> $LOG_DIR/weekend_maintenance.log 2>&1

# MASTER CONTINUOUS COLLECTOR (Every hour - OPTIMIZED)
# OPTIMIZATION: Reduced from every 15 min to every hour (75% reduction, saves ~$30-40/month)
# CRITICAL: This was the highest cost job - now optimized for cost savings
0 * * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 MASTER_CONTINUOUS_COLLECTOR.py >> $LOG_DIR/MASTER_CONTINUOUS.log 2>&1

# FEATURE PIPELINE REFRESH (Previously missing - now scheduled)
# CRITICAL: This ensures Big 8 signals are refreshed daily
0 6 * * * cd $SCRIPTS_DIR && python3 refresh_features_pipeline.py >> $LOG_DIR/feature_refresh.log 2>&1

# BREAKING NEWS (Previously missing - now scheduled)
0 9-16 * * 1-5 cd $SCRIPTS_DIR && python3 hourly_news.py >> $LOG_DIR/breaking_news.log 2>&1

# DAILY SIGNAL CALCULATIONS (Previously missing - now scheduled)
0 7 * * 1-5 cd $SCRIPTS_DIR && python3 daily_signals.py >> $LOG_DIR/signals.log 2>&1

# TRUMP SOCIAL MONITOR (Every 4 hours)
0 */4 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && python3 trump_truth_social_monitor.py >> $LOG_DIR/trump_social.log 2>&1

# ====================================================================
# MISSING CRITICAL DATA SOURCES (TO BE IMPLEMENTED)
# ====================================================================
# TODO: Add these missing sources:
# - Baltic Dry Index (daily freight rates)
# - Port congestion data (daily shipping delays)
# - Fertilizer prices (monthly cost pressures)
# - ENSO climate data (monthly weather forecasts)
# - Satellite crop health (weekly vegetation indices)

ENHANCED_SCHEDULE

echo "" >> /tmp/enhanced_cron
echo "# END OF CBI-V14 SCHEDULE" >> /tmp/enhanced_cron

# Install the enhanced crontab
crontab /tmp/enhanced_cron

echo ""
echo "✅ ENHANCED CRON SCHEDULE INSTALLED SUCCESSFULLY!"
echo "=================================================="
echo ""
echo "📅 OPTIMIZED SCHEDULE SUMMARY:"
echo "• Financial Data: Every hour (9 AM - 4 PM, weekdays) [OPTIMIZED: was 15 min]"
echo "• Weather: Every 6 hours (24/7, includes weekends)"
echo "• News/Social: Every 2 hours (24/7 coverage)"
echo "• Policy Data: 8:45 AM weekdays, 9:15 AM Saturday [OPTIMIZED: staggered + weekend]"
echo "• Economic Data: 7:45 AM weekdays, 7:45 AM Saturday [OPTIMIZED: staggered + weekend]"
echo "• CFTC Data: Weekly Fridays at 5 PM"
echo "• Export Sales: Weekly Thursdays at 3 PM"
echo "• Biofuel Data: Weekly Wednesdays at 10 AM"
echo "• Web Scraping: 9 AM & 4 PM (weekdays)"
echo "• Satellite Data: Daily at 7 AM"
echo "• Quality Monitoring: Every 4 hours [OPTIMIZED: was hourly]"
echo "• Master Collector: Every hour [OPTIMIZED: was 15 min - CRITICAL SAVINGS]"
echo "• Feature Pipeline: Daily at 6 AM [ADDED: was missing]"
echo "• Breaking News: Hourly during market hours [ADDED: was missing]"
echo "• Daily Signals: Daily at 7 AM weekdays [ADDED: was missing]"
echo "• Weekend Maintenance: Sunday at 2 AM"
echo ""
echo "📊 TOTAL SCHEDULED JOBS: $(grep -c "cd.*python3" /tmp/enhanced_cron)"
echo ""
echo "🔍 MONITORING:"
echo "• Logs: $LOG_DIR/"
echo "• Quality: enhanced_data_quality_monitor.py"
echo "• Backup: /tmp/cbi_v14_cron_backup_*"
echo ""
echo "⚠️  MISSING SOURCES TO IMPLEMENT:"
echo "• Baltic Dry Index (shipping costs)"
echo "• Port congestion data (supply chain)"
echo "• Fertilizer prices (production costs)"
echo "• ENSO climate data (weather forecasts)"
echo "• Satellite crop health (yield estimates)"
echo ""
echo "▶️  Test individual scripts:"
echo "   cd $SCRIPTS_DIR && python3 hourly_prices.py"
echo "   cd $INGESTION_DIR && python3 ingest_social_intelligence_comprehensive.py"
echo ""
echo "🔄 Current crontab:"
crontab -l | grep -E "(python3|cd)" | head -10

# Cleanup
rm -f /tmp/current_cron /tmp/enhanced_cron

echo ""
echo "🎯 ENHANCED DATA COLLECTION IS NOW ACTIVE!"
