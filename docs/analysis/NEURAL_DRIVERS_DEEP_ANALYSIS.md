---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🧠 NEURAL DRIVERS - The Hidden Layer Analysis
**Going DEEPER than surface correlations**
**Date: November 6, 2025**

---

## 🎯 THE PHILOSOPHY: DRIVERS BEHIND THE DRIVERS

Instead of: `Dollar Index → Soy Price`
We need: `[Employment + Inflation + Risk + Flows] → Dollar → Soy Price`

---

## 💵 DOLLAR INDEX DEEP DRIVERS

### Layer 1: What Drives DXY
```
DXY Movement = f(
  Interest_Rate_Differential +
  Risk_Sentiment +
  Trade_Balance +
  Capital_Flows +
  Geopolitical_Events
)
```

### Layer 2: What We Need to Collect

#### A. INTEREST RATE DIFFERENTIALS
```sql
-- Real yield spreads drive currency
CREATE OR REPLACE TABLE `cbi-v14.models_v4.rate_differentials` AS
SELECT 
  date,
  -- US vs Major Trading Partners
  us_10y_yield - german_10y_yield as us_eur_spread,
  us_10y_yield - japan_10y_yield as us_jpy_spread,
  us_2y_yield - german_2y_yield as us_eur_2y_spread,
  
  -- Real rates (inflation-adjusted)
  us_10y_yield - us_cpi_yoy as us_real_yield,
  german_10y_yield - eu_cpi_yoy as eu_real_yield,
  
  -- Rate expectations
  fed_funds_futures_3m - fed_funds_rate as fed_hike_probability,
  ecb_rate_expectations,
  boj_rate_expectations
FROM multiple_sources
```

**Data Sources Needed:**
- [ ] German/EU yields (ECB data)
- [ ] Japan yields (BOJ data)
- [ ] Fed Funds futures curve
- [ ] SOFR forwards
- [ ] Eurodollar futures

#### B. RISK SENTIMENT DRIVERS
```sql
-- Risk-on/Risk-off drives dollar as safe haven
CREATE OR REPLACE TABLE `cbi-v14.models_v4.risk_sentiment_drivers` AS
SELECT
  date,
  -- Credit spreads
  investment_grade_spread,
  high_yield_spread,
  em_sovereign_spread,
  
  -- Equity indicators
  sp500_put_call_ratio,
  nasdaq_advance_decline,
  emerging_markets_etf_flows,
  
  -- Safe haven flows
  gold_etf_inflows,
  treasury_etf_inflows,
  yen_positioning,
  swiss_franc_flows
```

**Data Sources:**
- [ ] FRED: Credit spreads (LQD, HYG, EMB)
- [ ] CBOE: Put/call ratios
- [ ] Bloomberg: Flow data
- [ ] CFTC: Currency positioning

#### C. CAPITAL FLOW DYNAMICS
```sql
-- Actual money movement drives currency
CREATE OR REPLACE TABLE `cbi-v14.models_v4.capital_flows` AS
SELECT
  date,
  -- Foreign investment in US
  treasury_foreign_holdings_change,
  foreign_direct_investment,
  portfolio_investment_flows,
  
  -- US investment abroad
  us_outbound_investment,
  repatriation_flows,
  
  -- Trade dynamics
  trade_balance,
  current_account,
  china_treasury_holdings  -- Biggest holder
```

---

## 🏦 FED DECISION DEEP DRIVERS

### Layer 1: What Drives Fed Policy
```
Fed_Decision = f(
  Employment_Dynamics +
  Inflation_Components +
  Financial_Conditions +
  Global_Risks +
  Political_Pressure
)
```

### Layer 2: Neural Inputs

#### A. EMPLOYMENT BEYOND HEADLINE
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.employment_drivers` AS
SELECT
  date,
  -- Deeper than unemployment rate
  nonfarm_payrolls_3m_avg,
  average_hourly_earnings_yoy,
  labor_force_participation_rate,
  quits_rate,  -- JOLTS data
  job_openings_to_unemployed_ratio,
  initial_claims_4wk_avg,
  continuing_claims_trend,
  
  -- Wage pressure indicators
  employment_cost_index,
  unit_labor_costs,
  productivity_growth
```

