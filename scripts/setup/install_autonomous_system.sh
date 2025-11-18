#!/bin/bash
set -e

###############################################################################
# AUTONOMOUS TRAINING SYSTEM INSTALLER
# 
# This script configures your Mac M4 to run the CBI-V14 training pipeline
# completely autonomously, every night at midnight.
#
# What it does:
# 1. Configures power management (prevent sleep, wake before training)
# 2. Installs LaunchDaemons (nightly pipeline + watchdog)
# 3. Validates system requirements
# 4. Creates necessary directories
# 5. Tests the setup
#
# Usage:
#   ./scripts/setup/install_autonomous_system.sh
#
# Requirements:
# - macOS (tested on M4 Mac)
# - Python 3.9+
# - sudo access (for LaunchDaemon installation)
# - Google Cloud credentials configured
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository root
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
cd "$REPO_ROOT"

echo ""
echo "================================================================================"
echo "🤖 AUTONOMOUS TRAINING SYSTEM INSTALLER"
echo "================================================================================"
echo ""
echo "This will configure your Mac M4 to run CBI-V14 training every night at midnight"
echo "Repository: $REPO_ROOT"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ Error: This script is for macOS only${NC}"
    exit 1
fi

###############################################################################
# STEP 1: VALIDATE PREREQUISITES
###############################################################################

echo ""
echo -e "${BLUE}[1/7] Validating prerequisites...${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"

# Check for required Python packages
echo "Checking Python packages..."
python3 -c "import pandas, numpy, google.cloud.bigquery" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Required Python packages installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some Python packages missing - you may need to install them${NC}"
fi

# Check Google Cloud credentials
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_APPLICATION_CREDENTIALS not set${NC}"
    echo "   You may need to configure this for BigQuery access"
else
    echo -e "${GREEN}✅ Google Cloud credentials configured${NC}"
fi

###############################################################################
# STEP 2: CONFIGURE POWER MANAGEMENT
###############################################################################

echo ""
echo -e "${BLUE}[2/7] Configuring power management...${NC}"
echo ""

# Note: These require user confirmation or sudo
echo "The following power settings will optimize your Mac for nightly training:"
echo ""
echo "1. Wake schedule: Mac will wake at 23:59 every night"
echo "2. During training: caffeinate prevents sleep"
echo ""

read -p "Configure power settings now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting wake schedule..."
    
    # Schedule wake every night at 23:59
    sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Wake schedule configured${NC}"
        
        # Show current schedule
        echo ""
        echo "Current power schedule:"
        pmset -g sched
    else
        echo -e "${YELLOW}⚠️  Could not configure wake schedule (may require sudo)${NC}"
    fi
    
    echo ""
    echo "Current power settings:"
    pmset -g
else
    echo -e "${YELLOW}⚠️  Skipped power management configuration${NC}"
    echo "   You can run this manually: sudo pmset schedule wakeorpoweron MTWRFSU 23:59:00"
fi

###############################################################################
# STEP 3: CREATE DIRECTORIES
###############################################################################

echo ""
echo -e "${BLUE}[3/7] Creating directories...${NC}"
echo ""

# Create log directories
mkdir -p "$REPO_ROOT/Logs/nightly"
mkdir -p "$REPO_ROOT/TrainingData/exports"
mkdir -p "$REPO_ROOT/Models/local"

echo -e "${GREEN}✅ Directories created${NC}"

###############################################################################
# STEP 4: INSTALL LAUNCHDAEMONS
###############################################################################

echo ""
echo -e "${BLUE}[4/7] Installing LaunchDaemons...${NC}"
echo ""

# Update plist files with current username and paths
USERNAME=$(whoami)
PYTHON_PATH=$(which python3)

echo "Current user: $USERNAME"
echo "Python path: $PYTHON_PATH"
echo "Repository: $REPO_ROOT"
echo ""

