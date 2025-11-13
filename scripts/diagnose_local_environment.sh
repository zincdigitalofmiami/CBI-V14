#!/bin/bash
#
# CBI-V14 Local Environment Diagnostic Script
# Verifies all critical components for local cron/launchd scheduling
#

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters for summary
PASSED=0
WARNINGS=0
FAILED=0
ISSUES=()

# External drive and repo paths
EXTERNAL_DRIVE="/Volumes/Satechi Hub"
REPO_PATH="${EXTERNAL_DRIVE}/Projects/CBI-V14"
SYMLINK_PATH="${HOME}/Documents/GitHub/CBI-V14"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CBI-V14 LOCAL ENVIRONMENT DIAGNOSTIC"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# 0. System Information (Header)
# ============================================================================
echo "📋 SYSTEM INFORMATION"
echo "────────────────────────────────────────────────"
echo "macOS Version: $(sw_vers -productVersion) ($(sw_vers -buildVersion))"
echo "Current User: $(whoami)"
echo "Current Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "System Uptime: $(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')"
echo ""

# ============================================================================
# 1. External Drive Mount Check
# ============================================================================
echo "🔍 CHECK 1: External Drive Mount"
echo "────────────────────────────────────────────────"
if [[ -d "$EXTERNAL_DRIVE" ]]; then
    if [[ -w "$EXTERNAL_DRIVE" ]]; then
        echo -e "${GREEN}✅ External Drive: Mounted and writable${NC}"
        echo "   Path: $EXTERNAL_DRIVE"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ External Drive: Mounted but NOT writable${NC}"
        echo "   Path: $EXTERNAL_DRIVE"
        ISSUES+=("External drive is not writable - check permissions")
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ External Drive: NOT mounted${NC}"
    echo "   Expected: $EXTERNAL_DRIVE"
    ISSUES+=("External drive not mounted - cron jobs will fail")
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 2. Repository and Symlink Verification
# ============================================================================
echo "🔍 CHECK 2: Repository and Symlink"
echo "────────────────────────────────────────────────"
REPO_OK=true
SYMLINK_OK=true

# Check repository exists
if [[ -d "$REPO_PATH" ]]; then
    echo "   ✅ Repository exists: $REPO_PATH"
else
    echo -e "   ${RED}❌ Repository NOT found: $REPO_PATH${NC}"
    ISSUES+=("Repository directory not found on external drive")
    REPO_OK=false
    FAILED=$((FAILED + 1))
fi

# Check symlink exists
if [[ -L "$SYMLINK_PATH" ]]; then
    SYMLINK_TARGET=$(readlink "$SYMLINK_PATH")
    if [[ "$SYMLINK_TARGET" == "$REPO_PATH" ]]; then
        echo "   ✅ Symlink exists and points correctly: $SYMLINK_PATH -> $REPO_PATH"
    else
        echo -e "   ${RED}❌ Symlink points to wrong location${NC}"
        echo "      Current: $SYMLINK_TARGET"
        echo "      Expected: $REPO_PATH"
        ISSUES+=("Symlink points to incorrect location")
        SYMLINK_OK=false
        FAILED=$((FAILED + 1))
    fi
elif [[ -d "$SYMLINK_PATH" ]]; then
    echo -e "   ${YELLOW}⚠️  Symlink path exists but is NOT a symlink (regular directory)${NC}"
    ISSUES+=("Symlink path is a directory, not a symlink")
    SYMLINK_OK=false
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "   ${RED}❌ Symlink NOT found: $SYMLINK_PATH${NC}"
    ISSUES+=("Symlink not found - repository may not be accessible from home directory")
    SYMLINK_OK=false
    FAILED=$((FAILED + 1))
fi

if [[ "$REPO_OK" == true && "$SYMLINK_OK" == true ]]; then
    echo -e "${GREEN}✅ Repository and Symlink: All checks passed${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Repository and Symlink: Issues detected${NC}"
    if [[ "$REPO_OK" == false ]]; then
        FAILED=$((FAILED + 1))
    fi
fi
echo ""

# ============================================================================
# 3. TensorFlow Metal GPU Detection
# ============================================================================
echo "🔍 CHECK 3: TensorFlow Metal GPU"
echo "────────────────────────────────────────────────"
TF_CHECK=$(python3 -c "
import sys
try:
    import tensorflow as tf
    version = tf.__version__
    major, minor = version.split('.')[:2]
    
    # Check version
    version_ok = (major == '2' and minor == '16')
    
    # Check for Metal GPU
    gpu_available = False
    gpu_info = ''
    try:
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            gpu_available = True
            gpu_info = str(gpus[0])
    except:
        pass
    
    # Check Metal backend
    metal_available = False
    try:
        if hasattr(tf.config, 'experimental') and hasattr(tf.config.experimental, 'get_device_details'):
            devices = tf.config.list_physical_devices()
            for device in devices:
                if 'GPU' in device.name or 'Metal' in str(device):
                    metal_available = True
                    break
    except:
        pass
    
    if version_ok and (gpu_available or metal_available):
        print(f'OK|{version}|{gpu_available}|{metal_available}')
        sys.exit(0)
    elif version_ok:
        print(f'WARN|{version}|{gpu_available}|{metal_available}')
        sys.exit(1)
    else:
        print(f'FAIL|{version}|{gpu_available}|{metal_available}')
        sys.exit(2)
except ImportError as e:
    print(f'FAIL|NOT_INSTALLED|{str(e)}')
    sys.exit(2)
except Exception as e:
    print(f'FAIL|ERROR|{str(e)}')
    sys.exit(2)
" 2>&1)

TF_EXIT=$?
TF_PARTS=($(echo "$TF_CHECK" | tr '|' '\n'))

if [[ $TF_EXIT -eq 0 ]]; then
    echo -e "${GREEN}✅ TensorFlow Metal GPU: Detected and configured${NC}"
    echo "   Version: ${TF_PARTS[1]}"
    echo "   GPU Available: ${TF_PARTS[2]}"
    echo "   Metal Backend: ${TF_PARTS[3]}"
    PASSED=$((PASSED + 1))
elif [[ $TF_EXIT -eq 1 ]]; then
    echo -e "${YELLOW}⚠️  TensorFlow: Installed but GPU/Metal not detected${NC}"
    echo "   Version: ${TF_PARTS[1]}"
    echo "   GPU Available: ${TF_PARTS[2]}"
    echo "   Metal Backend: ${TF_PARTS[3]}"
    ISSUES+=("TensorFlow installed but Metal GPU not detected - training may be slow")
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ TensorFlow: Not installed or error${NC}"
    if [[ "${TF_PARTS[1]}" == "NOT_INSTALLED" ]]; then
        echo "   Error: TensorFlow not installed"
        ISSUES+=("TensorFlow not installed - install with: pip install tensorflow-metal")
    else
        echo "   Error: ${TF_PARTS[2]}"
        ISSUES+=("TensorFlow error: ${TF_PARTS[2]}")
    fi
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 4. Cron Jobs Check
# ============================================================================
echo "🔍 CHECK 4: Cron Jobs"
echo "────────────────────────────────────────────────"
CRON_OUTPUT=$(crontab -l 2>/dev/null || echo "")
if [[ -z "$CRON_OUTPUT" ]]; then
    CBI_CRON_JOBS=0
else
    CBI_CRON_JOBS=$(echo "$CRON_OUTPUT" | grep -iE "CBI-V14|ingest_|cbi" | grep -v "^#" | wc -l | tr -d ' ')
fi

if [[ $CBI_CRON_JOBS -gt 0 ]]; then
    echo -e "${GREEN}✅ Cron Jobs: Found $CBI_CRON_JOBS CBI-V14 job(s)${NC}"
    echo "$CRON_OUTPUT" | grep -iE "CBI-V14|ingest_|cbi" | grep -v "^#" | head -3 | sed 's/^/   /'
    if [[ $CBI_CRON_JOBS -gt 3 ]]; then
        echo "   ... and $((CBI_CRON_JOBS - 3)) more"
    fi
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Cron Jobs: No CBI-V14 jobs found${NC}"
    echo "   Run: bash scripts/crontab_setup.sh"
    ISSUES+=("No cron jobs configured - run crontab_setup.sh to install schedule")
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 5. Launchd Agents Check
# ============================================================================
echo "🔍 CHECK 5: Launchd Agents"
echo "────────────────────────────────────────────────"
LAUNCHD_LOADED=0
if command -v launchctl >/dev/null 2>&1; then
    LAUNCHD_TEMP=$(timeout 2 launchctl list 2>/dev/null | grep -i cbi 2>/dev/null || true)
    if [[ -n "$LAUNCHD_TEMP" ]]; then
        LAUNCHD_LOADED=$(echo "$LAUNCHD_TEMP" | wc -l | awk '{print $1}')
    fi
fi

LAUNCHD_PLISTS=0
if [[ -d ~/Library/LaunchAgents ]]; then
    LAUNCHD_TEMP2=$(timeout 2 find ~/Library/LaunchAgents \( -name "*cbi*" -o -name "*CBI*" \) 2>/dev/null || true)
    if [[ -n "$LAUNCHD_TEMP2" ]]; then
        LAUNCHD_PLISTS=$(echo "$LAUNCHD_TEMP2" | wc -l | awk '{print $1}')
    fi
fi

if [[ ${LAUNCHD_LOADED:-0} -gt 0 ]]; then
    echo -e "${GREEN}✅ Launchd Agents: $LAUNCHD_LOADED agent(s) loaded${NC}"
    timeout 2 launchctl list 2>/dev/null | grep -i cbi | head -3 | sed 's/^/   /' || true
    PASSED=$((PASSED + 1))
elif [[ $LAUNCHD_PLISTS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Launchd Agents: $LAUNCHD_PLISTS plist(s) found but not loaded${NC}"
    timeout 2 find ~/Library/LaunchAgents \( -name "*cbi*" -o -name "*CBI*" \) 2>/dev/null | head -3 | sed 's/^/   /' || true
    ISSUES+=("Launchd plists exist but not loaded - run: launchctl load <plist>")
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${YELLOW}⚠️  Launchd Agents: None configured${NC}"
    echo "   (Optional - cron is sufficient for most jobs)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ============================================================================
# 6. Network Connectivity
# ============================================================================
echo "🔍 CHECK 6: Network Connectivity"
echo "────────────────────────────────────────────────"
if ping -c 2 -W 2000 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Network Connectivity: Working${NC}"
    echo "   Successfully pinged 8.8.8.8"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Network Connectivity: Failed${NC}"
    echo "   Cannot reach 8.8.8.8 - check internet connection"
    ISSUES+=("Network connectivity failed - ingestion jobs will fail")
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 7. Google Credentials Check
# ============================================================================
echo "🔍 CHECK 7: Google Credentials"
echo "────────────────────────────────────────────────"
if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
    CRED_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
    if [[ -f "$CRED_PATH" && -r "$CRED_PATH" ]]; then
        echo -e "${GREEN}✅ Google Credentials: Configured${NC}"
        echo "   Path: $CRED_PATH"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ Google Credentials: File not found or not readable${NC}"
        echo "   Path: $CRED_PATH"
        ISSUES+=("GOOGLE_APPLICATION_CREDENTIALS points to invalid file")
        FAILED=$((FAILED + 1))
    fi
else
    # Check for Application Default Credentials
    ADC_CHECK=$(timeout 3 gcloud auth application-default print-access-token 2>/dev/null | head -1 || echo "")
    if [[ -n "$ADC_CHECK" ]]; then
        echo -e "${YELLOW}⚠️  Google Credentials: Using Application Default Credentials${NC}"
        echo "   GOOGLE_APPLICATION_CREDENTIALS not set, but ADC available"
        echo "   (This may work, but explicit credentials are recommended for cron)"
        ISSUES+=("Using ADC instead of explicit credentials - may fail in cron context")
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${RED}❌ Google Credentials: Not configured${NC}"
        echo "   Set GOOGLE_APPLICATION_CREDENTIALS or run: gcloud auth application-default login"
        ISSUES+=("Google credentials not configured - BigQuery jobs will fail")
        FAILED=$((FAILED + 1))
    fi
fi
echo ""

# ============================================================================
# 8. External Drive Write Test
# ============================================================================
echo "🔍 CHECK 8: External Drive Write Test"
echo "────────────────────────────────────────────────"
TEST_FILE="${REPO_PATH}/.diagnostic_write_test_$$"
if touch "$TEST_FILE" 2>/dev/null; then
    if [[ -f "$TEST_FILE" ]]; then
        rm -f "$TEST_FILE"
        echo -e "${GREEN}✅ External Drive Write: Successful${NC}"
        echo "   Test file created and removed successfully"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ External Drive Write: File creation failed${NC}"
        ISSUES+=("Cannot write to external drive - check permissions")
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ External Drive Write: Permission denied${NC}"
    ISSUES+=("Cannot write to external drive - run: bash fix_satechi_permissions.sh")
    FAILED=$((FAILED + 1))
fi
echo ""

# ============================================================================
# 9. macOS Sleep/Awake Configuration
# ============================================================================
echo "🔍 CHECK 9: macOS Sleep Configuration"
echo "────────────────────────────────────────────────"
PMSET_OUTPUT=$(pmset -g 2>/dev/null || echo "")
SLEEP_VALUE=$(echo "$PMSET_OUTPUT" | grep -E "^\s*sleep\s+" | awk '{print $2}' || echo "unknown")
DISPLAYSLEEP_VALUE=$(echo "$PMSET_OUTPUT" | grep -E "^\s*displaysleep\s+" | awk '{print $2}' || echo "unknown")

# Check if caffeinate is available
CAFFEINATE_AVAIL=$(which caffeinate >/dev/null 2>&1 && echo "yes" || echo "no")

# Check for active caffeinate processes
CAFFEINATE_RUNNING=0
if pgrep -f caffeinate >/dev/null 2>&1; then
    CAFFEINATE_RUNNING=$(pgrep -f caffeinate 2>/dev/null | wc -l | awk '{print $1}')
    CAFFEINATE_RUNNING=${CAFFEINATE_RUNNING:-0}
fi

SLEEP_OK=true
if [[ "$SLEEP_VALUE" == "0" ]] || [[ "$SLEEP_VALUE" == "unknown" ]]; then
    echo "   ✅ Sleep: Disabled (0) or unknown"
elif [[ "$SLEEP_VALUE" -gt 1440 ]]; then
    echo "   ✅ Sleep: Set to $SLEEP_VALUE minutes (>24 hours)"
else
    echo -e "   ${YELLOW}⚠️  Sleep: Set to $SLEEP_VALUE minutes (may interrupt cron jobs)${NC}"
    ISSUES+=("System sleep enabled ($SLEEP_VALUE min) - cron jobs may not run if Mac sleeps")
    SLEEP_OK=false
    WARNINGS=$((WARNINGS + 1))
fi

if [[ "$DISPLAYSLEEP_VALUE" == "0" ]] || [[ "$DISPLAYSLEEP_VALUE" == "unknown" ]]; then
    echo "   ✅ Display Sleep: Disabled (0) or unknown"
else
    echo "   ℹ️  Display Sleep: $DISPLAYSLEEP_VALUE minutes (doesn't affect cron)"
fi

if [[ "$CAFFEINATE_AVAIL" == "yes" ]]; then
    echo "   ✅ Caffeinate: Available"
    if [[ ${CAFFEINATE_RUNNING:-0} -gt 0 ]]; then
        echo "   ✅ Caffeinate: ${CAFFEINATE_RUNNING} process(es) running (system staying awake)"
    fi
else
    echo -e "   ${YELLOW}⚠️  Caffeinate: Not found${NC}"
fi

if [[ "$SLEEP_OK" == true && "$CAFFEINATE_AVAIL" == "yes" ]]; then
    echo -e "${GREEN}✅ macOS Sleep Configuration: Acceptable${NC}"
    PASSED=$((PASSED + 1))
elif [[ "$SLEEP_OK" == true ]]; then
    echo -e "${YELLOW}⚠️  macOS Sleep Configuration: Sleep disabled but caffeinate unavailable${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${YELLOW}⚠️  macOS Sleep Configuration: Sleep enabled - may affect cron reliability${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DIAGNOSTIC SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $PASSED checks${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS checks${NC}"
echo -e "${RED}❌ Failed: $FAILED checks${NC}"
echo ""

if [[ ${#ISSUES[@]} -gt 0 ]]; then
    echo "ISSUES DETECTED:"
    for i in "${!ISSUES[@]}"; do
        echo "  $((i + 1)). ${ISSUES[$i]}"
    done
    echo ""
fi

# Exit code
if [[ $FAILED -gt 0 ]]; then
    echo "❌ Critical issues detected - fix before running cron jobs"
    exit 2
elif [[ $WARNINGS -gt 0 ]]; then
    echo "⚠️  Warnings detected - review and address for optimal reliability"
    exit 1
else
    echo "✅ All checks passed - environment ready for cron/launchd scheduling"
    exit 0
fi

