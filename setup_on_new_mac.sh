#!/bin/bash

# Setup script for new Mac Mini
# Run this after extracting the migration package on your NEW Mac

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🚀 CBI-V14 Setup Script for New Mac Mini${NC}"
echo "=============================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATION_DIR="$SCRIPT_DIR"

# Check if we're in a migration package directory
if [ ! -d "$MIGRATION_DIR/git_repos" ]; then
    echo -e "${RED}❌ Error: Migration package not found${NC}"
    echo "Please extract the migration package and run this script from that directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# STEP 1: Install Prerequisites
echo -e "${BLUE}STEP 1: Installing Prerequisites...${NC}"

# Check if Homebrew is installed
if ! command_exists brew; then
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "  ✅ Homebrew already installed"
fi

# Install pyenv
if ! command_exists pyenv; then
    echo -e "${YELLOW}Installing pyenv...${NC}"
    brew install pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    echo "  ✅ pyenv installed"
else
    echo "  ✅ pyenv already installed"
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

# Install Google Cloud SDK
if ! command_exists gcloud; then
    echo -e "${YELLOW}Installing Google Cloud SDK...${NC}"
    brew install --cask google-cloud-sdk
    echo "  ✅ Google Cloud SDK installed"
    echo "  ⚠️  You may need to restart your terminal or run: source ~/.zshrc"
else
    echo "  ✅ Google Cloud SDK already installed"
fi

# STEP 2: Install Python Versions
echo -e "\n${BLUE}STEP 2: Installing Python Versions...${NC}"

if [ -f "$MIGRATION_DIR/python_envs/pyenv_versions.txt" ]; then
    echo "  📦 Installing Python 3.10.12..."
    pyenv install 3.10.12 || echo "  ⚠️  Python 3.10.12 may already be installed"
    
    echo "  📦 Installing Python 3.12.6..."
    pyenv install 3.12.6 || echo "  ⚠️  Python 3.12.6 may already be installed"
    
    echo "  📦 Creating vertex-metal-310 virtualenv..."
    pyenv virtualenv 3.10.12 vertex-metal-310 || echo "  ⚠️  virtualenv may already exist"
    
    echo "  ✅ Python versions installed"
else
    echo "  ⚠️  Python versions file not found, skipping"
fi

# STEP 3: Restore Git Repositories
echo -e "\n${BLUE}STEP 3: Restoring Git Repositories...${NC}"

mkdir -p ~/Projects
cd ~/Projects

if [ -f "$MIGRATION_DIR/git_repos/CBI-V14.bundle" ]; then
    echo "  📦 Cloning CBI-V14..."
    if [ -d "CBI-V14" ]; then
        echo "    ⚠️  CBI-V14 already exists, skipping"
    else
        git clone "$MIGRATION_DIR/git_repos/CBI-V14.bundle" CBI-V14
        cd CBI-V14
        git remote set-url origin https://github.com/zincdigitalofmiami/CBI-V14.git
        cd ~/Projects
        echo "    ✅ CBI-V14 restored"
    fi
fi

if [ -f "$MIGRATION_DIR/git_repos/Crystal-Ball-V12.bundle" ]; then
    echo "  📦 Cloning Crystal-Ball-V12..."
    if [ -d "Crystal-Ball-V12" ]; then
        echo "    ⚠️  Crystal-Ball-V12 already exists, skipping"
    else
        git clone "$MIGRATION_DIR/git_repos/Crystal-Ball-V12.bundle" Crystal-Ball-V12
        cd Crystal-Ball-V12
        git remote set-url origin https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git
        cd ~/Projects
        echo "    ✅ Crystal-Ball-V12 restored"
    fi
fi

if [ -f "$MIGRATION_DIR/git_repos/summit-marine-development.bundle" ]; then
    echo "  📦 Cloning summit-marine-development..."
    if [ -d "summit-marine-development" ]; then
        echo "    ⚠️  summit-marine-development already exists, skipping"
    else
        git clone "$MIGRATION_DIR/git_repos/summit-marine-development.bundle" summit-marine-development
        cd summit-marine-development
        git remote set-url origin https://github.com/zincdigitalofmiami/summit-marine-development.git
        cd ~/Projects
        echo "    ✅ summit-marine-development restored"
    fi
