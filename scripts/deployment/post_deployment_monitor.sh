#!/bin/bash
# ============================================================================
# Post-Deployment Monitoring Script
# Date: November 18, 2025
# Purpose: Run validation checks after each deployment phase
# ============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PHASE=0

cd "$REPO_ROOT" || exit 1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --phase)
      PHASE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --phase <1|2|3|4|5>"
      exit 1
      ;;
  esac
done

if [ "$PHASE" -eq 0 ]; then
  echo "❌ Error: --phase argument required"
  echo "Usage: $0 --phase <1|2|3|4|5>"
  exit 1
fi

echo "🔍 Post-Deployment Monitoring - Phase $PHASE"
echo "============================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

REPORT_FILE="DEPLOYMENT_PHASE_${PHASE}_RESULTS.md"

# Initialize report
cat > "$REPORT_FILE" << EOF
# Deployment Phase $PHASE Results
**Date:** $(date '+%Y-%m-%d %H:%M:%S')  
**Project:** CBI-V14  

---

EOF

# Phase-specific validation
case $PHASE in
  1)
    echo "📋 Phase 1: Validating Schema Deployment"
    echo "--------------------------------------------"
    echo ""
    echo "## Phase 1: Schema Deployment Validation" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Run validation for datasets and tables
    if python3 scripts/validation/validate_bq_deployment.py --phase 1 >> "$REPORT_FILE" 2>&1; then
      echo "✅ Phase 1 validation passed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ✅ PASS - Datasets and tables created successfully" >> "$REPORT_FILE"
      EXIT_CODE=0
    else
      echo "❌ Phase 1 validation failed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ❌ FAIL - Issues detected in schema deployment" >> "$REPORT_FILE"
      EXIT_CODE=1
    fi
    ;;
  
  2)
    echo "📋 Phase 2: Validating Folder Creation"
    echo "--------------------------------------------"
    echo ""
    echo "## Phase 2: Folder Creation Validation" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Check if live folders exist
    LIVE_PATH="/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live"
    LIVE_CONT_PATH="/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/live_continuous"
    
    if [ -d "$LIVE_PATH" ] && [ -d "$LIVE_CONT_PATH" ]; then
      echo "✅ Phase 2 validation passed - Folders exist"
      echo "- ✅ $LIVE_PATH" >> "$REPORT_FILE"
      echo "- ✅ $LIVE_CONT_PATH" >> "$REPORT_FILE"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ✅ PASS - Live folders created successfully" >> "$REPORT_FILE"
      EXIT_CODE=0
    else
      echo "❌ Phase 2 validation failed - Folders missing"
      if [ ! -d "$LIVE_PATH" ]; then
        echo "- ❌ $LIVE_PATH (missing)" >> "$REPORT_FILE"
      fi
      if [ ! -d "$LIVE_CONT_PATH" ]; then
        echo "- ❌ $LIVE_CONT_PATH (missing)" >> "$REPORT_FILE"
      fi
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ❌ FAIL - Live folders not created" >> "$REPORT_FILE"
      EXIT_CODE=1
    fi
    ;;
  
  3)
    echo "📋 Phase 3: Validating Overlay Views"
    echo "--------------------------------------------"
    echo ""
    echo "## Phase 3: Overlay Views Validation" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Run validation for views
    if python3 scripts/validation/validate_bq_deployment.py --phase 3 >> "$REPORT_FILE" 2>&1; then
      echo "✅ Phase 3 validation passed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ✅ PASS - Overlay views created successfully" >> "$REPORT_FILE"
      EXIT_CODE=0
    else
      echo "❌ Phase 3 validation failed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ❌ FAIL - Issues detected in overlay views" >> "$REPORT_FILE"
      EXIT_CODE=1
    fi
    ;;
  
  4)
    echo "📋 Phase 4: Validating Data Migration"
    echo "--------------------------------------------"
    echo ""
    echo "## Phase 4: Data Migration Validation" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Run validation for data
    if python3 scripts/validation/validate_bq_deployment.py --phase 4 >> "$REPORT_FILE" 2>&1; then
      echo "✅ Phase 4 validation passed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ✅ PASS - Data migrated successfully" >> "$REPORT_FILE"
      EXIT_CODE=0
    else
      echo "❌ Phase 4 validation failed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ❌ FAIL - Issues detected in data migration" >> "$REPORT_FILE"
      EXIT_CODE=1
    fi
    ;;
  
  5)
    echo "📋 Phase 5: Full Deployment Validation"
    echo "--------------------------------------------"
    echo ""
    echo "## Phase 5: Full Deployment Validation" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Run full validation
    if python3 scripts/validation/validate_bq_deployment.py --phase 5 >> "$REPORT_FILE" 2>&1; then
      echo "✅ Phase 5 validation passed - Full deployment validated"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ✅ PASS - Full deployment validated successfully" >> "$REPORT_FILE"
      EXIT_CODE=0
    else
      echo "❌ Phase 5 validation failed"
      echo "" >> "$REPORT_FILE"
      echo "**Status:** ❌ FAIL - Issues detected in full deployment" >> "$REPORT_FILE"
      EXIT_CODE=1
    fi
    ;;
  
  *)
    echo "❌ Invalid phase: $PHASE"
    echo "Valid phases: 1 (schema), 2 (folders), 3 (views), 4 (data), 5 (full)"
    exit 1
    ;;
esac

echo ""
echo "Report saved to: $REPORT_FILE"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Phase $PHASE monitoring complete - All checks passed"
else
  echo "❌ Phase $PHASE monitoring complete - Some checks failed"
  echo "Review $REPORT_FILE for details"
fi

exit $EXIT_CODE