# Create temporary plist files with correct paths
TEMP_NIGHTLY_PLIST="/tmp/com.cbi.nightly.plist"
TEMP_WATCHDOG_PLIST="/tmp/com.cbi.watchdog.plist"

# Generate nightly plist
cat > "$TEMP_NIGHTLY_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
 <dict>
   <key>Label</key>
   <string>com.cbi.nightly</string>
   <key>ProgramArguments</key>
   <array>
     <string>/usr/bin/caffeinate</string>
     <string>-dims</string>
     <string>$PYTHON_PATH</string>
     <string>$REPO_ROOT/scripts/run_nightly_pipeline.py</string>
   </array>
   <key>StartCalendarInterval</key>
   <dict>
     <key>Hour</key>
     <integer>0</integer>
     <key>Minute</key>
     <integer>0</integer>
   </dict>
   <key>StandardOutPath</key>
   <string>$REPO_ROOT/Logs/nightly/daemon_stdout.log</string>
   <key>StandardErrorPath</key>
   <string>$REPO_ROOT/Logs/nightly/daemon_stderr.log</string>
   <key>RunAtLoad</key>
   <false/>
   <key>KeepAlive</key>
   <false/>
   <key>WorkingDirectory</key>
   <string>$REPO_ROOT</string>
   <key>EnvironmentVariables</key>
   <dict>
     <key>PROJECT</key>
     <string>cbi-v14</string>
     <key>PATH</key>
     <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
   </dict>
 </dict>
</plist>
EOF

# Generate watchdog plist
cat > "$TEMP_WATCHDOG_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
   <key>Label</key>
   <string>com.cbi.watchdog</string>
   <key>ProgramArguments</key>
   <array>
       <string>$PYTHON_PATH</string>
       <string>$REPO_ROOT/scripts/watchdog.py</string>
   </array>
   <key>StartInterval</key>
   <integer>3600</integer>
   <key>StandardOutPath</key>
   <string>$REPO_ROOT/Logs/nightly/watchdog_stdout.log</string>
   <key>StandardErrorPath</key>
   <string>$REPO_ROOT/Logs/nightly/watchdog_stderr.log</string>
   <key>RunAtLoad</key>
   <true/>
   <key>KeepAlive</key>
   <false/>
   <key>WorkingDirectory</key>
   <string>$REPO_ROOT</string>
   <key>EnvironmentVariables</key>
   <dict>
     <key>PROJECT</key>
     <string>cbi-v14</string>
     <key>PATH</key>
     <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
   </dict>
</dict>
</plist>
EOF

echo "LaunchDaemon files created in /tmp"
echo ""

read -p "Install LaunchDaemons? (requires sudo) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Unload existing if present
    sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist 2>/dev/null || true
    sudo launchctl unload /Library/LaunchDaemons/com.cbi.watchdog.plist 2>/dev/null || true
    
    # Copy to system directory
    sudo cp "$TEMP_NIGHTLY_PLIST" /Library/LaunchDaemons/
    sudo cp "$TEMP_WATCHDOG_PLIST" /Library/LaunchDaemons/
    
    # Set permissions
    sudo chown root:wheel /Library/LaunchDaemons/com.cbi.nightly.plist
    sudo chown root:wheel /Library/LaunchDaemons/com.cbi.watchdog.plist
    sudo chmod 644 /Library/LaunchDaemons/com.cbi.nightly.plist
    sudo chmod 644 /Library/LaunchDaemons/com.cbi.watchdog.plist
    
    # Load daemons
    sudo launchctl load /Library/LaunchDaemons/com.cbi.nightly.plist
    sudo launchctl load /Library/LaunchDaemons/com.cbi.watchdog.plist
    
    echo -e "${GREEN}✅ LaunchDaemons installed and loaded${NC}"
    
    # Verify
    echo ""
    echo "Verifying installation:"
    sudo launchctl list | grep com.cbi || echo "Not running (will start at scheduled time)"
