-- ============================================
-- CREATE BOOST WEIGHTS LOG TABLE
-- Record multipliers for audit trail
-- Date: November 2025
-- ============================================

CREATE TABLE IF NOT EXISTS `cbi-v14.models_v4.boost_weights_log` (
  feature STRING NOT NULL,
  category STRING NOT NULL,
  multiplier FLOAT64 NOT NULL,
  boost_reason STRING,
  date_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  applied_by STRING DEFAULT 'rich_focused_pipeline'
)
PARTITION BY DATE(date_applied)
CLUSTER BY category, feature;

-- Insert initial boost weights
INSERT INTO `cbi-v14.models_v4.boost_weights_log` (feature, category, multiplier, boost_reason)
VALUES
  -- FX features (1.3x)
  ('dollar_index', 'fx', 1.3, 'Commodities dollar-priced; stronger USD pressures prices'),
  ('usd_cny_rate', 'fx', 1.3, 'China import rhythm sensitive to FX'),
  ('usd_brl_rate', 'fx', 1.3, 'Brazil export share swings with FX'),
  ('usd_ars_rate', 'fx', 1.3, 'Argentina pricing sensitive to FX'),
  ('fed_funds_rate', 'fx', 1.3, 'Rate differentials affect commodity flows'),
  ('treasury_10y_yield', 'fx', 1.3, 'Yield curve shapes import capacity'),
  ('real_yield', 'fx', 1.3, 'Real yields affect commodity demand'),
  ('yield_curve', 'fx', 1.3, 'Curve shape indicates macro regime'),
  ('dollar_index_7d_change', 'fx', 1.3, 'Recent FX momentum matters'),
  
  -- Trump/Policy/ICE (1.4x)
  ('trump_policy_events', 'trump', 1.4, 'Policy shocks move soy oil demand immediately'),
  ('trump_policy_impact_avg', 'trump', 1.4, 'RFS/biofuel decisions have immediate impact'),
  ('trump_policy_impact_max', 'trump', 1.4, 'Policy headlines have immediate price impact'),
  ('trump_policy_7d', 'trump', 1.4, 'Recent policy events drive volatility'),
  ('trump_events_7d', 'trump', 1.4, 'Executive orders move markets quickly'),
  ('ice_trump_policy_score', 'trump', 1.4, 'ICE intelligence captures policy signals'),
  ('ice_trump_executive_orders', 'trump', 1.4, 'Executive orders are first-order drivers'),
  ('ice_trump_company_deals', 'trump', 1.4, 'Company deals affect trade flows'),
  ('ice_trump_country_deals', 'trump', 1.4, 'Country deals reshape trade patterns'),
  ('rin_d4_price', 'trump', 1.4, 'RIN prices are first-order drivers of soy oil demand'),
  ('rin_d5_price', 'trump', 1.4, 'RIN prices drive biofuel economics'),
  ('rin_d6_price', 'trump', 1.4, 'RIN prices affect soy oil pricing'),
  ('rfs_mandate_biodiesel', 'trump', 1.4, 'RFS mandates directly affect demand'),
  ('rfs_mandate_advanced', 'trump', 1.4, 'RFS mandates shape biofuel demand'),
  ('rfs_mandate_total', 'trump', 1.4, 'RFS total mandate drives overall demand'),
  
  -- Tariffs/Trade (1.3x)
  ('trade_war_intensity', 'tariff', 1.3, 'Tariff shocks re-route flows and dent US pricing'),
  ('trade_war_impact_score', 'tariff', 1.3, 'Trade measures shift flows/prices'),
  ('china_tariff_rate', 'tariff', 1.3, 'China tariffs documented impacts from 2018'),
  ('tradewar_event_vol_mult', 'tariff', 1.3, 'Trade war events increase volatility'),
  ('china_policy_events', 'tariff', 1.3, 'China policy affects import patterns'),
  ('china_policy_impact', 'tariff', 1.3, 'China policy impacts documented'),
  
  -- Argentina (1.3x)
  ('argentina_export_tax', 'argentina', 1.3, '2025 suspension changed relative pricing'),
  ('argentina_china_sales_mt', 'argentina', 1.3, 'Argentina-China sales affect global supply'),
  ('argentina_port_congestion', 'argentina', 1.3, 'Rosario bottlenecks repeatedly impact shipments'),
  ('argentina_vessel_queue', 'argentina', 1.3, 'Vessel queues bottleneck exports'),
  ('argentina_crisis_score', 'argentina', 1.3, 'Crisis score captures regime changes'),
  ('arg_crisis_score', 'argentina', 1.3, 'Enhanced crisis score: vol + debt/GDP'),
  
  -- Recent Events/News (1.2x)
  ('news_intelligence_7d', 'news', 1.2, 'Near-term news correlates with short-horizon volatility'),
  ('news_volume_7d', 'news', 1.2, 'News volume indicates market attention'),
  ('news_sentiment_avg', 'news', 1.2, 'Sentiment affects near-term price moves'),
  ('china_news_count', 'news', 1.2, 'China news affects import expectations'),
  ('tariff_news_count', 'news', 1.2, 'Tariff news moves prices quickly'),
  ('biofuel_news_count', 'news', 1.2, 'Biofuel news affects demand expectations'),
  ('weather_news_count', 'news', 1.2, 'Weather news affects supply expectations');

-- Summary
SELECT 
  'BOOST WEIGHTS LOG CREATED' as status,
  COUNT(*) as features_logged,
  COUNT(DISTINCT category) as categories,
  AVG(multiplier) as avg_multiplier,
  MIN(multiplier) as min_multiplier,
  MAX(multiplier) as max_multiplier
FROM `cbi-v14.models_v4.boost_weights_log`;

-- Category breakdown
SELECT 
  category,
  COUNT(*) as feature_count,
  AVG(multiplier) as avg_multiplier
FROM `cbi-v14.models_v4.boost_weights_log`
GROUP BY category
ORDER BY avg_multiplier DESC;






