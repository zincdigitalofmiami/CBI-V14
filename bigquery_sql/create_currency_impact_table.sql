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

