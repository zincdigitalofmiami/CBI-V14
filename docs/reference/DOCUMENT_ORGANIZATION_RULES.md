---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Document Organization Rules
**Automatic Organization System for Markdown Files**  
**Last Updated:** November 5, 2025  
**Status:** ✅ ACTIVE

---

## 🎯 PURPOSE

This document defines the automatic organization rules for all markdown files in the CBI-V14 project. The `auto_organize_docs.py` script uses these rules to keep documentation organized.

---

## 📋 ORGANIZATION CATEGORIES

### 🔒 **PROTECTED - Always Stay in Root**

These files NEVER move automatically:

```
✓ README.md
✓ CONTRIBUTING.md  
✓ LICENSE.md
✓ CBI_V14*PLAN.md
✓ HANDOFF*.md
✓ MASTER*PLAN.md
```

**Rationale:** Critical project files that need immediate visibility

---

### 📊 **AUDITS → `docs/audits/`**

**Naming Patterns:**
- `*AUDIT*.md`
- `*_AUDIT_*.md`
- `*AUDIT_REPORT*.md`
- `*AUDIT_RESULTS*.md`
- `*NULL*AUDIT*.md`
- `*DATA*AUDIT*.md`
- `*COMPREHENSIVE*AUDIT*.md`

**Examples:**
- `MODEL_NAMING_AUDIT.md` → `docs/audits/`
- `NULL_AUDIT_AND_STRATEGY.md` → `docs/audits/`
- `VEGAS_INTEL_AUDIT_REPORT.md` → `docs/audits/`

**Exception:** Files with "ACTIVE" or current year in name stay in root temporarily

---

### 📋 **PLANS → `docs/older-plans/` or ROOT (if active)**

**Naming Patterns:**
- `*PLAN.md`
- `*_PLAN_*.md`
- `*EXECUTION*PLAN*.md`
- `*IMPLEMENTATION*PLAN*.md`
- `*PHASE*PLAN*.md`

**Active Plan Indicators** (stays in ROOT):
- Contains "CURRENT", "ACTIVE", "WORKING", "LIVE", "NOW"
- Modified in last 7 days
- Contains current year
- File content shows "IN PROGRESS" or "ACTIVE"

**Examples:**
- `CBI_V14_COMPLETE_EXECUTION_PLAN.md` → ROOT (protected + active)
- `PHASE_02_EXECUTION_GUIDE.md` → `docs/older-plans/` (completed)
- `IMPLEMENTATION_PLAN_REVIEW.md` → `docs/older-plans/` (completed)

---

### 📝 **CODE REVIEWS → `docs/reference-archive/`**

**Naming Patterns:**
- `*REVIEW.md`
- `*CODE*REVIEW*.md`
- `*_REVIEW_*.md`
- `*DRY*TEST*.md`

**Examples:**
- `ENHANCED_CALCULATOR_REVIEW.md` → `docs/reference-archive/`
- `EVENT_PREDICTIONS_CODE_REVIEW.md` → `docs/reference-archive/`
- `CALCULATOR_DRY_TEST.md` → `docs/reference-archive/`

---

### 🚀 **DEPLOYMENT DOCS → `archive/deployment-history/`**

**Naming Patterns:**
- `*DEPLOY*.md`
- `*DEPLOYMENT*.md`
- `*_DEPLOY_*.md`

**Examples:**
- `DEPLOY_CONSOLE_NOW.md` → `archive/deployment-history/`
- `DEPLOYMENT_BLOCKED_SUMMARY.md` → `archive/deployment-history/`
- `DEPLOYMENT_STATUS.md` → `archive/deployment-history/`

**Exception:** Files marked as "CURRENT" stay in root

---

### 📚 **SYSTEM REFERENCE → `docs/`**

**Naming Patterns:**
- `*README*.md` (except root README.md)
- `*DOCUMENTATION*.md`
- `*REFERENCE*.md`
- `*INTEGRATION*.md`
- `*SYSTEM*.md`
- `*API*REFERENCE*.md`
- `*GUIDE*.md`

**Examples:**
- `AI_METADATA_SYSTEM_README.md` → `docs/`
- `VERTEX_AI_INTEGRATION.md` → `docs/`
- `VEGAS_GLIDE_API_REFERENCE.md` → `docs/`
- `ASSET_CLASSIFICATION_SYSTEM.md` → `docs/`

---

### 📊 **ANALYSIS/REPORTS → `docs/audits/`**

**Naming Patterns:**
- `*ANALYSIS*.md`
- `*REPORT*.md`
- `*SUMMARY*.md`
- `*INVESTIGATION*.md`
- `*ASSESSMENT*.md`

**Examples:**
- `GAP_ANALYSIS_AND_COMPLETION.md` → `docs/older-plans/` (also matches plan pattern)
- `V4_EVALUATION_REPORT.md` → `docs/audits/`
- `FOLDER_ORGANIZATION_REVIEW.md` → `docs/` (reference)

---

### 📅 **STATUS UPDATES → ROOT (if recent) or `docs/`**

**Naming Patterns:**
- `*STATUS*.md`
- `*HANDOFF*.md`
- `*UPDATE*.md`

**Recent = Keep in ROOT** (last 7 days or current date in filename)

**Examples:**
- `HANDOFF_NOV5_END_OF_DAY.md` → ROOT (current)
- `DEPLOYMENT_STATUS.md` → `archive/deployment-history/` (old + deployment)

