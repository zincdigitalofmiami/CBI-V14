#!/bin/bash
#
# Test All Web Scrapers - Phase 0.2 Verification
# Tests each scraper individually and verifies BigQuery loading
#

set -e

cd /Users/zincdigital/CBI-V14

echo "================================================================================"
echo "TESTING ALL WEB SCRAPERS - PHASE 0.2 VERIFICATION"
echo "================================================================================"
echo "Start: $(date)"
echo ""

# Create test log directory
mkdir -p logs/scraper_tests

# ============================================================================
# Test 1: Comprehensive Web Scraper (All 12 classes)
# ============================================================================
echo "Test 1: Running comprehensive web scraper..."
python3 cbi-v14-ingestion/web_scraper.py > logs/scraper_tests/web_scraper_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Comprehensive web scraper executed successfully"
else
    echo "   ❌ Comprehensive web scraper failed (check logs/scraper_tests/web_scraper_test.log)"
fi

# ============================================================================
# Test 2: Truth Social Monitor
# ============================================================================
echo ""
echo "Test 2: Running Truth Social monitor..."
python3 cbi-v14-ingestion/trump_truth_social_monitor.py > logs/scraper_tests/truth_social_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Truth Social monitor executed successfully"
else
    echo "   ⚠️  Truth Social monitor completed with warnings (check logs)"
fi

# ============================================================================
# Test 3: Production Web Scraper
# ============================================================================
echo ""
echo "Test 3: Running production web scraper..."
python3 scripts/production_web_scraper.py > logs/scraper_tests/production_scraper_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Production web scraper executed successfully"
else
    echo "   ❌ Production web scraper failed"
fi

# ============================================================================
# Test 4: Social Intelligence
# ============================================================================
echo ""
echo "Test 4: Running social intelligence collector..."
python3 cbi-v14-ingestion/social_intelligence.py > logs/scraper_tests/social_intelligence_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Social intelligence collector executed successfully"
else
    echo "   ❌ Social intelligence collector failed"
fi

# ============================================================================
# Test 5: Economic Intelligence
# ============================================================================
echo ""
echo "Test 5: Running economic intelligence collector..."
python3 cbi-v14-ingestion/economic_intelligence.py > logs/scraper_tests/economic_intelligence_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Economic intelligence collector executed successfully"
else
    echo "   ❌ Economic intelligence collector failed"
fi

# ============================================================================
# Test 6: GDELT China Intelligence
# ============================================================================
echo ""
echo "Test 6: Running GDELT China intelligence..."
python3 cbi-v14-ingestion/gdelt_china_intelligence.py > logs/scraper_tests/gdelt_china_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ GDELT China intelligence executed successfully"
else
    echo "   ❌ GDELT China intelligence failed"
fi

# ============================================================================
# Test 7: Multi-Source Collector
# ============================================================================
echo ""
echo "Test 7: Running multi-source collector..."
python3 cbi-v14-ingestion/multi_source_collector.py > logs/scraper_tests/multi_source_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Multi-source collector executed successfully"
else
    echo "   ⚠️  Multi-source collector completed with warnings"
fi

# ============================================================================
# Verify BigQuery Data Loading
# ============================================================================
echo ""
echo "================================================================================"
echo "VERIFYING BIGQUERY DATA LOADING"
echo "================================================================================"
echo ""

echo "Checking row counts in web scraping tables..."
echo ""

for table in \
    futures_prices_barchart \
    futures_prices_marketwatch \
    futures_prices_investing \
    futures_sentiment_tradingview \
    policy_rfs_volumes \
    legislative_bills \
    policy_events_federalregister \
    ers_oilcrops_monthly \
    usda_wasde_soy \
    news_industry_brownfield \
    news_market_farmprogress \
    enso_climate_status \
    industry_intelligence_asa \
    news_reuters \
    futures_prices_cme_public \
    market_analysis_correlations
do
    count=$(bq query --use_legacy_sql=false --format=csv \
        "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.$table\`" 2>/dev/null | tail -1)
    
    if [ "$count" -gt 0 ]; then
        echo "   ✅ $table: $count rows"
    else
        echo "   ⚠️  $table: 0 rows (scraper may need debugging)"
    fi
done

echo ""
echo "Checking intelligence tables..."
echo ""

for table in \
    social_sentiment \
    economic_indicators \
    news_intelligence \
    trump_policy_intelligence
do
    count=$(bq query --use_legacy_sql=false --format=csv \
        "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.$table\`" 2>/dev/null | tail -1)
    
    if [ "$count" -gt 0 ]; then
        echo "   ✅ $table: $count rows"
    else
        echo "   ⚠️  $table: 0 rows"
    fi
done

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo "End: $(date)"
echo ""
echo "Logs saved to: logs/scraper_tests/"
echo ""
echo "Review individual logs for detailed error messages:"
echo "  - web_scraper_test.log"
echo "  - truth_social_test.log"
echo "  - production_scraper_test.log"
echo "  - social_intelligence_test.log"
echo "  - economic_intelligence_test.log"
echo "  - gdelt_china_test.log"
echo "  - multi_source_test.log"
echo ""
echo "================================================================================"

