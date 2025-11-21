# Restore AI Agents - Quick Fix Guide

**Date:** January 2025  
**Issue:** OpenAI key, Gemini Code Assist, and Gemini chat not working after uninstall

---

## 🔍 CURRENT STATUS

**Extensions Still Installed:**
- ✅ `google.geminicodeassist-2.58.0-universal` - Still there
- ✅ `openai.chatgpt-0.5.45-universal` - Still there

**Settings Still Configured:**
- ✅ Gemini API key: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
- ✅ Gemini project: `cbi-v14`

**What Needs Fixing:**
- ⚠️ Extensions may be disabled
- ⚠️ Keys may need to be re-entered in Cursor UI
- ⚠️ Extensions may need to be re-enabled

---

## ✅ QUICK RESTORATION STEPS

### Step 1: Re-enable Extensions

1. **Open Cursor**
2. **Press `Cmd + Shift + X`** (Extensions panel)
3. **Search for each extension:**
   - "Gemini Code Assist" → Click **Enable** if disabled
   - "ChatGPT" or "OpenAI" → Click **Enable** if disabled
4. **Restart Cursor** (`Cmd + Q`, then reopen)

---

### Step 2: Re-enter API Keys in Cursor Settings

#### For OpenAI/GPT:

1. **Open Cursor Settings:**
   - `Cmd + ,` (or Cursor → Settings)

2. **Search for:** `"OpenAI"` or `"API Key"`

3. **Find OpenAI API Key setting:**
   - Look for: `cursor.openAI.apiKey` or similar
   - If empty, you'll need to re-enter your key

4. **Get your OpenAI key:**
   - Go to: https://platform.openai.com/api-keys
   - Copy your key (starts with `sk-`)

5. **Enter key in Cursor:**
   - Paste the key
   - Save settings

#### For Gemini:

1. **Open Cursor Settings:**
   - `Cmd + ,`

2. **Search for:** `"geminicodeassist"` or `"Gemini"`

3. **Verify API Key:**
   - Should show: `geminicodeassist.apiKey`
   - Value should be: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
   - If empty, re-enter it

4. **Remove Project Setting (if causing issues):**
   - Find: `geminicodeassist.project`
   - Delete it or set to empty: `""`
   - This avoids license errors

---

### Step 3: Restart Cursor

1. **Quit Cursor completely:**
   - `Cmd + Q`

2. **Reopen Cursor**

3. **Test:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - Try using GPT features

---

## 🔧 ALTERNATIVE: Use Settings JSON

If UI doesn't work, edit settings directly:

1. **`Cmd + Shift + P`** → "Preferences: Open User Settings (JSON)"

2. **Add/Verify these settings:**

```json
{
  "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
  "geminicodeassist.enabled": true,
  "cursor.openAI.apiKey": "YOUR_OPENAI_KEY_HERE"
}
```

3. **Save and restart Cursor**

---

## 🎯 VERIFICATION

### Check Extensions Are Enabled:

1. `Cmd + Shift + X` (Extensions)
2. Search "Gemini Code Assist"
3. Should show: **Enabled** (green checkmark)
4. Search "ChatGPT" or "OpenAI"
5. Should show: **Enabled**

### Check API Keys:

1. `Cmd + ,` (Settings)
2. Search "geminicodeassist.apiKey"
3. Should show your key (masked)
4. Search "openAI" or "cursor.openAI"
5. Should show your OpenAI key (masked)

### Test Functionality:

1. **Gemini:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - Should open Gemini chat panel

2. **GPT:**
   - Use Cursor's composer/chat
   - Select GPT model from dropdown
   - Should work

---

## 🚨 IF STILL NOT WORKING

### For OpenAI:

1. **Check key is valid:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY"
   ```

2. **Check OpenAI dashboard:**
   - https://platform.openai.com/api-keys
   - Verify key exists and has credits

3. **Re-enter key:**
   - Clear old key
   - Paste new key
   - Save and restart

### For Gemini:

1. **Remove project setting:**
   - Delete `geminicodeassist.project` from settings
   - This avoids license errors

2. **Reinstall extension:**
   - `Cmd + Shift + X` → Find "Gemini Code Assist"
   - Uninstall
   - Restart Cursor
   - Reinstall from marketplace
   - Re-enter API key

3. **Use direct API instead:**
   - Python scripts work without extension
   - No license needed

---

## 📋 QUICK CHECKLIST

- [ ] Extensions enabled in Extensions panel
- [ ] OpenAI API key entered in Cursor Settings
- [ ] Gemini API key verified in Cursor Settings
- [ ] Project setting removed (if causing license errors)
- [ ] Cursor restarted
- [ ] Tested Gemini chat
- [ ] Tested GPT features

---

**Most likely fix:** Re-enable extensions and restart Cursor. The keys are still in your settings, they just need the extensions to be active.



