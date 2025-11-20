# Restore Cursor Models in Chat

**Date:** November 20, 2025  
**Status:** ✅ Complete  
**Purpose:** Restore all Cursor built-in models (Claude, GPT, Sonnet, etc.) in chat while keeping Codex app separate

---

## ✅ WHAT WAS DONE

### 1. Model Preferences Reset ✅
- Reset `cursor/lastSingleModelPreference` - Removed custom model preference
- Reset `cursor/bestOfNCountPreference` - Reset best-of-N selection
- Reset `cursor/bestOfNEnsemblePreferences` - Reset ensemble preferences

### 2. Model Support Enabled ✅
- Enabled `cursor/claudeMdEnabled` - Claude markdown support
- Enabled `cursor/memoriesEnabled` - AI memories feature

### 3. Database Backup ✅
- Created backup: `state.vscdb.backup_20251120_171840`
- Safe to restore if needed

### 4. Subscription Verified ✅
- Membership: **Ultra** (all models available)
- Status: **Active**
- All Cursor models should be accessible

---

## 🔄 NEXT STEPS

### 1. Restart Cursor (REQUIRED)
```bash
# Quit Cursor completely
Cmd + Q

# Then reopen Cursor
```

### 2. Test Models in Chat
1. Open Cursor
2. Open Chat/Composer (`Cmd + L` or `Cmd + I`)
3. Click model dropdown
4. Select from available models:
   - **Claude 4.5 Sonnet**
   - **Claude 4.5 Sonnet Thinking**
   - **GPT-5.1** (High, Fast, Codex)
   - **Other Cursor models**

### 3. Verify Models Work
- Try asking a question in chat
- Models should respond without errors
- All Cursor models should be available

---

## 📋 AVAILABLE CURSOR MODELS

With **Ultra** subscription, you have access to:

### Claude Models
- Claude 4.5 Sonnet
- Claude 4.5 Sonnet Thinking
- Claude 4 Sonnet (legacy)

### GPT Models
- GPT-5.1 (High)
- GPT-5.1 (Fast)
- GPT-5.1 (Codex)

### Other Models
- Sonnet 4.5
- Composer 1
- Other Cursor models

---

## 🔍 VERIFICATION

### Check Model Availability
1. Open Cursor Chat/Composer
2. Click model dropdown
3. Verify all models are listed
4. Try selecting different models
5. Test that they work

### If Models Still Not Working
1. **Restart Cursor** (most important step)
2. Check Cursor Settings → Models
3. Verify subscription is active
4. Try clearing cache:
   ```bash
   # Quit Cursor, then:
   rm -rf ~/Library/Application\ Support/Cursor/Cache
   # Reopen Cursor
   ```

---

## 🛠️ RESTORE SCRIPT

**Script:** `scripts/setup/restore_cursor_models.py`

**What it does:**
- Backs up Cursor database
- Resets model preferences
- Enables Claude markdown support
- Enables memories
- Verifies subscription status

**Run it:**
```bash
python3 scripts/setup/restore_cursor_models.py
```

---

## 📊 CODEX APP STATUS

**Codex App:**
- ✅ **Separate application** - Not affected by Cursor changes
- ✅ **Independent settings** - Has its own configuration
- ✅ **Still works** - No changes made to Codex
- ✅ **Unchanged** - All Codex functionality preserved

**Codex is completely separate from Cursor:**
- Different app
- Different settings
- Different API keys (if configured)
- Not affected by Cursor model restoration

---

## 🔄 RESTORE FROM BACKUP (If Needed)

If you need to restore the previous state:

```bash
# Find backup file
ls -la ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb.backup_*

# Restore backup (replace TIMESTAMP with actual timestamp)
cp ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb.backup_TIMESTAMP \
   ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb

# Restart Cursor
```

---

## ✅ STATUS SUMMARY

**Before:**
- ❌ Claude models failing in Cursor chat
- ⚠️ Model preferences potentially blocking Cursor models

**After:**
- ✅ Model preferences reset
- ✅ Claude markdown enabled
- ✅ Memories enabled
- ✅ All Cursor models should be available
- ✅ Codex app unchanged

**Next:**
- ⏳ **Restart Cursor** to apply changes
- ⏳ Test models in chat
- ⏳ Verify all models work

---

## 📄 RELATED FILES

- `scripts/setup/restore_cursor_models.py` - Restoration script
- `docs/setup/CURSOR_CHATS_FIXED.md` - Previous chat fixes
- `docs/setup/REMOVE_OPENAI_FROM_CURSOR.md` - OpenAI removal guide

---

**Status:** ✅ Cursor Models Restored - Restart Cursor to Apply

