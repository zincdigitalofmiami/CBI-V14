# Remove OpenAI from Cursor - Use Cursor Models Instead

**Date:** November 20, 2025  
**Status:** ✅ Complete  
**Purpose:** Remove OpenAI API key, use Cursor's built-in models

---

## 🎯 WHAT THIS DOES

**Removes:**
- ❌ OpenAI API key from Cursor database
- ❌ OpenAI connections in Cursor

**Keeps:**
- ✅ Codex app (separate, still works)
- ✅ Cursor's built-in models (GPT-5.1, Sonnet 4.5, Composer 1, etc.)

**Result:**
- Use Cursor's models instead of OpenAI API
- No OpenAI API key needed in Cursor
- Codex app continues to work independently

---

## 🔧 HOW TO REMOVE

### Method 1: Use Script (RECOMMENDED)

```bash
python3 scripts/setup/remove_openai_from_cursor.py
```

**What it does:**
- Backs up Cursor database
- Removes `cursorAuth/openAIKey` from database
- Keeps other settings intact
- Safe and reversible

### Method 2: Manual Removal

1. **Quit Cursor:**
   - `Cmd + Q` → Quit completely

2. **Backup database:**
   ```bash
   cp ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
      ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb.backup
   ```

3. **Remove OpenAI key:**
   ```bash
   sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
     "DELETE FROM ItemTable WHERE key = 'cursorAuth/openAIKey';"
   ```

4. **Reopen Cursor**

---

## ✅ VERIFICATION

**After removal:**

1. **Check database:**
   ```bash
   sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
     "SELECT key FROM ItemTable WHERE key = 'cursorAuth/openAIKey';"
   ```
   Should return nothing (key removed)

2. **Test Cursor models:**
   - Open Cursor
   - Try using chat/composer
   - Select models from Cursor's dropdown
   - Should work with Cursor's built-in models

3. **Verify Codex still works:**
   - Codex is a separate app
   - Should continue working independently
   - Not affected by Cursor changes

---

## 📋 USING CURSOR MODELS

**After removing OpenAI:**

1. **Available Models:**
   - GPT-5.1 (High, Fast, Codex)
   - Sonnet 4.5
   - Composer 1
   - Other Cursor models

2. **How to Use:**
   - Select model from Cursor's dropdown
   - Use chat/composer features
   - Models are built into Cursor
   - No API key needed

3. **Benefits:**
   - No API key management
   - No rate limits (Cursor handles it)
   - Integrated with Cursor features
   - Works out of the box

---

## 🔄 RESTORE IF NEEDED

**If you want OpenAI back:**

1. **Restore from backup:**
   ```bash
   cp ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb.backup.* \
      ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb
   ```

2. **Or re-add key:**
   - Go to Cursor Settings
   - Add OpenAI API key again
   - Or use: `scripts/setup/fix_cursor_apis.py`

---

## 📊 WHAT'S DIFFERENT

### Before (With OpenAI Key):
- Cursor uses your OpenAI API key
- Billing goes to your OpenAI account
- Subject to OpenAI rate limits
- Can use OpenAI models directly

### After (Cursor Models Only):
- Cursor uses its built-in models
- Billing handled by Cursor (if applicable)
- Cursor manages rate limits
- Use Cursor's model selection

### Codex App:
- **Unchanged** - Separate app
- Still uses your OpenAI key (if configured)
- Works independently
- Not affected by Cursor changes

---

## 🎯 SUMMARY

**What Changed:**
- ✅ OpenAI API key removed from Cursor
- ✅ Cursor uses built-in models
- ✅ Codex app still works

**Next Steps:**
1. Restart Cursor (`Cmd + Q`)
2. Use Cursor's model dropdown
3. Select Cursor models (GPT-5.1, Sonnet, etc.)
4. Codex continues working separately

**Benefits:**
- Simpler setup (no OpenAI key in Cursor)
- Use Cursor's integrated models
- Codex still available separately

---

## 📄 RELATED FILES

- `scripts/setup/remove_openai_from_cursor.py` - Removal script
- `docs/setup/CURSOR_CHATS_FIXED.md` - Previous OpenAI setup
- `docs/setup/ALL_CURSOR_PROBLEMS_COMPREHENSIVE.md` - All problems

---

**Status:** ✅ OpenAI Removed - Using Cursor Models

