# Signal Scoring Manual: Soybean Oil Futures Forecasting Platform

## Core Signal Scoring Principles

All signals in the platform follow these standardized scoring principles:

- **Range**: Most signals are normalized to 0.0-1.0 scale (some correlation indices use -1.0 to 1.0)
- **Interpretation**: Higher values (closer to 1.0) typically indicate bullish conditions for soybean oil prices
- **Crisis Threshold**: Values above 0.8 or below 0.2 typically trigger regime classification changes
- **Update Frequency**: Most signals update daily with market close data

## Big 7 Primary Signals

### 1. VIX Stress (Market Volatility)
**Formula**: `vix_current / 20.0` (capped at 3.0)

**Input Data**:
- Current VIX index value from volatility_data table
- Historical baseline of 20.0 (representing normal market conditions)

**Scoring Logic**:
- 0.0-0.5: Low volatility, stable markets (VIX below 10)
- 0.5-1.0: Normal volatility (VIX 10-20)
- 1.0-1.5: Elevated volatility (VIX 20-30)
- 1.5-2.0: High volatility/market stress (VIX 30-40)
- 2.0-3.0: Extreme volatility/crisis (VIX 40+)

**Crisis Threshold**: > 1.5 (VIX above 30)

**Example**: If VIX = 35, then VIX Stress = 35/20 = 1.75 (high volatility regime)

### 2. Harvest Pace (Supply Fundamentals)
**Formula**: `brazil_production_vs_trend * 0.7 + argentina_production_vs_trend * 0.3` (floored at 0.5)

**Input Data**:
- Brazil production vs historical trend (normalized to 0-1 scale)
- Argentina production vs historical trend (normalized to 0-1 scale)

**Scoring Logic**:
- 0.5-0.6: Severe production issues/drought (bullish for prices)
- 0.6-0.8: Below-average harvest pace (moderately bullish)
- 0.8-1.0: Normal to above-average production (bearish for prices)
- >1.0: Bumper crop (very bearish)

**Crisis Threshold**: < 0.8 (significant supply concerns)

**Example**: Brazil at 65% of trend (0.65) and Argentina at 75% of trend (0.75) = 0.65 × 0.7 + 0.75 × 0.3 = 0.68 (below average)

### 3. China Relations (Trade Dynamics)
**Formula**: `china_trade_tension_index * 0.6 + (1 - china_us_import_share_monthly) * 0.4` (capped at 1.0)

**Input Data**:
- China-US trade tension index (0-1 scale from sentiment analysis)
- China's US import share (percentage converted to 0-1 scale)

**Scoring Logic**:
- 0.0-0.3: Strong trade relations (bearish for US prices)
- 0.3-0.6: Normal trade relations (neutral)
- 0.6-0.8: Elevated tensions (bullish for prices)
- 0.8-1.0: Trade crisis/tariff risk (strongly bullish)

**Crisis Threshold**: > 0.8 (severe trade tension)

**Example**: Trade tension of 0.7 and US import share of 20% (0.2) = 0.7 × 0.6 + (1-0.2) × 0.4 = 0.42 + 0.32 = 0.74 (elevated tension)

### 4. Tariff Threat (Policy Risk)
**Formula**: `(trump_tariff_mentions_7d / 10.0) * 0.7 + china_trade_tension_index * 0.3` (capped at 1.0)

**Input Data**:
- Trump tariff mentions in past 7 days (normalized by dividing by 10)
- China trade tension index (0-1 scale)

**Scoring Logic**:
- 0.0-0.3: Low tariff probability (bearish)
- 0.3-0.6: Background tariff risk (neutral)
- 0.6-0.8: Elevated tariff risk (bullish)
- 0.8-1.0: Imminent tariff action (strongly bullish)

**Crisis Threshold**: > 0.8 (high probability of new tariffs)

**Example**: 7 Trump tariff mentions (0.7 after normalization) and trade tension of 0.6 = 0.7 × 0.7 + 0.6 × 0.3 = 0.49 + 0.18 = 0.67 (elevated risk)

### 5. Geopolitical Volatility Index (GVI)
**Formula**: `vix_current/20.0 * 0.4 + trump_tweet_market_correlation_score * 0.3 + panama_canal_transit_delays_days/15.0 * 0.2 + emerging_market_stress_index * 0.1` (capped at 1.0)

