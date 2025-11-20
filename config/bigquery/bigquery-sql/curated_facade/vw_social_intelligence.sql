-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- curated.vw_social_intelligence
-- Social intelligence facade view (temporary contract until staging table is introduced)
CREATE OR REPLACE VIEW `cbi-v14.curated.vw_social_intelligence` AS
SELECT
  DATE(timestamp) AS date,
  platform,
  subreddit,
  title,
  score,
  comments,
  sentiment_score,
  market_relevance,
  source_name,
  confidence_score,
  ingest_timestamp_utc,
  provenance_uuid
FROM `cbi-v14.forecasting_data_warehouse.social_sentiment`;









