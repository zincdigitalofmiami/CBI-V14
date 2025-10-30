#!/bin/bash
# Quick deployment script for CBI-V14 Dashboard

set -e

echo "🚀 CBI-V14 Dashboard - Quick Deploy"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in dashboard-nextjs directory"
    echo "Run this from: /Users/zincdigital/CBI-V14/dashboard-nextjs"
    exit 1
fi

echo "✓ In correct directory"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not installed"
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

echo "✓ Vercel CLI available"
echo ""

# Check if environment variables are set
echo "🔍 Checking environment variables..."
echo ""
echo "Required variables for Vercel:"
echo "  1. GCP_PROJECT_ID = cbi-v14"
echo "  2. GOOGLE_APPLICATION_CREDENTIALS_BASE64 = <base64 encoded JSON>"
echo ""

read -p "Have you added these to Vercel environment variables? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 To add environment variables:"
    echo ""
    echo "Option 1: Via Vercel Dashboard"
    echo "  1. Go to: https://vercel.com/your-project/settings/environment-variables"
    echo "  2. Add: GCP_PROJECT_ID = cbi-v14"
    echo "  3. Add: GOOGLE_APPLICATION_CREDENTIALS_BASE64 = <your base64 JSON>"
    echo ""
    echo "Option 2: Via CLI"
    echo "  vercel env add GCP_PROJECT_ID"
    echo "  vercel env add GOOGLE_APPLICATION_CREDENTIALS_BASE64"
    echo ""
    echo "To get base64 JSON:"
    echo "  cat path/to/service-account-key.json | base64 | tr -d '\n'"
    echo ""
    exit 1
fi

echo ""
echo "✓ Environment variables confirmed"
echo ""

# Build test
echo "🔨 Testing build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Fix errors before deploying."
    exit 1
fi

echo "✓ Build successful"
echo ""

# Deploy
echo "🚀 Deploying to Vercel production..."
vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🧪 Testing deployed API..."
    sleep 5  # Give Vercel a moment to propagate
    
    if command -v curl &> /dev/null; then
        echo "Testing health endpoint..."
        curl -s https://cbi-dashboard.vercel.app/api/health | head -3
        echo ""
        
        echo "Testing 1W forecast..."
        curl -s https://cbi-dashboard.vercel.app/api/v4/forecast/1w?model_type=automl_v4 | head -3
        echo ""
    fi
    
    echo ""
    echo "✅ All done! Your dashboard is live:"
    echo "   https://cbi-dashboard.vercel.app"
    echo ""
    echo "📊 Your Vertex AI models are now connected!"
    echo ""
    echo "Next steps:"
    echo "  1. Open https://cbi-dashboard.vercel.app in your browser"
    echo "  2. Check that forecasts are displaying"
    echo "  3. Run full test suite: ./test-api.sh https://cbi-dashboard.vercel.app"
    echo ""
else
    echo "❌ Deployment failed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Vercel logs: vercel logs --prod"
    echo "  2. Verify environment variables: vercel env ls"
    echo "  3. See DEPLOYMENT.md for detailed instructions"
    exit 1
fi





