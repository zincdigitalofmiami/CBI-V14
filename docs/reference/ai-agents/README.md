# AI Agent Documentation

**Location:** `docs/reference/ai-agents/`  
**Purpose:** Centralized documentation for all AI assistants working on CBI-V14

---

## 📚 Available Agent Manuals

### Core Manuals

| File | Platform | Purpose |
|------|----------|---------|
| **`claude.md`** | Anthropic Claude | Complete project manual for Claude AI assistants |
| **`grok.md`** | X/Twitter Grok | Complete project manual for Grok AI assistants |
| **`grok_system_prompt.txt`** | X/Twitter Grok (Web) | Copy-paste system prompt for web-based Grok interface |

---

## 🚀 Quick Start

### For Claude (Anthropic)
1. Read `claude.md` - Complete project manual
2. Review `../BEST_PRACTICES_DRAFT.md` - Mandatory best practices
3. Check `../ANSWERS_TO_GPT_QUESTIONS.md` - Common scenarios

### For Grok (X/Twitter)
1. **Code Editor Integration:** Read `grok.md` - Complete project manual
2. **Web Interface:** Copy contents of `grok_system_prompt.txt` into Grok's system prompt field

### For Cursor IDE
- See `.cursorrules` (root directory) - Cursor-specific rules and workflows
- See `.cursorignore` (root directory) - Files excluded from indexing

---

## 🏗️ Architecture Rules (Summary)

**CRITICAL - All AI assistants must follow these:**

1. **BigQuery is system of record**
   - Project: `cbi-v14`, Region: `us-central1`
   - External drive is cache/backup only, never source of truth

2. **Mac M-series handles ALL training**
   - NO BigQuery ML, NO Vertex AI, NO cloud training
   - All training via Python scripts on Mac, data pulled from BigQuery

3. **Targets are future price levels**
   - ZL production targets: future price **levels** (not returns)
   - Horizons: 1w (5d), 1m (20d), 3m (60d), 6m (120d), 12m (240d)

4. **Factor families A-H + Big 8**
   - All features must belong to documented factor families
   - Core signal set: "Big 8" drivers for ZL (crush, China, dollar, Fed, tariffs, biofuels, energy complex, palm)

5. **NO FAKE OR SYNTHETIC DATA**
   - Zero tolerance for placeholders, synthetic values, or "we'll fix it later"
   - All data from authenticated APIs or official sources only

---

## 📖 Related Documentation

### In `docs/reference/`
- **`BEST_PRACTICES_DRAFT.md`** - Comprehensive best practices (mandatory reading)
- **`ANSWERS_TO_GPT_QUESTIONS.md`** - Common questions and answers
- **`ACTIVE_EXECUTION_DOCS.md`** - Index of live execution documents

### In `docs/plans/`
- **`MASTER_PLAN.md`** - Canonical architecture and philosophy (START HERE)
- **`ZL_PRODUCTION_SPEC.md`** - Non-negotiable ZL baseline contract
- **`TRAINING_PLAN.md`** - High-level modeling/training phases

### Root Directory
- **`.cursorrules`** - Cursor IDE configuration
- **`.cursorignore`** - Cursor indexing exclusions

---

## 🎯 What Each Manual Contains

### `claude.md` & `grok.md` (Both contain):
- Where to start (canonical docs)
- Hard architecture rules
- Code & repo map
- Modeling rules (ZL baselines)
- Behavior & "Do Not" rules
- Ingestion & freshness guidelines
- Experiments vs Production
- Critical best practices
- Communication style
- Domain knowledge (ZL/MES drivers)
- Quant finance principles

### `grok_system_prompt.txt` (Web interface):
- Formatted as direct system prompt
- Copy-paste ready for Grok web interface
- Same content as `grok.md` but in prompt format

---

## ⚠️ Critical Rules for All AI Assistants

### NEVER DO:
- Create new plan documents (update existing ones)
- Use pandas-gbq (use google-cloud-bigquery only)
- Suggest Vertex AI or BQML for training (Mac-only)
- Use fake/synthetic data (zero tolerance)
- Create resources outside us-central1
- Create costly resources without approval (>$5/month)

### ALWAYS DO:
- Check existing resources before creating
- Audit after any data modification
- Research best practices before implementing
- Validate formulas against authoritative sources
- Follow source prefixing conventions
- Respect train/val/test splits

---

## 📁 File Organization

```
docs/reference/ai-agents/
├── README.md                    ← You are here
├── claude.md                    ← Claude manual
├── grok.md                      ← Grok manual
└── grok_system_prompt.txt        ← Grok web prompt
```

---

## 🔗 Quick Links

- **Start Here:** `docs/plans/MASTER_PLAN.md`
- **Production Spec:** `docs/plans/ZL_PRODUCTION_SPEC.md`
- **Best Practices:** `docs/reference/BEST_PRACTICES_DRAFT.md`
- **Active Docs Index:** `docs/reference/ACTIVE_EXECUTION_DOCS.md`

---

**Last Updated:** November 26, 2025  
**Maintained By:** CBI-V14 Team
