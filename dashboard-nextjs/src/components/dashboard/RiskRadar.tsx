'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface RiskFactor {
  factor: string
  value: number
  description: string
  top_driver: string
  importance: number
}

interface FeatureOverlay {
  name: string
  importance: number
}

interface RiskRadarData {
  data_date: string
  overall_risk_score: number
  risk_regime: string
  risk_factors: RiskFactor[]
  feature_overlays: {
    most_important: RiskFactor
    top_3_drivers: FeatureOverlay[]
  }
  market_stress_indicators: {
    vix_level: number
    price_volatility: number
    correlation_breakdown: boolean
  }
  last_updated: string
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function RiskRadar() {
  const { data, error, isLoading } = useSWR<RiskRadarData>('/api/v4/risk-radar', fetcher, {
    refreshInterval: 15 * 60 * 1000, // 15 minutes
    revalidateOnFocus: false
  })

  if (error) {
    return (
      <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
        <div className="text-center">
          <div className="text-red-400 text-sm font-medium mb-2">
            ⚠️ RISK RADAR OFFLINE
          </div>
          <div className="text-gray-400 text-xs">
            Risk analysis engine unavailable
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
          <div className="h-64 bg-gray-700 rounded mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const getRiskColor = (regime: string) => {
    switch (regime) {
      case 'CRITICAL': return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-400' }
      case 'HIGH': return { bg: 'bg-red-400/20', text: 'text-red-300', border: 'border-red-300' }
      case 'MODERATE': return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-400' }
      case 'LOW': return { bg: 'bg-green-400/20', text: 'text-green-300', border: 'border-green-300' }
      default: return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-400' }
    }
  }

  const riskColors = getRiskColor(data.risk_regime)
  
  // Prepare radar chart data
  const radarData = data.risk_factors.map(factor => ({
    factor: factor.factor.replace(' Risk', '').replace(' Shock', ''),
    value: factor.value,
    fullName: factor.factor,
    description: factor.description,
    driver: factor.top_driver,
    importance: factor.importance
  }))

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-background-tertiary border border-gray-600 rounded-lg p-3 shadow-xl max-w-xs">
          <p className="text-text-primary font-medium mb-2">{data.fullName}</p>
          <div className="space-y-1 text-sm">
            <p className="text-gray-300">Risk Level: <span className="font-medium">{data.value}/100</span></p>
            <p className="text-blue-400">Top Driver: {data.driver}</p>
            <p className="text-yellow-400">Model Weight: {data.importance.toFixed(1)}%</p>
            <p className="text-gray-300 text-xs mt-2 leading-relaxed">{data.description}</p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-background-secondary rounded-lg p-6 border border-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-1">
            Risk Radar - 6-Factor Analysis
          </h2>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">Overall Risk: {data.overall_risk_score}/100</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${riskColors.bg} ${riskColors.border} ${riskColors.text}`}>
              {data.risk_regime} RISK
            </span>
            <span className="text-gray-400">VIX: {data.market_stress_indicators.vix_level.toFixed(1)}</span>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>Data: {data.data_date}</div>
          <div>Updated: {new Date(data.last_updated).toLocaleTimeString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Radar Chart */}
        <div className="xl:col-span-2">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis 
                  dataKey="factor" 
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  className="text-xs"
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  tick={{ fill: '#6B7280', fontSize: 10 }}
                  tickCount={5}
                />
                <Radar
                  name="Risk Level"
                  dataKey="value"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          
          {/* Feature Importance Overlay */}
          <div className="mt-4 p-3 bg-background-tertiary rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-text-primary mb-2">
              🎯 Top Feature Drivers (Model Importance)
            </h3>
            <div className="flex items-center justify-between text-xs">
              {data.feature_overlays.top_3_drivers.map((driver, index) => (
                <div key={driver.name} className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    index === 0 ? 'bg-yellow-400' : 
                    index === 1 ? 'bg-blue-400' : 'bg-green-400'
                  }`}></div>
                  <span className="text-gray-300">{driver.name}</span>
                  <span className="font-medium text-gray-400">{driver.importance.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Risk Factor Details */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-text-primary mb-3">Risk Breakdown</h3>
          {data.risk_factors.map((factor, index) => (
            <div key={factor.factor} className="bg-background-tertiary rounded-lg p-3 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-text-primary">
                  {factor.factor}
                </span>
                <span className={`text-sm font-bold ${
                  factor.value > 70 ? 'text-red-400' :
                  factor.value > 55 ? 'text-yellow-400' :
                  factor.value > 40 ? 'text-blue-400' : 'text-green-400'
                }`}>
                  {factor.value}/100
                </span>
              </div>
              
              {/* Risk Level Bar */}
              <div className="mb-2">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      factor.value > 70 ? 'bg-red-400' :
                      factor.value > 55 ? 'bg-yellow-400' :
                      factor.value > 40 ? 'bg-blue-400' : 'bg-green-400'
                    }`}
                    style={{ width: `${factor.value}%` }}
                  />
                </div>
              </div>
              
              <p className="text-xs text-gray-300 mb-2 leading-relaxed">
                {factor.description}
              </p>
              
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>Driver: {factor.top_driver}</span>
                <span className="font-mono">{factor.importance.toFixed(1)}% weight</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Market Stress Indicators */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-400">VIX Level</div>
            <div className={`font-bold ${
              data.market_stress_indicators.vix_level > 25 ? 'text-red-400' :
              data.market_stress_indicators.vix_level > 20 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {data.market_stress_indicators.vix_level.toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Price Volatility</div>
            <div className={`font-bold ${
              data.market_stress_indicators.price_volatility > 20 ? 'text-red-400' :
              data.market_stress_indicators.price_volatility > 10 ? 'text-yellow-400' :
              'text-green-400'
            }`}>
              {data.market_stress_indicators.price_volatility.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-gray-400">Risk Regime</div>
            <div className={`font-bold ${riskColors.text}`}>
              {data.risk_regime}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Correlation Risk</div>
            <div className={`font-bold ${
              data.market_stress_indicators.correlation_breakdown ? 'text-red-400' : 'text-green-400'
            }`}>
              {data.market_stress_indicators.correlation_breakdown ? 'BREAKDOWN' : 'STABLE'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