else
    echo -e "${YELLOW}⚠️  Skipped LaunchDaemon installation${NC}"
    echo "   LaunchDaemon files available in /tmp/"
fi

# Clean up temp files
rm -f "$TEMP_NIGHTLY_PLIST" "$TEMP_WATCHDOG_PLIST"

###############################################################################
# STEP 5: MAKE SCRIPTS EXECUTABLE
###############################################################################

echo ""
echo -e "${BLUE}[5/7] Making scripts executable...${NC}"
echo ""

chmod +x "$REPO_ROOT/scripts/run_nightly_pipeline.py"
chmod +x "$REPO_ROOT/scripts/watchdog.py"
chmod +x "$REPO_ROOT/scripts/export_training_data.py"
chmod +x "$REPO_ROOT/scripts/data_quality_checks.py"
chmod +x "$REPO_ROOT/scripts/upload_predictions.py"
chmod +x "$REPO_ROOT/src/training/baselines/tree_models.py"
chmod +x "$REPO_ROOT/src/prediction/generate_local_predictions.py"

echo -e "${GREEN}✅ Scripts are executable${NC}"

###############################################################################
# STEP 6: VALIDATE INSTALLATION
###############################################################################

echo ""
echo -e "${BLUE}[6/7] Validating installation...${NC}"
echo ""

# Test Python scripts can import
echo "Testing pipeline script..."
python3 "$REPO_ROOT/scripts/run_nightly_pipeline.py" --help 2>/dev/null || \
    python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT/scripts'); import run_nightly_pipeline; print('Import successful')"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Pipeline script validated${NC}"
else
    echo -e "${YELLOW}⚠️  Could not validate pipeline script${NC}"
fi

echo "Testing watchdog script..."
python3 -c "import sys; sys.path.insert(0, '$REPO_ROOT/scripts'); import watchdog; print('Import successful')"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Watchdog script validated${NC}"
else
    echo -e "${YELLOW}⚠️  Could not validate watchdog script${NC}"
fi

###############################################################################
# STEP 7: SUMMARY AND NEXT STEPS
###############################################################################

echo ""
echo "================================================================================"
echo -e "${GREEN}🎉 INSTALLATION COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Your Mac M4 is now configured for autonomous training!"
echo ""
echo "📅 Schedule:"
echo "   - Mac wakes: Every day at 23:59"
echo "   - Training starts: Every day at 00:00 (midnight)"
echo "   - Watchdog checks: Every hour"
echo ""
echo "📁 Important locations:"
echo "   - Pipeline logs: $REPO_ROOT/Logs/nightly/"
echo "   - Daemon logs: $REPO_ROOT/Logs/nightly/daemon_*.log"
echo "   - Status file: $REPO_ROOT/Logs/nightly/last_run_status.json"
echo ""
echo "🔍 Monitoring commands:"
echo "   - Check daemon status: sudo launchctl list | grep com.cbi"
echo "   - View pipeline logs: tail -f $REPO_ROOT/Logs/nightly/nightly_pipeline_*.log"
echo "   - View watchdog logs: tail -f $REPO_ROOT/Logs/nightly/watchdog.log"
echo "   - Manual test run: python3 $REPO_ROOT/scripts/run_nightly_pipeline.py"
echo ""
echo "🛠️  Management commands:"
echo "   - Unload nightly: sudo launchctl unload /Library/LaunchDaemons/com.cbi.nightly.plist"
echo "   - Unload watchdog: sudo launchctl unload /Library/LaunchDaemons/com.cbi.watchdog.plist"
echo "   - Reload: sudo launchctl load /Library/LaunchDaemons/com.cbi.*.plist"
echo ""
echo "✨ Next steps:"
echo "   1. Test the pipeline manually: python3 scripts/run_nightly_pipeline.py"
echo "   2. Monitor logs for the first few runs"
echo "   3. Check that predictions appear in BigQuery"
echo ""
echo "================================================================================"
echo ""



