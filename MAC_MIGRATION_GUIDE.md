# Complete Mac Migration Guide - CBI-V14 Setup

This guide will help you migrate all your work, connections, and settings from your current Mac to your new Mac Mini.

## 📋 Pre-Migration Checklist

### 1. **Git Repositories** ✅
Your repositories are located at:
- `/Users/zincdigital/CBI-V14` → `https://github.com/zincdigitalofmiami/CBI-V14`
- `/Users/zincdigital/Crystal-Ball-V12` → `https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git`
- `/Users/zincdigital/Projects/summit-marine-development` → `https://github.com/zincdigitalofmiami/summit-marine-development`
- `/Users/zincdigital/PycharmProjects/CBI-V14` (duplicate - can skip)

### 2. **Cursor Settings** ✅
Location: `~/.cursor/`
- Contains: extensions, MCP config, IDE state, CLI config

### 3. **Google Cloud Credentials** ✅
Location: `~/.config/gcloud/`
- Project: `cbi-v14`
- Account: `zinc@zincdigital.co`
- Region: `us-central1`
- **CRITICAL**: Application Default Credentials at `~/.config/gcloud/application_default_credentials.json`

### 4. **Python Environment** ✅
- pyenv versions: `3.10.12`, `3.12.6`, `vertex-metal-310`
- Current Python: `3.12.8`
- Key packages: google-cloud-bigquery, tensorflow, pandas, etc.

### 5. **API Keys & Secrets** ⚠️
- Scrape Creators API: `B1TOgQvMVSV6TDglqB8lJ2cirqi2` (stored in memory)
- Google Secret Manager: `forecasting-data-keys` (JSON secret)
- **DO NOT** copy these - they should be re-authenticated on new machine

---

## 🚀 Migration Methods

### **Method 1: Automated Script (Recommended)**

Run the migration script on your OLD Mac to create a migration package:

```bash
cd /Users/zincdigital/CBI-V14
chmod +x migrate_to_new_mac.sh
./migrate_to_new_mac.sh
```

This will create a `migration_package/` directory with everything needed.

### **Method 2: Manual Step-by-Step**

Follow the sections below for manual migration.

---

## 📦 Step-by-Step Migration

### **STEP 1: On OLD Mac - Prepare Migration Package**

#### A. Export Git Repositories
```bash
# Create migration directory
mkdir -p ~/migration_package/git_repos

# Export CBI-V14 (current project)
cd /Users/zincdigital/CBI-V14
git bundle create ~/migration_package/git_repos/CBI-V14.bundle --all

# Export Crystal-Ball-V12
cd /Users/zincdigital/Crystal-Ball-V12
git bundle create ~/migration_package/git_repos/Crystal-Ball-V12.bundle --all

# Export summit-marine-development
cd /Users/zincdigital/Projects/summit-marine-development
git bundle create ~/migration_package/git_repos/summit-marine-development.bundle --all
```

#### B. Export Cursor Settings
```bash
# Copy Cursor configuration
cp -r ~/.cursor ~/migration_package/cursor_settings
```

#### C. Export Python Environment Info
```bash
# Export pyenv versions
pyenv versions > ~/migration_package/python_versions.txt

# Export pip packages for each environment
pyenv global 3.12.6
pip3 freeze > ~/migration_package/requirements_python3126.txt

pyenv global 3.10.12
pip3 freeze > ~/migration_package/requirements_python31012.txt

# Export pyenv virtualenv
pyenv versions --bare > ~/migration_package/pyenv_versions.txt
```

#### D. Export Google Cloud Config (READ-ONLY)
```bash
# Export gcloud config (without sensitive keys)
gcloud config list > ~/migration_package/gcloud_config.txt
gcloud auth list > ~/migration_package/gcloud_auth_list.txt

# NOTE: application_default_credentials.json will need to be re-authenticated
```

#### E. Create Migration Manifest
```bash
cat > ~/migration_package/MIGRATION_MANIFEST.txt << EOF
Migration Package Created: $(date)
Source Machine: $(hostname)
Source User: $(whoami)

REPOSITORIES:
- CBI-V14: https://github.com/zincdigitalofmiami/CBI-V14
- Crystal-Ball-V12: https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git
- summit-marine-development: https://github.com/zincdigitalofmiami/summit-marine-development

PYTHON ENVIRONMENTS:
- pyenv 3.10.12 (with vertex-metal-310 virtualenv)
- pyenv 3.12.6
- Current: 3.12.8

GOOGLE CLOUD:
- Project: cbi-v14
- Account: zinc@zincdigital.co
- Region: us-central1

CURSOR SETTINGS:
- Location: ~/.cursor/
- MCP Servers: dart, jetbrains

NEXT STEPS:
1. Transfer migration_package/ to new Mac (USB drive, cloud, or network)
2. Run setup_on_new_mac.sh on new Mac
3. Re-authenticate Google Cloud credentials
4. Re-authenticate API keys in Google Secret Manager
EOF
```

#### F. Compress Migration Package
```bash
cd ~
tar -czf migration_package_$(date +%Y%m%d).tar.gz migration_package/
```

---

### **STEP 2: Transfer to New Mac**

Transfer the `migration_package_YYYYMMDD.tar.gz` file to your new Mac Mini using:
- **USB Drive** (recommended for large files)
- **AirDrop** (if both Macs are nearby)
- **Cloud Storage** (Google Drive, Dropbox, etc.)
- **Network Transfer** (if both on same network)

---

### **STEP 3: On NEW Mac - Setup**

#### A. Extract Migration Package
```bash
cd ~
tar -xzf migration_package_YYYYMMDD.tar.gz
cd migration_package
```

