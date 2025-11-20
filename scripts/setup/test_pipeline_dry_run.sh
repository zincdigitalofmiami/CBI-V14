#!/bin/bash
set -e

###############################################################################
# PIPELINE DRY RUN TEST
# 
# Tests the autonomous system without actually running training.
# This validates all scripts can execute and are configured correctly.
#
# Usage:
#   ./scripts/setup/test_pipeline_dry_run.sh
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$REPO_ROOT"

echo ""
echo "================================================================================"
echo "🧪 AUTONOMOUS SYSTEM DRY RUN TEST"
echo "================================================================================"
echo ""
echo "This test validates the autonomous system without running actual training."
echo "Repository: $REPO_ROOT"
echo ""

###############################################################################
# Test 1: Python Environment
###############################################################################

echo -e "${BLUE}[1/6] Testing Python environment...${NC}"
echo ""

python3 --version
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python available${NC}"
echo ""

###############################################################################
# Test 2: Script Imports
###############################################################################

echo -e "${BLUE}[2/6] Testing script imports...${NC}"
echo ""

# Test master pipeline can import
python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT/scripts')
print('Importing run_nightly_pipeline...')
import run_nightly_pipeline
print('✅ Import successful')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Pipeline script import failed${NC}"
    exit 1
fi

# Test watchdog can import
python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT/scripts')
print('Importing watchdog...')
import watchdog
print('✅ Import successful')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Watchdog script import failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All scripts import successfully${NC}"
echo ""

###############################################################################
# Test 3: Required Directories
###############################################################################

echo -e "${BLUE}[3/6] Testing directory structure...${NC}"
echo ""

REQUIRED_DIRS=(
    "Logs/nightly"
    "TrainingData/exports"
    "Models/local"
    "scripts"
    "src/training"
    "src/prediction"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        echo -e "${GREEN}✅${NC} $dir"
    else
        echo -e "${YELLOW}⚠️${NC}  $dir (creating...)"
        mkdir -p "$REPO_ROOT/$dir"
    fi
done

echo ""

###############################################################################
# Test 4: Script Executability
###############################################################################

echo -e "${BLUE}[4/6] Testing script executability...${NC}"
echo ""

SCRIPTS=(
    "scripts/run_nightly_pipeline.py"
    "scripts/watchdog.py"
    "scripts/export_training_data.py"
    "scripts/data_quality_checks.py"
    "scripts/upload_predictions.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$REPO_ROOT/$script" ]; then
        if [ -x "$REPO_ROOT/$script" ]; then
            echo -e "${GREEN}✅${NC} $script (executable)"
        else
            echo -e "${YELLOW}⚠️${NC}  $script (making executable...)"
            chmod +x "$REPO_ROOT/$script"
        fi
    else
        echo -e "${RED}❌${NC} $script (missing)"
    fi
done

echo ""

###############################################################################
# Test 5: LaunchDaemon Files
###############################################################################

echo -e "${BLUE}[5/6] Testing LaunchDaemon configuration...${NC}"
echo ""

# Check if template files exist
if [ -f "$REPO_ROOT/config/system/com.cbi.nightly.plist" ]; then
    echo -e "${GREEN}✅${NC} Nightly daemon template exists"
else
    echo -e "${YELLOW}⚠️${NC}  Nightly daemon template missing"
fi

if [ -f "$REPO_ROOT/config/system/com.cbi.watchdog.plist" ]; then
    echo -e "${GREEN}✅${NC} Watchdog daemon template exists"
else
    echo -e "${YELLOW}⚠️${NC}  Watchdog daemon template missing"
fi

# Check if installed
if [ -f "/Library/LaunchDaemons/com.cbi.nightly.plist" ]; then
    echo -e "${GREEN}✅${NC} Nightly daemon installed"
    
    # Check if loaded
    if sudo launchctl list | grep -q com.cbi.nightly; then
        echo -e "${GREEN}✅${NC} Nightly daemon loaded"
    else
        echo -e "${YELLOW}⚠️${NC}  Nightly daemon not loaded (will start on schedule)"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Nightly daemon not installed (run install script)"
fi

if [ -f "/Library/LaunchDaemons/com.cbi.watchdog.plist" ]; then
    echo -e "${GREEN}✅${NC} Watchdog daemon installed"
    
    if sudo launchctl list | grep -q com.cbi.watchdog; then
        echo -e "${GREEN}✅${NC} Watchdog daemon loaded"
    else
        echo -e "${YELLOW}⚠️${NC}  Watchdog daemon not loaded"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Watchdog daemon not installed (run install script)"
fi

echo ""

###############################################################################
# Test 6: Power Management
###############################################################################

echo -e "${BLUE}[6/6] Testing power management...${NC}"
echo ""

# Check wake schedule
WAKE_SCHEDULE=$(pmset -g sched 2>/dev/null)

if echo "$WAKE_SCHEDULE" | grep -q "wake"; then
    echo -e "${GREEN}✅${NC} Wake schedule configured"
    echo "$WAKE_SCHEDULE"
else
    echo -e "${YELLOW}⚠️${NC}  No wake schedule found"
    echo "   Run: sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00"
fi

echo ""

###############################################################################
# Summary
###############################################################################

echo "================================================================================"
echo -e "${GREEN}🎉 DRY RUN TEST COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run full system validation:"
echo "   python3 scripts/setup/validate_system.py"
echo ""
echo "2. Test the pipeline manually (without training):"
echo "   python3 scripts/watchdog.py"
echo ""
echo "3. If everything looks good, install the autonomous system:"
echo "   ./scripts/setup/install_autonomous_system.sh"
echo ""
echo "4. Or test the full pipeline (this will take 1-2 hours):"
echo "   python3 scripts/run_nightly_pipeline.py"
echo ""
echo "================================================================================"
echo ""







