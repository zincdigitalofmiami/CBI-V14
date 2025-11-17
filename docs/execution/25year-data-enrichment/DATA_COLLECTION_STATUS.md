# 📊 DATA COLLECTION STATUS & ORGANIZATION
**Date**: November 16, 2025  
**Status**: Organizing & Verifying Quality

---

## ✅ SUCCESSFULLY COLLECTED & CLEAN

### 1. Weather Data ✅
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging/weather_2000_2025.parquet`
- **Records**: 37,808 
- **Coverage**: US Midwest, Brazil, Argentina (2000-2025)
- **Source**: NASA POWER (institutional-grade)
- **Quality**: Clean, no BQ contamination
- **Status**: Current (updated to Nov 16, 2025)

### 2. Yahoo Finance ✅
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/yahoo_finance/`
- **Symbols**: 74/79 collected
- **Categories**: Commodities, Indices, Currencies, ETFs
- **Quality**: Clean, proper date formatting
- **Status**: 2 days behind (updating in background)

### 3. FRED Economic Data ✅
- **Location**: `/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw/fred/combined/`
- **Series**: 16 collected
- **Quality**: Clean, current
- **Status**: Updated to Nov 16, 2025

---

## ⚠️ DATA WITH ISSUES (BQ Contamination)

### 1. CFTC COT Data ❌
- **Issue**: BigQuery contamination (dbdate types)
- **Files**: 
  - `staging/cftc_cot.parquet` - CONTAMINATED
  - `forecasting_data_warehouse/cftc_cot.parquet` - CONTAMINATED
- **Solution**: Re-collect from official CFTC sources

### 2. USDA Data ❌
- **Issue**: BigQuery contamination (dbdate types)
- **Files**:
  - `staging/usda_export_sales.parquet` - CONTAMINATED
  - `staging/usda_harvest_progress.parquet` - CONTAMINATED
  - `forecasting_data_warehouse/usda_wasde_soy.parquet` - EMPTY
- **Solution**: Re-collect from official USDA sources

### 3. EIA Biofuel Data ⚠️
- **Status**: Some files exist but need verification
- **Files**: 
  - `eia/processed/PET_EMM_EPM0_PTE_NUS_DPG_W.parquet`
  - `eia/combined/eia_all_20251116.parquet`
- **Solution**: Verify quality, re-collect if needed

---

## 🎯 GAPS TO FILL (New Sources Provided)

### Priority 1: China Demand Composite
1. **UN Comtrade API** - Monthly soy imports (HS 1201)
2. **USDA FAS ESR** - Weekly export sales to China
3. **DCE vs CBOT** - Dalian basis spread
4. **Sinograin/COFCO** - State reserve actions
5. **DCE Crush Margins** - A/M/Y contracts
6. **MARA Hog Data** - Monthly inventory
7. **FAO EMPRES** - ASF outbreak severity
8. **Customs Tariff** - China tariff timeline

### Priority 2: Tariff Intelligence
1. **FederalRegister.gov** - Section 301 notices
2. **USTR** - Trade deal milestones
3. **MOFCOM** - China retaliation schedules

### Priority 3: Biofuel Policy
1. **EIA API v2** - Biodiesel/renewable diesel
2. **EPA EMTS** - RIN prices (D4/D5/D6)
3. **CARB LCFS** - California credit prices
4. **Oregon DEQ** - Oregon credit prices

### Priority 4: Substitute Oils
1. **World Bank Pink Sheet** - Monthly FOB prices
2. **MPOB** - Palm oil statistics
3. **UN Comtrade** - Sunflower oil exports
4. **USDA AMS** - Distillers corn oil

---

## 📁 DIRECTORY ORGANIZATION

```
/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/
├── raw/                          # Immutable source zone
│   ├── yahoo_finance/           ✅ Clean
│   ├── fred/                    ✅ Clean
│   ├── weather/                 ✅ Clean (in staging)
│   ├── cftc/                    ❌ Needs replacement
│   ├── usda/                    ❌ Needs replacement
│   ├── eia/                     ⚠️ Needs verification
│   ├── china_trade/             🆕 To add (Comtrade)
│   ├── usda_fas_esr/           🆕 To add (Weekly ESR)
│   ├── dce_quotes/             🆕 To add (Dalian)
│   ├── tariffs_us/             🆕 To add (FR/USTR)
│   ├── tariffs_cn/             🆕 To add (MOFCOM)
│   ├── biofuels_eia/           🆕 To add (EIA API v2)
│   ├── rins_epa/               🆕 To add (EMTS)
│   ├── lcfs_carb/              🆕 To add (California)
│   ├── wb_pinksheet/           🆕 To add (World Bank)
│   └── usda_ams_energy/        🆕 To add (DCO prices)
├── staging/                     # Validated, conformed
│   ├── weather_2000_2025.parquet  ✅ Ready
│   └── [others to be conformed]
├── features/                    # Engineered signals
├── labels/                      # Forward targets
└── exports/                     # Final training sets

```

---

## 🚀 NEXT STEPS

1. **Clean house**: Remove all BQ-contaminated files
2. **Implement priority sources**: Start with China Demand Composite
3. **Test each source**: Verify data quality before committing
4. **Daily updates**: Set up automated daily refresh

---

## 📊 QUALITY METRICS

| Source | Records | Date Range | Quality | Status |
|--------|---------|------------|---------|--------|
| Weather | 37,808 | 2000-2025 | ✅ Clean | Current |
| Yahoo Finance | 74 symbols | 2000-2025 | ✅ Clean | Updating |
| FRED | 16 series | 2000-2025 | ✅ Clean | Current |
| CFTC | TBD | - | ❌ Contaminated | Replace |
| USDA | TBD | - | ❌ Contaminated | Replace |
| EIA | TBD | - | ⚠️ Verify | Check |
