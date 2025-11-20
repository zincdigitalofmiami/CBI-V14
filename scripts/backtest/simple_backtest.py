#!/usr/bin/env python3
"""
Lightweight backtesting helpers for CBI-V14.

Design goals:
- Purely local, no external APIs.
- Work with the master feature DataFrames you already build.
- Provide clear PnL and basic metrics for rule-based strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    price_col: str = "zl_price_current"
    signal_col: str = "signal"
    position_col: str = "position"


def build_position_from_signal(df: pd.DataFrame, config: BacktestConfig) -> pd.Series:
    """Convert a generic signal into a position series."""
    signal = df[config.signal_col]
    return np.sign(signal).fillna(0.0)


def run_backtest(df: pd.DataFrame, config: Optional[BacktestConfig] = None) -> pd.DataFrame:
    """Run a simple daily backtest on a feature DataFrame."""
    if config is None:
        config = BacktestConfig()

    bt_df = df.sort_values("date").copy()

    if config.position_col not in bt_df.columns:
        bt_df[config.position_col] = build_position_from_signal(bt_df, config)

    price = bt_df[config.price_col]
    returns = price.pct_change().fillna(0.0)
    bt_df["pnl"] = bt_df[config.position_col].shift(1).fillna(0.0) * returns
    bt_df["cum_pnl"] = bt_df["pnl"].cumsum()

    return bt_df