#### B. Install Prerequisites
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install pyenv
brew install pyenv

# Install Google Cloud SDK
brew install --cask google-cloud-sdk

# Install Cursor (download from cursor.sh)
# Then open Cursor once to initialize ~/.cursor directory
```

#### C. Restore Git Repositories
```bash
# Clone from bundles
mkdir -p ~/Projects
cd ~/Projects

# CBI-V14
git clone ~/migration_package/git_repos/CBI-V14.bundle CBI-V14
cd CBI-V14
git remote set-url origin https://github.com/zincdigitalofmiami/CBI-V14.git

# Crystal-Ball-V12
cd ~/Projects
git clone ~/migration_package/git_repos/Crystal-Ball-V12.bundle Crystal-Ball-V12
cd Crystal-Ball-V12
git remote set-url origin https://github.com/zincdigitalofmiami/Crystal-Ball-V12.git

# summit-marine-development
cd ~/Projects
git clone ~/migration_package/git_repos/summit-marine-development.bundle summit-marine-development
cd summit-marine-development
git remote set-url origin https://github.com/zincdigitalofmiami/summit-marine-development.git
```

#### D. Restore Python Environments
```bash
# Setup pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python versions
pyenv install 3.10.12
pyenv install 3.12.6

# Create virtualenv
pyenv virtualenv 3.10.12 vertex-metal-310

# Install packages
pyenv global 3.12.6
pip3 install -r ~/migration_package/requirements_python3126.txt

pyenv global 3.10.12
pip3 install -r ~/migration_package/requirements_python31012.txt
```

#### E. Restore Cursor Settings
```bash
# Backup existing Cursor settings (if any)
mv ~/.cursor ~/.cursor.backup 2>/dev/null || true

# Restore from migration package
cp -r ~/migration_package/cursor_settings ~/.cursor
```

#### F. Setup Google Cloud
```bash
# Authenticate
gcloud auth login zinc@zincdigital.co

# Set project
gcloud config set project cbi-v14

# Set region
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# Setup Application Default Credentials
gcloud auth application-default login

# Verify
gcloud config list
gcloud auth list
```

#### G. Setup Project Dependencies
```bash
# Navigate to CBI-V14
cd ~/Projects/CBI-V14

# Install project requirements
pip3 install -r forecast/requirements.txt
pip3 install -r scripts/requirements.txt
pip3 install -r ingestion/requirements.txt

# For M2 Max MacBook Pro with TensorFlow Metal GPU acceleration
pip3 install tensorflow tensorflow-metal
```

#### H. Verify Setup
```bash
# Test Python
python3 --version
pyenv versions

# Test Google Cloud
gcloud config list
gcloud auth list

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; print('BigQuery OK')"

# Test Git
cd ~/Projects/CBI-V14
git status
git remote -v
```

---

## 🔐 Security & Authentication

### **Items That Need Re-Authentication:**

1. **Google Cloud Application Default Credentials**
   ```bash
   gcloud auth application-default login
   ```

2. **Google Secret Manager** (if using)
   - Access via: `gcloud secrets versions access latest --secret="forecasting-data-keys"`
   - Or re-download from Google Cloud Console

3. **GitHub Authentication**
   - If using SSH: Generate new SSH key and add to GitHub
   - If using HTTPS: May need to re-enter credentials or use Personal Access Token

4. **API Keys**
   - Scrape Creators API: `B1TOgQvMVSV6TDglqB8lJ2cirqi2`
   - Store in Google Secret Manager or environment variables

---

## ✅ Post-Migration Verification

Run these checks on your new Mac:

```bash
# 1. Git repositories
cd ~/Projects/CBI-V14 && git status
cd ~/Projects/Crystal-Ball-V12 && git status

# 2. Python
python3 --version
pyenv versions

# 3. Google Cloud
gcloud config list
gcloud auth list

# 4. BigQuery connection
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')
print('BigQuery connection successful!')
print(f'Project: {client.project}')
"

# 5. Cursor
# Open Cursor and verify:
# - Extensions are installed
# - MCP servers configured
# - Settings match old machine
```

---

## 🆘 Troubleshooting

### Issue: Python packages missing
```bash
# Reinstall from requirements files
pip3 install -r ~/migration_package/requirements_python3126.txt
```

### Issue: Google Cloud authentication fails
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login
```

### Issue: Cursor extensions not working
```bash
# Reinstall extensions manually in Cursor
# Or check ~/.cursor/extensions/ directory
```

### Issue: Git remote authentication fails
```bash
# Update remote URLs
git remote set-url origin https://github.com/zincdigitalofmiami/REPO_NAME.git
# Or setup SSH keys
```

---

## 📝 Notes

- **DO NOT** copy `application_default_credentials.json` directly - it's machine-specific
- **DO NOT** hardcode API keys in files - use Google Secret Manager
- **DO** verify all connections work before deleting old machine data
- **DO** keep migration package as backup for 30 days

---

## 🎯 Quick Reference

**Old Mac Locations:**
- Projects: `/Users/zincdigital/CBI-V14`, `/Users/zincdigital/Crystal-Ball-V12`
- Cursor: `~/.cursor/`
- Python: `~/.pyenv/`
- GCloud: `~/.config/gcloud/`

**New Mac Locations:**
- Projects: `~/Projects/CBI-V14`, `~/Projects/Crystal-Ball-V12`
- Cursor: `~/.cursor/`
- Python: `~/.pyenv/`
- GCloud: `~/.config/gcloud/`

---

**Migration Date:** $(date)
**Created By:** Auto-generated migration guide



