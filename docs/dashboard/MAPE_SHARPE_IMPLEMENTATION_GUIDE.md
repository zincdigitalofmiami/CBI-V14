# MAPE & Sharpe Ratio Implementation Guide for CBI-V14 Dashboard

## Overview
This document contains comprehensive implementation instructions for MAPE (Mean Absolute Percentage Error) and Sharpe Ratio calculations specifically designed for the soybean oil futures forecasting platform. **Review existing URLs before implementing! Update all URLs with existing endpoints and schema!**

## 1. MAPE Calculation & Implementation Guide

### MAPE Definition & Formula
Mean Absolute Percentage Error (MAPE) is the industry-standard metric for measuring forecast accuracy in commodity price prediction. It represents the average percentage difference between forecasted prices and actual prices.

**Basic Formula:**
```
MAPE = (100/n) * Σ|Actual - Forecast|/|Actual|
```

Where:
- n = number of forecast periods
- Actual = the actual observed price
- Forecast = the predicted price

For the soybean oil futures forecasting platform, we track MAPE across multiple time horizons:

```sql
-- For 1-week forecasts
ABS(nn_forecast_1week - actual_1week_price) / actual_1week_price * 100 as mape_1week

-- For 1-month forecasts
ABS(nn_forecast_1month - actual_1month_price) / actual_1month_price * 100 as mape_1month

-- For 3-month forecasts
ABS(nn_forecast_3month - actual_3month_price) / actual_3month_price * 100 as mape_3month
```

### Implementation in BigQuery
Here's the complete SQL implementation to calculate and track MAPE in the platform:

```sql
-- Create or replace the performance tracking view
CREATE OR REPLACE VIEW `cbi-v14.performance.vw_forecast_performance_tracking` AS

WITH forecast_history AS (
  -- Collect all historical forecasts
  SELECT
    signal_date,
    master_regime_classification,
    crisis_intensity_score,
    zl_price_current,
    nn_forecast_1week,
    nn_forecast_1month,
    nn_forecast_3month
  FROM `cbi-v14.api.vw_ultimate_adaptive_signal_historical`
  WHERE signal_date <= CURRENT_DATE()
),

actual_prices AS (
  -- Get actual prices for comparing against forecasts
  SELECT
    price_date,
    close as actual_price
  FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
  WHERE symbol = 'ZL'
  AND price_date <= CURRENT_DATE()
),

forecast_vs_actual AS (
  -- Match forecasts with their corresponding actual prices
  SELECT
    f.signal_date as forecast_date,
    f.master_regime_classification,
    f.crisis_intensity_score,
    f.zl_price_current as price_at_forecast,
    
    -- 1-week forecasts vs actuals
    f.nn_forecast_1week,
    a1w.actual_price as actual_1week_price,
    CASE 
      WHEN a1w.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_1week - a1w.actual_price) / a1w.actual_price * 100 
      ELSE NULL 
    END as mape_1week,
    
    -- 1-month forecasts vs actuals
    f.nn_forecast_1month,
    a1m.actual_price as actual_1month_price,
    CASE 
      WHEN a1m.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_1month - a1m.actual_price) / a1m.actual_price * 100 
      ELSE NULL 
    END as mape_1month,
    
    -- 3-month forecasts vs actuals
    f.nn_forecast_3month,
    a3m.actual_price as actual_3month_price,
    CASE 
      WHEN a3m.actual_price IS NOT NULL 
      THEN ABS(f.nn_forecast_3month - a3m.actual_price) / a3m.actual_price * 100 
      ELSE NULL 
    END as mape_3month
    
  FROM forecast_history f
  -- Join with actual prices for 1-week horizon
  LEFT JOIN actual_prices a1w 
    ON DATE_ADD(f.signal_date, INTERVAL 7 DAY) = a1w.price_date
  -- Join with actual prices for 1-month horizon
  LEFT JOIN actual_prices a1m
    ON DATE_ADD(f.signal_date, INTERVAL 30 DAY) = a1m.price_date
  -- Join with actual prices for 3-month horizon
  LEFT JOIN actual_prices a3m
    ON DATE_ADD(f.signal_date, INTERVAL 90 DAY) = a3m.price_date
)

-- Calculate aggregated MAPE metrics
SELECT
  -- Overall MAPE statistics
  AVG(mape_1week) as overall_mape_1week,
  AVG(mape_1month) as overall_mape_1month,
  AVG(mape_3month) as overall_mape_3month,
  
  -- MAPE by regime type
  AVG(CASE WHEN master_regime_classification LIKE '%CRISIS%' THEN mape_1week END) as crisis_mape_1week,
  AVG(CASE WHEN master_regime_classification = 'FUNDAMENTALS_REGIME' THEN mape_1week END) as normal_mape_1week,
  
  -- MAPE by confidence/crisis intensity level
  AVG(CASE WHEN crisis_intensity_score > 75 THEN mape_1week END) as high_confidence_mape_1week,
  AVG(CASE WHEN crisis_intensity_score BETWEEN 50 AND 75 THEN mape_1week END) as medium_confidence_mape_1week,
  AVG(CASE WHEN crisis_intensity_score < 50 THEN mape_1week END) as low_confidence_mape_1week,
  
  -- Most recent MAPE statistics (last 30 days)
  AVG(CASE WHEN forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week END) as recent_mape_1week,
  
  -- Record counts for statistical validity
  COUNT(mape_1week) as total_1week_records,
  COUNT(mape_1month) as total_1month_records,
  COUNT(mape_3month) as total_3month_records,
  
  -- MAPE trend (current vs historical)
  AVG(CASE WHEN forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week END) / 
  AVG(CASE WHEN forecast_date < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN mape_1week END) as mape_trend_ratio

FROM forecast_vs_actual
WHERE mape_1week IS NOT NULL  -- Ensure we only include complete records
;
```

