# Deep Research Installation Guide

**Quick setup checklist for OpenAI Deep Research**

---

## ✅ INSTALLATION STEPS

### Step 1: Install OpenAI SDK
```bash
pip install openai
```

Or if using a virtual environment:
```bash
# Activate your venv first
source .venv/bin/activate  # or your venv path
pip install openai
```

### Step 2: Store OpenAI API Key
```bash
security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U
```

Replace `sk-...` with your actual OpenAI API key from:
https://platform.openai.com/api-keys

### Step 3: Verify Setup
```bash
python3 scripts/research/check_setup.py
```

All checks should pass ✅

### Step 4: Test
```bash
python3 scripts/research/test_deep_research.py
```

---

## 🔍 TROUBLESHOOTING

### "No module named 'openai'"
**Fix:** Install the SDK
```bash
pip install openai
```

### "OPENAI_API_KEY not found in Keychain"
**Fix:** Store your key
```bash
security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w "sk-..." -U
```

### Import errors
**Fix:** Make sure you're in project root
```bash
cd /Users/kirkmusick/Documents/GitHub/CBI-V14
python3 scripts/research/check_setup.py
```

---

## ✅ VERIFICATION

After installation, run:
```bash
python3 scripts/research/check_setup.py
```

You should see:
- ✅ OpenAI SDK installed
- ✅ OpenAI API key found in Keychain
- ✅ DeepResearcher class can be imported
- ✅ Research scripts exist and are executable
- ✅ Results directory exists

---

**Once all checks pass, you're ready to research! 🚀**



