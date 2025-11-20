#!/bin/bash
# ============================================================================
# Shell Script Linting Validation
# Date: November 18, 2025
# Purpose: Lint all deployment scripts using shellcheck
# ============================================================================

set -uo pipefail

echo "🔍 Shell Script Linting Validation"
echo "============================================"
echo ""

# Check if shellcheck is installed
if ! command -v shellcheck &> /dev/null; then
  echo "⚠️  WARNING: shellcheck not installed"
  echo ""
  echo "Install with:"
  echo "  macOS: brew install shellcheck"
  echo "  Linux: apt-get install shellcheck"
  echo ""
  echo "Skipping shell linting..."
  exit 0
fi

echo "✅ shellcheck found: $(shellcheck --version | head -1)"
echo ""

# Validation counters
TOTAL_SCRIPTS=0
PASSED_SCRIPTS=0
FAILED_SCRIPTS=0
WARNED_SCRIPTS=0

# Find all shell scripts in deployment and validation directories
SCRIPTS=(
  "scripts/deployment/deploy_bq_schema.sh"
  "scripts/validation/pre_flight_sql_validation.sh"
  "scripts/validation/lint_deployment_scripts.sh"
)

# Add any additional scripts found
while IFS= read -r script; do
  if [[ ! " ${SCRIPTS[@]} " =~ " ${script} " ]]; then
    SCRIPTS+=("$script")
  fi
done < <(find scripts/deployment scripts/validation -name "*.sh" -type f 2>/dev/null || true)

echo "Found ${#SCRIPTS[@]} shell scripts to lint"
echo ""

# Lint each script
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$script" ]; then
    continue
  fi
  
  TOTAL_SCRIPTS=$((TOTAL_SCRIPTS + 1))
  echo "📋 Linting: $script"
  echo "--------------------------------------------"
  
  # Run shellcheck
  if shellcheck -x "$script" 2>&1; then
    echo "✅ PASS: No issues found"
    PASSED_SCRIPTS=$((PASSED_SCRIPTS + 1))
  else
    # Check exit code
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 1 ]; then
      echo "❌ FAIL: Critical issues found"
      FAILED_SCRIPTS=$((FAILED_SCRIPTS + 1))
    else
      echo "⚠️  WARNING: Minor issues found"
      WARNED_SCRIPTS=$((WARNED_SCRIPTS + 1))
    fi
  fi
  echo ""
done

# ============================================================================
# Check 1: Proper shebangs
# ============================================================================
echo "📋 Check 1: Proper Shebangs"
echo "--------------------------------------------"

MISSING_SHEBANG=()
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$script" ]; then
    continue
  fi
  
  FIRST_LINE=$(head -1 "$script")
  if [[ ! "$FIRST_LINE" =~ ^#!/ ]]; then
    MISSING_SHEBANG+=("$script")
  fi
done

if [ ${#MISSING_SHEBANG[@]} -eq 0 ]; then
  echo "✅ PASS: All scripts have proper shebangs"
else
  echo "❌ FAIL: Missing shebangs:"
  for script in "${MISSING_SHEBANG[@]}"; do
    echo "   - $script"
  done
fi
echo ""

# ============================================================================
# Check 2: Executable permissions
# ============================================================================
echo "📋 Check 2: Executable Permissions"
echo "--------------------------------------------"

NON_EXECUTABLE=()
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$script" ]; then
    continue
  fi
  
  if [ ! -x "$script" ]; then
    NON_EXECUTABLE+=("$script")
  fi
done

if [ ${#NON_EXECUTABLE[@]} -eq 0 ]; then
  echo "✅ PASS: All scripts are executable"
else
  echo "⚠️  WARNING: Non-executable scripts (fix with chmod +x):"
  for script in "${NON_EXECUTABLE[@]}"; do
    echo "   - $script"
  done
fi
echo ""

# ============================================================================
# Check 3: Error handling (set -e or set -uo pipefail)
# ============================================================================
echo "📋 Check 3: Error Handling (set flags)"
echo "--------------------------------------------"

NO_ERROR_HANDLING=()
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$script" ]; then
    continue
  fi
  
  if ! grep -q "set -" "$script"; then
    NO_ERROR_HANDLING+=("$script")
  fi
done

if [ ${#NO_ERROR_HANDLING[@]} -eq 0 ]; then
  echo "✅ PASS: All scripts use error handling (set flags)"
else
  echo "⚠️  WARNING: Missing error handling:"
  for script in "${NO_ERROR_HANDLING[@]}"; do
    echo "   - $script"
  done
  echo ""
  echo "Recommended: Add 'set -euo pipefail' or 'set -uo pipefail'"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "============================================"
echo "LINTING SUMMARY"
echo "============================================"
echo "Total scripts: $TOTAL_SCRIPTS"
echo "Passed: $PASSED_SCRIPTS"
echo "Warnings: $WARNED_SCRIPTS"
echo "Failed: $FAILED_SCRIPTS"
echo ""

if [ "$FAILED_SCRIPTS" -eq 0 ]; then
  if [ "$WARNED_SCRIPTS" -eq 0 ]; then
    echo "✅ ALL SCRIPTS PASSED - No issues found"
    exit 0
  else
    echo "⚠️  SCRIPTS PASSED WITH WARNINGS - Review warnings above"
    exit 0
  fi
else
  echo "❌ LINTING FAILED - Fix critical issues before deployment"
  exit 1
fi





