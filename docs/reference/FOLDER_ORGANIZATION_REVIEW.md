# CBI-V14 Top-Level Folder Organization Review
**READ ONLY ANALYSIS - Recommendations for Restructuring**  
**Date:** November 5, 2025  
**Status:** 📊 Analysis Complete - Awaiting Approval

---

## 🎯 EXECUTIVE SUMMARY

**Current State:** 18 top-level folders with inconsistent naming, 3 empty directories, duplicate structures  
**Recommendation:** Consolidate to ~12 well-organized folders with clear naming conventions  
**Impact:** Improved navigation, reduced confusion, better maintainability  
**Risk Level:** LOW - Most changes are simple renames/consolidations

---

## 📊 CURRENT FOLDER ANALYSIS

### ✅ WELL-ORGANIZED (Keep As-Is)
| Folder | Size | Last Modified | Status | Purpose |
|--------|------|---------------|--------|---------|
| `dashboard-nextjs/` | 826M | Oct 31 | ✅ ACTIVE | Next.js frontend - clear name |
| `docs/` | 1.8M | Nov 5 | ✅ ACTIVE | Documentation hub - good structure |
| `archive/` | 43M | Nov 5 | ✅ ACTIVE | Historical files - well organized |
| `config/` | 32K | Nov 2 | ✅ ACTIVE | Configuration files - clear purpose |

---

### ⚠️ NAMING INCONSISTENCIES (Recommend Rename)

#### Problem: Inconsistent Naming Conventions
- **Snake_case:** `bigquery_sql`, `models_v4`, `inmet_csv_data`
- **Kebab-case:** `cb-ingest`, `cbi-v14-ingestion`, `terraform-deploy`, `dashboard-nextjs`
- **Mixed:** Some with prefixes, some without

#### 🔧 RECOMMENDATION 1: Standardize to kebab-case

| Current Name | Recommended Name | Reason |
|--------------|------------------|--------|
| `bigquery_sql/` | `bigquery-sql/` | Consistency with other folders |
| `models_v4/` | `models-v4/` | Consistency (or just `models/`) |
| `inmet_csv_data/` | Archive or Delete | Empty folder, not used |
| `cbi_venv/` | `.venv/` | Standard Python convention |

---

### 🔄 DUPLICATE/OVERLAPPING STRUCTURES

#### Problem: Similar Purposes, Confusing Names

| Folder | Purpose | Files | Recommendation |
|--------|---------|-------|----------------|
| `scripts/` | Utility scripts, monitors, deployment | 80+ files | ✅ Keep - general utilities |
| `cbi-v14-ingestion/` | Data ingestion pipelines | 70+ files | ⚠️ Rename to `ingestion/` |
| `automl/` | Vertex AI prediction scripts | 7 files | ⚠️ Rename to `vertex-ai/` or merge into `scripts/ml/` |
| `forecast/` | FastAPI forecast service | 7 files | ✅ Keep - standalone service |

#### 🔧 RECOMMENDATION 2: Clarify Purpose Through Naming

**Current:** `cbi-v14-ingestion/` (redundant project prefix)  
**Better:** `ingestion/` (clear, concise)

**Current:** `automl/` (vague - is it AutoML config or predictions?)  
**Better:** `vertex-ai/` or `predictions/` (explicit purpose)

---

### 🗑️ EMPTY/UNUSED FOLDERS (Recommend Remove)

| Folder | Size | Files | Last Modified | Action |
|--------|------|-------|---------------|--------|
| `cache/` | 0B | 0 | Oct 20 | 🗑️ DELETE (not used) |
| `cb-ingest/` | 0B | 0 | Oct 3 | 🗑️ DELETE (not used) |
| `inmet_csv_data/` | 0B | 0 | Oct 6 | 🗑️ DELETE (empty) |

**Note:** These folders are completely empty and serve no purpose.

---

### 🔍 REDUNDANT/CONFUSING STRUCTURES

#### Problem: `cbi-v14-ingestion/bigquery_sql/` vs `bigquery_sql/`

**Analysis:**
- Root `bigquery_sql/`: 112+ SQL files for training, BQML, features
- `cbi-v14-ingestion/bigquery_sql/`: Empty folder (0 files)

