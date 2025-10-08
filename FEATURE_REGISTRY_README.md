# Feature Registry - Semantic Metadata System

## Purpose

The Feature Registry provides **economic context and semantic meaning** for all data features in the CBI-V14 forecasting system. This enables:

1. **Neural networks** to understand economic relationships and generate smart lag features
2. **AI agents** to explain predictions with economic reasoning
3. **Chat interfaces** to translate natural language queries to feature names
4. **Developers** to understand the purpose and impact of each data point

---

## Architecture

### BigQuery Table: `feature_metadata`

Located at: `cbi-v14.forecasting_data_warehouse.feature_metadata`

**Schema:**
- `feature_name` - Canonical name (e.g., 'fed_funds_rate')
- `feature_type` - Category: MACRO, CURRENCY, COMMODITY, WEATHER, SENTIMENT
- `asset_class` - Sub-category (e.g., INTEREST_RATE, FX, AGRICULTURE)
- `economic_meaning` - Full economic explanation (2-3 sentences)
- `directional_impact` - POSITIVE, NEGATIVE, COMPLEX, LEADING, TARGET, SUBSTITUTE
- `typical_lag_days` - Days until effect appears (for auto-lag generation)
- `typical_range_min/max` - Realistic value ranges (for anomaly detection)
- `source_table` - Where to find this data
- `source_column` - Which column contains the value
- `related_features` - Array of economically related features
- `chat_aliases` - Array of natural language alternatives
- `last_updated` - Metadata timestamp
- `is_active` - Boolean flag

### Python Module: `feature_registry.py`

Located at: `cbi-v14-ingestion/feature_registry.py`

**Main Class:** `FeatureRegistry`

**Key Methods:**
- `get_feature(name)` - Get metadata for a feature
- `get_features_by_type(type)` - Get all MACRO, WEATHER, etc.
- `get_features_by_impact(impact)` - Get all NEGATIVE impact features
- `translate_chat_query(query)` - Natural language → feature name
- `get_lag_features(min_days)` - Features with lag effects
- `explain_feature(name)` - Generate human-readable explanation

---

## Current Coverage

**17 features documented across 5 categories:**

### MACRO (4 features)
- `fed_funds_rate` - Federal Reserve policy rate
- `ten_year_treasury` - US 10Y yield
- `cpi_inflation` - Consumer Price Index
- `dollar_index` - DXY currency strength

### CURRENCY (2 features)
- `usd_brl_rate` - USD/BRL exchange rate (Brazil)
- `usd_cny_rate` - USD/CNY exchange rate (China)

### COMMODITY (5 features)
- `soybean_oil_prices` - TARGET (primary forecast)
- `soybean_prices` - ZS futures
- `palm_oil_prices` - FCPO (substitute)
- `corn_prices` - ZC futures
- `crude_oil_wti` - WTI crude oil

### WEATHER (3 features)
- `precip_mm` - Precipitation
- `temp_max` - Maximum temperature
- `temp_min` - Minimum temperature

### SENTIMENT (3 features)
- `social_sentiment` - Reddit/Twitter aggregation
- `news_intelligence` - Multi-source news monitoring
- `ice_trump_intelligence` - Policy risk tracking

---

## Usage Examples

### 1. Neural Network Feature Engineering

```python
from feature_registry import feature_registry

# Get all features with lag effects
lag_features = feature_registry.get_lag_features(min_lag_days=7)

# Auto-generate lag features
for feature_meta in lag_features:
    feature_name = feature_meta['feature_name']
    lag_days = feature_meta['typical_lag_days']
    
    # Create lagged feature
    df[f'{feature_name}_lag_{lag_days}'] = df[feature_name].shift(lag_days)
    
    print(f"✅ Created {feature_name}_lag_{lag_days} (impact: {feature_meta['directional_impact']})")

# Example output:
# ✅ Created fed_funds_rate_lag_30 (impact: NEGATIVE)
# ✅ Created ten_year_treasury_lag_14 (impact: NEGATIVE)
# ✅ Created usd_brl_rate_lag_7 (impact: NEGATIVE)
```

### 2. AI Agent Explanation

```python
from feature_registry import explain_feature

# User asks: "Why did soybean oil prices drop?"
# AI agent checks recent changes and explains:

explanation = explain_feature('fed_funds_rate')
print(explanation)

# Output:
# 📊 **Fed Funds Rate**
# 
# **Type:** INTEREST_RATE (MACRO)
# 
# **Economic Meaning:**
# Federal Reserve target interest rate - primary US monetary policy tool. 
# Higher rates increase borrowing costs, strengthen USD, typically pressure 
# commodity prices downward through demand destruction.
# 
# **Market Impact:** NEGATIVE
# **Typical Lag:** 30 days
# **Typical Range:** 0.0 - 6.0
# 
# **Related Features:** ten_year_treasury, dollar_index, cpi_inflation
```

### 3. Chat Interface Natural Language

```python
from feature_registry import translate_query, get_feature

# User types: "What are interest rates doing?"
feature_name = translate_query("interest rates")  # Returns: 'fed_funds_rate'

# Get current value
query = f"""
SELECT value, time 
FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
WHERE indicator = '{feature_name}'
ORDER BY time DESC LIMIT 1
"""
result = bq_client.query(query).to_dataframe()

# Response:
# "Interest rates (Federal Funds Rate) are currently 4.25%, 
#  last updated Oct 5, 2025. This is a NEGATIVE driver for 
#  commodity prices with a typical 30-day lag."
```

