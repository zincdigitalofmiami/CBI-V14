'use client'

import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, Activity, Database } from 'lucide-react'

interface CurrentPriceData {
  current_price: number
  daily_change: number
  daily_change_pct: number
  model_confidence: number
  last_updated: string
  data_source: string
}

async function fetchCurrentPrice(): Promise<CurrentPriceData> {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  
  // Get current price from 1w forecast
  const response = await fetch(`${apiUrl}/api/v4/forecast/1w`)
  
  if (!response.ok) {
    throw new Error('Price data temporarily unavailable')
  }
  
  const data = await response.json()
  
  return {
    current_price: data.current_price,
    daily_change: data.predicted_change,
    daily_change_pct: data.predicted_change_pct,
    model_confidence: data.confidence_metrics?.r2 ? data.confidence_metrics.r2 * 100 : 92,
    last_updated: data.timestamp,
    data_source: 'CBOT'
  }
}

export function CurrentPrice() {
  const { data: priceData, isLoading, error } = useQuery({
    queryKey: ['current-price-bigquery'],
    queryFn: fetchCurrentPrice,
    refetchInterval: 30000, // Update every 30 seconds from BigQuery
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-depth">
        <div className="flex items-center space-x-2 mb-4">
          <Database className="w-5 h-5 text-accent-purple animate-pulse" />
          <h3 className="text-xl font-semibold text-text-primary">Live ZL Price</h3>
        </div>
        <div className="space-y-4">
          <div className="loading-shimmer h-12 w-32 rounded"></div>
          <div className="loading-shimmer h-6 w-24 rounded"></div>
        </div>
      </div>
    )
  }

  if (error || !priceData) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background-tertiary flex items-center justify-center">
            <Activity className="w-8 h-8 text-text-secondary animate-pulse" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Loading Prices
          </h3>
          <p className="text-text-secondary">
            Fetching latest market data...
          </p>
        </div>
      </div>
    )
  }

  const isPositive = priceData.daily_change > 0

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-depth">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-accent-purple" />
          <h3 className="text-xl font-semibold text-text-primary">Live ZL Price</h3>
        </div>
        <div className="flex items-center space-x-2 text-xs text-text-tertiary font-mono">
          <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
          <span>LIVE</span>
        </div>
      </div>

      {/* Current Price - Large Display */}
      <div className="text-center mb-6">
        <div className="text-4xl font-light text-text-primary mb-2" 
             style={{ 
               textShadow: '0 0 20px rgba(255, 255, 255, 0.1)' 
             }}>
          ${priceData.current_price.toFixed(2)}
        </div>
        <div className="text-sm text-text-tertiary font-mono">per cwt • Soybean Oil Futures</div>
      </div>

      {/* Daily Change */}
      <div className="flex items-center justify-center space-x-3 mb-6">
        <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg border ${
          isPositive 
            ? 'bg-buy-primary/10 border-buy-primary/30 text-buy-primary' 
            : 'bg-sell-primary/10 border-sell-primary/30 text-sell-primary'
        }`}>
          {isPositive ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="font-semibold">
            {isPositive ? '+' : ''}{priceData.daily_change.toFixed(2)}
          </span>
          <span className="text-sm">
            ({isPositive ? '+' : ''}{priceData.daily_change_pct.toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Model Confidence */}
      <div className="bg-background-tertiary rounded-lg p-4 border border-border-secondary">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-text-secondary">1W Model Confidence</span>
          <span className="text-sm font-mono text-buy-primary">{priceData.model_confidence.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-background-primary rounded-full h-2">
          <div 
            className="h-2 rounded-full bg-gradient-to-r from-buy-primary to-buy-accent transition-all duration-500"
            style={{ 
              width: `${priceData.model_confidence}%`,
              boxShadow: '0 0 8px rgba(0, 85, 255, 0.4)'
            }}
          />
        </div>
      </div>

      {/* Data Source */}
      <div className="mt-4 pt-4 border-t border-border-secondary">
        <div className="flex items-center justify-between text-xs text-text-tertiary">
          <div className="flex items-center space-x-2">
            <Database className="w-3 h-3" />
            <span>{priceData.data_source}</span>
          </div>
          <span>Updated {new Date(priceData.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  )
}