'use client'

import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, AlertTriangle, Activity, Zap, Globe } from 'lucide-react'

interface MarketDriver {
  title: string
  status: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'CRITICAL'
  value: string
  impact_description: string
  confidence: number
  last_updated: string
  data_source: string
}

interface MarketDriversData {
  drivers: MarketDriver[]
  net_sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  updated_at: string
}

async function fetchMarketDrivers(): Promise<MarketDriversData> {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  
  const response = await fetch(`${apiUrl}/api/v4/forecast/1w`)
  
  if (!response.ok) {
    // NO FAKE DATA - Must connect to real BigQuery market driver signals
    throw new Error(`Market Drivers API unavailable: ${response.status}. ZERO FAKE DATA POLICY - Cannot display hardcoded market driver data.`)
  }
  
  return await response.json()
}

const getStatusColor = (status: MarketDriver['status']) => {
  switch (status) {
    case 'BULLISH': return 'text-buy-primary'
    case 'BEARISH': return 'text-sell-primary'
    case 'CRITICAL': return 'text-sell-critical'
    case 'NEUTRAL': return 'text-text-secondary'
    default: return 'text-text-secondary'
  }
}

const getStatusIcon = (status: MarketDriver['status']) => {
  switch (status) {
    case 'BULLISH': return <TrendingUp className="w-4 h-4" />
    case 'BEARISH': return <TrendingDown className="w-4 h-4" />
    case 'CRITICAL': return <AlertTriangle className="w-4 h-4" />
    case 'NEUTRAL': return <Activity className="w-4 h-4" />
    default: return <Activity className="w-4 h-4" />
  }
}

export function MarketDrivers() {
  const { data: driversData, isLoading, error } = useQuery({
    queryKey: ['market-drivers'],
    queryFn: fetchMarketDrivers,
    refetchInterval: 15 * 60 * 1000, // Update every 15 minutes
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary rounded-lg border border-border-primary p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Zap className="w-5 h-5 text-accent-purple animate-pulse" />
          <h2 className="text-lg font-semibold text-text-primary">
            Why Prices Are Moving - AI Market Intelligence
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-background-tertiary rounded-lg p-4">
              <div className="loading-shimmer h-4 w-24 rounded mb-2"></div>
              <div className="loading-shimmer h-6 w-16 rounded mb-1"></div>
              <div className="loading-shimmer h-3 w-full rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !driversData) {
    return (
      <div className="bg-sell-critical/10 border border-sell-critical/20 rounded-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background-tertiary flex items-center justify-center">
            <Zap className="w-8 h-8 text-sell-critical" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            No Market Intelligence Available
          </h3>
          <p className="text-text-secondary mb-4">
            Cannot connect to BigQuery market driver signals. ZERO FAKE DATA POLICY in effect.
          </p>
          <div className="bg-background-tertiary rounded-lg p-4 text-left">
            <h4 className="text-sm font-medium text-text-primary mb-2">Required BigQuery Features:</h4>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• feature_vix_stress (Market Volatility)</li>
              <li>• feature_harvest_pace (Supply Pressure)</li>
              <li>• china_soybean_imports_mt (Demand)</li>
              <li>• argentina_export_tax (Competition)</li>
            </ul>
          </div>
          <p className="text-xs text-text-tertiary mt-4">
            Error: {error?.message || 'API connection failed'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary rounded-lg border border-border-primary p-6 shadow-depth">
      {/* Header with Real-Time Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Zap className="w-5 h-5 text-accent-purple" />
          <h2 className="text-lg font-semibold text-text-primary">
            Why Prices Are Moving - AI Market Intelligence
          </h2>
        </div>
        <div className="flex items-center space-x-4">
          {/* Net Sentiment Indicator */}
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
            driversData.net_sentiment === 'BEARISH' 
              ? 'bg-sell-critical/20 text-sell-critical border border-sell-critical/30'
              : driversData.net_sentiment === 'BULLISH'
              ? 'bg-buy-primary/20 text-buy-primary border border-buy-primary/30'
              : 'bg-text-secondary/20 text-text-secondary border border-text-secondary/30'
          }`}>
            {getStatusIcon(driversData.net_sentiment)}
            <span>NET: {driversData.net_sentiment}</span>
          </div>
          {/* Live Update Indicator */}
          <div className="flex items-center space-x-2 text-xs text-text-tertiary font-mono">
            <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
            <span>LIVE</span>
          </div>
        </div>
      </div>

      {/* AI-Driven Market Drivers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {driversData.drivers.map((driver, index) => (
          <div 
            key={index}
            className="bg-background-tertiary rounded-lg p-4 border border-border-secondary hover:border-accent-purple/30 transition-all duration-200"
          >
            {/* Driver Header */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-secondary">
                {driver.title}
              </h3>
              <div className={`flex items-center space-x-1 ${getStatusColor(driver.status)}`}>
                {getStatusIcon(driver.status)}
              </div>
            </div>

            {/* Current Value/Status */}
            <div className={`text-base font-semibold mb-2 ${getStatusColor(driver.status)}`}>
              {driver.value}
            </div>

            {/* AI Analysis Description */}
            <p className="text-xs text-text-tertiary leading-relaxed mb-3 min-h-[36px]">
              {driver.impact_description}
            </p>

            {/* Confidence & Source */}
            <div className="space-y-2">
              {/* BigQuery Signal Strength */}
              <div>
                <div className="flex justify-between text-xs text-text-tertiary mb-1">
                  <span>BigQuery Signal</span>
                  <span className="text-accent-green font-mono">LIVE</span>
                </div>
                <div className="w-full bg-background-primary rounded-full h-1.5">
                  <div 
                    className="h-1.5 rounded-full bg-gradient-to-r from-accent-green to-buy-primary transition-all duration-500"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {/* Data Source */}
              <div className="flex items-center space-x-1">
                <Globe className="w-3 h-3 text-text-tertiary" />
                <span className="text-xs text-text-tertiary font-mono truncate">
                  {driver.data_source.split(' + ')[0]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Intelligence Summary */}
      <div className="mt-6 pt-4 border-t border-border-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-text-secondary">
            <Activity className="w-4 h-4" />
            <span>
              Market Intelligence: <strong className="text-text-primary">4 active signals</strong> 
              • Net Impact: <strong className={getStatusColor(driversData.net_sentiment)}>
                {driversData.net_sentiment}
              </strong>
            </span>
          </div>
          <div className="text-xs text-text-tertiary font-mono">
            Last updated: {new Date(driversData.updated_at).toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}