## 2. Soybean-Specific Sharpe Ratio Implementation Guide

### Soybean-Adjusted Sharpe Ratio Definition & Formula
The Sharpe ratio requires customization for agricultural commodity futures like soybean oil due to their unique volatility and seasonality patterns:

```
Soybean-Adjusted Sharpe Ratio = (Rp - Rf) / (σp * Seasonal_Factor)
```

Where:
- Rp = Return of the soybean trading strategy
- Rf = Risk-free rate of return
- σp = Standard deviation of strategy returns (volatility)
- Seasonal_Factor = Adjustment for natural seasonal volatility in soybean markets

### Standard Sharpe (Annualized):
```
Annualized Sharpe = (Average Daily Return - Daily Risk-free Rate) / Standard Deviation of Daily Returns * √252
```
*Note: √252 is the annualization factor for daily returns (252 trading days per year)*

### Soybean Trading Signal Sharpe:
```
Soybean Signal Sharpe = (Average Signal Return - Daily Risk-free Rate) / (Standard Deviation of Signal Returns * Regime_Factor) * √Signal Count
Where Regime_Factor adjusts volatility expectations based on market regime (0.85 for crisis periods, 1.0 for normal periods)
```

## 3. Dashboard Integration Components

### 3.1 Main Dashboard Header
Add a "Forecast Accuracy" section to the main dashboard header:

```html
<div class="forecast-accuracy-module">
    <div class="accuracy-headline">
        <h3>Forecast Accuracy</h3>
        <span class="accuracy-tag" 
              data-quality="${forecast_reliability_score >= 90 ? 'excellent' : 
                             forecast_reliability_score >= 85 ? 'good' : 
                             forecast_reliability_score >= 80 ? 'fair' : 'poor'}">
            ${forecast_reliability_score}% Reliable
        </span>
    </div>
    
    <div class="mape-stats">
        <div class="mape-stat">
            <span class="stat-label">1-Week MAPE</span>
            <span class="stat-value">${overall_mape_1week}%</span>
        </div>
        <div class="mape-stat">
            <span class="stat-label">Current Regime MAPE</span>
            <span class="stat-value">${relevant_regime_mape}%</span>
        </div>
        <div class="mape-trend">
            <span class="trend-label">Trend</span>
            <span class="trend-indicator ${forecast_quality_trend.toLowerCase()}">
                ${forecast_quality_trend}
                <i class="trend-icon ${forecast_quality_trend === 'IMPROVING' ? 'fa-arrow-up' : 
                                     forecast_quality_trend === 'DEGRADING' ? 'fa-arrow-down' : 'fa-minus'}"></i>
            </span>
        </div>
    </div>
</div>
```