**🔧 RECOMMENDATION 3:** Delete empty `cbi-v14-ingestion/bigquery_sql/` folder

---

### 📁 DATA STORAGE ANALYSIS

#### Current Data Folders:
| Folder | Purpose | Size | Status |
|--------|---------|------|--------|
| `data/` | Social media scraped data | 11M | ✅ ACTIVE |
| `data/csv/` | Historical price CSVs (Oct 3) | ~270K | ⚠️ OLD DATA |
| `logs/` | Application logs | 1.7M | ✅ ACTIVE |

**🔧 RECOMMENDATION 4:** Move `data/csv/` to `archive/data-snapshots/oct-2025/`

---

### 🏗️ BUILD/DEPLOY FOLDERS

| Folder | Purpose | Size | Files | Recommendation |
|--------|---------|------|-------|----------------|
| `terraform-deploy/` | IaC deployment | 4K | 1 file | ⚠️ Rename to `terraform/` |
| `forecast/` | FastAPI service | 256K | Dockerfile, main.py | ✅ Keep - clear purpose |
| `src/` | React components (legacy?) | 20K | 4 files | ⚠️ Archive or clarify |

**Issue:** `src/` appears to be old React code, but we have `dashboard-nextjs/src/`

**🔧 RECOMMENDATION 5:** 
- If `src/` is legacy: Move to `archive/legacy-react/`
- If active: Rename to `react-components/` or merge into dashboard

---

### 🔒 HIDDEN/SYSTEM FOLDERS (Currently Visible)

| Folder | Purpose | Recommendation |
|--------|---------|----------------|
| `__pycache__/` | Python bytecode cache | ✅ Already in .gitignore |
| `cbi_venv/` | Python virtual env | ⚠️ Rename to `.venv/` (hidden) |

**🔧 RECOMMENDATION 6:** Rename `cbi_venv/` to `.venv/` (standard convention)

---

## 🎯 PROPOSED REORGANIZATION PLAN

### Phase 1: Remove Dead Weight (Low Risk)
```bash
# Delete 3 empty folders
rm -rf cache/ cb-ingest/ inmet_csv_data/
```

### Phase 2: Standardize Naming (Medium Risk - Update paths)
```bash
# Rename for consistency
mv bigquery_sql/ bigquery-sql/
mv models_v4/ models/
mv cbi-v14-ingestion/ ingestion/
mv automl/ vertex-ai/
mv terraform-deploy/ terraform/
mv cbi_venv/ .venv/
```

### Phase 3: Archive Old Data (Low Risk)
```bash
# Move outdated CSV data
mkdir -p archive/data-snapshots/oct-2025/
mv data/csv/* archive/data-snapshots/oct-2025/
```

### Phase 4: Clarify Purpose (Medium Risk - Requires Investigation)
```bash
# Investigate src/ folder
# If legacy: mv src/ archive/legacy-react/
# If active: Rename appropriately
```

---

## 📋 FINAL RECOMMENDED STRUCTURE

```
/Users/zincdigital/CBI-V14/
├── .venv/                          # Python virtual env (hidden)
├── archive/                        # Historical files ✅
├── bigquery-sql/                   # SQL queries (renamed)
├── config/                         # Configuration ✅
├── dashboard-nextjs/               # Next.js frontend ✅
├── data/                           # Active data files ✅
├── docs/                           # Documentation ✅
├── forecast/                       # FastAPI service ✅
├── ingestion/                      # Data pipelines (renamed)
├── logs/                           # Application logs ✅
├── models/                         # Model artifacts (renamed)
├── scripts/                        # Utility scripts ✅
├── terraform/                      # Infrastructure (renamed)
├── vertex-ai/                      # Vertex AI predictions (renamed)
│
├── CBI_V14_COMPLETE_EXECUTION_PLAN.md
├── HANDOFF_NOV5_END_OF_DAY.md
├── README.md
├── CONTRIBUTING.md
├── Makefile
├── LICENSE
├── cloudbuild.yaml
└── cron_audit_report.py
```

