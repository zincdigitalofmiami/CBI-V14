#!/bin/bash
# CBI-V14 Folder Reorganization - Executable Commands
# READ ONLY REVIEW - DO NOT EXECUTE WITHOUT APPROVAL
# Date: November 5, 2025

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     CBI-V14 FOLDER REORGANIZATION - EXECUTION SCRIPT           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  WARNING: This script will reorganize your folder structure."
echo "⚠️  Make sure you have reviewed FOLDER_ORGANIZATION_REVIEW.md first."
echo ""
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# PHASE 0: BACKUP (ALWAYS RUN FIRST)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 0: Creating backup..."
echo "═══════════════════════════════════════════════════════════════"

BACKUP_NAME="CBI-V14-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "../$BACKUP_NAME" . --exclude='node_modules' --exclude='cbi_venv' --exclude='.venv' --exclude='__pycache__'
echo "✅ Backup created: ../$BACKUP_NAME"

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: DELETE EMPTY FOLDERS (LOW RISK - 5 minutes)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 1: Deleting empty folders..."
echo "═══════════════════════════════════════════════════════════════"

# Verify folders are actually empty
if [ ! "$(ls -A cache/)" ]; then
    rmdir cache/
    echo "✅ Deleted: cache/"
else
    echo "⚠️  Skipped: cache/ (not empty)"
fi

if [ ! "$(ls -A cb-ingest/)" ]; then
    rmdir cb-ingest/
    echo "✅ Deleted: cb-ingest/"
else
    echo "⚠️  Skipped: cb-ingest/ (not empty)"
fi

if [ ! "$(ls -A inmet_csv_data/)" ]; then
    rmdir inmet_csv_data/
    echo "✅ Deleted: inmet_csv_data/"
else
    echo "⚠️  Skipped: inmet_csv_data/ (not empty)"
fi

echo "✅ Phase 1 Complete - Empty folders removed"

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: SEARCH FOR HARDCODED PATHS (CRITICAL - Don't skip!)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 2: Searching for hardcoded paths..."
echo "═══════════════════════════════════════════════════════════════"

echo "Searching for: cbi-v14-ingestion"
grep -r "cbi-v14-ingestion" . --exclude-dir=node_modules --exclude-dir=cbi_venv --exclude-dir=.git \
    --exclude-dir=__pycache__ --exclude="*.log" --exclude="*.md" 2>/dev/null | head -20 || echo "  None found ✅"

echo ""
echo "Searching for: bigquery_sql"
grep -r "bigquery_sql" . --exclude-dir=node_modules --exclude-dir=cbi_venv --exclude-dir=.git \
    --exclude-dir=__pycache__ --exclude="*.log" --exclude="*.md" 2>/dev/null | head -20 || echo "  None found ✅"

echo ""
echo "Searching for: models_v4"
grep -r "models_v4" . --exclude-dir=node_modules --exclude-dir=cbi_venv --exclude-dir=.git \
    --exclude-dir=__pycache__ --exclude="*.log" --exclude="*.md" 2>/dev/null | head -20 || echo "  None found ✅"

echo ""
echo "Searching for: cbi_venv"
grep -r "cbi_venv" . --exclude-dir=node_modules --exclude-dir=cbi_venv --exclude-dir=.git \
    --exclude-dir=__pycache__ --exclude="*.log" --exclude="*.md" 2>/dev/null | head -20 || echo "  None found ✅"

echo ""
echo "⚠️  IMPORTANT: Review the output above before proceeding to Phase 3"
echo "⚠️  Update any hardcoded paths found before renaming folders"
echo ""
read -p "All paths updated? Continue to Phase 3? (yes/no): " PHASE3_CONFIRM
if [ "$PHASE3_CONFIRM" != "yes" ]; then
    echo "❌ Paused. Update paths manually, then re-run starting from Phase 3."
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: RENAME FOLDERS (MEDIUM RISK - 2 hours with testing)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 3: Renaming folders..."
echo "═══════════════════════════════════════════════════════════════"

# Rename folders to standardize naming
mv bigquery_sql/ bigquery-sql/
echo "✅ Renamed: bigquery_sql → bigquery-sql"

mv models_v4/ models/
echo "✅ Renamed: models_v4 → models"

mv cbi-v14-ingestion/ ingestion/
echo "✅ Renamed: cbi-v14-ingestion → ingestion"

mv automl/ vertex-ai/
echo "✅ Renamed: automl → vertex-ai"

mv terraform-deploy/ terraform/
echo "✅ Renamed: terraform-deploy → terraform"

mv cbi_venv/ .venv/
echo "✅ Renamed: cbi_venv → .venv"

echo "✅ Phase 3 Complete - Folders renamed"

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: ARCHIVE OLD DATA (LOW RISK - 10 minutes)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 4: Archiving old data..."
echo "═══════════════════════════════════════════════════════════════"

# Create archive directory
mkdir -p archive/data-snapshots/oct-2025/

# Move old CSV data (from Oct 3)
if [ -d "data/csv" ] && [ "$(ls -A data/csv)" ]; then
    mv data/csv/* archive/data-snapshots/oct-2025/
    rmdir data/csv
    echo "✅ Moved: data/csv/ → archive/data-snapshots/oct-2025/"
else
    echo "⚠️  Skipped: data/csv/ (already moved or empty)"
fi

echo "✅ Phase 4 Complete - Old data archived"

# ═══════════════════════════════════════════════════════════════════
# PHASE 5: INVESTIGATE src/ FOLDER (MANUAL - 15 minutes)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 5: Investigate src/ folder (MANUAL ACTION REQUIRED)"
echo "═══════════════════════════════════════════════════════════════"

echo "📁 Contents of src/:"
ls -lah src/

echo ""
echo "❓ Is this legacy code or actively used?"
echo ""
echo "Option A: If LEGACY → Run: mv src/ archive/legacy-react/"
echo "Option B: If ACTIVE → Rename appropriately or merge into dashboard"
echo ""
echo "⚠️  This step requires manual decision - not automated"

# ═══════════════════════════════════════════════════════════════════
# PHASE 6: VERIFICATION & TESTING
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 6: Verification"
echo "═══════════════════════════════════════════════════════════════"

echo ""
echo "📋 Final folder structure:"
ls -d */ | sort

echo ""
echo "✅ REORGANIZATION COMPLETE!"
echo ""
echo "📝 Next Steps:"
echo "  1. Test key scripts to verify imports still work"
echo "  2. Update any documentation with new paths"
echo "  3. Run cron_audit_report.py to verify functionality"
echo "  4. Update .gitignore if needed (add .venv/)"
echo "  5. Git commit: 'refactor: reorganize folder structure for clarity'"
echo ""
echo "💾 Backup location: ../$BACKUP_NAME"
echo ""

# ═══════════════════════════════════════════════════════════════════
# END OF SCRIPT
# ═══════════════════════════════════════════════════════════════════

