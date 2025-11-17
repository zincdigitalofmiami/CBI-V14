# 📊 DATA SOURCES IMPLEMENTATION STATUS
**Date**: November 16, 2025  
**Status**: Scripts Created, Testing Required

---

## ✅ SCRIPTS CREATED & READY FOR TESTING

### 1. UN Comtrade - China Soybean Imports ✅
- **Script**: `scripts/ingest/collect_un_comtrade.py`
- **Endpoint**: `https://comtrade.un.org/api/get`
- **Coverage**: 2000→present (25 years)
- **Status**: ⚠️ API may require registration (returns HTML)
- **Action**: Test with registered API key or use alternative endpoint

### 2. USDA FAS ESR - Weekly Export Sales ✅
- **Script**: `scripts/ingest/collect_usda_fas_esr.py`
- **Pages**: 
  - Soybeans: `https://apps.fas.usda.gov/export-sales/h801.htm`
  - Soybean Oil: `https://apps.fas.usda.gov/export-sales/h902.htm`
- **Coverage**: 25+ years (weekly)
- **Status**: Ready to test HTML scraping
- **Action**: Test scraping actual page structure

### 3. EPA EMTS RIN Prices ✅
- **Script**: `scripts/ingest/collect_epa_rin_prices.py`
- **Source**: EPA EMTS Transparency dashboard
- **Coverage**: 2010→present (weekly)
- **Status**: Ready to test CSV export
- **Action**: Verify CSV export URL/format

### 4. World Bank Pink Sheet ✅
- **Script**: `scripts/ingest/collect_worldbank_pinksheet.py`
- **URL**: World Bank CMO Historical Data Monthly XLSX
- **Coverage**: 1960s→present (monthly)
- **Status**: Ready to test XLSX download
- **Action**: Test download and sheet parsing

---

## 🎯 REMAINING PRIORITY SOURCES TO IMPLEMENT

### High Priority (China Demand Composite)
1. **DCE vs CBOT Basis Spread**
   - DCE: Scrape `https://www.dce.com.cn/dceg/` historical data
   - CBOT: CME Market Data API (licensed) or Nasdaq Data Link
   - **Coverage**: ~2000→present (daily)

2. **State Reserve Actions**
   - Sinograin: `http://www.sinograin.com.cn/xwzx/`
   - COFCO: `https://www.cofco.com/en/News/`
   - **Coverage**: ~10 years online, supplement with GDELT

3. **China Crush Margins**
   - Compute from DCE M/Y contracts + CBOT + FX
   - **Coverage**: Mid-2000s→present

4. **MARA Hog Inventory**
   - Scrape MARA "生猪专题" pages
   - **Coverage**: Monthly from 2010s, quarterly/annual earlier

5. **ASF Outbreak Severity**
   - WOAH WAHIS + FAO EMPRES-i
   - **Coverage**: China 2018→present

### Medium Priority (Tariff Intelligence)
1. **Federal Register Section 301**
   - Scrape FR notices with effective dates
   - **Coverage**: 2018→present

2. **MOFCOM Retaliation Lists**
   - Scrape Chinese announcements
   - **Coverage**: 2018→present

### Medium Priority (Biofuel Policy)
1. **EIA Biodiesel/Renewable Diesel**
   - EIA Open Data API v1
   - **Coverage**: Biodiesel 2001→present, Renewable 2013→present

2. **CARB LCFS Credits**
   - Scrape weekly XLSX from CARB
   - **Coverage**: 2019→present

3. **Oregon CFP Credits**
   - Scrape monthly reports from DEQ
   - **Coverage**: 2016/2017→present

### Lower Priority (Substitute Oils)
1. **USDA AMS Distillers Corn Oil**
   - Scrape weekly PDFs or use MyMarketNews API
   - **Coverage**: Weekly from 2010s

---

## 📋 TESTING CHECKLIST

Before committing any script to production:

- [ ] **UN Comtrade**: Test API with registration or find alternative endpoint
- [ ] **USDA FAS ESR**: Test HTML scraping, verify table structure
- [ ] **EPA RIN**: Test CSV export, verify column names
- [ ] **World Bank Pink Sheet**: Test XLSX download, verify sheet names
- [ ] **Data Quality**: Verify no BQ contamination, proper date formats
- [ ] **Date Ranges**: Confirm coverage matches expectations
- [ ] **Error Handling**: Test with invalid inputs, rate limits
- [ ] **Output Format**: Verify parquet files load correctly

---

## 🚨 KNOWN ISSUES

1. **UN Comtrade API**: Returns HTML instead of JSON (may require registration)
   - **Solution**: Register for API access or use alternative endpoint
   - **Alternative**: Use China Customs Statistics web scraping

2. **DCE/CBOT Data**: Requires licensed access or vendor feed
   - **Solution**: Use Nasdaq Data Link CHRIS or license CME
   - **Alternative**: Compute monthly spreads from World Bank Pink Sheet

3. **Historical Coverage**: Not all sources have full 25-year history
   - **Solution**: Document actual coverage, use monthly proxies where needed
   - **Strategy**: Use World Bank monthly for long-run spreads

---

## 📊 COVERAGE SUMMARY

### What's Available from Sources (Not Necessarily Collected)

| Source | Daily | Monthly | Available Coverage | 25-Year? | Status |
|--------|-------|---------|-------------------|----------|--------|
| UN Comtrade (China imports) | - | ✅ | 2000→present | ✅ Yes | ❌ Not usable (needs registration) |
| USDA FAS ESR (weekly) | - | - | 25+ years | ✅ Yes | ⚠️ Aggregate only (not China-specific) |
| World Bank Pink Sheet | - | ✅ | 1960s→present | ✅ Yes | ⏳ Script ready, needs testing |
| EPA RIN Prices | - | - | 2010→present | ❌ No (~15y) | ⚠️ Manual download required |
| EIA Biodiesel | - | ✅ | 2001→present | ✅ Near (24y) | ❌ **NOT COLLECTED** (file has gasoline only) |
| EIA Renewable Diesel | - | ✅ | 2013→present | ❌ No (~12y) | ❌ **NOT COLLECTED** |
| DCE/CBOT Basis | ✅ | ✅ | ~2000→present | ✅ Yes | ⏳ Needs licensed access |
| MARA Hogs | - | ✅ | 2010s monthly, earlier quarterly | ⚠️ Partial | ⏳ Not collected |
| ASF Severity | - | - | 2018→present | ❌ No | ⏳ Not collected |
| Section 301 Tariffs | - | - | 2018→present | ❌ No | ⏳ Not collected |

### What We've Actually Collected

| Source | Records | Date Range | Status |
|--------|---------|------------|--------|
| Weather | 37,808 | 2000-2025 | ✅ Collected & Clean |
| Yahoo Finance | 6,380 | 2000-2025 | ✅ Collected & Clean |
| FRED | 103,029 | 2000-2025 | ✅ Collected & Clean |
| EIA | 1,702 | 1993-2025 | ⚠️ **Gasoline only** (NOT biodiesel) |
| CFTC COT | - | - | ❌ Contaminated (needs replacement) |
| USDA Agricultural | - | - | ❌ Contaminated (needs replacement) |

---

## 🎯 NEXT STEPS

1. **Test existing scripts** with small date ranges
2. **Fix API issues** (registration, endpoints)
3. **Implement remaining high-priority sources**
4. **Set up daily/weekly update schedules**
5. **Create conformance scripts** for all new data

---

## 📝 NOTES

- All scripts follow the same pattern: raw → staging → features
- Quarantine logic in place for invalid data
- Date standardization handled in conformance step
- No BigQuery contamination in new scripts
