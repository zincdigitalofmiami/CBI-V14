---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# CBI-V14 Documentation

This directory contains all project documentation organized by topic and purpose.

## Directory Structure

```
docs/
├── analysis/          # Market analysis, correlations, heavy hitters
├── audits/            # System audits, verification reports
├── code-reviews/      # Code review documentation
├── data/              # Data manifests, schemas, ETL documentation
├── forecast/          # Forecast outputs and analysis
├── handoffs/          # Session handoffs and summaries
├── plans/             # Historical planning documents
├── production/        # Production system configuration docs
├── reference/         # Reference guides and quick starts
├── training/          # Training reports and model documentation
├── vegas/             # Vegas-specific intelligence
└── vegas-intel/       # Vegas Glide API integration docs
```

## Finding What You Need

### Quick Start & Orientation
- `../START_HERE.md` (repo root)
- `reference/QUICK_START_NEXT_SESSION.md`
- `../QUICK_REFERENCE.txt` (repo root)

### Current Plans & Strategy
- `../active-plans/MASTER_EXECUTION_PLAN.md` ⭐ **Start here for overall strategy**
- `../active-plans/VERTEX_AI_TRUMP_ERA_PLAN.md`
- `../active-plans/TRUMP_ERA_EXECUTION_PLAN.md`
- `../active-plans/MAC_TRAINING_SETUP_PLAN.md`

### System Documentation
- `production/` - Production system configs
- `reference/OFFICIAL_PRODUCTION_SYSTEM.md` - Naming conventions, data flow
- `audits/` - System verification reports
- `data/` - Data pipeline documentation

### Historical Context
- `handoffs/` - Previous session summaries
- `plans/` - Old planning documents
- `../legacy/` - Deprecated BQML work

## Navigation Tips

1. **For daily work**: Check `../active-plans/MASTER_EXECUTION_PLAN.md`
2. **For data questions**: Look in `data/` or `audits/`
3. **For historical context**: Check `handoffs/` or `plans/`
4. **For Vegas work**: See `vegas/` or `vegas-intel/`

## Maintenance

- Keep `../active-plans/` focused on current execution only
- Move completed work from `active-plans/` to `docs/plans/` with date stamps
- Archive old documentation to `../archive/` if no longer relevant
- Update this README when adding new doc categories

**Last Updated**: November 12, 2025
