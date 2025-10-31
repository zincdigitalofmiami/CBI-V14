#!/usr/bin/env bash
# CBI-V14 Rule Enforcement: Environment Variables
# Ensures no hardcoded credentials or project IDs

set -euo pipefail

echo "Checking environment variable usage..."

# Check for hardcoded project IDs (should use env vars)
HARDCODED_PROJECT=$(grep -r -n \
    -E "(PROJECT|project_id)\s*=\s*['\"]cbi-v14['\"]" \
    --include="*.py" --include="*.js" --include="*.jsx" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=.git \
    --exclude=PROJECT_RULES.md \
    --exclude=README.md \
    --exclude=*.sh || true)

if [ -n "$HARDCODED_PROJECT" ]; then
    echo "WARNING: Hardcoded project ID detected:"
    echo "$HARDCODED_PROJECT"
    echo ""
    echo "Rule #3: Use environment variables"
    echo "Replace with: os.environ['PROJECT'] or import.meta.env.VITE_PROJECT"
fi

# Check for .env files in git staging
if [ -d .git ]; then
    STAGED_ENV=$(git diff --cached --name-only 2>/dev/null | grep -E "^\.env$|\.env\.production$|\.env\.staging$" || true)

    if [ -n "$STAGED_ENV" ]; then
        echo "RULE VIOLATION: .env file staged for commit:"
        echo "$STAGED_ENV"
        echo ""
        echo "Never commit .env files with secrets"
        echo "Run: git reset HEAD $STAGED_ENV"
        exit 1
    fi
fi

# Check for service account keys
SA_KEYS=$(find . -type f -name "*-key.json" -o -name "service-account*.json" | grep -v node_modules || true)

if [ -n "$SA_KEYS" ]; then
    echo "WARNING: Service account keys found:"
    echo "$SA_KEYS"
    echo ""
    echo "Ensure these are in .gitignore"
fi

echo "PASS: Environment variable usage looks good"
exit 0
