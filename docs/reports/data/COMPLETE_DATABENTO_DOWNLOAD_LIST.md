# 🔥 COMPLETE DATABENTO HISTORICAL DOWNLOAD - FULL REQUIREMENTS
**Date:** November 20, 2025  
**Status:** ALL HISTORICAL DATA NEEDED  
**User Directive:** "we need it all"

---

## ✅ VERIFICATION COMPLETE

All existing Databento JSON files are **readable and valid**:
- ✅ MES daily: 9,034 records (2019-2025)
- ✅ MES 1-minute: 44,594 records in sample file
- ✅ ZL daily: 224,626 records (2010-2025, all contracts + spreads)
- ✅ ZL 1-hour: ~4,000 files (2010-2025)

---

## 📦 COMPLETE DOWNLOAD LIST (26 SYMBOLS)

### **TIER 1: CRITICAL - SOY COMPLEX & CORE INDICES**

| Symbol | Description | Exchange | Timeframes | Date Range | Priority | Est. Size |
|--------|-------------|----------|------------|------------|----------|-----------|
| **ZL** | Soybean Oil | CBOT | **1-minute**, daily | 2010-2025 | **CRITICAL** | ~2-3 GB |
| **ZS** | Soybeans | CBOT | **1-minute**, daily | 2010-2025 | **CRITICAL** | ~2-3 GB |
| **ZM** | Soybean Meal | CBOT | **1-minute**, daily | 2010-2025 | **CRITICAL** | ~2 GB |
| **ES** | E-mini S&P 500 | CME | daily | 2010-2025 | **CRITICAL** | ~3 MB |

**Why Critical:**
- ZL: Primary asset, need microstructure features
- ZS/ZM: Crush spread calculation (essential ZL feature)
- ES: Market regime classification and reference

**Total Tier 1:** ~7.5 GB

---

### **TIER 2: HIGH PRIORITY - ENERGY COMPLEX**

| Symbol | Description | Exchange | Timeframes | Date Range | Purpose |
|--------|-------------|----------|------------|------------|---------|
| **CL** | WTI Crude Oil | NYMEX | daily | 2010-2025 | Biodiesel input cost |
| **HO** | Heating Oil (ULSD) | NYMEX | daily | 2010-2025 | Biodiesel blend economics |
| **NG** | Natural Gas | NYMEX | daily | 2010-2025 | Fertilizer cost proxy |
| **RB** | RBOB Gasoline | NYMEX | daily | 2010-2025 | Ethanol blend economics |

**Total Tier 2:** ~20 MB

---

### **TIER 3: HIGH PRIORITY - GRAINS**

| Symbol | Description | Exchange | Timeframes | Date Range | Purpose |
|--------|-------------|----------|------------|------------|---------|
| **ZC** | Corn | CBOT | daily | 2010-2025 | Competing crop, ag breadth |
| **ZW** | Wheat | CBOT | daily | 2010-2025 | Ag complex breadth |

**Total Tier 3:** ~10 MB

---

### **TIER 4: IMPORTANT - ADDITIONAL INDICES**

| Symbol | Description | Exchange | Timeframes | Date Range | Purpose |
|--------|-------------|----------|------------|------------|---------|
| **NQ** | E-mini Nasdaq-100 | CME | daily | 2010-2025 | Tech sector risk |
| **MNQ** | Micro Nasdaq | CME | daily | 2019-2025 | Micro equity context |
| **RTY** | E-mini Russell 2000 | CME | daily | 2010-2025 | Small cap risk |
| **M2K** | Micro Russell | CME | daily | 2019-2025 | Micro equity context |

**Total Tier 4:** ~15 MB

---

### **TIER 5: IMPORTANT - METALS**

| Symbol | Description | Exchange | Timeframes | Date Range | Purpose |
|--------|-------------|----------|------------|------------|---------|
| **GC** | Gold | COMEX | daily | 2010-2025 | Safe haven, inflation |
| **SI** | Silver | COMEX | daily | 2010-2025 | Industrial metals |
| **HG** | Copper | COMEX | daily | 2010-2025 | Economic activity |

**Total Tier 5:** ~15 MB

---

### **TIER 6: ADDITIONAL COVERAGE - COMPLETE UNIVERSE**

