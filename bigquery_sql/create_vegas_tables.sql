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

