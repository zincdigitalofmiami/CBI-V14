"""
ZL engine market configuration for CBI-V14.

Centralizes key ZL-related settings so they are not duplicated across
scripts and plans.
"""

from typing import Dict, List

# Canonical futures root for soybean oil
ZL_ROOT: str = "ZL"

# Supporting roots for the ZL engine (soy complex + energy)
ZL_SUPPORTING_ROOTS: List[str] = ["ZS", "ZM", "CL", "HO"]

# Combined root universe for the ZL engine
ZL_ENGINE_ROOTS: List[str] = [ZL_ROOT] + ZL_SUPPORTING_ROOTS

# Horizon definitions in trading days (baseline engine)
ZL_HORIZON_DAYS: Dict[str, int] = {
    "1w": 5,
    "1m": 20,
    "3m": 60,
    "6m": 120,
    "12m": 240,
}

