# How to Use Gemini 3 Pro in Cursor

**Date:** November 20, 2025  
**Goal:** Configure Gemini 3 Pro as your AI model in Cursor

---

## ✅ GEMINI 3 PRO IS AVAILABLE

As of November 2025, **Gemini 3 Pro is available in Cursor**. Here's how to set it up:

---

## 🎯 METHOD 1: Cursor Settings UI (Recommended)

### Step 1: Open Cursor Settings
1. Press `Cmd + ,` (or Cursor → Settings)
2. Or: `Cursor → Preferences → Settings`

### Step 2: Navigate to Models
1. In Settings, look for:
   - **"Models"** tab/section
   - **"Language Models"** section
   - **"AI Models"** or **"Model Provider"** section
2. Search for: `"model"` or `"gemini"` or `"provider"`

### Step 3: Select Gemini 3 Pro
1. Look for **"Gemini 3 Pro"** in the list of available models
2. **Enable** it by:
   - Toggling it on
   - Selecting it as your preferred model
   - Or setting it as default

### Step 4: Verify API Key
- Your Google API key is already configured: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
- If needed, verify it's set in:
  - Settings → API Keys → Google/Gemini

### Step 5: Restart Cursor
- Quit Cursor completely (`Cmd + Q`)
- Reopen Cursor
- Gemini 3 Pro should now be available

---

## 🔧 METHOD 2: Command Palette

### Access Model Selection
1. Press `Cmd + Shift + P`
2. Type: `"Cursor: Select Model"` or `"Change Model"`
3. Look for **"Gemini 3 Pro"** in the list
4. Select it

### Or: Open Composer with Gemini 3 Pro
1. Press `Cmd + Shift + P`
2. Type: `"Cursor: Open Composer"`
3. In the composer, check the model dropdown
4. Select **"Gemini 3 Pro"**

---

## 🛠️ METHOD 3: Settings JSON (Advanced)

If you can't find it in the UI, you can try setting it directly:

1. Press `Cmd + Shift + P`
2. Type: `"Preferences: Open User Settings (JSON)"`
3. Add or modify:
   ```json
   {
     "cursor.languageModel.provider": "gemini",
     "cursor.languageModel.model": "gemini-3-pro",
     "cursor.gemini.model": "gemini-3-pro",
     "cursor.gemini.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"
   }
   ```

**Note:** The exact setting names may vary. Check Cursor's documentation or settings UI for the correct keys.

---

## 📋 METHOD 4: MCP Server (If Native Support Not Available)

If Gemini 3 Pro isn't available as a native option, you can set up an MCP server:

### Option A: Google Gemini MCP Server

1. **Install MCP Server:**
   ```bash
   # Check if you have Node.js
   node --version
   
   # Install Google Gemini MCP server (if available)
   npm install -g @modelcontextprotocol/server-gemini
   ```

2. **Configure MCP in Cursor:**
   - Edit `~/.cursor/mcp.json`
   - Add:
   ```json
   {
     "mcpServers": {
       "gemini-3-pro": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-gemini"
         ],
         "env": {
           "GEMINI_API_KEY": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
           "GEMINI_MODEL": "gemini-3-pro"
         }
       }
     }
   }
   ```

3. **Restart Cursor**

### Option B: Custom Model Provider

If Cursor supports custom model providers:

1. **Check Cursor Settings:**
   - Settings → Custom Model Provider
   - Or: Settings → Language Models → Add Custom Provider

2. **Configure:**
   - **Provider Name:** Google Gemini
   - **API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro:generateContent`
   - **API Key:** `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
   - **Model Name:** `gemini-3-pro`

---

## 🔍 VERIFICATION

### Check if Gemini 3 Pro is Available

1. **In Composer:**
   - Open Composer (`Cmd + I` or `Cmd + Shift + I`)
   - Check the model dropdown
   - Look for "Gemini 3 Pro" or "gemini-3-pro"

2. **In Settings:**
   - Settings → Models
   - Should see "Gemini 3 Pro" listed

3. **Via Command Palette:**
   - `Cmd + Shift + P` → "Select Model"
   - Should see "Gemini 3 Pro" in the list

---

## 🎯 QUICK START CHECKLIST

- [ ] Open Cursor Settings (`Cmd + ,`)
- [ ] Navigate to Models/Language Models section
- [ ] Find "Gemini 3 Pro" in the list
- [ ] Enable/Select "Gemini 3 Pro"
- [ ] Verify API key is set (already configured: `AIzaSy...`)
- [ ] Restart Cursor
- [ ] Test in Composer - select "Gemini 3 Pro" from model dropdown

---

## 🛠️ TROUBLESHOOTING

### If Gemini 3 Pro Doesn't Appear:

1. **Check Cursor Version:**
   - Make sure you're on the latest version
   - Gemini 3 Pro support was added in recent versions
   - Check: `Cursor → About Cursor`

2. **Check API Key:**
   - Verify key is valid: https://console.cloud.google.com/apis/credentials
   - Make sure key has access to Gemini API
   - Enable Gemini API in Google Cloud Console if needed

3. **Check Model Availability:**
   - Gemini 3 Pro may be in preview/beta
   - May require specific Cursor subscription tier
   - Check Cursor release notes for Gemini 3 Pro support

4. **Try Alternative Names:**
   - `gemini-3-pro`
   - `gemini-pro-3`
   - `gemini-3.0-pro`
   - `models/gemini-3-pro`

5. **Contact Support:**
   - If still not working, check Cursor documentation
   - Or contact Cursor support about Gemini 3 Pro availability

---

## 📝 YOUR CURRENT CONFIGURATION

- **Google API Key:** ✅ Configured (`AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`)
- **Gemini Extension:** ✅ Installed (`google.geminicodeassist` v2.58.0)
- **MCP Servers:** ⚠️ None configured (may need to set up)

---

## 🎯 RECOMMENDED APPROACH

1. **First:** Try Method 1 (Settings UI) - easiest
2. **If not available:** Try Method 2 (Command Palette) - check model selection
3. **If still not working:** Try Method 3 (Settings JSON) - manual configuration
4. **Last resort:** Method 4 (MCP Server) - custom setup

---

**Next Step:** Open Cursor Settings and look for "Models" or "Language Models" section to find Gemini 3 Pro!

