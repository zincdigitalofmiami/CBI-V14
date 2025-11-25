"""
⚠️ CRITICAL: NO FAKE DATA ⚠️
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
"""

# B2) Cloud Function (Gen-2) — daily Pivot calculator
# Updated to use Databento instead of Yahoo/Alpha

import os
import json
import math
from datetime import date, timedelta
import numpy as np
import pandas as pd
from google.cloud import bigquery
import functions_framework

PROJECT = os.environ.get("BQ_PROJECT", "cbi-v14")
SRC = os.environ.get("SRC_VIEW", f"{PROJECT}.curated.vw_ohlcv_daily")
DST = os.environ.get("DST_TABLE", f"{PROJECT}.features.pivot_math_daily")
SYMBOLS = os.environ.get("SYMBOLS", "ZL=F,FCPO,USDBRL,CL=F,DXY,ZC=F,HO=F,RS=F,ZS=F,ZM=F,MES=F").split(",")

bq = bigquery.Client(project=PROJECT)


def _fetch(symbol: str, days: int) -> pd.DataFrame:
    """Fetch OHLCV data from Databento view."""
    sql = f"""
      SELECT date, high, low, close
      FROM `{SRC}`
      WHERE symbol = @s AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      ORDER BY date
    """
    return bq.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("s", "STRING", symbol)]
        ),
    ).to_dataframe()


def _daily_pivots(prev_H: float, prev_L: float, prev_C: float) -> dict:
    """Calculate daily pivot points using standard formula."""
    P = (prev_H + prev_L + prev_C) / 3.0
    R1, S1 = 2 * P - prev_L, 2 * P - prev_H
    R2, S2 = P + (prev_H - prev_L), P - (prev_H - prev_L)
    R3, S3 = prev_H + 2 * (P - prev_L), prev_L - 2 * (prev_H - P)
    R4, S4 = prev_H + 3 * (prev_H - prev_L), prev_L - 3 * (prev_H - prev_L)
    M1, M2, M3, M4 = (P + R1) / 2, (R1 + R2) / 2, (R2 + R3) / 2, (R3 + R4) / 2
    M5, M6, M7, M8 = (P + S1) / 2, (S1 + S2) / 2, (S2 + S3) / 2, (S3 + S4) / 2
    return dict(
        P=P, R1=R1, S1=S1, R2=R2, S2=S2, R3=R3, S3=S3, R4=R4, S4=S4,
        M1=M1, M2=M2, M3=M3, M4=M4, M5=M5, M6=M6, M7=M7, M8=M8
    )


def _range_pivots(H: float, L: float, C: float) -> dict:
    """Calculate pivots for weekly/monthly ranges (same formula)."""
    return _daily_pivots(H, L, C)


def _confluence_count(price: float, levels: list, sym: str) -> int:
    """Count pivot levels within ±1.0¢ of current price (ZL only)."""
    if sym != "ZL=F":
        return None
    tol = 1.0  # ±1.0¢ absolute band for ZL
    return int(sum(abs(price - l) <= tol for l in levels if np.isfinite(l)))