### 3.2 Soybean Strategy Performance Module
```html
<div class="soybean-strategy-performance-module">
    <div class="performance-headline">
        <h3>Soybean Strategy Performance</h3>
        <span class="sharpe-tag" 
              data-quality="${soybean_adjusted_sharpe >= 2.5 ? 'exceptional' : 
                             soybean_adjusted_sharpe >= 1.8 ? 'excellent' : 
                             soybean_adjusted_sharpe >= 1.2 ? 'good' : 
                             soybean_adjusted_sharpe >= 0.8 ? 'fair' : 'poor'}">
            Soybean Sharpe: ${soybean_adjusted_sharpe}
        </span>
        <span class="seasonal-badge ${seasonal_advantage_active ? 'active' : 'inactive'}">
            ${seasonal_advantage_active ? 'SEASONAL ADVANTAGE ACTIVE' : 'NEUTRAL SEASON'}
        </span>
    </div>
    
    <div class="performance-stats">
        <div class="stat">
            <span class="stat-label">Return</span>
            <span class="stat-value ${soybean_strategy_return_pct >= 0 ? 'positive' : 'negative'}">
                ${soybean_strategy_return_pct}%
            </span>
        </div>
        <div class="stat">
            <span class="stat-label">Win Rate</span>
            <span class="stat-value ${win_rate_pct >= 65 ? 'excellent' : 
                                     win_rate_pct >= 55 ? 'good' : 
                                     win_rate_pct >= 50 ? 'fair' : 'poor'}">
                ${win_rate_pct}%
            </span>
        </div>
        <div class="stat">
            <span class="stat-label">Profit Factor</span>
            <span class="stat-value ${soybean_profit_factor >= 2.5 ? 'excellent' : 
                                     soybean_profit_factor >= 1.8 ? 'good' : 
                                     soybean_profit_factor >= 1.3 ? 'fair' : 'poor'}">
                ${soybean_profit_factor}
            </span>
        </div>
        <div class="stat">
            <span class="stat-label">Weather Sharpe</span>
            <span class="stat-value ${weather_driven_sharpe >= 2.0 ? 'excellent' : 
                                     weather_driven_sharpe >= 1.3 ? 'good' : 
                                     weather_driven_sharpe >= 0.8 ? 'fair' : 'poor'}">
                ${weather_driven_sharpe}
            </span>
        </div>
    </div>
</div>
```

## 4. MAPE Interpretation Guide

### MAPE Values in the Platform
| MAPE Range | Classification | Interpretation |
|------------|----------------|----------------|
| 0-2% | Excellent | Institutional-grade accuracy, highest conviction |
| 2-3% | Good | Strong accuracy, high conviction |
| 3-5% | Fair | Acceptable accuracy, medium conviction |
| 5-8% | Poor | Below-target accuracy, low conviction |
| >8% | Critical | Requires model retraining or recalibration |

### MAPE by Market Regime
| Regime Type | Target MAPE | Acceptable Range |
|-------------|-------------|------------------|
| Fundamentals Regime | <2% | 0-3% |
| Mixed Signals Regime | <3% | 0-4% |
| VIX Crisis Regime | <5% | 0-8% |
| Supply Crisis Regime | <5% | 0-8% |
| China/Tariff Crisis Regime | <5% | 0-8% |
| Geopolitical/Biofuel Regimes | <6% | 0-10% |

## 5. Soybean-Specific Sharpe Ratio Interpretation

### Soybean Sharpe Ratios
| Soybean Sharpe Range | Classification | Interpretation |
|---------------------|----------------|----------------|
| > 2.5 | Exceptional | Elite agricultural commodity performance |
| 1.8 - 2.5 | Excellent | Top-tier commodity trading desk performance |
| 1.2 - 1.8 | Good | Professional agricultural trader performance |
| 0.8 - 1.2 | Fair | Acceptable agricultural commodity performance |
| 0.5 - 0.8 | Modest | Break-even after costs in agricultural futures |
| < 0.5 | Poor | Underperforming agricultural trading strategy |

### Sharpe by Soybean Market Regime
| Regime Type | Target Sharpe | Acceptable Range | Context |
|-------------|---------------|------------------|---------|
| Normal Markets | > 0.8 | 0.6 - 1.2 | Low volatility, technical trading |
| Weather Premium | > 1.2 | 0.9 - 1.8 | Weather-driven volatility regimes |
| China Trade Policy | > 1.5 | 1.1 - 2.0 | Trade war and policy uncertainty |
| Biofuel Impact | > 1.4 | 1.0 - 2.2 | Demand-driven policy shifts |
| Seasonal Events | > 1.0 | 0.7 - 1.5 | USDA report-driven volatility |
| Crop Failure Crisis | > 2.0 | 1.5 - 2.5 | Major supply disruptions |

