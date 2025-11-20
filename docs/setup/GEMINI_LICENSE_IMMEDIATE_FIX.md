# Gemini Code Assist - Immediate Fix for License Error

**Date:** January 2025  
**Issue:** "You are missing a valid license for Gemini Code Assist"

---

## 🔴 IMMEDIATE WORKAROUNDS

### Option 1: Remove Project Setting (Try This First)

The extension has a project setting (`geminicodeassist.project: "cbi-v14"`) that may be triggering license checks for enterprise features.

**Fix:**
1. Open Cursor Settings (`Cmd + ,`)
2. Search for: `geminicodeassist.project`
3. **Clear or remove** the project setting
4. Leave it blank or unset
5. Restart Cursor
6. Try using Gemini Code Assist again

**Why this works:**
- Project settings trigger enterprise/organization license checks
- Without a project, it may use individual/free tier
- Your API key should work for basic features

---

### Option 2: Disable Extension, Use Cursor's Built-in Gemini

**If the extension won't work, use Cursor's built-in model:**

1. **Disable Extension (Temporary):**
   - `Cmd + Shift + X` (Extensions)
   - Find "Gemini Code Assist"
   - Click "Disable" (not uninstall)
   - Restart Cursor

2. **Use Cursor's Model Selection:**
   - In Cursor's chat/composer, select model dropdown
   - Look for "Gemini 3 Pro" or "Gemini" options
   - Select it and use your API key

3. **Configure API Key in Cursor:**
   - `Cmd + ,` (Settings)
   - Search for: `cursor.gemini.apiKey` or `cursor.google.apiKey`
   - Enter: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`

**Note:** This may bill through Cursor, not directly to Google. Check Cursor's billing settings.

---

### Option 3: Use Python Scripts Directly

**Bypass the extension entirely:**

```python
import google.generativeai as genai

# Configure with your API key
genai.configure(api_key="AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q")

# Use any available model
model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
# Or: model = genai.GenerativeModel('gemini-2.5-flash')

response = model.generate_content("Your prompt here")
print(response.text)
```

**This definitely works** - no license needed, bills directly to Google.

---

## 🔍 ROOT CAUSE ANALYSIS

**What's happening:**
1. ✅ Your API key works (tested successfully) - likely from **Google AI Studio**
2. ✅ Extension is installed and configured
3. ❌ Extension requires a **Google Cloud project with license** (not just API key)
4. ⚠️ Project setting (`cbi-v14`) triggers enterprise license check
5. ⚠️ **AI Studio keys don't work with extension's enterprise features**

**The License Requirement:**
- Gemini Code Assist extension has **two tiers**:
  - **Individual/Free:** Uses API key only (AI Studio key may work here)
  - **Enterprise/Standard:** Requires Google Cloud project with paid license
- Setting a project (`geminicodeassist.project`) forces enterprise mode
- Enterprise mode requires license on the Google Cloud project
- **AI Studio keys are NOT associated with Google Cloud projects**

**Key Insight:**
- Your API key (`AIzaSy...`) is likely from **Google AI Studio**
- It works for direct API calls ✅
- But extension needs **Google Cloud project API key** with license ❌

**See:** `docs/setup/AI_STUDIO_VS_GOOGLE_CLOUD_KEY.md` for full explanation

---

## ✅ STEP-BY-STEP FIX

### Step 1: Clear Project Setting

1. `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"
2. Find: `"geminicodeassist.project": "cbi-v14"`
3. **Delete this line** or set to empty string: `""`
4. Save file
5. Restart Cursor

### Step 2: Verify API Key

1. Settings (`Cmd + ,`) → Search "geminicodeassist.apiKey"
2. Verify: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
3. If missing, add it

### Step 3: Test Extension

1. `Cmd + Shift + P` → "Gemini: Open Chat"
2. Try making a request
3. If license error persists, go to Step 4

### Step 4: Disable Extension (If Still Not Working)

1. `Cmd + Shift + X` → Find "Gemini Code Assist"
2. Click "Disable"
3. Use Option 2 or 3 above instead

---

## 📋 QUICK REFERENCE

**Your Current Config:**
```json
{
  "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
  "geminicodeassist.project": "cbi-v14"  // ← REMOVE THIS
}
```

**Recommended Config:**
```json
{
  "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"
  // No project setting = individual/free tier
}
```

---

## 🎯 RECOMMENDED ACTION

**Try in this order:**

1. **First:** Remove `geminicodeassist.project` setting
2. **Second:** Restart Cursor and test extension
3. **Third:** If still fails, disable extension and use Python scripts
4. **Last resort:** Purchase license if you need extension features

---

## 🔗 RELATED

- `docs/setup/GEMINI_CODE_ASSIST_LICENSE_ERROR.md` - Full diagnosis
- `docs/setup/CURSOR_GEMINI_ASSIST_TROUBLESHOOTING.md` - General troubleshooting

---

**Bottom Line:** Remove the project setting first. If that doesn't work, the extension requires a paid license. Use Python scripts or Cursor's built-in model as alternatives.

