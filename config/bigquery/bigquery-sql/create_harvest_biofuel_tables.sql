-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- =====================================================
-- HARVEST PACE AND BIOFUEL DATA TABLES
-- Real data structures for academic rigor
-- =====================================================

-- HARVEST PROGRESS TABLE
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.harvest_progress` (
  report_date DATE NOT NULL,
  country STRING NOT NULL,
  crop_type STRING NOT NULL,
  crop_year STRING NOT NULL,
  progress_pct FLOAT64 NOT NULL,
  five_year_avg_pct FLOAT64 NOT NULL,
  
  -- Normalized scores for signal generation
  vs_5yr_avg FLOAT64 NOT NULL,  -- Current progress / 5-year average (normalized)
  vs_prior_week FLOAT64,        -- Week-over-week change
  days_ahead_behind INT64,      -- Days ahead/behind normal pace
  
  -- Harvest quality metrics
  yield_estimate FLOAT64,       -- Current yield estimate
  yield_vs_trend FLOAT64,       -- Yield vs trend (normalized)
  moisture_content FLOAT64,     -- Average moisture content
  
  -- Metadata
  source STRING NOT NULL,       -- Data source (USDA, CONAB, etc.)
  confidence_score FLOAT64,
  ingest_timestamp_utc TIMESTAMP NOT NULL,
  provenance_uuid STRING
)
PARTITION BY report_date
CLUSTER BY country, crop_type;

-- BIOFUEL METRICS TABLE
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.biofuel_metrics` (
  report_date DATE NOT NULL,
  
  -- Production metrics
  ethanol_production_thousand_barrels FLOAT64 NOT NULL,
  biodiesel_production_thousand_barrels FLOAT64,
  ethanol_stocks_thousand_barrels FLOAT64 NOT NULL,
  
  -- Policy metrics
  d4_rin_price FLOAT64,  -- Biomass-based diesel RIN price
  d6_rin_price FLOAT64,  -- Conventional ethanol RIN price
  
  -- Crush margin metrics
  soybean_oil_price FLOAT64 NOT NULL,
  biodiesel_price FLOAT64,
  soybean_oil_biodiesel_crush_margin FLOAT64,  -- (biodiesel_price - soybean_oil_price)
  
  -- Normalized metrics for signal generation  
  ethanol_production_vs_capacity FLOAT64 NOT NULL,  -- Production / capacity (normalized)
  ethanol_stocks_vs_5yr_avg FLOAT64 NOT NULL,  -- Stocks / 5-year average
  crush_margin_vs_trend FLOAT64,  -- Crush margin vs. 12-month average
  policy_impact_score FLOAT64,  -- Composite score from RIN prices and policy changes
  
  -- Metadata
  source STRING NOT NULL,
  confidence_score FLOAT64,
  ingest_timestamp_utc TIMESTAMP NOT NULL,
  provenance_uuid STRING
)
PARTITION BY report_date;

