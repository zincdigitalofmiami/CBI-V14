-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Create Vegas-related tables for Kevin's sales intelligence

-- Vegas Customers table
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_customers` (
  customer_id STRING NOT NULL,
  customer_name STRING NOT NULL,
  location STRING,
  consumption_gallons_per_month FLOAT64,
  last_order_date DATE,
  status STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY customer_id;

-- Vegas Events table
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_events` (
  event_id STRING NOT NULL,
  event_name STRING NOT NULL,
  venue STRING,
  start_date DATE NOT NULL,
  end_date DATE,
  expected_attendance INT64,
  oil_demand_gallons_estimate FLOAT64,
  priority STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY start_date;

-- Vegas Calculation Config (Kevin-editable)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_calculation_config` (
  config_key STRING NOT NULL,
  config_value STRING NOT NULL,
  description STRING,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_by STRING
)
CLUSTER BY config_key;

-- Vegas Sales Opportunities
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_sales_opportunities` (
  opportunity_id STRING NOT NULL,
  event_id STRING,
  customer_id STRING,
  opportunity_name STRING NOT NULL,
  estimated_gallons FLOAT64,
  estimated_revenue FLOAT64,
  confidence_score FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY confidence_score;

-- Vegas Sales (already referenced in API)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.vegas_sales` (
  date DATE NOT NULL,
  sales FLOAT64,
  region STRING,
  customer_count INT64,
  volume_gallons FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY region;

-- Create Legislative-related tables

-- Legislation Events (generic, used by multiple routes)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.legislation_events` (
  event_date DATE NOT NULL,
  event_title STRING NOT NULL,
  event_type STRING NOT NULL,  -- 'biofuel_mandate', 'tariff', 'trade_deal', 'traceability', etc.
  description STRING,
  impact_score FLOAT64,
  passage_probability FLOAT64,
  soybean_oil_demand_impact_pct FLOAT64,
  price_impact_per_lb FLOAT64,
  compliance_region STRING,
  compliance_score FLOAT64,
  cost_impact_per_mt FLOAT64,
  deadline_date DATE,
  risk_level STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY event_date
CLUSTER BY event_type;

-- Tariff Data
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.tariff_data` (
  date DATE NOT NULL,
  country STRING NOT NULL,
  tariff_rate FLOAT64,
  commodity_type STRING,
  impact_per_mt FLOAT64,
  source STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY country;

-- Trade Deals
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.trade_deals` (
  deal_id STRING NOT NULL,
  deal_name STRING NOT NULL,
  countries STRING,  -- Comma-separated or JSON
  status STRING,
  signed_date DATE,
  effective_date DATE,
  soy_export_commitment_mt FLOAT64,
  impact_score FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY signed_date;

-- All Bills (Congressional bills filtered for soy relevance)
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.all_bills` (
  bill_id STRING NOT NULL,
  bill_number STRING NOT NULL,
  title STRING NOT NULL,
  status STRING,
  passage_probability FLOAT64,
  soy_relevance_score FLOAT64,
  demand_impact_pct FLOAT64,
  introduced_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY introduced_date
CLUSTER BY soy_relevance_score;

-- Lobbying Data
CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.lobbying` (
  date DATE NOT NULL,
  organization STRING NOT NULL,
  amount FLOAT64,
  bill_id STRING,
  issue_category STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY organization;

-- Create currency_impact table for FX waterfall visualization
-- Tracks 5 FX pairs: USD/BRL, USD/ARS, USD/MYR, USD/IDR, USD/CNY

CREATE TABLE IF NOT EXISTS `cbi-v14.forecasting_data_warehouse.currency_impact` (
  date DATE NOT NULL,
  pair STRING NOT NULL,  -- 'USD/BRL', 'USD/ARS', 'USD/MYR', 'USD/IDR', 'USD/CNY'
  close_rate FLOAT64 NOT NULL,
  pct_change FLOAT64,  -- Day-over-day % change
  impact_score FLOAT64,  -- Weighted procurement cost impact (derived metric)
  source_name STRING,  -- 'TradingEconomics', 'YahooFinance', 'Investing.com', etc.
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY pair;