#### B. INFLATION COMPONENTS
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.inflation_drivers` AS
SELECT
  date,
  -- Not just CPI
  core_pce_yoy,  -- Fed's preferred
  trimmed_mean_pce,
  sticky_price_cpi,
  
  -- Forward-looking
  5y5y_inflation_expectations,
  michigan_inflation_expectations,
  tips_breakevens_5y,
  
  -- Supply chain
  ism_prices_paid,
  ppi_final_demand,
  freight_costs_index
```

---

## 🥇 CRUSH MARGIN DEEP DRIVERS

### What Drives Crush Spreads
```
Crush_Margin = f(
  Processing_Capacity +
  Meal_Demand +
  Oil_Premium +
  Logistics_Costs +
  Energy_Prices
)
```

### Neural Inputs Needed
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.crush_drivers` AS
SELECT
  date,
  -- Processing dynamics
  us_crushing_capacity_utilization,
  argentina_crush_capacity,
  brazil_crush_capacity,
  
  -- Meal demand drivers
  livestock_prices,  -- Drives feed demand
  hog_corn_ratio,
  cattle_corn_ratio,
  chinese_hog_inventory,
  
  -- Oil premium drivers
  biodiesel_margins,
  palm_soy_spread,
  canola_soy_spread,
  
  -- Logistics
  rail_rates_illinois_to_gulf,
  barge_rates_mississippi,
  truck_availability_index
```

---

## 🇨🇳 CHINA IMPORT DEEP DRIVERS

### What Drives China's Buying
```
China_Imports = f(
  Domestic_Crop_Production +
  Hog_Inventory_Cycle +
  Strategic_Reserves +
  Brazil_Basis +
  Political_Tensions
)
```

### Neural Inputs
```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.china_import_drivers` AS
SELECT
  date,
  -- Domestic supply
  china_soybean_production_estimate,
  china_corn_production,
  weather_stress_index_northeast_china,
  
  -- Demand drivers  
  china_hog_inventory_yoy,
  china_sow_inventory,  -- Leading indicator
  pork_prices_china,
  african_swine_fever_cases,
  
  -- Competition
  brazil_soybean_basis,
  brazil_export_lineup,  -- Vessel count
  argentina_farmer_selling_pace,
  
  -- Strategic
  estimated_state_reserves,
  dalian_soybean_futures_curve,
  rmb_devaluation_pressure
```

---

## 🔬 TESTING & WEIGHTING METHODOLOGY

### 1. MULTI-LAYER CORRELATION TESTING
```sql
-- Don't just correlate to price, correlate through the chain
CREATE OR REPLACE MODEL `cbi-v14.models_v4.neural_path_model`
OPTIONS(
  model_type='BOOSTED_TREE_REGRESSOR',
  input_label_cols=['target_1w']
) AS
WITH neural_features AS (
  SELECT
    date,
    
    -- Layer 3: Deep drivers
    us_eur_spread,
    fed_hike_probability,
    high_yield_spread,
    
    -- Layer 2: Mid drivers  
    (us_eur_spread * 0.3 + fed_hike_probability * 0.4 + high_yield_spread * 0.3) as dollar_pressure,
    
    -- Layer 1: Surface drivers
    dollar_index,
    
    -- Target
    target_1w
  FROM joined_data
)
SELECT * FROM neural_features;

-- Extract feature importance at EACH layer
SELECT 
  feature,
  importance_gain,
  CASE 
    WHEN feature IN ('us_eur_spread', 'fed_hike_probability') THEN 'Layer3_Deep'
    WHEN feature IN ('dollar_pressure') THEN 'Layer2_Mid'
    WHEN feature IN ('dollar_index') THEN 'Layer1_Surface'
  END as layer
