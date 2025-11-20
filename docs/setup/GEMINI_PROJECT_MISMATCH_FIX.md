# Gemini Code Assist - Project Mismatch Fix

**Date:** January 2025  
**Issue:** API key from one project, extension configured for different project

---

## 🔍 THE PROBLEM

**Your API Key Details:**
- API Key: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
- **Project:** `projects/1065708057795` (Project number: 1065708057795)
- **Name:** CBI V14 Cursor

**Your Cursor Settings:**
- `geminicodeassist.project: "cbi-v14"` ← **Different project!**
- `geminicodeassist.apiKey: "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"` ✅

**The Issue:**
- API key is from project `1065708057795`
- Extension is configured for project `cbi-v14`
- **Mismatch causes license check to fail** ❌

---

## ✅ SOLUTIONS

### Solution 1: Update Project Setting to Match API Key (RECOMMENDED)

**Use the actual project number from your API key:**

1. **Open Cursor Settings:**
   - `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"

2. **Update project setting:**
   ```json
   {
     "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
     "geminicodeassist.project": "1065708057795"
   }
   ```

3. **Save and restart Cursor**

4. **Test extension:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - Try making a request

**Why this works:**
- Project setting now matches the API key's project
- License check will look at the correct project
- If project has license, it should work

---

### Solution 2: Remove Project Setting (Use Individual Tier)

**If project doesn't have license, remove project setting:**

1. **Open Cursor Settings:**
   - `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"

2. **Remove project setting:**
   ```json
   {
     "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"
     // Remove: "geminicodeassist.project": "cbi-v14"
   }
   ```

3. **Save and restart Cursor**

4. **Test extension:**
   - Should use individual/free tier
   - No project license required

---

### Solution 3: Assign License to Project

**If you need enterprise features:**

1. **Go to Google Cloud Console:**
   - https://console.cloud.google.com/gemini/code-assist/licenses?project=1065708057795

2. **Check License Status:**
   - See if project `1065708057795` has Gemini Code Assist license
   - If not, purchase/assign license

3. **Update Cursor Settings:**
   - Set `geminicodeassist.project: "1065708057795"`
   - Keep API key as is

4. **Restart Cursor and test**

---

## 🔍 HOW TO VERIFY PROJECT

### Check Your API Key's Project:

1. **Go to Google Cloud Console:**
   - https://console.cloud.google.com/apis/credentials?project=1065708057795

2. **Find your API key:**
   - Look for key starting with `AIzaSyBUEg8HK4z...`
   - Verify it's in project `1065708057795`

3. **Check Project Details:**
   - Project ID: `1065708057795`
   - Project Name: Should be "CBI V14 Cursor" or similar

### Check if Project Has License:

1. **Go to:**
   - https://console.cloud.google.com/gemini/code-assist/licenses?project=1065708057795

2. **Look for:**
   - Gemini Code Assist licenses
   - License assignments
   - Available licenses

---

## 📋 RECOMMENDED ACTION

**Step 1: Update Project Setting**
- Change `geminicodeassist.project` from `"cbi-v14"` to `"1065708057795"`
- This matches your API key's actual project

**Step 2: Check License**
- Go to Google Cloud Console
- Check if project `1065708057795` has Gemini Code Assist license

**Step 3: If No License**
- Either assign license to project
- Or remove project setting to use individual tier

---

## 🎯 QUICK FIX

**Update your settings JSON:**

```json
{
  "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
  "geminicodeassist.project": "1065708057795"
}
```

**Then:**
1. Save settings
2. Restart Cursor
3. Test: `Cmd + Shift + P` → "Gemini: Open Chat"

---

## 🔗 RELATED

- `docs/setup/AI_STUDIO_VS_GOOGLE_CLOUD_KEY.md` - Key type differences
- `docs/setup/GEMINI_LICENSE_IMMEDIATE_FIX.md` - General fixes
- `docs/setup/GEMINI_CODE_ASSIST_LICENSE_ERROR.md` - Full diagnosis

---

**Summary:** Your API key is from project `1065708057795`, but Cursor is configured for project `cbi-v14`. Update the project setting to match your API key's project, then check if that project has a license assigned.






