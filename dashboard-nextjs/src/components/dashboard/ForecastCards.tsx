'use client'

import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, Clock, AlertTriangle, Activity } from 'lucide-react'

interface HorizonForecast {
  horizon: string
  business_label: string
  current_price: number
  predicted_price: number
  change_pct: number
  confidence: number
  model_id: string
  mape: number | null
  recommendation: string
  procurement_timeline: string
  use_case: string
}

interface ForecastData {
  forecasts: HorizonForecast[]
  last_updated: string
}

async function fetchForecasts(): Promise<ForecastData> {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  
  // Fetch all 4 horizons from V4 API
  const horizons = ['1w', '1m', '3m', '6m']
  const forecastPromises = horizons.map(h => 
    fetch(`${apiUrl}/api/v4/forecast/${h}`).then(r => r.ok ? r.json() : null)
  )
  
  const results = await Promise.all(forecastPromises)
  
  const horizonMap: Record<string, any> = {
    '1w': {
      business_label: 'Immediate Spot Orders',
      procurement_timeline: 'Execute this week',
      use_case: 'Daily operations & spot purchases'
    },
    '1m': {
      business_label: 'Monthly Contracts',
      procurement_timeline: 'Plan for next month',
      use_case: 'Standard monthly supply contracts'
    },
    '3m': {
      business_label: 'Quarterly Planning',
      procurement_timeline: 'Q2 2025 contracts',
      use_case: 'Quarterly hedging & budget planning'
    },
    '6m': {
      business_label: 'Strategic Hedging',
      procurement_timeline: 'H2 2025 strategy',
      use_case: 'Long-term contracts & annual planning'
    }
  }
  
  const forecasts: HorizonForecast[] = results
    .filter(r => r !== null)
    .map((item: any) => {
      const horizonInfo = horizonMap[item.horizon]
      return {
        horizon: item.horizon,
        business_label: horizonInfo.business_label,
        current_price: item.current_price,
        predicted_price: item.prediction,
        change_pct: item.predicted_change_pct,
        confidence: item.confidence_metrics?.r2 ? item.confidence_metrics.r2 * 100 : 85,
        model_id: item.model_name,
        mape: item.confidence_metrics?.mape_percent || null,
        recommendation: item.predicted_change_pct > 2 ? 'Buy now' : item.predicted_change_pct < -2 ? 'Wait' : 'Monitor',
        procurement_timeline: horizonInfo.procurement_timeline,
        use_case: horizonInfo.use_case
      }
    })
  
  return {
    forecasts,
    last_updated: new Date().toISOString()
  }
}

export function ForecastCards() {
  const { data: forecastData, isLoading, error } = useQuery({
    queryKey: ['forecasts-all'],
    queryFn: fetchForecasts,
    refetchInterval: 120000, // Update every 2 minutes
  })

  if (isLoading) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-text-primary mb-6">
          Chris's Procurement Timeline - Loading Model Forecasts...
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-background-secondary border border-border-primary rounded-lg p-6">
              <div className="space-y-4">
                <div className="loading-shimmer h-6 w-32 rounded"></div>
                <div className="loading-shimmer h-12 w-full rounded"></div>
                <div className="loading-shimmer h-8 w-full rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !forecastData) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-text-primary mb-6">
          Price Forecasts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {['1 Week', '1 Month', '3 Months', '6 Months'].map((horizon) => (
            <div key={horizon} className="bg-background-secondary border border-border-primary rounded-lg p-6">
              <div className="text-center py-8">
                <Activity className="w-8 h-8 text-text-secondary mx-auto mb-4 animate-pulse" />
                <h3 className="text-sm font-medium text-text-secondary">
                  {horizon} Forecast
                </h3>
                <p className="text-xs text-text-tertiary mt-2">
                  Loading...
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-text-primary">
          Procurement Timeline
        </h2>
        <div className="flex items-center space-x-2 text-sm text-text-secondary">
          <Clock className="w-4 h-4" />
          <span>Updated {new Date(forecastData.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {forecastData.forecasts.map((forecast) => {
          const isPositive = forecast.change_pct > 0
          const isTraining = forecast.model_id.includes('TRAINING')
          
          return (
            <div
              key={forecast.horizon}
              className="bg-background-secondary border border-border-primary rounded-lg p-6 hover:border-accent-blue/50 transition-colors"
            >
              {/* Header with Business Context */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-text-primary">
                    {forecast.horizon.toUpperCase()}
                  </h3>
                  <Activity className={`w-5 h-5 ${
                    isPositive ? 'text-bull-500' : 'text-bear-500'
                  }`} />
                </div>
                <p className="text-sm text-text-secondary font-medium">
                  {forecast.business_label}
                </p>
                <p className="text-xs text-text-tertiary">
                  {forecast.use_case}
                </p>
              </div>
              
              {/* Price Forecast */}
              <div className="space-y-4 mb-6">
                <div>
                  <p className="text-xs text-text-tertiary uppercase tracking-wider mb-1">
                    Current → Target
                  </p>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-lg font-light text-text-primary">
                      ${forecast.current_price.toFixed(2)}
                    </span>
                    <span className="text-xs text-text-tertiary">→</span>
                    <span className="text-xl font-semibold text-text-primary">
                      ${forecast.predicted_price.toFixed(2)}
                    </span>
                  </div>
                </div>
                
                <div className={`flex items-center space-x-2 ${
                  isPositive ? 'text-bull-500' : 'text-bear-500'
                }`}>
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  <span className="font-medium">
                    {isPositive ? '+' : ''}{forecast.change_pct.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Procurement Recommendation */}
              <div className="mb-4 p-3 bg-background-tertiary rounded-lg">
                <p className="text-xs text-text-tertiary uppercase tracking-wider mb-1">
                  Chris's Action
                </p>
                <p className="text-sm font-medium text-text-primary">
                  {forecast.recommendation}
                </p>
                <p className="text-xs text-text-tertiary mt-1">
                  {forecast.procurement_timeline}
                </p>
              </div>
              
              {/* Model Performance */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-text-tertiary mb-1">
                    <span>Model Confidence</span>
                    <span>{forecast.confidence.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-background-tertiary rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isTraining 
                          ? 'bg-gradient-to-r from-yellow-600 to-yellow-400'
                          : 'bg-gradient-to-r from-bull-600 to-bull-400'
                      }`}
                      style={{ width: `${forecast.confidence}%` }}
                    />
                  </div>
                </div>

                <div className="text-xs text-text-tertiary">
                  {isTraining ? (
                    <span className="text-yellow-500">Model Training...</span>
                  ) : (
                    <>
                      <span>Model: {forecast.model_id.slice(-6)}</span>
                      {forecast.mape && (
                        <span> • MAPE: {forecast.mape.toFixed(1)}%</span>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
