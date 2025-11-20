# Cursor Authentication Audit Report

**Date:** November 20, 2025  
**Error:** `ERROR_BAD_USER_API_KEY: Unauthorized User API key`  
**Status:** 🔍 Comprehensive Audit

---

## 🔴 THE ERROR

```
ERROR_BAD_USER_API_KEY
Unauthorized User API key
```

**What this means:**
- Cursor's internal authentication system is rejecting the request
- This is **NOT** about Gemini or OpenAI API keys
- This is about **Cursor's own authentication** (access tokens, subscription)

---

## 🔍 AUDIT FINDINGS

### 1. Cursor Authentication System

**How Cursor authenticates:**
- Uses **access tokens** stored in database
- Uses **refresh tokens** to get new access tokens
- Checks **subscription status** (Stripe)
- Validates **membership type** (Pro, etc.)

**Location:**
- Database: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- Keys: `cursorAuth/accessToken`, `cursorAuth/refreshToken`, etc.

### 2. Common Causes

**Issue 1: Expired Access Token**
- Access tokens expire after some time
- Cursor should auto-refresh using refresh token
- If refresh fails, you get "Bad User API key" error

**Issue 2: Invalid Refresh Token**
- Refresh token may be invalid/expired
- Can't get new access token
- Authentication fails

**Issue 3: Subscription Issues**
- Subscription expired
- Payment failed
- Account suspended

**Issue 4: Database Corruption**
- Database file corrupted
- Tokens not readable
- Authentication data lost

---

## ✅ AUDIT CHECKLIST

Run the audit script:
```bash
python3 scripts/setup/audit_cursor_auth.py
```

**What it checks:**
1. ✅ Cursor installation directory
2. ✅ Settings file (JSON valid, API keys present)
3. ✅ Database (exists, readable)
4. ✅ Access token (exists, valid format)
5. ✅ Refresh token (exists)
6. ✅ Subscription status (active)
7. ✅ Membership type (Pro, etc.)
8. ✅ API key functionality (Gemini, OpenAI)

---

## 🔧 FIXES

### Fix 1: Re-authenticate with Cursor

**Steps:**
1. **Open Cursor Settings:**
   - `Cmd + ,` (Settings)
   - Or: Cursor → Preferences → Settings

2. **Go to Account:**
   - Search for "Account" or "Sign In"
   - Or: Cursor → Account

3. **Sign Out:**
   - Click "Sign Out" or "Log Out"
   - Wait for sign out to complete

4. **Sign Back In:**
   - Click "Sign In"
   - Enter your Cursor account credentials
   - This will generate new access/refresh tokens

5. **Restart Cursor:**
   - `Cmd + Q` → Quit
   - Reopen Cursor

**Why this works:**
- Generates fresh access token
- Gets new refresh token
- Updates subscription status
- Fixes authentication issues

---

### Fix 2: Check Subscription Status

**Steps:**
1. **Go to Cursor Account:**
   - https://cursor.sh/settings
   - Or: Cursor → Account → Manage Subscription

2. **Verify:**
   - Subscription is active
   - Payment method is valid
   - No payment failures

3. **If expired:**
   - Renew subscription
   - Update payment method
   - Wait for activation

---

### Fix 3: Clear Cursor Cache (Nuclear Option)

**If re-authentication doesn't work:**

1. **Quit Cursor:**
   - `Cmd + Q` → Quit completely

2. **Backup database:**
   ```bash
   cp ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
      ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb.backup
   ```

3. **Delete authentication data:**
   ```bash
   # Remove only auth entries (keeps other settings)
   sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
     "DELETE FROM ItemTable WHERE key LIKE 'cursorAuth/%';"
   ```

4. **Reopen Cursor:**
   - Cursor will prompt you to sign in
   - Sign in with your account
   - New tokens will be generated

**⚠️ WARNING:** This removes all authentication data. You'll need to sign in again.

---

### Fix 4: Reinstall Cursor (Last Resort)

**If nothing else works:**

1. **Export settings:**
   - Backup `settings.json`
   - Note your API keys

2. **Uninstall Cursor:**
   - Delete application
   - Delete `~/Library/Application Support/Cursor`

3. **Reinstall Cursor:**
   - Download from cursor.sh
   - Install fresh

4. **Restore settings:**
   - Copy `settings.json` back
   - Re-enter API keys
   - Sign in to Cursor account

---

## 🔍 DIAGNOSTIC COMMANDS

### Check Access Token
```bash
sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
  "SELECT key, length(value) FROM ItemTable WHERE key = 'cursorAuth/accessToken';"
```

### Check Subscription
```bash
sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
  "SELECT key, value FROM ItemTable WHERE key LIKE 'cursorAuth/stripe%';"
```

### Check All Auth Keys
```bash
sqlite3 ~/Library/Application\ Support/Cursor/User/globalStorage/state.vscdb \
  "SELECT key FROM ItemTable WHERE key LIKE 'cursorAuth/%';"
```

---

## 📋 TROUBLESHOOTING FLOWCHART

```
Bad User API key Error
         │
         ├─→ Run audit script
         │   └─→ Check findings
         │
         ├─→ Access token missing/invalid?
         │   └─→ Re-authenticate (Fix 1)
         │
         ├─→ Subscription expired?
         │   └─→ Renew subscription (Fix 2)
         │
         ├─→ Database corrupted?
         │   └─→ Clear cache (Fix 3)
         │
         └─→ Still not working?
             └─→ Reinstall Cursor (Fix 4)
```

---

## ✅ VERIFICATION

**After applying fixes:**

1. **Run audit again:**
   ```bash
   python3 scripts/setup/audit_cursor_auth.py
   ```

2. **Check for issues:**
   - Should show ✅ for all checks
   - No ❌ critical issues
   - Warnings are OK

3. **Test Cursor:**
   - Try using Cursor features
   - Check if error is gone
   - Verify subscription works

---

## 🎯 SUMMARY

**The Problem:**
- Cursor's internal authentication is failing
- Access token may be expired/invalid
- Subscription may have issues

**The Solution:**
1. **First:** Re-authenticate (Fix 1) - Usually fixes it
2. **Second:** Check subscription (Fix 2) - If payment issue
3. **Third:** Clear cache (Fix 3) - If database issue
4. **Last:** Reinstall (Fix 4) - Nuclear option

**Most Common Fix:**
- Re-authenticate with Cursor account
- This refreshes tokens and fixes 90% of cases

---

## 📄 RELATED FILES

- `scripts/setup/audit_cursor_auth.py` - Comprehensive audit script
- `docs/setup/CURSOR_CHATS_FIXED.md` - Gemini/OpenAI API fixes
- `docs/setup/TOP_K_ERROR_FINAL_FIX.md` - Gemini top_k error fix

---

**Status:** 🔍 Audit Complete - Apply Fixes Based on Findings

