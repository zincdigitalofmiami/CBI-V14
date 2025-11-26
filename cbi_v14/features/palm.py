"""
Palm oil feature engineering for ZL forecasting.

Source assumption:
- Daily palm oil prices (already forward-filled from FRED PPOILUSDM or
  an equivalent macro table) with column `palm_price_monthly`.
- Daily ZL closes with column `zl_close`.

This module does NOT call external APIs or BigQuery directly. It expects
clean input DataFrames and returns a DataFrame of palm-related features
keyed by `date`. Persistence and ingestion are handled by callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class PalmFeatureConfig:
    """Configuration for palm feature engineering windows."""

    one_month_days: int = 30
    three_month_days: int = 90
    corr_30d_min_periods: int = 20
    corr_90d_min_periods: int = 60
    lbs_per_metric_ton: float = 2204.62


def engineer_palm_features(
    palm_daily: pd.DataFrame,
    zl_daily: pd.DataFrame,
    config: PalmFeatureConfig | None = None,
) -> pd.DataFrame:
    """
    Engineer palm oil features with daily forward-fill and staleness tracking.

    Parameters
    ----------
    palm_daily :
        DataFrame with columns:
          - 'date' (datetime-like)
          - 'palm_price_monthly' (float, USD/MT, forward-filled monthly series)
    zl_daily :
        DataFrame with columns:
          - 'date' (datetime-like)
          - 'zl_close' (float, ZL close in cents per lb)
    config :
        Optional PalmFeatureConfig to override defaults.

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per date and columns:
          - date
          - palm_price_monthly
          - palm_staleness_days
          - palm_1m_return
          - palm_3m_return
          - palm_zl_spread_usd_mt
          - palm_zl_ratio
          - palm_zl_corr_30d
          - palm_zl_corr_90d
    """
    if config is None:
        config = PalmFeatureConfig()

    if "date" not in palm_daily.columns or "palm_price_monthly" not in palm_daily.columns:
        raise ValueError("palm_daily must have 'date' and 'palm_price_monthly' columns.")
    if "date" not in zl_daily.columns or "zl_close" not in zl_daily.columns:
        raise ValueError("zl_daily must have 'date' and 'zl_close' columns.")

    palm = palm_daily.copy()
    palm["date"] = pd.to_datetime(palm["date"])
    palm = palm.sort_values("date")
    palm = palm.set_index("date")

    # Staleness: days since the last change in palm_price_monthly
    first_indices = palm.index.to_series().groupby(palm["palm_price_monthly"]).transform("first")
    palm["palm_staleness_days"] = (palm.index - first_indices).dt.days

    # Returns (monthly-based, using calendar-day approximations)
    palm["palm_1m_return"] = palm["palm_price_monthly"].pct_change(config.one_month_days)
    palm["palm_3m_return"] = palm["palm_price_monthly"].pct_change(config.three_month_days)

    palm = palm.reset_index()  # bring date back as a column

    # Merge with ZL
    zl = zl_daily.copy()
    zl["date"] = pd.to_datetime(zl["date"])
    zl = zl.sort_values("date")

    merged = palm.merge(zl[["date", "zl_close"]], on="date", how="inner")

    # Convert ZL from cents/lb to USD/MT
    merged["zl_usd_mt"] = merged["zl_close"] * 0.01 * config.lbs_per_metric_ton

    # Spread and ratio
    merged["palm_zl_spread_usd_mt"] = merged["palm_price_monthly"] - merged["zl_usd_mt"]
    merged["palm_zl_ratio"] = merged["palm_price_monthly"] / merged["zl_usd_mt"]

    # Rolling correlations between palm price and ZL close
    merged = merged.sort_values("date").set_index("date")
    merged["palm_zl_corr_30d"] = (
        merged["palm_price_monthly"]
        .rolling(window=config.one_month_days, min_periods=config.corr_30d_min_periods)
        .corr(merged["zl_close"])
    )
    merged["palm_zl_corr_90d"] = (
        merged["palm_price_monthly"]
        .rolling(window=config.three_month_days, min_periods=config.corr_90d_min_periods)
        .corr(merged["zl_close"])
    )

    merged = merged.reset_index()

    # Drop intermediate columns not meant for features
    merged = merged.drop(columns=["zl_usd_mt"])

    feature_cols = [
        "date",
        "palm_price_monthly",
        "palm_staleness_days",
        "palm_1m_return",
        "palm_3m_return",
        "palm_zl_spread_usd_mt",
        "palm_zl_ratio",
        "palm_zl_corr_30d",
        "palm_zl_corr_90d",
    ]

    return merged[feature_cols]


def validate_palm_features(
    palm_features: pd.DataFrame,
    zl_daily: pd.DataFrame,
) -> Dict[str, Dict[str, float | int | bool]]:
    """
    Basic validation checks on palm features against expectations.

    Parameters
    ----------
    palm_features :
        DataFrame produced by engineer_palm_features.
    zl_daily :
        DataFrame with 'date' and 'zl_close' columns for correlation checks.

    Returns
    -------
    dict
        Dictionary of validation checks with pass/fail flags and metrics.
    """
    results: Dict[str, Dict[str, float | int | bool]] = {}

    df = palm_features.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Join ZL for correlation checks
    zl = zl_daily.copy()
    zl["date"] = pd.to_datetime(zl["date"])
    zl = zl.sort_values("date")
    merged = df.merge(zl[["date", "zl_close"]], on="date", how="inner")

    # Null checks
    critical_cols = [
        "palm_price_monthly",
        "palm_staleness_days",
        "palm_zl_spread_usd_mt",
        "palm_zl_ratio",
    ]
    for col in critical_cols:
        nulls = merged[col].isnull().sum()
        results[f"{col}_nulls"] = {"pass": nulls == 0, "value": int(nulls)}

    # Staleness range (0–35 days is reasonable for monthly series)
    if "palm_staleness_days" in merged.columns and not merged["palm_staleness_days"].empty:
        min_stale = int(merged["palm_staleness_days"].min())
        max_stale = int(merged["palm_staleness_days"].max())
        results["staleness_range"] = {
            "pass": 0 <= min_stale and max_stale <= 40,
            "min": min_stale,
            "max": max_stale,
        }

    # Overall palm–ZL price correlation
    if not merged.empty:
        overall_corr = merged["palm_price_monthly"].corr(merged["zl_close"])
    else:
        overall_corr = np.nan
    results["overall_palm_zl_corr"] = {
        "pass": bool(overall_corr >= 0.5) if not np.isnan(overall_corr) else False,
        "value": float(overall_corr) if not np.isnan(overall_corr) else float("nan"),
    }

    # Mean 90d correlation from the features (if present)
    if "palm_zl_corr_90d" in merged.columns and merged["palm_zl_corr_90d"].notnull().any():
        mean_90d = float(merged["palm_zl_corr_90d"].mean())
        results["mean_90d_corr"] = {
            "pass": mean_90d >= 0.5,
            "value": mean_90d,
        }

    # Price ratio reasonableness (rough sanity checks)
    if "palm_zl_ratio" in merged.columns and merged["palm_zl_ratio"].notnull().any():
        p05 = float(merged["palm_zl_ratio"].quantile(0.05))
        p95 = float(merged["palm_zl_ratio"].quantile(0.95))
        ratio_ok = (p05 > 0.5) and (p95 < 2.5)
        results["palm_zl_ratio_range"] = {
            "pass": ratio_ok,
            "p05": p05,
            "p95": p95,
        }

    return results

