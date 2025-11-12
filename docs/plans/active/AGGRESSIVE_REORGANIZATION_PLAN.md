# CBI-V14 Aggressive Reorganization Plan
**Complete Project Restructure with Active/Old/New System**  
**Date:** November 5, 2025

---

## 🎯 NEW ORGANIZATION PHILOSOPHY

### **Universal Structure: active/ | old/ | new/**
Every category gets three subfolders:
- `active/` - Currently working on
- `old/` - Completed/archived  
- `new/` - Recently added, needs review/categorization

---

## 📁 PROPOSED ROOT STRUCTURE

```
/Users/zincdigital/CBI-V14/
│
├── README.md                          [KEEP - GitHub requires it]
├── .gitignore                         [KEEP - Git requires it]
├── CBI_V14_COMPLETE_EXECUTION_PLAN.md [KEEP - Main plan always visible]
├── HANDOFF_NOV5_END_OF_DAY.md         [KEEP - Latest status]
│
├── system/                            [NEW] System config & build files
│   ├── config/
│   │   ├── .pre-commit-config.yaml
│   │   ├── cloudbuild.yaml
│   │   ├── Makefile
│   │   └── deploy configs...
│   ├── docs/
│   │   ├── CONTRIBUTING.md
│   │   ├── LICENSE
│   │   └── setup guides...
│   └── scripts/
│       └── system maintenance scripts...
│
├── audits/                            [NEW] All audits organized
│   ├── active/                        Currently running audits
│   ├── old/                           Completed audits
│   └── new/                           Recently created, needs review
│
├── plans/                             [NEW] All plans organized
│   ├── active/                        Current execution plans
│   ├── old/                           Completed plans
│   └── new/                           Proposed plans
│
├── documentation/                     [NEW] All docs organized
│   ├── active/                        Current/living docs
│   │   ├── api-references/
│   │   ├── guides/
│   │   └── system-docs/
│   ├── old/                           Historical documentation
│   └── new/                           Recently added docs
│
├── code-reviews/                      [NEW] All reviews organized
│   ├── active/                        Ongoing reviews
│   ├── old/                           Completed reviews
│   └── new/                           Pending review
│
├── deployment/                        [NEW] All deployment docs
│   ├── active/                        Current deployment configs
│   ├── old/                           Historical deployments
│   └── new/                           Pending deployments
│
├── data/                              [RESTRUCTURE]
│   ├── active/                        Current data files
│   ├── old/                           Archived data
│   └── new/                           Recently ingested
│
├── logs/                              [RESTRUCTURE]
│   ├── active/                        Recent logs (last 7 days)
│   ├── old/                           Archived logs
│   └── error-logs/                    Error tracking
│
├── src/                               [CODE - Keep as-is]
├── scripts/                           [CODE - Keep as-is]
├── models/                            [RENAMED from models_v4]
│   ├── active/                        Currently training/deployed
│   ├── old/                           Retired models
│   └── new/                           Experimental models
│
├── ingestion/                         [RENAMED from cbi-v14-ingestion]
├── bigquery-sql/                      [RENAMED from bigquery_sql]
├── dashboard-nextjs/                  [Keep as-is]
├── forecast/                          [Keep as-is]
├── terraform/                         [RENAMED from terraform-deploy]
├── vertex-ai/                         [RENAMED from automl]
│
└── archive/                           [KEEP - Ultimate old storage]
    ├── 2024/
    ├── 2025-q1/
    ├── 2025-q2/
    ├── 2025-q3/
    └── legacy/
```

---

## 🗂️ CATEGORY BREAKDOWN

### **1. SYSTEM FILES** → `system/`

**What:** Configuration, build files, contributor docs

**Structure:**
```
system/
├── config/
│   ├── .pre-commit-config.yaml (moved from root)
│   ├── cloudbuild.yaml (moved from root)
│   ├── Makefile (moved from root)
│   ├── terraform.tfvars
│   └── deployment configs
│
├── docs/
│   ├── CONTRIBUTING.md (moved from root)
│   ├── LICENSE (moved from root)
│   ├── setup guides
│   └── system documentation
│
└── scripts/
    ├── setup scripts
    ├── maintenance scripts
    └── system utilities
```

**Why:** Cleanest root possible, all system files in one place

---

### **2. AUDITS** → `audits/active|old|new/`

