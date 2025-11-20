# Cursor API Key Authentication Error Fix

**Date:** January 2025  
**Error:** `ERROR_BAD_USER_API_KEY` - "Unauthorized User API key"

---

## 🔴 ERROR MESSAGE

```
{"error":"ERROR_BAD_USER_API_KEY","details":{"title":"Bad User API key","detail":"Unauthorized User API key"}}
```

---

## ✅ QUICK FIX

### Method 1: Update API Key in Settings

1. **Open Cursor Settings:**
   - Press `Cmd + ,` (or `Cursor → Settings`)
   - Or `Cmd + Shift + P` → "Preferences: Open Settings"

2. **Find API Key Setting:**
   - Search for "API Key" or "Cursor API"
   - Look for `cursor.apiKey` or similar setting

3. **Get New API Key:**
   - Go to: https://cursor.sh/settings
   - Copy your API key

4. **Update Setting:**
   - Paste new API key into Cursor settings
   - Save settings

5. **Restart Cursor:**
   - `Cmd + Q` to quit completely
   - Reopen Cursor

### Method 2: Re-authenticate

1. **Open Command Palette:**
   - `Cmd + Shift + P`

2. **Sign In:**
   - Type: "Cursor: Sign In"
   - Follow authentication flow

3. **Or Use Account Menu:**
   - Click account icon in Cursor
   - Select "Sign In" or "Re-authenticate"

---

## 🔍 VERIFY FIX

After updating:

1. **Check Settings:**
   - Verify API key is saved in `settings.json`
   - Location: `~/Library/Application Support/Cursor/User/settings.json`

2. **Test Cursor Features:**
   - Try using Cursor chat
   - Try code completion
   - Check if error is gone

---

## 📝 SETTINGS FILE LOCATION

**macOS:**
```
~/Library/Application Support/Cursor/User/settings.json
```

**Check current API key:**
```bash
cat ~/Library/Application\ Support/Cursor/User/settings.json | grep -i apikey
```

---

## ⚠️ COMMON CAUSES

1. **Expired Key:** API key may have expired
2. **Invalid Key:** Key was copied incorrectly
3. **Account Issue:** Cursor account subscription issue
4. **Network Issue:** Temporary connection problem

---

## 🔗 RELATED

- Cursor Settings: https://cursor.sh/settings
- Cursor Documentation: https://cursor.sh/docs

---

**After fixing, you should be able to use Cursor features normally again.**


