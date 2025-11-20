#!/usr/bin/env python3
"""
FX feature helpers for CBI-V14.

Centralizes:
- List of FX symbols
- Per-symbol technical feature calculations
- Cross-currency FX features
- ZL-FX correlation and impact scores
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from src.utils.fx_config import FX_CONFIG
from src.utils.timeseries import (
    moving_average,
    exponential_moving_average,
    bollinger_bands,
    relative_strength_index,
)


FOREX_SYMBOLS: List[str] = FX_CONFIG.databento_symbols()


def add_symbol_technicals(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Add per-symbol FX technical features (RSI, MACD, MAs, bands, returns, vol, ATR)."""
    prefix = f"fx_{symbol}_"
    close_col = f"{symbol}_close"

    if close_col not in df.columns:
        return df

    out = df.sort_values("date").copy()
    price = out[close_col]

    # RSI
    out[f"{prefix}rsi_14"] = relative_strength_index(price, 14)
    out[f"{prefix}rsi_7"] = relative_strength_index(price, 7)

    # MACD
    macd_df = exponential_macd(price)
    out[f"{prefix}macd_line"] = macd_df["macd_line"]
    out[f"{prefix}macd_signal"] = macd_df["macd_signal"]
    out[f"{prefix}macd_hist"] = macd_df["macd_histogram"]

    # Moving Averages (SMA/EMA)
    for period in [5, 10, 20, 50, 100]:
        out[f"{prefix}sma_{period}"] = moving_average(price, period)
        out[f"{prefix}ema_{period}"] = exponential_moving_average(price, period)

    # Bollinger Bands (20-day, 2 std)
    bb = bollinger_bands(price, 20, num_std=2.0)
    out[f"{prefix}bb_upper"] = bb["bb_upper"]
    out[f"{prefix}bb_lower"] = bb["bb_lower"]
    out[f"{prefix}bb_width"] = bb["bb_width"]
    out[f"{prefix}bb_position"] = bb["bb_position"]

    # Returns
    out[f"{prefix}return_1d"] = price.pct_change(1)
    out[f"{prefix}return_7d"] = price.pct_change(7)
    out[f"{prefix}return_30d"] = price.pct_change(30)

    # Volatility (rolling std of returns, not annualized)
    ret = price.pct_change()
    for period in [5, 10, 20, 30]:
        out[f"{prefix}vol_{period}d"] = ret.rolling(period, min_periods=period // 2).std()

    # ATR (if high/low available)
    high_col = f"{symbol}_high"
    low_col = f"{symbol}_low"
    if high_col in out.columns and low_col in out.columns:
        hl = out[high_col] - out[low_col]
        hc = (out[high_col] - out[close_col].shift()).abs()
        lc = (out[low_col] - out[close_col].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        out[f"{prefix}atr_14"] = tr.rolling(14, min_periods=1).mean()

    return out


def exponential_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD using exponential moving averages."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return pd.DataFrame(
        {
            "macd_line": line,
            "macd_signal": sig,
            "macd_histogram": hist,
        }
    )


def add_cross_currency_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-currency correlations, spreads, and FX strength index."""
    out = df.sort_values("date").copy()

    # Raw close columns for FX (not already prefixed)
    close_cols = [c for c in out.columns if c.endswith("_close") and not c.startswith("fx_")]
    if len(close_cols) < 2:
        return out

    # Returns per currency
    for col in close_cols:
        symbol = col.replace("_close", "")
        out[f"fx_{symbol}_ret"] = out[col].pct_change()

    # Cross-currency correlations (30d, 90d)
    ret_cols = [c for c in out.columns if c.startswith("fx_") and c.endswith("_ret")]
    for window in [30, 90]:
        for i, col1 in enumerate(ret_cols):
            for col2 in ret_cols[i + 1 :]:
                symbol1 = col1.replace("fx_", "").replace("_ret", "")
                symbol2 = col2.replace("fx_", "").replace("_ret", "")
                out[f"fx_corr_{symbol1}_{symbol2}_{window}d"] = (
                    out[col1].rolling(window, min_periods=window // 2).corr(out[col2])
                )

    # Currency spreads (BRL-CNY, EUR-USD, etc.)
    if "6l_close" in out.columns and "cnh_close" in out.columns:
        out["fx_spread_brl_cny"] = out["6l_close"] - out["cnh_close"]
        out["fx_ratio_brl_cny"] = out["6l_close"] / (out["cnh_close"] + 1e-10)

    if "6e_close" in out.columns:
        # EUR-USD spread (simplified vs 1.0 baseline)
        out["fx_eur_usd_spread"] = out["6e_close"] - 1.0

    # Currency strength index (mean of 1d FX returns)
    if ret_cols:
        out["fx_strength_index"] = out[ret_cols].mean(axis=1)
        out["fx_volatility_regime"] = pd.cut(
            out[ret_cols].std(axis=1),
            bins=[0, 0.01, 0.02, 0.05, 1.0],
            labels=["low", "normal", "high", "crisis"],
        )

    return out


def add_zl_fx_correlations(df: pd.DataFrame, staging_dir, logger=None) -> pd.DataFrame:
    """Calculate ZL-FX correlations and FX impact scores."""
    out = df.sort_values("date").copy()

    # Try to load ZL price data
    zl_files = [
        staging_dir / "zl_daily_aggregated.parquet",
        staging_dir / "yahoo_zl.parquet",
        staging_dir / "databento_zl_daily.parquet",
    ] + list(staging_dir.glob("*zl*.parquet"))

    zl_df = None
    zl_close_col = None

    for zl_file in zl_files:
        if zl_file.exists():
            try:
                tmp = pd.read_parquet(zl_file)
                if "date" in tmp.columns:
                    tmp["date"] = pd.to_datetime(tmp["date"])
                for col in ["zl_close", "close", "zl_price_current", "price", "yahoo_zl_close", "databento_zl_close"]:
                    if col in tmp.columns:
                        zl_df = tmp
                        zl_close_col = col
                        if logger:
                            logger.info(f"   ✅ Found ZL data in {zl_file.name}")
                        break
                if zl_df is not None:
                    break
            except Exception:
                continue

    if zl_df is None or zl_close_col is None:
        if logger:
            logger.warning("   ⚠️  ZL price data not found, skipping ZL-FX correlations")
        return out

    zl_subset = zl_df[["date", zl_close_col]].rename(columns={zl_close_col: "zl_close"}).copy()
    zl_subset = zl_subset.dropna(subset=["zl_close"])

    merged = out.merge(zl_subset, on="date", how="inner")
    if merged.empty:
        if logger:
            logger.warning("   ⚠️  No overlapping dates with ZL data")
        return out

    merged["zl_return"] = merged["zl_close"].pct_change()

    for window in [30, 90]:
        if "fx_6l_ret" in merged.columns:
            merged[f"cross_corr_fx_brl_{window}d"] = (
                merged["zl_return"].rolling(window, min_periods=window // 2).corr(merged["fx_6l_ret"])
            )
        if "fx_cnh_ret" in merged.columns:
            merged[f"cross_corr_fx_cny_{window}d"] = (
                merged["zl_return"].rolling(window, min_periods=window // 2).corr(merged["fx_cnh_ret"])
            )
        if "fx_6e_ret" in merged.columns:
            merged[f"cross_corr_fx_eur_{window}d"] = (
                merged["zl_return"].rolling(window, min_periods=window // 2).corr(merged["fx_6e_ret"])
            )
        if "fx_strength_index" in merged.columns:
            merged[f"cross_corr_fx_usd_index_{window}d"] = (
                merged["zl_return"].rolling(window, min_periods=window // 2).corr(merged["fx_strength_index"])
            )

    # Impact scores
    if "fx_6l_ret" in merged.columns and "cross_corr_fx_brl_30d" in merged.columns:
        merged["fx_brl_impact_score"] = merged["fx_6l_ret"] * merged["cross_corr_fx_brl_30d"]
    if "fx_cnh_ret" in merged.columns and "cross_corr_fx_cny_30d" in merged.columns:
        merged["fx_cny_impact_score"] = merged["fx_cnh_ret"] * merged["cross_corr_fx_cny_30d"]

    if logger:
        count = len(
            [
                c
                for c in merged.columns
                if c.startswith("cross_corr_fx_") or (c.startswith("fx_") and "impact" in c)
            ]
        )
        logger.info(f"   ✅ Added {count} ZL-FX correlation features")

    return merged

