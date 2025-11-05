#!/bin/bash
# CBI-V14 AGGRESSIVE REORGANIZATION - EXECUTION SCRIPT
# Complete restructure with active/old/new system for everything
# WARNING: This makes significant structural changes!

set -e  # Exit on error

PROJECT_ROOT="/Users/zincdigital/CBI-V14"
cd "$PROJECT_ROOT"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     CBI-V14 AGGRESSIVE REORGANIZATION - EXECUTE                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  WARNING: This will make MAJOR structural changes!"
echo "⚠️  This script will:"
echo "    • Create new active/old/new folder structure"
echo "    • Move system files to system/ folder"
echo "    • Reorganize ALL documentation"
echo "    • Rename folders to kebab-case"
echo "    • Delete empty folders"
echo ""
read -p "Create backup and continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# PHASE 0: BACKUP
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 0: Creating backup..."
echo "═══════════════════════════════════════════════════════════════"

BACKUP_NAME="CBI-V14-pre-aggressive-reorg-$(date +%Y%m%d-%H%M%S).tar.gz"
cd ..
tar -czf "$BACKUP_NAME" CBI-V14/ \
    --exclude='node_modules' \
    --exclude='cbi_venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git'
cd "$PROJECT_ROOT"

echo "✅ Backup created: ../$BACKUP_NAME"

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: CREATE NEW STRUCTURE
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 1: Creating new folder structure..."
echo "═══════════════════════════════════════════════════════════════"

# System folder
mkdir -p system/{config,docs,scripts}

# Category folders with active/old/new
mkdir -p audits/{active,old,new}
mkdir -p plans/{active,old,new}
mkdir -p documentation/active/{api-references,guides,system-docs}
mkdir -p documentation/{old,new}
mkdir -p code-reviews/{active,old,new}
mkdir -p deployment/{active,old,new}
mkdir -p data/{active,old,new}
mkdir -p models/{active,old,new}
mkdir -p logs/{active,old,error-logs}

echo "✅ New structure created"

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: MOVE SYSTEM FILES
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 2: Organizing system files..."
echo "═══════════════════════════════════════════════════════════════"

# Move to system/config/
[ -f "Makefile" ] && mv Makefile system/config/ && echo "  ✓ Moved Makefile"
[ -f "cloudbuild.yaml" ] && cp cloudbuild.yaml system/config/ && echo "  ✓ Copied cloudbuild.yaml (keeping root symlink)"
[ -f ".pre-commit-config.yaml" ] && cp .pre-commit-config.yaml system/config/ && echo "  ✓ Copied .pre-commit-config.yaml"

# Move to system/docs/
[ -f "LICENSE" ] && mv LICENSE system/docs/ && echo "  ✓ Moved LICENSE"

# Keep CONTRIBUTING.md visible for now, can move later
# [ -f "CONTRIBUTING.md" ] && mv CONTRIBUTING.md system/docs/

