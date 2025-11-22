# CBI-V14 Project Context for Gemini

**Project:** CBI-V14 - Comprehensive Baseline Intelligence for Trading  
**Purpose:** This file provides context and instructions for Gemini AI agents working on this project.

---

## 🎯 PROJECT OVERVIEW

CBI-V14 is a quantitative trading system that:
- Collects market data from multiple sources (Databento, Alpha Vantage, FRED, etc.)
- Stores data in BigQuery (us-central1 region)
- Trains machine learning models locally on M4 Mac
- Deploys models to Vertex AI
- Uses 25+ years of historical data
- Implements regime-aware training strategies

---

## 📋 CRITICAL RULES (MUST FOLLOW)

### Data Quality
1. **NO FAKE DATA** - Never use placeholders, synthetic data, or fake values
2. **ALWAYS CHECK BEFORE CREATING** - Verify tables/schemas/datasets exist before creating
3. **ALWAYS AUDIT AFTER WORK** - Run data quality checks after modifications

### Cost & Resource Management
4. **us-central1 ONLY** - All BigQuery/GCS resources MUST be in us-central1 (never US multi-region)
5. **NO COSTLY RESOURCES WITHOUT APPROVAL** - Don't create Cloud SQL, Workstations, etc. without approval

### Research & Validation
6. **RESEARCH BEST PRACTICES** - Always research online before implementing
7. **RESEARCH QUANT FINANCE** - For modeling features, research quant finance best practices

---

## 🏗️ ARCHITECTURE

### Current Stack
- **Training:** Local M4 Mac → Vertex AI deployment
- **Data Storage:** BigQuery (us-central1)
- **Data Sources:** Databento, Alpha Vantage, FRED, NewsAPI
- **Models:** TCN, LSTM, XGBoost, ensemble architectures
- **Deployment:** Vertex AI endpoints

### NOT Using
- ❌ BQML training (we use Vertex AI)
- ❌ AutoML (we use custom neural models)
- ❌ Cloud-first training (we train locally)

---

## 📁 KEY DIRECTORIES

### Current Files (USE THESE)
- `scripts/data_quality_checks.py` - Data validation
- `scripts/export_training_data.py` - Training data export
- `src/training/baselines/*.py` - Baseline models
- `vertex-ai/deployment/*.py` - Deployment scripts
- `config/bigquery/bigquery-sql/*.sql` - SQL queries

### Legacy (IGNORE)
- `archive/` - Old/archived work
- `legacy/` - Legacy implementations
- Anything mentioning BQML or AutoML

---

## 🔑 API KEYS & SECURITY

### Key Management
- All API keys stored in macOS Keychain
- Use `src/utils/keychain_manager.py` to retrieve keys
- Never hardcode keys in code

### Current API Keys
- **Gemini API:** `AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY` (project: cbi-v14)
- **OpenAI API:** Stored in Keychain as `cbi-v14.OPENAI_API_KEY` (for Deep Research)
- **Databento:** Stored in Keychain as `cbi-v14.DATABENTO_API_KEY`
- **Alpha Vantage:** Stored in Keychain as `cbi-v14.ALPHA_VANTAGE_API_KEY`
- **FRED:** Stored in Keychain as `cbi-v14.FRED_API_KEY`

---

## 📊 DATA SOURCES

### Primary Sources
1. **Databento** - Market data (ZL futures, ES futures)
2. **Alpha Vantage** - Technical indicators, options, FX, commodities
3. **FRED** - Economic indicators
4. **NewsAPI** - News sentiment data

### Data Flow
```
External APIs → Python Scripts → External Drive (/Volumes/Satechi Hub/) → BigQuery
```

---

## 🎓 TRAINING METHODOLOGY

### Phase 1: Baseline Testing
- Run comprehensive baselines on ALL features (400-500+)
- Test ALL data (25+ years)
- Test ALL regimes
- Test multiple architectures (TCN, LSTM, XGBoost, ensemble)
- Use SHAP for feature importance
- Conduct ablation studies

### Phase 2: Refined Training
- Apply baseline learnings
- Keep proven features, drop non-contributors
- Optimal feature set determined by evidence, not theory
- Regime-aware training (separate models per regime or regime-weighted)