fi

# STEP 4: Restore Cursor Settings
echo -e "\n${BLUE}STEP 4: Restoring Cursor Settings...${NC}"

if [ -d "$MIGRATION_DIR/cursor_settings" ]; then
    if [ -d "$HOME/.cursor" ]; then
        echo "  📦 Backing up existing Cursor settings..."
        mv "$HOME/.cursor" "$HOME/.cursor.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    echo "  📦 Restoring Cursor settings..."
    cp -r "$MIGRATION_DIR/cursor_settings" "$HOME/.cursor"
    echo "  ✅ Cursor settings restored"
    echo "  ⚠️  You may need to restart Cursor for changes to take effect"
else
    echo "  ⚠️  Cursor settings not found in migration package"
fi

# STEP 5: Install Python Packages
echo -e "\n${BLUE}STEP 5: Installing Python Packages...${NC}"

if [ -f "$MIGRATION_DIR/python_envs/requirements_python3126.txt" ]; then
    echo "  📦 Installing packages for Python 3.12.6..."
    pyenv global 3.12.6
    pip3 install --upgrade pip
    pip3 install -r "$MIGRATION_DIR/python_envs/requirements_python3126.txt" || echo "  ⚠️  Some packages may have failed to install"
fi

if [ -f "$MIGRATION_DIR/python_envs/requirements_python31012.txt" ]; then
    echo "  📦 Installing packages for Python 3.10.12..."
    pyenv global 3.10.12
    pip3 install --upgrade pip
    pip3 install -r "$MIGRATION_DIR/python_envs/requirements_python31012.txt" || echo "  ⚠️  Some packages may have failed to install"
fi

# Install TensorFlow Metal for M-series Macs
if [[ $(uname -m) == "arm64" ]]; then
    echo "  📦 Installing TensorFlow Metal for Apple Silicon..."
    pyenv global 3.10.12
    pip3 install tensorflow tensorflow-metal || echo "  ⚠️  TensorFlow Metal installation may have issues"
fi

# Install project-specific requirements
if [ -d "$HOME/Projects/CBI-V14" ]; then
    echo "  📦 Installing CBI-V14 project requirements..."
    cd "$HOME/Projects/CBI-V14"
    
    if [ -f "forecast/requirements.txt" ]; then
        pip3 install -r forecast/requirements.txt || true
    fi
    if [ -f "scripts/requirements.txt" ]; then
        pip3 install -r scripts/requirements.txt || true
    fi
    if [ -f "ingestion/requirements.txt" ]; then
        pip3 install -r ingestion/requirements.txt || true
    fi
fi

# STEP 6: Setup Google Cloud (Manual Steps)
echo -e "\n${BLUE}STEP 6: Google Cloud Setup (Manual Required)${NC}"
echo ""
echo -e "${YELLOW}You need to manually authenticate Google Cloud:${NC}"
echo ""
echo "Run these commands:"
echo "  gcloud auth login zinc@zincdigital.co"
echo "  gcloud config set project cbi-v14"
echo "  gcloud config set compute/region us-central1"
echo "  gcloud config set compute/zone us-central1-a"
echo "  gcloud auth application-default login"
echo ""
echo "Then verify with:"
echo "  gcloud config list"
echo "  gcloud auth list"
echo ""

# Final Summary
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next Steps:"
echo "1. ✅ Authenticate Google Cloud (see commands above)"
echo "2. ✅ Open Cursor and verify settings/extensions"
echo "3. ✅ Test BigQuery connection:"
echo "   cd ~/Projects/CBI-V14"
echo "   python3 -c \"from google.cloud import bigquery; print('BigQuery OK')\""
echo "4. ✅ Verify Git repositories:"
echo "   cd ~/Projects/CBI-V14 && git status"
echo ""
echo "If you encounter issues, check MAC_MIGRATION_GUIDE.md for troubleshooting"
echo ""



