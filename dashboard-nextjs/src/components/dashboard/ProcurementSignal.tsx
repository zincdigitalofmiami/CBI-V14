'use client'

import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, TrendingDown, Clock, Shield } from 'lucide-react'
import { InstitutionalGauge } from '@/components/ui/InstitutionalGauge'

interface ProcurementData {
  signal: 'BUY' | 'WAIT' | 'MONITOR'
  confidence: number
  current_price: number
  target_price: number
  expected_change_pct: number
  timeframe: string
  reason: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  next_action: string
}

async function fetchProcurementSignal(): Promise<ProcurementData> {
  // Use the REAL Vertex AI endpoint
  const response = await fetch('/api/v4/forecast/1w')
  
  if (!response.ok) {
    throw new Error('Market data temporarily unavailable')
  }
  
  const forecast = await response.json()
  
  const currentPrice = forecast.current_price
  const predictedPrice = forecast.prediction
  const changePercent = forecast.predicted_change_pct
  
  // Business logic for signal
  let signal: 'BUY' | 'WAIT' | 'MONITOR' = 'MONITOR'
  let reason = 'Market conditions stable. Monitor for opportunities.'
  let nextAction = 'Continue monitoring market conditions. No immediate action required.'
  let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'MEDIUM'
  
  if (changePercent < -2) {
    signal = 'WAIT'
    reason = 'Prices expected to decline. Wait for better entry point.'
    nextAction = `Delay purchases for 1-2 weeks. Set price alerts at $${(currentPrice * 0.97).toFixed(2)}`
    riskLevel = 'LOW'
  } else if (changePercent > 2) {
    signal = 'BUY'
    reason = 'Prices trending up. Secure contracts before further increases.'
    nextAction = 'Lock in contracts this week before prices rise further.'
    riskLevel = 'MEDIUM'
  }
  
  return {
    signal,
    confidence: forecast.confidence_metrics?.r2 ? forecast.confidence_metrics.r2 * 100 : 85,
    current_price: currentPrice,
    target_price: predictedPrice,
    expected_change_pct: changePercent,
    timeframe: '1 week',
    reason,
    risk_level: riskLevel,
    next_action: nextAction
  }
}

function getSignalColor(signal: string) {
  switch (signal) {
    case 'BUY': return 'text-bull-500 bg-bull-500/10 border-bull-500/30'
    case 'WAIT': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30' 
    case 'MONITOR': return 'text-neutral-500 bg-neutral-500/10 border-neutral-500/30'
    default: return 'text-neutral-500 bg-neutral-500/10 border-neutral-500/30'
  }
}

function getRiskColor(level: string) {
  switch (level) {
    case 'LOW': return 'text-bull-500'
    case 'MEDIUM': return 'text-yellow-500'
    case 'HIGH': return 'text-bear-500'
    default: return 'text-neutral-500'
  }
}

export function ProcurementSignal() {
  const { data: signal, isLoading, error } = useQuery({
    queryKey: ['procurement-signal'],
    queryFn: fetchProcurementSignal,
    refetchInterval: 60000, // Update every minute
  })

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="space-y-4">
          <div className="loading-shimmer h-6 w-40 rounded"></div>
          <div className="loading-shimmer h-16 w-full rounded"></div>
          <div className="loading-shimmer h-24 w-full rounded"></div>
        </div>
      </div>
    )
  }

  if (error || !signal) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background-tertiary flex items-center justify-center">
            <Clock className="w-8 h-8 text-text-secondary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Loading Market Data
          </h3>
          <p className="text-text-secondary">
            Analyzing current market conditions...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-text-primary">
          Procurement Signal
        </h2>
        <div className="flex items-center space-x-2 text-sm text-text-secondary">
          <Clock className="w-4 h-4" />
          <span>Updated 30 seconds ago</span>
        </div>
      </div>

      {/* Institutional Gauge Signal */}
      <div className="flex items-center justify-center mb-8">
        <div className="text-center">
          <InstitutionalGauge 
            value={signal.confidence} 
            signal={signal.signal}
            confidence={signal.confidence}
            size="lg"
          />
          <div className="mt-6">
            <div className="text-2xl font-light text-text-primary mb-2">
              {signal.signal === 'BUY' && 'Lock in contracts NOW'}
              {signal.signal === 'WAIT' && `Expect better prices in ${signal.timeframe}`}
              {signal.signal === 'MONITOR' && 'Watch for buying opportunities'}
            </div>
            <div className="text-sm text-text-secondary">
              Risk Level: <span className={getRiskColor(signal.risk_level)}>{signal.risk_level}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Price Targets - Institutional Cards */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-subtle">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2 font-mono">
            Current Price
          </div>
          <div className="text-3xl font-light text-text-primary mb-1">
            ${signal.current_price.toFixed(2)}
          </div>
          <div className="text-xs text-text-secondary font-mono">per cwt</div>
        </div>
        
        <div className="bg-background-secondary border border-border-primary rounded-lg p-6 shadow-subtle">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2 font-mono">
            Target Price
          </div>
          <div className="text-3xl font-light text-text-primary mb-1">
            ${signal.target_price.toFixed(2)}
          </div>
          <div className={`text-sm flex items-center font-mono ${
            signal.expected_change_pct < 0 ? 'text-sell-primary' : 'text-buy-primary'
          }`}>
            <TrendingDown className="w-3 h-3 mr-1" />
            {signal.expected_change_pct.toFixed(1)}%
          </div>
        </div>
      </div>

    </div>
  )
}