---

## 🤖 AUTOMATIC ORGANIZATION

### **Usage:**

```bash
# Dry run - see what would be organized
python scripts/auto_organize_docs.py

# Execute - actually move files
python scripts/auto_organize_docs.py --execute
```

### **When It Runs:**

1. **Manual:** Run script anytime via command above
2. **Pre-commit:** (Optional) Add to git pre-commit hook
3. **CI/CD:** GitHub Actions workflow on push
4. **Cron:** Weekly cleanup job

---

## 🔍 ACTIVE DOCUMENT DETECTION

A document is considered "ACTIVE" if:

1. **Filename contains:**
   - CURRENT, ACTIVE, WORKING, LIVE, NOW
   - Current year (2025)
   - V14, MASTER, MAIN

2. **Modified recently:**
   - Modified in last 7 days

3. **Content indicates:**
   - First 500 chars contain "ACTIVE", "CURRENT", "IN PROGRESS", "WORKING"

**Active documents stay in ROOT even if pattern matches archive category**

---

## 📁 FOLDER STRUCTURE

```
/Users/zincdigital/CBI-V14/
│
├── *.md (ACTIVE PLANS, HANDOFFS, README, CONTRIBUTING)
│
├── docs/
│   ├── audits/                    # Completed audit reports
│   ├── older-plans/               # Completed implementation plans
│   ├── reference-archive/         # Code reviews, tests
│   └── *.md                       # System docs, references, guides
│
└── archive/
    └── deployment-history/        # Old deployment docs
```

---

## ✅ NAMING CONVENTIONS

### **For Auto-Organization to Work Best:**

**Audits:**
```
✓ MODEL_NAMING_AUDIT.md
✓ DATA_QUALITY_AUDIT_2025.md
✓ COMPREHENSIVE_FEATURE_AUDIT.md
```

**Plans:**
```
✓ FEATURE_IMPLEMENTATION_PLAN.md
✓ PHASE_03_EXECUTION_PLAN.md
✓ MIGRATION_PLAN_V14.md
```

**Reviews:**
```
✓ API_CODE_REVIEW.md
✓ SECURITY_REVIEW_2025.md
✓ PERFORMANCE_DRY_TEST.md
```

**Deployment:**
```
✓ DEPLOY_DASHBOARD_NOW.md
✓ DEPLOYMENT_CHECKLIST.md
✓ PRODUCTION_DEPLOY_STATUS.md
```

**System Docs:**
```
✓ DATABASE_SCHEMA_REFERENCE.md
✓ API_INTEGRATION_GUIDE.md
✓ FEATURE_REGISTRY_SYSTEM.md
```

---

## 🚨 MANUAL OVERRIDE

If auto-organization moves a file incorrectly:

1. **Add to protected list** in `auto_organize_docs.py`
2. **Rename file** to match intended category
3. **Move manually** and document in this file
4. **Update rules** if pattern needs refinement

---

## 📊 EXAMPLES

### **Scenario 1: New Audit Created**
```bash
# You create: MODEL_PERFORMANCE_AUDIT.md in root
$ python scripts/auto_organize_docs.py --execute
# Result: Moved to docs/audits/MODEL_PERFORMANCE_AUDIT.md
```

### **Scenario 2: New Active Plan**
```bash
# You create: PHASE_04_ACTIVE_PLAN.md in root
$ python scripts/auto_organize_docs.py --execute
# Result: Stays in root (contains "ACTIVE")
```

### **Scenario 3: Old Deployment Doc**
```bash
# File exists: DEPLOY_OLD_VERSION.md (from Oct)
$ python scripts/auto_organize_docs.py --execute
# Result: Moved to archive/deployment-history/
```

---

## 🔄 MAINTENANCE

### **Weekly:**
- Run auto-organize script
- Review uncategorized files
- Update rules if new patterns emerge

### **Monthly:**
- Audit root directory
- Move completed "active" plans to older-plans
- Archive status files older than 30 days

### **Quarterly:**
- Review all organization rules
- Consolidate duplicate docs
- Update this guide

---

## 🛠️ CUSTOMIZATION

To add new categories, edit `scripts/auto_organize_docs.py`:

```python
ORGANIZATION_RULES = {
    # Add new category
    "your_category": [
        r".*YOUR_PATTERN.*\.md$",
    ],
}

DESTINATIONS = {
    "your_category": "docs/your-folder/",
}
```

Then update this document with the new rules.

---

## ✅ CHECKLIST FOR NEW DOCUMENTS

Before creating a new markdown file:

- [ ] Use descriptive naming (WHAT_TYPE_PURPOSE.md)
- [ ] Include category keyword (AUDIT, PLAN, REVIEW, etc.)
- [ ] Add date if time-sensitive (HANDOFF_NOV5.md)
- [ ] Mark as ACTIVE if current work
- [ ] Run auto-organize after creation
- [ ] Verify correct location

---

## 📞 SUPPORT

**Issues with auto-organization?**
1. Check this document for rules
2. Run dry-run mode to see what would happen
3. Review `auto_organize_docs.py` for pattern matching
4. Update rules or add manual override

**Questions?**
- See: `scripts/auto_organize_docs.py`
- Reference: `FOLDER_ORGANIZATION_REVIEW.md`

---

**Last Review:** November 5, 2025  
**Next Review:** December 5, 2025  
**Maintained By:** Project organization system








