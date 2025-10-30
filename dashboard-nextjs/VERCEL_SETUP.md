# Vercel Deployment Setup for CBI-V14 Dashboard

## Issue Identified
The dashboard was calling `localhost:8080` which works locally but fails on Vercel production. We've now created Next.js API routes that can access BigQuery/Vertex AI models directly from Vercel.

## Prerequisites
1. Google Cloud Service Account with BigQuery access
2. Service Account Key JSON file
3. Vercel account with dashboard project

## Setup Instructions

### 1. Get Google Cloud Credentials

```bash
# In Google Cloud Console:
# 1. Go to IAM & Admin > Service Accounts
# 2. Create or select service account with these roles:
#    - BigQuery Data Viewer
#    - BigQuery Job User
#    - Vertex AI User
# 3. Create Key > JSON
# 4. Download the JSON file
```

### 2. Configure Vercel Environment Variables

```bash
# Method 1: Via Vercel Dashboard
# 1. Go to your project settings
# 2. Navigate to Environment Variables
# 3. Add these variables:

GCP_PROJECT_ID=cbi-v14
GOOGLE_APPLICATION_CREDENTIALS_BASE64=<base64 encoded JSON>

# To get base64 encoded JSON:
cat path/to/service-account-key.json | base64

# Method 2: Via Vercel CLI
vercel env add GCP_PROJECT_ID
# Enter: cbi-v14

vercel env add GOOGLE_APPLICATION_CREDENTIALS_BASE64
# Paste the base64 encoded JSON
```

### 3. Update API Route (if needed)

The API route at `/src/app/api/v4/forecast/[horizon]/route.ts` automatically uses:
- Service account credentials from environment variables on Vercel
- Application default credentials locally

### 4. Deploy to Vercel

```bash
# From dashboard-nextjs directory
vercel --prod

# Or push to GitHub and let Vercel auto-deploy
git add .
git commit -m "Fix: Use Next.js API routes for Vertex AI predictions"
git push origin main
```

## Model Registry

The API routes now support these Vertex AI models:

- **1W**: Model ID `575258986094264320` (2.02% MAPE)
- **3M**: Model ID `3157158578716934144` (2.68% MAPE)  
- **6M**: Model ID `3788577320223113216` (2.51% MAPE)
- **1M**: Currently training (Pipeline `7445431996387426304`)

## Testing

### Local Testing
```bash
# 1. Create .env.local from .env.local.example
cp .env.local.example .env.local

# 2. Add your credentials to .env.local
# 3. Start development server
npm run dev

# 4. Test API route
curl http://localhost:3000/api/v4/forecast/1w?model_type=automl_v4
```

### Production Testing
```bash
# After deploying to Vercel
curl https://cbi-dashboard.vercel.app/api/v4/forecast/1w?model_type=automl_v4
```

## Troubleshooting

### Error: "GOOGLE_APPLICATION_CREDENTIALS not found"
- Ensure environment variable is set in Vercel
- Check that the base64 encoding is correct
- Verify service account has proper permissions

### Error: "Model not found"
- Check that model IDs in route.ts match your BigQuery models
- Verify models exist: `bq ls -m cbi-v14:models_v4`

### Error: "Permission denied"
- Ensure service account has these roles:
  - BigQuery Data Viewer
  - BigQuery Job User
  - Vertex AI User

## Next Steps

1. ✅ Created Next.js API routes for Vertex AI predictions
2. ✅ Updated frontend to use relative URLs
3. 🔄 Configure Google Cloud credentials in Vercel
4. ⏳ Test locally before deploying
5. ⏳ Deploy to Vercel production

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Production                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Next.js Dashboard (Frontend)                        │   │
│  │  https://cbi-dashboard.vercel.app                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                        ↓                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Next.js API Routes                                   │   │
│  │  /api/v4/forecast/[horizon]                          │   │
│  │  (Runs on Vercel Edge Functions)                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        ↓
              ┌────────────────────┐
              │  Google Cloud      │
              │  BigQuery          │
              │  + Vertex AI       │
              │  Models            │
              └────────────────────┘
```

## Benefits of This Approach

1. **No separate backend needed** - Next.js API routes run on Vercel
2. **Secure credentials** - Environment variables never exposed to frontend
3. **Automatic scaling** - Vercel handles all infrastructure
4. **Cost efficient** - No need to run separate FastAPI server
5. **Single deployment** - Dashboard + API in one Vercel project





