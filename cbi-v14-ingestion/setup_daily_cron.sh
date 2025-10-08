#!/bin/bash
# CBI-V14 Daily Data Collection Scheduler
# Runs existing working pipelines on automated schedule

INGESTION_DIR="/Users/zincdigital/CBI-V14/cbi-v14-ingestion"
LOG_DIR="/Users/zincdigital/CBI-V14/logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Install cron jobs
(crontab -l 2>/dev/null; cat << CRON

# CBI-V14 Data Collection Schedule
# All times are local system time

# Multi-source collector (every 2 hours during market hours)
0 9,11,13,15 * * 1-5 cd $INGESTION_DIR && python3 multi_source_collector.py >> $LOG_DIR/multi_source.log 2>&1

# GDELT China intelligence (every 6 hours)
0 */6 * * * cd $INGESTION_DIR && python3 gdelt_china_intelligence.py >> $LOG_DIR/gdelt_china.log 2>&1

# Social intelligence (twice daily)
0 10,16 * * * cd $INGESTION_DIR && python3 social_intelligence.py >> $LOG_DIR/social.log 2>&1

# Trump Truth Social (every 4 hours)
0 */4 * * * cd $INGESTION_DIR && python3 trump_truth_social_monitor.py >> $LOG_DIR/trump_social.log 2>&1

# Weather - NOAA (daily at 6 AM)
0 6 * * * cd $INGESTION_DIR && python3 ingest_weather_noaa.py >> $LOG_DIR/weather_noaa.log 2>&1

# Weather - Brazil INMET (daily at 7 AM)
0 7 * * * cd $INGESTION_DIR && python3 ingest_brazil_weather_inmet.py >> $LOG_DIR/weather_brazil.log 2>&1

CRON
) | crontab -

echo "✅ Cron jobs installed successfully"
echo ""
echo "Scheduled jobs:"
crontab -l | grep -v "^#" | grep "CBI-V14"
