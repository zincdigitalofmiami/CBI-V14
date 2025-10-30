'use client'

import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, TrendingDown, Database, Zap } from 'lucide-react'

interface BigEightSignal {
  signal_name: string
  current_value: number
  signal_strength: 'STRONG' | 'MODERATE' | 'WEAK'
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  impact_score: number
  last_updated: string
  bigquery_view: string
}

interface BigEightData {
  signals: BigEightSignal[]
  overall_sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  last_updated: string
}

async function fetchBigEight(): Promise<BigEightData> {
  const response = await fetch('/api/v4/big-eight-signals')
  
  if (!response.ok) {
    // NO FAKE DATA - Must connect to real BigQuery BIG 8 signals
    throw new Error(`Big Eight Signals API unavailable: ${response.status}. ZERO FAKE DATA POLICY - Cannot display hardcoded signal values.`)
  }
  
  const data = await response.json()
  
  // Transform to expected format - USE ACTUAL PERCENTAGES FROM API
  const signals: BigEightSignal[] = data.signals.map((s: any) => ({
    signal_name: s.name,
    current_value: s.value,
    signal_strength: s.impact === 'HIGH' ? 'STRONG' : s.impact === 'MEDIUM' ? 'MODERATE' : 'WEAK',
    trend: s.status === 'BULLISH' ? 'BULLISH' : s.status === 'BEARISH' || s.status === 'CRITICAL' || s.status === 'ELEVATED' ? 'BEARISH' : 'NEUTRAL',
    impact_score: s.percentage, // USE ACTUAL PERCENTAGE (26%, 56%, 0%, 20%, etc)
    last_updated: data.data_date,
    bigquery_view: s.key
  }))
  
  const bullishCount = signals.filter(s => s.trend === 'BULLISH').length
  const bearishCount = signals.filter(s => s.trend === 'BEARISH').length
  const overall_sentiment = bullishCount > bearishCount ? 'BULLISH' : bearishCount > bullishCount ? 'BEARISH' : 'NEUTRAL'
  
  return {
    signals,
    overall_sentiment,
    last_updated: data.updated_at
  }
}

const getTrendColor = (trend: string) => {
  switch (trend) {
    case 'BULLISH': return 'text-buy-primary'
    case 'BEARISH': return 'text-sell-primary' 
    case 'NEUTRAL': return 'text-text-secondary'
    default: return 'text-text-secondary'
  }
}

const getStrengthColor = (strength: string) => {
  switch (strength) {
    case 'STRONG': return 'text-accent-purple'
    case 'MODERATE': return 'text-buy-accent'
    case 'WEAK': return 'text-text-tertiary'
    default: return 'text-text-secondary'
  }
}

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'BULLISH': return <TrendingUp className="w-3 h-3" />
    case 'BEARISH': return <TrendingDown className="w-3 h-3" />
    case 'NEUTRAL': return <Activity className="w-3 h-3" />
    default: return <Activity className="w-3 h-3" />
  }
}

