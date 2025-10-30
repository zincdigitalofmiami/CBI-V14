# CBI-V14 Dashboard - Vercel Deployment Guide

## Problem Summary

Your dashboard was calling `localhost:8080` which works locally but fails on Vercel. We've now created **Next.js API routes** that connect directly to BigQuery and Vertex AI models, eliminating the need for a separate backend server.

## What We Fixed

### 1. Created Next.js API Routes ✅
- **File**: `/src/app/api/v4/forecast/[horizon]/route.ts`
- **Purpose**: Direct access to Vertex AI models from Vercel
- **Models Available**:
  - 1W: Model `575258986094264320` (2.02% MAPE) ✅ TRAINED
  - 3M: Model `3157158578716934144` (2.68% MAPE) ✅ TRAINED
  - 6M: Model `3788577320223113216` (2.51% MAPE) ✅ TRAINED
  - 1M: Pipeline `7445431996387426304` (🚀 TRAINING)

### 2. Updated Frontend Components ✅
- Changed from `http://localhost:8080/api/v4/forecast/` → `/api/v4/forecast/`
- Now uses relative URLs that work on both local and Vercel
- Components updated:
  - `ForecastCards.tsx`
  - `ProcurementSignal.tsx`

### 3. Created BigQuery Helper Library ✅
- **File**: `/src/lib/bigquery.ts`
- Handles credentials automatically:
  - **Local**: Uses `GOOGLE_APPLICATION_CREDENTIALS` environment variable
  - **Vercel**: Uses `GOOGLE_APPLICATION_CREDENTIALS_BASE64` (base64 encoded JSON)

## Deployment Instructions

### Step 1: Set Up Google Cloud Credentials

You need to add your Google Cloud service account credentials to Vercel:

```bash
# Option A: Via Vercel Dashboard (RECOMMENDED)
1. Go to https://vercel.com/your-project/settings/environment-variables
2. Add these variables:
   - GCP_PROJECT_ID = cbi-v14
   - GOOGLE_APPLICATION_CREDENTIALS_BASE64 = <base64 encoded JSON>

# To get the base64 encoded JSON:
cat path/to/your-service-account-key.json | base64 | tr -d '\n'

# Option B: Via Vercel CLI
vercel env add GCP_PROJECT_ID
# Enter: cbi-v14

vercel env add GOOGLE_APPLICATION_CREDENTIALS_BASE64
# Paste the base64 encoded JSON (from command above)
```

### Step 2: Test Locally First

```bash
cd /Users/zincdigital/CBI-V14/dashboard-nextjs

# 1. Install dependencies (if needed)
npm install

# 2. Create .env.local with your credentials
cat > .env.local << EOF
GCP_PROJECT_ID=cbi-v14
# Add your GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_BASE64
EOF

# 3. Start dev server
npm run dev

# 4. Run test script
./test-api.sh http://localhost:3000

# 5. Open browser to test dashboard
open http://localhost:3000
```

### Step 3: Deploy to Vercel

```bash
# Make sure you're in the dashboard directory
cd /Users/zincdigital/CBI-V14/dashboard-nextjs

# Deploy to production
vercel --prod

# Or if you're using git (recommended)
git add .
git commit -m "Fix: Use Next.js API routes for Vertex AI predictions"
git push origin main
# Vercel will auto-deploy from git push
```

### Step 4: Test Production

```bash
# Test the production API
./test-api.sh https://cbi-dashboard.vercel.app

# Or manually:
curl https://cbi-dashboard.vercel.app/api/health
curl https://cbi-dashboard.vercel.app/api/v4/forecast/1w?model_type=automl_v4
```

## Architecture

### Before (Broken on Vercel)
```
Dashboard (Vercel) → localhost:8080 (FastAPI) → BigQuery
                     ❌ Doesn't work on Vercel
```

### After (Works Everywhere)
```
Dashboard (Vercel) → Next.js API Routes (Vercel) → BigQuery/Vertex AI
                     ✅ Works on Vercel
```

## Environment Variables Required

