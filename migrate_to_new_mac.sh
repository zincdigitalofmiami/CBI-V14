#!/bin/bash

# CBI-V14 Mac Migration Script
# This script prepares a migration package from your current Mac to a new Mac Mini

set -e  # Exit on error

echo "🚀 CBI-V14 Mac Migration Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create migration package directory
MIGRATION_DIR="$HOME/migration_package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${YELLOW}Creating migration package directory...${NC}"
rm -rf "$MIGRATION_DIR"
mkdir -p "$MIGRATION_DIR"/{git_repos,cursor_settings,python_envs,gcloud_config,docs}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# STEP 1: Export Git Repositories
echo -e "\n${GREEN}STEP 1: Exporting Git Repositories...${NC}"

repos=(
    "/Users/zincdigital/CBI-V14:https://github.com/zincdigitalofmiami/CBI-V14"
    "/Users/zincdigital/Crystal-Ball-V12:https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git"
    "/Users/zincdigital/Projects/summit-marine-development:https://github.com/zincdigitalofmiami/summit-marine-development"
)

for repo_info in "${repos[@]}"; do
    IFS=':' read -r repo_path repo_url <<< "$repo_info"
    repo_name=$(basename "$repo_path")
    
    if [ -d "$repo_path/.git" ]; then
        echo "  📦 Exporting $repo_name..."
        cd "$repo_path"
        git bundle create "$MIGRATION_DIR/git_repos/${repo_name}.bundle" --all
        echo "    ✅ $repo_name exported"
    else
        echo "    ⚠️  $repo_name not found at $repo_path"
    fi
done

# STEP 2: Export Cursor Settings
echo -e "\n${GREEN}STEP 2: Exporting Cursor Settings...${NC}"
if [ -d "$HOME/.cursor" ]; then
    echo "  📦 Copying Cursor settings..."
    cp -r "$HOME/.cursor" "$MIGRATION_DIR/cursor_settings/"
    echo "    ✅ Cursor settings exported"
else
    echo "    ⚠️  Cursor settings not found"
fi

# STEP 3: Export Python Environment Info
echo -e "\n${GREEN}STEP 3: Exporting Python Environment Info...${NC}"

if command_exists pyenv; then
    echo "  📦 Exporting pyenv versions..."
    pyenv versions > "$MIGRATION_DIR/python_envs/pyenv_versions.txt" 2>&1 || true
    
    # Export packages for each Python version
    for version in 3.12.6 3.10.12; do
        if pyenv versions --bare | grep -q "^${version}$"; then
            echo "    📦 Exporting packages for Python $version..."
            pyenv global "$version"
            pip3 freeze > "$MIGRATION_DIR/python_envs/requirements_python${version//./}.txt" 2>&1 || true
        fi
    done
    
    # Export virtualenv info
    if pyenv versions --bare | grep -q "vertex-metal-310"; then
        echo "    📦 Found vertex-metal-310 virtualenv"
        echo "vertex-metal-310" > "$MIGRATION_DIR/python_envs/virtualenvs.txt"
    fi
    
    echo "    ✅ Python environment info exported"
else
    echo "    ⚠️  pyenv not found"
fi

# Also export current pip packages
if command_exists pip3; then
    echo "  📦 Exporting current pip packages..."
    pip3 freeze > "$MIGRATION_DIR/python_envs/requirements_current.txt" 2>&1 || true
fi

# STEP 4: Export Google Cloud Config (read-only info)
echo -e "\n${GREEN}STEP 4: Exporting Google Cloud Configuration...${NC}"

if command_exists gcloud; then
    echo "  📦 Exporting gcloud config..."
    gcloud config list > "$MIGRATION_DIR/gcloud_config/gcloud_config.txt" 2>&1 || true
    gcloud auth list > "$MIGRATION_DIR/gcloud_config/gcloud_auth_list.txt" 2>&1 || true
    gcloud projects list > "$MIGRATION_DIR/gcloud_config/gcloud_projects.txt" 2>&1 || true
    echo "    ✅ Google Cloud config exported"
    echo "    ⚠️  NOTE: You'll need to re-authenticate on new Mac"
else
    echo "    ⚠️  gcloud not found"
fi

# STEP 5: Export Project Requirements
echo -e "\n${GREEN}STEP 5: Exporting Project Requirements...${NC}"

CBI_PROJECT="/Users/zincdigital/CBI-V14"
if [ -d "$CBI_PROJECT" ]; then
    echo "  📦 Copying project requirements..."
    for req_file in "$CBI_PROJECT"/forecast/requirements.txt \
                    "$CBI_PROJECT"/scripts/requirements.txt \
                    "$CBI_PROJECT"/ingestion/requirements.txt; do
        if [ -f "$req_file" ]; then
            cp "$req_file" "$MIGRATION_DIR/python_envs/$(basename $(dirname $req_file))_requirements.txt"
        fi
    done
    echo "    ✅ Project requirements exported"
fi

# STEP 6: Create Migration Manifest
echo -e "\n${GREEN}STEP 6: Creating Migration Manifest...${NC}"

cat > "$MIGRATION_DIR/MIGRATION_MANIFEST.txt" << EOF
CBI-V14 Mac Migration Package
=============================
Created: $(date)
Source Machine: $(hostname)
Source User: $(whoami)

REPOSITORIES EXPORTED:
- CBI-V14: https://github.com/zincdigitalofmiami/CBI-V14
- Crystal-Ball-V12: https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git
- summit-marine-development: https://github.com/zincdigitalofmiami/summit-marine-development

PYTHON ENVIRONMENTS:
$(if command_exists pyenv; then pyenv versions 2>&1 | sed 's/^/  /'; else echo "  pyenv not found"; fi)

