#!/bin/bash

# SETUP BI-DAILY NEWS SCRAPING CRON JOB

echo "Setting up bi-daily news scraping schedule..."

# Create logs directory if it doesn't exist
mkdir -p /Users/zincdigital/CBI-V14/logs

# Python script path
SCRIPT_PATH="/Users/zincdigital/CBI-V14/scripts/bidaily_news_scraper.py"
PYTHON_PATH="/usr/bin/python3"

# Create cron job (runs at 6 AM and 6 PM every day)
CRON_CMD="0 6,18 * * * cd /Users/zincdigital/CBI-V14 && $PYTHON_PATH $SCRIPT_PATH >> /Users/zincdigital/CBI-V14/logs/cron.log 2>&1"

# Check if cron job already exists
crontab -l 2>/dev/null | grep -q "bidaily_news_scraper"
if [ $? -eq 0 ]; then
    echo "Cron job already exists. Updating..."
    # Remove old job and add new one
    (crontab -l 2>/dev/null | grep -v "bidaily_news_scraper"; echo "$CRON_CMD") | crontab -
else
    echo "Adding new cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
fi

echo "✓ Bi-daily scraping scheduled for 6 AM and 6 PM"
echo ""
echo "To verify: crontab -l"
echo "To edit: crontab -e"
echo "To remove: crontab -r"
echo ""
echo "Logs will be saved to: /Users/zincdigital/CBI-V14/logs/"
