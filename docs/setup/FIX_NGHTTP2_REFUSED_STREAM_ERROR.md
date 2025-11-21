# Fix NGHTTP2_REFUSED_STREAM Error in Cursor

**Date:** November 20, 2025  
**Error:** `NGHTTP2_REFUSED_STREAM` - Stream closed with error code  
**Status:** 🔴 Connectivity Issue with Cursor Backend

---

## 🔴 THE ERROR

**Error Message:**
```
ConnectError: [internal] Stream closed with error code NGHTTP2_REFUSED_STREAM
```

**What's Failing:**
- ❌ Ping - Stream refused
- ❌ Chat - Stream refused
- ❌ Agent - Stream refused
- ✅ API - Working (check successful)

**What This Means:**
- Cursor's backend services are refusing new streams
- Could be server overload, network issues, or connection problems
- This is NOT a model configuration issue
- This is a connectivity/streaming issue

---

## ✅ SOLUTIONS

### Solution 1: Restart Cursor (Try This First)

1. **Quit Cursor completely:**
   - Press `Cmd + Q`
   - Wait 10-15 seconds
   - Make sure it's fully closed

2. **Reopen Cursor**

3. **Check if errors are gone:**
   - Go to Settings → Network (or check logs)
   - Try using Chat/Composer
   - See if streams work now

### Solution 2: Clear Cursor Cache

1. **Quit Cursor:**
   - `Cmd + Q`

2. **Clear cache:**
   ```bash
   rm -rf ~/Library/Application\ Support/Cursor/Cache
   rm -rf ~/Library/Application\ Support/Cursor/CachedData
   ```

3. **Reopen Cursor**

### Solution 3: Check Network Connection

1. **Verify internet connection:**
   - Check if other apps can connect
   - Try browsing the web
   - Check if VPN is interfering

2. **Check firewall/proxy:**
   - Make sure Cursor can access:
     - `api.cursor.sh`
     - `cursor.sh`
   - Check if corporate firewall is blocking

3. **Try different network:**
   - Switch WiFi networks
   - Try mobile hotspot
   - See if issue persists

### Solution 4: Reset Network Settings in Cursor

1. **Open Cursor Settings:**
   - `Cmd + ,` (Settings)

2. **Go to Network section:**
   - Look for "Network" or "Connection" settings
   - Or search for "network"

3. **Reset network settings:**
   - Clear any proxy settings
   - Reset connection preferences
   - Disable any custom network configs

4. **Restart Cursor**

### Solution 5: Check Cursor Server Status

1. **Check if Cursor is having issues:**
   - Visit: https://status.cursor.sh (if available)
   - Check Cursor's Twitter/Discord for outages
   - See if others are reporting issues

2. **Wait and retry:**
   - If it's a server-side issue, wait 10-15 minutes
   - Try again later

### Solution 6: Re-authenticate with Cursor

1. **Sign out of Cursor:**
   - Settings → Account → Sign Out

2. **Sign back in:**
   - Sign in with your account
   - This refreshes connection tokens

3. **Restart Cursor**

---

## 🔍 TECHNICAL DETAILS

### What is NGHTTP2_REFUSED_STREAM?

**NGHTTP2_REFUSED_STREAM:**
- HTTP/2 error code
- Server is refusing to accept new streams
- Usually means server is overloaded or connection is bad

**Why It Happens:**
1. **Server overload** - Cursor's backend is too busy
2. **Network issues** - Connection problems
3. **Connection limits** - Too many concurrent connections
4. **Firewall/proxy** - Blocking HTTP/2 streams
5. **Stale connection** - Old connection needs refresh

### What's Working vs Not Working

**Working:**
- ✅ API check - Basic connectivity works

**Not Working:**
- ❌ Ping - Can't establish stream
- ❌ Chat - Can't start chat stream
- ❌ Agent - Can't start agent stream

**This suggests:**
- Basic connection works (API check succeeds)
- Streaming connections fail (HTTP/2 streams refused)
- Likely server-side or network issue

---

## 🔧 ADVANCED TROUBLESHOOTING

### Check Cursor Logs

1. **Open Cursor:**
   - Go to Help → Toggle Developer Tools
   - Or: `Cmd + Option + I`

2. **Check Console:**
   - Look for network errors
   - Check for connection failures
   - See detailed error messages

### Test Connection Manually

```bash
# Test if you can reach Cursor's API
curl -I https://api.cursor.sh

# Check DNS resolution
nslookup api.cursor.sh

# Test HTTP/2 connection
curl --http2 -I https://api.cursor.sh
```

### Check System Network Settings

1. **Check DNS:**
   - Make sure DNS is resolving correctly
   - Try using Google DNS (8.8.8.8) or Cloudflare (1.1.1.1)

2. **Check Proxy:**
   - System Settings → Network → Proxy
   - Make sure no proxy is interfering

3. **Check Firewall:**
   - System Settings → Security → Firewall
   - Make sure Cursor is allowed

---

## ✅ VERIFICATION

After trying fixes:

1. **Restart Cursor**
2. **Check logs again:**
   - Settings → Network (or logs)
   - Should see green checkmarks
   - No red X errors

3. **Test Chat:**
   - Open Chat/Composer
   - Try asking a question
   - Should work without stream errors

4. **Test Agent:**
   - Try using Cursor's agent features
   - Should work without errors

---

## 🎯 SUMMARY

**The Problem:**
- HTTP/2 streams being refused by Cursor's backend
- Connectivity/streaming issue, not model config

**Most Likely Causes:**
1. Server-side issue (Cursor backend overloaded)
2. Network connectivity problems
3. Stale connection needing refresh

**Quick Fixes:**
1. Restart Cursor (often fixes it)
2. Clear cache
3. Check network connection
4. Re-authenticate

**If Nothing Works:**
- Wait 10-15 minutes (might be server-side)
- Check Cursor status page
- Contact Cursor support

---

**Status:** 🔴 Connectivity Issue - Try Restart First

