#!/bin/bash
# Add best practices header to SQL files
# Usage: ./scripts/utilities/add_best_practices_to_sql.sh [sql_file]

BEST_PRACTICES_HEADER="-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--
-- 📋 BEST PRACTICES: See \`.cursorrules\` and \`docs/reference/BEST_PRACTICES_DRAFT.md\` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results
--
"

if [ -z "$1" ]; then
    echo "Usage: $0 <sql_file>"
    echo "Or to add to all SQL files in config/bigquery:"
    echo "  find config/bigquery -name '*.sql' -exec $0 {} \;"
    exit 1
fi

SQL_FILE="$1"

# Check if file already has best practices header
if grep -q "BEST PRACTICES:" "$SQL_FILE"; then
    echo "✅ $SQL_FILE already has best practices header"
    exit 0
fi

# Add header after existing NO FAKE DATA comment if present
if grep -q "CRITICAL: NO FAKE DATA" "$SQL_FILE"; then
    # Insert after the NO FAKE DATA section
    awk -v header="$BEST_PRACTICES_HEADER" '
        /^-- All data must come from authenticated APIs/ {
            print
            print ""
            print header
            next
        }
        { print }
    ' "$SQL_FILE" > "$SQL_FILE.tmp" && mv "$SQL_FILE.tmp" "$SQL_FILE"
    echo "✅ Added best practices header to $SQL_FILE"
else
    # Prepend to file
    echo "$BEST_PRACTICES_HEADER" | cat - "$SQL_FILE" > "$SQL_FILE.tmp" && mv "$SQL_FILE.tmp" "$SQL_FILE"
    echo "✅ Added best practices header to $SQL_FILE (prepended)"
fi