**Input Data**:
- Current VIX (normalized by 20.0 baseline)
- Trump tweet market correlation (0-1 scale)
- Panama Canal transit delays (days, normalized by dividing by 15)
- Emerging market stress index (0-1 scale)

**Scoring Logic**:
- 0.0-0.3: Stable geopolitical environment (bearish)
- 0.3-0.6: Normal geopolitical tension (neutral)
- 0.6-0.8: Elevated geopolitical risk (bullish)
- 0.8-1.0: Geopolitical crisis (strongly bullish)

**Crisis Threshold**: > 0.8 (major geopolitical disruption)

**Example**: VIX at 30 (1.5 normalized), Trump correlation of 0.7, Panama delays of 9 days (0.6 normalized), EM stress of 0.5 = 1.5 × 0.4 + 0.7 × 0.3 + 0.6 × 0.2 + 0.5 × 0.1 = 0.6 + 0.21 + 0.12 + 0.05 = 0.98 (crisis level)

### 6. Biofuel Substitution Cascade (BSC)
**Formula**: `us_rfs_mandate_change_expected * 0.3 + indonesia_b40_mandate_export_impact_mt/3000000.0 * 0.3 + renewable_diesel_margin_spread/150.0 * 0.2 + eu_red_ii_palm_phase_out_acceleration * 0.2` (capped at 1.0)

**Input Data**:
- US RFS mandate expected change (0-1 scale)
- Indonesia B40 mandate impact (MT, normalized by dividing by 3M)
- Renewable diesel margin spread ($/MT, normalized by dividing by 150)
- EU RED II palm phase-out acceleration (boolean converted to 0/1)

**Scoring Logic**:
- 0.0-0.3: Bearish biofuel policy environment
- 0.3-0.6: Neutral biofuel dynamics
- 0.6-0.8: Bullish biofuel policy impact
- 0.8-1.0: Major biofuel demand surge

**Crisis Threshold**: > 0.8 (significant biofuel policy shift)

**Example**: RFS change of 0.5, Indonesia impact of 2.4M MT (0.8 normalized), RD margin of 120 (0.8 normalized), EU phase-out true (1.0) = 0.5 × 0.3 + 0.8 × 0.3 + 0.8 × 0.2 + 1.0 × 0.2 = 0.15 + 0.24 + 0.16 + 0.2 = 0.75 (bullish)

### 7. Hidden Correlation Index (HCI)
**Formula**: `zl_correlation_with_crude_30d * 0.25 + zl_correlation_with_dxy_30d * -0.25 + soy_palm_price_ratio_correlation_30d * 0.25 + vix_trump_correlation_24h * 0.25` (range: -1.0 to 1.0)

**Input Data**:
- ZL correlation with crude oil (30-day, -1 to 1 range)
- ZL correlation with USD index (30-day, -1 to 1 range, inverted)
- Soy-palm price ratio correlation (30-day, -1 to 1 range)
- VIX-Trump tweet correlation (24-hour, -1 to 1 range)

**Scoring Logic**:
- -1.0 to -0.6: Strong negative hidden correlations (bearish)
- -0.6 to -0.2: Moderate negative correlations (slightly bearish)
- -0.2 to 0.2: Neutral/normal correlation patterns
- 0.2 to 0.6: Moderate positive correlations (slightly bullish)
- 0.6 to 1.0: Strong positive hidden correlations (bullish)

**Crisis Threshold**: > 0.8 or < -0.8 (extreme correlation regime shift)

**Example**: ZL-crude correlation of 0.7, ZL-USD correlation of 0.2 (inverted to -0.2), soy-palm correlation of 0.5, VIX-Trump correlation of 0.6 = 0.7 × 0.25 + (-0.2) × 0.25 + 0.5 × 0.25 + 0.6 × 0.25 = 0.175 - 0.05 + 0.125 + 0.15 = 0.4 (moderately positive)

## Composite Signal Categories

### Weather Composite Signal
**Formula**:
```sql
CASE
    WHEN brazil_drought_severity_index > 0.7 AND brazil_critical_season_precip < 10 THEN 0.85
    WHEN us_planting_season_stress > 0.6 AND us_midwest_precip_avg < 20 THEN 0.80
    WHEN argentina_harvest_stress_index > 0.5 THEN 0.75
    ELSE 0.50
END
```

**Input Data**:
- Brazil drought severity index (0-1 scale)
- Brazil critical season precipitation (mm)
- US planting season stress index (0-1 scale)
- US Midwest average precipitation (mm)
- Argentina harvest stress index (0-1 scale)

