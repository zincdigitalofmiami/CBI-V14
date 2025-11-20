#!/bin/bash

###############################################################################
# QUICK SYSTEM HEALTH CHECK
# 
# Provides instant status of the autonomous training system.
# Run anytime to check if everything is working.
#
# Usage:
#   ./scripts/check_system_health.sh
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$REPO_ROOT"

echo ""
echo "================================================================================"
echo -e "${BLUE}🏥 CBI-V14 AUTONOMOUS SYSTEM HEALTH CHECK${NC}"
echo "================================================================================"
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

###############################################################################
# Check 1: LaunchDaemons
###############################################################################

echo -e "${BLUE}[1/5] LaunchDaemons${NC}"
echo ""

if sudo launchctl list | grep -q com.cbi.nightly; then
    echo -e "${GREEN}✅${NC} Nightly daemon: Running"
else
    if [ -f /Library/LaunchDaemons/com.cbi.nightly.plist ]; then
        echo -e "${YELLOW}⚠️${NC}  Nightly daemon: Installed but not running (will start on schedule)"
    else
        echo -e "${RED}❌${NC} Nightly daemon: Not installed"
    fi
fi

if sudo launchctl list | grep -q com.cbi.watchdog; then
    echo -e "${GREEN}✅${NC} Watchdog daemon: Running"
else
    if [ -f /Library/LaunchDaemons/com.cbi.watchdog.plist ]; then
        echo -e "${YELLOW}⚠️${NC}  Watchdog daemon: Installed but not running"
    else
        echo -e "${RED}❌${NC} Watchdog daemon: Not installed"
    fi
fi

echo ""

###############################################################################
# Check 2: Wake Schedule
###############################################################################

echo -e "${BLUE}[2/5] Power Management${NC}"
echo ""

WAKE_SCHEDULE=$(pmset -g sched 2>/dev/null)

if echo "$WAKE_SCHEDULE" | grep -q "wake"; then
    echo -e "${GREEN}✅${NC} Wake schedule configured"
    echo "$WAKE_SCHEDULE" | grep -i wake | sed 's/^/   /'
else
    echo -e "${RED}❌${NC} No wake schedule found"
    echo "   Set with: sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00"
fi

echo ""

###############################################################################
# Check 3: Last Pipeline Run
###############################################################################

echo -e "${BLUE}[3/5] Last Pipeline Run${NC}"
echo ""

STATUS_FILE="$REPO_ROOT/Logs/nightly/last_run_status.json"

if [ -f "$STATUS_FILE" ]; then
    # Parse JSON using Python
    python3 << EOF
import json
from datetime import datetime

