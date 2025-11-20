# Cursor AI Agents Diagnosis & Configuration

**Date:** November 2025  
**Issue:** GPT key not working, Gemini key status unknown

---

## 🔍 DIAGNOSIS RESULTS

### Current Status

**Settings Files Checked:**
- ✅ `~/Library/Application Support/Cursor/User/settings.json` - No AI settings found
- ✅ `~/.cursor/ide_state.json` - No AI settings found  
- ✅ `~/.cursor/mcp.json` - Empty (no MCP servers configured)

**Environment Variables:**
- ❌ No API keys found in environment variables
- ❌ OPENAI_API_KEY: Not set
- ❌ GEMINI_API_KEY: Not set
- ❌ GOOGLE_API_KEY: Not set

**MCP Configuration:**
- ⚠️ No MCP servers configured

**Keychain:**
- Need to check manually (see below)

---

## 🎯 WHERE TO FIND AI AGENT SETTINGS IN CURSOR

### Method 1: Cursor Settings UI (Recommended)

1. **Open Cursor Settings:**
   - Press `Cmd + ,` (or Cursor → Settings)
   - Or: `Cursor → Preferences → Settings`

2. **Search for AI Settings:**
   - Search for: `"OpenAI"` or `"API"` or `"Language Model"`
   - Look for these settings:
     - `cursor.openAI.apiKey`
     - `cursor.gemini.apiKey`
     - `cursor.languageModel.*`
     - `cursor.customModelProvider.*`

3. **Check AI Features Section:**
   - Go to: `Features → AI` or `Features → Language Models`
   - Look for model provider settings
   - Check if GPT/Gemini are enabled

### Method 2: Command Palette

1. Press `Cmd + Shift + P`
2. Type: `"Cursor: Open Settings"`
3. Search for: `"OpenAI"` or `"Gemini"` or `"API Key"`

### Method 3: Settings JSON (Advanced)

1. Press `Cmd + Shift + P`
2. Type: `"Preferences: Open User Settings (JSON)"`
3. Look for keys like:
   - `"cursor.openAI.apiKey"`
   - `"cursor.gemini.apiKey"`
   - `"cursor.languageModel.*"`

---

## 🔧 HOW TO FIX GPT KEY ISSUE

### Step 1: Verify Key Format

**OpenAI API Key Format:**
- Should start with `sk-`
- Example: `sk-proj-...` or `sk-...`
- Length: Usually 51+ characters

**Common Issues:**
- ❌ Key missing `sk-` prefix
- ❌ Key truncated (copied incorrectly)
- ❌ Key expired or revoked
- ❌ Wrong key type (using organization key instead of personal)

### Step 2: Check Key Status

1. **Test Key Directly:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY_HERE"
   ```

2. **Check OpenAI Dashboard:**
   - Go to: https://platform.openai.com/api-keys
   - Verify key exists and is active
   - Check usage/credits available

### Step 3: Re-enter Key in Cursor

1. Open Cursor Settings (`Cmd + ,`)
2. Search for `"OpenAI"` or `"API Key"`
3. Clear existing key (if any)
4. Paste new key
5. Save settings
6. Restart Cursor

### Step 4: Check Cursor Logs

1. Open Cursor
2. Go to: `Help → Toggle Developer Tools`
3. Check Console for errors
4. Look for API key related errors

---

## 🔍 HOW TO CHECK GEMINI STATUS

### Step 1: Verify Gemini is Available in Cursor

**Gemini Support:**
- Cursor may or may not have native Gemini support
- Check Cursor version/release notes
- May require extension or custom model provider

### Step 2: Check for Gemini Settings

1. Open Cursor Settings (`Cmd + ,`)
2. Search for: `"Gemini"` or `"Google"`
3. Look for:
   - `cursor.gemini.apiKey`
   - `cursor.google.apiKey`
   - Custom model provider settings

### Step 3: Verify Gemini Key Format

**Google API Key Format:**
- Usually starts with `AIza...`
- Or may be a service account JSON
- Check Google Cloud Console: https://console.cloud.google.com/apis/credentials

### Step 4: Check if Gemini is Enabled

- Look for model selection dropdown
- Check if Gemini appears as an option
- May need to enable in Cursor settings

---

## 📋 QUICK CHECKLIST

### For GPT Key:
- [ ] Key is in Cursor Settings (Cmd+, → search "OpenAI")
- [ ] Key format is correct (starts with `sk-`)
- [ ] Key is active in OpenAI dashboard
- [ ] Key has credits/permissions
- [ ] Cursor has been restarted after setting key
- [ ] Check Cursor logs for errors

### For Gemini:
- [ ] Gemini is supported in your Cursor version
- [ ] Key is in Cursor Settings (Cmd+, → search "Gemini")
- [ ] Key format is correct (Google API key)
- [ ] Key is active in Google Cloud Console
- [ ] Gemini is enabled/selected as model
- [ ] Check Cursor logs for errors

---

## 🛠️ TROUBLESHOOTING COMMANDS

### Check Cursor Settings File
```bash
cat ~/Library/Application\ Support/Cursor/User/settings.json | python3 -m json.tool
```

### Check for API Keys in Keychain
```bash
# OpenAI
security find-generic-password -a "OpenAI" 2>/dev/null

# Google/Gemini
security find-generic-password -a "Google" 2>/dev/null
security find-generic-password -a "Gemini" 2>/dev/null

# Cursor
security find-generic-password -a "Cursor" 2>/dev/null
```

### Run Diagnostic Script
```bash
python3 scripts/analysis/check_cursor_ai_agents.py
```

---

## 📝 WHERE CURSOR STORES API KEYS

Cursor typically stores API keys in:
1. **Encrypted storage** (not in plain JSON files)
2. **macOS Keychain** (for secure storage)
3. **Internal database** (Cursor's own storage)
4. **Settings JSON** (may be encrypted or obfuscated)

**You won't see keys in plain text** - this is by design for security.

---

## ✅ NEXT STEPS

1. **Open Cursor Settings** (`Cmd + ,`)
2. **Search for "OpenAI"** - Check if key is set
3. **Search for "Gemini"** - Check if key is set
4. **Check model selection** - See what models are available
5. **Review Cursor logs** - Look for API key errors
6. **Test keys directly** - Verify they work outside Cursor

---

## 🔗 RESOURCES

- **OpenAI API Keys:** https://platform.openai.com/api-keys
- **Google Cloud API Keys:** https://console.cloud.google.com/apis/credentials
- **Cursor Documentation:** Check Cursor's help/docs for AI model configuration

---

**Status:** ⚠️ No API keys found in accessible settings files  
**Action Required:** Check Cursor Settings UI directly (keys are stored securely, not in plain text)

