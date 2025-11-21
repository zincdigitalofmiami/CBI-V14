# ⚠️ CRITICAL: DO NOT USE GEMINI FROM CURSOR'S DROPDOWN

**Date:** November 20, 2025  
**Status:** 🔴 ACTIVE ISSUE - Cursor Bug  
**Error:** `Invalid JSON payload received. Unknown name "top_k": Cannot find field.`

---

## 🚨 THE PROBLEM

**Cursor's built-in Gemini integration is broken.**

When you select **"Gemini 3"** or any Gemini model from **Cursor's main chat dropdown**, Cursor sends an invalid `top_k` parameter that Gemini API doesn't accept.

**This will ALWAYS fail with the `top_k` error.**

---

## ✅ THE SOLUTION

### ❌ DO NOT DO THIS:
- ❌ **DO NOT** select "Gemini 3" from Cursor's chat dropdown
- ❌ **DO NOT** select "Gemini" from Cursor's model list
- ❌ **DO NOT** use any Gemini model in Cursor's main chat

### ✅ DO THIS INSTEAD:

**Use the Gemini Code Assist Extension:**

1. **Press:** `Cmd + Shift + P`
2. **Type:** `Gemini: Open Chat`
3. **Press:** Enter
4. **Select model** in the extension's chat window
5. **Works perfectly** ✅

---

## 📋 WHAT TO USE IN CURSOR'S MAIN CHAT

**Use Cursor's built-in models (these work fine):**

- ✅ **Claude 4.5 Sonnet** (recommended)
- ✅ **Claude 4.5 Sonnet Thinking**
- ✅ **GPT-5.1** (Cursor version)
- ✅ **Sonnet 4.5**
- ✅ **Composer 1**

**These are included with your Ultra subscription and work perfectly.**

---

## 🔍 WHY THIS HAPPENS

**Cursor's built-in Gemini integration:**
- Uses a generic parameter template
- Sends `top_k` (an OpenAI parameter) to Gemini
- Gemini API doesn't recognize `top_k`
- This is a **Cursor bug** that needs to be fixed by Cursor team

**Gemini Code Assist Extension:**
- Built specifically for Gemini API
- Handles parameters correctly
- No compatibility issues
- Works perfectly ✅

---

## 🎯 QUICK REFERENCE

| What | Where | Status |
|------|-------|--------|
| Gemini 3 | Cursor's dropdown | ❌ **BROKEN** - Don't use |
| Gemini 3 | Extension (`Cmd+Shift+P` → "Gemini: Open Chat") | ✅ **WORKS** - Use this |
| Claude 4.5 Sonnet | Cursor's dropdown | ✅ **WORKS** - Use this |
| GPT-5.1 | Cursor's dropdown | ✅ **WORKS** - Use this |

---

## 📝 REMEMBER

**If you see the `top_k` error:**
1. You selected Gemini from Cursor's dropdown ❌
2. **Solution:** Use the extension instead ✅
3. **Or:** Use Claude/GPT-5.1 in Cursor's main chat ✅

---

**Status:** 🔴 Cursor Bug - Use Extension for Gemini, Use Built-In Models for Everything Else

