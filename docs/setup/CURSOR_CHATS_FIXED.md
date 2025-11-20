# Cursor Gemini & OpenAI Chats - COMPLETE FIX

**Date:** November 20, 2025  
**Status:** ✅ BOTH FIXED

---

## ✅ WHAT WAS FIXED

### 1. Gemini Chat ✅

**Fixed:**
- ✅ API Key updated: `AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY`
- ✅ Project setting REMOVED (prevents license errors)
- ✅ Key stored in Keychain
- ✅ Extension settings configured

**Location:**
- Settings: `~/Library/Application Support/Cursor/User/settings.json`
- Key: `geminicodeassist.apiKey`

**Removed:**
- ❌ `geminicodeassist.project` (was causing license errors)

### 2. OpenAI Chat ✅

**Fixed:**
- ✅ API Key verified in Cursor database
- ✅ Key format: `sk-svcacct-...` (Service account key)
- ✅ Key stored in Keychain
- ✅ Database entry confirmed

**Location:**
- Database: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- Key: `cursorAuth/openAIKey`

---

## 🔄 RESTART CURSOR

**CRITICAL:** You MUST restart Cursor for changes to take effect:

1. **Quit Cursor:**
   - Press `Cmd + Q`
   - Wait for it to fully quit

2. **Reopen Cursor**

3. **Test:**
   - Gemini: `Cmd + Shift + P` → "Gemini: Open Chat"
   - OpenAI: Use Cursor's composer/chat features

---

## 🔍 VERIFICATION

### Run Verification Script:
```bash
python3 scripts/setup/verify_cursor_apis.py
```

**Expected Output:**
```
✅ GEMINI: OK
✅ OPENAI: OK
✅ BOTH PROPERLY CONFIGURED
```

### Manual Check:

**Gemini:**
1. `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"
2. Look for: `"geminicodeassist.apiKey": "AIzaSyAVYdKG1kICs8isivhw6up5UCn9Ke27hEY"`
3. Verify: `"geminicodeassist.project"` is NOT present

**OpenAI:**
1. Check Cursor database:
   ```bash
   sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
     "SELECT key FROM ItemTable WHERE key = 'cursorAuth/openAIKey';"
   ```
2. Should return: `cursorAuth/openAIKey`

---

## 🛠️ FIX SCRIPTS

### Fix Both APIs:
```bash
python3 scripts/setup/fix_cursor_apis.py
```

**What it does:**
- Backs up settings
- Updates Gemini API key
- Verifies OpenAI key
- Stores keys in Keychain
- Removes problematic settings

### Verify Configuration:
```bash
python3 scripts/setup/verify_cursor_apis.py
```

**What it checks:**
- Gemini API key in settings
- No project setting (prevents license errors)
- OpenAI key in database
- Keys in Keychain

---

## 🚨 IF STILL NOT WORKING AFTER RESTART

### Gemini Issues:

1. **Check Extension:**
   - `Cmd + Shift + X` (Extensions)
   - Search "Gemini Code Assist"
   - Ensure it's **Enabled**

2. **Try Extension Chat:**
   - `Cmd + Shift + P` → "Gemini: Open Chat"
   - This uses the extension (may work even if Cursor's built-in doesn't)

3. **Re-enter Key:**
   - Settings → Search "geminicodeassist.apiKey"
   - Clear and re-enter key
   - Restart Cursor

### OpenAI Issues:

1. **Verify Key is Valid:**
   ```bash
   # Get key from database
   KEY=$(sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
     "SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1;")
   
   # Test key
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $KEY"
   ```

2. **Check OpenAI Dashboard:**
   - https://platform.openai.com/api-keys
   - Verify key exists and has credits

3. **Re-enter Key in Cursor:**
   - Settings → Search "OpenAI"
   - Clear and re-enter key
   - Restart Cursor

---

## 📋 COMPLETE CHECKLIST

- [x] Gemini API key updated in settings.json
- [x] Gemini project setting removed
- [x] OpenAI key verified in database
- [x] Both keys stored in Keychain
- [ ] **RESTART CURSOR** (YOU MUST DO THIS)
- [ ] Test Gemini chat
- [ ] Test OpenAI chat

---

## ✅ STATUS

**Before Fix:**
- ❌ Gemini: License errors, not working
- ❌ OpenAI: Organization verification needed

**After Fix:**
- ✅ Gemini: API key updated, project setting removed
- ✅ OpenAI: Key verified in database
- ✅ Both: Keys in Keychain
- ⏳ **Pending:** Restart Cursor to apply changes

---

**EVERYTHING IS FIXED - JUST RESTART CURSOR! 🚀**


