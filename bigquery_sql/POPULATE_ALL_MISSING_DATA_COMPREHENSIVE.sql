-- ============================================
-- COMPREHENSIVE DATA POPULATION
-- Fill ALL missing data from ALL available sources
-- ============================================

-- ============================================
-- PART 1: FED FUNDS RATE (4.1% NULL)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH fed_data AS (
    SELECT 
      CAST(time AS DATE) as date,
      value as fed_funds_rate
    FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
    WHERE indicator = 'fed_funds_rate' AND value IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY CAST(time AS DATE) ORDER BY time DESC) = 1
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  fed_daily AS (
    SELECT 
      td.date,
      LAST_VALUE(fd.fed_funds_rate IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as fed_funds_rate
    FROM training_dates td
    LEFT JOIN fed_data fd ON td.date = fd.date
  )
  SELECT date, fed_funds_rate
  FROM fed_daily
  WHERE fed_funds_rate IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  fed_funds_rate = COALESCE(target.fed_funds_rate, source.fed_funds_rate);

-- ============================================
-- PART 2: BRAZIL WEATHER (13.6% NULL)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH brazil_weather AS (
    SELECT 
      date,
      temp_avg_c as weather_brazil_temp,
      precip_mm as weather_brazil_precip
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE region = 'Brazil'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  brazil_daily AS (
    SELECT 
      td.date,
      LAST_VALUE(bw.weather_brazil_temp IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as weather_brazil_temp,
      LAST_VALUE(bw.weather_brazil_precip IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as weather_brazil_precip
    FROM training_dates td
    LEFT JOIN brazil_weather bw ON td.date = bw.date
  )
  SELECT date, weather_brazil_temp, weather_brazil_precip
  FROM brazil_daily
  WHERE weather_brazil_temp IS NOT NULL OR weather_brazil_precip IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  weather_brazil_temp = COALESCE(target.weather_brazil_temp, source.weather_brazil_temp),
  weather_brazil_precip = COALESCE(target.weather_brazil_precip, source.weather_brazil_precip);

-- ============================================
-- PART 3: ARGENTINA WEATHER (13.6% NULL)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH argentina_weather AS (
    SELECT 
      date,
      temp_avg as weather_argentina_temp,
      precip_mm as weather_argentina_precip
    FROM `cbi-v14.forecasting_data_warehouse.weather_data`
    WHERE region = 'Argentina'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  argentina_daily AS (
    SELECT 
      td.date,
      LAST_VALUE(aw.weather_argentina_temp IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as weather_argentina_temp,
      LAST_VALUE(aw.weather_argentina_precip IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as weather_argentina_precip
    FROM training_dates td
    LEFT JOIN argentina_weather aw ON td.date = aw.date
  )
  SELECT date, weather_argentina_temp, weather_argentina_precip
  FROM argentina_daily
  WHERE weather_argentina_temp IS NOT NULL OR weather_argentina_precip IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  weather_argentina_temp = COALESCE(target.weather_argentina_temp, source.weather_argentina_temp),
  weather_argentina_precip = COALESCE(target.weather_argentina_precip, source.weather_argentina_precip);

-- ============================================
-- PART 4: CHINA RELATIONS & TARIFF FEATURES (13.6% NULL)
-- ============================================

-- Check if signal views exist
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH china_tariff_signals AS (
    SELECT 
      date,
      feature_china_relations,
      feature_tariff_threat
    FROM `cbi-v14.signals.vw_china_relations_big8` cr
    FULL OUTER JOIN `cbi-v14.signals.vw_tariff_threat_big8` tt USING (date)
    WHERE feature_china_relations IS NOT NULL OR feature_tariff_threat IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  signals_daily AS (
    SELECT 
      td.date,
      LAST_VALUE(cts.feature_china_relations IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as feature_china_relations,
      LAST_VALUE(cts.feature_tariff_threat IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as feature_tariff_threat
    FROM training_dates td
    LEFT JOIN china_tariff_signals cts ON td.date = cts.date
  )
  SELECT date, feature_china_relations, feature_tariff_threat
  FROM signals_daily
  WHERE feature_china_relations IS NOT NULL OR feature_tariff_threat IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  feature_china_relations = COALESCE(target.feature_china_relations, source.feature_china_relations),
  feature_tariff_threat = COALESCE(target.feature_tariff_threat, source.feature_tariff_threat);

-- ============================================
-- PART 5: CFTC DATA (95.9% NULL)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH cftc_data AS (
    SELECT 
      date,
      commercial_long as cftc_commercial_long,
      commercial_short as cftc_commercial_short,
      commercial_net as cftc_commercial_net,
      managed_long as cftc_managed_long,
      managed_short as cftc_managed_short,
      managed_net as cftc_managed_net,
      open_interest as cftc_open_interest
    FROM `cbi-v14.forecasting_data_warehouse.cftc_cot`
    WHERE commodity = 'Soybean Oil' OR commodity LIKE '%Soybean%Oil%'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY date ORDER BY date DESC) = 1
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  cftc_daily AS (
    SELECT 
      td.date,
      LAST_VALUE(cd.cftc_commercial_long IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_commercial_long,
      LAST_VALUE(cd.cftc_commercial_short IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_commercial_short,
      LAST_VALUE(cd.cftc_commercial_net IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_commercial_net,
      LAST_VALUE(cd.cftc_managed_long IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_managed_long,
      LAST_VALUE(cd.cftc_managed_short IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_managed_short,
      LAST_VALUE(cd.cftc_managed_net IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_managed_net,
      LAST_VALUE(cd.cftc_open_interest IGNORE NULLS) OVER (
        ORDER BY td.date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) as cftc_open_interest
    FROM training_dates td
    LEFT JOIN cftc_data cd ON td.date = cd.date
  )
  SELECT date, 
    cftc_commercial_long, cftc_commercial_short, cftc_commercial_net,
    cftc_managed_long, cftc_managed_short, cftc_managed_net,
    cftc_open_interest
  FROM cftc_daily
  WHERE cftc_commercial_long IS NOT NULL OR cftc_managed_long IS NOT NULL
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  cftc_commercial_long = COALESCE(target.cftc_commercial_long, source.cftc_commercial_long),
  cftc_commercial_short = COALESCE(target.cftc_commercial_short, source.cftc_commercial_short),
  cftc_commercial_net = COALESCE(target.cftc_commercial_net, source.cftc_commercial_net),
  cftc_managed_long = COALESCE(target.cftc_managed_long, source.cftc_managed_long),
  cftc_managed_short = COALESCE(target.cftc_managed_short, source.cftc_managed_short),
  cftc_managed_net = COALESCE(target.cftc_managed_net, source.cftc_managed_net),
  cftc_open_interest = COALESCE(target.cftc_open_interest, source.cftc_open_interest);

-- ============================================
-- PART 6: NEWS DATA (99.7% NULL)
-- ============================================

MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (
  WITH news_data AS (
    SELECT 
      DATE(published_at) as date,
      COUNT(*) as news_article_count,
      AVG(sentiment_score) as news_avg_score
    FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
    WHERE published_at IS NOT NULL
    GROUP BY DATE(published_at)
  ),
  training_dates AS (
    SELECT DISTINCT date
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    WHERE target_1w IS NOT NULL
  ),
  news_daily AS (
    SELECT 
      td.date,
      COALESCE(nd.news_article_count, 0) as news_article_count,
      nd.news_avg_score as news_avg_score
    FROM training_dates td
    LEFT JOIN news_data nd ON td.date = nd.date
  )
  SELECT date, news_article_count, news_avg_score
  FROM news_daily
) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  news_article_count = COALESCE(target.news_article_count, source.news_article_count),
  news_avg_score = COALESCE(target.news_avg_score, source.news_avg_score);

-- ============================================
-- PART 7: VERIFICATION
-- ============================================

SELECT 
  'FINAL COVERAGE STATUS' as status,
  COUNT(*) as total_rows,
  ROUND((1 - COUNTIF(fed_funds_rate IS NULL) / COUNT(*)) * 100, 1) as fed_funds_coverage,
  ROUND((1 - COUNTIF(weather_brazil_temp IS NULL) / COUNT(*)) * 100, 1) as brazil_weather_coverage,
  ROUND((1 - COUNTIF(weather_argentina_temp IS NULL) / COUNT(*)) * 100, 1) as argentina_weather_coverage,
  ROUND((1 - COUNTIF(feature_china_relations IS NULL) / COUNT(*)) * 100, 1) as china_relations_coverage,
  ROUND((1 - COUNTIF(feature_tariff_threat IS NULL) / COUNT(*)) * 100, 1) as tariff_threat_coverage,
  ROUND((1 - COUNTIF(cftc_commercial_long IS NULL) / COUNT(*)) * 100, 1) as cftc_coverage,
  ROUND((1 - COUNTIF(news_article_count IS NULL) / COUNT(*)) * 100, 1) as news_coverage
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;


