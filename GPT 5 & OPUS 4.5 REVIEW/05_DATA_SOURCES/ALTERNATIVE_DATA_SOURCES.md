---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Alternative Data Sources for Missing Data
**Date**: November 16, 2025  
**Status**: Research Phase  
**Goal**: Find alternative sources for data we don't have

---

## 1. CHINA DEMAND COMPOSITE (8 sub-series)

### Required Data:
- Monthly China soy imports
- Weekly purchase pace
- Dalian vs CBOT basis spread
- State reserve actions (Sinograin/COFCO)
- China crush margins
- Hog herd size
- ASF outbreak severity
- Tariff/quota timeline

### Alternative Sources:

#### A. USDA FAS (Foreign Agricultural Service)
- **Source**: https://apps.fas.usda.gov/psdonline/
- **Data**: China soybean imports (monthly)
- **Access**: Public, free
- **Format**: CSV downloads
- **Script**: `scripts/ingest/collect_usda_fas_china.py`

#### B. Dalian Commodity Exchange
- **Source**: http://www.dce.com.cn/
- **Data**: Dalian futures prices (soybean, soybean meal, soybean oil)
- **Access**: Public prices, historical data available
- **Format**: Web scraping or API
- **Script**: `scripts/ingest/collect_dalian_futures.py`

#### C. China Customs Data (Alternative)
- **Source**: Various data providers (TradingEconomics, CEIC, Wind)
- **Data**: Monthly import statistics
- **Access**: May require subscription
- **Alternative**: Use USDA FAS (free, reliable)

#### D. News Scraping for State Reserves
- **Source**: ScrapeCreators API (already have access)
- **Data**: Sinograin/COFCO announcements
- **Access**: Via ScrapeCreators
- **Script**: `scripts/ingest/collect_china_reserve_announcements.py`

#### E. China Hog Herd Data
- **Source**: USDA FAS Livestock Reports
- **Data**: China hog inventory estimates
- **Access**: Public, free
- **Script**: `scripts/ingest/collect_china_hog_data.py`

#### F. ASF Outbreak Data
- **Source**: OIE (World Organisation for Animal Health)
- **Data**: ASF outbreak reports
- **Access**: Public database
- **Script**: `scripts/ingest/collect_asf_outbreaks.py`

---

## 2. TARIFF INTELLIGENCE (Dated Events)

### Required Data:
- Section 301 timelines
- Exclusion lists
- Retaliatory schedules
- Trade deal milestones

### Alternative Sources:

#### A. USTR (United States Trade Representative)
- **Source**: https://ustr.gov/
- **Data**: Section 301 announcements, exclusion lists
- **Access**: Public, free
- **Format**: PDFs, press releases (web scraping)
- **Script**: `scripts/ingest/collect_ustr_tariffs.py`

#### B. Federal Register
- **Source**: https://www.federalregister.gov/
- **Data**: Tariff announcements, effective dates
- **Access**: Public API available
- **Format**: JSON API
- **Script**: `scripts/ingest/collect_federal_register_tariffs.py`

#### C. China Ministry of Commerce
- **Source**: http://english.mofcom.gov.cn/
- **Data**: Retaliatory tariff announcements
- **Access**: Public, free
- **Format**: Web scraping
- **Script**: `scripts/ingest/collect_china_retaliatory_tariffs.py`

#### D. Trade Deal Milestones
- **Source**: News scraping (ScrapeCreators)
- **Data**: Phase 1 deal announcements, negotiations
- **Access**: Via ScrapeCreators
- **Script**: `scripts/ingest/collect_trade_deal_milestones.py`

---

## 3. BIOFUEL POLICY & PRICES

### Required Data:
- EIA biodiesel/renewable diesel production (weekly)
- RIN prices (D4, D5, D6)
- LCFS credit prices (CA/OR)
- Mandate paths (RFS, state LCFS, SAF, Brazil RenovaBio, Indonesia B35→B40)

### Alternative Sources:

#### A. EIA Biofuel Data
- **Source**: EIA API v1 or CSV downloads
- **Data**: Biodiesel/renewable diesel production, stocks
- **Access**: Public, free
- **Format**: API or CSV
- **Script**: `scripts/ingest/collect_eia_biofuels_v1.py` (fix existing script)