@functions_framework.http
def handler(request):
    """Cloud Function entry point for daily pivot calculation."""
    today = date.today()
    rows = []

    for sym in SYMBOLS:
        df = _fetch(sym, days=370)
        if df.shape[0] < 23:  # needs prior day + week + month
            continue

        # Current and prior day
        df = df.dropna()
        if len(df) < 2:
            continue

        cur = df.iloc[-1]
        prev = df.iloc[-2]

        # Weekly range (prior completed week Mon..Sun)
        d = df.copy()
        d['dow'] = pd.to_datetime(d['date']).dt.weekday  # Mon=0
        # last completed week ends the day before this week's Monday
        this_monday = pd.to_datetime(today) - pd.Timedelta(
            days=pd.to_datetime(today).weekday()
        )
        wk = d[d['date'] < this_monday.date()].tail(7)
        if not wk.empty:
            H_w, L_w, C_w = (
                wk['high'].max(),
                wk['low'].min(),
                wk['close'].iloc[-1],
            )
        else:
            H_w, L_w, C_w = np.nan, np.nan, np.nan

        # Monthly range (prior completed calendar month)
        t = pd.to_datetime(today)
        first_of_this_month = t.replace(day=1)
        last_of_prev_month = (first_of_this_month - pd.Timedelta(days=1)).date()
        mo = d[
            pd.to_datetime(d['date']).dt.to_period('M')
            == pd.to_datetime(last_of_prev_month).to_period('M')
        ]
        if not mo.empty:
            H_m, L_m, C_m = (
                mo['high'].max(),
                mo['low'].min(),
                mo['close'].iloc[-1],
            )
        else:
            H_m, L_m, C_m = np.nan, np.nan, np.nan

        dp = _daily_pivots(prev.high, prev.low, prev.close)
        wp = (
            _range_pivots(H_w, L_w, C_w)
            if np.isfinite(H_w)
            else {k: np.nan for k in ['P', 'R1', 'S1', 'R2', 'S2', 'R3', 'S3']}
        )
        mp = (
            _range_pivots(H_m, L_m, C_m)
            if np.isfinite(H_m)
            else {k: np.nan for k in ['P', 'R1', 'S1', 'R2', 'S2', 'R3', 'S3']}
        )

        price = float(cur.close)

        # Distances
        def dist(x):
            return (price - x) if np.isfinite(x) else np.nan

        dP = dist(dp['P'])
        dR1 = dist(dp['R1'])
        dS1 = dist(dp['S1'])
        dR2 = dist(dp['R2'])
        dS2 = dist(dp['S2'])
        dR3 = dist(dp['R3'])
        dS3 = dist(dp['S3'])

        nearest, nearest_type = None, None
        for name in ['P', 'R1', 'S1', 'R2', 'S2', 'R3', 'S3', 'R4', 'S4', 'M1', 'M5']:
            lv = dp.get(name, np.nan)
            if np.isfinite(lv):
                di = abs(price - lv)
                if nearest is None or di < nearest:
                    nearest, nearest_type = di, name

        price_above_P = price > dp['P']
        price_between_R1_R2 = (price >= min(dp['R1'], dp['R2'])) and (
            price <= max(dp['R1'], dp['R2'])
        )
        price_between_S1_P = (price >= min(dp['S1'], dp['P'])) and (
            price <= max(dp['S1'], dp['P'])
        )

        weekly_dist = abs(price - wp['P']) if np.isfinite(wp['P']) else np.nan
        monthly_dist = abs(price - mp['P']) if np.isfinite(mp['P']) else np.nan

        conf_levels = [
            dp['P'],
            dp['R1'],
            dp['S1'],
            dp['R2'],
            dp['S2'],
            wp.get('P', np.nan),
            mp.get('P', np.nan),
        ]
        conf_count = _confluence_count(price, conf_levels, sym)
        zone_strength = (
            None
            if conf_count is None
            else (
                1
                if conf_count <= 1
                else 2
                if conf_count == 2
                else 3
                if conf_count == 3
                else 4
                if conf_count == 4
                else 5
            )
        )

        # High-probability signals
        # price_rejected_R1_twice: prior 3 days touched above R1 but closed back below R1 twice
        last3 = df.tail(4)  # includes prev day
        rej = False
        if last3.shape[0] >= 3 and np.isfinite(dp['R1']):
            touches = (
                (last3['high'].iloc[:-1] > dp['R1'])
                & (last3['close'].iloc[:-1] < dp['R1'])
            ).sum()
            rej = touches >= 2

        # price_bouncing_off_S1: last 3 sessions low <= S1 and closes above P twice
        bnc = False
        if (
            last3.shape[0] >= 3
            and np.isfinite(dp['S1'])
            and np.isfinite(dp['P'])
        ):
            lows = (last3['low'].iloc[:-1] <= dp['S1']).sum()
            closes = (last3['close'].iloc[:-1] >= dp['P']).sum()
            bnc = (lows >= 1 and closes >= 2)

        # stuck between R1 and S1 for 3 days
        between = lambda row: (
            min(dp['S1'], dp['R1']) <= row['close'] <= max(dp['S1'], dp['R1'])
        )
        stuck = (
            last3.iloc[:-1].apply(between, axis=1).sum() >= 3
            if last3.shape[0] >= 4
            else False
        )

        # weekly_pivot_flip: today close above WP while yesterday close below WP (or vice versa)
        flip = False
        if np.isfinite(wp['P']) and df.shape[0] >= 2:
            y_close = df.iloc[-2]['close']
            flip = (
                (y_close < wp['P'] and price > wp['P'])
                or (y_close > wp['P'] and price < wp['P'])
            )

        rows.append({
            "date": today,
            "symbol": sym,
            **dp,
            "M1": dp["M1"],
            "M2": dp["M2"],
            "M3": dp["M3"],
            "M4": dp["M4"],
            "M5": dp["M5"],
            "M6": dp["M6"],
            "M7": dp["M7"],
            "M8": dp["M8"],
            "WP": wp.get("P"),
            "WR1": wp.get("R1"),
            "WS1": wp.get("S1"),
            "WR2": wp.get("R2"),
            "WS2": wp.get("S2"),
            "WR3": wp.get("R3"),
            "WS3": wp.get("S3"),
            "MP": mp.get("P"),
            "MR1": mp.get("R1"),
            "MS1": mp.get("S1"),
            "MR2": mp.get("R2"),
            "MS2": mp.get("S2"),
            "MR3": mp.get("R3"),
            "MS3": mp.get("S3"),
            "current_price": price,
            "distance_to_P": dP,
            "distance_to_R1": dR1,
            "distance_to_S1": dS1,
            "distance_to_R2": dR2,
            "distance_to_S2": dS2,
            "distance_to_R3": dR3,
            "distance_to_S3": dS3,
            "distance_to_nearest_pivot": float(nearest) if nearest is not None else None,
            "nearest_pivot_type": nearest_type,
            "price_above_P": price_above_P,
            "price_between_R1_R2": price_between_R1_R2,
            "price_between_S1_P": price_between_S1_P,
            "weekly_pivot_distance": weekly_dist,
            "monthly_pivot_distance": monthly_dist,
            "pivot_confluence_count": conf_count,
            "pivot_zone_strength": zone_strength,
            "price_rejected_R1_twice": rej,
            "price_bouncing_off_S1": bnc,
            "price_stuck_between_R1_S1_for_3_days": stuck,
            "weekly_pivot_flip": flip,
            "pivot_confluence_3_or_higher": (conf_count is not None and conf_count >= 3),
        })

    if not rows:
        return ("no-rows", 200)

    out = pd.DataFrame(rows)
    bq.load_table_from_dataframe(
        out,
        DST,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
    ).result()

    return (
        json.dumps({"inserted": len(rows)}),
        200,
        {"Content-Type": "application/json"},
    )

