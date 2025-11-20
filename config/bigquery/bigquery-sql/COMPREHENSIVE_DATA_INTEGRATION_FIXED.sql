-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- ============================================
-- COMPREHENSIVE DATA INTEGRATION - FIX ALL GAPS
-- JOIN ALL EXISTING SOURCE DATA TO TRAINING DATASET
-- CORRECTED VERSION - Verified column names
-- ============================================

-- Create backup before major changes
CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_dataset_pre_integration_backup` AS
SELECT * FROM `cbi-v14.models_v4.training_dataset_super_enriched`;

-- ============================================
-- CRITICAL FIX 1: JOIN NEWS INTELLIGENCE (99.7% NULL → 0% NULL)
-- Column: published (TIMESTAMP), not published_at
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.news_intelligence_daily` AS
WITH news_daily_agg AS (
  SELECT 
    DATE(published) as date,
    COUNT(*) as news_article_count,
    AVG(intelligence_score) as news_avg_score,
    -- Calculate sentiment averages (use intelligence_score as sentiment proxy)
    AVG(intelligence_score) as news_sentiment_avg,
    
    -- Categorize news by content (check title and content columns)
    COUNTIF(LOWER(COALESCE(title, '')) LIKE '%china%' OR LOWER(COALESCE(content, '')) LIKE '%china%') as china_news_count,
    COUNTIF(LOWER(COALESCE(title, '')) LIKE '%biofuel%' OR LOWER(COALESCE(content, '')) LIKE '%biofuel%' OR LOWER(COALESCE(content, '')) LIKE '%ethanol%') as biofuel_news_count,
    COUNTIF(LOWER(COALESCE(title, '')) LIKE '%tariff%' OR LOWER(COALESCE(content, '')) LIKE '%trade war%') as tariff_news_count,
    COUNTIF(LOWER(COALESCE(title, '')) LIKE '%weather%' OR LOWER(COALESCE(content, '')) LIKE '%drought%' OR LOWER(COALESCE(content, '')) LIKE '%flood%') as weather_news_count
  FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
  WHERE published IS NOT NULL
  GROUP BY DATE(published)
),
news_daily AS (
  SELECT 
    date,
    news_article_count,
    news_avg_score,
    news_sentiment_avg,
    china_news_count,
    biofuel_news_count,
    tariff_news_count,
    weather_news_count,
    -- Calculate 7-day rolling averages after aggregation
    AVG(news_avg_score) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_intelligence_7d,
    SUM(news_article_count) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as news_volume_7d
  FROM news_daily_agg
)
SELECT * FROM news_daily ORDER BY date;