# Move config folder contents
if [ -d "config" ]; then
    cp -r config/* system/config/ 2>/dev/null || true
    echo "  ✓ Copied config/ contents"
fi

# Create README for system folder
cat > system/README.md << 'EOF'
# System Configuration & Build Files

This folder contains all system-level configuration, build files, and maintenance scripts.

## Structure

- `config/` - Build configs, deployment files, makefiles
- `docs/` - Contributor guides, license, setup docs  
- `scripts/` - System maintenance and setup scripts

## Files

### config/
- `Makefile` - Build automation
- `cloudbuild.yaml` - Cloud Build configuration
- `.pre-commit-config.yaml` - Git pre-commit hooks
- Other deployment and build configs

### docs/
- `LICENSE` - Project license
- `CONTRIBUTING.md` - Contribution guidelines
- Setup and installation guides

Note: Some files (README.md, .gitignore) must stay in project root per tool requirements.
EOF

echo "✅ System files organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: ORGANIZE AUDITS
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 3: Organizing audits..."
echo "═══════════════════════════════════════════════════════════════"

# Move old audits
if [ -d "docs/audits" ]; then
    find docs/audits -name "*.md" -type f -exec mv {} audits/old/ \; 2>/dev/null || true
    echo "  ✓ Moved docs/audits/*.md → audits/old/"
fi

# Move any audit CSVs
if [ -d "docs/audits" ]; then
    find docs/audits -name "*.csv" -type f -exec mv {} audits/old/ \; 2>/dev/null || true
fi

echo "✅ Audits organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 4: ORGANIZE PLANS
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 4: Organizing plans..."
echo "═══════════════════════════════════════════════════════════════"

# Move old plans
if [ -d "docs/older-plans" ]; then
    find docs/older-plans -name "*.md" -type f -exec mv {} plans/old/ \; 2>/dev/null || true
    echo "  ✓ Moved docs/older-plans/*.md → plans/old/"
fi

# Create symlink to main plan
if [ -f "CBI_V14_COMPLETE_EXECUTION_PLAN.md" ]; then
    ln -sf ../../CBI_V14_COMPLETE_EXECUTION_PLAN.md plans/active/
    echo "  ✓ Created symlink to main plan in plans/active/"
fi

echo "✅ Plans organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 5: ORGANIZE DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 5: Organizing documentation..."
echo "═══════════════════════════════════════════════════════════════"

# API references
find docs -maxdepth 1 -name "*API*" -o -name "*REFERENCE*" | while read file; do
    [ -f "$file" ] && mv "$file" documentation/active/api-references/ && echo "  ✓ Moved $(basename $file) → api-references/"
done

# Guides
find docs -maxdepth 1 -name "*GUIDE*" | while read file; do
    [ -f "$file" ] && mv "$file" documentation/active/guides/ && echo "  ✓ Moved $(basename $file) → guides/"
done

# System docs
find docs -maxdepth 1 \( -name "*SYSTEM*" -o -name "*INTEGRATION*" -o -name "*README*" \) | while read file; do
    [ -f "$file" ] && mv "$file" documentation/active/system-docs/ && echo "  ✓ Moved $(basename $file) → system-docs/"
done

# Move remaining docs
find docs -maxdepth 1 -name "*.md" -type f | while read file; do
    [ -f "$file" ] && mv "$file" documentation/new/ && echo "  ✓ Moved $(basename $file) → documentation/new/"
done

echo "✅ Documentation organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 6: ORGANIZE CODE REVIEWS
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 6: Organizing code reviews..."
echo "═══════════════════════════════════════════════════════════════"

if [ -d "docs/reference-archive" ]; then
    find docs/reference-archive -name "*REVIEW*" -o -name "*TEST*" | while read file; do
        [ -f "$file" ] && mv "$file" code-reviews/old/ && echo "  ✓ Moved $(basename $file)"
    done
fi

echo "✅ Code reviews organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 7: ORGANIZE DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 7: Organizing deployment docs..."
echo "═══════════════════════════════════════════════════════════════"

if [ -d "archive/deployment-history" ]; then
    find archive/deployment-history -type f | while read file; do
        [ -f "$file" ] && mv "$file" deployment/old/ && echo "  ✓ Moved $(basename $file)"
    done
fi

echo "✅ Deployment docs organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 8: ORGANIZE DATA
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 8: Organizing data files..."
echo "═══════════════════════════════════════════════════════════════"

# Create social-media subfolder in active
mkdir -p data/active/social-media

# Move social media data
for platform in facebook twitter truth_social linkedin reddit tiktok youtube; do
    if [ -d "data/$platform" ]; then
        mv "data/$platform" data/active/social-media/
        echo "  ✓ Moved data/$platform/ → data/active/social-media/"
    fi
done

# Move old CSV data if exists
if [ -d "data/old/2025" ]; then
    echo "  ✓ data/old/2025 already exists"
else
    # Already organized
    echo "  ✓ Data structure looks good"
fi

echo "✅ Data organized"

# ═══════════════════════════════════════════════════════════════════
# PHASE 9: RENAME FOLDERS (Standardize to kebab-case)
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 9: Renaming folders to kebab-case..."
echo "═══════════════════════════════════════════════════════════════"

# Rename folders
[ -d "bigquery_sql" ] && mv bigquery_sql bigquery-sql && echo "  ✓ bigquery_sql → bigquery-sql"
[ -d "cbi-v14-ingestion" ] && mv cbi-v14-ingestion ingestion && echo "  ✓ cbi-v14-ingestion → ingestion"
[ -d "models_v4" ] && mv models_v4 models-temp && echo "  ✓ models_v4 → models-temp"
[ -d "terraform-deploy" ] && mv terraform-deploy terraform && echo "  ✓ terraform-deploy → terraform"
[ -d "automl" ] && mv automl vertex-ai && echo "  ✓ automl → vertex-ai"
[ -d "cbi_venv" ] && mv cbi_venv .venv && echo "  ✓ cbi_venv → .venv"

# Move models to new structure
if [ -d "models-temp" ]; then
    mkdir -p models/active
    mv models-temp/* models/active/ 2>/dev/null || true
    rmdir models-temp 2>/dev/null || true
    echo "  ✓ Organized models into models/active/"
fi

echo "✅ Folders renamed"

# ═══════════════════════════════════════════════════════════════════
# PHASE 10: DELETE EMPTY FOLDERS
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 10: Deleting empty folders..."
echo "═══════════════════════════════════════════════════════════════"

# Delete empty folders
for folder in cache cb-ingest inmet_csv_data; do
    if [ -d "$folder" ] && [ ! "$(ls -A $folder)" ]; then
        rmdir "$folder" && echo "  ✓ Deleted $folder/"
    fi
done

# Clean up old docs folder if empty
if [ -d "docs" ]; then
    find docs -type d -empty -delete 2>/dev/null || true
    if [ ! "$(ls -A docs 2>/dev/null)" ]; then
        rmdir docs && echo "  ✓ Deleted empty docs/"
    fi
fi

# Clean up old archive folders if empty
if [ -d "archive/deployment-history" ]; then
    rmdir archive/deployment-history 2>/dev/null && echo "  ✓ Deleted archive/deployment-history/"
fi

# Clean up old config if empty
if [ -d "config" ] && [ ! "$(ls -A config)" ]; then
    rmdir config && echo "  ✓ Deleted empty config/"
fi

echo "✅ Empty folders deleted"

# ═══════════════════════════════════════════════════════════════════
# PHASE 11: CREATE INDEX FILES
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 11: Creating index/README files..."
echo "═══════════════════════════════════════════════════════════════"

# Create README files for each major category
cat > audits/README.md << 'EOF'
# Audits

All project audits organized by status.

- `active/` - Currently running audits
- `old/` - Completed audits
- `new/` - Recently created, needs categorization
EOF

cat > plans/README.md << 'EOF'
# Plans

All project plans organized by status.

- `active/` - Current execution plans
- `old/` - Completed plans  
- `new/` - Proposed plans pending approval
EOF

cat > documentation/README.md << 'EOF'
# Documentation

All project documentation organized by status.

- `active/` - Current living documentation
  - `api-references/` - API documentation
  - `guides/` - How-to guides
  - `system-docs/` - System documentation
- `old/` - Historical/outdated documentation
- `new/` - Recently added, needs categorization
EOF

echo "✅ Index files created"

# ═══════════════════════════════════════════════════════════════════
# FINAL: SUMMARY
# ═══════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ AGGRESSIVE REORGANIZATION COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 New Structure Created:"
echo "   • system/ - All config & system files"
echo "   • audits/active|old|new/ - All audits"
echo "   • plans/active|old|new/ - All plans"
echo "   • documentation/active|old|new/ - All docs"
echo "   • code-reviews/active|old|new/ - All reviews"
echo "   • deployment/active|old|new/ - All deployment docs"
echo "   • data/active|old|new/ - All data"
echo "   • models/active|old|new/ - All models"
echo ""
echo "📁 Folders Renamed:"
echo "   • bigquery_sql → bigquery-sql"
echo "   • cbi-v14-ingestion → ingestion"
echo "   • models_v4 → models"
echo "   • terraform-deploy → terraform"
echo "   • automl → vertex-ai"
echo "   • cbi_venv → .venv"
echo ""
echo "🗑️  Deleted:"
echo "   • Empty folders (cache, cb-ingest, inmet_csv_data)"
echo "   • Old docs/ structure (moved to new locations)"
echo ""
echo "💾 Backup: ../$BACKUP_NAME"
echo ""
echo "⚠️  NEXT STEPS:"
echo "   1. Review new structure"
echo "   2. Update import paths in scripts"
echo "   3. Test key functionality"
echo "   4. Update documentation references"
echo ""
echo "📊 Root directory now has MINIMAL files!"
echo ""
ls -1 *.md 2>/dev/null || echo "No loose MD files in root!"
echo ""

