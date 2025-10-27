#!/bin/bash
# Setup automated pulls for bi-daily news and 4x daily prices

echo "========================================================================"
echo "SETTING UP AUTOMATED DATA PULLS"
echo "========================================================================"

# Make scripts executable
chmod +x scripts/bidaily_news_scraper.py
chmod +x scripts/four_daily_price_fetcher.py

# Create logs directory if it doesn't exist
mkdir -p logs

# Backup existing crontab
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "No existing crontab"

# Get current directory
CURRENT_DIR=$(pwd)

echo ""
echo "Current directory: $CURRENT_DIR"
echo ""

# Add new cron jobs
crontab -l 2>/dev/null | grep -v "bidaily_news_scraper\|four_daily_price_fetcher" > temp_cron || true

# BI-DAILY NEWS SCRAPING (every 12 hours at 8 AM and 8 PM ET)
echo "0 8,20 * * * cd $CURRENT_DIR && /usr/bin/python3 scripts/bidaily_news_scraper.py >> logs/bidaily_scraper.log 2>&1" >> temp_cron

# FOUR-DAILY PRICE FETCHING (8 AM, 12 PM, 4 PM, 8 PM ET)
echo "0 8,12,16,20 * * * cd $CURRENT_DIR && /usr/bin/python3 scripts/four_daily_price_fetcher.py >> logs/daily_price_fetcher.log 2>&1" >> temp_cron

# Install new crontab
crontab temp_cron
rm temp_cron

echo ""
echo "✓ CRON JOBS INSTALLED"
echo ""
echo "Schedule Summary:"
echo "  - Bi-daily news scraping: 8:00 AM & 8:00 PM ET"
echo "  - Four-daily price fetching: 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM ET"
echo ""
echo "To view scheduled jobs:"
echo "  crontab -l"
echo ""
echo "To remove scheduled jobs:"
echo "  crontab -r"
echo ""
echo "To test manually:"
echo "  python3 scripts/bidaily_news_scraper.py"
echo "  python3 scripts/four_daily_price_fetcher.py"
echo ""
echo "========================================================================"
echo "SETUP COMPLETE"
echo "========================================================================"

