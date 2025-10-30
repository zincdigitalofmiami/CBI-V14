#!/bin/bash
#
# PHASE 6: CRON CONFIGURATION
# Sets up all automated jobs
#

cat > /tmp/cbi_crontab << 'EOF'
# CBI-V14 Automated Jobs
# Generated: $(date)

# ============================================================================
# MONTHLY JOBS (1st of month)
# ============================================================================

# Vertex AI Predictions (1st @ 2 AM)
0 2 1 * * /Users/zincdigital/CBI-V14/scripts/monthly_vertex_predictions.sh >> /Users/zincdigital/CBI-V14/logs/cron.log 2>&1

# ============================================================================
# DAILY JOBS  
# ============================================================================

# Weather Update (6 AM)
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 daily_weather.py >> /Users/zincdigital/CBI-V14/logs/weather.log 2>&1

# Signal Calculations (7 AM)
0 7 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 daily_signals.py >> /Users/zincdigital/CBI-V14/logs/signals.log 2>&1

# Data Quality Checks (8 AM)
0 8 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 data_quality_check.py >> /Users/zincdigital/CBI-V14/logs/quality.log 2>&1

# ============================================================================
# HOURLY JOBS
# ============================================================================

# Price Updates (Every hour)
0 * * * * cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_prices.py >> /Users/zincdigital/CBI-V14/logs/prices.log 2>&1

# Sentiment Analysis (:30 of every hour)
30 * * * * cd /Users/zincdigital/CBI-V14/scripts && python3 sentiment_update.py >> /Users/zincdigital/CBI-V14/logs/sentiment.log 2>&1

# Dashboard Cache Refresh (:45 of every hour)
45 * * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_dashboard_cache.py >> /Users/zincdigital/CBI-V14/logs/cache.log 2>&1

# ============================================================================
# CLEANUP & MONITORING
# ============================================================================

# Log rotation (Daily @ midnight)
0 0 * * * find /Users/zincdigital/CBI-V14/logs -name "*.log" -mtime +30 -delete

# Emergency endpoint cleanup (Daily @ 3 AM - in case monthly script fails)
0 3 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 cleanup_endpoints.py >> /Users/zincdigital/CBI-V14/logs/cleanup.log 2>&1

EOF

echo "="*80
echo "CRONTAB CONFIGURATION"
echo "="*80
echo ""
echo "Preview of crontab:"
cat /tmp/cbi_crontab
echo ""
echo "To install: crontab /tmp/cbi_crontab"
echo "To view: crontab -l"
echo "="*80

