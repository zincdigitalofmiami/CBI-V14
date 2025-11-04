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

# CRITICAL FINANCIAL DATA (Every 15 minutes during market hours)
*/15 9-16 * * 1-5 cd $SCRIPTS_DIR && python3 hourly_prices.py >> $LOG_DIR/prices.log 2>&1

# WEATHER DATA (Every 6 hours - includes weekends for crop monitoring)
0 */6 * * * cd $SCRIPTS_DIR && python3 daily_weather.py >> $LOG_DIR/weather.log 2>&1

# NEWS & SOCIAL INTELLIGENCE (Every 2 hours - 24/7 coverage)
0 */2 * * * cd $INGESTION_DIR && python3 ingest_social_intelligence_comprehensive.py >> $LOG_DIR/social_intel.log 2>&1

# POLICY & GOVERNMENT DATA (Daily at market open)
0 9 * * 1-5 cd $INGESTION_DIR && python3 backfill_trump_intelligence.py >> $LOG_DIR/trump_policy.log 2>&1

# ECONOMIC INDICATORS (Daily at 8 AM weekdays)
0 8 * * 1-5 cd $INGESTION_DIR && python3 ingest_market_prices.py >> $LOG_DIR/economic_data.log 2>&1

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

# DATA QUALITY MONITORING (Hourly)
0 * * * * cd $INGESTION_DIR && python3 enhanced_data_quality_monitor.py >> $LOG_DIR/quality_monitor.log 2>&1

# WEEKEND MAINTENANCE (Sunday at 2 AM)
0 2 * * 0 cd $SCRIPTS_DIR && python3 daily_data_pull_and_migrate.py >> $LOG_DIR/weekend_maintenance.log 2>&1

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
echo "📅 NEW SCHEDULE SUMMARY:"
echo "• Financial Data: Every 15 min (9 AM - 4 PM, weekdays)"
echo "• Weather: Every 6 hours (24/7, includes weekends)"
echo "• News/Social: Every 2 hours (24/7 coverage)"
echo "• Policy Data: Daily at 9 AM (weekdays)"
echo "• Economic Data: Daily at 8 AM (weekdays)"
echo "• CFTC Data: Weekly Fridays at 5 PM"
echo "• Export Sales: Weekly Thursdays at 3 PM"
echo "• Biofuel Data: Weekly Wednesdays at 10 AM"
echo "• Web Scraping: 9 AM & 4 PM (weekdays)"
echo "• Satellite Data: Daily at 7 AM"
echo "• Quality Monitoring: Hourly"
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

