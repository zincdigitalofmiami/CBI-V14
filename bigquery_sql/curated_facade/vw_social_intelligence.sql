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









