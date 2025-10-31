#!/usr/bin/env bash
# CBI-V14 Rule Enforcement: NO MOCK DATA - EVER
# This script fails the build if any mock data is detected

set -euo pipefail

echo "Checking for mock data violations..."

# Check for forbidden filenames
FORBIDDEN_FILES=$(find . -type f \( \
    -name "*mock*.js" -o \
    -name "*mock*.py" -o \
    -name "*fake*.js" -o \
    -name "*fake*.py" -o \
    -name "*sample*.js" -o \
    -name "*dummy*.js" -o \
    -name "fixtures.js" \
    \) ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/.git/*" || true)

if [ -n "$FORBIDDEN_FILES" ]; then
    echo "RULE VIOLATION: Mock data files detected:"
    echo "$FORBIDDEN_FILES"
    echo ""
    echo "Rule #1: NO MOCK DATA - EVER"
    echo "Remove these files or rename them."
    exit 1
fi

# Check for forbidden variable names in JavaScript/React
MOCK_VARS_JS=$(grep -r -n \
    -E "(mockData|fakeData|sampleData|dummyData|testData)\s*=" \
    --include="*.js" --include="*.jsx" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=dist \
    --exclude-dir=build \
    --exclude-dir=.git || true)

if [ -n "$MOCK_VARS_JS" ]; then
    echo "RULE VIOLATION: Mock data variables detected in JavaScript:"
    echo "$MOCK_VARS_JS"
    echo ""
    echo "Rule #1: NO MOCK DATA - Use real API calls only"
    exit 1
fi

# Check for forbidden imports (faker library)
FAKER_IMPORTS=$(grep -r -n \
    -E "from ['\"](faker|@faker-js)" \
    --include="*.js" --include="*.jsx" --include="*.py" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=.git || true)

if [ -n "$FAKER_IMPORTS" ]; then
    echo "RULE VIOLATION: Faker library detected:"
    echo "$FAKER_IMPORTS"
    echo ""
    echo "Rule #1: NO MOCK DATA - Remove faker imports"
    exit 1
fi

# Check for TODO comments about mock data
TODO_MOCK=$(grep -r -n \
    -E "TODO.*mock|FIXME.*fake|TODO.*replace with real" \
    --include="*.js" --include="*.jsx" --include="*.py" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=.git || true)

if [ -n "$TODO_MOCK" ]; then
    echo "WARNING: TODO comments about mock data:"
    echo "$TODO_MOCK"
    echo ""
    echo "Resolve these before committing."
fi

echo "PASS: No mock data violations detected"
exit 0
