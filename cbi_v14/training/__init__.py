"""
Training utilities and model runners for CBI-V14.

This package is the home for reusable training code (dataset loading,
splitting, metric calculation, and model fitting). Production training
scripts under `scripts/train/` should import from here instead of
re-implementing training logic ad hoc.

Initial focus:
- ZL baseline engines (see docs/plans/ZL_PRODUCTION_SPEC.md).
- MES engines once the ZL pipeline is stable.

Over time, this package should expose small, composable helpers that
mirror the patterns now embedded in `scripts/train/train_zl_baselines.py`
and the experimental `quick_zl_baseline.py`.
"""