## 6. JavaScript Chart Implementations

### MAPE Trends Chart (D3.js)
```javascript
// D3.js time-series line chart
function renderMAPEChart(data) {
    const margin = {top: 20, right: 30, bottom: 30, left: 40},
          width = 800 - margin.left - margin.right,
          height = 400 - margin.top - margin.bottom;
    
    const svg = d3.select("#mape-trend-chart")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // X scale = dates
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.tracking_date))
        .range([0, width]);
    
    // Y scale = MAPE values
    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => Math.max(d.overall_mape_1week, d.crisis_mape_1week, d.normal_mape_1week)) * 1.1])
        .range([height, 0]);
    
    // Add axes
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));
    
    svg.append("g")
        .call(d3.axisLeft(y).tickFormat(d => d + "%"));
    
    // Add overall MAPE line
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#2C82C9")
        .attr("stroke-width", 2)
        .attr("d", d3.line()
            .x(d => x(d.tracking_date))
            .y(d => y(d.overall_mape_1week))
        );
    
    // Add crisis MAPE line
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#FC6042")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")
        .attr("d", d3.line()
            .x(d => x(d.tracking_date))
            .y(d => y(d.crisis_mape_1week))
        );
    
    // Add normal MAPE line
    svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#65C87A")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "3,3")
        .attr("d", d3.line()
            .x(d => x(d.tracking_date))
            .y(d => y(d.normal_mape_1week))
        );
}
```

