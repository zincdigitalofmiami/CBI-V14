# Fix xAI API Key Error - Use Cursor Models

**Date:** November 20, 2025  
**Error:** `Incorrect API key provided: sk***QA. You can obtain an API key from https://console.x.ai`  
**Status:** ✅ Solution Available

---

## 🔴 THE ERROR

**Error Message:**
```
ERROR_OPENAI
Unable to reach the model provider
Incorrect API key provided: sk***QA
You can obtain an API key from https://console.x.ai
```

**What this means:**
- Cursor is trying to use xAI (x.ai) API
- The xAI API key is invalid or missing
- Cursor is routing to external API instead of built-in models

---

## ✅ SOLUTION: Use Cursor's Built-In Models

**The fix:** Select Cursor's built-in models instead of external APIs.

### Step 1: Check Model Selection

1. **Open Cursor Chat/Composer**
2. **Look at the model dropdown** (top of chat window)
3. **Check what model is selected:**
   - ❌ If it says "o3-pro" or "xAI" → This uses external API
   - ✅ Should say "Claude 4.5 Sonnet" or "GPT-5.1" (Cursor)

### Step 2: Switch to Cursor Models

1. **Click the model dropdown**
2. **Select Cursor's built-in models:**
   - ✅ **Claude 4.5 Sonnet** (recommended)
   - ✅ **Claude 4.5 Sonnet Thinking**
   - ✅ **GPT-5.1** (Cursor's version, not OpenAI API)
   - ✅ **Sonnet 4.5**
   - ✅ **Composer 1**

3. **Avoid these (they use external APIs):**
   - ❌ o3-pro (uses xAI API)
   - ❌ Any model that says "API" or requires API key
   - ❌ Custom model providers

### Step 3: Verify It Works

- Try asking a question in chat
- Should work without API key errors
- Uses Cursor's subscription (Ultra = all models available)

---

## 🔧 IF MODELS STILL DON'T WORK

### Option 1: Clear Cursor Cache

1. **Quit Cursor completely:**
   - `Cmd + Q`

2. **Clear cache:**
   ```bash
   rm -rf ~/Library/Application\ Support/Cursor/Cache
   ```

3. **Reopen Cursor**
4. **Try again**

### Option 2: Reset Model Preferences

Run the restore script:
```bash
python3 scripts/setup/restore_cursor_models.py
```

This resets model preferences to use Cursor defaults.

### Option 3: Check Cursor Settings

1. **Open Cursor Settings:**
   - `Cmd + ,` (Settings)

2. **Search for:**
   - "model"
   - "provider"
   - "custom"

3. **Disable any custom model providers:**
   - Uncheck "Use custom model providers"
   - Disable any external API integrations

---

## 📊 UNDERSTANDING THE ISSUE

### Why This Happens

**Cursor has two types of models:**

1. **Built-in Models (What you want):**
   - Claude 4.5 Sonnet
   - GPT-5.1 (Cursor version)
   - Sonnet 4.5
   - Composer 1
   - ✅ No API key needed
   - ✅ Uses Cursor subscription
   - ✅ No rate limits

2. **External API Models (What's failing):**
   - o3-pro (xAI API)
   - OpenAI API models
   - Custom providers
   - ❌ Requires API keys
   - ❌ Subject to rate limits
   - ❌ Can fail if keys invalid

### Your Situation

- **Subscription:** Ultra (all built-in models available)
- **Problem:** Cursor is trying to use xAI API instead of built-in models
- **Solution:** Select built-in models from dropdown

---

## ✅ VERIFICATION

### Check Model Selection

1. Open Chat/Composer
2. Look at model dropdown
3. Should show: "Claude 4.5 Sonnet" or similar (Cursor model)
4. Should NOT show: "o3-pro" or "xAI" or "API"

### Test Chat

1. Ask a simple question
2. Should respond without errors
3. No API key errors
4. Works with Cursor subscription

---

## 🎯 SUMMARY

**Problem:**
- Cursor trying to use xAI API → Invalid API key error

**Solution:**
- Use Cursor's built-in models instead
- Select from model dropdown
- Avoid external API models

**Next Steps:**
1. Open Chat/Composer
2. Click model dropdown
3. Select "Claude 4.5 Sonnet" or other Cursor models
4. Avoid "o3-pro" or external API models

---

**Status:** ✅ Use Cursor Built-In Models - No API Keys Needed!

