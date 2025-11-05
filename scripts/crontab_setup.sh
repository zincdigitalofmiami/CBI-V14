#!/bin/bash
#
# PHASE 6: CRON CONFIGURATION (OPTIMIZED)
# Sets up all automated jobs with cost and performance optimizations
# Updated: 2025-11-05
# Optimizations: Reduced frequencies, staggered peak times, added missing jobs
#

cat > /tmp/cbi_crontab << 'EOF'
# CBI-V14 Automated Jobs (Optimized)
# Generated: $(date)
# Optimizations: Reduced frequency for cost savings, staggered peak times

# ============================================================================
# MONTHLY JOBS (1st of month)
# ============================================================================

# Vertex AI Predictions (1st @ 2 AM)
0 2 1 * * /Users/zincdigital/CBI-V14/scripts/monthly_vertex_predictions.sh >> /Users/zincdigital/CBI-V14/logs/cron.log 2>&1

# ============================================================================
# DAILY JOBS  
# ============================================================================

# Weather Update (Every 6 hours - includes weekends for crop monitoring)
# OPTIMIZATION: Changed from daily at 6 AM to every 6 hours for better coverage
0 */6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 daily_weather.py >> /Users/zincdigital/CBI-V14/logs/weather.log 2>&1

# Signal Calculations (7 AM weekdays)
# OPTIMIZATION: Added to schedule (was missing)
0 7 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 daily_signals.py >> /Users/zincdigital/CBI-V14/logs/signals.log 2>&1

# Data Quality Checks (Every 4 hours - reduced from hourly)
# OPTIMIZATION: Reduced from hourly to every 4 hours (75% reduction)
0 */4 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 data_quality_check.py >> /Users/zincdigital/CBI-V14/logs/quality.log 2>&1

# ============================================================================
# HOURLY JOBS (Optimized for market hours)
# ============================================================================

# Price Updates (Every hour during market hours - 9 AM to 4 PM weekdays)
# OPTIMIZATION: Reduced from every 15 min to every hour (75% reduction)
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_prices.py >> /Users/zincdigital/CBI-V14/logs/prices.log 2>&1

# Sentiment Analysis (:30 of every hour)
30 * * * * cd /Users/zincdigital/CBI-V14/scripts && python3 sentiment_update.py >> /Users/zincdigital/CBI-V14/logs/sentiment.log 2>&1

# Dashboard Cache Refresh (:45 of every hour)
45 * * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_dashboard_cache.py >> /Users/zincdigital/CBI-V14/logs/cache.log 2>&1

# === BIG-8 FEATURE REFRESH (Once daily - optimized from twice daily) ===
# OPTIMIZATION: Reduced from 2x/day to 1x/day (50% reduction)
0 6 * * * cd /Users/zincdigital/CBI-V14/scripts && python3 refresh_features_pipeline.py >> /Users/zincdigital/CBI-V14/logs/feature_refresh.log 2>&1

# === HOURLY BREAKING NEWS (During market hours) ===
# OPTIMIZATION: Limited to market hours (9 AM - 4 PM weekdays)
0 9-16 * * 1-5 cd /Users/zincdigital/CBI-V14/scripts && python3 hourly_news.py >> /Users/zincdigital/CBI-V14/logs/breaking_news.log 2>&1

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

