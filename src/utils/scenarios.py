#!/usr/bin/env python3
"""
Simple scenario and shock utilities for CBI-V14.

These helpers let you apply percentage shocks to FX and macro
series and recompute key impact features for dashboard "what-if"
analysis, inspired by gs-quant's MarketDataScenario utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd


@dataclass(frozen=True)
class Shock:
    """Percentage shock to a column, e.g. +0.05 = +5%."""

    column: str
    pct: float


def apply_shocks(df: pd.DataFrame, shocks: Iterable[Shock]) -> pd.DataFrame:
    """Return a new DataFrame with multiplicative shocks applied."""
    result = df.copy()
    for shock in shocks:
        if shock.column in result.columns:
            result[shock.column] = result[shock.column] * (1.0 + shock.pct)
    return result


def fx_impact_scores(
    df: pd.DataFrame,
    fx_return_cols: Dict[str, str],
    fx_corr_cols: Dict[str, str],
    prefix: str = "fx_impact_",
) -> pd.DataFrame:
    """
    Compute FX impact scores: return × correlation.

    fx_return_cols: {"BRL": "fx_brl_return_1d", ...}
    fx_corr_cols: {"BRL": "cross_corr_fx_brl_30d", ...}
    """
    out = df.copy()
    for ccy, ret_col in fx_return_cols.items():
        corr_col = fx_corr_cols.get(ccy)
        if ret_col in out.columns and corr_col in out.columns:
            out[f"{prefix}{ccy.lower()}_score"] = out[ret_col] * out[corr_col]
    return out

