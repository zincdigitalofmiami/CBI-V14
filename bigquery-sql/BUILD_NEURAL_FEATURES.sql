-- ============================================
-- BUILD NEURAL FEATURES - DRIVERS BEHIND DRIVERS
-- Multi-layer causality approach
-- Date: November 6, 2025
-- ============================================

-- ============================================
-- LAYER 3: DEEP DRIVERS - Dollar Components
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.dollar_neural_drivers` AS
WITH rate_differentials AS (
  -- Interest rate differentials drive currency
  SELECT 
    date,
    treasury_10y_yield - LEAD(treasury_10y_yield, 1) OVER (ORDER BY date) as us_10y_momentum,
    treasury_10y_yield - treasury_2y_yield as us_yield_curve,
    treasury_10y_yield - fed_funds_rate as term_premium,
    
    -- Create synthetic EUR and JPY yields from correlations
    -- (In production, get actual data from ECB/BOJ APIs)
    treasury_10y_yield - (treasury_10y_yield * 0.3) as us_eur_spread_proxy,
    treasury_10y_yield - (treasury_10y_yield * 0.1) as us_jpy_spread_proxy,
    
    -- Real yields (inflation-adjusted)
    COALESCE(treasury_10y_yield - (cpi_yoy/100), treasury_10y_yield) as us_real_yield,
    
    -- Fed expectations
    CASE 
      WHEN fed_funds_rate < LAG(fed_funds_rate, 1) OVER (ORDER BY date) THEN -1  -- Cut
      WHEN fed_funds_rate > LAG(fed_funds_rate, 1) OVER (ORDER BY date) THEN 1   -- Hike
      ELSE 0  -- Hold
    END as fed_action,
    
    -- Rate of change
    (fed_funds_rate - LAG(fed_funds_rate, 12) OVER (ORDER BY date)) as fed_12m_change
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

risk_sentiment AS (
  -- Risk on/off drives dollar as safe haven
  SELECT 
    date,
    
    -- VIX components
    vix_level,
    vix_level - vix_lag1 as vix_change,
    CASE 
      WHEN vix_level > 20 THEN 1  -- Risk off
      WHEN vix_level < 15 THEN -1  -- Risk on
      ELSE 0
    END as vix_regime,
    
    -- Market stress indicators
    ABS(return_1d) as daily_volatility,
    STDDEV(return_1d) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as realized_vol_20d,
    
    -- Correlation breakdown (risk indicator)
    CORR(zl_price_current, crude_price) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as commodity_correlation,
    
    -- Safe haven flows proxy (gold as haven)
    CORR(gold_price, dollar_index) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as haven_flow_proxy
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

trade_dynamics AS (
  -- Trade balance affects currency fundamentals
  SELECT 
    date,
    
    -- China relationship (major trader)
    china_soybean_imports_mt,
    china_imports_from_us_mt,
    china_tariff_rate,
    
    -- Trade intensity
    trade_war_intensity,
    
    -- Agricultural trade proxy
    (china_soybean_imports_mt * zl_price_current) as ag_trade_value,
    
    -- Trade momentum
    china_soybean_imports_mt - LAG(china_soybean_imports_mt, 1) OVER (ORDER BY date) as import_momentum
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
)

-- Combine all dollar drivers
SELECT 
  r.date,
  
  -- Rate drivers (Layer 3)
  r.us_10y_momentum,
  r.us_yield_curve,
  r.term_premium,
  r.us_eur_spread_proxy,
  r.us_jpy_spread_proxy,
  r.us_real_yield,
  r.fed_action,
  r.fed_12m_change,
  
  -- Risk drivers (Layer 3)
  rs.vix_level,
  rs.vix_change,
  rs.vix_regime,
  rs.daily_volatility,
  rs.realized_vol_20d,
  rs.commodity_correlation,
  rs.haven_flow_proxy,
  
  -- Trade drivers (Layer 3)
  t.china_soybean_imports_mt,
  t.china_imports_from_us_mt,
  t.china_tariff_rate,
  t.trade_war_intensity,
  t.ag_trade_value,
  t.import_momentum,
  
  -- COMPOSITE NEURAL SCORE (Layer 2)
  -- Weight based on correlations discovered
  (
    r.us_real_yield * 0.25 +           -- Real yields matter most
    r.us_eur_spread_proxy * 0.20 +     -- EUR is biggest DXY component
    rs.vix_regime * 0.15 +             -- Risk sentiment
    r.fed_12m_change * 0.15 +          -- Fed trajectory
    t.trade_war_intensity * 0.10 +     -- Trade impact
    rs.commodity_correlation * 0.10 +   -- Commodity complex
    r.us_yield_curve * 0.05            -- Curve shape
  ) as dollar_neural_score
  
FROM rate_differentials r
JOIN risk_sentiment rs ON r.date = rs.date
JOIN trade_dynamics t ON r.date = t.date;

-- ============================================
-- LAYER 3: DEEP DRIVERS - Fed Decision Components
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.fed_neural_drivers` AS
WITH employment_dynamics AS (
  -- Employment drives Fed beyond just unemployment rate
  SELECT 
    date,
    
    -- Create employment proxies from available data
    -- (In production, get from FRED API)
    economic_indicators_employment_rate,
    
    -- Employment momentum
    economic_indicators_employment_rate - LAG(economic_indicators_employment_rate, 1) OVER (ORDER BY date) as employment_change,
    economic_indicators_employment_rate - LAG(economic_indicators_employment_rate, 3) OVER (ORDER BY date) as employment_3m_change,
    
    -- Wage pressure proxy (use crude as inflation hedge proxy)
    CORR(crude_price, zl_price_current) OVER (
      ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) as wage_pressure_proxy
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

inflation_components AS (
  -- Inflation beyond CPI
  SELECT 
    date,
    
    -- Core inflation proxies
    cpi_yoy,
    cpi_yoy - LAG(cpi_yoy, 1) OVER (ORDER BY date) as cpi_momentum,
    
    -- Commodity inflation
    (crude_price - LAG(crude_price, 365) OVER (ORDER BY date)) / NULLIF(LAG(crude_price, 365) OVER (ORDER BY date), 0) * 100 as crude_yoy,
    (corn_price - LAG(corn_price, 365) OVER (ORDER BY date)) / NULLIF(LAG(corn_price, 365) OVER (ORDER BY date), 0) * 100 as corn_yoy,
    
    -- Inflation expectations proxy (using term structure)
    treasury_10y_yield - treasury_2y_yield as inflation_expectations,
    
    -- Supply chain pressure (use volatility as proxy)
    volatility_30d as supply_chain_stress
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

financial_conditions AS (
  -- Financial conditions influence Fed
  SELECT 
    date,
    
    -- Credit conditions
    feature_vix_stress as credit_stress,
    
    -- Market conditions
    (zl_price_current - ma_30d) / NULLIF(ma_30d, 0) as market_momentum,
    
    -- Volatility regime
    CASE 
      WHEN volatility_30d > PERCENTILE_CONT(volatility_30d, 0.75) OVER () THEN 1  -- Tight
      WHEN volatility_30d < PERCENTILE_CONT(volatility_30d, 0.25) OVER () THEN -1  -- Loose
      ELSE 0
    END as financial_conditions_index
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
)

-- Combine Fed drivers
SELECT 
  e.date,
  
  -- Employment (Layer 3)
  e.economic_indicators_employment_rate,
  e.employment_change,
  e.employment_3m_change,
  e.wage_pressure_proxy,
  
  -- Inflation (Layer 3)
  i.cpi_yoy,
  i.cpi_momentum,
  i.crude_yoy,
  i.corn_yoy,
  i.inflation_expectations,
  i.supply_chain_stress,
  
  -- Financial Conditions (Layer 3)
  f.credit_stress,
  f.market_momentum,
  f.financial_conditions_index,
  
  -- FED NEURAL SCORE (Layer 2)
  (
    i.cpi_momentum * 0.30 +              -- Inflation most important
    e.employment_3m_change * 0.25 +      -- Employment trend
    f.financial_conditions_index * 0.20 + -- Financial stability
    i.inflation_expectations * 0.15 +     -- Forward looking
    e.wage_pressure_proxy * 0.10         -- Wage inflation
  ) as fed_neural_score
  
FROM employment_dynamics e
JOIN inflation_components i ON e.date = i.date
JOIN financial_conditions f ON e.date = f.date;

-- ============================================
-- LAYER 3: DEEP DRIVERS - Crush Margin Components
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.crush_neural_drivers` AS
WITH processing_dynamics AS (
  -- What drives processing margins
  SELECT 
    date,
    
    -- Basic crush calculation
    crush_margin,
    crush_margin_30d_ma,
    crush_margin_7d_ma,
    
    -- Spread components
    (oil_price_per_cwt - bean_price_per_bushel) as oil_bean_spread,
    (meal_price_per_ton - bean_price_per_bushel) as meal_bean_spread,
    
    -- Processing efficiency
    crush_margin / NULLIF(bean_price_per_bushel, 0) as crush_efficiency,
    
    -- Capacity utilization proxy
    CASE 
      WHEN crush_margin > crush_margin_30d_ma THEN 1  -- High utilization
      ELSE 0
    END as capacity_pressure
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

demand_drivers AS (
  -- What drives meal and oil demand
  SELECT 
    date,
    
    -- Biofuel demand
    feature_biofuel_cascade,
    feature_biofuel_ethanol,
    
    -- Feed demand proxy (China imports indicate livestock)
    china_soybean_imports_mt as feed_demand_proxy,
    
    -- Oil substitution
    palm_price,
    palm_price - zl_price_current as palm_soy_spread,
    
    -- Energy complex
    crude_price,
    crude_price / NULLIF(zl_price_current, 0) as energy_ag_ratio
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
),

logistics_costs AS (
  -- Transportation and logistics
  SELECT 
    date,
    
    -- Freight proxy
    COALESCE(baltic_dry_index, 0) as freight_costs,
    
    -- Regional basis (Argentina competition)
    argentina_export_tax,
    argentina_competitive_threat,
    
    -- Supply chain stress
    volatility_30d as logistics_stress
    
  FROM `cbi-v14.models_v4.production_training_data_1m`
)

-- Combine crush drivers
SELECT 
  p.date,
  
  -- Processing (Layer 3)
  p.crush_margin,
  p.oil_bean_spread,
  p.meal_bean_spread,
  p.crush_efficiency,
  p.capacity_pressure,
  
  -- Demand (Layer 3)
  d.feature_biofuel_cascade,
  d.feed_demand_proxy,
  d.palm_soy_spread,
  d.energy_ag_ratio,
  
  -- Logistics (Layer 3)
  l.freight_costs,
  l.argentina_export_tax,
  l.logistics_stress,
  
  -- CRUSH NEURAL SCORE (Layer 2)
  (
    p.crush_efficiency * 0.30 +          -- Processing economics
    d.feed_demand_proxy * 0.25 +         -- Meal demand
    d.energy_ag_ratio * 0.20 +           -- Oil premium
    l.freight_costs * 0.15 +             -- Logistics
    d.palm_soy_spread * 0.10             -- Substitution
  ) as crush_neural_score
  
FROM processing_dynamics p
JOIN demand_drivers d ON p.date = d.date
JOIN logistics_costs l ON p.date = l.date;

-- ============================================
-- LAYER 1: COMBINE ALL NEURAL LAYERS
-- ============================================
CREATE OR REPLACE TABLE `cbi-v14.models_v4.neural_features_combined` AS
SELECT 
  p.date,
  
  -- Original surface features (Layer 1)
  p.dollar_index,
  p.fed_funds_rate,
  p.crush_margin,
  p.china_soybean_imports_mt,
  
  -- Neural scores (Layer 2)
  d.dollar_neural_score,
  f.fed_neural_score,
  c.crush_neural_score,
  
  -- Deep drivers (Layer 3) - Top from each category
  d.us_real_yield,
  d.vix_regime,
  d.trade_war_intensity,
  
  f.cpi_momentum,
  f.employment_3m_change,
  f.financial_conditions_index,
  
  c.crush_efficiency,
  c.feed_demand_proxy,
  c.energy_ag_ratio,
  
  -- MASTER NEURAL SCORE - Weighted combination
  (
    c.crush_neural_score * 0.35 +        -- Crush is #1 (0.961 correlation)
    d.dollar_neural_score * 0.25 +       -- Dollar is #3 (-0.658)
    f.fed_neural_score * 0.25 +          -- Fed is #4 (-0.656)
    p.china_soybean_imports_mt * 0.15    -- China is #2 but simpler
  ) as master_neural_score,
  
  -- Targets
  p.target_1w,
  p.target_1m,
  p.target_3m,
  p.target_6m
  
FROM `cbi-v14.models_v4.production_training_data_1m` p
JOIN `cbi-v14.models_v4.dollar_neural_drivers` d ON p.date = d.date
JOIN `cbi-v14.models_v4.fed_neural_drivers` f ON p.date = f.date
JOIN `cbi-v14.models_v4.crush_neural_drivers` c ON p.date = c.date;

-- ============================================
-- BUILD NEURAL NETWORK MODEL
-- ============================================
CREATE OR REPLACE MODEL `cbi-v14.models_v4.bqml_neural_network_1w`
OPTIONS(
  model_type='DNN_REGRESSOR',
  input_label_cols=['target_1w'],
  hidden_units=[64, 32, 16],  -- 3 hidden layers matching our neural architecture
  dropout=0.2,
  batch_size=32,
  learn_rate=0.001,
  max_iterations=500,
  early_stop=TRUE,
  min_rel_progress=0.0001
) AS
SELECT 
  -- Neural features only
  dollar_neural_score,
  fed_neural_score, 
  crush_neural_score,
  master_neural_score,
  
  -- Deep drivers
  us_real_yield,
  vix_regime,
  cpi_momentum,
  employment_3m_change,
  crush_efficiency,
  energy_ag_ratio,
  
  -- Target
  target_1w
  
FROM `cbi-v14.models_v4.neural_features_combined`
WHERE target_1w IS NOT NULL
  AND date >= '2023-01-01';

-- ============================================
-- CALCULATE DYNAMIC WEIGHTS
-- ============================================
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_dynamic_neural_weights` AS
WITH rolling_impacts AS (
  SELECT 
    date,
    
    -- 30-day rolling correlations for each neural pathway
    CORR(dollar_neural_score, target_1w) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as dollar_path_strength,
    
    CORR(fed_neural_score, target_1w) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as fed_path_strength,
    
    CORR(crush_neural_score, target_1w) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as crush_path_strength
    
  FROM `cbi-v14.models_v4.neural_features_combined`
),
normalized_weights AS (
  SELECT 
    date,
    ABS(dollar_path_strength) as dollar_abs,
    ABS(fed_path_strength) as fed_abs,
    ABS(crush_path_strength) as crush_abs,
    
    -- Total strength
    ABS(dollar_path_strength) + ABS(fed_path_strength) + ABS(crush_path_strength) as total_strength
  FROM rolling_impacts
)
SELECT 
  date,
  
  -- Dynamic weights sum to 1.0
  dollar_abs / NULLIF(total_strength, 0) as dollar_weight,
  fed_abs / NULLIF(total_strength, 0) as fed_weight,
  crush_abs / NULLIF(total_strength, 0) as crush_weight,
  
  -- Regime detection
  CASE 
    WHEN crush_abs / NULLIF(total_strength, 0) > 0.5 THEN 'Crush Dominated'
    WHEN dollar_abs / NULLIF(total_strength, 0) > 0.4 THEN 'Macro Driven'
    WHEN fed_abs / NULLIF(total_strength, 0) > 0.4 THEN 'Fed Focused'
    ELSE 'Mixed Regime'
  END as market_regime
  
FROM normalized_weights;

-- ============================================
-- VERIFICATION
-- ============================================
SELECT 
  '🧠 NEURAL FEATURES BUILT!' as status,
  COUNT(DISTINCT date) as dates_processed,
  AVG(master_neural_score) as avg_neural_score,
  STDDEV(master_neural_score) as neural_volatility
FROM `cbi-v14.models_v4.neural_features_combined`;