**Scoring Logic**:
- 0.5: Normal weather conditions (neutral)
- 0.75: Moderate weather stress (bullish)
- 0.8: Significant US weather issues (bullish)
- 0.85: Severe Brazil drought (strongly bullish)

**Crisis Threshold**: None directly; feeds into Harvest Pace primary signal

### Supply/Demand Composite Signal
**Formula**:
```sql
CASE
    WHEN global_soybean_stocks_to_use < 0.08 THEN 0.90
    WHEN us_ending_stocks_mt < 200 THEN 0.80
    WHEN brazil_production_vs_trend < -0.05 THEN 0.85
    WHEN china_import_vs_historical_avg > 1.2 THEN 0.75
    ELSE 0.50
END
```

**Input Data**:
- Global soybean stocks-to-use ratio
- US ending stocks (million metric tons)
- Brazil production vs trend (percentage deviation)
- China import vs historical average (ratio)

**Scoring Logic**:
- 0.5: Balanced supply/demand (neutral)
- 0.75: Strong China import demand (bullish)
- 0.8: Tight US stocks (bullish)
- 0.85: Brazil production shortfall (strongly bullish)
- 0.9: Critically tight global supplies (strongly bullish)

**Crisis Threshold**: None directly; feeds into other primary signals

### Crush Economics Composite Signal
**Formula**:
```sql
CASE
    WHEN us_crush_margin_cents_per_bushel > 75 THEN 0.80
    WHEN us_crush_margin_cents_per_bushel < 25 THEN 0.20
    ELSE 0.50
END
```

**Input Data**:
- US crush margin (cents per bushel)

**Scoring Logic**:
- 0.2: Poor crush margins (bearish)
- 0.5: Normal crush economics (neutral)
- 0.8: Strong crush margins (bullish)

**Crisis Threshold**: None directly

### Trump Geopolitical Composite Signal
**Formula**:
```sql
CASE
    WHEN trump_tariff_mentions_7d > 5 AND china_trade_tension_index > 0.8 THEN 0.15  -- Bearish for US
    WHEN trump_agriculture_mentions_7d > 3 AND farm_bill_legislative_momentum > 0.7 THEN 0.75
    WHEN ice_labor_shortage_risk_score > 0.7 AND ice_seasonal_timing_impact = 'CRITICAL' THEN 0.25
    ELSE 0.50
END
```

**Input Data**:
- Trump tariff mentions in past 7 days
- China trade tension index (0-1 scale)
- Trump agriculture mentions in past 7 days
- Farm bill legislative momentum (0-1 scale)
- ICE labor shortage risk score (0-1 scale)
- ICE seasonal timing impact (categorical)

**Scoring Logic**:
- 0.15: High tariff risk (bearish for US producers)
- 0.25: Labor shortage risk (bearish)
- 0.5: Neutral geopolitical environment
- 0.75: Positive agricultural policy momentum (bullish)

**Crisis Threshold**: None directly; feeds into Tariff Threat signal

### China Diversification Composite Signal
**Formula**:
```sql
CASE
    WHEN china_us_import_share_monthly < 0.15 THEN 0.20  -- Severe US displacement
    WHEN china_alternative_supplier_share > 0.20 THEN 0.25  -- Structural US loss
    WHEN china_commitment_compliance_rate < 0.6 THEN 0.30
    ELSE 0.50
END
```

**Input Data**:
- China's US import share (percentage)
- China's alternative supplier share (percentage)
- China's commitment compliance rate (0-1 scale)

**Scoring Logic**:
- 0.2: Severe US displacement (bearish for US producers)
- 0.25: Structural shift to alternative suppliers (bearish)
- 0.3: Poor compliance with purchase commitments (bearish)
- 0.5: Normal trade patterns (neutral)

**Crisis Threshold**: None directly; feeds into China Relations signal

### Biofuel Policy Composite Signal
**Formula**:
```sql
CASE
    WHEN us_rfs_mandate_change_expected > 0.05 THEN 0.85
    WHEN indonesia_b40_mandate_export_impact_mt > 2000000 THEN 0.80
    WHEN eu_red_ii_palm_phase_out_acceleration THEN 0.75
    ELSE 0.50
END
```

**Input Data**:
- US RFS mandate expected change (percentage)
- Indonesia B40 mandate export impact (metric tons)
- EU RED II palm phase-out acceleration (boolean)

