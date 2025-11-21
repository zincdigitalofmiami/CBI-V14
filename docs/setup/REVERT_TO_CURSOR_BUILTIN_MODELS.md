# Revert Cursor IDE to Built-In Models Only

**Date:** November 20, 2025  
**Status:** ✅ Complete - Settings Clean  
**Purpose:** Ensure Cursor uses only its built-in models, not external APIs

---

## ✅ VERIFICATION COMPLETE

### Settings Check Results

**Current Status:**
- ✅ **No custom provider settings** found
- ✅ **No custom baseUrl** settings found
- ✅ **No extra parameters** (like top_k) found
- ✅ **Settings are clean** - ready to use built-in models

**What's Configured:**
- ✅ Gemini extension API key (for extension use only)
- ✅ Cursor composer settings
- ✅ Cloud Code settings
- ✅ Theme and UI settings

**What's NOT Configured (Good):**
- ❌ No custom OpenAI baseUrl
- ❌ No custom provider settings
- ❌ No custom model provider
- ❌ No extra parameters

---

## 📋 HOW TO USE CURSOR BUILT-IN MODELS

### Step 1: Restart Cursor

1. **Quit Cursor completely:**
   - Press `Cmd + Q`
   - Wait for it to fully quit

2. **Reopen Cursor**

### Step 2: Select Built-In Models

1. **Open Chat/Composer:**
   - Press `Cmd + L` (Chat) or `Cmd + I` (Composer)
   - Or click the chat/composer icon

2. **Click the model dropdown** (top of chat window)

3. **Select Cursor's built-in models:**
   - ✅ **Claude 4.5 Sonnet** (recommended)
   - ✅ **Claude 4.5 Sonnet Thinking**
   - ✅ **GPT-5.1** (Cursor version)
   - ✅ **Sonnet 4.5**
   - ✅ **Composer 1**

4. **Avoid these (they use external APIs):**
   - ❌ o3-pro (uses xAI API)
   - ❌ Any model that says "API" or requires API key
   - ❌ Custom model providers
   - ❌ Gemini via Cursor built-in (use extension instead)

### Step 3: Verify It Works

- Ask a question in chat
- Should respond without errors
- No API key errors
- Uses Cursor subscription (Ultra = all models available)

---

## 🔧 IF YOU SEE CUSTOM PROVIDER SETTINGS

### Check Settings JSON

1. **Open Settings JSON:**
   - Press `Cmd + Shift + P`
   - Type: `Preferences: Open Settings (JSON)`

2. **Look for these (should NOT exist):**
   ```json
   {
     "cursor.openAI.baseUrl": "...",  // ❌ Remove
     "cursor.ai.provider": "...",     // ❌ Remove
     "cursor.baseUrl": "...",         // ❌ Remove
     "cursor.extraParameters": {...}, // ❌ Remove
     "cursor.top_k": 40,              // ❌ Remove
   }
   ```

3. **If found, remove them:**
   - Delete the entire line
   - Save the file
   - Restart Cursor

### Run Fix Script

If you need to clean settings again:

```bash
python3 scripts/setup/revert_to_cursor_builtin_models.py
```

This will:
- Backup your settings
- Remove all custom provider/baseUrl settings
- Verify settings are clean

---

## 📊 UNDERSTANDING THE SETUP

### Cursor Built-In Models ✅

**What they are:**
- Models provided by Cursor
- Included with your subscription
- No API keys needed
- No rate limits (Cursor handles it)

**Available models:**
- Claude 4.5 Sonnet
- Claude 4.5 Sonnet Thinking
- GPT-5.1 (Cursor version)
- Sonnet 4.5
- Composer 1

### External API Models ❌

**What they are:**
- Models that require external API keys
- Subject to rate limits
- Can fail if keys invalid

**Examples:**
- o3-pro (xAI API)
- OpenAI API models
- Custom model providers

### Gemini Extension ✅

**What it is:**
- Separate extension for Gemini
- Uses your Google API key
- Bypasses Cursor's buggy built-in integration

**How to use:**
- `Cmd + Shift + P` → "Gemini: Open Chat"
- Works perfectly (no top_k errors)

---

## ✅ VERIFICATION CHECKLIST

After reverting:

- [x] Settings checked - no custom provider settings
- [x] Settings checked - no custom baseUrl
- [x] Settings checked - no extra parameters
- [ ] Cursor restarted
- [ ] Model dropdown shows Cursor models
- [ ] Selected Cursor built-in model
- [ ] Chat works without errors
- [ ] No API key errors

---

## 🎯 SUMMARY

**Current State:**
- ✅ Settings are clean
- ✅ No custom provider settings
- ✅ Ready to use built-in models

**What to Do:**
1. Restart Cursor (`Cmd + Q`)
2. Open Chat/Composer
3. Select Cursor built-in model from dropdown
4. Use normally - no API keys needed

**Codex CLI:**
- ✅ Still works independently
- ✅ Uses OpenAI models separately
- ✅ Not affected by Cursor changes

---

## 📄 RELATED FILES

- `scripts/setup/revert_to_cursor_builtin_models.py` - Revert script
- `docs/setup/CURSOR_CONFIGURATION_STATUS.md` - Current status
- `docs/setup/RESTORE_CURSOR_MODELS.md` - Model restoration guide

---

**Status:** ✅ Ready - Use Cursor Built-In Models Only!