GOOGLE CLOUD:
$(if command_exists gcloud; then gcloud config list 2>&1 | sed 's/^/  /'; else echo "  gcloud not found"; fi)

CURSOR SETTINGS:
- Location: ~/.cursor/
$(if [ -f "$HOME/.cursor/mcp.json" ]; then echo "  - MCP Servers configured"; fi)

NEXT STEPS ON NEW MAC:
1. Extract this migration package
2. Run setup_on_new_mac.sh (if provided)
3. Or follow MAC_MIGRATION_GUIDE.md step-by-step
4. Re-authenticate Google Cloud: gcloud auth login && gcloud auth application-default login
5. Re-authenticate GitHub (if using SSH, generate new key)
6. Verify all connections work

SECURITY NOTES:
- DO NOT copy application_default_credentials.json directly
- DO NOT hardcode API keys - use Google Secret Manager
- Re-authenticate all credentials on new machine
- Keep this package secure during transfer

PACKAGE CONTENTS:
$(find "$MIGRATION_DIR" -type f | sed 's|'"$MIGRATION_DIR"'/|  |' | sort)
EOF

echo "    ✅ Migration manifest created"

# STEP 7: Create Setup Script for New Mac
echo -e "\n${GREEN}STEP 7: Creating Setup Script for New Mac...${NC}"

cat > "$MIGRATION_DIR/setup_on_new_mac.sh" << 'SETUP_SCRIPT'
#!/bin/bash

# Setup script for new Mac Mini
# Run this after extracting the migration package

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 CBI-V14 Setup Script for New Mac${NC}"
echo "=================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install pyenv
if ! command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}Installing pyenv...${NC}"
    brew install pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
    source ~/.zshrc
fi

# Install Google Cloud SDK
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Installing Google Cloud SDK...${NC}"
    brew install --cask google-cloud-sdk
fi

# Install Python versions
echo -e "${YELLOW}Installing Python versions...${NC}"
if [ -f python_envs/pyenv_versions.txt ]; then
    pyenv install 3.10.12 || true
    pyenv install 3.12.6 || true
    pyenv virtualenv 3.10.12 vertex-metal-310 || true
fi

# Restore Git repositories
echo -e "${YELLOW}Restoring Git repositories...${NC}"
mkdir -p ~/Projects
cd ~/Projects

if [ -f "$OLDPWD/git_repos/CBI-V14.bundle" ]; then
    git clone "$OLDPWD/git_repos/CBI-V14.bundle" CBI-V14
    cd CBI-V14
    git remote set-url origin https://github.com/zincdigitalofmiami/CBI-V14.git
    cd ..
fi

if [ -f "$OLDPWD/git_repos/Crystal-Ball-V12.bundle" ]; then
    git clone "$OLDPWD/git_repos/Crystal-Ball-V12.bundle" Crystal-Ball-V12
    cd Crystal-Ball-V12
    git remote set-url origin https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git
    cd ..
fi

if [ -f "$OLDPWD/git_repos/summit-marine-development.bundle" ]; then
    git clone "$OLDPWD/git_repos/summit-marine-development.bundle" summit-marine-development
    cd summit-marine-development
    git remote set-url origin https://github.com/zincdigitalofmiami/summit-marine-development.git
    cd ..
fi

# Restore Cursor settings
echo -e "${YELLOW}Restoring Cursor settings...${NC}"
if [ -d cursor_settings ]; then
    mv ~/.cursor ~/.cursor.backup 2>/dev/null || true
    cp -r cursor_settings ~/.cursor
fi

# Install Python packages
echo -e "${YELLOW}Installing Python packages...${NC}"
if [ -f python_envs/requirements_python3126.txt ]; then
    pyenv global 3.12.6
    pip3 install -r python_envs/requirements_python3126.txt
fi

if [ -f python_envs/requirements_python31012.txt ]; then
    pyenv global 3.10.12
    pip3 install -r python_envs/requirements_python31012.txt
fi

# Setup Google Cloud
echo -e "${YELLOW}Setting up Google Cloud...${NC}"
echo "You'll need to authenticate manually:"
echo "  gcloud auth login zinc@zincdigital.co"
echo "  gcloud config set project cbi-v14"
echo "  gcloud auth application-default login"

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo "Next steps:"
echo "1. Authenticate Google Cloud (see commands above)"
echo "2. Open Cursor and verify settings"
echo "3. Test BigQuery connection"
SETUP_SCRIPT

chmod +x "$MIGRATION_DIR/setup_on_new_mac.sh"
echo "    ✅ Setup script created"

# STEP 8: Create compressed archive
echo -e "\n${GREEN}STEP 8: Creating compressed archive...${NC}"
cd "$HOME"
ARCHIVE_NAME="migration_package_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" migration_package/
echo "    ✅ Archive created: $ARCHIVE_NAME"
echo "    📦 Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"

# Final Summary
echo -e "\n${GREEN}✅ Migration Package Created Successfully!${NC}"
echo "================================"
echo ""
echo "Package Location: $HOME/$ARCHIVE_NAME"
echo "Package Size: $(du -h "$HOME/$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "Next Steps:"
echo "1. Transfer $ARCHIVE_NAME to your new Mac Mini"
echo "2. Extract: tar -xzf $ARCHIVE_NAME"
echo "3. Follow MAC_MIGRATION_GUIDE.md or run setup_on_new_mac.sh"
echo ""
echo "Transfer Methods:"
echo "  - USB Drive (recommended)"
echo "  - AirDrop (if nearby)"
echo "  - Cloud Storage (Google Drive, Dropbox)"
echo "  - Network Transfer (same network)"
echo ""



