# NULL ELIMINATION STRATEGY - 41 HIGH-NULL COLUMNS

## NULL CATEGORIES & DATA SOURCES

### 🔴 CATEGORY 1: ECONOMIC DATA (7 columns - 96-99% NULL)
- `cpi_yoy` (99.46% NULL)
- `econ_gdp_growth` (99.46% NULL) 
- `gdp_growth` (99.46% NULL)
- `unemployment_rate` (99.46% NULL)
- `econ_inflation_rate` (99.12% NULL)
- `econ_unemployment_rate` (96.48% NULL)
- `cftc_*` (7 columns, 97.07% NULL)

**Data Sources:**
- ✅ FRED API (we have yfinance as fallback)
- ✅ Alpha Vantage (key: BA7CQWXKRFBNFY49)
- ✅ Calculate from existing data (interpolation)

### 🔴 CATEGORY 2: US MIDWEST WEATHER (6 columns - 99.46% NULL)
- `us_midwest_temp_c`
- `us_midwest_precip_mm`
- `us_midwest_conditions_score`
- `us_midwest_heat_stress_days`
- `us_midwest_drought_days`
- `us_midwest_flood_days`

**Data Sources:**
- ✅ NOAA API (need token)
- ✅ Calculate from existing weather data
- ✅ Use social intelligence as proxy (Twitter/Facebook farmer reports)

### 🔴 CATEGORY 3: BRAZIL WEATHER (6 columns - 50.66% NULL)
- `brazil_temp_c`
- `brazil_precip_mm`
- `brazil_conditions_score`
- `brazil_heat_stress_days`
- `brazil_drought_days`
- `brazil_flood_days`

**Data Sources:**
- ✅ We have `weather_brazil_temp`, `weather_brazil_precip` columns
- ✅ Map/copy from existing columns
- ✅ Calculate conditions_score from temp+precip

### 🔴 CATEGORY 4: ARGENTINA WEATHER (6 columns - 66-86% NULL)
- `argentina_temp_c` (86.60% NULL)
- `argentina_precip_mm` (85.62% NULL)
- `argentina_conditions_score` (66.89% NULL)
- `argentina_heat_stress_days` (66.89% NULL)
- `argentina_drought_days` (66.89% NULL)
- `argentina_flood_days` (66.89% NULL)

**Data Sources:**
- ✅ We have `weather_argentina_temp` column
- ✅ Map/copy from existing columns
- ✅ Calculate derived features

### 🔴 CATEGORY 5: NEWS/SENTIMENT (2 columns - 99.80% NULL)
- `news_article_count`
- `news_avg_score`

**Data Sources:**
- ✅ We have `news_*` tables already
- ✅ Query and aggregate from existing news tables
- ✅ Calculate from social_sentiment table

### 🔴 CATEGORY 6: TRUMP INTELLIGENCE (5 columns - 98-99% NULL)
- `trump_soybean_sentiment_7d` (99.66% NULL)
- `trump_agricultural_impact_30d` (98.39% NULL)
- `trump_soybean_relevance_30d` (98.39% NULL)
- `days_since_trump_policy` (98.39% NULL)
- `trump_policy_intensity_14d` (98.39% NULL)

**Data Sources:**
- ✅ ScrapeCreators Twitter API (Trump handles)
- ✅ Parse and calculate from collected tweets
- ✅ Historical: use existing backfill_trump_intelligence.py

### 🔴 CATEGORY 7: SOCIAL SENTIMENT (1 column - 99.02% NULL)
- `social_sentiment_momentum_7d`

**Data Sources:**
- ✅ Use existing social_sentiment table
- ✅ Calculate rolling 7-day momentum

### 🔴 CATEGORY 8: GLOBAL WEATHER (1 column - 50.66% NULL)
- `global_weather_risk_score`

**Data Sources:**
- ✅ Calculate from brazil + argentina + us_midwest weather
- ✅ Composite score

### 🔴 CATEGORY 9: RETURN DATA (1 column - 51.59% NULL)
- `return_1d`

**Data Sources:**
- ✅ Calculate from zl_price_current: (price - lag(price)) / lag(price)

---

## EXECUTION PLAN

### Step 1: IMMEDIATE FIXES (Calculate from Existing Data - No API needed)
**Columns:** 15-20 columns can be filled from existing data

**Actions:**
1. Copy `weather_brazil_temp` → `brazil_temp_c`
2. Copy `weather_argentina_temp` → `argentina_temp_c`
3. Calculate `return_1d` from `zl_price_current`
4. Calculate `global_weather_risk_score` from regional weather
5. Calculate weather `conditions_score`, `heat_stress_days`, etc from temp+precip
6. Aggregate `news_article_count`, `news_avg_score` from existing news tables

**Script:** `scripts/backfill_from_existing_data.py`

### Step 2: FETCH ECONOMIC DATA (FRED/Alpha Vantage/yfinance)
**Columns:** cpi_yoy, econ_gdp_growth, unemployment_rate, etc.

**Actions:**
1. Use `scripts/fetch_fred_economic_data.py` (already exists)
2. Use `scripts/fetch_market_data.py` (already exists - yfinance working)
3. Update training table

**Cron:** Add to existing hourly_prices cron (NOT scrapecreator)

### Step 3: FETCH TRUMP/SOCIAL DATA (ScrapeCreators)
**Columns:** trump_*, social_sentiment_momentum_7d

**Actions:**
1. Use existing `cbi-v14-ingestion/ingest_scrapecreators_institutional.py`
2. Use existing `cbi-v14-ingestion/social_intelligence.py`
3. Parse properly with `legacy.created_at` dates

**Cron:** Separate scrapecreator cron (already exists)

### Step 4: DEEP TRAINING AUDIT
**Check:**
- All NULLs eliminated or in EXCEPT clause
- No temporal leakage
- No label leakage
- Data quality validation
- SQL syntax validation

### Step 5: TRAIN
**Execute:** `scripts/execute_phase_1.py`

---

**Starting Step 1 now - backfilling from existing data?**


