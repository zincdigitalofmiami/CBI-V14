-- ============================================
-- UPDATED TRAINING EXCEPT CLAUSE
-- After comprehensive NULL fixes
-- ============================================

-- REMOVED FROM EXCEPT (now 95%+ coverage):
--   treasury_10y_yield      ✅ 100% coverage
--   soybean_meal_price      ✅ 100% coverage
--   unemployment_rate       ✅ 97% coverage (acceptable)
--   usd_cny_rate            ✅ 100% coverage
--   palm_price              ✅ 99.2% coverage
--   zl_price_current        ✅ 100% coverage
--   corn_price              ✅ 100% coverage
--   wheat_price             ✅ 100% coverage
--   vix_level               ✅ 100% coverage
--   dollar_index            ✅ 100% coverage

-- KEEP IN EXCEPT (still 97%+ NULL):
--   cpi_yoy                 ❌ 99.56% NULL (need FRED API fetch)
--   econ_gdp_growth         ❌ 99.56% NULL (need FRED API fetch)
--   gdp_growth              ❌ 99.56% NULL (need FRED API fetch)
--   us_midwest_temp_c       ❌ 97.8% NULL (no historical data)
--   us_midwest_precip_mm    ❌ 97.8% NULL (no historical data)
--   us_midwest_conditions_score   ❌ 97.8% NULL
--   us_midwest_heat_stress_days   ❌ 97.8% NULL
--   us_midwest_drought_days       ❌ 97.8% NULL
--   us_midwest_flood_days         ❌ 97.8% NULL

-- RECOMMENDED EXCEPT CLAUSE:
SELECT 
  target_1w,
  * EXCEPT(
    date,
    -- Economic data (need FRED API)
    cpi_yoy,
    econ_gdp_growth,
    gdp_growth,
    -- US Midwest weather (no historical data)
    us_midwest_temp_c,
    us_midwest_precip_mm,
    us_midwest_conditions_score,
    us_midwest_heat_stress_days,
    us_midwest_drought_days,
    us_midwest_flood_days,
    -- CFTC data (97% NULL)
    cftc_commercial_long,
    cftc_commercial_short,
    cftc_commercial_net,
    cftc_managed_long,
    cftc_managed_short,
    cftc_managed_net,
    cftc_open_interest,
    -- News data (99%+ NULL)
    news_article_count,
    news_avg_score
  )
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;


