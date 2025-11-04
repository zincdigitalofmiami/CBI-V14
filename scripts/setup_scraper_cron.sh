#!/bin/bash
# Setup cron for bi-daily web scraping (twice per day: 9 AM and 4 PM)
# For CBI-V14 production scraper

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up bi-daily cron for web scraper..."
echo "Project directory: $PROJECT_DIR"

# Create cron job entries
CRON_ENTRY_MORNING="0 9 * * * cd $PROJECT_DIR && /usr/bin/python3 $PROJECT_DIR/scripts/production_web_scraper.py >> $PROJECT_DIR/logs/scraper_morning.log 2>&1"

CRON_ENTRY_AFTERNOON="0 16 * * * cd $PROJECT_DIR && /usr/bin/python3 $PROJECT_DIR/scripts/production_web_scraper.py >> $PROJECT_DIR/logs/scraper_afternoon.log 2>&1"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Check if entries already exist
if crontab -l 2>/dev/null | grep -q "production_web_scraper.py"; then
    echo "⚠️  Cron entries already exist for production_web_scraper.py"
    echo "   Remove existing entries first if you want to update"
else
    # Add new cron entries
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY_MORNING") | crontab -
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY_AFTERNOON") | crontab -
    
    echo "✅ Cron jobs added:"
    echo "   - Morning run: 9:00 AM daily"
    echo "   - Afternoon run: 4:00 PM daily"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "production_web_scraper.py"
fi

echo ""
echo "To view logs:"
echo "   Morning: tail -f $PROJECT_DIR/logs/scraper_morning.log"
echo "   Afternoon: tail -f $PROJECT_DIR/logs/scraper_afternoon.log"
echo ""
echo "To remove cron jobs:"
echo "   crontab -e"
echo "   (then delete lines with production_web_scraper.py)"



