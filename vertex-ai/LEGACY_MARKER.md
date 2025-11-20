# ⚠️ LEGACY DIRECTORY - REFERENCE ONLY

**Date**: November 2025  
**Status**: Not Used in Current Architecture

---

## Important Notice

This `vertex-ai/` directory contains **legacy code** that is **NOT used** in the current training architecture.

### Current Architecture (November 2025)

- ✅ **100% Local Training** on Mac M4
- ✅ **BigQuery for Storage Only** (no cloud compute)
- ❌ **NO Vertex AI** (not used for training or inference)
- ❌ **NO BQML Training** (deprecated)

### Why This Directory Exists

This directory is kept for **reference purposes only**:
- Historical implementation patterns
- Previous deployment approaches
- Legacy table naming conventions

### What to Use Instead

**For Training**:
- `src/training/baselines/` - Local training scripts
- `src/training/config/m4_config.py` - M4-optimized configs
- `src/training/evaluation/metrics.py` - Evaluation pipeline

**For Data**:
- `scripts/export_training_data.py` - Export from BigQuery
- `scripts/upload_predictions.py` - Upload predictions

**For Documentation**:
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Current training plan
- `docs/training/M4_OPTIMIZATION_GUIDE.md` - M4 optimization guide

---

**DO NOT USE** scripts in this directory for current work. They reference old table names and deprecated architectures.