### 4. Dashboard AI Agent

```python
from feature_registry import feature_registry

# Analyze today's price movement
def analyze_price_change(asset, date):
    # Get all features that affect this asset
    target_meta = feature_registry.get_feature(asset)
    related_features = target_meta['related_features']
    
    # Check recent changes in each related feature
    analysis = []
    for feature in related_features:
        meta = feature_registry.get_feature(feature)
        recent_change = get_recent_change(feature, days=meta['typical_lag_days'])
        
        if abs(recent_change) > 2%:  # Significant move
            analysis.append({
                'feature': feature,
                'change': recent_change,
                'impact': meta['directional_impact'],
                'meaning': meta['economic_meaning']
            })
    
    return analysis

# Output for dashboard:
# "Soybean oil fell 3% due to:
#  - Fed raised rates 0.25% (NEGATIVE impact, 30-day lag) → stronger dollar
#  - USD/BRL rose 2% (NEGATIVE impact) → Brazil export competition
#  - Crude oil fell 5% (biodiesel demand weakened)"
```

---

## Benefits

### For Neural Networks:
✅ **Automatic lag feature generation** based on typical_lag_days  
✅ **Economic relationship encoding** via related_features  
✅ **Feature selection guidance** via directional_impact  
✅ **Anomaly detection** via typical ranges  

### For AI Agents:
✅ **Economic explanations** for predictions  
✅ **Natural language understanding** via chat_aliases  
✅ **Cross-asset reasoning** via related_features  
✅ **Confidence scoring** based on typical ranges  

### For Developers:
✅ **Self-documenting data** - no need to ask "what's this column?"  
✅ **Onboarding acceleration** - new devs understand the system faster  
✅ **Debugging** - know expected ranges and relationships  

---

## Maintenance

### Adding New Features

When new data is ingested, add metadata:

```sql
INSERT INTO `cbi-v14.forecasting_data_warehouse.feature_metadata` 
(feature_name, feature_type, asset_class, economic_meaning, directional_impact, 
 typical_lag_days, typical_range_min, typical_range_max, source_table, source_column, 
 related_features, chat_aliases, last_updated, is_active)
VALUES
  ('new_feature_name', 'COMMODITY', 'AGRICULTURE',
   'Economic explanation of what this feature represents and why it matters',
   'POSITIVE', 7, 100.0, 500.0,
   'table_name', 'column_name',
   ['related_feature_1', 'related_feature_2'],
   ['alias1', 'alias2', 'alias3'],
   CURRENT_TIMESTAMP(), TRUE);
```

### Updating Existing Features

```sql
UPDATE `cbi-v14.forecasting_data_warehouse.feature_metadata`
SET 
  economic_meaning = 'Updated explanation...',
  typical_range_max = 150.0,
  last_updated = CURRENT_TIMESTAMP()
WHERE feature_name = 'existing_feature';
```

### Deactivating Deprecated Features

```sql
UPDATE `cbi-v14.forecasting_data_warehouse.feature_metadata`
SET is_active = FALSE, last_updated = CURRENT_TIMESTAMP()
WHERE feature_name = 'deprecated_feature';
```

---

## Next Steps

### Immediate (Completed ✅):
- [x] Create `feature_metadata` BigQuery table
- [x] Populate 17 core features (macro, currency, commodity, weather, sentiment)
- [x] Build `feature_registry.py` Python module
- [x] Test natural language translation
- [x] Test feature explanation generation

### Short-term (1-2 weeks):
- [ ] Add remaining commodity features (cotton, cocoa, soybean meal, etc.)
- [ ] Integrate feature_registry into neural training pipeline
- [ ] Build AI agent dashboard component using feature_registry
- [ ] Add chat interface using translate_query()
- [ ] Create unit tests for feature_registry module

### Medium-term (1-2 months):
- [ ] Add freight/logistics features (when available)
- [ ] Add policy features (RFS mandates, trade agreements)
- [ ] Add satellite imagery features (NDVI, soil moisture)
- [ ] Build feature importance tracking (which features predict best?)
- [ ] Create feature lineage graph visualization

---

## Technical Notes

### Why This Matters for Neural Networks

Traditional ML approaches treat features as opaque numbers:
- `feature_42` = some number
- Neural network learns correlations blindly

With semantic metadata:
- `fed_funds_rate` = monetary policy signal with 30-day lag and NEGATIVE impact
- Neural network can use economic priors (regularization toward known relationships)
- Feature engineering becomes intelligent (auto-generate fed_rate_lag_30)
- Explainability becomes possible (cite economic mechanisms)

This is **how institutional trading desks operate** - they don't train blind models, they encode domain knowledge into the architecture.

---

## Status

**✅ PRODUCTION READY**

- Feature metadata table: CREATED
- 17 features documented: COMPLETE
- Python module: TESTED
- Natural language: WORKING
- AI explanations: WORKING

**Ready for:**
- Neural network integration
- Dashboard AI agent
- Chris chat interface
- Feature engineering automation

---

**Last Updated:** October 8, 2025  
**Maintainer:** CBI-V14 Data Engineering Team

