# Deep Research Examples for CBI-V14

**Date:** January 2025  
**Purpose:** Real-world examples of using Deep Research for CBI-V14 tasks

---

## 🎯 EXAMPLE 1: Market Regime Analysis

**Research Question:** How do Fed policy changes affect ZL futures market regimes?

```bash
python3 scripts/research/research_market_regimes.py \
  --asset ZL \
  --date-range 2000-2025 \
  --focus "Fed policy" \
  --model o4-mini-deep-research \
  --output results/research/zl_fed_regimes_$(date +%Y%m%d).json
```

**Expected Output:**
- Identification of distinct market regimes
- Fed policy change dates and their impact
- Regime transition analysis
- Statistical correlation between Fed actions and regime changes
- Citations from FRED, Fed minutes, academic papers

---

## 🎯 EXAMPLE 2: Feature Engineering Best Practices

**Research Question:** What are the most effective technical indicators for ZL futures?

```bash
python3 scripts/research/research_feature_engineering.py \
  --asset ZL \
  --indicator-type momentum \
  --model o4-mini-deep-research \
  --output results/research/zl_momentum_indicators_$(date +%Y%m%d).json
```

**Expected Output:**
- Ranking of momentum indicators by effectiveness
- Optimal lookback periods for ZL
- Regime-aware indicator selection
- Academic validation studies
- Statistical evidence and citations

---

## 🎯 EXAMPLE 3: Trade War Impact Analysis

**Research Question:** How did the 2018-2020 trade war affect ZL futures prices?

```bash
python3 scripts/research/research_economic_impact.py \
  "trade wars" \
  --asset ZL \
  --date-range 2018-2020 \
  --model o4-mini-deep-research \
  --output results/research/trade_war_zl_impact.json
```

**Expected Output:**
- Specific trade war events and dates
- Price movement analysis
- Correlation and causation analysis
- Lag effects and transmission mechanisms
- Comparison with other agricultural commodities

---

## 🎯 EXAMPLE 4: Custom Research (Python)

**Research Question:** Weather patterns and ZL futures correlation

```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o4-mini-deep-research")

response = researcher.research(
    query="""
    Research the correlation between weather patterns (drought, floods, temperature) 
    and ZL (soybean oil) futures prices from 2000-2025.
    
    Include:
    - Specific weather events and their impact on prices
    - Lag effects (how long before prices react)
    - Regional weather impacts (US, Brazil, Argentina)
    - Statistical correlation analysis
    - Academic studies on weather-commodity relationships
    
    Prioritize sources: USDA reports, academic papers, weather service data.
    """,
    max_tool_calls=50,
    use_code_interpreter=True,  # For statistical analysis
)

print(response.output_text)

# Save results
import json
with open('results/research/weather_zl_correlation.json', 'w') as f:
    json.dump({
        "query": "Weather patterns and ZL futures",
        "output": response.output_text,
        "response_id": getattr(response, 'id', None),
    }, f, indent=2)
```

---

## 🎯 EXAMPLE 5: Data Source Evaluation

**Research Question:** Evaluate weather data APIs for agricultural futures trading

```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o4-mini-deep-research")

response = researcher.research_data_sources(
    data_type="weather data APIs",
    use_case="agricultural futures trading (soybean oil)",
)

print(response.output_text)
```

**Expected Output:**
- Comparison of weather APIs (NOAA, Weather.com, OpenWeatherMap, etc.)
- Data quality assessment
- Cost comparison
- Integration complexity
- Suitability for quant trading

---

## 🎯 EXAMPLE 6: Biofuel Policy Impact

**Research Question:** How does biofuel policy affect ZL futures prices?

```bash
python3 scripts/research/research_economic_impact.py \
  "biofuel policy and RINs" \
  --asset ZL \
  --date-range 2010-2025 \
  --model o4-mini-deep-research \
  --output results/research/biofuel_policy_impact.json
```

---

## 🎯 EXAMPLE 7: Regime-Aware Feature Selection

**Research Question:** What features work best in different market regimes?

```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o3-deep-research")  # Use full model for complex analysis

response = researcher.research(
    query="""
    Research regime-aware feature selection methodologies for agricultural futures.
    
    Focus on:
    - Which features are most predictive in trending regimes vs ranging regimes
    - How to identify regime transitions
    - Feature importance changes across regimes
    - Academic research on regime-aware models
    - Best practices for training regime-specific models
    
    Include statistical analysis and citations from quant finance literature.
    """,
    max_tool_calls=60,
    use_code_interpreter=True,
)

print(response.output_text)
```

---

## 📊 USING RESULTS

### Save Results
All scripts support `--output` flag to save results as JSON:
```bash
--output results/research/research_$(date +%Y%m%d_%H%M%S).json
```

### Analyze Results
```python
import json

with open('results/research/zl_fed_regimes_20250115.json', 'r') as f:
    data = json.load(f)

print("Research Output:")
print(data['output'])

# Extract key findings
# Parse citations
# Integrate into feature engineering
```

### Integrate Findings
Use research findings to:
- Update feature engineering scripts
- Refine regime detection logic
- Improve model training strategies
- Validate data source choices

---

## 💡 TIPS

1. **Start Small:** Use `o4-mini-deep-research` and `max_tool_calls=30` for initial research
2. **Save Everything:** Always use `--output` to save results
3. **Review Citations:** Check sources for additional reading
4. **Iterate:** Refine queries based on initial results
5. **Cost Control:** Monitor usage in OpenAI dashboard

---

## 🔗 RELATED

- `docs/setup/DEEP_RESEARCH_QUICK_START.md` - Quick start guide
- `docs/setup/OPENAI_DEEP_RESEARCH_INTEGRATION.md` - Full integration docs
- `src/utils/deep_research.py` - Core utility class

---

**Ready to research! Start with the examples above and adapt for your specific needs.**