**Structure:**
```
audits/
├── active/
│   └── (currently running audits - modified in last 30 days)
│
├── old/
│   ├── 2024/
│   ├── 2025-q1/
│   ├── 2025-q2/
│   └── 2025-q3/
│
└── new/
    └── (recently created, pending categorization)
```

**Auto-categorization rules:**
- Modified < 30 days → `active/`
- Modified > 30 days → `old/YYYY-QX/`
- Just created → `new/` (then manual move)

---

### **3. PLANS** → `plans/active|old|new/`

**Structure:**
```
plans/
├── active/
│   ├── CBI_V14_COMPLETE_EXECUTION_PLAN.md (symlink to root)
│   ├── PHASE_XX_ACTIVE_PLAN.md
│   └── current execution plans
│
├── old/
│   ├── 2024/
│   ├── 2025-q1/
│   ├── 2025-q2/
│   └── 2025-q3/
│       ├── PHASE_02_EXECUTION_GUIDE.md
│       └── PHASE_02_IMPLEMENTATION_COMPLETE.md
│
└── new/
    └── (proposed plans pending approval)
```

---

### **4. DOCUMENTATION** → `documentation/active|old|new/`

**Structure:**
```
documentation/
├── active/
│   ├── api-references/
│   │   └── VEGAS_GLIDE_API_REFERENCE.md
│   ├── guides/
│   │   └── integration guides
│   ├── system-docs/
│   │   ├── AI_METADATA_SYSTEM_README.md
│   │   ├── ASSET_CLASSIFICATION_SYSTEM.md
│   │   └── VERTEX_AI_INTEGRATION.md
│   └── README.md (index of all docs)
│
├── old/
│   └── (outdated documentation)
│
└── new/
    └── (recently written, needs review)
```

---

### **5. CODE REVIEWS** → `code-reviews/active|old|new/`

**Structure:**
```
code-reviews/
├── active/
│   └── (ongoing reviews)
│
├── old/
│   ├── ENHANCED_CALCULATOR_REVIEW.md
│   ├── EVENT_PREDICTIONS_CODE_REVIEW.md
│   └── CALCULATOR_DRY_TEST.md
│
└── new/
    └── (pending review)
```

---

### **6. DEPLOYMENT** → `deployment/active|old|new/`

**Structure:**
```
deployment/
├── active/
│   ├── current-deployment-status.md
│   └── active configs
│
├── old/
│   ├── DEPLOY_CONSOLE_NOW.md
│   ├── DEPLOYMENT_BLOCKED_SUMMARY.md
│   └── historical deployments
│
└── new/
    └── (pending deployments)
```

---

### **7. DATA** → `data/active|old|new/`

**Structure:**
```
data/
├── active/
│   ├── social-media/ (current scrapes)
│   ├── market-data/ (current)
│   └── intelligence/ (current)
│
├── old/
│   ├── 2024/
│   └── 2025/
│       └── csv/ (Oct 3 price data)
│
└── new/
    └── (recently ingested, needs validation)
```

---

### **8. MODELS** → `models/active|old|new/`

**Structure:**
```
models/
├── active/
│   ├── 1w-model/
│   ├── 1m-model/
│   ├── 3m-model/
│   └── 6m-model/
│
├── old/
│   ├── v1/
│   ├── v2/
│   ├── v3/
│   └── deprecated/
│
└── new/
    └── (experimental models)
```

---

## 🚀 EXECUTION PLAN

### **Phase 1: Create New Structure**
```bash
# Create all new directories
mkdir -p system/{config,docs,scripts}
mkdir -p audits/{active,old,new}
mkdir -p plans/{active,old,new}
mkdir -p documentation/{active/{api-references,guides,system-docs},old,new}
mkdir -p code-reviews/{active,old,new}
mkdir -p deployment/{active,old,new}
mkdir -p data/{active,old,new}
mkdir -p models/{active,old,new}
mkdir -p logs/{active,old,error-logs}
```

### **Phase 2: Move System Files**
```bash
# Config files (create copies first, some need to stay in root)
cp .pre-commit-config.yaml system/config/
cp cloudbuild.yaml system/config/
mv Makefile system/config/

# Docs
mv CONTRIBUTING.md system/docs/
mv LICENSE system/docs/

# Note: README.md, .gitignore MUST stay in root
```

### **Phase 3: Organize Audits**
```bash
# Old audits
mv docs/audits/*.md audits/old/

# Active audits (if any)
# (manually move currently running audits to audits/active/)
```

