# Remaining NULLs Analysis & Recommendations

**Date:** 2025-11-03  
**Dataset:** `cbi-v14.models_v4.training_dataset_super_enriched`  
**Total Rows:** 2,043

---

## ✅ SUCCESSFULLY FIXED (Remove from EXCEPT clause)

| Column | Before | After | Status |
|--------|--------|-------|--------|
| `soybean_meal_price` | 28.17% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `unemployment_rate` | 96.48% NULL | **3% NULL** | ✅ REMOVE FROM EXCEPT |
| `treasury_10y_yield` | 28.7% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `usd_cny_rate` | 38.83% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `palm_price` | 38.39% NULL | **0.8% NULL** | ✅ REMOVE FROM EXCEPT |
| `zl_price_current` | 28.17% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `corn_price` | 38.83% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `wheat_price` | 38.83% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `vix_level` | 38.53% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |
| `dollar_index` | 38.83% NULL | **0% NULL** | ✅ REMOVE FROM EXCEPT |

---

## ❌ STILL 99.56% NULL (9 Columns - KEEP IN EXCEPT)

### Economic Data (3 columns)

| Column | NULL Count | Coverage | Data Source Status |
|--------|-----------|----------|-------------------|
| `cpi_yoy` | 2,034/2,043 | 0.4% | ❌ CPIAUCSL only has 10 monthly records (Nov 2024-Aug 2025) |
| `econ_gdp_growth` | 2,034/2,043 | 0.4% | ❌ GDPC1 data NOT in economic_indicators table |
| `gdp_growth` | 2,034/2,043 | 0.4% | ❌ GDPC1 data NOT in economic_indicators table |

**Analysis:**
- CPI data exists but only 10 monthly records (very limited)
- GDP data needs to be **fetched from FRED API** using `scripts/fetch_fred_economic_data.py`
- FRED API key is **working** (tested successfully)

**Recommendation:** 
- **Option A:** Run `scripts/fetch_fred_economic_data.py` to fetch GDPC1 from FRED API, then populate
- **Option B:** Accept these will be NULL and keep in EXCEPT clause

### US Midwest Weather (6 columns)

| Column | NULL Count | Coverage | Data Source Status |
|--------|-----------|----------|-------------------|
| `us_midwest_temp_c` | 1,998/2,043 | 2.2% | ⚠️ Only 45 records (2025-09-20 to 2025-11-02) |
| `us_midwest_precip_mm` | 1,998/2,043 | 2.2% | ⚠️ Only 45 records (2025-09-20 to 2025-11-02) |
| `us_midwest_conditions_score` | 1,998/2,043 | 2.2% | ⚠️ Calculated from temp/precip |
| `us_midwest_heat_stress_days` | 1,998/2,043 | 2.2% | ⚠️ Calculated from temp |
| `us_midwest_drought_days` | 1,998/2,043 | 2.2% | ⚠️ Calculated from temp/precip |
| `us_midwest_flood_days` | 1,998/2,043 | 2.2% | ⚠️ Calculated from precip |

**Analysis:**
- `weather_data` table has US_Midwest data but **only 45 records** (recent dates only)
- Data starts 2025-09-20 (missing 2,000+ earlier dates)
- Cannot forward-fill backward effectively (no historical data)