try:
    with open('$STATUS_FILE') as f:
        status = json.load(f)
    
    start_time = datetime.fromisoformat(status.get('start_time', ''))
    age_hours = (datetime.now() - start_time).total_seconds() / 3600
    success = status.get('success', False)
    
    if success:
        print('\033[0;32m✅\033[0m Pipeline completed successfully')
    else:
        print('\033[0;31m❌\033[0m Pipeline failed')
    
    print(f'   Start time: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'   Age: {age_hours:.1f} hours ago')
    
    if 'failed_stage' in status and status['failed_stage']:
        print(f'   Failed at: {status["failed_stage"]}')
    
    # Show stage summary
    stages = status.get('stages', [])
    passed = sum(1 for s in stages if s.get('success'))
    total = len(stages)
    
    if total > 0:
        print(f'   Stages: {passed}/{total} passed')

except Exception as e:
    print(f'\033[1;33m⚠️\033[0m Could not parse status: {e}')
EOF

else
    echo -e "${YELLOW}⚠️${NC}  No status file found (pipeline never run)"
fi

echo ""

###############################################################################
# Check 4: Recent Logs
###############################################################################

echo -e "${BLUE}[4/5] Recent Logs${NC}"
echo ""

LOG_DIR="$REPO_ROOT/Logs/nightly"

if [ -d "$LOG_DIR" ]; then
    # Count logs
    PIPELINE_LOGS=$(find "$LOG_DIR" -name "nightly_pipeline_*.log" | wc -l | tr -d ' ')
    
    echo "   Pipeline logs: $PIPELINE_LOGS total"
    
    # Latest log
    LATEST_LOG=$(ls -t "$LOG_DIR"/nightly_pipeline_*.log 2>/dev/null | head -1)
    
    if [ -n "$LATEST_LOG" ]; then
        LOG_AGE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LATEST_LOG")
        LOG_SIZE=$(du -h "$LATEST_LOG" | cut -f1)
        
        echo "   Latest log: $(basename "$LATEST_LOG")"
        echo "   Modified: $LOG_AGE"
        echo "   Size: $LOG_SIZE"
        
        # Check for errors
        if grep -q "COMPLETED SUCCESSFULLY" "$LATEST_LOG"; then
            echo -e "   ${GREEN}✅${NC} Completed successfully"
        elif grep -q "CRITICAL FAILURE" "$LATEST_LOG"; then
            echo -e "   ${RED}❌${NC} Critical failure detected"
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  No pipeline logs found"
    fi
    
    # Watchdog log
    if [ -f "$LOG_DIR/watchdog.log" ]; then
        WATCHDOG_LINES=$(wc -l < "$LOG_DIR/watchdog.log" | tr -d ' ')
        echo "   Watchdog checks: $WATCHDOG_LINES logged"
    fi
else
    echo -e "${RED}❌${NC} Log directory not found"
fi

echo ""

###############################################################################
# Check 5: Disk Space
###############################################################################

echo -e "${BLUE}[5/5] Disk Space${NC}"
echo ""

DF_OUTPUT=$(df -h "$REPO_ROOT" | tail -1)
AVAIL=$(echo "$DF_OUTPUT" | awk '{print $4}')
PERCENT=$(echo "$DF_OUTPUT" | awk '{print $5}')

echo "   Available: $AVAIL"
echo "   Used: $PERCENT"

# Extract numeric value from percent
PERCENT_NUM=$(echo "$PERCENT" | sed 's/%//')

if [ "$PERCENT_NUM" -gt 90 ]; then
    echo -e "   ${RED}❌${NC} Disk usage critical (>90%)"
elif [ "$PERCENT_NUM" -gt 80 ]; then
    echo -e "   ${YELLOW}⚠️${NC}  Disk usage high (>80%)"
else
    echo -e "   ${GREEN}✅${NC} Disk space OK"
fi

echo ""

###############################################################################
# Summary
###############################################################################

echo "================================================================================"
echo -e "${BLUE}SUMMARY${NC}"
echo "================================================================================"
echo ""

# Determine overall health
HEALTH_SCORE=0
MAX_SCORE=5

# Check 1: Daemons
if sudo launchctl list | grep -q com.cbi.nightly; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

# Check 2: Wake schedule
if pmset -g sched 2>/dev/null | grep -q wake; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

# Check 3: Recent successful run
if [ -f "$STATUS_FILE" ]; then
    if python3 -c "import json; s=json.load(open('$STATUS_FILE')); exit(0 if s.get('success') else 1)" 2>/dev/null; then
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    fi
fi

# Check 4: Logs exist
if [ -d "$LOG_DIR" ] && [ -n "$(ls -A "$LOG_DIR"/*.log 2>/dev/null)" ]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

# Check 5: Disk space OK
if [ "$PERCENT_NUM" -lt 80 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

echo "Health Score: $HEALTH_SCORE/$MAX_SCORE"
echo ""

if [ $HEALTH_SCORE -eq $MAX_SCORE ]; then
    echo -e "${GREEN}🎉 SYSTEM HEALTHY - All checks passed${NC}"
elif [ $HEALTH_SCORE -ge 3 ]; then
    echo -e "${YELLOW}⚠️  SYSTEM MOSTLY HEALTHY - Review warnings above${NC}"
else
    echo -e "${RED}🚨 SYSTEM UNHEALTHY - Action required${NC}"
fi

echo ""
echo "For detailed validation, run:"
echo "  python3 scripts/setup/validate_system.py"
echo ""
echo "To view logs, run:"
echo "  tail -f Logs/nightly/watchdog.log"
echo ""
echo "================================================================================"
echo ""







