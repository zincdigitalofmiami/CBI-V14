"""
⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

# A2) Cloud Function (Gen-2) — daily Fibonacci calculator
# Updated to use Databento instead of Yahoo/Alpha

import os
import json
from datetime import date, timedelta
import numpy as np
import pandas as pd
from google.cloud import bigquery
import functions_framework

PROJECT = os.environ.get("BQ_PROJECT", "cbi-v14")
SRC_VIEW = os.environ.get("SRC_VIEW", f"{PROJECT}.curated.vw_ohlcv_daily")
DST_TABLE = os.environ.get("DST_TABLE", f"{PROJECT}.features.fib_levels_daily")
SYMBOLS = os.environ.get("SYMBOLS", "ZL=F,FCPO,USDBRL,CL=F,DXY,ZC=F,HO=F,RS=F,ZS=F,ZM=F,MES=F").split(",")
LOOKBACK = int(os.environ.get("LOOKBACK_DAYS", "220"))  # fetch ~200+ days
SWING_WIN = int(os.environ.get("SWING_WINDOW", "126"))  # 126 trading days
ZIGZAG = float(os.environ.get("ZIGZAG_PCT", "0.06"))  # 5–7% → default 6%

bq = bigquery.Client(project=PROJECT)


def _fetch(symbol: str) -> pd.DataFrame:
    """Fetch close prices from Databento view."""
    sql = f"""
    SELECT date, close FROM `{SRC_VIEW}`
    WHERE symbol = @sym AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK} DAY)
    ORDER BY date
    """
    return bq.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("sym", "STRING", symbol)]
        ),
    ).to_dataframe()


def _zigzag_last_swing(px: pd.Series, pct: float, lookback: int) -> dict:
    """
    Zigzag algorithm to detect last swing high/low.
    
    Args:
        px: Price series
        pct: Minimum percentage move to register a pivot (default 6%)
        lookback: Number of days to look back
    
    Returns:
        dict with low_idx, high_idx, direction, swing_low, swing_high
    """
    s = px.tail(lookback).reset_index(drop=True)
    p = s.values
    n = len(p)
    
    if n < 40:
        return None
    
    piv_types, piv_idx = [], []
    i0 = 0
    extreme_idx = 0
    extreme_price = p[0]
    direction = None
    
    for i in range(1, n):
        x = p[i]
        if direction is None:
            if (x - p[i0]) / p[i0] >= pct:
                piv_types.append('L')
                piv_idx.append(i0)
                direction = 'up'
                extreme_idx = i
                extreme_price = x
            elif (p[i0] - x) / p[i0] >= pct:
                piv_types.append('H')
                piv_idx.append(i0)
                direction = 'down'
                extreme_idx = i
                extreme_price = x
        elif direction == 'up':
            if x >= extreme_price:
                extreme_price, extreme_idx = x, i
            elif (extreme_price - x) / extreme_price >= pct:
                piv_types.append('H')
                piv_idx.append(extreme_idx)
                direction = 'down'
                extreme_idx = i
                extreme_price = x
        else:  # direction == 'down'
            if x <= extreme_price:
                extreme_price, extreme_idx = x, i
            elif (x - extreme_price) / extreme_price >= pct:
                piv_types.append('L')
                piv_idx.append(extreme_idx)
                direction = 'up'
                extreme_idx = i
                extreme_price = x
    
    if len(piv_idx) < 2:
        # Fallback: use absolute min/max
        lo, hi = int(np.argmin(p)), int(np.argmax(p))
        if lo < hi:
            last = (('L', lo), ('H', hi))
        else:
            last = (('H', hi), ('L', lo))
    else:
        last = list(zip(piv_types, piv_idx))[-2:]
    
    (t1, i1), (t2, i2) = last
    low_idx = i1 if t1 == 'L' else i2
    high_idx = i1 if t1 == 'H' else i2
    swing_low, swing_high = float(p[low_idx]), float(p[high_idx])
    low_is_first = low_idx < high_idx
    direction = 'up' if low_is_first else 'down'
    
    return {
        "low_idx": low_idx,
        "high_idx": high_idx,
        "direction": direction,
        "swing_low": swing_low,
        "swing_high": swing_high,
    }


def _levels(swing_low: float, swing_high: float, direction: str) -> dict:
    """
    Calculate Fibonacci retracements and extensions.
    
    Args:
        swing_low: Swing low price
        swing_high: Swing high price
        direction: 'up' or 'down'
    
    Returns:
        dict with retracement and extension levels
    """
    r = swing_high - swing_low
    if r <= 0:
        return None
    
    # Retracements (inside swing)
    if direction == 'up':
        retr = {
            "retrace_236": swing_high - 0.236 * r,
            "retrace_382": swing_high - 0.382 * r,
            "retrace_50": swing_high - 0.500 * r,
            "retrace_618": swing_high - 0.618 * r,
            "retrace_786": swing_high - 0.786 * r,
        }
    else:  # direction == 'down'
        retr = {
            "retrace_236": swing_low + 0.236 * r,
            "retrace_382": swing_low + 0.382 * r,
            "retrace_50": swing_low + 0.500 * r,
            "retrace_618": swing_low + 0.618 * r,
            "retrace_786": swing_low + 0.786 * r,
        }
    
    # Extensions (beyond swing along trend)
    if direction == 'up':
        ext = {
            "ext_100": swing_high,
            "ext_1236": swing_high + 0.236 * r,
            "ext_1382": swing_high + 0.382 * r,
            "ext_1618": swing_high + 0.618 * r,
            "ext_200": swing_high + 1.000 * r,
            "ext_2618": swing_high + 1.618 * r,
        }
    else:  # direction == 'down'
        ext = {
            "ext_100": swing_low,
            "ext_1236": swing_low - 0.236 * r,
            "ext_1382": swing_low - 0.382 * r,
            "ext_1618": swing_low - 0.618 * r,
            "ext_200": swing_low - 1.000 * r,
            "ext_2618": swing_low - 1.618 * r,
        }
    
    return retr | ext


def _near(price: float, level: float, tol_abs: float = None, tol_pct: float = 0.01) -> bool:
    """Check if price is near a Fibonacci level."""
    if np.isnan(level):
        return False
    return abs(price - level) <= (tol_abs if tol_abs is not None else tol_pct * price)


def _tolerances(symbol: str) -> dict:
    """
    Get tolerance values for near-level detection.
    
    Per spec: ZL has cent-based tolerances, others use percentage.
    """
    if symbol == "ZL=F":
        return dict(ret_618=0.8, ext_1618=1.2, generic_pct=0.01)  # cents
    return dict(ret_618=None, ext_1618=None, generic_pct=0.01)  # percentage


@functions_framework.http
def handler(request):
    """Cloud Function entry point for daily Fibonacci calculation."""
    today = date.today()
    rows = []

    for sym in SYMBOLS:
        df = _fetch(sym)
        if df.empty:
            continue

        zz = _zigzag_last_swing(df['close'], pct=ZIGZAG, lookback=SWING_WIN)
        if not zz:
            continue

        levels = _levels(zz["swing_low"], zz["swing_high"], zz["direction"])
        if not levels:
            continue

        # Dates for indices
        s_tail = df.tail(SWING_WIN).reset_index(drop=True)
        low_date = s_tail.loc[zz["low_idx"], 'date'].date()
        high_date = s_tail.loc[zz["high_idx"], 'date'].date()

        cp = float(df['close'].iloc[-1])
        pos_pct = float(100.0 * (cp - zz["swing_low"]) / (zz["swing_high"] - zz["swing_low"]))
        ddays = (today - (low_date if zz["direction"] == 'up' else high_date)).days

        tol = _tolerances(sym)
        near_618 = _near(cp, levels["retrace_618"], tol_abs=tol["ret_618"], tol_pct=tol["generic_pct"])
        near_1618 = _near(cp, levels["ext_1618"], tol_abs=tol["ext_1618"], tol_pct=tol["generic_pct"])
        near_any = any([
            _near(cp, levels["retrace_382"], tol_pct=tol["generic_pct"]),
            _near(cp, levels["retrace_50"], tol_pct=tol["generic_pct"]),
            near_618,
            _near(cp, levels["ext_100"], tol_pct=tol["generic_pct"]),
            near_1618,
        ])

        rows.append({
            "date": today,
            "symbol": sym,
            "swing_date_low": low_date,
            "swing_date_high": high_date,
            "swing_low_price": zz["swing_low"],
            "swing_high_price": zz["swing_high"],
            "trend_direction": zz["direction"],
            "days_since_swing": ddays,
            **levels,
            "current_price": cp,
            "swing_position_pct": pos_pct,
            "price_near_618_retrace": bool(near_618),
            "price_near_1618_ext": bool(near_1618),
            "price_near_any_major": bool(near_any),
        })

    if not rows:
        return ("no-rows", 200)

    out = pd.DataFrame(rows)
    bq.load_table_from_dataframe(
        out,
        DST_TABLE,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
    ).result()

    return (
        json.dumps({"inserted": len(rows)}),
        200,
        {"Content-Type": "application/json"},
    )

