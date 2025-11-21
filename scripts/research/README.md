# Research Scripts - CBI-V14

**Purpose:** OpenAI Deep Research integration for comprehensive market analysis

---

## 📋 AVAILABLE SCRIPTS

### 1. `check_setup.py`
**Verify your setup is correct**
```bash
python3 scripts/research/check_setup.py
```
Checks:
- OpenAI SDK installation
- API key in Keychain
- Scripts exist and are executable
- Results directory exists

### 2. `test_deep_research.py`
**Test deep research with a simple query**
```bash
python3 scripts/research/test_deep_research.py
```
Quick test to verify everything works.

### 3. `research_market_regimes.py`
**Research market regimes and transitions**
```bash
python3 scripts/research/research_market_regimes.py \
  --asset ZL \
  --date-range 2000-2025 \
  --focus "Fed policy" \
  --output results/research/regimes_zl.json
```

### 4. `research_feature_engineering.py`
**Research feature engineering best practices**
```bash
python3 scripts/research/research_feature_engineering.py \
  --asset ZL \
  --indicator-type momentum \
  --output results/research/features_zl.json
```

### 5. `research_economic_impact.py`
**Research economic impact on asset prices**
```bash
python3 scripts/research/research_economic_impact.py \
  "Fed rate changes" \
  --asset ZL \
  --date-range 2000-2025 \
  --output results/research/fed_impact.json
```

### 6. `batch_research_cbi_v14.py`
**Run multiple research tasks in sequence**
```bash
python3 scripts/research/batch_research_cbi_v14.py
```
Runs:
- Market regimes research
- Feature engineering research
- Fed policy impact
- Trade war impact

Saves all results to `results/research/` with timestamps.

---

## 🚀 QUICK START

1. **Store OpenAI API key:**
   ```bash
   security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U
   ```

2. **Check setup:**
   ```bash
   python3 scripts/research/check_setup.py
   ```

3. **Test:**
   ```bash
   python3 scripts/research/test_deep_research.py
   ```

4. **Run research:**
   ```bash
   python3 scripts/research/research_market_regimes.py --asset ZL
   ```

---

## 💡 USAGE TIPS

### Cost Control
- Start with `o4-mini-deep-research` (lower cost)
- Use `--max-calls` to limit tool usage
- Monitor usage: https://platform.openai.com/usage

### Saving Results
Always use `--output` to save results:
```bash
--output results/research/research_$(date +%Y%m%d).json
```

### Custom Research
Use the DeepResearcher class directly:
```python
from src.utils.deep_research import DeepResearcher

researcher = DeepResearcher(model="o4-mini-deep-research")
response = researcher.research("Your research question")
```

---

## 📚 DOCUMENTATION

- **Quick Start:** `docs/setup/DEEP_RESEARCH_QUICK_START.md`
- **Examples:** `docs/research/DEEP_RESEARCH_EXAMPLES.md`
- **Integration:** `docs/setup/OPENAI_DEEP_RESEARCH_INTEGRATION.md`
- **Setup Complete:** `docs/setup/DEEP_RESEARCH_SETUP_COMPLETE.md`

---

## 🔧 TROUBLESHOOTING

### API Key Not Found
```bash
security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U
```

### Import Errors
Make sure you're in project root:
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
python3 scripts/research/test_deep_research.py
```

### Cost Concerns
- Use `o4-mini-deep-research` instead of `o3-deep-research`
- Reduce `max_tool_calls` (e.g., 20-30)
- Disable code interpreter if not needed

---

**All scripts are ready to use! Check setup first, then start researching.**



