---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Organization Quick Reference
**Universal active/old/new System**  
**Last Updated:** November 5, 2025

---

## 🎯 PHILOSOPHY

**Everything** uses the `active/old/new/` structure:
- `active/` = Currently working on
- `old/` = Completed/archived
- `new/` = Recently created, needs categorization

---

## 📁 ROOT DIRECTORY (4 Files Only!)

```
✅ CBI_V14_COMPLETE_EXECUTION_PLAN.md     Main execution plan
✅ HANDOFF_NOV5_END_OF_DAY.md             Latest project status
✅ HANDOFF_VEGAS_GLIDE_INTEGRATION_NOV5.md Vegas integration status
✅ README.md                              Project documentation
```

Plus: `.gitignore`, `cloudbuild.yaml`, `cron_audit_report.py`

---

## 🗂️ ORGANIZATION SYSTEM

### **system/** - System Config & Build
```
system/
├── config/   Makefile, cloudbuild.yaml, .pre-commit-config.yaml
├── docs/     LICENSE, CONTRIBUTING.md
└── scripts/  Reorganization scripts
```

### **audits/** - All Audits
```
audits/
├── active/   Currently running audits
├── old/      Completed audits (4 files)
└── new/      Recently created
```

###**plans/** - All Plans
```
plans/
├── active/   Current plans + symlink to main plan
├── old/      Completed plans (2 files)
└── new/      Proposed plans
```

### **documentation/** - All Documentation
```
documentation/
├── active/
│   ├── api-references/  (VEGAS_GLIDE_API_REFERENCE.md)
│   ├── guides/          (How-to guides)
│   └── system-docs/     (4 files: setup, organization docs)
├── old/                 (Outdated docs)
└── new/                 (Recently added)
```

### **code-reviews/** - All Code Reviews
```
code-reviews/
├── active/   Ongoing reviews
├── old/      Completed reviews (3 files)
└── new/      Pending review
```

### **deployment/** - All Deployment Docs
```
deployment/
├── active/   Current deployments
├── old/      Historical deployments (5 files)
└── new/      Pending deployments
```

### **data/** - All Data Files
```
data/
├── active/
│   └── social-media/  (7 platforms: facebook, twitter, etc.)
├── old/               (Archived data)
└── new/               (Recently ingested)
```

### **models/** - All Models
```
models/
├── active/  Current models (from models_v4)
├── old/     Retired models
└── new/     Experimental models
```

---

## 🔤 NAMING CONVENTIONS

### Folders: `kebab-case`
```
✅ bigquery-sql/
✅ ingestion/
✅ dashboard-nextjs/
✅ vertex-ai/
✅ terraform/
```

### Files: Descriptive with keywords
```
✅ MODEL_PERFORMANCE_AUDIT_NOV2025.md
✅ FEATURE_X_IMPLEMENTATION_PLAN.md
✅ API_INTEGRATION_GUIDE.md
```

---

## 📊 WORKFLOW

### Creating New Audit:
```bash
1. Create: audits/new/MY_AUDIT.md
2. Working: mv audits/new/MY_AUDIT.md audits/active/
3. Complete: mv audits/active/MY_AUDIT.md audits/old/
```

### Creating New Plan:
```bash
1. Create: plans/new/MY_PLAN.md
2. Approved: mv plans/new/MY_PLAN.md plans/active/
3. Complete: mv plans/active/MY_PLAN.md plans/old/
```

### Creating New Documentation:
```bash
1. Create: documentation/new/MY_DOC.md
2. Categorize: mv documentation/new/MY_DOC.md documentation/active/[type]/
3. Outdated: mv documentation/active/[type]/MY_DOC.md documentation/old/
```

**Same pattern for:** code-reviews, deployment, data, models

---

## 🚀 KEY LOCATIONS

**System Configuration:**
- Makefile: `system/config/Makefile`
- LICENSE: `system/docs/LICENSE`
- CONTRIBUTING: `system/docs/CONTRIBUTING.md`

**Main Plan:**
- Root: `CBI_V14_COMPLETE_EXECUTION_PLAN.md`
- Symlink: `plans/active/CBI_V14_COMPLETE_EXECUTION_PLAN.md`

**API References:**
- `documentation/active/api-references/`

**Active Models:**
- `models/active/`

**Social Media Data:**
- `data/active/social-media/`

**System Scripts:**
- Reorganization: `system/scripts/`
- Project scripts: `scripts/`

---

## 💡 QUICK TIPS

1. **Root stays clean** - Only 4 MD files allowed
2. **New → Active → Old** - Follow this flow
3. **Use active/old/new** - For everything
4. **kebab-case** - For all folder names
5. **Descriptive names** - Include type in filename

---

## 📋 FOLDER COUNT

```
Total top-level folders: 19
  
Organization folders (8):
  ✅ system/          (config & docs)
  ✅ audits/          (active/old/new)
  ✅ plans/           (active/old/new)
  ✅ documentation/   (active/old/new)
  ✅ code-reviews/    (active/old/new)
  ✅ deployment/      (active/old/new)
  ✅ data/            (active/old/new)
  ✅ models/          (active/old/new)

Code folders (9):
  ✅ bigquery-sql/
  ✅ ingestion/
  ✅ dashboard-nextjs/
  ✅ forecast/
  ✅ scripts/
  ✅ src/
  ✅ terraform/
  ✅ vertex-ai/
  ✅ logs/

Archive (1):
  ✅ archive/

Hidden (1):
  ✅ .venv/
```

---

## ✅ BENEFITS

**Before:** Cluttered root, inconsistent naming, no organization
**After:** 4-file root, universal structure, production-grade

---

**Quick Reference Created:** November 5, 2025  
**Organization System:** active/old/new for everything  
**Root Files:** 4 markdown files only