-- HARVEST PACE SIGNAL VIEW
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_harvest_pace_signal_real` AS
WITH 
us_soybean_harvest AS (
  SELECT
    report_date,
    progress_pct / 100 as us_progress,
    vs_5yr_avg as us_vs_avg
  FROM `cbi-v14.forecasting_data_warehouse.harvest_progress`
  WHERE country = 'US' AND crop_type = 'SOYBEANS'
  ORDER BY report_date DESC
  LIMIT 1
),

brazil_soybean_harvest AS (
  SELECT
    report_date,
    progress_pct / 100 as brazil_progress,
    vs_5yr_avg as brazil_vs_avg
  FROM `cbi-v14.forecasting_data_warehouse.harvest_progress`
  WHERE country = 'BRAZIL' AND crop_type = 'SOYBEANS'
  ORDER BY report_date DESC
  LIMIT 1
),

argentina_soybean_harvest AS (
  SELECT
    report_date,
    progress_pct / 100 as argentina_progress,
    vs_5yr_avg as argentina_vs_avg
  FROM `cbi-v14.forecasting_data_warehouse.harvest_progress`
  WHERE country = 'ARGENTINA' AND crop_type = 'SOYBEANS'
  ORDER BY report_date DESC
  LIMIT 1
)

SELECT
  CURRENT_DATE() as signal_date,
  
  -- Calculate seasonal weight based on time of year
  CASE
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (9, 10, 11) THEN 0.8  -- US harvest season
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (2, 3, 4) THEN 0.7    -- Brazil harvest season
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (4, 5, 6) THEN 0.7    -- Argentina harvest season
    ELSE 0.5  -- Off-season weight
  END as seasonal_weight,
  
  -- Individual country harvest scores (normalized)
  COALESCE(us.us_vs_avg, 1.0) as us_harvest_score,
  COALESCE(b.brazil_vs_avg, 1.0) as brazil_harvest_score,
  COALESCE(a.argentina_vs_avg, 1.0) as argentina_harvest_score,
  
  -- Composite harvest pace score (weighted by importance to global supply)
  CASE
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (9, 10, 11)  -- US harvest season
      THEN COALESCE(us.us_vs_avg * 0.7 + b.brazil_vs_avg * 0.2 + a.argentina_vs_avg * 0.1, 1.0)
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (2, 3, 4)    -- Brazil harvest season
      THEN COALESCE(us.us_vs_avg * 0.2 + b.brazil_vs_avg * 0.7 + a.argentina_vs_avg * 0.1, 1.0)
    WHEN EXTRACT(MONTH FROM CURRENT_DATE()) IN (4, 5, 6)    -- Argentina harvest season
      THEN COALESCE(us.us_vs_avg * 0.2 + b.brazil_vs_avg * 0.2 + a.argentina_vs_avg * 0.6, 1.0)
    ELSE COALESCE(us.us_vs_avg * 0.4 + b.brazil_vs_avg * 0.4 + a.argentina_vs_avg * 0.2, 1.0)
  END as harvest_pace_composite,
  
  -- Crisis flag
  CASE 
    WHEN (COALESCE(us.us_vs_avg, 1.0) < 0.8 AND EXTRACT(MONTH FROM CURRENT_DATE()) IN (9, 10, 11)) OR
         (COALESCE(b.brazil_vs_avg, 1.0) < 0.8 AND EXTRACT(MONTH FROM CURRENT_DATE()) IN (2, 3, 4)) OR
         (COALESCE(a.argentina_vs_avg, 1.0) < 0.8 AND EXTRACT(MONTH FROM CURRENT_DATE()) IN (4, 5, 6))
    THEN TRUE
    ELSE FALSE
  END as harvest_crisis_flag,
  
  CURRENT_TIMESTAMP() as updated_at
  
FROM us_soybean_harvest us
CROSS JOIN brazil_soybean_harvest b
CROSS JOIN argentina_soybean_harvest a;

-- BIOFUEL CASCADE SIGNAL VIEW
CREATE OR REPLACE VIEW `cbi-v14.signals.vw_biofuel_cascade_signal_real` AS
WITH 
latest_biofuel_data AS (
  SELECT
    *,
    LAG(ethanol_production_thousand_barrels) OVER (ORDER BY report_date) as prev_ethanol_production,
    LAG(biodiesel_production_thousand_barrels) OVER (ORDER BY report_date) as prev_biodiesel_production,
    LAG(d4_rin_price) OVER (ORDER BY report_date) as prev_d4_rin_price,
    LAG(d6_rin_price) OVER (ORDER BY report_date) as prev_d6_rin_price
  FROM `cbi-v14.forecasting_data_warehouse.biofuel_metrics`
  ORDER BY report_date DESC
  LIMIT 8  -- Two months of weekly data
),

biofuel_trends AS (
  SELECT
    MAX(report_date) as latest_date,
    
    -- Production trends (4-week rolling average)
    AVG(ethanol_production_thousand_barrels) as avg_ethanol_production,
    AVG(biodiesel_production_thousand_barrels) as avg_biodiesel_production,
    
    -- Stock trends
    AVG(ethanol_stocks_thousand_barrels) as avg_ethanol_stocks,
    
    -- Price and margin trends
    AVG(d4_rin_price) as avg_d4_rin_price,
    AVG(d6_rin_price) as avg_d6_rin_price,
    AVG(soybean_oil_biodiesel_crush_margin) as avg_crush_margin,
    
    -- Week-over-week changes
    AVG((ethanol_production_thousand_barrels - prev_ethanol_production) / 
        NULLIF(prev_ethanol_production, 0)) as avg_ethanol_production_change,
    AVG((biodiesel_production_thousand_barrels - prev_biodiesel_production) / 
        NULLIF(prev_biodiesel_production, 0)) as avg_biodiesel_production_change,
    AVG((d4_rin_price - prev_d4_rin_price) / 
        NULLIF(prev_d4_rin_price, 0)) as avg_d4_rin_price_change,
    AVG((d6_rin_price - prev_d6_rin_price) / 
        NULLIF(prev_d6_rin_price, 0)) as avg_d6_rin_price_change
  FROM latest_biofuel_data
)

SELECT
  CURRENT_DATE() as signal_date,
  
  -- Get latest values
  (SELECT ethanol_production_vs_capacity FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1) as ethanol_capacity_utilization,
  (SELECT ethanol_stocks_vs_5yr_avg FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1) as ethanol_stocks_normalized,
  (SELECT crush_margin_vs_trend FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1) as crush_margin_normalized,
  (SELECT policy_impact_score FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1) as policy_score,
  
  -- Get trend values
  t.avg_ethanol_production_change,
  t.avg_biodiesel_production_change,
  t.avg_d4_rin_price_change,
  t.avg_d6_rin_price_change,
  
  -- Composite biofuel cascade score
  (
    -- Production component (35%)
    COALESCE((SELECT ethanol_production_vs_capacity FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1), 0.5) * 0.2 +
    COALESCE(t.avg_ethanol_production_change * 5 + 0.5, 0.5) * 0.15 +
    
    -- Policy component (35%)
    COALESCE((SELECT policy_impact_score FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1), 0.5) * 0.2 +
    COALESCE(t.avg_d4_rin_price_change * 5 + 0.5, 0.5) * 0.15 +
    
    -- Margin component (30%)
    COALESCE((SELECT crush_margin_vs_trend FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1), 0.5) * 0.3
  ) as biofuel_cascade_composite,
  
  -- Crisis flag (when RIN prices spike or crush margins collapse)
  CASE 
    WHEN t.avg_d4_rin_price_change > 0.2 OR t.avg_d6_rin_price_change > 0.2 THEN TRUE
    WHEN (SELECT crush_margin_vs_trend FROM latest_biofuel_data ORDER BY report_date DESC LIMIT 1) < 0.3 THEN TRUE
    ELSE FALSE
  END as biofuel_crisis_flag,
  
  CURRENT_TIMESTAMP() as updated_at
  
FROM biofuel_trends t;