**Scoring Logic**:
- 0.5: Stable biofuel policy environment (neutral)
- 0.75: EU palm restrictions (bullish for soy)
- 0.8: Indonesia domestic consumption increase (bullish)
- 0.85: Higher US RFS mandate (strongly bullish)

**Crisis Threshold**: None directly; feeds into Biofuel Substitution Cascade

### Palm Substitution Composite Signal
**Formula**:
```sql
CASE
    WHEN soy_palm_price_ratio > 2.2 THEN 0.25  -- Extreme substitution to palm
    WHEN soy_palm_price_ratio < 1.3 THEN 0.80  -- Soy advantage
    WHEN palm_oil_export_restriction_severity > 0.8 THEN 0.85
    ELSE 0.50
END
```

**Input Data**:
- Soy/palm price ratio
- Palm oil export restriction severity (0-1 scale)

**Scoring Logic**:
- 0.25: Extreme substitution to palm (bearish for soy)
- 0.5: Normal substitution dynamics (neutral)
- 0.8: Price advantage for soy (bullish)
- 0.85: Palm export restrictions (strongly bullish for soy)

**Crisis Threshold**: None directly

### Energy Correlation Composite Signal
**Formula**:
```sql
CASE
    WHEN crude_oil_trend_classification = 'BULLISH' AND biofuel_economics_index > 0.7 THEN 0.80
    WHEN renewable_diesel_margin_spread > 100 THEN 0.75
    ELSE 0.50
END
```

**Input Data**:
- Crude oil trend classification (categorical)
- Biofuel economics index (0-1 scale)
- Renewable diesel margin spread ($/MT)

**Scoring Logic**:
- 0.5: Normal energy correlations (neutral)
- 0.75: Strong renewable diesel margins (bullish)
- 0.8: Bullish crude + strong biofuel economics (strongly bullish)

**Crisis Threshold**: None directly

### Logistics Disruption Composite Signal
**Formula**:
```sql
CASE
    WHEN panama_canal_transit_delays_days > 10 THEN 0.75
    WHEN argentina_port_strikes_risk > 0.7 THEN 0.70
    WHEN us_mississippi_draft_restrictions THEN 0.65
    ELSE 0.50
END
```

**Input Data**:
- Panama Canal transit delays (days)
- Argentina port strikes risk (0-1 scale)
- US Mississippi draft restrictions (boolean)

**Scoring Logic**:
- 0.5: Normal logistics flows (neutral)
- 0.65: Mississippi restrictions (moderately bullish)
- 0.7: Argentina port strike risk (bullish)
- 0.75: Panama Canal delays (strongly bullish)

**Crisis Threshold**: None directly

### Technical Momentum Composite Signal
**Formula**:
```sql
CASE
    WHEN zl_rsi_14 > 70 AND zl_momentum_20d > 0.05 THEN 0.80
    WHEN zl_rsi_14 < 30 AND zl_momentum_20d < -0.05 THEN 0.20
    WHEN zl_bollinger_position > 0.8 THEN 0.75
    ELSE 0.50
END
```

**Input Data**:
- ZL 14-day RSI
- ZL 20-day momentum (percentage change)
- ZL Bollinger Band position (0-1 scale, 1 = upper band)

**Scoring Logic**:
- 0.2: Oversold conditions (bearish momentum)
- 0.5: Neutral technical setup
- 0.75: Near upper Bollinger Band (bullish)
- 0.8: Overbought with strong momentum (strongly bullish)

**Crisis Threshold**: None directly

### Market Structure Composite Signal
**Formula**:
```sql
CASE
    WHEN cftc_managed_money_percentile_rank > 80 THEN 0.25  -- Crowded long
    WHEN cftc_commercial_net_position < -50000 THEN 0.80    -- Commercial buying
    WHEN open_interest_growth_rate > 0.15 THEN 0.70
    ELSE 0.50
END
```

**Input Data**:
- CFTC managed money percentile rank (0-100)
- CFTC commercial net position (contracts)
- Open interest growth rate (percentage)

**Scoring Logic**:
- 0.25: Crowded speculative long position (bearish contrarian indicator)
- 0.5: Neutral market structure
- 0.7: Strong open interest growth (bullish)
- 0.8: Significant commercial buying (strongly bullish)

**Crisis Threshold**: None directly

## Crisis Intensity Score Calculation

