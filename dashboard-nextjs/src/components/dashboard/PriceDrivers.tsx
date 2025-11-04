'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'

interface PriceDriver {
  id: string
  name: string
  technical_name: string
  current_value: number
  impact_score: number
  dollar_impact: number
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  explanation: string
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
}

interface PriceDriversData {
  data_date: string
  current_price: number
  total_drivers: number
  net_dollar_impact: number
  drivers: PriceDriver[]
  market_regime: string
  last_updated: string
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function PriceDrivers() {
  const { data, error, isLoading } = useSWR<PriceDriversData>('/api/v4/price-drivers', fetcher, {
    refreshInterval: 15 * 60 * 1000, // 15 minutes
    revalidateOnFocus: false
  })

  if (error) {
    return (
      <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
        <div className="text-center">
          <div className="text-red-400 text-sm font-medium mb-2">
            ⚠️ PRICE DRIVERS UNAVAILABLE
          </div>
          <div className="text-gray-400 text-xs">
            Feature analysis engine offline - refresh pending
          </div>
        </div>
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'BULLISH': return 'text-green-400 bg-green-400/10'
      case 'BEARISH': return 'text-red-400 bg-red-400/10'
      default: return 'text-gray-400 bg-gray-400/10'
    }
  }

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'HIGH': return 'text-green-400'
      case 'MEDIUM': return 'text-yellow-400'
      default: return 'text-gray-400'
    }
  }

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'HIGH_VOLATILITY': return 'text-red-400 bg-red-400/20'
      case 'ELEVATED_VOLATILITY': return 'text-yellow-400 bg-yellow-400/20'
      case 'NORMAL_VOLATILITY': return 'text-blue-400 bg-blue-400/20'
      default: return 'text-green-400 bg-green-400/20'
    }
  }

  return (
    <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-1">
            Why Prices Are Moving - AI Market Intelligence
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span>Current ZL: ${data.current_price.toFixed(2)}</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${getRegimeColor(data.market_regime)}`}>
              {data.market_regime.replace('_', ' ')}
            </span>
            <span>Net Impact: ${data.net_dollar_impact.toFixed(2)}</span>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>Data: {data.data_date}</div>
          <div>Updated: {new Date(data.last_updated).toLocaleTimeString()}</div>
        </div>
      </div>

      {/* Top 4 Primary Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {data.drivers.slice(0, 4).map((driver) => (
          <div key={driver.id} className="bg-background-tertiary rounded-lg p-4 border border-gray-700">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-medium text-text-primary text-sm mb-1">
                  {driver.name}
                </h3>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getDirectionColor(driver.direction)}`}>
                    {driver.direction}
                  </span>
                  <span className={`text-xs font-medium ${getConfidenceColor(driver.confidence)}`}>
                    {driver.confidence}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${driver.dollar_impact >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {driver.dollar_impact >= 0 ? '+' : ''}${driver.dollar_impact.toFixed(2)}
                </div>
                <div className="text-xs text-gray-400">impact</div>
              </div>
            </div>

            {/* Impact Bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>Signal Strength</span>
                <span>{Math.round(driver.impact_score)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    driver.direction === 'BULLISH' ? 'bg-green-400' : 
                    driver.direction === 'BEARISH' ? 'bg-red-400' : 'bg-gray-400'
                  }`}
                  style={{ width: `${Math.min(Math.abs(driver.impact_score), 100)}%` }}
                />
              </div>
            </div>

            {/* AI Explanation */}
            <p className="text-sm text-gray-300 leading-relaxed">
              {driver.explanation}
            </p>

            {/* Technical Detail */}
            <div className="mt-2 pt-2 border-t border-gray-600">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Value: {typeof driver.current_value === 'number' ? driver.current_value.toFixed(2) : driver.current_value}</span>
                <span className="font-mono">{driver.technical_name}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Secondary Drivers (Compact) */}
      {data.drivers.length > 4 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3">Secondary Factors</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {data.drivers.slice(4, 8).map((driver) => (
              <div key={driver.id} className="bg-background-tertiary rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-text-primary truncate">
                    {driver.name}
                  </span>
                  <span className={`text-xs font-bold ${driver.dollar_impact >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {driver.dollar_impact >= 0 ? '+' : ''}${Math.abs(driver.dollar_impact).toFixed(1)}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      driver.direction === 'BULLISH' ? 'bg-green-400' : 
                      driver.direction === 'BEARISH' ? 'bg-red-400' : 'bg-gray-400'
                    }`}
                    style={{ width: `${Math.min(Math.abs(driver.impact_score), 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                  {driver.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-400">
            AI analyzed {data.total_drivers} market factors • 
            <span className="ml-1">
              {data.drivers.filter(d => d.direction === 'BULLISH').length} bullish, {' '}
              {data.drivers.filter(d => d.direction === 'BEARISH').length} bearish signals
            </span>
          </div>
          <div className="text-right">
            <span className="text-gray-400">Net price impact: </span>
            <span className={`font-bold ${data.net_dollar_impact >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.net_dollar_impact >= 0 ? '+' : ''}${data.net_dollar_impact.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}