**Recommendation:**
- **Option A:** Keep in EXCEPT clause (recommended - data doesn't exist historically)
- **Option B:** Use NOAA API or another weather source to fetch historical data
- **Option C:** Accept BQML will impute these (acceptable for training)

---

## 📊 UPDATED EXCEPT CLAUSE RECOMMENDATION

### Current EXCEPT Clause (Before Fixes):
```sql
SELECT * EXCEPT(
  date, 
  treasury_10y_yield,      -- ❌ REMOVE (now 100% filled)
  econ_gdp_growth,         -- ✅ KEEP (99.56% NULL)
  econ_unemployment_rate,  -- ❌ REMOVE (now 97% filled - acceptable)
  us_midwest_temp_c,       -- ✅ KEEP (97.8% NULL)
  us_midwest_precip_mm,    -- ✅ KEEP (97.8% NULL)
  news_article_count       -- ✅ KEEP (if still 99%+ NULL)
)
```

### Recommended EXCEPT Clause (After Fixes):
```sql
SELECT * EXCEPT(
  date,
  -- Economic data (need FRED API fetch)
  cpi_yoy,                    -- 99.56% NULL - needs FRED API
  econ_gdp_growth,            -- 99.56% NULL - needs FRED API
  gdp_growth,                 -- 99.56% NULL - needs FRED API
  -- US Midwest weather (no historical data)
  us_midwest_temp_c,          -- 97.8% NULL - no historical data
  us_midwest_precip_mm,       -- 97.8% NULL - no historical data
  us_midwest_conditions_score,-- 97.8% NULL - derived from temp/precip
  us_midwest_heat_stress_days,-- 97.8% NULL - derived from temp
  us_midwest_drought_days,    -- 97.8% NULL - derived from temp/precip
  us_midwest_flood_days,      -- 97.8% NULL - derived from precip
  -- Other high-NULL columns (if applicable)
  news_article_count,         -- Check if still 99%+ NULL
  cftc_commercial_long,       -- 97.07% NULL (from original audit)
  cftc_commercial_short,      -- 97.07% NULL
  cftc_commercial_net,         -- 97.07% NULL
  cftc_managed_long,          -- 97.07% NULL
  cftc_managed_short,         -- 97.07% NULL
  cftc_managed_net,           -- 97.07% NULL
  cftc_open_interest          -- 97.07% NULL
)
```

---

## 🎯 RECOMMENDED ACTION PLAN

### Option 1: Train NOW (Recommended) ✅
**Pros:**
- All critical features are 95%+ covered
- Can train immediately
- BQML will handle remaining NULLs (imputation)
- GDP/CPI/Weather are supplementary features

**Cons:**
- Missing economic growth features
- Missing US Midwest weather features

**Action:**
- Update EXCEPT clause to remove fixed columns
- Keep 9 high-NULL columns in EXCEPT
- Proceed with training

### Option 2: Fill NULLs First (1-2 hours)
**Pros:**
- More complete dataset
- GDP/CPI features available

**Cons:**
- Requires FRED API fetch (GDPC1)
- US Midwest weather still can't be filled (no historical data)
- Delays training

**Action:**
1. Run `scripts/fetch_fred_economic_data.py` to fetch GDPC1
2. Calculate GDP growth from GDPC1
3. Forward-fill GDP to daily
4. Still keep US Midwest weather in EXCEPT (data doesn't exist)

### Option 3: Accept Current State
**Pros:**
- No additional work
- Current state is acceptable

**Cons:**
- Missing some features

**Action:**
- Keep all 9 columns in EXCEPT
- Proceed with training

---

## 📋 SUMMARY

**What We Fixed:**
- ✅ 10 columns went from 28-96% NULL to 0-3% NULL
- ✅ Removed duplicate dates
- ✅ Fixed invalid values
- ✅ Treasury 10Y: 100% coverage
- ✅ USD/CNY: 100% coverage
- ✅ Palm Price: 99.2% coverage

**What Remains:**
- ❌ 3 Economic columns (99.56% NULL) - need FRED API fetch
- ❌ 6 US Midwest weather columns (97.8% NULL) - no historical data exists

**Recommendation:** **Train NOW** - The 9 remaining columns are supplementary features. BQML can handle NULLs via imputation, and you have all critical price/volume/economic indicators at 95%+ coverage.

---

## 🚀 NEXT STEPS

1. **Update training SQL** - Remove fixed columns from EXCEPT clause
2. **Proceed with training** - Dataset is ready
3. **Optional:** Fetch GDP data from FRED API later if needed


