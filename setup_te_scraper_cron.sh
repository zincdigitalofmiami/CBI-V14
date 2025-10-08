#!/bin/bash
# Setup cron job for TradingEconomics hourly scraping
# This script installs the hourly cron job that runs the scraper

PROJECT_DIR="/Users/zincdigital/CBI-V14"
PYTHON_BIN=$(which python3)
SCRAPER_SCRIPT="$PROJECT_DIR/cbi-v14-ingestion/tradingeconomics_scraper.py"
LOG_FILE="/tmp/tradingeconomics_scraper.log"

echo "Setting up TradingEconomics hourly scraper..."
echo "Project dir: $PROJECT_DIR"
echo "Python: $PYTHON_BIN"
echo "Scraper: $SCRAPER_SCRIPT"

# Make scraper executable
chmod +x "$SCRAPER_SCRIPT"

# Create cron job entry
CRON_JOB="0 * * * * cd $PROJECT_DIR && $PYTHON_BIN $SCRAPER_SCRIPT >> $LOG_FILE 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -v "$SCRAPER_SCRIPT") | crontab -

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job installed:"
echo "$CRON_JOB"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "Log file: $LOG_FILE"
echo "To test manually: cd $PROJECT_DIR && $PYTHON_BIN $SCRAPER_SCRIPT"
echo ""
echo "Setup complete! Scraper will run every hour on the hour."

