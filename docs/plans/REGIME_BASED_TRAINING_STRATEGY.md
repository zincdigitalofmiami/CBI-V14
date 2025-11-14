# Regime-Based Training Strategy for Vertex AI

**Date:** November 7, 2025  
**Status:** STRATEGIC DESIGN  
**Purpose:** Leverage ALL 125 years of data with intelligent regime weighting

---

## KEY INSIGHT FROM VERTEX AI DOCUMENTATION

**From [Vertex AI Forecasting Documentation](https://docs.cloud.google.com/vertex-ai/docs/tabular-data/forecasting/prepare-data):**

> "Add a weight column to your dataset to give rows a relative weight. The weight column must be a numeric column. The weight value can be 0‑10,000. Higher values indicate that the row is more important when training the model."

**This changes EVERYTHING. We don't throw away historical data - we WEIGHT it!**

---

## COMMODITY MARKET REGIMES (Based on Structural Breaks)

### Regime 1: Pre-Financial Crisis (2000-2007)
**Characteristics:**
- Low volatility
- Steady China demand growth
- Stable USD
- Pre-biofuel mandate era

**Weight:** 100 (baseline - learn patterns but don't over-emphasize)

---

### Regime 2: Financial Crisis (2008-2009)
**Characteristics:**
- Extreme volatility (VIX >80)
- Correlation breakdown
- Dollar strength
- Demand destruction

**Weight:** 500 (high volatility regime - important to learn crisis behavior)

**Key Events:**
- Lehman collapse (Sep 2008)
- Commodity crash
- Fed QE1 begins

---

### Regime 3: QE Era / China Supercycle (2010-2014)
**Characteristics:**
- Zero interest rates
- China infrastructure boom
- Commodity supercycle peak
- Strong biofuel demand

**Weight:** 300 (learn commodity boom dynamics)

**Key Events:**
- QE2, QE3
- China 4 trillion stimulus
- Agricultural commodity peaks

---

### Regime 4: Commodity Crash / Dollar Surge (2014-2016)
**Characteristics:**
- Oil crash from $100 to $30
- Dollar strength (DXY rally)
- China demand slowdown
- Agricultural commodity bear market

**Weight:** 400 (learn crash dynamics)

**Key Events:**
- Oil crash (2014-2016)
- Fed rate hike cycle begins (2015)
- Strong dollar

---

### Regime 5: Trade War Era (2017-2019)
**Characteristics:**
- Trump tariffs on China
- Soybean export collapse
- Agricultural retaliatory tariffs
- High policy uncertainty

**Weight:** 1,500 (CRITICAL - most relevant to Trump 2.0)

**Key Events:**
- Section 301 tariffs (2018)
- China soybean tariffs (25%)
- Argentina export tax changes
- Trade negotiations

---

### Regime 6: COVID Crisis (2020-2021)
**Characteristics:**
- Supply chain disruption
- Demand shock then recovery
- Unprecedented fiscal/monetary stimulus
- Commodity rally begins

**Weight:** 800 (supply chain disruption patterns relevant)

**Key Events:**
- COVID lockdowns
- Biofuel demand collapse then recovery
- Supply chain chaos
- Crush margin volatility

---

### Regime 7: Inflation / Rate Hike Era (2021-2023)
**Characteristics:**
- 40-year high inflation
- Fed aggressive rate hikes
- Ukraine war commodity shock
- Energy crisis

**Weight:** 1,200 (inflation dynamics important)

**Key Events:**
- CPI >9%
- Fed funds 0% → 5.5%
- Russia-Ukraine war
- Energy prices surge

---

### Regime 8: Trump 2.0 Era (2023-2025) **CURRENT**
**Characteristics:**
- Policy volatility
- Tariff threats/implementation
- China relations uncertainty
- Agricultural trade sensitivity
- Biofuel policy changes

**Weight:** 5,000 (MAXIMUM EMPHASIS - current regime)

**Key Events:**
- Trump re-election
- New tariff threats
- China trade uncertainty
- ICE enforcement on agricultural labor
- RFS mandate changes

---

### Regime 9: Structural Events (Crisis Periods)
**Characteristics:**
- Major supply disruptions
- Weather catastrophes
- Geopolitical shocks

**Weight:** 2,000 (learn extreme event response)

**Examples:**
- Argentina drought events
- Brazil frost events
- Major El Niño/La Niña cycles

---

## REGIME WEIGHTING IMPLEMENTATION

### SQL Implementation

```sql
CREATE OR REPLACE TABLE `cbi-v14.models_v4.master_weighted_training_data` AS
SELECT 
  date,
  -- All features
  *,
  -- Regime weight column
  CASE 
    -- Trump 2.0 Era (2023-2025) - MAXIMUM WEIGHT
    WHEN date >= '2023-01-01' THEN 5000
    
    -- Trade War Era (2017-2019) - HIGH WEIGHT (most similar to current)
    WHEN date >= '2017-01-01' AND date < '2020-01-01' THEN 1500
    
    -- Inflation Era (2021-2023) - VERY HIGH WEIGHT
    WHEN date >= '2021-01-01' AND date < '2023-01-01' THEN 1200
    
    -- COVID Crisis (2020-2021) - HIGH WEIGHT
    WHEN date >= '2020-01-01' AND date < '2021-01-01' THEN 800
    
    -- Financial Crisis (2008-2009) - MODERATE-HIGH WEIGHT
    WHEN date >= '2008-01-01' AND date < '2010-01-01' THEN 500
    
    -- Commodity Crash (2014-2016) - MODERATE WEIGHT
    WHEN date >= '2014-01-01' AND date < '2017-01-01' THEN 400
    
    -- QE/China Supercycle (2010-2014) - MODERATE WEIGHT
    WHEN date >= '2010-01-01' AND date < '2014-01-01' THEN 300
    
    -- Pre-Crisis (2000-2007) - BASELINE
    WHEN date >= '2000-01-01' AND date < '2008-01-01' THEN 100
    
    -- Historical (pre-2000) - LOW WEIGHT (for pattern learning only)
    ELSE 50
    
  END AS training_weight,
  
  -- Regime label (for analysis)
  CASE 
    WHEN date >= '2023-01-01' THEN 'Trump_2.0'
    WHEN date >= '2021-01-01' THEN 'Inflation_Era'
    WHEN date >= '2020-01-01' THEN 'COVID_Crisis'
    WHEN date >= '2017-01-01' THEN 'Trade_War'
    WHEN date >= '2014-01-01' THEN 'Commodity_Crash'
    WHEN date >= '2010-01-01' THEN 'QE_Supercycle'
    WHEN date >= '2008-01-01' THEN 'Financial_Crisis'
    WHEN date >= '2000-01-01' THEN 'Pre_Crisis'
    ELSE 'Historical'
  END AS market_regime

FROM `cbi-v14.models_v4.core_features_consolidated`
```

---

## ADVANTAGES OF THIS APPROACH

### 1. Uses ALL Historical Data (125 Years)
- Don't throw away valuable patterns
- Learn from multiple crisis types
- Understand long-term relationships
- Build robust feature engineering

### 2. Emphasizes Recent/Relevant Regimes
- Trump 2.0 data gets 50-100x weight vs historical
- Trade War era (2017-2019) heavily weighted (most similar to current)
- Recent crises weighted higher than old data

### 3. Crisis Learning
- Financial Crisis (2008-2009): Learn volatility spikes
- COVID Crisis: Learn supply chain disruptions
- Trade War: Learn tariff impacts (CRITICAL for Trump 2.0)

### 4. Vertex AI Native
- Uses built-in `weight` column feature
- No custom code needed
- AutoML automatically handles weights
- Interpretable and transparent

---

## REGIME-SPECIFIC FEATURE IMPORTANCE

### Trump 2.0 Era Features (Weight: 5,000)
- Trump policy intelligence (tweets, announcements)
- China import cancellations
- Tariff rates
- ICE enforcement activity
- RFS mandate changes
- Political event calendars

### Trade War Era Features (Weight: 1,500)
- Section 301 tariff data
- China retaliation
- Argentina opportunistic exports
- Farmer bailout programs
- Export credit programs

### Inflation Era Features (Weight: 1,200)
- Fed funds rate changes
- CPI/PPI data
- Energy price correlation
- Supply chain indicators
- Input cost inflation

### COVID Era Features (Weight: 800)
- Biofuel demand collapse/recovery
- Restaurant demand proxy
- Supply chain disruption indicators
- Crush margin volatility
- Government support programs

---

## IMPLEMENTATION PHASES

### Phase 1: Create Weighted Master Table
```sql
-- Single table with 16,824 rows (1900-2025)
-- Each row has a training_weight column
-- Vertex AI uses this for training emphasis
```

### Phase 2: Regime-Specific Features
```sql
-- Add regime indicators
-- Add regime-specific interaction terms
-- Example: trump_sentiment × tariff_rate (only relevant in Trump eras)
```

### Phase 3: Create Horizon-Specific Training Tables
```sql
-- 4 tables (1M, 3M, 6M, 12M)
-- Each includes ALL historical data with weights
-- Not just Trump era - but Trump era heavily weighted
```

### Phase 4: Vertex AI Training
```python
training_job = aiplatform.AutoMLTabularTrainingJob(
    display_name="CBI V14 Vertex – AutoML 1M",
    optimization_objective="minimize-rmse",
)

model = training_job.run(
    dataset=dataset,
    target_column="target_1m",
    weight_column="training_weight",  # <-- THIS IS THE KEY!
    budget_milli_node_hours=20000,
)
```

---

## WHY THIS IS BETTER THAN "TRUMP ERA ONLY"

### Trump Era Only (700 rows):
- ❌ Small dataset
- ❌ No crisis learning
- ❌ Overfitting risk
- ❌ Limited pattern diversity

### Weighted Historical (16,824 rows):
- ✅ Large dataset (16,824 rows)
- ✅ Learn from multiple crises
- ✅ Robust patterns
- ✅ Trump era STILL dominates (weight 5,000 vs 50-500)

### Effective Training Distribution:
```
Trump 2.0 rows:     ~700 × 5,000 weight = 3,500,000 effective rows
Trade War rows:     ~700 × 1,500 weight = 1,050,000 effective rows
Inflation rows:     ~500 × 1,200 weight =   600,000 effective rows
COVID rows:         ~500 ×   800 weight =   400,000 effective rows
Other regimes:   ~14,424 ×   100 weight = 1,442,400 effective rows
                                        ---------------
                                Total:  7,000,000+ weighted rows
```

**Result:** Trump 2.0 represents ~50% of effective training despite being <5% of rows!

---

## REGIME-AWARE FEATURE ENGINEERING

### Create Regime-Specific Features
```sql
-- Trump era tariff impact
CASE WHEN market_regime IN ('Trump_2.0', 'Trade_War') 
     THEN china_imports * tariff_rate 
     ELSE NULL END as trump_tariff_impact,

-- Crisis volatility amplification
CASE WHEN market_regime IN ('Financial_Crisis', 'COVID_Crisis', 'Commodity_Crash')
     THEN vix_close * crush_margin_volatility
     ELSE NULL END as crisis_volatility_amplifier,

-- Policy uncertainty interaction
CASE WHEN market_regime = 'Trump_2.0'
     THEN trump_sentiment_score * policy_uncertainty_index
     ELSE NULL END as trump_policy_uncertainty
```

---

## VALIDATION STRATEGY

### 1. Regime-Stratified Validation
- Validate on recent Trump 2.0 data (2024-2025)
- Validate on Trade War data (2018-2019) as proxy
- Compare performance across regimes

### 2. Out-of-Sample Testing
- Hold out last 3 months of Trump 2.0 era
- Test on completely unseen Trump 2.0 data
- Verify model generalizes within regime

### 3. Cross-Regime Performance
- Test how well model handles regime transitions
- Measure performance degradation on old regimes
- Acceptable to perform worse on pre-2010 data

---

## SUCCESS METRICS

### Primary: Trump 2.0 Era Performance
- MAPE on 2024-2025 data: Target 2-4%
- Directional accuracy: Target 65-70%
- Confidence interval coverage: 80-90%

### Secondary: Trade War Era Performance
- MAPE on 2018-2019 data: Target 3-5%
- Validates model works on similar regimes

### Tertiary: Overall Performance
- MAPE across all data: Less important
- OK if worse on pre-2010 data
- Focus is Trump 2.0 prediction accuracy

---

## FINAL ARCHITECTURE

```
16,824 historical rows (1900-2025)
    ↓
Regime weights assigned (50 - 5,000)
    ↓
1,000 selected features
    ↓
4 horizon-specific targets
    ↓
Vertex AI AutoML with weight column
    ↓
Models optimized for Trump 2.0 regime
```

---

## COMPARISON TO ORIGINAL PLAN

| Aspect | Original Plan | Regime-Weighted Plan |
|--------|--------------|---------------------|
| Training Rows | 700 (Trump era only) | 16,824 (all history) |
| Effective Emphasis | 100% Trump | 50% Trump, 50% similar regimes |
| Crisis Learning | None | Financial Crisis, COVID, etc. |
| Overfitting Risk | HIGH (700 rows) | LOW (16,824 rows) |
| Implementation | Filter to 2023+ | Weight column |
| Vertex AI Native | Yes | Yes (weight column) |
| Pattern Diversity | LOW | HIGH |
| Robustness | Risky | Robust |

---

**This is how institutional commodity quants actually train regime-aware models.**

**Reference:** [Vertex AI Forecasting Prepare Data](https://docs.cloud.google.com/vertex-ai/docs/tabular-data/forecasting/prepare-data)

