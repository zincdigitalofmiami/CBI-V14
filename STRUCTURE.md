# CBI-V14 Project Structure

## Overview
This document describes the fully organized structure of the CBI-V14 project after the comprehensive November 2025 reorganization. The project is now cleanly separated between current Vertex AI work and legacy BQML work, with all documentation properly categorized and no duplicate folders.

## Path Relationship (Critical)

**The repository lives on the external drive, with a symlink for convenience:**

- **Actual Location (Primary)**: `/Volumes/Satechi Hub/Projects/CBI-V14/`
  - This is where the `.git` repository actually lives
  - All files, code, plans, configs are stored here
  - This is the working directory for all operations

- **Symlink (Convenience)**: `/Users/kirkmusick/Documents/GitHub/CBI-V14/`
  - Points to the external drive location via symlink
  - Created by `setup_new_machine.sh` for IDE/tool compatibility
  - **Both paths point to the same files** - edit either one

**When editing files:**
- Use either path - they're the same via symlink
- Git operations work from either location
- All tools (Cursor, VS Code, terminal) can use either path
- The external drive path is the "source of truth" (where `.git` lives)

**Why this setup:**
- External drive stores everything (code + large TrainingData/Models/Logs)
- Symlink provides standard GitHub path for tools expecting `~/Documents/GitHub/`
- Single source of truth, no sync needed

## Directory Structure

```
/Volumes/Satechi Hub/Projects/CBI-V14/
│
├── 📁 active-plans/              # Current working plans (8 strategic files)
│   ├── MASTER_EXECUTION_PLAN.md              # PRIMARY - 7-day institutional system
│   ├── VERTEX_AI_TRUMP_ERA_PLAN.md
│   ├── TRUMP_ERA_EXECUTION_PLAN.md
│   ├── MAC_TRAINING_SETUP_PLAN.md
│   ├── MAC_TRAINING_EXPANDED_STRATEGY.md
│   ├── BASELINE_STRATEGY.md
│   ├── PHASE_1_PRODUCTION_GAPS.md
│   └── REGIME_BASED_TRAINING_STRATEGY.md
│
├── 📁 archive/                   # Historical snapshots and legacy packages
│   └── [date-based archives]
│
├── 📁 config/                    # Configuration files
│   ├── bigquery/                # SQL queries and views
│   │   ├── PRODUCTION_HORIZON_SPECIFIC/
│   │   ├── PRODUCTION_STANDARD_258_FEATURES/
│   │   └── vertex-ai/
│   └── terraform/               # Infrastructure as code
│
├── 📁 dashboard-nextjs/          # Frontend dashboard (Next.js)
│
├── 📁 data/                      # Local cache / temporary datasets
│
├── 📁 docs/                      # Documentation library
│   ├── analysis/                # Data & model analysis reports
│   ├── audits/                  # Verification & audit reports
│   ├── handoffs/                # Session handoffs & summaries
│   ├── operations/              # Operational documentation
│   ├── plans/                   # Historical planning documents
│   ├── reference/               # Reference guides & architecture docs
│   └── vegas-intel/             # Vegas intelligence documentation
│
├── 📁 legacy/                    # All legacy work & deprecated assets
│   ├── bqml-work/              # BQML specific files (including sql/)
│   ├── old-analysis/
│   ├── old-plans/
│   ├── old-scripts/
│   └── old-training/
│
├── 📁 Logs/                      # Execution logs (training/ingestion/deployment)
├── 📁 Models/                    # Trained model artifacts
├── 📁 scripts/                   # Shell utilities, cron helpers, orchestration
├── 📁 src/                       # Application source code
│   ├── ingestion/
│   ├── prediction/
│   ├── training/
│   ├── utils/
│   └── [frontend components]
│
├── 📁 TrainingData/              # Training datasets stored on external drive
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── 📁 vertex-ai/                 # Vertex AI implementation
│   ├── data/                    # Data validation & audit scripts
│   ├── deployment/              # Model deployment pipeline (4 scripts)
│   ├── evaluation/              # Model explainability
│   ├── prediction/              # Prediction generation
│   └── training/                # Training scripts (Day 2+)
│
├── cloudbuild.yaml
├── fix_satechi_permissions.sh
├── migrate_to_new_mac.sh
├── README.md                     # Project overview
├── QUICK_REFERENCE.txt           # Fast reference for production system
├── START_HERE.md                 # Session kickoff guide
├── STRUCTURE.md                  # (this file)
├── setup_new_machine.sh          # M4 Mac mini setup script
├── setup_on_new_mac.sh           # Legacy migration helper (see notes)
└── CBI-V14.code-workspace        # Cursor/VS Code workspace
```

## Key Organization Principles

### 1. Active vs Legacy Separation
- **active-plans/**: Current initiatives (Vertex AI + neural Mac pipeline)
- **legacy/**: Deprecated BQML plans, scripts, and archives retained for reference
- **archive/**: Immutable snapshots and previous turnovers

### 2. Source Code Layout
- **src/** contains all Python/TypeScript source by responsibility
- **scripts/** stores operational utilities (status checks, ingestion triggers)
- **vertex-ai/** encapsulates everything required to train/export/deploy neural models

### 3. Documentation Layout
- **docs/** now houses everything previously scattered across `audits/`, `plans/`, `system/`, etc.
  - Refer to the subdirectories for the theme you need (audits, handoffs, reference, vegas-intel, …)
- Root documentation (`README.md`, `START_HERE.md`, `QUICK_REFERENCE.txt`, `STRUCTURE.md`) stays concise and current

### 4. Data & Model Assets
- **TrainingData/**, **Models/**, and **Logs/** are stored on the external drive to protect the internal SSD
- `TrainingData/exports/` is the canonical landing zone for BigQuery exports
- `Logs/` contains structured subfolders (`training/`, `ingestion/`, `deployment/`)

## Navigation Guide

### For Daily Work
1. Review `active-plans/` for the latest priorities and execution details
2. Develop in `src/` and `vertex-ai/`
3. Use `scripts/` for operational commands (status checks, consolidations)

### For Reference
1. `docs/handoffs/` → prior handover summaries and session wraps
2. `docs/audits/` → verification reports
3. `legacy/` → historical BQML materials or retired plans when context is required

### For New Team Members
1. Start with `START_HERE.md`
2. Read `README.md` for the platform overview
3. Follow `active-plans/` to understand current execution focus

## Maintenance Guidelines

### Adding New Files
- Source code → `src/` (or relevant subfolder inside `vertex-ai/`)
- Automation scripts → `scripts/`
- Documentation → appropriate subfolder inside `docs/`
- Deprecated assets → move to `legacy/`

### Archiving Old Work
- Use `legacy/old-*` for retired scripts, plans, or analyses
- Snapshot full turnovers into `archive/` (date-stamped folder) when needed

### Updating Plans & Docs
- Keep `active-plans/` limited to in-flight efforts only
- Update `README.md`, `STRUCTURE.md`, and `QUICK_REFERENCE.txt` whenever paths or ownership change
- Use `docs/` for detailed long-form documentation; cross-link from root files for discoverability

## External Drive Structure
```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/
│   ├── processed/
│   └── exports/
├── Models/
│   ├── local/
│   ├── vertex-ai/
│   └── bqml/
└── Logs/
    ├── training/
    ├── ingestion/
    └── deployment/
```

## Success Metrics
- ✅ Top-level structure matches the reorganized repository
- ✅ Clear separation between active work, documentation, and legacy assets
- ✅ Directory naming consistent across repository, documentation, and setup scripts
- ✅ External storage usage documented and easy to navigate

## Last Updated
November 12, 2025 - Post reorganization alignment
