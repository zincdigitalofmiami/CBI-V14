# Deep Research Quick Start - CBI-V14

**Date:** January 2025  
**Status:** ✅ Ready to use with OpenAI Pro plan

---

## 🚀 QUICK START

### 1. Store OpenAI API Key

```bash
# Store your OpenAI API key in Keychain
security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U
```

### 2. Run Your First Research

**Research market regimes:**
```bash
python3 scripts/research/research_market_regimes.py --asset ZL --date-range 2000-2025
```

**Research feature engineering:**
```bash
python3 scripts/research/research_feature_engineering.py --asset ZL --indicator-type momentum
```

**Research economic impact:**
```bash
python3 scripts/research/research_economic_impact.py "Fed rate changes" --asset ZL
```

---

## 📋 AVAILABLE SCRIPTS

### Market Regimes Research
```bash
python3 scripts/research/research_market_regimes.py \
  --asset ZL \
  --date-range 2000-2025 \
  --focus "Fed policy" \
  --model o4-mini-deep-research \
  --output results/regimes_zl.json
```

### Feature Engineering Research
```bash
python3 scripts/research/research_feature_engineering.py \
  --asset ZL \
  --indicator-type volatility \
  --model o4-mini-deep-research \
  --output results/features_zl.json
```

### Economic Impact Research
```bash
python3 scripts/research/research_economic_impact.py \
  "trade wars" \
  --asset ZL \
  --date-range 2018-2025 \
  --model o4-mini-deep-research \
  --output results/trade_war_impact.json
```

### Custom Research (Python)
```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o4-mini-deep-research")

response = researcher.research(
    query="Research the impact of weather patterns on ZL futures prices",
    max_tool_calls=40,
)

print(response.output_text)
```

---

## 🎯 RECOMMENDED RESEARCH TOPICS FOR CBI-V14

### 1. Market Regimes
- ZL regime transitions 2000-2025
- Fed policy impact on regimes
- Trade war regime analysis
- Weather-driven regime changes

### 2. Feature Engineering
- Best technical indicators for ZL
- Optimal lookback periods
- Regime-aware feature selection
- Feature interaction strategies

### 3. Economic Impact
- Fed rate changes → ZL prices
- Trade wars → ZL prices
- Biofuel policy → ZL prices
- China imports → ZL prices

### 4. Data Sources
- Weather data APIs evaluation
- Economic indicator APIs comparison
- News sentiment APIs review
- Alternative data sources

---

## 💰 COST MANAGEMENT

**With Pro Plan:**
- `o4-mini-deep-research`: Lower cost, good for most tasks
- `o3-deep-research`: Higher cost, more comprehensive
- Use `--max-calls` to limit tool usage
- Monitor usage: https://platform.openai.com/usage

**Recommended Settings:**
- Start with `o4-mini-deep-research`
- Use `max_tool_calls=30-50` for cost control
- Use background mode (default) for long tasks

---

## 📊 OUTPUT FORMAT

Results include:
- Comprehensive research report
- Inline citations
- Source metadata
- Statistical analysis (if code interpreter used)
- Web search results

Save to JSON for later analysis:
```bash
--output results/research_$(date +%Y%m%d).json
```

---

## 🔧 ADVANCED USAGE

### Custom Research Query
```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o3-deep-research")

response = researcher.research(
    query="""
    Research the relationship between Brazilian soybean production and ZL futures prices.
    Include statistical analysis, correlation studies, and lag effects.
    """,
    instructions="Focus on quantitative analysis and data-backed conclusions.",
    max_tool_calls=60,
    use_code_interpreter=True,
    use_web_search=True,
)

print(response.output_text)
```

### With Vector Stores (Future)
```python
response = researcher.research(
    query="Research market regimes using our internal data",
    vector_store_ids=["vs_12345..."],
    max_tool_calls=50,
)
```

---

## 📝 NOTES

- **Background Mode:** Default enabled - tasks run asynchronously
- **Timeouts:** Set to 3600 seconds (1 hour) by default
- **Citations:** All results include inline citations
- **Cost:** Monitor via OpenAI dashboard
- **Storage:** Results can be saved to JSON for analysis

---

## 🎯 NEXT STEPS

1. ✅ Store OpenAI API key in Keychain
2. ✅ Run first research task
3. ✅ Review results and citations
4. ✅ Integrate findings into feature engineering
5. ✅ Use for regime analysis

**You're all set! Start researching! 🚀**