export function BigEightSignals() {
  const { data: bigEightData, isLoading, error } = useQuery({
    queryKey: ['big-eight-signals'],
    queryFn: fetchBigEight,
    refetchInterval: 60000, // Update every minute from BigQuery
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary rounded-lg border border-border-primary p-6 shadow-depth">
        <div className="flex items-center space-x-2 mb-6">
          <Zap className="w-6 h-6 text-accent-purple animate-pulse" />
          <h2 className="text-xl font-semibold text-text-primary">Big 8 Signals</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
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

  if (error || !bigEightData) {
    return (
      <div className="bg-sell-critical/10 border border-sell-critical/20 rounded-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background-tertiary flex items-center justify-center">
            <Zap className="w-8 h-8 text-sell-critical" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            No Big 8 Signals Available
          </h3>
          <p className="text-text-secondary mb-4">
            Cannot connect to BigQuery Big 8 signal views. ZERO FAKE DATA POLICY in effect.
          </p>
          <div className="bg-background-tertiary rounded-lg p-4 text-left">
            <h4 className="text-sm font-medium text-text-primary mb-2">Required BigQuery Views:</h4>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• signals.vw_vix_stress_signal</li>
              <li>• signals.vw_harvest_pace_signal</li>
              <li>• signals.vw_china_relations_signal</li>
              <li>• signals.vw_tariff_threat_signal</li>
              <li>• signals.vw_geopolitical_volatility_signal</li>
              <li>• signals.vw_biofuel_cascade_signal_real</li>
              <li>• signals.vw_hidden_correlation_signal</li>
              <li>• signals.vw_biofuel_ethanol_signal</li>
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
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Zap className="w-6 h-6 text-accent-purple" />
          <h2 className="text-xl font-semibold text-text-primary">Big 8 Signals - BigQuery Live</h2>
        </div>
        <div className="flex items-center space-x-4">
          {/* Overall Sentiment */}
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium border ${
            bigEightData.overall_sentiment === 'BEARISH' 
              ? 'bg-sell-primary/20 text-sell-primary border-sell-primary/30'
              : bigEightData.overall_sentiment === 'BULLISH'
              ? 'bg-buy-primary/20 text-buy-primary border-buy-primary/30'
              : 'bg-text-secondary/20 text-text-secondary border-text-secondary/30'
          }`}>
            {getTrendIcon(bigEightData.overall_sentiment)}
            <span>NET: {bigEightData.overall_sentiment}</span>
          </div>
          {/* Live Indicator */}
          <div className="flex items-center space-x-2 text-xs text-text-tertiary font-mono">
            <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
            <span>BigQuery</span>
          </div>
        </div>
      </div>

      {/* Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {(bigEightData?.signals || []).map((signal, index) => (
          <div 
            key={index}
            className="bg-background-tertiary rounded-lg p-4 border border-border-secondary hover:border-accent-purple/30 transition-all duration-200"
            style={{
              boxShadow: signal.signal_strength === 'STRONG' 
                ? '0 0 12px rgba(144, 0, 255, 0.2)' 
                : 'none'
            }}
          >
            {/* Signal Header */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-primary truncate">
                {signal.signal_name}
              </h3>
              <div className={`flex items-center space-x-1 ${getTrendColor(signal.trend)}`}>
                {getTrendIcon(signal.trend)}
              </div>
            </div>

            {/* Signal Value & Strength */}
            <div className="mb-3">
              <div className="text-lg font-semibold text-text-primary mb-1">
                {signal.current_value.toFixed(2)}
              </div>
              <div className={`text-xs font-medium ${getStrengthColor(signal.signal_strength)}`}>
                {signal.signal_strength} SIGNAL
              </div>
            </div>

            {/* Impact Score */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-text-tertiary mb-1">
                <span>Impact Score</span>
                <span className={signal.impact_score > 0 ? 'text-buy-primary' : signal.impact_score < 0 ? 'text-sell-primary' : 'text-text-secondary'}>
                  {signal.impact_score > 0 ? '+' : ''}{signal.impact_score.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-background-primary rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    signal.impact_score > 0 
                      ? 'bg-gradient-to-r from-buy-primary to-buy-accent' 
                      : signal.impact_score < 0 
                      ? 'bg-gradient-to-r from-sell-primary to-sell-critical'
                      : 'bg-gradient-to-r from-text-secondary to-text-tertiary'
                  }`}
                  style={{ 
                    width: `${Math.min(Math.abs(signal.impact_score), 100)}%`, // Direct percentage
                    boxShadow: signal.impact_score !== 0 
                      ? `0 0 6px ${signal.impact_score > 0 ? 'rgba(0, 85, 255, 0.4)' : 'rgba(229, 0, 0, 0.4)'}` 
                      : 'none'
                  }}
                />
              </div>
            </div>

            {/* BigQuery View */}
            <div className="flex items-center space-x-1 text-xs text-text-tertiary font-mono truncate">
              <Database className="w-3 h-3 flex-shrink-0" />
              <span>{signal.bigquery_view.split('.')[1]}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-border-secondary">
        <div className="flex items-center justify-between text-xs text-text-tertiary">
          <div className="flex items-center space-x-2">
            <Database className="w-3 h-3" />
            <span>Live BigQuery signals - No fake data or placeholders</span>
          </div>
          <span>Updated {new Date(bigEightData.last_updated).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  )
}
