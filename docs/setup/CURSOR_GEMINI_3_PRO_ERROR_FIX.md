# Gemini 3 Pro Error Fix

**Date:** November 20, 2025  
**Error:** `Invalid JSON payload received. Unknown name "top_k": Cannot find field.`

---

## 🔴 THE PROBLEM

When selecting **"Gemini 3 Pro"** in Cursor's model dropdown, you get this error:

```
Invalid JSON payload received. Unknown name "top_k": Cannot find field.
```

**What's happening:**
- ✅ Your API key IS working (request reaches Google)
- ❌ Cursor is sending `top_k` parameter that Gemini 3 Pro doesn't accept
- This is a **Cursor compatibility issue**, not your API key

---

## ✅ SOLUTIONS

### Solution 1: Use Gemini Code Assist Extension (RECOMMENDED)

**This extension handles Gemini API correctly:**

1. **Install/Use:** Gemini Code Assist extension (already installed)
2. **Access:** `Cmd + Shift + P` → "Gemini: Open Chat"
3. **Select:** "Gemini 3 Pro" in the extension's chat
4. **Works:** ✅ No `top_k` error, billing goes to Google

**Why this works:**
- Extension is built specifically for Gemini API
- Handles parameters correctly
- Uses your API key (billing to Google)

---

### Solution 2: Use Different Model in Cursor

**Try these models that Cursor supports better:**
- `GPT-5.1 High` (currently selected, works)
- `GPT-5.1 Codex High Fast`
- `Sonnet 4.5`
- `Composer 1`

**Note:** These may bill to Cursor, not Google (depending on configuration)

---

### Solution 3: Report Bug to Cursor

**This is a Cursor bug:**
- Cursor shouldn't send `top_k` to Gemini 3 Pro
- They need to fix their Gemini 3 Pro integration

**How to report:**
1. Cursor Settings → Help → Report Issue
2. Include error message and request ID: `f0362db4-8cfd-4852-b524-0275aad09a7c`

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

**What this means:**
- Cursor is sending: `{"top_k": <value>, ...}`
- Gemini 3 Pro expects: Different parameter structure
- Gemini API doesn't recognize `top_k` parameter

### Why It Happens

Cursor's model integration likely:
1. Uses a generic parameter template for all models
2. Sends `top_k` (common in OpenAI models) to Gemini
3. Gemini 3 Pro doesn't support `top_k` (or uses different name)

---

## ✅ RECOMMENDED ACTION

**Use Gemini Code Assist Extension:**
- ✅ Works with Gemini 3 Pro
- ✅ Uses your API key (billing to Google)
- ✅ Proper parameter handling
- ✅ No compatibility issues

**Access:** `Cmd + Shift + P` → "Gemini: Open Chat"

---

## 📊 VERIFICATION

**After using Gemini Code Assist:**
1. Make a request
2. Check Google Cloud Console: https://console.cloud.google.com/apis/dashboard
3. Look for API calls → ✅ Should see activity
4. Check billing: https://console.cloud.google.com/billing → ✅ Should bill to Google

---

## 🎯 SUMMARY

**The Issue:**
- Cursor's built-in "Gemini 3 Pro" has a bug (sends invalid `top_k` parameter)
- Your API key works fine
- This is Cursor's integration problem

**The Solution:**
- Use **Gemini Code Assist extension** instead
- It handles Gemini 3 Pro correctly
- Billing goes to Google ✅

**Next Step:**
- `Cmd + Shift + P` → "Gemini: Open Chat"
- Select "Gemini 3 Pro" in extension
- Test and verify in Google Cloud Console