FROM ML.FEATURE_IMPORTANCE(MODEL `cbi-v14.models_v4.neural_path_model`)
ORDER BY importance_gain DESC;
```

### 2. DYNAMIC WEIGHT CALCULATION
```sql
-- Weights based on rolling correlation strength
CREATE OR REPLACE VIEW `cbi-v14.models_v4.vw_dynamic_weights` AS
WITH rolling_correlations AS (
  SELECT
    date,
    -- 30-day rolling correlations
    CORR(us_eur_spread, dollar_index) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as spread_to_dollar_corr,
    
    CORR(dollar_index, target_1w) OVER (
      ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as dollar_to_target_corr,
    
    -- Calculate path strength
    ABS(spread_to_dollar_corr * dollar_to_target_corr) as path_strength
  FROM data
)
SELECT 
  date,
  -- Dynamic weights based on correlation strength
  path_strength / SUM(path_strength) OVER (PARTITION BY date) as dynamic_weight
FROM rolling_correlations;
```

### 3. CAUSALITY TESTING (Granger)
```python
# Test if X actually causes Y, not just correlates
from statsmodels.tsa.stattools import grangercausalitytests

def test_causality_chain():
    # Test each link in the chain
    results = {}
    
    # Does rate spread Granger-cause dollar?
    results['spread_causes_dollar'] = grangercausalitytests(
        data[['dollar_index', 'us_eur_spread']], 
        maxlag=5
    )
    
    # Does dollar Granger-cause soy price?
    results['dollar_causes_soy'] = grangercausalitytests(
        data[['soy_price', 'dollar_index']], 
        maxlag=5
    )
    
    return results
```

---

## 📊 TOP 10 PUSHERS - FULL NEURAL TREATMENT

### Ranked by Impact with Deep Drivers

1. **CRUSH MARGIN (0.961)**
   - Layer 2: Processing capacity, meal demand, oil premium
   - Layer 3: Livestock cycles, biodiesel policy, rail logistics

2. **CHINA IMPORTS (-0.813)**
   - Layer 2: Hog cycle, domestic production, Brazil competition
   - Layer 3: ASF outbreaks, weather, state reserves

3. **DOLLAR INDEX (-0.658)**
   - Layer 2: Rate differentials, risk sentiment, flows
   - Layer 3: Employment, inflation components, Fed dots

4. **FED FUNDS RATE (-0.656)**
   - Layer 2: Employment, inflation, financial conditions
   - Layer 3: JOLTS data, PCE components, credit spreads

5. **TRADE WAR INTENSITY (0.648)**
   - Layer 2: Tweet sentiment, retaliation probability
   - Layer 3: Election polls, lobby spending, China hawks

6. **TARIFF THREAT (0.647)**
   - Layer 2: Policy momentum, congressional support
   - Layer 3: Trade deficit, manufacturing employment

7. **CHINA TARIFF RATE (-0.626)**
   - Layer 2: Negotiation progress, phase deal status
   - Layer 3: Ag purchases, tech restrictions

8. **BIOFUEL CASCADE (-0.601)**
   - Layer 2: RIN prices, blending margins, mandates
   - Layer 3: Gasoline demand, ethanol stocks, corn basis

9. **CRUDE OIL (0.584)**
   - Layer 2: OPEC decisions, US production, inventory
   - Layer 3: Rig counts, DUCs, crack spreads

10. **VIX (0.398)**
    - Layer 2: Term structure, put/call skew
    - Layer 3: Correlation breakdown, dispersion

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Data Collection (Week 1)
```python
# Priority data sources to add
data_sources = {
    'fred_api': [
        'DGS10', 'DGS2',      # US yields
        'DEXUSEU',            # EUR/USD
        'BAMLH0A0HYM2',       # High yield spread
        'VIXCLS',             # VIX
        'DCOILWTICO'          # WTI Crude
    ],
    'ecb_api': [
        'german_10y',
        'ecb_rate_expectations'
    ],
    'cme_api': [
        'fed_funds_futures',
        'eurodollar_futures'
    ]
}
```

### Phase 2: Build Neural Features (Week 2)
```sql
-- Create deep feature engineering pipeline
CREATE OR REPLACE PROCEDURE `cbi-v14.models_v4.sp_build_neural_features`()
BEGIN
  -- Layer 3: Raw inputs
  CALL build_rate_differentials();
  CALL build_risk_indicators();
  CALL build_flow_metrics();
  
  -- Layer 2: Composite indicators  
  CALL build_dollar_drivers();
  CALL build_fed_drivers();
  
  -- Layer 1: Final features
  CALL combine_neural_layers();
END;
```

### Phase 3: Test & Weight (Week 3)
- Granger causality tests
- Rolling correlation windows
- Dynamic weight calculation
- Cross-validation on regimes

---

## 💡 THIS IS THE NEXT LEVEL

**Current approach:** Dollar → Soy Price

**Neural approach:** 
```
Employment Data → Fed Expectations → Rate Differentials → 
Capital Flows → Dollar Strength → Commodity Prices →
Crush Margins → Soybean Oil Price
```

**This is how quant funds think!** Multi-layer causality, not simple correlation.







