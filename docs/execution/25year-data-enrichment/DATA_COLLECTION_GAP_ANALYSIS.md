---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Data Collection Gap Analysis
**Date**: November 16, 2025  
**Status**: Active Assessment  
**Strategy**: Keep INMET for Brazil, NOAA API for US/Argentina

---

## ✅ COLLECTED & WORKING

### 1. Economic Data
- **FRED Economic Data**: ✅ 34/35 series collected successfully
  - Script: `scripts/ingest/collect_fred_comprehensive.py`
  - Status: Working, daily updates
  - Location: `TrainingData/raw/fred/`

### 2. Market Data
- **Yahoo Finance**: ✅ 74/79 symbols collected successfully
  - Script: `scripts/ingest/collect_yahoo_finance_comprehensive.py`
  - Status: Working, daily updates
  - Location: `TrainingData/raw/yahoo/`
  - Coverage: Commodities, indices, currencies, ETFs, volatility

### 3. Weather Data
- **INMET Brazil**: ✅ Script exists (`src/ingestion/ingest_brazil_weather_inmet.py`)
  - Status: Need to verify collection
  - Coverage: Brazil only (5 stations in Mato Grosso/Mato Grosso do Sul)
  - **Action**: Verify it's collecting daily
  
- **NOAA API**: ⚠️ Script exists (`scripts/ingest/collect_noaa_comprehensive.py`)
  - Status: Collected but needs verification
  - Coverage: US Midwest (10 stations), Brazil (10 stations), Argentina (10 stations)
  - **Action**: Verify collection, use for US/Argentina (not Brazil - INMET is better)

---

## ⚠️ INCOMPLETE (Scripts Exist, Need Fixing/Testing)

### 1. CFTC COT Data
- **Script**: `scripts/ingest/collect_cftc_comprehensive.py`
- **Status**: ❌ Failing (404 errors, wrong URLs)
- **Priority**: P0 (Critical for positioning data)
- **Action**: Fix URLs using legacy script from `archive/oct31_2025_cleanup/scripts_legacy/ingest_cftc_cot_historical.py`
- **Coverage Needed**: 2006-2025 (20 years)

### 2. USDA Agricultural Data
- **Script**: `scripts/ingest/collect_usda_comprehensive.py`
- **Status**: ⚠️ Fixed (duplicate column issue resolved), needs testing
- **Priority**: P0 (Critical for crop reports, exports)
- **Action**: Test collection, verify data quality
- **Coverage Needed**: 
  - WASDE reports (monthly)
  - Export sales (weekly)
  - Crop progress (weekly during growing season)
  - NASS reports (monthly)

### 3. EIA Biofuel Data
- **Script**: `scripts/ingest/collect_eia_comprehensive.py`
- **Status**: ❌ Failing (API endpoint changes)
- **Priority**: P1 (Important for biofuel demand)
- **Action**: Try EIA API v1 or direct CSV downloads
- **Coverage Needed**:
  - Biodiesel production (weekly)
  - Renewable diesel production (weekly)
  - Stocks (weekly)

---

## ❌ NOT STARTED (Critical Gaps from Plan)

### Tier 1 Critical Gaps (Must-Have)

#### 1. China Demand Composite (8 sub-series)
**Status**: ❌ NOT STARTED  
**Priority**: P0 (CRITICAL - China is largest importer)

**Required Data**:
- [ ] Monthly China soy imports (FAS/USDA)
- [ ] Weekly purchase pace
- [ ] Dalian vs CBOT basis spread
- [ ] State reserve actions (Sinograin/COFCO announcements)
- [ ] China crush margins
- [ ] Hog herd size (meal demand proxy)
- [ ] ASF outbreak severity indices
- [ ] Tariff/quota event timeline

**Sources**:
- USDA FAS (Foreign Agricultural Service)
- Dalian Commodity Exchange
- China Customs (if accessible)
- News scraping for Sinograin/COFCO announcements

**Script Needed**: `scripts/ingest/collect_china_demand_composite.py`

---

#### 2. Tariff Intelligence (Dated Events)
**Status**: ❌ NOT STARTED  
**Priority**: P0 (CRITICAL - Trade policy drives prices)

