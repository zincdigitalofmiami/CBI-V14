#!/bin/bash
# Setup automatic document organization cron job
# Runs weekly to keep documentation organized

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Setup Auto-Organize Documentation Cron Job                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Cron job entry
CRON_JOB="0 3 * * 1 cd $PROJECT_ROOT && /usr/bin/python3 scripts/auto_organize_docs.py --execute >> logs/auto_organize.log 2>&1"

echo "📋 Proposed Cron Job:"
echo "   Schedule: Every Monday at 3:00 AM"
echo "   Command:  python3 scripts/auto_organize_docs.py --execute"
echo "   Log:      logs/auto_organize.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_organize_docs.py"; then
    echo "⚠️  Auto-organize cron job already exists!"
    echo ""
    echo "Current crontab entries for auto-organize:"
    crontab -l | grep "auto_organize_docs.py"
    echo ""
    read -p "Replace existing entry? (yes/no): " REPLACE
    if [ "$REPLACE" != "yes" ]; then
        echo "❌ Aborted - no changes made"
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "auto_organize_docs.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Auto-organize cron job installed!"
echo ""
echo "📋 Verification:"
crontab -l | grep "auto_organize_docs.py"
echo ""
echo "💡 Manual Commands:"
echo "   • Test now:     python scripts/auto_organize_docs.py"
echo "   • Execute now:  python scripts/auto_organize_docs.py --execute"
echo "   • View logs:    tail -f logs/auto_organize.log"
echo "   • Remove cron:  crontab -e (then delete the line)"
echo ""







