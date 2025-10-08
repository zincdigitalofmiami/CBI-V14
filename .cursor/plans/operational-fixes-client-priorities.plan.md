# CBI-V14 Operational Fixes & Client Priority Data Gaps

## Context
CBI-V14 is an operational soybean oil forecasting platform (LightGBM baseline + neural discovery). The core architecture works, but several pipelines are stale/broken, and client dashboard priorities (China, harvest, biofuels) have data gaps.

## Client Dashboard Priorities (U.S. Oil Solutions)
1. **China purchases/cancellations** - medium-term driver (GDELT working ✅, need USDA export sales)
2. **Harvest updates** - short-term driver (weather loaders BROKEN ❌)
3. **Biofuel markets** - long-term driver (EPA RFS, production reports MISSING ❌)

## Phase 1: Fix Broken Weather Pipelines (IMMEDIATE)
**Problem:** All 3 countries have stale weather (Brazil 8d, Argentina 45d, US 34d)

**Actions:**
1. Check if `ingest_weather_noaa.py` has cron job scheduled
2. Test manual run to see error messages
3. Check NOAA API token validity
4. If NOAA broken, fall back to alternative free sources
5. Validate <24hr freshness after fix

**Files:** `ingest_weather_noaa.py`, `ingest_brazil_weather_inmet.py`
**Target table:** `weather_data` (existing)
**Budget:** $0

## Phase 2: Add Biofuels Data (CLIENT PRIORITY #3)
**Gap:** No EPA RFS mandates, RIN prices, biodiesel production

**Actions:**
1. Build `ingest_epa_rfs.py` - EPA biofuel mandate volumes
2. Add RIN price tracking (if free source exists)
3. USDA biofuel production monthly reports

**Route to:** `economic_indicators` (mandates), `news_intelligence` (reports)
**Budget:** $0 (all free APIs/scraping)

## Phase 3: Add Harvest Reports (CLIENT PRIORITY #2)
**Gap:** No USDA Crop Progress, CONAB Brazil, MAGyP Argentina

**Actions:**
1. USDA NASS Crop Progress API (weekly US harvest %) → `news_intelligence`
2. CONAB Brazil scraper (monthly harvest forecasts, Portuguese) → `news_intelligence`
3. MAGyP Argentina scraper (if available, Spanish) → `news_intelligence`

**Budget:** $0 (all free sources)

## Phase 4: Enhance China Tracking (CLIENT PRIORITY #1)
**Current:** GDELT working (130 events) ✅
**Gap:** USDA export sales (weekly China purchase volumes)

**Actions:**
1. USDA FAS export sales API → `news_intelligence`
2. Parse weekly China soybean/meal/oil purchases
3. Calculate pace vs seasonal norms

**Budget:** $0 (free USDA API)

## Phase 5: Fill Minor Gaps
1. USD/CNY source in `multi_source_collector.py`
2. Crude oil WTI source in `multi_source_collector.py`
3. MPOB Malaysia palm fundamentals → `palm_oil_fundamentals` (existing table)

**Budget:** $0

## Validation Criteria
- Weather <24hr fresh (all 3 countries) ✅
- Biofuels data updating (EPA RFS) ✅
- Harvest reports flowing (USDA, CONAB) ✅
- China purchases tracked (USDA export sales) ✅
- All client priorities have data for dashboard ✅

## NO NEW TABLES
All data routes to existing tables: `weather_data`, `economic_indicators`, `news_intelligence`, `palm_oil_fundamentals`

## Success Metrics
- 0 pipelines >24hr stale
- Client priorities (China/harvest/biofuels) fully covered
- Dashboard-ready data (no "no data yet" for client priorities)
- ML training ready (LightGBM baseline can use all features)

