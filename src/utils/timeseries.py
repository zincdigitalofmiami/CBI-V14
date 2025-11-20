#!/usr/bin/env python3
"""
Core time-series utilities for CBI-V14.

Purpose:
- Provide a small, reusable library for technical indicators and volatility calculations,
  inspired by the structure of `gs_quant.timeseries` but implemented locally.
- Keep feature scripts (e.g., scripts/features/feature_calculations.py) thin by delegating
  common calculations here.

Notes:
- Only deterministic transforms of real input series. No synthetic data generation.
- All functions accept pandas Series or DataFrames and return aligned Series/DataFrames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
import pandas as pd

WindowLike = Union[int, "Window"]


@dataclass
class Window:
    """Simple rolling window specification."""

    size: Optional[int]

    def normalize(self, series: pd.Series) -> int:
        if self.size is None:
            return len(series)
        return int(self.size)


def _ensure_series(x: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    if isinstance(x, pd.DataFrame):
        if x.shape[1] != 1:
            raise ValueError("Expected a single-column Series or DataFrame.")
        return x.iloc[:, 0]
    return x


def moving_average(x: Union[pd.Series, pd.DataFrame], window: WindowLike) -> pd.Series:
    """Simple moving average over a rolling window."""
    s = _ensure_series(x)
    w = window if isinstance(window, Window) else Window(window)
    n = w.normalize(s)
    return s.rolling(window=n, min_periods=1).mean()


def exponential_moving_average(x: Union[pd.Series, pd.DataFrame], span: int) -> pd.Series:
    """Exponential moving average with given span."""
    s = _ensure_series(x)
    return s.ewm(span=span, adjust=False).mean()


def bollinger_bands(
    x: Union[pd.Series, pd.DataFrame],
    window: WindowLike,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands (upper, lower, width, position)."""
    s = _ensure_series(x)
    w = window if isinstance(window, Window) else Window(window)
    n = w.normalize(s)

    ma = s.rolling(window=n, min_periods=1).mean()
    std = s.rolling(window=n, min_periods=1).std()

    upper = ma + num_std * std
    lower = ma - num_std * std
    width = upper - lower
    position = (s - lower) / (width.replace(0, np.nan))

    return pd.DataFrame(
        {
            "bb_middle": ma,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_width": width,
            "bb_position": position,
        }
    )


def relative_strength_index(
    x: Union[pd.Series, pd.DataFrame],
    period: int = 14,
) -> pd.Series:
    """Relative Strength Index (RSI)."""
    s = _ensure_series(x)
    delta = s.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def macd(
    x: Union[pd.Series, pd.DataFrame],
    fast_span: int = 12,
    slow_span: int = 26,
    signal_span: int = 9,
) -> pd.DataFrame:
    """MACD line, signal, and histogram."""
    s = _ensure_series(x)
    ema_fast = exponential_moving_average(s, fast_span)
    ema_slow = exponential_moving_average(s, slow_span)
    line = ema_fast - ema_slow
    signal = line.ewm(span=signal_span, adjust=False).mean()
    hist = line - signal
    return pd.DataFrame(
        {
            "macd_line": line,
            "macd_signal": signal,
            "macd_histogram": hist,
        }
    )


def realized_volatility(
    returns: Union[pd.Series, pd.DataFrame],
    window: int,
    annualization_factor: float = 252.0,
) -> pd.Series:
    """Rolling realized volatility of returns, annualized."""
    s = _ensure_series(returns)
    return s.rolling(window=window, min_periods=max(1, window // 2)).std() * np.sqrt(
        annualization_factor
    )


def range_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int = 30,
    annualization_factor: float = 252.0,
) -> pd.Series:
    """Parkinson-style range-based volatility estimate."""
    log_hl_sq = (np.log(high / low)) ** 2
    parkinson_var = log_hl_sq.rolling(window=window, min_periods=max(1, window // 2)).mean() / (
        4 * np.log(2)
    )
    return np.sqrt(parkinson_var) * np.sqrt(annualization_factor)


def seasonal_adjustment_rolling(
    x: Union[pd.Series, pd.DataFrame],
    window: int = 252,
) -> pd.Series:
    """
    Lightweight seasonal adjustment using a centered rolling mean.

    This is intentionally simple and dependency-free, but gives you a
    quick way to compare level vs trend for FX and macro series.
    """
    s = _ensure_series(x)
    trend = s.rolling(window=window, center=True, min_periods=window // 4).mean()
    return s - trend