| Symbol | Description | Exchange | Timeframes | Date Range | Purpose |
|--------|-------------|----------|------------|------------|---------|
| **BZ** | Brent Crude | NYMEX | daily | 2010-2025 | International energy |
| **QM** | E-mini Crude | NYMEX | daily | 2010-2025 | Mini energy futures |
| **PA** | Palladium | COMEX | daily | 2010-2025 | Precious metals |
| **PL** | Platinum | COMEX | daily | 2010-2025 | Precious metals |
| **ZR** | Rough Rice | CBOT | daily | 2010-2025 | Ag breadth |
| **ZO** | Oats | CBOT | daily | 2010-2025 | Ag breadth |
| **LE** | Live Cattle | CME | daily | 2010-2025 | Livestock |
| **GF** | Feeder Cattle | CME | daily | 2010-2025 | Livestock |
| **HE** | Lean Hogs | CME | daily | 2010-2025 | Livestock |

**Total Tier 6:** ~40 MB

---

## 📊 DOWNLOAD SUMMARY

| Category | Symbols | Timeframes | Est. Total Size |
|----------|---------|------------|-----------------|
| **1-minute bars** | ZL, ZS, ZM | 2010-2025 (15 years) | ~7-8 GB |
| **Daily bars** | 23 symbols | 2010-2025 (15 years) | ~100 MB |
| **GRAND TOTAL** | **26 symbols** | **Mixed** | **~8-10 GB** |

---

## ✅ ALREADY HAVE (NO NEED TO DOWNLOAD)

### MES (Micro E-mini S&P 500) - COMPLETE ✅
- ✅ Daily: 2019-04-14 to 2025-11-16 (raw JSON)
- ✅ 1-Hour: 2019-04-14 to 2025-11-16 (98 files)
- ✅ 1-Minute: 2019-04-14 to 2025-11-16 (98 files, 722 MB)

### ZL (Soybean Oil) - PARTIAL ⚠️
- ✅ Daily: 2010-06-06 to 2025-11-17 (48 MB, 224K records)
- ✅ 1-Hour: 2010-06-06 to 2025-11-17 (413 MB, ~4K files)
- ❌ 1-Minute: **NOT DOWNLOADED** (need this!)

### FX Futures - COMPLETE ✅
- ✅ 6E, 6A, 6B, 6C, 6J, 6L, CNH daily (2010-2025)
- Already processed into parquet files

---

## 🌦️ WEATHER SEGMENTATIONS - ORGANIZED

Weather data is now properly segmented by region. Each region has its own home:

### US Midwest (11 stations)
**Location:** `/TrainingData/raw/noaa/regional/`
- Illinois, Iowa, Indiana, Nebraska, Ohio, Missouri, Michigan, Wisconsin, Minnesota, South Dakota, North Dakota
- **Status:** ✅ Complete (337 KB combined file)
- **Columns:** `weather_us_{state}_{variable}`

### Brazil (5 key states)
**Location:** `/TrainingData/raw/brazil_weather/`
- Mato Grosso, Mato Grosso do Sul, Rio Grande do Sul, Paraná, Goiás
- **Status:** ✅ Complete (14 KB Brazil daily)
- **Columns:** `weather_br_{region}_{variable}`

### Argentina (3 key regions)
**Location:** `/TrainingData/raw/brazil_weather/`
- Buenos Aires, Córdoba, Santa Fe
- **Status:** ✅ Complete (7.5 KB Argentina daily)
- **Columns:** `weather_ar_{region}_{variable}`

### Combined/Staging
**Location:** `/TrainingData/staging/`
- `weather_granular.parquet` - 995 KB (all regions wide format)
- `noaa_weather_2000_2025.parquet` - Link to weather file
- **Status:** ✅ Ready for BigQuery load

**Weather is READY - no additional downloads needed!** ✅

---

## 🚀 EXECUTION SCRIPT CREATED

**Script:** `scripts/ingest/download_ALL_databento_historical.py`

### What It Does:
1. Downloads ALL 26 symbols from Databento
2. Organized by priority tiers (1-6)
3. Automatic job submission and tracking
4. Saves job IDs for monitoring
5. Provides clear next steps

### How to Run:
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14

# Make executable
chmod +x scripts/ingest/download_ALL_databento_historical.py