### **Phase 4: Organize Plans**
```bash
# Old plans
mv docs/older-plans/*.md plans/old/

# Active plans stay visible
# Create symlink to main plan
ln -s ../../CBI_V14_COMPLETE_EXECUTION_PLAN.md plans/active/
```

### **Phase 5: Organize Documentation**
```bash
# API references
mv docs/*API*REFERENCE*.md documentation/active/api-references/

# Guides
mv docs/*GUIDE*.md documentation/active/guides/

# System docs
mv docs/*SYSTEM*.md documentation/active/system-docs/
mv docs/*INTEGRATION*.md documentation/active/system-docs/
```

### **Phase 6: Organize Code Reviews**
```bash
mv docs/reference-archive/*REVIEW*.md code-reviews/old/
mv docs/reference-archive/*TEST*.md code-reviews/old/
```

### **Phase 7: Organize Deployment**
```bash
mv archive/deployment-history/*.md deployment/old/
```

### **Phase 8: Organize Data**
```bash
# Move old CSV data
mv data/csv/ data/old/2025/

# Organize current data by type
mv data/facebook/ data/active/social-media/
mv data/twitter/ data/active/social-media/
mv data/truth_social/ data/active/social-media/
# etc...
```

### **Phase 9: Organize Models**
```bash
# Rename and restructure
mv models_v4/ models/
# Categorize models into active/old/new
```

### **Phase 10: Organize Logs**
```bash
# Move recent logs to active
find logs/ -name "*.log" -mtime -7 -exec mv {} logs/active/ \;

# Move old logs
find logs/ -name "*.log" -mtime +7 -exec mv {} logs/old/ \;
```

### **Phase 11: Rename Folders (Standardize)**
```bash
mv bigquery_sql/ bigquery-sql/
mv cbi-v14-ingestion/ ingestion/
mv terraform-deploy/ terraform/
mv automl/ vertex-ai/
```

### **Phase 12: Delete Empty Folders**
```bash
rmdir cache/ cb-ingest/ inmet_csv_data/
```

### **Phase 13: Delete Old docs/ Folder**
```bash
# After everything moved
rm -rf docs/
```

---

## 🔄 UPDATED AUTO-ORGANIZE SCRIPT

Will update `scripts/auto_organize_docs.py` to use new structure:

```python
DESTINATIONS = {
    "audits": "audits/new/",           # Manual → active/old
    "plans": "plans/new/",             # Manual → active/old
    "reviews": "code-reviews/new/",    # Manual → active/old
    "deployment": "deployment/new/",   # Manual → active/old
    "system_docs": "documentation/new/", # Manual → active/old
}
```

All files go to `/new/` first, then manually categorize to `active/` or `old/`

---

## 📋 FINAL ROOT DIRECTORY

**Only 4-5 files in root:**
```
/Users/zincdigital/CBI-V14/
├── README.md                          [Required by GitHub]
├── .gitignore                         [Required by Git]
├── CBI_V14_COMPLETE_EXECUTION_PLAN.md [Main plan - always visible]
├── HANDOFF_NOV5_END_OF_DAY.md         [Latest handoff]
└── (working directories only)
```

**Everything else:** organized in categorized folders with `active/old/new/` structure

---

## ⚡ BENEFITS

### Before:
- Mixed files in root
- Unclear what's active vs old
- Hard to find anything
- No consistent structure

### After:
- Ultra-clean root (4-5 files max)
- Clear active/old/new separation
- Everything categorized
- Universal structure pattern
- Easy to find anything

---

## ⚠️ WARNINGS

**Files that MUST stay in root:**
- `README.md` - GitHub convention
- `.gitignore` - Git requirement
- `.pre-commit-config.yaml` - Pre-commit looks here (can symlink)
- `cloudbuild.yaml` - Cloud Build looks here (can symlink)

**Solution:** Create symlinks in root pointing to `system/config/`

---

## 🎯 READY TO EXECUTE?

This is an AGGRESSIVE reorganization. Recommend:

1. **Full backup first**
2. **Test in dry-run**
3. **Execute in phases**
4. **Update all path references**
5. **Test all scripts after**

**Estimated time:** 2-3 hours  
**Risk level:** HIGH (many path changes)  
**Benefit:** MAXIMUM organization

---

**Status:** PLAN READY - Awaiting approval to execute