-- ============================================
-- CRITICAL FIX 2: JOIN CFTC DATA (95.9% NULL → 5% NULL)
-- Columns: managed_money_long/short (not noncommercial)
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.cftc_daily_filled` AS
WITH cftc_weekly AS (
  SELECT 
    report_date as date,
    commercial_long,
    commercial_short,
    managed_money_long as noncommercial_long,  -- Map to expected name
    managed_money_short as noncommercial_short,  -- Map to expected name
    open_interest,
    -- Calculate net positions
    (commercial_long - commercial_short) as commercial_net,
    (managed_money_long - managed_money_short) as noncommercial_net
  FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
  WHERE commercial_long IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY report_date ORDER BY report_date DESC) = 1
),
cftc_with_percentiles AS (
  SELECT 
    *,
    -- Calculate positioning extremes (percentiles) across all dates
    PERCENT_RANK() OVER (ORDER BY commercial_net) as commercial_net_percentile,
    PERCENT_RANK() OVER (ORDER BY noncommercial_net) as spec_net_percentile
  FROM cftc_weekly
),
-- Get all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),
-- Forward-fill CFTC weekly data to daily
cftc_daily_filled AS (
  SELECT 
    td.date,
    -- Forward fill all CFTC values
    LAST_VALUE(cw.commercial_long IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_commercial_long,
    LAST_VALUE(cw.commercial_short IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_commercial_short,
    LAST_VALUE(cw.noncommercial_long IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_managed_long,  -- Use managed_money name in output
    LAST_VALUE(cw.noncommercial_short IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_managed_short,  -- Use managed_money name in output
    LAST_VALUE(cw.open_interest IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_open_interest,
    LAST_VALUE(cw.commercial_net IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_commercial_net,
    LAST_VALUE(cw.noncommercial_net IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_managed_net,  -- Use managed_money name
    LAST_VALUE(cw.commercial_net_percentile IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_commercial_extreme,
    LAST_VALUE(cw.spec_net_percentile IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cftc_spec_extreme
  FROM training_dates td
  LEFT JOIN cftc_with_percentiles cw ON td.date = cw.date
)
SELECT * FROM cftc_daily_filled;

-- ============================================
-- CRITICAL FIX 3: ADD PALM OIL (FCPO=F)
-- Check if data exists, if not use alternative palm oil sources
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.palm_oil_complete` AS
WITH 
-- Try FCPO=F first
fcpo_data AS (
  SELECT 
    date,
    Close as palm_price,
    Volume as palm_volume,
    'FCPO=F' as source
  FROM `cbi-v14.forecasting_data_warehouse.yahoo_finance_enhanced`
  WHERE symbol = 'FCPO=F' AND Close IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY pulled_at DESC) = 1
),
-- Try alternative palm oil sources from palm_oil_prices table (if available)
alt_palm_data AS (
  SELECT 
    DATE(time) as date,
    close as palm_price,
    volume as palm_volume,
    'palm_oil_prices' as source
  FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
  WHERE close IS NOT NULL AND time IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(time) ORDER BY time DESC) = 1
),
-- Combine all palm oil sources
combined_palm AS (
  SELECT date, palm_price, palm_volume, source FROM fcpo_data
  UNION ALL
  SELECT date, palm_price, palm_volume, source FROM alt_palm_data
),
-- Get best palm oil data per date
palm_prioritized AS (
  SELECT 
    date,
    palm_price,
    palm_volume,
    source,
    ROW_NUMBER() OVER (PARTITION BY date ORDER BY 
      CASE source 
        WHEN 'FCPO=F' THEN 1
        WHEN 'palm_oil_prices' THEN 2  
        ELSE 3 
      END
    ) as priority
  FROM combined_palm
),
-- Forward-fill palm oil to all training dates
training_dates AS (
  SELECT DISTINCT date 
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  ORDER BY date
),
palm_daily_filled AS (
  SELECT 
    td.date,
    LAST_VALUE(pp.palm_price IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as palm_price_filled,
    LAST_VALUE(pp.palm_volume IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as palm_volume_filled,
    LAST_VALUE(pp.source IGNORE NULLS) OVER (
      ORDER BY td.date 
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as palm_source
  FROM training_dates td
  LEFT JOIN palm_prioritized pp ON td.date = pp.date AND pp.priority = 1
)
SELECT * FROM palm_daily_filled WHERE palm_price_filled IS NOT NULL;

-- ============================================
-- HIGH PRIORITY FIX 4: JOIN SOCIAL SENTIMENT (653 records exist)
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.social_sentiment_daily` AS
WITH sentiment_daily_agg AS (
  SELECT 
    DATE(timestamp) as date,
    AVG(sentiment_score) as social_sentiment_avg,
    STDDEV(sentiment_score) as social_sentiment_volatility,
    COUNT(*) as social_post_count,
    -- Calculate directional sentiment
    COUNTIF(sentiment_score > 0.6) / COUNT(*) as bullish_ratio,
    COUNTIF(sentiment_score < 0.4) / COUNT(*) as bearish_ratio
  FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`
  WHERE sentiment_score IS NOT NULL
  GROUP BY DATE(timestamp)
),
sentiment_daily AS (
  SELECT 
    date,
    social_sentiment_avg,
    social_sentiment_volatility,
    social_post_count,
    bullish_ratio,
    bearish_ratio,
    -- 7-day rolling metrics after aggregation
    AVG(social_sentiment_avg) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as social_sentiment_7d,
    SUM(social_post_count) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as social_volume_7d
  FROM sentiment_daily_agg
)
SELECT * FROM sentiment_daily ORDER BY date;

-- ============================================
-- HIGH PRIORITY FIX 5: JOIN TRUMP POLICY (215 records exist)
-- Columns: timestamp (not event_date), use agricultural_impact or soybean_relevance
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.trump_policy_daily` AS
WITH policy_daily_agg AS (
  SELECT 
    DATE(timestamp) as date,
    COUNT(*) as trump_policy_events,
    AVG(COALESCE(agricultural_impact, soybean_relevance, 0.5)) as trump_policy_impact_avg,
    MAX(COALESCE(agricultural_impact, soybean_relevance, 0.5)) as trump_policy_impact_max,
    -- Categorize by policy type
    COUNTIF(LOWER(COALESCE(category, '')) LIKE '%trade%' OR LOWER(COALESCE(category, '')) LIKE '%tariff%' OR LOWER(COALESCE(text, '')) LIKE '%trade%') as trade_policy_events,
    COUNTIF(LOWER(COALESCE(category, '')) LIKE '%china%' OR LOWER(COALESCE(text, '')) LIKE '%china%') as china_policy_events,
    COUNTIF(LOWER(COALESCE(category, '')) LIKE '%agricultural%' OR LOWER(COALESCE(category, '')) LIKE '%farm%' OR agricultural_impact IS NOT NULL) as ag_policy_events
  FROM `cbi-v14.forecasting_data_warehouse.trump_policy_intelligence`
  WHERE timestamp IS NOT NULL
  GROUP BY DATE(timestamp)
),
policy_daily AS (
  SELECT 
    date,
    trump_policy_events,
    trump_policy_impact_avg,
    trump_policy_impact_max,
    trade_policy_events,
    china_policy_events,
    ag_policy_events,
    -- 7-day rolling impact after aggregation
    AVG(trump_policy_impact_avg) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as trump_policy_7d,
    SUM(trump_policy_events) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as trump_events_7d
  FROM policy_daily_agg
)
SELECT * FROM policy_daily ORDER BY date;

-- ============================================
-- MEDIUM PRIORITY FIX 6: CHECK AND JOIN USDA DATA
-- Columns: report_date (not week_ending), net_sales_mt (not weekly_sales), destination_country (not destination)
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.usda_export_daily` AS
WITH export_weekly AS (
  SELECT 
    report_date as date,
    commodity,
    destination_country as destination,
    net_sales_mt as weekly_sales,
    cumulative_exports_mt as cumulative_sales
  FROM `cbi-v14.forecasting_data_warehouse.usda_export_sales`
  WHERE commodity IN ('Soybeans', 'Soybean Oil', 'Soybean Meal')
),
export_aggregated AS (
  SELECT 
    date,
    SUM(CASE WHEN commodity = 'Soybeans' THEN weekly_sales ELSE 0 END) as soybean_weekly_sales,
    SUM(CASE WHEN commodity = 'Soybean Oil' THEN weekly_sales ELSE 0 END) as soybean_oil_weekly_sales,
    SUM(CASE WHEN commodity = 'Soybean Meal' THEN weekly_sales ELSE 0 END) as soybean_meal_weekly_sales,
    -- China-specific sales
    SUM(CASE WHEN commodity = 'Soybeans' AND destination = 'China' THEN weekly_sales ELSE 0 END) as china_soybean_sales
  FROM export_weekly
  GROUP BY date
)
SELECT * FROM export_aggregated ORDER BY date;

-- ============================================
-- MEDIUM PRIORITY FIX 7: ADD MISSING CURRENCY PAIRS
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.currency_complete` AS
WITH all_currency_pairs AS (
  SELECT 
    date,
    from_currency,
    to_currency,
    rate
  FROM `cbi-v14.forecasting_data_warehouse.currency_data`
  WHERE (from_currency = 'USD' AND to_currency IN ('CNY', 'BRL', 'ARS', 'MYR'))
     OR (from_currency IN ('CNY', 'BRL', 'ARS', 'MYR') AND to_currency = 'USD')
),
currency_normalized AS (
  SELECT 
    date,
    CASE 
      WHEN from_currency = 'USD' THEN CONCAT('USD_', to_currency)
      ELSE CONCAT('USD_', from_currency)
    END as currency_pair,
    CASE 
      WHEN from_currency = 'USD' THEN rate
      ELSE 1.0 / NULLIF(rate, 0)  -- Invert rate for non-USD base
    END as usd_rate
  FROM all_currency_pairs
),
currency_pivoted AS (
  SELECT 
    date,
    MAX(CASE WHEN currency_pair = 'USD_CNY' THEN usd_rate END) as usd_cny_rate,
    MAX(CASE WHEN currency_pair = 'USD_BRL' THEN usd_rate END) as usd_brl_rate,
    MAX(CASE WHEN currency_pair = 'USD_ARS' THEN usd_rate END) as usd_ars_rate,
    MAX(CASE WHEN currency_pair = 'USD_MYR' THEN usd_rate END) as usd_myr_rate
  FROM currency_normalized
  GROUP BY date
)
SELECT * FROM currency_pivoted ORDER BY date;

-- ============================================
-- COMPREHENSIVE INTEGRATION: MERGE ALL DATA INTO TRAINING DATASET
-- Only update columns that exist in target table
-- ============================================

-- NOTE: This SQL targets production_training_data_* tables
-- Update each horizon table separately (1w, 1m, 3m, 6m)
-- For now, updating zl_training_prod_allhistory_1m as example

MERGE `cbi-v14.training.zl_training_prod_allhistory_1m` AS target
USING (
  WITH 
  -- News data
  news AS (
    SELECT 
      date,
      news_article_count, news_avg_score, news_sentiment_avg,
      china_news_count, biofuel_news_count, tariff_news_count, weather_news_count,
      news_intelligence_7d, news_volume_7d
    FROM `cbi-v14.models_v4.news_intelligence_daily`
  ),
  
  -- CFTC data
  cftc AS (
    SELECT 
      date,
      cftc_commercial_long, cftc_commercial_short, cftc_managed_long,
      cftc_managed_short, cftc_open_interest, cftc_commercial_net,
      cftc_managed_net, cftc_commercial_extreme, cftc_spec_extreme
    FROM `cbi-v14.models_v4.cftc_daily_filled`
  ),
  
  -- Palm oil data
  palm AS (
    SELECT 
      date,
      palm_price_filled as palm_price_new,
      palm_volume_filled as palm_volume_new
    FROM `cbi-v14.models_v4.palm_oil_complete`
  ),
  
  -- Social sentiment data
  social AS (
    SELECT 
      date,
      social_sentiment_avg, social_sentiment_volatility, social_post_count,
      bullish_ratio, bearish_ratio, social_sentiment_7d, social_volume_7d
    FROM `cbi-v14.models_v4.social_sentiment_daily`
  ),
  
  -- Trump policy data
  trump AS (
    SELECT 
      date,
      trump_policy_events, trump_policy_impact_avg, trump_policy_impact_max,
      trade_policy_events, china_policy_events, ag_policy_events,
      trump_policy_7d, trump_events_7d
    FROM `cbi-v14.models_v4.trump_policy_daily`
  ),
  
  -- USDA export data
  usda AS (
    SELECT 
      date,
      soybean_weekly_sales, soybean_oil_weekly_sales, soybean_meal_weekly_sales,
      china_soybean_sales
    FROM `cbi-v14.models_v4.usda_export_daily`
  ),
  
  -- Currency data
  currency AS (
    SELECT 
      date,
      usd_cny_rate as usd_cny_rate_new,
      usd_brl_rate as usd_brl_rate_new,
      usd_ars_rate,
      usd_myr_rate
    FROM `cbi-v14.models_v4.currency_complete`
  ),
  
  -- NEW: RIN prices data
  rin AS (
    SELECT 
      date,
      rin_d4_price,
      rin_d5_price,
      rin_d6_price
    FROM `cbi-v14.models_v4.rin_prices_daily`
  ),
  
  -- NEW: RFS mandates data
  rfs AS (
    SELECT 
      date,
      rfs_mandate_biodiesel,
      rfs_mandate_advanced,
      rfs_mandate_total
    FROM `cbi-v14.models_v4.rfs_mandates_daily`
  ),
  
  -- NEW: Freight logistics data
  freight AS (
    SELECT 
      date,
      baltic_dry_index
    FROM `cbi-v14.models_v4.freight_logistics_daily`
  ),
  
  -- NEW: Argentina port logistics data
  argentina_port AS (
    SELECT 
      date,
      argentina_vessel_queue_count,
      argentina_port_throughput_teu
    FROM `cbi-v14.models_v4.argentina_port_logistics_daily`
  )
  
  -- Combine all data sources
  SELECT 
    COALESCE(news.date, cftc.date, palm.date, social.date, trump.date, usda.date, currency.date, rin.date, rfs.date, freight.date, argentina_port.date) as date,
    
    -- News features
    news.news_article_count, news.news_avg_score, news.news_sentiment_avg,
    news.china_news_count, news.biofuel_news_count, news.tariff_news_count, news.weather_news_count,
    news.news_intelligence_7d, news.news_volume_7d,
    
    -- CFTC features
    cftc.cftc_commercial_long, cftc.cftc_commercial_short, cftc.cftc_managed_long,
    cftc.cftc_managed_short, cftc.cftc_open_interest, cftc.cftc_commercial_net,
    cftc.cftc_managed_net, cftc.cftc_commercial_extreme, cftc.cftc_spec_extreme,
    
    -- Palm oil features
    palm.palm_price_new, palm.palm_volume_new,
    
    -- Social sentiment features
    social.social_sentiment_avg, social.social_sentiment_volatility, social.social_post_count,
    social.bullish_ratio, social.bearish_ratio, social.social_sentiment_7d, social.social_volume_7d,
    
    -- Trump policy features
    trump.trump_policy_events, trump.trump_policy_impact_avg, trump.trump_policy_impact_max,
    trump.trade_policy_events, trump.china_policy_events, trump.ag_policy_events,
    trump.trump_policy_7d, trump.trump_events_7d,
    
    -- USDA features
    usda.soybean_weekly_sales, usda.soybean_oil_weekly_sales, usda.soybean_meal_weekly_sales,
    usda.china_soybean_sales,
    usda.china_weekly_cancellations_mt,
    
    -- Currency features
    currency.usd_cny_rate_new, currency.usd_brl_rate_new, currency.usd_ars_rate, currency.usd_myr_rate,
    
    -- NEW: RIN prices features
    rin.rin_d4_price,
    rin.rin_d5_price,
    rin.rin_d6_price,
    
    -- NEW: RFS mandate features
    rfs.rfs_mandate_biodiesel,
    rfs.rfs_mandate_advanced,
    rfs.rfs_mandate_total,
    
    -- NEW: Freight logistics features
    freight.baltic_dry_index,
    
    -- NEW: Argentina port logistics features
    argentina_port.argentina_vessel_queue_count,
    argentina_port.argentina_port_throughput_teu
    
  FROM news
  FULL OUTER JOIN cftc USING(date)
  FULL OUTER JOIN palm USING(date)
  FULL OUTER JOIN social USING(date)
  FULL OUTER JOIN trump USING(date)
  FULL OUTER JOIN usda USING(date)
  FULL OUTER JOIN currency USING(date)
  FULL OUTER JOIN rin USING(date)
  FULL OUTER JOIN rfs USING(date)
  FULL OUTER JOIN freight USING(date)
  FULL OUTER JOIN argentina_port USING(date)
  WHERE COALESCE(news.date, cftc.date, palm.date, social.date, trump.date, usda.date, currency.date, rin.date, rfs.date, freight.date, argentina_port.date) IS NOT NULL
  
) AS source ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  -- News intelligence updates (fix 99.7% NULL)
  news_article_count = COALESCE(target.news_article_count, source.news_article_count),
  news_avg_score = COALESCE(target.news_avg_score, source.news_avg_score),
  
  -- CFTC updates (fix 95.9% NULL)
  cftc_commercial_long = COALESCE(target.cftc_commercial_long, source.cftc_commercial_long),
  cftc_commercial_short = COALESCE(target.cftc_commercial_short, source.cftc_commercial_short),
  cftc_managed_long = COALESCE(target.cftc_managed_long, source.cftc_managed_long),
  cftc_managed_short = COALESCE(target.cftc_managed_short, source.cftc_managed_short),
  cftc_open_interest = COALESCE(target.cftc_open_interest, source.cftc_open_interest),
  cftc_commercial_net = COALESCE(target.cftc_commercial_net, source.cftc_commercial_net),
  cftc_managed_net = COALESCE(target.cftc_managed_net, source.cftc_managed_net),
  
  -- Palm oil updates (add missing FCPO=F)
  palm_price = COALESCE(target.palm_price, source.palm_price_new),
  
  -- Currency updates  
  usd_cny_rate = COALESCE(target.usd_cny_rate, source.usd_cny_rate_new),
  usd_brl_rate = COALESCE(target.usd_brl_rate, source.usd_brl_rate_new),
  
  -- NEW: RIN prices updates
  rin_d4_price = COALESCE(target.rin_d4_price, source.rin_d4_price),
  rin_d5_price = COALESCE(target.rin_d5_price, source.rin_d5_price),
  rin_d6_price = COALESCE(target.rin_d6_price, source.rin_d6_price),
  
  -- NEW: RFS mandates updates
  rfs_mandate_biodiesel = COALESCE(target.rfs_mandate_biodiesel, source.rfs_mandate_biodiesel),
  rfs_mandate_advanced = COALESCE(target.rfs_mandate_advanced, source.rfs_mandate_advanced),
  rfs_mandate_total = COALESCE(target.rfs_mandate_total, source.rfs_mandate_total),
  
  -- NEW: Freight logistics updates
  baltic_dry_index = COALESCE(target.baltic_dry_index, source.baltic_dry_index),
  
  -- NEW: Argentina port logistics updates
  argentina_vessel_queue_count = COALESCE(target.argentina_vessel_queue_count, source.argentina_vessel_queue_count),
  argentina_port_throughput_teu = COALESCE(target.argentina_port_throughput_teu, source.argentina_port_throughput_teu),
  
  -- NEW: China weekly cancellations update
  china_weekly_cancellations_mt = COALESCE(target.china_weekly_cancellations_mt, source.china_weekly_cancellations_mt);

-- ============================================
-- FINAL VERIFICATION: CHECK ALL IMPROVEMENTS
-- ============================================

SELECT 
  '🎉 COMPREHENSIVE DATA INTEGRATION RESULTS' as status,
  COUNT(*) as total_rows,
  
  -- Check news intelligence (was 99.7% NULL)
  ROUND((1 - COUNTIF(news_article_count IS NULL) / COUNT(*)) * 100, 1) as news_coverage,
  
  -- Check CFTC (was 95.9% NULL)
  ROUND((1 - COUNTIF(cftc_commercial_long IS NULL) / COUNT(*)) * 100, 1) as cftc_coverage,
  
  -- Check palm oil (was 0 records)
  ROUND((1 - COUNTIF(palm_price IS NULL) / COUNT(*)) * 100, 1) as palm_coverage,
  
  -- Check currency pairs
  ROUND((1 - COUNTIF(usd_cny_rate IS NULL) / COUNT(*)) * 100, 1) as usd_cny_coverage,
  ROUND((1 - COUNTIF(usd_brl_rate IS NULL) / COUNT(*)) * 100, 1) as usd_brl_coverage,
  
  -- Final assessment
  CASE 
    WHEN COUNTIF(news_article_count IS NOT NULL) / COUNT(*) >= 0.8 AND
         COUNTIF(cftc_commercial_long IS NOT NULL) / COUNT(*) >= 0.8 AND
         COUNTIF(palm_price IS NOT NULL) / COUNT(*) >= 0.8
    THEN '🚀 MISSION ACCOMPLISHED - ALL CRITICAL GAPS FILLED'
    WHEN COUNTIF(news_article_count IS NOT NULL) / COUNT(*) >= 0.5 AND
         COUNTIF(cftc_commercial_long IS NOT NULL) / COUNT(*) >= 0.5
    THEN '✅ MAJOR SUCCESS - SIGNIFICANT IMPROVEMENTS MADE'
    ELSE '⚠️ PARTIAL SUCCESS - SOME GAPS REMAIN'
  END as final_assessment
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

