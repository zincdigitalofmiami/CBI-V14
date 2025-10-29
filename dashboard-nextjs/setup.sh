#!/bin/bash

echo "🚀 Setting up CBI-V14 Next.js Dashboard..."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env.local file
echo "⚙️  Creating environment file..."
cat > .env.local << EOL
# CBI-V14 Dashboard Environment Variables
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080

# Add your backend URL here
# NEXT_PUBLIC_API_BASE_URL=https://your-api-url.com
EOL

# Create types directory
mkdir -p src/types

# Create basic types file
cat > src/types/index.ts << EOL
export interface ForecastData {
  horizon: string
  prediction: number
  current_price: number
  predicted_change_pct: number
  confidence_metrics: {
    mae: number
    r2: number
  }
}

export interface PriceData {
  current_price: number
  daily_change: number
  daily_change_pct: number
  volume: number
  high_24h: number
  low_24h: number
  last_updated: string
}

export interface MarketData {
  regime: string
  regime_description: string
  vix: number
  sentiment_score: number
  key_drivers: string[]
  risk_level: 'low' | 'medium' | 'high'
  recommendation: string
}
EOL

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. cd dashboard-nextjs"
echo "2. npm run dev"
echo "3. Open http://localhost:3000"
echo ""
echo "📝 To customize:"
echo "- Edit src/app/page.tsx for main dashboard"
echo "- Update API endpoints in components"
echo "- Customize colors in tailwind.config.js"
echo ""
echo "🔧 API Integration:"
echo "- Replace mock data with real API calls"
echo "- Update NEXT_PUBLIC_API_BASE_URL in .env.local"
echo ""
echo "Ready to build professional TradingView-style dashboard! 🎉"