**Result:**
- ✅ 14 top-level folders (from 18)
- ✅ Consistent kebab-case naming
- ✅ Clear purpose for each folder
- ✅ No empty/unused directories
- ✅ No duplicate structures

---

## 🎨 NAMING CONVENTION GUIDELINES

### Adopted Standard: `kebab-case` for Folders

**Why kebab-case?**
1. URL-friendly (dashboard-nextjs aligns with subdomain naming)
2. Easy to read and type
3. No special character escaping needed
4. Industry standard for modern projects

**Examples:**
- ✅ `bigquery-sql`, `vertex-ai`, `terraform`
- ❌ `bigquery_sql`, `models_v4`, `cb-ingest`

**Exceptions:**
- Hidden folders: `.venv`, `.cache`, `.git` (start with dot)
- Special Python: `__pycache__` (double underscore is standard)
- Single words: `data`, `logs`, `config`, `scripts` (no separator needed)

---

## ⚠️ IMPACT ANALYSIS

### Files Requiring Path Updates After Reorganization

#### High Priority (Update Required):
1. **Python imports** - If any scripts reference `cbi-v14-ingestion`
2. **Shell scripts** - Any `cd` commands with old paths
3. **Cron jobs** - Path references in `cron_audit_report.py`
4. **Docker/Cloud Build** - `cloudbuild.yaml` volume mounts
5. **Documentation** - Update all MD files with old paths

#### Search Commands Before Renaming:
```bash
# Find all hardcoded paths
grep -r "cbi-v14-ingestion" . --exclude-dir=node_modules
grep -r "bigquery_sql" . --exclude-dir=node_modules
grep -r "models_v4" . --exclude-dir=node_modules
grep -r "cbi_venv" . --exclude-dir=node_modules
```

---

## 🚦 RISK ASSESSMENT

| Change | Risk Level | Impact | Mitigation |
|--------|-----------|--------|------------|
| Delete empty folders | 🟢 LOW | None - unused | None needed |
| Rename folders | 🟡 MEDIUM | Update imports/paths | Search & replace before execution |
| Archive old data | 🟢 LOW | Historical only | Keep in archive/ |
| Standardize naming | 🟡 MEDIUM | Import paths change | Test thoroughly |

---

## ✅ RECOMMENDED EXECUTION ORDER

1. **Backup First** - `tar -czf CBI-V14-backup-$(date +%Y%m%d).tar.gz .`
2. **Delete empty folders** (Phase 1)
3. **Search for hardcoded paths** (grep commands above)
4. **Update path references** in code/configs
5. **Rename folders** (Phase 2)
6. **Test imports** - Run key scripts to verify
7. **Archive old data** (Phase 3)
8. **Update documentation** - All MD files
9. **Git commit** - "refactor: reorganize folder structure for clarity"

---

## 💡 ADDITIONAL OBSERVATIONS

### Positive Aspects:
✅ Clear separation of concerns (dashboard, ingestion, scripts)  
✅ Archive folder already established  
✅ Good documentation structure in `docs/`  
✅ Active maintenance (Nov 5 updates visible)

### Areas for Improvement:
⚠️ Inconsistent naming conventions across folders  
⚠️ Empty/unused directories creating clutter  
⚠️ Some vague names (`automl`, `src`) don't describe purpose  
⚠️ Redundant project prefix (`cbi-v14-ingestion`)

---

## 🎯 NEXT STEPS

**Option A: Full Reorganization (Recommended)**
- Apply all 6 recommendations
- ~2-3 hours work including testing
- Maximum clarity and consistency

**Option B: Minimal Changes (Conservative)**
- Just delete empty folders (cache, cb-ingest, inmet_csv_data)
- ~5 minutes work
- Quick win with zero risk

**Option C: Phased Approach (Balanced)**
- Phase 1: Delete empty folders (now)
- Phase 2: Rename folders (next sprint)
- Phase 3: Archive old data (next sprint)
- Spreads risk, easier to test

---

**Recommendation:** Start with **Option C (Phased)** - delete empty folders immediately, then plan renames during next maintenance window.

---

**Status:** ✅ ANALYSIS COMPLETE - Ready for Review  
**Prepared by:** Folder organization audit system  
**Next Action:** Review with team and select execution plan







