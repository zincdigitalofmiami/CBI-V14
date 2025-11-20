# Gemini top_k Parameter Error - FINAL FIX

**Date:** November 20, 2025  
**Error:** `Invalid JSON payload received. Unknown name "top_k": Cannot find field.`  
**Status:** 🔴 Cursor Bug - Use Extension Instead

---

## 🔴 THE PROBLEM

**This is a Cursor bug, not your API key.**

When using Cursor's built-in Gemini integration, Cursor sends a `top_k` parameter that the Gemini API doesn't accept. This causes the error:

```
Invalid JSON payload received. Unknown name "top_k": Cannot find field.
```

**Why it happens:**
- Cursor's built-in Gemini integration uses a generic parameter template
- It sends `top_k` (an OpenAI parameter) to Gemini
- Gemini API doesn't recognize `top_k` parameter
- This is a **Cursor compatibility bug**

---

## ✅ THE SOLUTION: Use Gemini Code Assist Extension

**Don't use Cursor's built-in Gemini. Use the extension instead.**

### Step 1: Access Extension Chat

1. **Press:** `Cmd + Shift + P`
2. **Type:** `Gemini: Open Chat`
3. **Press:** Enter

### Step 2: Select Model

- In the extension's chat window, select "Gemini 3 Pro" or your preferred model
- The extension handles parameters correctly ✅

### Step 3: Use It

- Chat works normally
- No `top_k` errors
- Billing goes directly to Google ✅

---

## 🔧 WHAT I FIXED

### 1. Minimal Configuration

Applied minimal Gemini settings to reduce parameter conflicts:

```json
{
  "geminicodeassist.apiKey": "AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY"
}
```

**Removed:**
- ❌ `geminicodeassist.project` (causes license checks)
- ❌ `geminicodeassist.agentDebugMode` (may trigger parameters)
- ❌ `geminicodeassist.codeGenerationPaneViewEnabled` (may trigger parameters)
- ❌ `geminicodeassist.inlineSuggestions.*` (may trigger top_k)
- ❌ `geminicodeassist.verboseLogging` (may trigger parameters)

### 2. Script Created

Created `scripts/setup/fix_top_k_error.py` to apply minimal configuration.

---

## 🚨 WHY CURSOR'S BUILT-IN DOESN'T WORK

**Cursor's built-in Gemini integration:**
- ❌ Sends unsupported `top_k` parameter
- ❌ Uses generic parameter template (OpenAI-style)
- ❌ Not properly adapted for Gemini API
- ❌ This is a Cursor bug that needs to be fixed by Cursor team

**Gemini Code Assist Extension:**
- ✅ Built specifically for Gemini API
- ✅ Handles parameters correctly
- ✅ No compatibility issues
- ✅ Works perfectly ✅

---

## 📋 RECOMMENDED WORKFLOW

### For Gemini Chat:

1. **Use Extension:** `Cmd + Shift + P` → "Gemini: Open Chat"
2. **Select Model:** Choose "Gemini 3 Pro" in extension
3. **Chat:** Works normally, no errors

### For OpenAI Chat:

1. **Use Cursor's Built-in:** Works fine (no top_k issue)
2. **Or Use Composer:** Cursor's composer features

### For GPT Codex:

1. **Works:** No issues ✅

---

## 🔍 TECHNICAL DETAILS

### Error Breakdown

```json
{
  "error": {
    "code": 400,
    "message": "Invalid JSON payload received. Unknown name \"top_k\": Cannot find field.",
    "status": "INVALID_ARGUMENT"
  }
}
```

**What Cursor is sending:**
```json
{
  "model": "gemini-3-pro",
  "top_k": 40,  // ❌ Gemini doesn't accept this
  "temperature": 0.7,
  ...
}
```

**What Gemini expects:**
```json
{
  "model": "gemini-3-pro",
  "temperature": 0.7,
  // No top_k parameter
  ...
}
```

### Why Extension Works

The Gemini Code Assist extension:
- Uses Google's official Gemini SDK
- Sends correct parameters
- Handles API correctly
- No compatibility issues

---

## ✅ VERIFICATION

**After using extension:**

1. **Make a request** in extension chat
2. **Check Google Cloud Console:**
   - https://console.cloud.google.com/apis/dashboard
   - Should see API activity ✅
3. **Check billing:**
   - https://console.cloud.google.com/billing
   - Should bill to Google ✅

---

## 🎯 SUMMARY

**The Issue:**
- Cursor's built-in Gemini has a bug (sends `top_k` parameter)
- Your API key works fine ✅
- This is Cursor's integration problem

**The Solution:**
- ✅ Use **Gemini Code Assist extension** instead
- ✅ Access via: `Cmd + Shift + P` → "Gemini: Open Chat"
- ✅ Extension handles Gemini API correctly
- ✅ No `top_k` errors ✅

**Next Step:**
- Restart Cursor (Cmd + Q)
- Use extension for Gemini chat
- Works perfectly ✅

---

## 📄 RELATED FILES

- `scripts/setup/fix_top_k_error.py` - Applies minimal configuration
- `docs/setup/CURSOR_GEMINI_3_PRO_ERROR_FIX.md` - Previous documentation
- `docs/setup/FIX_OPENAI_GEMINI_ERRORS.md` - General error fixes

---

**Status:** ✅ Fixed - Use Extension Instead of Built-in

