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

