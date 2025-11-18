#!/bin/bash
# Final Migration Verification: Local Files & Scripts
# - Verifies new data exports exist
# - Checks for and recommends removal of old data exports
# - Greps for any lingering old naming patterns in scripts

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo "========================================================================"
echo "FINAL MIGRATION VERIFICATION: LOCAL FILES & SCRIPTS"
echo "========================================================================"

ALL_OK=true

# 1. Verify new data exports
echo
echo "1. Verifying New Data Exports (TrainingData/exports/)..."
echo "------------------------------------------------------------------------"
NEW_FILES_FOUND=0
for horizon in 1w 1m 3m 6m 12m; do
    for surface in prod full; do
        FILE="TrainingData/exports/zl_training_${surface}_allhistory_${horizon}.parquet"
        if [ -f "$FILE" ]; then
            echo "  ✅ ${FILE}"
            ((NEW_FILES_FOUND++))
        else
            echo "  ❌ ${FILE} - NOT FOUND"
            ALL_OK=false
        fi
    done
done

# 2. Check for old data exports
echo
echo "2. Checking for Old Data Exports..."
echo "------------------------------------------------------------------------"
OLD_FILES=$(find TrainingData/exports -name "production_training_data_*.parquet" | wc -l)
if [ "$OLD_FILES" -gt 0 ]; then
    echo "  ⚠️  Found ${OLD_FILES} old data export files. Recommend removal:"
    find TrainingData/exports -name "production_training_data_*.parquet" -exec echo "     - {}" \;
    echo "     rm TrainingData/exports/production_training_data_*.parquet"
else
    echo "  ✅ No old data export files found."
fi

# 3. Grep for lingering old patterns
echo
echo "3. Grepping for Lingering Old Patterns in Scripts..."
echo "------------------------------------------------------------------------"
LINGERING_PATTERNS=$(grep -r "production_training_data" src/training src/prediction --include="*.py" | grep -v "__pycache__" | wc -l | tr -d ' ')
if [ "$LINGERING_PATTERNS" -gt 0 ]; then
    echo "  ❌ Found ${LINGERING_PATTERNS} lingering instances of 'production_training_data' in scripts:"
    grep -r "production_training_data" src/training src/prediction --include="*.py" | grep -v "__pycache__"
    ALL_OK=false
else
    echo "  ✅ No lingering old patterns found in training or prediction scripts."
fi


echo
echo "========================================================================"
if [ "$ALL_OK" = true ]; then
    echo "✅ LOCAL FILE & SCRIPT VERIFICATION PASSED"
else
    echo "❌ LOCAL FILE & SCRIPT VERIFICATION FAILED - some issues found."
fi
echo "========================================================================"