---

## 🚫 COMMON MISTAKES TO AVOID

1. **Don't create resources in wrong regions** - Always us-central1
2. **Don't use fake data** - Only real, verified data
3. **Don't skip data quality checks** - Always audit after work
4. **Don't create costly resources** - Get approval first
5. **Don't reference archive/legacy** - Use current files only
6. **Don't assume schema** - Always check before creating tables

---

## 📚 REFERENCE DOCUMENTATION

### Must Read Before Work
- `docs/plans/GPT_READ_FIRST.md` - Start here
- `docs/plans/MASTER_PLAN.md` - Source of truth
- `docs/plans/TRAINING_PLAN.md` - Training strategy
- `.cursorrules` - Complete best practices

### Key Plans
- `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md` - Training execution
- `docs/plans/BIGQUERY_MIGRATION_PLAN.md` - BigQuery setup
- `docs/reference/BEST_PRACTICES_DRAFT.md` - Detailed best practices

---

## 🔧 WORKFLOW CHECKLIST

### Before Starting Work
- [ ] Read `docs/plans/GPT_READ_FIRST.md`
- [ ] Check existing resources (tables, datasets, files)
- [ ] Research best practices for the task
- [ ] Verify naming conventions
- [ ] Estimate costs if creating GCP resources

### During Work
- [ ] Follow existing patterns in codebase
- [ ] Use source prefixes for columns
- [ ] Document complex logic
- [ ] Test code as you write
- [ ] Validate data at each stage

### After Work
- [ ] Run data quality checks
- [ ] Audit for errors (nulls, duplicates, gaps)
- [ ] Test queries/scripts
- [ ] Verify BigQuery views/tables
- [ ] Update documentation
- [ ] Clean up temporary resources

---

## 💡 QUICK REFERENCE

### BigQuery Best Practices
- Partition on date columns
- Cluster on frequently filtered columns
- Limit query date ranges
- Monitor query costs (stay under 1 TB/month)

### Model Training
- Run 24-audit suite before training (`config/bigquery/bigquery-sql/24_AUDIT_SUITE.sql`)
- Use local M4 Mac only
- Validate training data quality
- Save models with proper metadata

### Cost Lessons
- See `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - AI created ~$250/month mistake
- Always use us-central1, never US multi-region
- Get approval for any resource > $5/month

---

## 🎯 CURRENT FOCUS AREAS

1. **Alpha Vantage Integration** - Collecting 50+ technical indicators
2. **Baseline Training** - Comprehensive feature testing
3. **Data Quality** - Continuous validation and auditing
4. **Regime-Aware Training** - Separate models per market regime
5. **Deep Research** - OpenAI Deep Research for market analysis and feature engineering research

## 🔬 DEEP RESEARCH CAPABILITIES

**OpenAI Deep Research** is integrated for comprehensive research tasks:

### Available Research Scripts
- `scripts/research/research_market_regimes.py` - Market regime analysis
- `scripts/research/research_feature_engineering.py` - Feature engineering best practices
- `scripts/research/research_economic_impact.py` - Economic impact analysis
- `scripts/research/batch_research_cbi_v14.py` - Batch research for multiple topics

### Quick Start
```bash
# Store OpenAI API key
security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U

# Test setup
python3 scripts/research/test_deep_research.py

# Run research
python3 scripts/research/research_market_regimes.py --asset ZL
```

### Use Cases
- Market regime research and analysis
- Feature engineering best practices
- Economic impact studies (Fed policy, trade wars, etc.)
- Data source evaluation
- Quant finance methodology research

See `docs/setup/DEEP_RESEARCH_QUICK_START.md` for full documentation.

---

## 📞 WHEN IN DOUBT

1. **Check existing code** - Look for similar patterns
2. **Read the plans** - `docs/plans/` has the answers
3. **Research online** - Best practices, quant finance papers
4. **Ask before creating** - Especially for GCP resources
5. **Always audit** - Data quality checks are mandatory

---

**Last Updated:** January 2025  
**Project Status:** Active Development - Phase 1 (Infrastructure & Baseline Testing)

