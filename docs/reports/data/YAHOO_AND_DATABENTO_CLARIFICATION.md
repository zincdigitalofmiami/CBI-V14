---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Yahoo & DataBento Usage Clarification
**Date**: November 18, 2025  
**Status**: Final Architecture Decision

## 🎯 Executive Summary

- **Alpha Vantage**: ❌ COMPLETELY REMOVED - No longer used
- **Yahoo Finance**: ✅ LIMITED ONGOING USE - Historical bridge only  
- **DataBento**: ✅ PRIMARY SOURCE - All live and forward data

## 📊 Yahoo Finance - LIMITED But ONGOING Use

### What Yahoo IS Used For:
1. **ZL Historical Bridge (2000-2010)**
   - DataBento only goes back to 2010-06-06
   - Yahoo provides the missing decade
   - Table: `market_data.yahoo_zl_historical_2000_2010`

2. **Technical Indicators on Historical Data**
   - 46+ indicators calculated from Yahoo OHLCV
   - One-time calculation, stored permanently
   - Columns: `yahoo_zl_rsi_14`, `yahoo_zl_macd`, etc.

### What Yahoo is NOT Used For:
- ❌ Live data collection
- ❌ Real-time feeds
- ❌ Any data after 2010
- ❌ Other symbols (only ZL)

### Yahoo Data Flow:
```
Historical Yahoo ZL (2000-2010)
    ↓
One-time backfill
    ↓
market_data.yahoo_zl_historical_2000_2010
    ↓
Stitched with DataBento in master_features
    ↓
Static historical reference (no updates)
```

## 🚀 DataBento - PRIMARY Live Source

### What DataBento Provides:
- **All futures data** (2010-present)
- **29 symbols** + calendar spreads
- **Live feeds** (1-minute updates)
- **Microstructure** (trades, depth, orderflow)
- **All horizons** (1min to 12m)

### DataBento Collection Schedule:
- **ZL**: Every 5 minutes (priority)
- **MES**: Every 1 minute (intraday training)
- **Others**: Every hour (standard)

### DataBento Tables:
- `market_data.databento_futures_ohlcv_1m`
- `market_data.databento_futures_ohlcv_1d`
- `market_data.databento_futures_continuous_1d`
- `market_data.orderflow_1m`

## 📈 Complete Data Architecture

```
HISTORICAL (2000-2010):
Yahoo ZL → One-time backfill → Static storage

LIVE (2010-present):
DataBento → Continuous updates → BigQuery → Dashboard

TRAINING:
Master Features = Yahoo Historical + DataBento Live
```

## ✅ Migration Checklist

### Completed:
- ✅ Removed all Alpha Vantage references
- ✅ Updated all documentation
- ✅ Deleted Alpha Vantage files (7 files)
- ✅ Updated BigQuery schema
- ✅ Updated deployment scripts

### Yahoo Specific Actions:
1. **One-time historical backfill** (Day 1 post-deployment)
2. **Calculate technical indicators** (Day 1)
3. **Store permanently** in BigQuery
4. **No ongoing collection scripts needed**

## 🎯 Final Architecture

| Source | Period | Usage | Updates |
|--------|--------|-------|---------|
| Yahoo | 2000-2010 | Historical bridge | None (static) |
| DataBento | 2010-present | Primary source | Continuous |
| ~~Alpha Vantage~~ | ~~None~~ | ~~Removed~~ | ~~N/A~~ |

## 📝 Key Decisions

1. **Yahoo is kept** for historical continuity (2000-2010)
2. **DataBento is primary** for all live/forward data
3. **Alpha Vantage is eliminated** completely
4. **No redundancy** - each source has a specific, non-overlapping purpose

---
**Architecture Locked** ✅  
**Ready for Deployment** ✅
