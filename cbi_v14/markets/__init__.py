"""
Market-specific configuration and helpers for CBI-V14.

This package is intended to hold:
- ZL engine-specific configs (supported horizons, symbols, feature groups).
- MES engine-specific configs.
- Any shared utilities for mapping BigQuery tables into market-aware
  data structures used by training and backtests.

Keeping these definitions here avoids scattering "what is ZL?" and
"what are the ZL horizons?" across multiple scripts.
"""