### Soybean Seasonal Performance Chart
```javascript
// D3.js seasonal performance chart for soybeans
function renderSoybeanSeasonalPerformance(data) {
    const margin = {top: 30, right: 30, bottom: 50, left: 60},
          width = 600 - margin.left - margin.right,
          height = 350 - margin.top - margin.bottom;
    
    const svg = d3.select("#soybean-seasonal-chart")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Prepare seasonal data
    const seasonalData = [
        {season: "SPRING (Plant)", return: data.spring_avg_return * 100, sharpe: data.spring_sharpe},
        {season: "SUMMER (Grow)", return: data.summer_avg_return * 100, sharpe: data.summer_sharpe},
        {season: "FALL (Harvest)", return: data.fall_avg_return * 100, sharpe: data.fall_sharpe},
        {season: "WINTER (Dormant)", return: data.winter_avg_return * 100, sharpe: data.winter_sharpe}
    ];
    
    // X scale for seasons
    const x = d3.scaleBand()
        .domain(seasonalData.map(d => d.season))
        .range([0, width])
        .padding(0.2);
    
    // Y scale for returns
    const y = d3.scaleLinear()
        .domain([
            Math.min(0, d3.min(seasonalData, d => d.return) * 1.2),
            Math.max(0, d3.max(seasonalData, d => d.return) * 1.2)
        ])
        .range([height, 0]);
    
    // Add X axis
    svg.append("g")
        .attr("transform", `translate(0,${y(0)})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "translate(-10,0)rotate(-45)")
        .style("text-anchor", "end");
    
    // Add Y axis
    svg.append("g")
        .call(d3.axisLeft(y).tickFormat(d => `${d.toFixed(1)}%`));
    
    // Add bars with dynamic coloring
    svg.selectAll(".bar")
        .data(seasonalData)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.season))
        .attr("width", x.bandwidth())
        .attr("y", d => d.return > 0 ? y(d.return) : y(0))
        .attr("height", d => Math.abs(y(0) - y(d.return)))
        .attr("fill", d => d.return > 0 ? "#4CAF50" : "#F44336")
        .attr("opacity", 0.7);
}
```

## 7. Position Sizing Based on Sharpe
```javascript
// Position sizing based on Soybean-adjusted Sharpe ratio with seasonal considerations
function calculateSoybeanPositionSize(signal) {
    // Base position size as percentage of capital
    let baseSize = 0.1;  // 10% of capital
    
    // Adjust based on Soybean-adjusted Sharpe ratio
    if (signal.soybean_adjusted_sharpe >= 2.5) {
        baseSize = 0.18;  // 18% for exceptional Sharpe (lower than equities due to agricultural volatility)
    } else if (signal.soybean_adjusted_sharpe >= 1.8) {
        baseSize = 0.15;  // 15% for excellent Sharpe
    } else if (signal.soybean_adjusted_sharpe >= 1.2) {
        baseSize = 0.12;  // 12% for good Sharpe
    } else if (signal.soybean_adjusted_sharpe < 0.8) {
        baseSize = 0.05;  // 5% for poor Sharpe
    }
    
    // Further adjust by recommendation strength
    const recommendationMultiplier = {
        'STRONG_BUY': 1.0,
        'BUY': 0.75,
        'WEAK_BUY': 0.5,
        'HOLD': 0,
        'WEAK_SELL': 0.5,
        'SELL': 0.75,
        'STRONG_SELL': 1.0
    }[signal.trading_recommendation];
    
    // Apply regime/confidence adjustment
    const confidenceMultiplier = {
        'HIGH_CONVICTION': 1.0,
        'MEDIUM_CONVICTION': 0.8,
        'LOW_CONVICTION': 0.6
    }[signal.forecast_confidence];
    
    // Apply seasonal advantage multiplier (unique to agricultural commodities)
    const seasonalMultiplier = signal.seasonal_advantage_active ? 1.2 : 1.0;
    
    // Apply weather-driven premium for weather-based signals
    const weatherMultiplier = 
        signal.primary_signal_driver.includes('weather') || 
        signal.primary_signal_driver.includes('harvest') ? 1.15 : 1.0;
    
    // Calculate final position size with soybean-specific adjustments
    return baseSize * 
           recommendationMultiplier * 
           confidenceMultiplier * 
           seasonalMultiplier *
           weatherMultiplier;
}
```

## 8. Automated Monitoring Systems

### MAPE Monitoring System
```python
#!/usr/bin/env python3
"""
MAPE Monitoring System
Updates MAPE metrics daily and triggers alerts on accuracy degradation
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

class MAPEMonitor:
    def __init__(self, project_id="cbi-v14"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.alert_thresholds = {
            'overall_mape_1week': 5.0,  # Alert if overall MAPE exceeds 5%
            'crisis_mape_1week': 8.0,   # Alert if crisis MAPE exceeds 8%
            'normal_mape_1week': 3.0,   # Alert if normal MAPE exceeds 3%
            'mape_trend_ratio': 1.2     # Alert if MAPE is 20% worse than historical
        }
```

### Soybean Sharpe Monitoring System
```python
#!/usr/bin/env python3
"""
Soybean Sharpe Ratio Monitoring System
Tracks Sharpe ratio metrics with agricultural-specific thresholds
"""

class SoybeanSharpeMonitor:
    def __init__(self, project_id="cbi-v14"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        
        # Agricultural futures specific thresholds (lower than equities)
        self.alert_thresholds = {
            'seasonal_adjusted_sharpe_1week': 0.8,  # Alert if adjusted Sharpe drops below 0.8
            'crisis_sharpe_1week': 1.2,             # Alert if crisis Sharpe drops below 1.2
            'normal_sharpe_1week': 0.6,             # Alert if normal Sharpe drops below 0.6
            'weather_driven_sharpe_1week': 1.0,     # Alert if weather-driven Sharpe drops below 1.0
            'sharpe_trend_ratio': 0.7               # Alert if Sharpe is 30% worse than historical
        }
```

## 9. Implementation Notes

### Critical Requirements:
1. **Review existing URLs before implementing!** Update all URLs with existing endpoints and schema
2. **Use existing BigQuery table structures** - don't create new tables without permission
3. **Follow the established naming conventions** for views and tables
4. **Integrate with existing API endpoints** rather than creating new ones
5. **Use the existing dashboard framework** and component structure

### Next Steps:
1. Audit existing BigQuery views and tables for MAPE/Sharpe data
2. Update existing API endpoints to include performance metrics
3. Integrate performance components into existing dashboard layout
4. Test with real data from the current system
5. Implement monitoring and alerting systems

---

**This guide provides comprehensive implementation instructions for MAPE and Sharpe ratio calculations specifically designed for the soybean oil futures forecasting platform. All components are tailored for agricultural commodity trading with appropriate thresholds and seasonal considerations.**
