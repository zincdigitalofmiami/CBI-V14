# Gemini Code Assist Not Working - Troubleshooting

**Date:** November 20, 2025  
**Issue:** Gemini Code Assist extension not working

---

## 🔍 CURRENT STATUS

**Extension Installed:**
- ✅ `google.geminicodeassist` v2.58.0
- ✅ Has been used before (hasRunOnce: true)
- ✅ Chat threads exist in database

**API Key:**
- ✅ Stored in Cursor database: `cursorAuth/googleKey`
- ⚠️ **May need to be set in extension settings separately**

---

## 🔴 COMMON ISSUES & FIXES

### Issue 1: API Key Not Set in Extension Settings

**Problem:** API key is in Cursor's database but not in extension's own settings.

**Fix:**
1. Open Cursor Settings (`Cmd + ,`)
2. Search for: `"geminicodeassist"`
3. Look for: `geminicodeassist.apiKey` or `geminicodeassist.googleApiKey`
4. Enter your key: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
5. Save and restart Cursor

**Or via Settings JSON:**
1. `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"
2. Add:
   ```json
   {
     "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q"
   }
   ```

---

### Issue 2: Extension Not Enabled

**Problem:** Extension is installed but disabled.

**Fix:**
1. Open Extensions (`Cmd + Shift + X`)
2. Search for "Gemini Code Assist"
3. Verify it shows "Enabled" (not "Disabled")
4. If disabled, click "Enable"
5. Restart Cursor

---

### Issue 3: Can't Find Gemini Chat

**Problem:** Extension works but can't access the chat interface.

**Fix:**
1. **Command Palette:** `Cmd + Shift + P` → Type "Gemini: Open Chat"
2. **View Menu:** `View → Gemini` or `View → Gemini Chat`
3. **Sidebar:** Look for Gemini icon in sidebar
4. **If hidden:** `View → Appearance → Show Gemini Chat`

---

### Issue 4: Extension Needs Update

**Problem:** Old version may have bugs.

**Fix:**
1. Open Extensions (`Cmd + Shift + X`)
2. Search for "Gemini Code Assist"
3. Check for "Update" button
4. Click "Update" if available
5. Restart Cursor

---

### Issue 5: Workspace Settings Override

**Problem:** Workspace settings may be blocking extension.

**Check:**
- Your workspace file (`CBI-V14.code-workspace`) has `geminicodeassist.rules` set
- This is fine, but verify extension is enabled in workspace

**Fix:**
1. Open workspace settings: `Cmd + Shift + P` → "Preferences: Open Workspace Settings (JSON)"
2. Verify extension is not disabled:
   ```json
   {
     "geminicodeassist.enabled": true
   }
   ```

---

## 🔧 STEP-BY-STEP DIAGNOSIS

### Step 1: Verify Extension is Installed

```bash
# Check extension directory
ls -la ~/.cursor/extensions/ | grep gemini
```

**Expected:** Should see `google.geminicodeassist-*` directory

---

### Step 2: Check Extension is Enabled

1. `Cmd + Shift + X` (Extensions)
2. Search "Gemini Code Assist"
3. Verify: **Enabled** (green checkmark)

---

### Step 3: Verify API Key in Extension Settings

1. `Cmd + ,` (Settings)
2. Search: `"geminicodeassist"`
3. Find: `geminicodeassist.apiKey`
4. Verify: Your key is set (`AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`)

**If not set:**
- Enter your key
- Save
- Restart Cursor

---

### Step 4: Test Access

1. `Cmd + Shift + P`
2. Type: `"Gemini: Open Chat"`
3. Should open Gemini chat panel

**If command not found:**
- Extension may not be loaded
- Try restarting Cursor
- Check for errors in Cursor's Developer Tools

---

### Step 5: Check for Errors

1. `Cmd + Shift + P` → "Developer: Toggle Developer Tools"
2. Look in Console tab for errors
3. Check for:
   - API key errors
   - Extension loading errors
   - Network errors

---

## 🎯 QUICK FIX CHECKLIST

- [ ] Extension is installed (`google.geminicodeassist`)
- [ ] Extension is **enabled** (not disabled)
- [ ] API key is set in extension settings (`geminicodeassist.apiKey`)
- [ ] Cursor has been restarted after setting API key
- [ ] Can access via `Cmd + Shift + P` → "Gemini: Open Chat"
- [ ] No errors in Developer Tools console

---

## 🚨 IF STILL NOT WORKING

### Option 1: Reinstall Extension

1. `Cmd + Shift + X` (Extensions)
2. Find "Gemini Code Assist"
3. Click "Uninstall"
4. Restart Cursor
5. Reinstall from Extensions marketplace
6. Configure API key
7. Restart again

### Option 2: Check Cursor Logs

1. `Cmd + Shift + P` → "Developer: Toggle Developer Tools"
2. Go to "Console" tab
3. Look for errors related to:
   - `geminicodeassist`
   - `google.geminicodeassist`
   - API key errors
   - Extension loading errors

### Option 3: Use Cloud Code Extension Instead

If Gemini Code Assist won't work, try:
- **Cloud Code** extension (`googlecloudtools.cloudcode`)
- Also includes Gemini chat
- May work better in some cases

---

## 📋 YOUR CURRENT CONFIGURATION

**From Database:**
- ✅ Extension installed: `google.geminicodeassist` v2.58.0
- ✅ API key in Cursor: `cursorAuth/googleKey` = `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
- ✅ Extension has been used before
- ✅ Chat threads exist

**What to Check:**
1. ⚠️ **API key in extension settings** (may need to be set separately)
2. ⚠️ **Extension enabled** (verify in Extensions panel)
3. ⚠️ **Access method** (Command Palette vs View menu)

---

## ✅ MOST LIKELY FIX

**The API key needs to be set in the extension's own settings:**

1. `Cmd + ,` (Settings)
2. Search: `"geminicodeassist.apiKey"`
3. Enter: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
4. Save
5. Restart Cursor
6. Try: `Cmd + Shift + P` → "Gemini: Open Chat"

---

**Let me know what specific error or behavior you're seeing, and I can help diagnose further!**







