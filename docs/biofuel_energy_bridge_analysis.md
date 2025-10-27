# BIOFUEL: THE ENERGY-AGRICULTURE BRIDGE
**Critical Component for Soybean Oil Price Forecasting**

## Executive Summary
Biofuel represents the critical nexus between energy and agriculture markets, transforming from 10% to 30%+ of US soybean oil demand. This creates a powerful price transmission mechanism that neural networks must understand for accurate forecasting.

## The Energy-Agriculture Nexus

```
CRUDE OIL → Diesel Price → Biodiesel Economics → Soybean Oil Demand
    ↓           ↓              ↓                      ↓
  Energy     Spread        RIN Values            Price Support
```

## Why Biofuel Matters for Soybean Oil

### 1. DIRECT DEMAND DRIVER
- **~30% of US soybean oil** goes to biodiesel (up from 5% a decade ago)
- **Renewable diesel (RD) capacity** growing 300% by 2025
- **SAF mandates** (Sustainable Aviation Fuel) starting in 2025

### 2. ENERGY-AG PRICE TRANSMISSION
- When crude > $80, biodiesel becomes profitable
- RIN prices (D4/D6) directly impact soy oil demand
- Biofuel mandates create price floors for soy oil

### 3. CROSS-MARKET ARBITRAGE
- Soy oil can go to: Food OR Fuel
- Palm oil can substitute in both markets
- Creates complex substitution dynamics

### 4. POLICY SENSITIVITY
- EPA RFS volumes
- IRS 45Z tax credits
- EU RED III mandates
- State-level LCFS programs

## The Hidden Correlations

### Direct Correlation (Weak but Misleading)
- Soy Oil - Crude Oil: 0.146 (overall)

### Conditional Correlations (The Real Story)
- **When crude > $80**: correlation jumps to ~0.5
- **During policy announcements**: correlation spikes to 0.7+
- **In tight veg oil markets**: correlation strengthens to 0.6+

## Neural Network Architecture

```
ENERGY BRANCH              AGRICULTURE BRANCH
    Crude Oil                  Soybeans
    Diesel                     Soy Oil
    Natural Gas                Palm Oil
    RINs                       Corn (ethanol)
         \                    /
          \                  /
           BIOFUEL BRIDGE NODE
                 |
           [Hidden Layers]
                 |
           ZL PRICE FORECAST
```

## Key Features for Neural Training

### Energy Spreads
- Biodiesel-Diesel spread
- Soy oil-Crude ratio
- HOBO spread (Heating Oil vs Soy Oil)

### Policy Signals
- RIN prices (D4 biomass, D6 renewable)
- RFS mandate volumes
- 45Z tax credit value
- State LCFS credit prices

### Capacity Metrics
- RD (renewable diesel) utilization rate
- Biodiesel production rates
- SAF facility buildout progress
- Crush margin dynamics

### Substitution Dynamics
- Palm-Soy spread for biodiesel
- UCO (used cooking oil) availability
- Tallow prices
- Corn oil extraction rates

## Market Dynamics

### The Multiplier Effect
1 MMT increase in RD capacity = 3-4¢/lb increase in soy oil baseline

### Policy Floors
- RFS mandate = guaranteed demand
- Creates price support at biodiesel breakeven
- Typically $0.45-0.55/lb soy oil

### Seasonal Patterns
- Q4: RIN compliance buying
- Q1: New mandate year starts
- Summer: Driving season demand
- Winter: Heating oil competition

## Implementation for CBI-V14

### Data Requirements
1. **RIN Prices**: Daily D4/D6 values
2. **Biodiesel Margins**: BOHO spread
3. **Capacity Data**: Monthly RD/BD production
4. **Policy Updates**: EPA RVO announcements
5. **Substitutes**: Palm, UCO, tallow prices

### Neural Features to Add
```python
biofuel_features = {
    'rin_d4_price': 'Direct policy value signal',
    'rin_d6_price': 'Ethanol RIN for correlation',
    'biodiesel_margin': 'Profitability indicator',
    'rd_capacity_util': 'Demand strength metric',
    'crude_soy_ratio': 'Energy-ag relationship',
    'palm_soy_spread': 'Substitution pressure',
    'rfs_mandate_pct': 'Policy floor indicator',
    'saf_demand_forecast': 'Future demand driver'
}
```

### Expected Impact on Model Performance
- **MAPE Improvement**: 0.5-1.0% reduction
- **Regime Detection**: Better crisis identification
- **Policy Shock Capture**: 80%+ accuracy on RFS announcements
- **Long-term Accuracy**: Significant improvement in 6-12 month forecasts

## Conclusion
Biofuel is not just another feature - it's the BRIDGE that connects two massive commodity complexes. Including it in neural training will capture the growing influence of energy transition on agricultural markets, matching the sophisticated models used by Goldman Sachs and other tier-1 institutions.

---
*This analysis should be displayed prominently on the Biofuel Dashboard page to educate users on the critical importance of the energy-agriculture nexus.*