**Required Data**:
- [ ] Section 301 timelines (announcement vs effective dates)
- [ ] Exclusion lists (product-level exemptions)
- [ ] Retaliatory schedules (China's response)
- [ ] Trade deal milestones

**Sources**:
- USTR (United States Trade Representative) website
- Federal Register (tariff announcements)
- China Ministry of Commerce
- News scraping for trade deal milestones

**Script Needed**: `scripts/ingest/collect_tariff_intelligence.py`

---

#### 3. Biofuel Policy & Prices
**Status**: ⚠️ PARTIALLY STARTED (EIA script exists but failing)

**Required Data**:
- [ ] EIA biodiesel production (weekly) - ⚠️ Script exists, needs fixing
- [ ] EIA renewable diesel production - ⚠️ Script exists, needs fixing
- [ ] RIN prices (D4, D5, D6) - ❌ NOT STARTED
- [ ] LCFS credit prices (California/Oregon) - ❌ NOT STARTED
- [ ] Mandate paths (RFS, state LCFS, SAF, Brazil RenovaBio, Indonesia B35→B40) - ❌ NOT STARTED

**Sources**:
- EIA API (for production/stocks)
- EPA RIN prices (EPA website or API)
- California Air Resources Board (LCFS credits)
- Oregon DEQ (LCFS credits)
- Government websites for mandate paths

**Scripts Needed**:
- `scripts/ingest/collect_rin_prices.py`
- `scripts/ingest/collect_lcfs_credits.py`
- `scripts/ingest/collect_biofuel_mandates.py`

---

#### 4. Substitute Oils (Full History)
**Status**: ❌ NOT STARTED  
**Priority**: P1 (Important for price relationships)

**Required Data**:
- [ ] Palm oil (FCPO/MPOB continuous series)
- [ ] Sunflower oil (Ukraine/Russia exports + prices)
- [ ] Rapeseed/canola oil (ICE/Euronext)
- [ ] Corn oil (distillers oil)
- [ ] FOB spreads between oils

**Sources**:
- MPOB (Malaysian Palm Oil Board) - prices, production, exports
- BMD (Bursa Malaysia Derivatives) - FCPO futures
- ICE/Euronext - Rapeseed/canola futures
- USDA - Corn oil production
- Trade data - Sunflower oil exports

**Script Needed**: `scripts/ingest/collect_substitute_oils.py`

---

## 📊 DATA SOURCE PRIORITY MATRIX

| Data Source | Status | Priority | Effort | Impact |
|------------|--------|----------|--------|--------|
| **FRED Economic** | ✅ Working | P0 | Low | High |
| **Yahoo Finance** | ✅ Working | P0 | Low | High |
| **INMET Brazil** | ⚠️ Verify | P0 | Low | High |
| **NOAA Weather** | ⚠️ Verify | P0 | Low | High |
| **CFTC COT** | ❌ Fix | P0 | Medium | High |
| **USDA** | ⚠️ Test | P0 | Medium | High |
| **China Demand** | ❌ Start | P0 | High | Critical |
| **Tariff Intelligence** | ❌ Start | P0 | Medium | Critical |
| **EIA Biofuels** | ❌ Fix | P1 | Medium | Medium |
| **RIN Prices** | ❌ Start | P1 | Medium | Medium |
| **LCFS Credits** | ❌ Start | P1 | Medium | Medium |
| **Substitute Oils** | ❌ Start | P1 | High | Medium |

---

## 🎯 IMMEDIATE ACTION ITEMS

### Phase 1: Verify Working Sources (1-2 hours)
1. ✅ Verify INMET Brazil is collecting daily
2. ✅ Verify NOAA API collection for US/Argentina
3. ✅ Verify FRED data is current
4. ✅ Verify Yahoo Finance data is current

### Phase 2: Fix Incomplete Sources (4-6 hours)
1. ❌ Fix CFTC COT URLs (use legacy script)
2. ⚠️ Test USDA collection (verify fixed script works)
3. ❌ Fix EIA Biofuels API (try v1 or CSV)

### Phase 3: Start Critical Gaps (8-12 hours)
1. ❌ Build China Demand Composite collector
2. ❌ Build Tariff Intelligence collector
3. ❌ Build RIN Prices collector
4. ❌ Build LCFS Credits collector

### Phase 4: Complete Remaining Gaps (4-6 hours)
1. ❌ Build Substitute Oils collector
2. ❌ Build Biofuel Mandates collector

---

## 📝 NOTES

### Weather Strategy Confirmed
- **INMET**: Brazil only (better coverage of soybean regions)
- **NOAA API**: US Midwest + Argentina (30 stations total)
- **Google GSOD**: Backup only if APIs fail

### Data Collection Philosophy
- **Keep working sources** (FRED, Yahoo, INMET, NOAA)
- **Fix incomplete sources** (CFTC, USDA, EIA)
- **Start critical gaps** (China, Tariffs, Biofuels)
- **Google Marketplace**: Backup/gap filler only

---

**Next Steps**: Start with Phase 1 verification, then move to Phase 2 fixes.