# Run it
python3 scripts/ingest/download_ALL_databento_historical.py
```

### What It Downloads:
- ✅ Tier 1: ZL/ZS/ZM 1-min + ES daily (~7.5 GB)
- ✅ Tier 2: Energy complex daily (CL, HO, NG, RB) (~20 MB)
- ✅ Tier 3: Grains daily (ZC, ZW) (~10 MB)
- ✅ Tier 4: Indices daily (NQ, MNQ, RTY, M2K) (~15 MB)
- ✅ Tier 5: Metals daily (GC, SI, HG) (~15 MB)
- ✅ Tier 6: Additional (BZ, QM, PA, PL, ZR, ZO, LE, GF, HE) (~40 MB)

---

## 📋 POST-DOWNLOAD CHECKLIST

After downloads complete:

### 1. Verify Downloads
```bash
# Check all directories created
ls -lh /Volumes/Satechi\ Hub/Projects/CBI-V14/TrainingData/raw/databento_*
```

### 2. Extract Files
```bash
# Databento downloads come as ZIP files
# Extract to appropriate directories
```

### 3. Load to BigQuery
```bash
python3 scripts/ingest/load_databento_to_bigquery.py
```

### 4. Verify BigQuery Tables
```bash
bq query --use_legacy_sql=false "
SELECT 
  root,
  COUNT(*) as records,
  MIN(date) as min_date,
  MAX(date) as max_date
FROM \`cbi-v14.market_data.databento_futures_ohlcv_1d\`
GROUP BY root
ORDER BY root
"
```

### 5. Build Master Features
```bash
python3 scripts/features/build_master_features.py
```

### 6. Verify Master Features
```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) as total_rows 
FROM \`cbi-v14.features.master_features\`
"
```

---

## 💰 COST BREAKDOWN

### Databento Historical Downloads
- **Cost:** $0.00 ✅
- **Why:** Included in your CME Globex MDP 3.0 Standard plan
- **Coverage:** All historical data from 2010-06-06 to present
- **No extra charges** for historical backfills

### Storage (External Drive)
- **Current Usage:** ~2 GB (MES + ZL partial + FX + weather)
- **After ALL downloads:** ~10-12 GB total
- **External Drive:** 256 GB available (plenty of space)

### BigQuery Storage
- **Current:** 0 rows in databento tables
- **After load:** ~5-10 GB estimated
- **Cost:** Still under free tier (10 GB free)

---

## 🎯 IMMEDIATE NEXT STEPS

### Step 1: Load Existing Data to BigQuery (NOW)
Before downloading more data, load what we already have:
```bash
# Load existing ZL daily + MES all timeframes
python3 scripts/ingest/load_existing_databento_to_bq.py
```

### Step 2: Run Complete Download (After Step 1)
```bash
python3 scripts/ingest/download_ALL_databento_historical.py
```

### Step 3: Monitor Jobs
- Visit: https://databento.com/portal/batch/jobs
- Track completion of all 30+ jobs
- Download when ready

### Step 4: Extract and Load
```bash
# Extract all ZIP files to appropriate directories
# Then load to BigQuery
python3 scripts/ingest/load_databento_to_bigquery.py
```

### Step 5: Verify and Build Features
```bash
# Verify all data loaded
python3 scripts/validation/verify_databento_coverage.py

# Build master features
python3 scripts/features/build_master_features.py
```

---

## ✅ FINAL SUMMARY

### What We Have:
- ✅ MES: Complete (all timeframes)
- ✅ ZL: Daily + 1-hour (missing 1-minute)
- ✅ FX: All 7 pairs daily
- ✅ Weather: All regions segmented and ready

### What We Need:
- ❌ ZL 1-minute (highest priority)
- ❌ ZS 1-minute + daily
- ❌ ZM 1-minute + daily
- ❌ ES daily
- ❌ Energy complex (CL, HO, NG, RB, BZ, QM)
- ❌ Grains (ZC, ZW, ZR, ZO)
- ❌ Indices (NQ, MNQ, RTY, M2K)
- ❌ Metals (GC, SI, HG, PA, PL)
- ❌ Livestock (LE, GF, HE)

### Total Missing:
- **26 symbols** (some with multiple timeframes)
- **~8-10 GB** total estimated
- **All included** in Databento plan (no extra cost)

### Weather Status:
- **✅ COMPLETE** - All regions segmented into their own homes
- **✅ READY** - Staged for BigQuery load
- **No additional downloads needed**

---

**READY TO EXECUTE: Run the download script to get ALL historical data!** 🚀









