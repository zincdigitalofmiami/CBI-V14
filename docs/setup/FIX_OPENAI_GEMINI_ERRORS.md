# Fix OpenAI & Gemini Errors - Quick Guide

**Date:** January 2025  
**Issues:** 
1. OpenAI organization verification needed
2. Gemini `top_k` parameter error

---

## 🔴 ERROR 1: OpenAI Organization Verification

**Error Message:**
```
Your organization must be verified to generate reasoning summaries.
Please go to: https://platform.openai.com/settings/organization/general
```

**Fix:**
1. **Go to OpenAI Settings:**
   - https://platform.openai.com/settings/organization/general
   - Sign in with your OpenAI account

2. **Verify Organization:**
   - Click "Verify Organization" button
   - Follow the verification process
   - Wait up to 15 minutes for access to propagate

3. **Alternative: Disable Reasoning Summaries**
   - If you don't need reasoning summaries, Cursor may have a setting to disable them
   - Check Cursor Settings → Search "reasoning" or "summary"

---

## 🔴 ERROR 2: Gemini `top_k` Parameter Error

**Error Message:**
```
Invalid JSON payload received. Unknown name "top_k": Cannot find field.
```

**This is the same Gemini issue we fixed before!** Cursor is sending `top_k` parameter that Gemini doesn't accept.

**Fixes:**

### Option 1: Remove Project Setting (Quick Fix)

1. **`Cmd + Shift + P`** → "Preferences: Open User Settings (JSON)"
2. **Find and delete:**
   ```json
   "geminicodeassist.project": "cbi-v14",
   ```
3. **Save and restart Cursor**

This makes Gemini use individual tier which may avoid the parameter issue.

### Option 2: Use Different Model

**In Cursor's model selection:**
- Don't use "Gemini 3 Pro" from Cursor's dropdown
- Use "Gemini Code Assist" extension instead:
  - `Cmd + Shift + P` → "Gemini: Open Chat"
  - Select model in the extension's chat

### Option 3: Disable Gemini in Cursor, Use Extension Only

1. **Disable Cursor's built-in Gemini:**
   - Settings → Search "gemini"
   - Disable any Cursor-native Gemini settings

2. **Use Gemini Code Assist Extension:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - This extension handles parameters correctly

---

## ✅ QUICK FIX CHECKLIST

### For OpenAI:
- [ ] Go to: https://platform.openai.com/settings/organization/general
- [ ] Click "Verify Organization"
- [ ] Wait 15 minutes
- [ ] Test again

### For Gemini:
- [ ] Remove `geminicodeassist.project` from settings
- [ ] OR: Use Gemini Code Assist extension instead of Cursor's built-in
- [ ] OR: Disable Cursor's Gemini integration
- [ ] Restart Cursor

---

## 🎯 RECOMMENDED ACTION

**Immediate fixes:**

1. **OpenAI:** Verify organization (5 minutes)
   - https://platform.openai.com/settings/organization/general

2. **Gemini:** Remove project setting (30 seconds)
   ```json
   // Delete this line from settings.json:
   "geminicodeassist.project": "cbi-v14",
   ```

3. **Restart Cursor**

4. **Test:**
   - OpenAI should work after org verification
   - Gemini should work via extension (Cmd+Shift+P → "Gemini: Open Chat")

---

## 🔍 WHY THESE ERRORS HAPPEN

### OpenAI Error:
- Cursor is trying to use "reasoning summaries" feature
- This requires organization verification
- New security requirement from OpenAI

### Gemini Error:
- Cursor's built-in Gemini integration sends `top_k` parameter
- Gemini API doesn't accept `top_k` (it's an OpenAI parameter)
- This is a Cursor compatibility bug
- Using the extension avoids this (extension handles parameters correctly)

---

## 🧪 QUOTAS VS REAL ERRORS

### Previous Issues (NOT Quota Related)

From direct API tests:
- Made multiple rapid requests to the Gemini API with your key
- No rate limit or quota errors occurred
- API key works and quotas are not being hit

The real issues were:
- `top_k` parameter error → Cursor bug in its built-in Gemini integration
- `ERROR_BAD_USER_API_KEY` → Expired/invalid Cursor authentication token (not Gemini/OpenAI keys)
- OpenAI "organization must be verified" → Security requirement from OpenAI

### NEW: Actual Quota Error (TPM Rate Limit)

**If you see this error:**
```
Request too large for gpt-5.1 on tokens per min (TPM): Limit 30000, Requested 162807
```

**This IS a quota/rate limit issue:**
- ✅ Real rate limit error
- ✅ TPM (Tokens Per Minute) limit exceeded
- ✅ Request is too large for your plan

**Fix:** See `docs/setup/OPENAI_TPM_RATE_LIMIT_FIX.md` for solutions

### How to Tell the Difference

**Quota/Rate Limit Errors:**
- `rate_limit_exceeded`
- `tokens per min (TPM)`
- `Limit X, Requested Y`
- `429 Too Many Requests`
- `Quota exceeded`
- `RESOURCE_EXHAUSTED`

**NOT Quota Errors:**
- `top_k parameter` → Cursor bug
- `ERROR_BAD_USER_API_KEY` → Expired auth
- `organization must be verified` → Security requirement
- `Invalid JSON payload` → Parameter mismatch

---

## 📋 ALTERNATIVE: Use GPT Codex Only

If you want to avoid these issues temporarily:

1. **Disable Gemini in Cursor:**
   - Settings → Disable Gemini features
   - Or just don't use Gemini

2. **Use GPT Codex:**
   - This is working for you
   - No verification needed
   - No parameter issues

3. **Use Gemini via Python scripts:**
   - Direct API calls work fine
   - No Cursor integration issues

---

**Summary:** 
- OpenAI: Verify organization (5 min wait)
- Gemini: Remove project setting OR use extension only
- Both should work after these fixes

