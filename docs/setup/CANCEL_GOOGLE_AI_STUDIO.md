# Cancel Google AI Studio - Stop $70/month Charge

**Date:** January 2025  
**Issue:** Google AI Studio costing $70/month, not being used

---

## 🚨 IMMEDIATE ACTION REQUIRED

**Current Cost:** $70/month for Google AI Studio  
**Action:** Cancel subscription and disable APIs

---

## ✅ STEP-BY-STEP CANCELLATION

### Step 1: Cancel Subscription in Google Cloud Console

1. **Go to Google Cloud Console:**
   - https://console.cloud.google.com/billing
   - Sign in with your Google account

2. **Find Subscriptions:**
   - Click on your billing account
   - Look for "Subscriptions" or "Purchased Products"
   - Find "Google AI Studio" or "Gemini API" subscription

3. **Cancel Subscription:**
   - Click on the subscription
   - Click "Cancel Subscription" or "Disable Auto-Renewal"
   - Confirm cancellation
   - **Note:** You'll have access until end of billing period

---

### Step 2: Disable Generative Language API

**Disable the API to prevent any usage charges:**

```bash
# Disable Generative Language API
gcloud services disable generativelanguage.googleapis.com --project=cbi-v14

# Disable Gemini for Google Cloud API (if not needed)
gcloud services disable cloudaicompanion.googleapis.com --project=cbi-v14
```

**Or via Console:**
1. Go to: https://console.cloud.google.com/apis/library?project=cbi-v14
2. Search for "Generative Language API"
3. Click on it
4. Click "DISABLE API"
5. Confirm

---

### Step 3: Delete/Revoke API Keys

**If you're not using the API key, revoke it:**

1. **Go to API Credentials:**
   - https://console.cloud.google.com/apis/credentials?project=cbi-v14

2. **Find your API key:**
   - Look for key: `AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q`
   - Or any other Gemini/AI Studio keys

3. **Revoke or Delete:**
   - Click on the key
   - Click "DELETE" or "RESTRICT KEY"
   - Confirm

**Note:** If you still want to use Gemini via Python scripts (free tier), you can keep the key but restrict it to prevent charges.

---

### Step 4: Remove from Cursor Settings

**Remove Gemini API key from Cursor to prevent usage:**

1. **Open Cursor Settings:**
   - `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"

2. **Remove or comment out:**
   ```json
   // Remove these lines:
   "geminicodeassist.apiKey": "AIzaSyBUEg8HK4z-J2foquJ2chAlQVRoGkiPM1Q",
   "geminicodeassist.project": "cbi-v14",
   ```

3. **Save and restart Cursor**

---

## 🔍 VERIFY CANCELLATION

### Check Billing:

1. **Go to:** https://console.cloud.google.com/billing
2. **Check:** Current month charges
3. **Verify:** No new charges for AI Studio/Gemini

### Check API Status:

```bash
# Check if APIs are disabled
gcloud services list --enabled --project=cbi-v14 | grep generativelanguage
# Should return nothing if disabled
```

### Check Subscriptions:

1. **Go to:** https://console.cloud.google.com/billing/subscriptions
2. **Verify:** No active AI Studio subscriptions

---

## 💰 UNDERSTANDING THE $70 CHARGE

**Possible sources:**

1. **Google AI Studio Premium Subscription:**
   - Monthly subscription fee
   - Cancel via billing console

2. **High API Usage:**
   - If using paid tier models
   - Check usage: https://console.cloud.google.com/apis/dashboard?project=cbi-v14

3. **Gemini Code Assist License:**
   - Enterprise/Standard license
   - Cancel: https://console.cloud.google.com/gemini/code-assist/licenses

---

## 🎯 QUICK COMMANDS

**Disable APIs (run these):**

```bash
# Disable Generative Language API
gcloud services disable generativelanguage.googleapis.com --project=cbi-v14

# Verify disabled
gcloud services list --enabled --project=cbi-v14 | grep -i "generative\|gemini"
```

**Check current charges:**

```bash
# Check billing account
gcloud billing accounts list

# Check project billing
gcloud billing projects describe cbi-v14
```

---

## ⚠️ IMPORTANT NOTES

1. **Access Until Period End:**
   - Cancellation takes effect at end of billing period
   - You'll still be charged for current period

2. **Free Tier Still Available:**
   - Google AI Studio has a free tier
   - You can still use it without subscription
   - Just disable paid features

3. **If You Need Gemini:**
   - Use free tier (limited requests)
   - Or use direct API calls with free tier
   - No $70/month subscription needed

---

## 📋 CHECKLIST

- [ ] Cancel subscription in billing console
- [ ] Disable Generative Language API
- [ ] Revoke/delete API keys (if not needed)
- [ ] Remove API key from Cursor settings
- [ ] Verify no new charges
- [ ] Check next billing cycle

---

## 🔗 LINKS

- **Billing Console:** https://console.cloud.google.com/billing
- **Subscriptions:** https://console.cloud.google.com/billing/subscriptions
- **API Library:** https://console.cloud.google.com/apis/library?project=cbi-v14
- **API Credentials:** https://console.cloud.google.com/apis/credentials?project=cbi-v14

---

**After cancellation, you should see $0 charges for AI Studio in next billing cycle.**


