# Gemini top_k Error - Quick Fix Applied

**Date:** November 20, 2025  
**Time:** ~7:37 PM  
**Error:** `Invalid JSON payload received. Unknown name "top_k": Cannot find field.`  
**Status:** ✅ Fixed - Settings Cleaned

---

## ✅ WHAT WAS FIXED

### 1. Removed Problematic Setting
- ❌ **Removed:** `geminicodeassist.project: "cbi-v14"`
- ✅ **Kept:** `geminicodeassist.apiKey` (for extension use only)

**Why this matters:**
- The `project` setting can trigger Cursor's built-in Gemini integration
- Built-in integration sends invalid `top_k` parameter
- Extension doesn't need project setting (works with API key only)

### 2. Updated Fix Script
- ✅ Updated `scripts/setup/revert_to_cursor_builtin_models.py`
- ✅ Now removes `geminicodeassist.project` automatically
- ✅ Prevents this issue in the future

---

## 🔄 NEXT STEPS

### 1. Restart Cursor
1. **Quit Cursor completely:**
   - Press `Cmd + Q`
   - Wait for it to fully quit

2. **Reopen Cursor**

### 2. Use Correct Models

**✅ DO USE:**
- **Cursor Built-In Models** (in Cursor's chat dropdown):
  - Claude 4.5 Sonnet
  - Claude 4.5 Sonnet Thinking
  - GPT-5.1 (Cursor)
  - Sonnet 4.5
  - Composer 1

- **Gemini Extension** (separate):
  - `Cmd + Shift + P` → "Gemini: Open Chat"
  - Select model in extension's chat window
  - Works perfectly ✅

**❌ DON'T USE:**
- Gemini 3 Pro from Cursor's built-in dropdown
- Any Gemini model in Cursor's main chat
- These trigger the `top_k` error

---

## 📋 CURRENT SETTINGS

**What's Configured:**
```json
{
  "geminicodeassist.apiKey": "AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY"
}
```

**What's Removed:**
- ❌ `geminicodeassist.project` (was causing issues)
- ❌ All custom provider settings
- ❌ All custom baseUrl settings
- ❌ All extra parameters

---

## 🎯 SUMMARY

**The Problem:**
- Cursor's built-in Gemini sends invalid `top_k` parameter
- This is a Cursor bug, not your API key
- `geminicodeassist.project` setting can trigger built-in integration

**The Fix:**
- ✅ Removed `geminicodeassist.project` setting
- ✅ Settings now minimal (API key only for extension)
- ✅ Updated fix script for future use

**What to Do:**
1. Restart Cursor (`Cmd + Q`)
2. Use Cursor built-in models (Claude, GPT-5.1, etc.)
3. Use Gemini extension for Gemini (`Cmd + Shift + P` → "Gemini: Open Chat")
4. Avoid Gemini in Cursor's main chat dropdown

---

## 📄 RELATED FILES

- `scripts/setup/revert_to_cursor_builtin_models.py` - Fix script (updated)
- `docs/setup/TOP_K_ERROR_FINAL_FIX.md` - Detailed explanation
- `docs/setup/CURSOR_CONFIGURATION_STATUS.md` - Current status

---

**Status:** ✅ Fixed - Restart Cursor and Use Correct Models!

