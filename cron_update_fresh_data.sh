#!/bin/bash
# CRON UPDATE - Fresh Data Pulls - TWICE DAILY
# Update existing crontab with comprehensive fresh data collection

echo "=================================="
echo "📅 UPDATING CRON SCHEDULE"
echo "=================================="
echo ""

# Backup existing crontab
crontab -l > cron_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "No existing crontab"

# Create new crontab entries
cat > mycron_new << 'EOF'
# CBI-V14 COMPREHENSIVE DATA COLLECTION SCHEDULE
# All times in local system time (CDT/CST)

# ========================================
# FRESH DATA PULLS - TWICE DAILY (Morning & Evening)
# ========================================

# Morning Fresh Data Pull (8 AM)
0 8 * * * cd /Users/zincdigital/CBI-V14 && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 scripts/fresh_data_emergency_pull.py >> logs/fresh_pull.log 2>&1

# Evening Fresh Data Pull (6 PM)
0 18 * * * cd /Users/zincdigital/CBI-V14 && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 scripts/fresh_data_emergency_pull.py >> logs/fresh_pull.log 2>&1

# ========================================
# EXISTING SCHEDULED PULLS (Prices, Weather, etc.)
# ========================================

# Prices - 4x daily during market hours
0 9,11,13,15 * * 1-5 cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 multi_source_collector.py >> /Users/zincdigital/CBI-V14/logs/multi_source.log 2>&1

# Social Intelligence - Twice daily
0 10,16 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 social_intelligence.py >> /Users/zincdigital/CBI-V14/logs/social.log 2>&1

# GDELT China Intelligence - Every 6 hours
0 */6 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 gdelt_china_intelligence.py >> /Users/zincdigital/CBI-V14/logs/gdelt_china.log 2>&1

# Trump Social Monitor - Every 4 hours
0 */4 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 trump_truth_social_monitor.py >> /Users/zincdigital/CBI-V14/logs/trump_social.log 2>&1

# Weather NOAA - Daily at 6 AM
0 6 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 ingest_weather_noaa.py >> /Users/zincdigital/CBI-V14/logs/weather_noaa.log 2>&1

# Weather Brazil - Daily at 7 AM
0 7 * * * cd /Users/zincdigital/CBI-V14/cbi-v14-ingestion && /Users/zincdigital/CBI-V14/cbi_venv/bin/python3 ingest_brazil_weather_inmet.py >> /Users/zincdigital/CBI-V14/logs/weather_brazil.log 2>&1

EOF

# Install new crontab
crontab mycron_new

echo "✅ CRON SCHEDULE UPDATED"
echo ""
echo "New Schedule:"
echo "  - Fresh Data Pulls: 8 AM & 6 PM (twice daily)"
echo "  - Prices: 4x daily during market hours"
echo "  - Social Intelligence: 2x daily"
echo "  - GDELT China: Every 6 hours"
echo "  - Trump Social: Every 4 hours"
echo "  - Weather: Daily"
echo ""
echo "Installed crontab entries."
echo ""

# Show current crontab
echo "Current crontab:"
crontab -l

echo ""
echo "=================================="
echo "✅ Done!"
echo "=================================="





