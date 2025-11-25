# Dashboard Documentation

All dashboard-related documentation organized by category with active/old/new structure.

## Structure

### **pages/** - Page Documentation
```
pages/
├── active/   Currently working on pages
├── old/      Completed/deprecated pages
└── new/      Recently created pages
```
Document individual dashboard pages, components, features.

### **audits/** - Dashboard Audits
```
audits/
├── active/   Ongoing audits
├── old/      Completed audits
└── new/      Pending audits
```
Performance audits, accessibility audits, code quality reviews.

### **plans/** - Dashboard Plans
```
plans/
├── active/   Current development plans
├── old/      Completed plans
└── new/      Proposed features/plans
```
Feature roadmaps, implementation plans, architecture decisions.

### **coding/** - Code Documentation
```
coding/
├── active/   Current coding guidelines/standards
├── old/      Deprecated patterns
└── new/      Proposed standards
```
Component patterns, TypeScript types, styling guidelines.

### **deployment/** - Deployment Documentation
```
deployment/
├── active/   Current deployment configs (2 files)
│   ├── DEPLOYMENT.md
│   └── VERCEL_SETUP.md
├── old/      Historical deployments
└── new/      Pending deployment changes
```
Vercel setup, deployment guides, CI/CD configurations.

### **guides/** - General Guides
Setup guides, contribution guidelines, how-tos.

---

## Workflow

1. **New Documentation** → Create in `[category]/new/`
2. **Active Work** → Move to `[category]/active/`
3. **Completed/Archived** → Move to `[category]/old/`

---

## Examples

### Documenting a New Page:
```bash
# 1. Create documentation
echo "# Vegas Intelligence Page" > docs/pages/new/vegas-intelligence.md

# 2. While building
mv docs/pages/new/vegas-intelligence.md docs/pages/active/

# 3. When complete
mv docs/pages/active/vegas-intelligence.md docs/pages/old/
```

### Performance Audit:
```bash
# Create audit
docs/audits/new/PERFORMANCE_AUDIT_DEC2025.md

# Move to active while investigating
mv docs/audits/new/PERFORMANCE_AUDIT_DEC2025.md docs/audits/active/

# Archive when complete
mv docs/audits/active/PERFORMANCE_AUDIT_DEC2025.md docs/audits/old/
```

---

## Current Files

**Audits (old/):**
- ACTUAL_STATE_ANALYSIS.md
- SUMMARY.md

**Deployment (active/):**
- DEPLOYMENT.md
- VERCEL_SETUP.md

---

## Root Files (Keep in dashboard-nextjs/)

- **README.md** - Main dashboard README
- Package files (package.json, package-lock.json)
- Config files (next.config.js, tailwind.config.js, tsconfig.json)
- Scripts (deploy.sh, setup.sh, test-api.sh)

All other documentation → `docs/` folder

---

**Last Updated:** November 5, 2025  
**Organization System:** active/old/new for all categories








