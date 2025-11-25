---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# FX Calculations Required (From Plans)
**Date:** November 20, 2025  
**Status:** ✅ Scripts Created, Ready for Execution

---

## FX Data Sources

### DataBento (CME FX Futures)
- **6L** (BRL/USD - Brazilian Real)
- **6E** (EUR/USD - Euro)
- **6J** (JPY/USD - Japanese Yen)
- **6C** (CAD/USD - Canadian Dollar)
- **6B** (GBP/USD - British Pound)
- **6A** (AUD/USD - Australian Dollar)
- **CNH** (CNH/USD - Chinese Yuan)

### FRED (Spot FX)
- **DTWEXAFEGS** - Trade Weighted U.S. Dollar Index: Advanced Foreign Economies, Goods and Services
- **DEXCHUS** - China / U.S. Foreign Exchange Rate
- **DEXBZUS** - Brazil / U.S. Foreign Exchange Rate
- **DEXMXUS** - Mexico / U.S. Foreign Exchange Rate
- **DEXUSEU** - U.S. / Euro Foreign Exchange Rate
- **DEXJPUS** - Japan / U.S. Foreign Exchange Rate

---

## FX Calculations Required (From Plans)

### 1. Technical Indicators (Per Currency)
**From:** `docs/plans/MASTER_PLAN.md` - Standard technical indicators

- **RSI**: 7, 14 periods
- **MACD**: Line, Signal, Histogram
- **Moving Averages**: SMA/EMA (5, 10, 20, 50, 100)
- **Bollinger Bands**: Upper, Lower, Width, Position
- **ATR**: 14 period
- **Returns**: 1d, 7d, 30d
- **Volatility**: Realized vol (5, 10, 20, 30-day)

**Prefix:** `fx_{symbol}_{indicator}` (e.g., `fx_6l_rsi_14`, `fx_6e_close`)

### 2. Cross-Currency Correlations
**From:** `docs/plans/MASTER_PLAN.md` - Cross-asset features

- **30-day rolling correlations** between all FX pairs
- **90-day rolling correlations** between all FX pairs
- **Currency strength index** (weighted average of all currencies)

**Prefix:** `fx_corr_{symbol1}_{symbol2}_{window}` (e.g., `fx_corr_6l_6e_30d`)

### 3. ZL-FX Correlations (Critical)
**From:** `docs/plans/MASTER_PLAN.md` - Cross-asset features, Dashboard plans

- **ZL-BRL correlation** (30d, 90d rolling) - Critical for export competitiveness
- **ZL-CNY correlation** (30d, 90d rolling) - Critical for China trade
- **ZL-EUR correlation** (30d, 90d rolling) - European market impact
- **ZL-USD Index correlation** (30d, 90d rolling) - Broad dollar impact

**Prefix:** `cross_corr_fx_{currency}_{window}` (e.g., `cross_corr_fx_brl_30d`)

### 4. FX Impact Features
**From:** `docs/plans/DASHBOARD_PAGES_PLAN.md` - Currency impact cards

- **BRL impact on ZL**: `fx_brl_impact_score` = BRL return × ZL-BRL correlation
- **CNY impact on ZL**: `fx_cny_impact_score` = CNY return × ZL-CNY correlation
- **USD strength index**: Weighted average of USD vs major currencies
- **FX volatility regime**: High/low volatility periods for FX

**Prefix:** `fx_impact_{currency}` or `fx_{currency}_impact`

### 5. Currency Spreads
**From:** Cross-asset features pattern

- **BRL-CNY spread**: `fx_spread_brl_cny` = BRL - CNY
- **EUR-USD spread**: `fx_spread_eur_usd` = EUR - USD
- **Currency ratios**: `fx_ratio_{currency1}_{currency2}`

**Prefix:** `fx_spread_{currency1}_{currency2}` or `fx_ratio_{currency1}_{currency2}`

### 6. FX Regime Features
**From:** Regime detection pattern

- **FX volatility regime**: Low/Normal/High/Crisis
- **FX trend regime**: Bullish/Bearish/Neutral
- **FX correlation regime**: High correlation periods vs low correlation periods

**Prefix:** `fx_regime_{type}` (e.g., `fx_regime_vol`, `fx_regime_trend`)

---

## Implementation Status

### ✅ Created Scripts:
1. **`scripts/ingest/collect_databento_forex.py`**
   - Collects FX futures from DataBento
   - Outputs: Raw FX files

2. **`scripts/features/build_forex_features.py`**
   - Calculates technical indicators
   - Calculates cross-currency correlations
   - Outputs: `forex_features.parquet`

### 🚧 Needs Enhancement:
- Add ZL-FX correlations (requires ZL price data)
- Add FX impact scores
- Add FX regime detection
- Add currency spreads/ratios

---

## BigQuery Requirements

### Tables Needed:
- `features.forex_features` - Combined FX table with all currencies and features
- `features.master_features` - Must include FX columns:
  - `databento_6e_close` (EUR/USD futures)
  - `cme_6l_brl_close` (BRL futures)
  - `fred_usd_cny` (CNY spot)
  - `fred_usd_ars` (ARS spot)
  - All `fx_*` feature columns

### Views Needed:
- `features.vw_fx_correlations` - FX correlation matrix
- `features.vw_fx_zl_impact` - ZL-FX impact analysis

---

## Next Steps

1. ✅ Run `collect_databento_forex.py` for historical backfill
2. ✅ Run `build_forex_features.py` to calculate features
3. 🚧 Enhance `build_forex_features.py` to add:
   - ZL-FX correlations (requires ZL staging data)
   - FX impact scores
   - FX regime detection
4. 🚧 Update `join_spec.yaml` to include forex features
5. 🚧 Load forex features to BigQuery
6. 🚧 Update master features view

---

**Last Updated:** November 20, 2025