The Crisis Intensity Score (0-100) is calculated based on the Big 7 signals:

```sql
LEAST(
    (CASE WHEN vix_current > 30 THEN 17 ELSE 0 END +
     CASE WHEN sa_harvest_composite < 0.8 THEN 17 ELSE 0 END +
     CASE WHEN china_stress_composite > 0.8 THEN 17 ELSE 0 END +
     CASE WHEN tariff_threat_composite > 0.8 THEN 17 ELSE 0 END +
     CASE WHEN geopolitical_volatility_index > 0.8 THEN 12 ELSE 0 END +
     CASE WHEN biofuel_substitution_cascade > 0.8 THEN 12 ELSE 0 END +
     CASE WHEN ABS(hidden_correlation_index) > 0.8 THEN 8 ELSE 0 END), 
    100
)
```

**Scoring Tiers**:
- 0-25: Normal market conditions
- 25-50: Elevated stress (medium conviction)
- 50-75: Crisis conditions (high conviction)
- 75-100: Severe crisis (extreme conviction)

## Market Regime Classification

The Master Regime Classification is determined by evaluating the Big 7 signals in the following priority order:

### Crisis Regimes (single factor dominance)
- VIX > 30 → "VIX_CRISIS_REGIME"
- Harvest Pace < 0.8 → "SUPPLY_CRISIS_REGIME"
- China Relations > 0.8 → "CHINA_CRISIS_REGIME"
- Tariff Threat > 0.8 → "TARIFF_CRISIS_REGIME"
- GVI > 0.8 → "GEOPOLITICAL_CRISIS_REGIME"
- BSC > 0.8 → "BIOFUEL_IMPACT_REGIME"
- |HCI| > 0.8 → "CORRELATION_SHIFT_REGIME"

### Multi-Factor Stress Regimes
- VIX > 25 + China Relations > 0.6 → "GEOPOLITICAL_STRESS_REGIME"
- Harvest Pace < 0.9 + China Relations > 0.6 → "SUPPLY_GEOPOLITICAL_REGIME"
- VIX > 25 + Tariff Threat > 0.6 → "TRUMP_VOLATILITY_REGIME"
- BSC > 0.6 + HCI > 0.6 → "BIOFUEL_CORRELATION_REGIME"

### Normal Regimes
- VIX < 20 + Harvest Pace > 0.95 + China Relations < 0.4 + Tariff Threat < 0.3 → "FUNDAMENTALS_REGIME"

### Default
- All other conditions → "MIXED_SIGNALS_REGIME"

## Neural Network Weighting Strategy

For the neural network model, the Big 7 signals are weighted according to their market importance:

### Tier 1 (2.5x weight): The original Big 4 signals
- VIX Stress
- Harvest Pace
- China Relations
- Tariff Threat

### Tier 2 (1.5x weight): Secondary Big 7 signals
- Geopolitical Volatility Index
- Biofuel Substitution Cascade

### Tier 3 (1.0x weight): Specialized signal
- Hidden Correlation Index

## Override Flag Logic

Override flags are triggered when signals exceed their crisis thresholds:

```sql
-- PRIORITY SIGNAL FLAGS
feature_vix_stress > 1.5 as vix_override_flag,
feature_harvest_pace < 0.8 as harvest_override_flag,
feature_china_relations > 0.8 as china_override_flag,
feature_tariff_probability > 0.8 as tariff_override_flag,
feature_geopolitical_volatility > 0.8 as geopolitical_override_flag,
feature_biofuel_impact > 0.8 as biofuel_override_flag,
ABS(feature_hidden_correlation) > 0.8 as correlation_override_flag
```

These override flags are used to:
- Adjust neural network weights
- Determine the primary signal driver
- Calculate the crisis intensity score
- Display active overrides in the API response

## Performance Tracking Metrics

The system tracks forecast accuracy using Mean Absolute Percentage Error (MAPE):

```sql
ABS(nn_forecast_1week - actual_1week) / actual_1week * 100 as ape_1week
```

**MAPE Scoring Standards**:
- < 2%: Excellent accuracy (fundamentals regime)
- < 3%: Good accuracy (overall)
- < 5%: Acceptable accuracy (crisis regimes)
- > 5%: Poor accuracy (requires model retraining)

## Signal Update Schedule

