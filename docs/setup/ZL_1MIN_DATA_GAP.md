# ZL 1-Minute Data Gap - CRITICAL

**Date:** 2025-11-18  
**Status:** BLOCKING for accurate ZL microstructure features

## Problem

ZL raw data currently contains ONLY 1-hour OHLCV files (`ohlcv-1h`), NOT 1-minute data.

**Location:** `TrainingData/raw/databento_zl/`
- GLBX-20251118-FRGDM3B7UG: 1-day files
- GLBX-20251118-TAAH7VN45V: 1-hour files (per-day files like `glbx-mdp3-20100606.ohlcv-1h.json`)

## Impact

Even after fixing the ZL aggregator (`scripts/ingest/aggregate_zl_intraday.py`), the following features in `staging/zl_daily_aggregated.parquet` are **mathematically incorrect**:

- `zl_60min_realized_vol` - computed from 1h bars instead of intraday ticks → artificially low variance
- `zl_60min_hl_vol` - high-low volatility estimated from 1h candles → underestimates true intraday volatility  
- `zl_60min_vwap` - meaningless when calculated on 1h OHLC bars instead of tick data

## Join Spec Impact

`registry/join_spec.yaml` lines 217-228 expect these ZL microstructure features for the join:

```yaml
# === JOIN: ZL Intraday Aggregated Features (from Databento) ===
- name: "add_zl_intraday_features"
  left: "<<add_mes_intraday_features>>"
  right: "staging/zl_daily_aggregated.parquet"
  on: ["date"]
  how: "left"
  null_policy:
    allow: true
    fill_method: "ffill"
  tests:
    - expect_rows_preserved
    - expect_columns_added: ["zl_60min_realized_vol", "zl_60min_hl_vol", "zl_60min_vwap"]
```

**Current State:** These columns exist but contain unreliable values computed from hourly data.

## Required Action

### Option A: Download 1-Minute ZL Data (Recommended)

1. **Submit Databento historical data request:**
   - Symbol: ZL (Soybean Oil futures)
   - Schema: OHLCV-1M (1-minute bars)
   - Date range: 2010-06-06 to 2025-11-17 (match existing 1d/1h coverage)
   - Dataset: GLBX.MDP3
   - Format: JSON with pretty_ts/pretty_px

2. **Download and place in:** `TrainingData/raw/databento_zl/`

3. **Rerun:** `python3 scripts/ingest/aggregate_zl_intraday.py`

4. **Verify:** Microstructure features recalculated from true 1-minute bars

### Option B: Relax Join Tests (Interim)

Update `registry/join_spec.yaml` lines 217-228 to flag ZL features as unreliable:

```yaml
tests:
  - expect_rows_preserved
  # DISABLED until 1-minute data arrives:
  # - expect_columns_added: ["zl_60min_realized_vol", "zl_60min_hl_vol", "zl_60min_vwap"]
```

Add comment documenting the data gap.

### Option C: Skip ZL Microstructure Entirely

Remove ZL intraday features from training pipeline until proper 1-minute data is available. Use only daily ZL OHLCV from 1-day files.

## Current Mitigation

The ZL aggregator script has been fixed to:
- Filter outright-only contracts (no spreads)
- Use volume-weighted selection when multiple contracts trade same day
- Generate numeric columns

However, the underlying data limitation (1h instead of 1m) remains and cannot be fixed without new data.

## Recommendation

**Download 1-minute ZL data from Databento** as soon as possible to enable accurate microstructure feature calculation for soybean oil futures.