#### B. EPA RIN Prices
- **Source**: EPA RIN Data (https://www.epa.gov/fuels-registration-reporting-and-compliance-help)
- **Data**: D4, D5, D6 RIN prices
- **Access**: Public, free
- **Format**: CSV downloads
- **Script**: `scripts/ingest/collect_epa_rin_prices.py`

#### C. California LCFS Credits
- **Source**: California Air Resources Board (CARB)
- **Data**: LCFS credit prices
- **Access**: Public, free
- **Format**: CSV downloads or web scraping
- **Script**: `scripts/ingest/collect_carb_lcfs.py`

#### D. Oregon LCFS Credits
- **Source**: Oregon DEQ
- **Data**: LCFS credit prices
- **Access**: Public, free
- **Format**: CSV downloads
- **Script**: `scripts/ingest/collect_oregon_lcfs.py`

#### E. RFS Mandate Paths
- **Source**: EPA RFS Program
- **Data**: Annual volume requirements
- **Access**: Public, free
- **Format**: PDFs, web scraping
- **Script**: `scripts/ingest/collect_rfs_mandates.py`

#### F. Brazil RenovaBio
- **Source**: ANP (Brazil National Agency of Petroleum)
- **Data**: RenovaBio mandate volumes
- **Access**: Public, free
- **Format**: Web scraping
- **Script**: `scripts/ingest/collect_brazil_renovabio.py`

#### G. Indonesia B35→B40
- **Source**: Indonesian government announcements
- **Data**: Biodiesel mandate increases
- **Access**: Public, free
- **Format**: News scraping
- **Script**: `scripts/ingest/collect_indonesia_biodiesel_mandates.py`

---

## 4. SUBSTITUTE OILS

### Required Data:
- Palm oil (FCPO/MPOB)
- Sunflower oil (Ukraine/Russia exports + prices)
- Rapeseed/canola oil (ICE/Euronext)
- Corn oil (distillers oil)
- FOB spreads

### Alternative Sources:

#### A. Palm Oil - MPOB
- **Source**: Malaysian Palm Oil Board (MPOB)
- **Data**: Production, exports, stocks, prices
- **Access**: Public, free
- **Format**: CSV downloads
- **Script**: `scripts/ingest/collect_mpob_palm_oil.py`

#### B. Palm Oil - BMD Futures
- **Source**: Bursa Malaysia Derivatives (BMD)
- **Data**: FCPO futures prices
- **Access**: Public prices
- **Format**: Web scraping or Yahoo Finance (FCPO=F)
- **Script**: Use Yahoo Finance collection (already have)

#### C. Sunflower Oil
- **Source**: USDA FAS, Trade data
- **Data**: Ukraine/Russia exports
- **Access**: Public, free
- **Format**: USDA reports
- **Script**: `scripts/ingest/collect_sunflower_oil_trade.py`

#### D. Rapeseed/Canola Oil
- **Source**: ICE/Euronext futures
- **Data**: Futures prices
- **Access**: Public prices
- **Format**: Yahoo Finance (already collecting)
- **Script**: Add to Yahoo Finance symbol list

#### E. Corn Oil (Distillers Oil)
- **Source**: USDA ERS, Ethanol production data
- **Data**: Corn oil production from ethanol plants
- **Access**: Public, free
- **Format**: USDA reports
- **Script**: `scripts/ingest/collect_corn_oil_production.py`

---

## 📊 PRIORITY MATRIX

| Data Source | Priority | Effort | Availability | Action |
|------------|----------|--------|--------------|--------|
| USDA FAS China Imports | P0 | Low | ✅ Free | Start immediately |
| Dalian Futures | P0 | Medium | ✅ Free | Start immediately |
| USTR Tariffs | P0 | Medium | ✅ Free | Start immediately |
| Federal Register | P0 | Low | ✅ Free API | Start immediately |
| EPA RIN Prices | P1 | Low | ✅ Free | Start after P0 |
| CARB LCFS | P1 | Medium | ✅ Free | Start after P0 |
| MPOB Palm Oil | P1 | Medium | ✅ Free | Start after P0 |
| China Reserve News | P0 | Medium | ✅ ScrapeCreators | Start immediately |

---

## 🎯 IMMEDIATE ACTION ITEMS

1. **Start with Free, Public Sources**:
   - USDA FAS China imports
   - USTR/Federal Register tariffs
   - EPA RIN prices
   - MPOB palm oil

2. **Use Existing Tools**:
   - ScrapeCreators for news scraping (China reserves, trade deals)
   - Yahoo Finance for futures prices (Dalian, palm oil, rapeseed)

3. **Build Scripts**:
   - Create collection scripts for each source
   - Test with recent data first
   - Expand to full historical collection

---

**Next Steps**: Start building collection scripts for P0 sources (USDA FAS, USTR, Federal Register).