| Signal Category | Update Frequency | Data Source Refresh |
|-----------------|------------------|---------------------|
| VIX Stress | Real-time | Market data API |
| Harvest Pace | Weekly | CONAB/USDA reports |
| China Relations | Weekly | Trade data + daily sentiment |
| Tariff Threat | Daily | Social media monitoring |
| Geopolitical Volatility | Daily | News API + market data |
| Biofuel Substitution | Weekly | Policy trackers + pricing data |
| Hidden Correlation | Daily | Market close correlation analysis |

## News Sentiment Integration

The platform integrates 16 news categories into the signal scoring system:

### China Demand Levers
- **Bullish triggers**: Reserve stockpiles rebuild, import quota increases
- **Bearish triggers**: Biosecurity import restrictions, state reserve releases

### Argentina Policy + FX
- **Bullish triggers**: Export taxes increase, port blockades, trucker strikes
- **Bearish triggers**: Temporary export tax cuts, FX incentives to sell

### Brazil Policy + Infrastructure
- **Bullish triggers**: Export licensing delays, environmental enforcement slowing expansion
- **Bearish triggers**: Logistics upgrades, port privatizations, BRL strengthening

### U.S. Policy
- **Bullish triggers**: Higher China tariff/retaliation risk, rail/port strikes
- **Bearish triggers**: Export credit guarantees, inspection streamlining

### Biofuels Policy
- **Bullish triggers**: Indonesia B40 implementation, Brazil biodiesel blend increases
- **Bearish triggers**: Feedstock ILUC pushback, weaker LCFS credit prices

### Palm Oil Geopolitics
- **Bullish triggers (for soy)**: Export levies/bans in Indonesia/Malaysia
- **Bearish triggers (for soy)**: Export liberalization, India import duty cuts on palm

### Black Sea Vegoils & War Spillovers
- **Bullish triggers**: Corridor disruptions, port strikes
- **Bearish triggers**: Corridor re-openings, sunflower oil exports resume

### Global Chokepoints & Freight
- **Bullish triggers**: Red Sea/Suez risk, Panama Canal restrictions
- **Bearish triggers**: Rerouting subsidies, canal rainfall recovery

### Fertilizer & Energy Sanctions
- **Bullish triggers**: Sanctions on ammonia/potash, natural gas price spikes
- **Bearish triggers**: Sanction carve-outs, new supply sources

### Animal Disease Shocks
- **Bullish/Bearish**: Depends on whether culling triggers policy stockpiles
- Generally bearish for meal in short term

### Trade Disputes & Quotas
- **Bullish triggers**: Antidumping/CVD actions, new quotas or SPS barriers
- **Bearish triggers**: Fresh bilateral deals, purchase commitments

### ESG/Deforestation Rules
- **Bullish triggers**: Strict traceability deadlines causing shipment delays
- **Bearish triggers**: Phased enforcement or exemptions

### Labor & Civil Unrest
- **Bullish triggers**: Port strikes, trucker protests, farmer blockades
- **Bearish triggers**: Strike settlements with throughput guarantees

### Cyber/Infrastructure Surprises
- **Bullish triggers**: Ransomware at ports/traders, AIS spoofing, customs outages
- **Bearish triggers**: Quick recovery from outages

### Regulatory Approvals
- **Bullish triggers**: Bans on agrochemicals, delayed trait approvals
- **Bearish triggers**: Rapid approvals, alternative herbicide programs

### Macro/FX Flow-through
- **Varies**: USD↑ often pressures commodities; BRL/ARS↓ boosts exports
- Scored based on historical correlation patterns

## Using the Signal Scoring Manual

### For Traders and Analysts:
- Monitor the Big 7 signals for early warning of regime shifts
- Check crisis intensity score for forecast conviction level
- Review active overrides to understand primary market drivers
- Analyze composite signals for deeper insight into specific factors

### For Data Scientists and Engineers:
- Use these scoring formulas to calibrate new signals
- Maintain consistent 0-1 scaling for all new signals
- Follow the established crisis threshold patterns (typically 0.8)
- Integrate new signals into the neural network with appropriate tier weighting

### For Product Managers:
- Ensure all 16 news categories are monitored for sentiment scoring
- Prioritize data source reliability for the Big 7 primary signals
- Schedule regular validation of signal performance vs. market moves
- Consider adding visualization of signal trends over time

---

This manual provides a standardized framework for evaluating all signals in the soybean oil futures forecasting platform. It ensures consistent interpretation and helps users understand the key drivers behind the market forecasts.
