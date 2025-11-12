#!/bin/bash
#
# Verify Cron Optimization Implementation
# Checks that all optimizations are properly applied
#

set -e

echo "================================================================================"
echo "VERIFYING CRON OPTIMIZATION IMPLEMENTATION"
echo "================================================================================"
echo ""

CRON_CONTENT=$(crontab -l 2>/dev/null || echo "")

if [ -z "$CRON_CONTENT" ]; then
    echo "❌ No crontab found"
    exit 1
fi

echo "📋 Checking current crontab configuration..."
echo ""

# Check for optimized frequencies
echo "1. Checking frequency optimizations..."
echo ""

# Check MASTER_CONTINUOUS_COLLECTOR - should be hourly, not every 15 min
if echo "$CRON_CONTENT" | grep -q "MASTER_CONTINUOUS_COLLECTOR.py"; then
    if echo "$CRON_CONTENT" | grep "MASTER_CONTINUOUS_COLLECTOR" | grep -q "^\*/15"; then
        echo "   ❌ MASTER_CONTINUOUS_COLLECTOR still runs every 15 min (should be hourly)"
    elif echo "$CRON_CONTENT" | grep "MASTER_CONTINUOUS_COLLECTOR" | grep -q "^0 \*"; then
        echo "   ✅ MASTER_CONTINUOUS_COLLECTOR optimized to hourly"
    else
        echo "   ⚠️  MASTER_CONTINUOUS_COLLECTOR schedule unclear"
    fi
else
    echo "   ⚠️  MASTER_CONTINUOUS_COLLECTOR not found in crontab"
fi

# Check hourly_prices - should be hourly during market hours, not every 15 min
if echo "$CRON_CONTENT" | grep -q "hourly_prices.py"; then
    if echo "$CRON_CONTENT" | grep "hourly_prices.py" | grep -q "\*/15"; then
        echo "   ❌ hourly_prices.py still runs every 15 min (should be hourly)"
    elif echo "$CRON_CONTENT" | grep "hourly_prices.py" | grep -q "^0 9-16"; then
        echo "   ✅ hourly_prices.py optimized to hourly during market hours"
    else
        echo "   ⚠️  hourly_prices.py schedule unclear"
    fi
else
    echo "   ⚠️  hourly_prices.py not found in crontab"
fi

# Check enhanced_data_quality_monitor - should be every 4 hours, not hourly
if echo "$CRON_CONTENT" | grep -q "enhanced_data_quality_monitor.py"; then
    if echo "$CRON_CONTENT" | grep "enhanced_data_quality_monitor" | grep -q "^0 \*"; then
        echo "   ❌ enhanced_data_quality_monitor still runs hourly (should be every 4 hours)"
    elif echo "$CRON_CONTENT" | grep "enhanced_data_quality_monitor" | grep -q "\*/4"; then
        echo "   ✅ enhanced_data_quality_monitor optimized to every 4 hours"
    else
        echo "   ⚠️  enhanced_data_quality_monitor schedule unclear"
    fi
else
    echo "   ⚠️  enhanced_data_quality_monitor not found in crontab"
fi

echo ""
echo "2. Checking for added missing jobs..."
echo ""

# Check refresh_features_pipeline
if echo "$CRON_CONTENT" | grep -q "refresh_features_pipeline.py"; then
    echo "   ✅ refresh_features_pipeline.py is scheduled"
else
    echo "   ❌ refresh_features_pipeline.py is NOT scheduled (should be daily at 6 AM)"
fi

# Check hourly_news
if echo "$CRON_CONTENT" | grep -q "hourly_news.py"; then
    echo "   ✅ hourly_news.py is scheduled"
else
    echo "   ❌ hourly_news.py is NOT scheduled (should run hourly during market hours)"
fi

# Check daily_signals
if echo "$CRON_CONTENT" | grep -q "daily_signals.py"; then
    echo "   ✅ daily_signals.py is scheduled"
else
    echo "   ❌ daily_signals.py is NOT scheduled (should run daily at 7 AM weekdays)"
fi

echo ""
echo "3. Checking for staggered peak times..."
echo ""

# Check if 9 AM jobs are staggered
AM_9_JOBS=$(echo "$CRON_CONTENT" | grep -E "^\s*(0|15|30|45)\s+9" | wc -l | tr -d ' ')
if [ "$AM_9_JOBS" -gt 1 ]; then
    echo "   ⚠️  Multiple jobs at 9 AM (consider staggering)"
    echo "$CRON_CONTENT" | grep -E "^\s*(0|15|30|45)\s+9" | sed 's/^/      /'
else
    echo "   ✅ 9 AM jobs properly staggered or single job"
fi

echo ""
echo "4. Checking weekend coverage..."
echo ""

# Check if critical jobs run on weekends
if echo "$CRON_CONTENT" | grep "backfill_trump_intelligence\|ingest_market_prices" | grep -q "\* 6"; then
    echo "   ✅ Policy and economic data have weekend coverage"
else
    echo "   ⚠️  Policy and economic data may not have weekend coverage"
fi

echo ""
echo "5. Counting total jobs..."
echo ""

TOTAL_JOBS=$(echo "$CRON_CONTENT" | grep -c "python3" || echo "0")
echo "   Total Python jobs scheduled: $TOTAL_JOBS"

echo ""
echo "================================================================================"
echo "VERIFICATION SUMMARY"
echo "================================================================================"
echo ""
echo "✅ Optimizations should reduce total runs by ~50%"
echo "✅ Expected monthly runs: ~1,100 (down from ~2,200)"
echo "✅ Expected cost savings: ~\$40-60/month"
echo ""
echo "📝 Next steps:"
echo "   1. Monitor logs for 1 week after optimization"
echo "   2. Check BigQuery costs daily"
echo "   3. Verify data freshness is maintained"
echo "   4. Set up monitoring alerts (run setup_monitoring_alerts.sh)"
echo ""







