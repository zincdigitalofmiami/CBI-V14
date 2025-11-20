# AI Studio Key vs Google Cloud Project - License Issue Explained

**Date:** January 2025  
**Issue:** AI Studio API key works for direct API calls, but Gemini Code Assist extension requires Google Cloud project license

---

## 🔍 THE KEY DIFFERENCE

### Google AI Studio API Key
- ✅ **What it is:** API key from https://aistudio.google.com/
- ✅ **Works for:** Direct API calls (Python scripts, curl, etc.)
- ✅ **Billing:** Bills to your Google account
- ❌ **Does NOT work for:** Gemini Code Assist extension (requires project license)

### Google Cloud Project API Key
- ✅ **What it is:** API key from Google Cloud Console project
- ✅ **Works for:** Direct API calls AND Gemini Code Assist extension
- ✅ **Requires:** Google Cloud project with "Gemini for Google Cloud API" enabled
- ✅ **Requires:** Gemini Code Assist license assigned to project

---

## 🎯 YOUR CURRENT SITUATION

**Your API Key:** `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`

**This key:**
- ✅ Works for direct API calls (we tested this successfully)
- ✅ Is likely from Google AI Studio
- ❌ May not be associated with a Google Cloud project
- ❌ Extension requires a project with license

**Your Project Setting:**
- `geminicodeassist.project: "cbi-v14"`
- This triggers enterprise license check
- Project may not have Gemini Code Assist license assigned

---

## ✅ SOLUTIONS

### Solution 1: Remove Project Setting (Use Individual Tier)

**If you have an AI Studio key, use it without a project:**

1. **Remove project setting:**
   - `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"
   - Delete: `"geminicodeassist.project": "cbi-v14"`
   - Save and restart Cursor

2. **Keep API key:**
   - `"geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"`
   - This should work for individual/free tier features

3. **Test extension:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - Try making a request

**Why this works:**
- Individual tier doesn't require project license
- AI Studio key should work for basic features
- No enterprise license check

---

### Solution 2: Create Google Cloud Project with License

**If you need enterprise features:**

1. **Create/Use Google Cloud Project:**
   - Go to: https://console.cloud.google.com/
   - Create project or use existing: `cbi-v14`
   - Enable "Gemini for Google Cloud API"

2. **Get API Key from Project:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create API key for the project
   - Use this key instead of AI Studio key

3. **Assign License:**
   - Go to: https://console.cloud.google.com/gemini/code-assist/licenses
   - Purchase/assign Gemini Code Assist license to project
   - Assign license to your account

4. **Update Settings:**
   - Use new Google Cloud project API key
   - Keep project setting: `"geminicodeassist.project": "cbi-v14"`

---

### Solution 3: Use Direct API (No Extension)

**Bypass extension entirely - use AI Studio key directly:**

```python
import google.generativeai as genai

# Your AI Studio key works perfectly for this
genai.configure(api_key="AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q")

# Use any model
model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
response = model.generate_content("Your prompt")
print(response.text)
```

**This definitely works:**
- ✅ No license needed
- ✅ Uses your AI Studio key
- ✅ Bills to your Google account
- ✅ No extension required

---

## 🔍 HOW TO CHECK YOUR KEY TYPE

### Check if Key is from AI Studio:
1. Go to: https://aistudio.google.com/app/apikey
2. See if your key (`AIzaSy...`) is listed there
3. If yes → It's an AI Studio key

### Check if Key is from Google Cloud:
1. Go to: https://console.cloud.google.com/apis/credentials
2. See if your key is listed under a project
3. If yes → It's a Google Cloud project key

---

## 📋 RECOMMENDED ACTION

**For your situation (AI Studio key):**

1. **First:** Remove `geminicodeassist.project` setting
2. **Second:** Test if extension works with AI Studio key (individual tier)
3. **Third:** If still fails, use Python scripts with direct API
4. **Last resort:** Create Google Cloud project and get license

---

## 🎯 SUMMARY

**The Problem:**
- AI Studio keys work for direct API calls ✅
- Gemini Code Assist extension needs Google Cloud project with license ❌
- Project setting (`cbi-v14`) triggers enterprise license check ❌

**The Solution:**
- Remove project setting → Use individual tier with AI Studio key
- OR: Use direct API (Python scripts) - no license needed
- OR: Create Google Cloud project and assign license

**Your AI Studio key is fine** - it just doesn't work with the extension's enterprise features. Use it directly via Python or remove the project setting to try individual tier.

---

## 🔗 RELATED

- `docs/setup/GEMINI_LICENSE_IMMEDIATE_FIX.md` - Step-by-step fix
- `docs/setup/GEMINI_CODE_ASSIST_LICENSE_ERROR.md` - Full diagnosis