| Variable | Value | Where |
|----------|-------|-------|
| `GCP_PROJECT_ID` | `cbi-v14` | Vercel Environment Variables |
| `GOOGLE_APPLICATION_CREDENTIALS_BASE64` | Base64 encoded JSON | Vercel Environment Variables |

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not found"

**Solution**: Add the environment variable to Vercel:
```bash
# Get your service account key
cat ~/path/to/service-account-key.json | base64 | tr -d '\n'

# Add to Vercel (via dashboard or CLI)
vercel env add GOOGLE_APPLICATION_CREDENTIALS_BASE64
```

### Error: "Permission denied" or "BigQuery access denied"

**Solution**: Verify your service account has these roles:
- BigQuery Data Viewer
- BigQuery Job User
- Vertex AI User

```bash
# Check in Google Cloud Console:
# IAM & Admin > Service Accounts > Your Service Account > Permissions
```

### Error: "Model not found"

**Solution**: Check that your model IDs in the API route match your trained models:

```bash
# List your models
bq ls -m cbi-v14:models_v4

# Update the AVAILABLE_MODELS object in:
# src/app/api/v4/forecast/[horizon]/route.ts
```

### Dashboard shows "Loading..." forever

**Possible causes**:
1. API routes returning errors (check browser console)
2. Environment variables not set in Vercel
3. BigQuery credentials invalid

**Debug steps**:
```bash
# Check Vercel logs
vercel logs --prod

# Test API directly
curl https://cbi-dashboard.vercel.app/api/health

# Check browser console for errors
# Open DevTools (F12) > Console tab
```

## Model Status

According to `MASTER_TRAINING_PLAN.md`:

| Horizon | Model ID | MAPE | R² | Status |
|---------|----------|------|-----|--------|
| **1W** | 575258986094264320 | **2.02%** | 0.9836 | ✅ COMPLETE |
| **1M** | (training) | *pending* | - | 🚀 RUNNING |
| **3M** | 3157158578716934144 | **2.68%** | 0.9727 | ✅ COMPLETE |
| **6M** | 3788577320223113216 | **2.51%** | 0.9792 | ✅ COMPLETE |

The dashboard will automatically use the trained models as they become available.

## Files Changed

```
dashboard-nextjs/
├── src/
│   ├── app/
│   │   └── api/
│   │       ├── health/
│   │       │   └── route.ts (NEW - Health check endpoint)
│   │       └── v4/
│   │           └── forecast/
│   │               └── [horizon]/
│   │                   └── route.ts (NEW - Vertex AI predictions)
│   ├── components/
│   │   └── dashboard/
│   │       ├── ForecastCards.tsx (UPDATED - Uses relative URLs)
│   │       └── ProcurementSignal.tsx (UPDATED - Uses relative URLs)
│   └── lib/
│       └── bigquery.ts (NEW - BigQuery client helper)
├── .env.local.example (NEW - Example environment config)
├── VERCEL_SETUP.md (NEW - Detailed setup guide)
├── DEPLOYMENT.md (THIS FILE)
└── test-api.sh (NEW - Test script)
```

## Next Steps

1. ✅ Set up Google Cloud credentials in Vercel
2. ✅ Test locally: `npm run dev && ./test-api.sh`
3. ✅ Deploy: `vercel --prod`
4. ✅ Test production: `./test-api.sh https://cbi-dashboard.vercel.app`
5. ✅ Monitor: Check Vercel dashboard for any errors

## Support

If you encounter issues:

1. **Check Vercel logs**: `vercel logs --prod`
2. **Test API health**: `curl https://cbi-dashboard.vercel.app/api/health`
3. **Verify credentials**: Make sure environment variables are set in Vercel
4. **Check browser console**: Open DevTools (F12) and look for errors

---

**Dashboard URL**: https://cbi-dashboard.vercel.app (permanent, never changes)

**API Endpoints**:
- Health: `/api/health`
- Forecasts: `/api/v4/forecast/{1w|1m|3m|6m}?model_type=automl_v4`

**Cost**: Next.js API routes on Vercel are included in your plan, no additional backend costs!



